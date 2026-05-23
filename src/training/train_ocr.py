"""Train the CRNN Thai-plate OCR model on the synthetic dataset.

Run:  python src/training/train_ocr.py
Saves: models/ocr_crnn.pt  +  models/ocr_train_log.txt

Trained on SYNTHETIC data -- the accuracy reported here proves the training
loop and decoding work. For production accuracy, retrain on real labelled
crops placed under data/ocr_dataset/ with the same layout.
"""
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from alpr.charset import NUM_CLASSES, decode, encode  # noqa: E402
from alpr.crnn import CRNN  # noqa: E402

DATA = ROOT / "data" / "ocr_dataset"
MODEL_PATH = ROOT / "models" / "ocr_crnn.pt"
LOG_PATH = ROOT / "models" / "ocr_train_log.txt"
IMG_H, IMG_W = 32, 200
EPOCHS, BATCH, LR = 25, 96, 1e-3
EARLY_STOP_PATIENCE = 5    # stop if val_acc stops improving for N epochs

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class OCRDataset(Dataset):
    def __init__(self, split: str):
        self.dir = DATA / split
        lines = (DATA / f"{split}_labels.txt").read_text(encoding="utf-8").splitlines()
        self.items = [ln.split("\t") for ln in lines if ln.strip()]

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        fname, text = self.items[i]
        img = Image.open(self.dir / fname).convert("L").resize((IMG_W, IMG_H))
        arr = (np.asarray(img, dtype=np.float32) / 255.0 - 0.5) / 0.5
        return torch.from_numpy(arr).unsqueeze(0), torch.tensor(encode(text)), text


def collate(batch):
    imgs, targets, texts = zip(*batch)
    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    return torch.stack(imgs), torch.cat(targets), target_lengths, texts


def greedy_decode(logits: torch.Tensor) -> list[str]:
    """CTC greedy decode: argmax -> collapse repeats -> drop blanks."""
    args = logits.argmax(2).permute(1, 0).tolist()  # (B, W)
    out = []
    for seq in args:
        collapsed, prev = [], 0
        for idx in seq:
            if idx != prev and idx != 0:
                collapsed.append(idx)
            prev = idx
        out.append(decode(collapsed))
    return out


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


@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    exact = total = cer_num = cer_den = 0
    for imgs, _, _, texts in loader:
        preds = greedy_decode(model(imgs.to(device)).cpu())
        for p, g in zip(preds, texts):
            total += 1
            exact += int(p == g)
            cer_num += levenshtein(p, g)
            cer_den += max(len(g), 1)
    return exact / total, cer_num / cer_den


def log(msg: str):
    print(msg, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main():
    torch.manual_seed(42)
    random.seed(42)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    log(f"Device: {device} | classes: {NUM_CLASSES}")

    train_loader = DataLoader(OCRDataset("train"), batch_size=BATCH,
                              shuffle=True, collate_fn=collate)
    val_loader = DataLoader(OCRDataset("val"), batch_size=BATCH, collate_fn=collate)

    model = CRNN(NUM_CLASSES).to(device)
    ctc = torch.nn.CTCLoss(blank=0, zero_infinity=True)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS, eta_min=1e-5)

    best = 0.0
    stale = 0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        t0, running = time.time(), 0.0
        for imgs, targets, target_lengths, _ in train_loader:
            logits = model(imgs.to(device))  # (W, B, C)
            input_lengths = torch.full((imgs.size(0),), logits.size(0), dtype=torch.long)
            loss = ctc(logits, targets, input_lengths, target_lengths)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            running += loss.item()
        sched.step()

        acc, cer = evaluate(model, val_loader)
        log(f"epoch {epoch:2d}/{EPOCHS} | loss {running / len(train_loader):.3f} "
            f"| val_acc {acc * 100:.2f}% | val_CER {cer * 100:.2f}% "
            f"| {time.time() - t0:.0f}s")
        if acc > best:
            best = acc
            stale = 0
            torch.save({"model_state": model.state_dict(),
                        "num_classes": NUM_CLASSES,
                        "img_height": IMG_H, "img_width": IMG_W}, MODEL_PATH)
        else:
            stale += 1
            if stale >= EARLY_STOP_PATIENCE:
                log(f"Early stop at epoch {epoch}: no val_acc improvement "
                    f"for {EARLY_STOP_PATIENCE} epochs.")
                break

    log(f"DONE. best val_acc {best * 100:.2f}% -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
