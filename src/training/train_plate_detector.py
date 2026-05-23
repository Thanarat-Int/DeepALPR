"""Train a YOLOv8 plate detector -- enables detection.plate_mode = "model".

The demo runs in "mock" mode: plate boxes come from the ground-truth sidecar
that make_mock_video.py produces. This script trains a REAL single-class plate
detector instead:

  1. exports a YOLO-format dataset from mock_traffic.mp4 + its sidecar
  2. fine-tunes yolov8n on it
  3. writes weights to models/plate_detector.pt

For production, replace the exported frames/labels in data/plate_dataset/ with
REAL annotated CCTV footage and rerun, then set `detection.plate_mode: model`
in config.yaml.

Run:  python src/training/train_plate_detector.py
"""
import json
import shutil
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

VIDEO = ROOT / "assets" / "mock_traffic.mp4"
SIDECAR = ROOT / "assets" / "mock_traffic.plates.json"
DATASET = ROOT / "data" / "plate_dataset"
FRAME_STRIDE = 3            # export every Nth frame to limit dataset size
VAL_FRACTION = 0.15


def export_yolo_dataset():
    """Turn the mock video + sidecar into a YOLO detection dataset."""
    if not VIDEO.exists() or not SIDECAR.exists():
        raise FileNotFoundError("Run src/data/make_mock_video.py first.")

    frames = json.loads(SIDECAR.read_text(encoding="utf-8"))["frames"]
    if DATASET.exists():
        shutil.rmtree(DATASET)
    for split in ("train", "val"):
        (DATASET / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET / "labels" / split).mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(VIDEO))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    idx = exported = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        records = frames.get(str(idx), [])
        if idx % FRAME_STRIDE == 0 and records:
            split = "val" if (exported % int(1 / VAL_FRACTION) == 0) else "train"
            cv2.imwrite(str(DATASET / "images" / split / f"f{idx:05d}.jpg"), frame)
            lines = []
            for r in records:
                x1, y1, x2, y2 = r["bbox"]
                cx = (x1 + x2) / 2 / width
                cy = (y1 + y2) / 2 / height
                bw = (x2 - x1) / width
                bh = (y2 - y1) / height
                lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            (DATASET / "labels" / split / f"f{idx:05d}.txt").write_text(
                "\n".join(lines))
            exported += 1
        idx += 1
    cap.release()

    data_yaml = DATASET / "data.yaml"
    data_yaml.write_text(
        f"path: {DATASET.as_posix()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n  0: plate\n", encoding="utf-8")
    print(f"Exported {exported} labelled frames to {DATASET}")
    return data_yaml


def main():
    data_yaml = export_yolo_dataset()
    from ultralytics import YOLO

    model = YOLO("yolov8n.pt")
    model.train(data=str(data_yaml), epochs=40, imgsz=640, batch=8,
                project=str(ROOT / "runs"), name="plate_detector")

    best = ROOT / "runs" / "plate_detector" / "weights" / "best.pt"
    target = ROOT / "models" / "plate_detector.pt"
    if best.exists():
        shutil.copy(best, target)
        print(f"Saved detector -> {target}")
        print('Set `detection.plate_mode: model` in config.yaml to use it.')


if __name__ == "__main__":
    main()
