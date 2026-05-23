"""Evaluate the trained CRNN per plate type.

Reads data/ocr_dataset/test_labels.txt + test_meta.txt and reports:
  - overall exact-match accuracy and CER
  - per-plate-type breakdown
  - confusion examples (first few mismatches)

Run:  python src/eval/evaluate_per_type.py
"""
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from alpr.charset import NUM_CLASSES, decode  # noqa: E402
from alpr.crnn import CRNN  # noqa: E402

DATA = ROOT / "data" / "ocr_dataset"
MODEL_PATH = ROOT / "models" / "ocr_crnn.pt"
LOG_PATH = ROOT / "models" / "ocr_eval_pertype.txt"
IMG_H, IMG_W = 32, 200
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


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


def greedy_decode(logits: torch.Tensor) -> list[str]:
    args = logits.argmax(2).permute(1, 0).tolist()
    out = []
    for seq in args:
        collapsed, prev = [], 0
        for idx in seq:
            if idx != prev and idx != 0:
                collapsed.append(idx)
            prev = idx
        out.append(decode(collapsed))
    return out


class TestDataset(Dataset):
    def __init__(self):
        self.dir = DATA / "test"
        labels = (DATA / "test_labels.txt").read_text(encoding="utf-8").splitlines()
        meta_path = DATA / "test_meta.txt"
        meta = (meta_path.read_text(encoding="utf-8").splitlines()
                if meta_path.exists() else [])
        meta_map = {ln.split("\t")[0]: ln.split("\t")[1] for ln in meta if ln.strip()}
        self.items = []
        for ln in labels:
            if not ln.strip():
                continue
            fname, text = ln.split("\t")
            self.items.append((fname, text, meta_map.get(fname, "unknown")))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        fname, text, ptype = self.items[i]
        img = Image.open(self.dir / fname).convert("L").resize((IMG_W, IMG_H))
        arr = (np.asarray(img, dtype=np.float32) / 255.0 - 0.5) / 0.5
        return torch.from_numpy(arr).unsqueeze(0), text, ptype


def collate(batch):
    imgs, texts, types = zip(*batch)
    return torch.stack(imgs), texts, types


def main():
    ckpt = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    model = CRNN(NUM_CLASSES).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    loader = DataLoader(TestDataset(), batch_size=128, collate_fn=collate)
    per_type = defaultdict(lambda: {"exact": 0, "total": 0,
                                     "cer_num": 0, "cer_den": 0,
                                     "mistakes": []})
    overall_exact = overall_total = 0
    overall_cer_num = overall_cer_den = 0
    t0 = time.time()
    with torch.no_grad():
        for imgs, texts, types in loader:
            preds = greedy_decode(model(imgs.to(device)).cpu())
            for p, g, ptype in zip(preds, texts, types):
                bucket = per_type[ptype]
                bucket["total"] += 1
                overall_total += 1
                if p == g:
                    bucket["exact"] += 1
                    overall_exact += 1
                else:
                    if len(bucket["mistakes"]) < 5:
                        bucket["mistakes"].append((g, p))
                ed = levenshtein(p, g)
                den = max(len(g), 1)
                bucket["cer_num"] += ed
                bucket["cer_den"] += den
                overall_cer_num += ed
                overall_cer_den += den
    dt = time.time() - t0

    lines = []
    lines.append("=" * 64)
    lines.append("Deep ALPR - OCR per plate-type evaluation")
    lines.append("=" * 64)
    lines.append(f"Model: {MODEL_PATH}")
    lines.append(f"Test set: {overall_total} samples")
    lines.append(f"Wall time: {dt:.1f}s on {device}")
    lines.append("")
    lines.append(f"OVERALL  exact-match = {overall_exact*100/overall_total:.2f}%   "
                 f"CER = {overall_cer_num*100/max(overall_cer_den,1):.3f}%")
    lines.append("")
    lines.append(f"{'plate_type':12s}  {'n':>5s}  {'exact':>7s}  {'CER':>7s}")
    lines.append("-" * 40)
    for ptype, b in sorted(per_type.items(),
                           key=lambda kv: -kv[1]["total"]):
        if b["total"] == 0:
            continue
        acc = b["exact"] * 100 / b["total"]
        cer = b["cer_num"] * 100 / max(b["cer_den"], 1)
        lines.append(f"{ptype:12s}  {b['total']:>5d}  {acc:>6.2f}%  {cer:>6.3f}%")
    lines.append("")
    lines.append("Sample mistakes (gt -> pred):")
    for ptype, b in per_type.items():
        if not b["mistakes"]:
            continue
        lines.append(f"  [{ptype}]")
        for gt, pr in b["mistakes"]:
            lines.append(f"    {gt!r:>18s}  ->  {pr!r}")
    report = "\n".join(lines)
    LOG_PATH.write_text(report, encoding="utf-8")
    # Print via the file's utf-8 encoding so Thai sample mistakes don't crash
    # the default cp874 Windows console.
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode("ascii", "replace").decode("ascii"))
    print(f"\nWritten -> {LOG_PATH}")


if __name__ == "__main__":
    main()
