"""Compare v1 (4 plate types) vs v2 (8 plate types) on the new test set.

The new test set covers all 8 Thai plate types. v1 was trained on 4 types
only so this benchmark shows the gain from expanding the training corpus.

Run:  python src/eval/compare_models.py
"""
import sys
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
V1_PATH = ROOT / "models" / "ocr_crnn_v1_synth4types.pt"
V2_PATH = ROOT / "models" / "ocr_crnn.pt"
OUT_PATH = ROOT / "models" / "ocr_eval_compare.txt"
IMG_H, IMG_W = 32, 200
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def levenshtein(a, b):
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[n]


def greedy_decode(logits):
    args = logits.argmax(2).permute(1, 0).tolist()
    out = []
    for seq in args:
        col, prev = [], 0
        for idx in seq:
            if idx != prev and idx != 0:
                col.append(idx)
            prev = idx
        out.append(decode(col))
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
            f, txt = ln.split("\t")
            self.items.append((f, txt, meta_map.get(f, "unknown")))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        f, text, ptype = self.items[i]
        img = Image.open(self.dir / f).convert("L").resize((IMG_W, IMG_H))
        arr = (np.asarray(img, dtype=np.float32) / 255.0 - 0.5) / 0.5
        return torch.from_numpy(arr).unsqueeze(0), text, ptype


def coll(batch):
    imgs, texts, types = zip(*batch)
    return torch.stack(imgs), texts, types


def eval_model(path):
    ckpt = torch.load(path, map_location=device, weights_only=True)
    model = CRNN(ckpt["num_classes"]).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    loader = DataLoader(TestDataset(), batch_size=128, collate_fn=coll)
    per_type = defaultdict(lambda: {"e": 0, "n": 0, "c": 0, "d": 0})
    tot_e = tot_n = tot_c = tot_d = 0
    with torch.no_grad():
        for imgs, texts, types in loader:
            preds = greedy_decode(model(imgs.to(device)).cpu())
            for p, g, pt in zip(preds, texts, types):
                b = per_type[pt]
                b["n"] += 1; tot_n += 1
                if p == g: b["e"] += 1; tot_e += 1
                ed = levenshtein(p, g); dn = max(len(g), 1)
                b["c"] += ed; b["d"] += dn; tot_c += ed; tot_d += dn
    return per_type, (tot_e, tot_n, tot_c, tot_d)


def main():
    if not V1_PATH.exists() or not V2_PATH.exists():
        print(f"missing model: v1={V1_PATH.exists()} v2={V2_PATH.exists()}")
        return

    print("Evaluating v1 (4 types) ...")
    v1, (v1e, v1n, v1c, v1d) = eval_model(V1_PATH)
    print("Evaluating v2 (8 types) ...")
    v2, (v2e, v2n, v2c, v2d) = eval_model(V2_PATH)

    lines = ["=" * 72,
             "Deep ALPR - OCR comparison v1 (4 types) vs v2 (8 types)",
             "=" * 72,
             f"Test set: {v1n} samples (covers all 8 Thai plate types)",
             "",
             f"OVERALL  v1  exact = {v1e*100/v1n:.2f}%   CER = {v1c*100/max(v1d,1):.3f}%",
             f"OVERALL  v2  exact = {v2e*100/v2n:.2f}%   CER = {v2c*100/max(v2d,1):.3f}%",
             f"Delta        +{(v2e/v2n - v1e/v1n)*100:.2f} pp",
             "",
             f"{'plate_type':12s}  {'n':>5s}  {'v1_acc':>8s}  {'v2_acc':>8s}  {'delta':>7s}",
             "-" * 56]
    for pt in sorted(set(v1) | set(v2),
                     key=lambda k: -v1.get(k, {"n": 0})["n"]):
        b1, b2 = v1.get(pt, {"e": 0, "n": 0}), v2.get(pt, {"e": 0, "n": 0})
        n = max(b1["n"], b2["n"])
        if n == 0:
            continue
        a1 = b1["e"] * 100 / max(b1["n"], 1)
        a2 = b2["e"] * 100 / max(b2["n"], 1)
        lines.append(f"{pt:12s}  {n:>5d}  {a1:>7.2f}%  {a2:>7.2f}%  "
                     f"{a2-a1:>+6.2f}")
    report = "\n".join(lines)
    print()
    print(report)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(f"\nWritten -> {OUT_PATH}")


if __name__ == "__main__":
    main()
