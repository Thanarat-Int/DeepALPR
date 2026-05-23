"""ALPR pipeline orchestrator.

Per frame:  detect plates -> track -> estimate speed -> OCR -> multi-frame vote
            -> speed gate -> emit a PlateEvent (once per plate).

A plate becomes an event only when it has been read on `votes_required` frames,
the voted text passes Thai-plate validation and the confidence threshold, and
(if the speed gate is on) the vehicle was travelling at <= max_speed_kmh.
"""
import logging
import secrets
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from alpr.capture import FrameSource
from alpr.color import classify_color, vehicle_bbox_from_plate
from alpr.config import resolve
from alpr.detection import PlateDetector
from alpr.events import PlateEvent, is_valid_thai_plate, now_iso
from alpr.ocr import PlateOCR
from alpr.tracking import PlateTracker

log = logging.getLogger("alpr.pipeline")

_FONT_CANDIDATES = ["C:/Windows/Fonts/leelawdb.ttf", "C:/Windows/Fonts/tahomabd.ttf"]


def _load_font(size):
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


class ALPRPipeline:
    def __init__(self, config, on_event=None):
        self.cfg = config
        self.on_event = on_event or (lambda e: None)

        self.video_path = resolve(config.capture.source)
        sidecar = self.video_path.with_name(self.video_path.stem + ".plates.json")

        self.detector = PlateDetector(
            mode=config.detection.plate_mode,
            model_path=resolve(config.detection.plate_model),
            conf=config.detection.plate_conf,
            sidecar=sidecar)
        self.tracker = PlateTracker(
            iou_threshold=config.tracking.iou_threshold,
            max_age=config.tracking.max_age)
        self.ocr = PlateOCR(resolve(config.ocr.model))

        self.votes_required = config.ocr.votes_required
        self.min_conf = config.ocr.min_confidence
        self.min_plate_width = config.detection.get("min_plate_width", 0)
        self.max_speed = config.speed.max_speed_kmh
        self.speed_gate = config.speed.speed_gate_enabled
        self.mpp = config.speed.meters_per_pixel

        self.image_dir = resolve(config.storage.image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        self.fps = 30.0
        self._emitted_plates: set[str] = set()      # de-duplicate repeat events
        self.stats = {"frames": 0, "events": 0,
                      "rejected_fast": 0, "tracks_seen": 0}
        self._font = _load_font(22)
        self._font_small = _load_font(16)

        # --- Live Camera state (thread-safe, read by API /api/live/snapshot)
        self._latest_jpeg: bytes | None = None
        self._latest_lock = threading.Lock()
        self._latest_event: dict | None = None

    # --- frame processing ---------------------------------------------------
    def _crop(self, frame, bbox, pad=3):
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = (int(v) for v in bbox)
        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
        x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
        if x2 <= x1 or y2 <= y1:
            return None
        return frame[y1:y2, x1:x2]

    def _display_crop(self, frame, bbox):
        """Crop the FULL plate (registration + province line) for display.

        The OCR bbox covers only the registration region (top ~55% of the
        plate), so to render the captured image with the province visible we
        expand the bbox vertically. A small horizontal pad gives the plate
        breathing room from the surrounding bumper / paint.
        """
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = (int(v) for v in bbox)
        bw, bh = x2 - x1, y2 - y1
        pad_x = int(bw * 0.08)
        # registration ~ top 55% -> province occupies another ~45% of plate
        # height (= ~0.82x of bbox height since bbox is the 55% slice)
        pad_y_top = int(bh * 0.18)
        pad_y_bot = int(bh * 0.92)
        x1 = max(0, x1 - pad_x)
        x2 = min(w, x2 + pad_x)
        y1 = max(0, y1 - pad_y_top)
        y2 = min(h, y2 + pad_y_bot)
        if x2 <= x1 or y2 <= y1:
            return None
        return frame[y1:y2, x1:x2]

    def _save_crop(self, crop, track_id) -> str:
        if crop is None or crop.size == 0:
            return ""
        stamp = now_iso().replace(":", "").replace("-", "")
        # random suffix -> unique filename, no collisions across runs
        path = self.image_dir / f"plate_{track_id}_{stamp}_{secrets.token_hex(3)}.jpg"
        cv2.imwrite(str(path), crop)
        return str(path)

    def process_frame(self, frame, frame_idx) -> list[PlateEvent]:
        """Run one frame through the pipeline. Returns events emitted this frame.

        OCR readings are accumulated on every active track; a plate is emitted
        only once its track leaves the scene, so the voted result draws on
        every frame the plate was visible -- not just the first few (when the
        vehicle is still far away and the plate is small)."""
        boxes = self.detector.detect(frame, frame_idx)
        boxes = [b for b in boxes if (b[2] - b[0]) >= self.min_plate_width]
        active, retired = self.tracker.update(boxes, frame_idx)

        for track in active:
            if track.missed != 0:
                continue            # not detected this frame -- bbox is stale
            ocr_crop = self._crop(frame, track.bbox)
            text, conf = self.ocr.read(ocr_crop)
            # Save the FULL plate crop (registration + province) for display;
            # OCR runs on the tight registration crop only.
            display_crop = self._display_crop(frame, track.bbox)
            track.add_reading(text, conf, display_crop)
            track.estimate_speed(self.fps, self.mpp)
            # Sample vehicle colour from the area around the plate. Cheap (HSV
            # histogram, no ML); accumulated across frames so a single noisy
            # sample does not bias the final answer.
            vbox = vehicle_bbox_from_plate(track.bbox, frame.shape)
            vcrop = frame[vbox[1]:vbox[3], vbox[0]:vbox[2]]
            label_en, label_th, col_conf = classify_color(vcrop)
            track.add_color(label_en, label_th, col_conf)

        events = []
        for track in retired:                       # car left the scene -> finalise
            event = self._try_emit(track)
            if event:
                events.append(event)

        self.stats["frames"] += 1
        self.stats["tracks_seen"] = self.tracker._next_id - 1
        return events

    def flush(self) -> list[PlateEvent]:
        """Emit any tracks still alive when the stream ends."""
        events = []
        for track in list(self.tracker.tracks):
            event = self._try_emit(track)
            if event:
                events.append(event)
        return events

    def _try_emit(self, track) -> PlateEvent | None:
        if track.emitted or track.reading_count < self.votes_required:
            return None
        plate, conf = track.best_plate()
        if conf < self.min_conf or not is_valid_thai_plate(plate):
            track.emitted = True
            return None

        speed = round(track.speed_kmh, 1)
        if self.speed_gate and speed > self.max_speed:
            track.emitted = True
            self.stats["rejected_fast"] += 1
            log.info("track %d skipped: %.1f km/h exceeds %d km/h gate",
                     track.id, speed, self.max_speed)
            return None

        track.emitted = True
        if plate in self._emitted_plates:           # same plate already reported
            return None
        self._emitted_plates.add(plate)
        color_en, color_th, color_conf = track.best_color()
        province = self.detector.province_for(plate)
        event = PlateEvent(
            plate=plate,
            speed_kmh=speed,
            confidence=round(conf, 3),
            timestamp=now_iso(),
            image_path=self._save_crop(track.best_crop(), track.id),
            track_id=track.id,
            province=province,
            vehicle_color=color_en if color_en != "unknown" else None,
            vehicle_color_th=color_th or None,
            color_conf=round(color_conf, 3) if color_conf else None,
        )
        self.stats["events"] += 1
        log.info("EVENT track %d: %s | %.1f km/h | conf %.2f",
                 track.id, plate, speed, conf)
        self.on_event(event)
        return event

    # --- visualisation ------------------------------------------------------
    def _annotate(self, frame) -> np.ndarray:
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        for track in self.tracker.tracks:
            x1, y1, x2, y2 = (int(v) for v in track.bbox)
            within = (not self.speed_gate) or track.speed_kmh <= self.max_speed
            color = (0, 200, 0) if within else (235, 130, 0)
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            plate, _ = track.best_plate()
            draw.text((x1, max(0, y1 - 27)), plate or "...",
                      fill=color, font=self._font)
            # second line below the plate: speed + colour (if known yet)
            color_en, color_th, _ = track.best_color()
            tag_bits = [f"{track.speed_kmh:.0f} km/h"]
            if color_en != "unknown":
                tag_bits.append(color_th or color_en)
            draw.text((x1, y2 + 2), "  ".join(tag_bits),
                      fill=color, font=self._font_small)
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # --- live preview -------------------------------------------------------
    def _publish_snapshot(self, frame_bgr: np.ndarray):
        """Encode the annotated frame as JPEG and stash it for the API."""
        ok, buf = cv2.imencode(".jpg", frame_bgr,
                               [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        if not ok:
            return
        with self._latest_lock:
            self._latest_jpeg = buf.tobytes()

    def latest_snapshot(self) -> bytes | None:
        """Read the most recent annotated JPEG (thread-safe)."""
        with self._latest_lock:
            return self._latest_jpeg

    def set_latest_event(self, payload: dict | None):
        """Called by run_service.on_event so /api/live can show the last hit."""
        self._latest_event = payload

    def get_latest_event(self) -> dict | None:
        return self._latest_event

    # --- run loop -----------------------------------------------------------
    def run(self, output_path=None, display=False, max_frames=None,
            loop=False) -> dict:
        """Run the pipeline over the configured source.

        If `loop` is True, the mock video restarts forever so the Live Camera
        keeps streaming and new events keep firing -- handy for demos when
        no real CCTV is connected yet. In production (real RTSP stream) the
        FrameSource itself never ends, so this flag is effectively a no-op.
        """
        iteration = 0
        while True:
            iteration += 1
            with FrameSource(self.video_path) as src:
                self.fps = src.fps
                writer = None
                if output_path and iteration == 1:
                    writer = cv2.VideoWriter(str(output_path),
                                             cv2.VideoWriter_fourcc(*"mp4v"),
                                             src.fps, (src.width, src.height))
                log.info("pipeline start (loop %d): %s (%d frames @ %.1f fps)",
                         iteration, self.video_path.name,
                         src.frame_count, src.fps)

                stopped = False
                for idx, frame in src.frames():
                    self.process_frame(frame, idx)
                    # Annotate every Nth frame so the Live Camera has a stream
                    # to show. 5 fps is plenty for a preview; 30 fps would
                    # burn CPU encoding JPEGs nobody watches.
                    annotated = None
                    publish_live = (idx % max(1, int(self.fps // 5)) == 0)
                    if publish_live or writer is not None or display:
                        annotated = self._annotate(frame)
                    if publish_live and annotated is not None:
                        self._publish_snapshot(annotated)
                    if writer is not None and annotated is not None:
                        writer.write(annotated)
                    if display and annotated is not None:
                        cv2.imshow("Deep ALPR", annotated)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            stopped = True
                            break
                    if max_frames and idx + 1 >= max_frames:
                        stopped = True
                        break

                self.flush()

                if writer is not None:
                    writer.release()
                if display and stopped:
                    cv2.destroyAllWindows()

            if not loop or stopped:
                break
            # Reset state so the next loop produces fresh events for the demo.
            self._emitted_plates.clear()
            self.tracker.tracks.clear()
            self.tracker._next_id = 1
            log.info("loop complete -- restarting video for live demo")

        log.info("pipeline done: %s", self.stats)
        return self.stats
