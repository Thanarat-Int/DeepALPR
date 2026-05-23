"""Evaluation harness -- measures the brief's accuracy requirement.

Part 1  OCR accuracy on the held-out synthetic test set:
          - plate-level exact-match accuracy  (the ">= 95%" metric)
          - character error rate (CER)
          - breakdown by registration length
Part 2  End-to-end sanity check: run the full pipeline on the mock video and
        compare emitted events against the ground-truth sidecar.

Run:  python src/eval/evaluate.py

NOTE: numbers here are measured on SYNTHETIC data. They prove the training,
decoding and pipeline work end-to-end. Real-world certification requires the
same harness pointed at a held-out set of REAL labelled Thai plates.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from alpr.config import CONFIG, resolve  # noqa: E402
from alpr.ocr import PlateOCR  # noqa: E402

TEST_DIR = ROOT / "data" / "ocr_dataset" / "test"
TEST_LABELS = ROOT / "data" / "ocr_dataset" / "test_labels.txt"
TARGET = 95.0


def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[n]


def evaluate_ocr() -> float:
    ocr = PlateOCR(resolve(CONFIG.ocr.model))
    items = [ln.split("\t") for ln in
             TEST_LABELS.read_text(encoding="utf-8").splitlines() if ln.strip()]

    exact = cer_num = cer_den = 0
    by_len, by_len_ok = Counter(), Counter()
    misreads = []
    for fname, gt in items:
        img = np.asarray(Image.open(TEST_DIR / fname).convert("L"))
        pred, _conf = ocr.read(img)
        hit = pred == gt
        exact += hit
        cer_num += levenshtein(pred, gt)
        cer_den += max(len(gt), 1)
        by_len[len(gt)] += 1
        by_len_ok[len(gt)] += hit
        if not hit and len(misreads) < 12:
            misreads.append((gt, pred))

    n = len(items)
    acc = exact / n * 100
    cer = cer_num / cer_den * 100

    print("=" * 56)
    print("  PART 1 -- OCR accuracy (held-out synthetic test set)")
    print("=" * 56)
    print(f"  Samples              : {n}")
    print(f"  Plate-level accuracy : {acc:.2f}%   (target >= {TARGET:.0f}%)")
    print(f"  Character error rate : {cer:.2f}%")
    print(f"  Verdict              : "
          f"{'PASS' if acc >= TARGET else 'BELOW TARGET'}")
    print("  Accuracy by registration length:")
    for length in sorted(by_len):
        ok, tot = by_len_ok[length], by_len[length]
        print(f"    {length} chars : {ok:4d}/{tot:<4d} = {ok / tot * 100:.1f}%")
    if misreads:
        print("  Sample misreads (truth -> predicted):")
        for gt, pred in misreads:
            print(f"    {gt:<10s} -> {pred}")
    return acc


def evaluate_end_to_end():
    print()
    print("=" * 56)
    print("  PART 2 -- end-to-end pipeline on the mock video")
    print("=" * 56)
    video = resolve(CONFIG.capture.source)
    sidecar = video.with_name(video.stem + ".plates.json")
    if not video.exists() or not sidecar.exists():
        print("  (skipped -- run src/data/make_mock_video.py first)")
        return

    data = json.loads(sidecar.read_text(encoding="utf-8"))
    min_w = CONFIG.detection.get("min_plate_width", 0)
    votes = CONFIG.ocr.votes_required

    # "Readable zone": a plate counts as expected only once it has been at a
    # readable size for >= votes frames -- mirrors a real camera trigger zone.
    readable_frames, track_reg = Counter(), {}
    for records in data["frames"].values():
        for r in records:
            track_reg[r["track_id"]] = r["registration"]
            x1, _, x2, _ = r["bbox"]
            if (x2 - x1) >= min_w:
                readable_frames[r["track_id"]] += 1
    expected = {track_reg[t] for t, c in readable_frames.items() if c >= votes}

    from alpr.pipeline import ALPRPipeline
    emitted = []
    pipe = ALPRPipeline(CONFIG, on_event=lambda e: emitted.append(e.plate))
    demo_video = ROOT / "assets" / "demo_output.mp4"
    pipe.run(output_path=demo_video)

    correct = expected & set(emitted)
    rejected = pipe.stats["rejected_fast"]
    in_scope = max(len(expected) - rejected, 1)     # readable AND within speed limit
    print(f"  Plates in readable zone        : {len(expected)}")
    print(f"  Within speed limit (<= {CONFIG.speed.max_speed_kmh} km/h)  : "
          f"{len(expected) - rejected}   ({rejected} gated out -- intended)")
    print(f"  Events emitted                 : {len(emitted)}")
    print(f"  Correct registrations          : {len(correct)}")
    if emitted:
        print(f"  Recognition accuracy           : "
              f"{len(correct) / len(emitted) * 100:.1f}%   (correct / emitted)")
    print(f"  Capture coverage               : "
          f"{len(emitted) / in_scope * 100:.1f}%   (emitted / in-scope)")
    print(f"  Annotated demo video           : {demo_video.name}")


def main():
    acc = evaluate_ocr()
    evaluate_end_to_end()
    print()
    print("Reminder: synthetic-data metrics. Retrain on real labelled plates "
          "for production certification.")
    sys.exit(0 if acc >= TARGET else 1)


if __name__ == "__main__":
    main()
