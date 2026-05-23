"""Train YOLOv8 plate detector on local mock + (optional) external dataset.

If data/plate_dataset_ext/ exists (created by fetch_external_dataset.py), its
images and labels are MERGED with the mock dataset before training.

Run:  python src/training/train_plate_detector_combined.py
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
MOCK_OUT = ROOT / "data" / "plate_dataset"
EXT_DIR = ROOT / "data" / "plate_dataset_ext"
COMBINED = ROOT / "data" / "plate_dataset_combined"
FRAME_STRIDE = 3
VAL_FRACTION = 0.15


def export_mock():
    """Export mock video frames as YOLO dataset."""
    if not VIDEO.exists() or not SIDECAR.exists():
        raise FileNotFoundError("Run src/data/make_mock_video.py first.")
    frames = json.loads(SIDECAR.read_text(encoding="utf-8"))["frames"]
    if MOCK_OUT.exists():
        shutil.rmtree(MOCK_OUT)
    for split in ("train", "val"):
        (MOCK_OUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (MOCK_OUT / "labels" / split).mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(VIDEO))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    idx = exported = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        recs = frames.get(str(idx), [])
        if idx % FRAME_STRIDE == 0 and recs:
            split = "val" if (exported % int(1 / VAL_FRACTION) == 0) else "train"
            cv2.imwrite(str(MOCK_OUT / "images" / split / f"mock_{idx:05d}.jpg"), frame)
            lines = []
            for r in recs:
                x1, y1, x2, y2 = r["plate_bbox"]
                cx = (x1 + x2) / 2 / W
                cy = (y1 + y2) / 2 / H
                bw = (x2 - x1) / W
                bh = (y2 - y1) / H
                lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            (MOCK_OUT / "labels" / split / f"mock_{idx:05d}.txt").write_text(
                "\n".join(lines))
            exported += 1
        idx += 1
    cap.release()
    print(f"Mock: exported {exported} frames")
    return exported


def combine_with_external():
    """Merge mock + external (if present) into COMBINED."""
    if COMBINED.exists():
        shutil.rmtree(COMBINED)
    for split in ("train", "val"):
        (COMBINED / "images" / split).mkdir(parents=True, exist_ok=True)
        (COMBINED / "labels" / split).mkdir(parents=True, exist_ok=True)

    def copy_tree(src_root: Path, prefix: str):
        count = 0
        for split in ("train", "val"):
            img_src = src_root / "images" / split
            lbl_src = src_root / "labels" / split
            if not img_src.exists():
                continue
            for img in img_src.iterdir():
                stem = f"{prefix}_{img.name}"
                shutil.copy(img, COMBINED / "images" / split / stem)
                lbl = lbl_src / (img.stem + ".txt")
                if lbl.exists():
                    shutil.copy(lbl,
                                COMBINED / "labels" / split / f"{prefix}_{img.stem}.txt")
                count += 1
        return count

    n_mock = copy_tree(MOCK_OUT, "mock")
    n_ext = copy_tree(EXT_DIR, "ext") if EXT_DIR.exists() else 0
    print(f"Combined: mock={n_mock}, external={n_ext}, total={n_mock + n_ext}")

    yaml = COMBINED / "data.yaml"
    yaml.write_text(
        f"path: {COMBINED.as_posix()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n  0: plate\n", encoding="utf-8")
    return yaml


def main():
    export_mock()
    data_yaml = combine_with_external()

    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    model.train(data=str(data_yaml), epochs=40, imgsz=640, batch=16,
                project=str(ROOT / "runs"), name="plate_detector",
                exist_ok=True, verbose=True)

    best = ROOT / "runs" / "plate_detector" / "weights" / "best.pt"
    target = ROOT / "models" / "plate_detector.pt"
    if best.exists():
        shutil.copy(best, target)
        print(f"Saved detector -> {target}")
        print('Set `detection.plate_mode: model` in config.yaml to use it.')


if __name__ == "__main__":
    main()
