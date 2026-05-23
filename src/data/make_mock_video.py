"""Build the mock traffic video for an end-to-end demo.

Takes assets/car.mp4 (real cars, real motion), detects + tracks vehicles with
YOLOv8, and composites a consistent synthetic Thai plate onto each vehicle.

Outputs:
    assets/mock_traffic.mp4          real cars wearing synthetic Thai plates
    assets/mock_traffic.plates.json  per-frame plate boxes + ground truth

This gives the pipeline genuine vehicle motion (so speed estimation is real)
with readable plates (so OCR is exercised). The ground-truth JSON is used by
detection.PlateDetector in "mock" mode and by the evaluation harness.

Run:  python src/data/make_mock_video.py
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from data.plate_generator import (REG_REGION, random_plate,  # noqa: E402
                                  render_full_plate)

SRC = ROOT / "assets" / "car.mp4"
OUT_VIDEO = ROOT / "assets" / "mock_traffic.mp4"
OUT_JSON = ROOT / "assets" / "mock_traffic.plates.json"
VEHICLE_CLASSES = [2, 3, 5, 7]          # car, motorcycle, bus, truck
MIN_VEHICLE_SIZE = 110                  # ignore tiny far-away vehicles
PLATE_SCALE = 0.48                      # plate width as a fraction of vehicle width


def main():
    random.seed(7)
    model = YOLO(str(ROOT / "yolov8n.pt"))

    cap = cv2.VideoCapture(str(SRC))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    writer = cv2.VideoWriter(str(OUT_VIDEO),
                             cv2.VideoWriter_fourcc(*"mp4v"),
                             fps, (width, height))

    plate_by_track: dict[int, tuple] = {}   # vehicle id -> (record, rendered img)
    frames_meta: dict[str, list] = {}

    results = model.track(source=str(SRC), stream=True, persist=True,
                          classes=VEHICLE_CLASSES, conf=0.40, verbose=False)

    idx = 0
    for r in results:
        frame = r.orig_img.copy()
        records = []

        if r.boxes is not None and r.boxes.id is not None:
            xyxy = r.boxes.xyxy.cpu().numpy()
            ids = r.boxes.id.int().cpu().tolist()
            for box, tid in zip(xyxy, ids):
                x1, y1, x2, y2 = (int(v) for v in box)
                vw, vh = x2 - x1, y2 - y1
                if vw < MIN_VEHICLE_SIZE or vh < MIN_VEHICLE_SIZE:
                    continue

                if tid not in plate_by_track:
                    rec = random_plate()
                    plate_by_track[tid] = (rec, render_full_plate(rec))
                rec, plate_img = plate_by_track[tid]

                pw = int(vw * PLATE_SCALE)
                ph = int(pw * plate_img.height / plate_img.width)
                px = x1 + (vw - pw) // 2
                py = y2 - ph - int(vh * 0.06)
                if px < 0 or py < 0 or px + pw > width or py + ph > height:
                    continue

                patch = cv2.cvtColor(
                    np.asarray(plate_img.resize((pw, ph))), cv2.COLOR_RGB2BGR)
                frame[py:py + ph, px:px + pw] = patch
                # The CRNN OCR reads a single line, so the detection box is the
                # registration-line region only; the province line is excluded.
                rx1, ry1, rx2, ry2 = REG_REGION
                records.append({
                    "bbox": [px + int(pw * rx1), py + int(ph * ry1),
                             px + int(pw * rx2), py + int(ph * ry2)],
                    "plate_bbox": [px, py, px + pw, py + ph],
                    "registration": rec["registration"],
                    "province": rec["province"],
                    "plate_type": rec["plate_type"],
                    "track_id": tid,
                })

        frames_meta[str(idx)] = records
        writer.write(frame)
        idx += 1
        if idx % 100 == 0:
            print(f"  ...{idx} frames", flush=True)

    writer.release()

    # Keep only moving vehicles in the sidecar. Parked background cars stay
    # drawn in the video (realistic) but are not traffic the system analyses.
    positions = defaultdict(list)
    for recs in frames_meta.values():
        for r in recs:
            x1, y1, x2, y2 = r["bbox"]
            positions[r["track_id"]].append(((x1 + x2) / 2, (y1 + y2) / 2))
    moving = {tid for tid, pts in positions.items()
              if len(pts) >= 2 and max(abs(pts[-1][0] - pts[0][0]),
                                       abs(pts[-1][1] - pts[0][1])) > 40}
    frames_meta = {f: [r for r in recs if r["track_id"] in moving]
                   for f, recs in frames_meta.items()}

    OUT_JSON.write_text(
        json.dumps({"fps": fps, "frames": frames_meta}, ensure_ascii=False),
        encoding="utf-8")
    print(f"Done: {OUT_VIDEO.name} ({idx} frames), {OUT_JSON.name} "
          f"({len(moving)} moving plates of {len(plate_by_track)} detected)")


if __name__ == "__main__":
    main()
