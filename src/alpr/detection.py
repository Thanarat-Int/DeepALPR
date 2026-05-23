"""License-plate detection.

Two modes (set via config `detection.plate_mode`):

  * "mock"  -- read plate boxes from a ground-truth sidecar JSON produced by
               make_mock_video.py. Lets the full pipeline run end-to-end on
               synthetic data without a trained detector.
  * "model" -- run a YOLO plate detector (train one with train_plate_detector.py
               once real annotated data is available).

In both modes only bounding boxes are returned -- the OCR stage still reads the
actual pixels, so recognition is always exercised honestly.
"""
import json
from pathlib import Path


class PlateDetector:
    def __init__(self, mode="mock", model_path=None, conf=0.35, sidecar=None):
        self.mode = mode
        self.conf = conf
        self._frames = {}
        self.model = None

        if mode == "mock":
            if not sidecar or not Path(sidecar).exists():
                raise FileNotFoundError(
                    f"mock mode needs the sidecar JSON ({sidecar}). "
                    f"Run: python src/data/make_mock_video.py")
            data = json.loads(Path(sidecar).read_text(encoding="utf-8"))
            self._frames = data["frames"]
        elif mode == "model":
            from ultralytics import YOLO
            if not model_path or not Path(model_path).exists():
                raise FileNotFoundError(
                    f"model mode needs trained weights ({model_path}). "
                    f"Run: python src/training/train_plate_detector.py")
            self.model = YOLO(str(model_path))
        else:
            raise ValueError(f"unknown plate_mode: {mode}")

    def detect(self, frame, frame_idx) -> list[tuple[int, int, int, int]]:
        """Return plate bounding boxes [(x1, y1, x2, y2), ...] for this frame."""
        if self.mode == "mock":
            return [tuple(r["bbox"]) for r in self._frames.get(str(frame_idx), [])]

        result = self.model(frame, verbose=False, conf=self.conf)[0]
        return [tuple(map(int, box))
                for box in result.boxes.xyxy.cpu().numpy()]

    def province_for(self, plate_text: str) -> str | None:
        """Look up the province for a given plate (mock-mode ground truth).

        Falls back to None in model mode -- province OCR is a separate feature
        that requires its own classifier. In a real deployment, province is
        usually pulled from the vehicle registry rather than read from the
        plate, so the API surface stays the same.
        """
        if self.mode != "mock":
            return None
        for recs in self._frames.values():
            for r in recs:
                if r.get("registration") == plate_text:
                    return r.get("province")
        return None
