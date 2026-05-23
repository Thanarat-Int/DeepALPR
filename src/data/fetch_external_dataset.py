"""Download an external Thai license-plate dataset into data/plate_dataset_ext/.

This script supports two sources. Both require an API key from the user; the
script will not auto-sign-up on your behalf.

  1) Roboflow Universe (recommended starting point)
     - free account: https://app.roboflow.com
     - get an API key at: https://app.roboflow.com/settings/api
     - search Universe for a Thai license-plate dataset and copy the
       workspace/project/version triple, then run:
            python src/data/fetch_external_dataset.py roboflow \\
                --api-key YOUR_KEY \\
                --workspace dataset-format-conversion-iidaz \\
                --project thailand-license-plate-recognition \\
                --version 1

  2) HuggingFace Datasets
     - public datasets need no auth; private ones need a token
     - example:
            python src/data/fetch_external_dataset.py huggingface \\
                --repo keremberke/license-plate-object-detection

After downloading, run:
    python src/training/train_plate_detector_combined.py
to combine with the local mock dataset and re-train YOLOv8.

NOTE: Only download Thai-specific datasets. Verify the license_plate.country
column or dataset name before training -- mixing non-Thai data degrades
recognition on Thai plates.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "plate_dataset_ext"


def fetch_roboflow(api_key: str, workspace: str, project: str, version: int):
    """Download a Roboflow Universe dataset in YOLOv8 format."""
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Roboflow SDK not installed. Run:  pip install roboflow")
        sys.exit(1)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    rf = Roboflow(api_key=api_key)
    proj = rf.workspace(workspace).project(project)
    ds = proj.version(version).download("yolov8", location=str(OUT_DIR))
    print(f"Downloaded -> {ds.location}")


def fetch_huggingface(repo: str, token: str | None = None):
    """Download a HuggingFace dataset and lay it out as YOLO format."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("HuggingFace datasets not installed. Run:  pip install datasets")
        sys.exit(1)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "images" / "train").mkdir(parents=True)
    (OUT_DIR / "images" / "val").mkdir(parents=True)
    (OUT_DIR / "labels" / "train").mkdir(parents=True)
    (OUT_DIR / "labels" / "val").mkdir(parents=True)

    ds = load_dataset(repo, token=token)
    print(f"Loaded HF dataset with splits: {list(ds.keys())}")
    # The actual coercion to YOLO format depends on the dataset schema.
    # This is a placeholder; the user must adapt to the specific dataset.
    print("NOTE: HuggingFace adapter requires per-dataset schema mapping. "
          "Edit this function to match the field names of your dataset "
          "(image, objects.bbox, objects.category) and write YOLO .txt files.")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="source", required=True)

    rf = sub.add_parser("roboflow", help="Download from Roboflow Universe")
    rf.add_argument("--api-key", required=True)
    rf.add_argument("--workspace", required=True)
    rf.add_argument("--project", required=True)
    rf.add_argument("--version", type=int, required=True)

    hf = sub.add_parser("huggingface", help="Download from HuggingFace Datasets")
    hf.add_argument("--repo", required=True)
    hf.add_argument("--token", default=None)

    args = p.parse_args()
    if args.source == "roboflow":
        fetch_roboflow(args.api_key, args.workspace, args.project, args.version)
    elif args.source == "huggingface":
        fetch_huggingface(args.repo, args.token)


if __name__ == "__main__":
    main()
