"""
================================================================
 DEEP ALPR · ทำความเข้าใจการเทรน OCR แบบลึกซึ้ง
================================================================

นี่คือไฟล์สำเนาของ src/training/train_ocr.py พร้อม comment ภาษาไทย
ละเอียดทุกบรรทัด เพื่อให้คุณเข้าใจว่า "เทรน AI" จริงๆ คือทำอะไร

อ่านไฟล์นี้จากบนลงล่าง ทุกคำที่ comment อธิบายไว้คือศัพท์มาตรฐานในวงการ
จำให้ขึ้นใจ จะใช้ในทุกโปรเจกต์ AI ต่อจากนี้
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
from alpr.charset import NUM_CLASSES, decode, encode
from alpr.crnn import CRNN


# ============================================================
# ส่วนที่ 1: HYPERPARAMETERS (ค่าตั้งต้นที่คนกำหนด ไม่ใช่ AI เรียนเอง)
# ============================================================
# Hyperparameter คือตัวเลขที่คนเลือก ตรงข้ามกับ "parameters" (weights)
# ที่ AI เรียนเอง. การเลือก hyperparameter ดีๆ คือทักษะของ ML engineer.

DATA = ROOT / "data" / "ocr_dataset"
MODEL_PATH = ROOT / "models" / "ocr_crnn.pt"   # ไฟล์ปลายทาง 3.63 MB
LOG_PATH = ROOT / "models" / "ocr_train_log.txt"

IMG_H, IMG_W = 32, 200
# ภาพ input ของโมเดลคงที่ 32x200 px. ทำไม?
#  - 32 เพราะ CRNN ของเราออกแบบให้ CNN ลดขนาดเหลือ 1 row พอดี
#  - 200 เพราะป้ายไทยกว้างกว่าสูงประมาณ 6 เท่า

EPOCHS = 25
# Epoch = "การดูข้อมูลครบ 1 รอบ". 25 epoch = AI เห็นภาพทุกใบ 25 ครั้ง
# ครั้งแรกๆ AI ยังโง่ ทายมั่ว. ครั้งหลังๆ ตัวเลข weights ปรับจน AI เก่ง

BATCH = 96
# Batch = "ดูทีละกี่ภาพแล้วค่อยปรับ weights". BATCH=96 หมายถึง:
#   1. เอาภาพ 96 ใบเข้าโมเดลพร้อมกัน
#   2. ดูว่าทายผิดแค่ไหน (loss)
#   3. ปรับ weights 1 ครั้ง
# ทำไมไม่ปรับทีละภาพ? เพราะ GPU มี parallel power คำนวณ 96 ภาพพร้อมกันได้
# ใน GPU เวลาเดียวกับ 1 ภาพ. ใหญ่กว่านี้จะกิน VRAM เกิน

LR = 1e-3
# Learning Rate = ขนาดของ "ก้าวเดิน" ตอนปรับ weights
# 0.001 หมายถึง: ทุกรอบขยับ weights ทีละ 0.1% ของทิศที่ดีขึ้น
# ใหญ่ไป → กระโดดข้ามจุดที่ดีที่สุด, เล็กไป → ไปไม่ถึงในเวลาที่กำหนด
# คือ hyperparameter ที่ critical ที่สุด

EARLY_STOP_PATIENCE = 5
# ถ้า val accuracy ไม่ดีขึ้นต่อกัน 5 epoch ให้หยุด
# กันเปลือง resource และกันโมเดล overfit

# device = "ใช้ GPU ถ้ามี ไม่งั้น CPU"
# ทุก tensor (matrix) ที่จะคำนวณต้องโยนไปอยู่ device เดียวกัน
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# ส่วนที่ 2: DATASET (ตำราที่ AI จะใช้เรียน)
# ============================================================

class OCRDataset(Dataset):
    """
    PyTorch Dataset = wrapper บอกว่า "ดึงตัวอย่างที่ index i ออกมายังไง"
    ต้องมี 2 method หลัก: __len__ และ __getitem__
    """
    def __init__(self, split: str):
        # split คือ "train", "val", หรือ "test"
        self.dir = DATA / split
        # อ่านไฟล์ labels: ทุกบรรทัดเป็น "<filename>\t<text>"
        lines = (DATA / f"{split}_labels.txt").read_text(encoding="utf-8").splitlines()
        self.items = [ln.split("\t") for ln in lines if ln.strip()]

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        # PyTorch จะเรียก method นี้ตอน loop ผ่าน dataset
        fname, text = self.items[i]

        # 1) โหลดภาพ + แปลงเป็น grayscale + resize ขนาดคงที่
        img = Image.open(self.dir / fname).convert("L").resize((IMG_W, IMG_H))

        # 2) แปลงเป็น numpy array แล้ว normalize ให้อยู่ในช่วง [-1, 1]
        # ทำไม normalize? เพราะ neural network ทำงานดีกับเลขใกล้ๆ 0
        # /255 → [0, 1]    - 0.5 → [-0.5, 0.5]    / 0.5 → [-1, 1]
        arr = (np.asarray(img, dtype=np.float32) / 255.0 - 0.5) / 0.5

        # 3) แปลง numpy → tensor และเพิ่ม channel dimension
        # shape: (H, W) → (1, H, W) เพราะ CNN รับ (channel, height, width)
        image_tensor = torch.from_numpy(arr).unsqueeze(0)

        # 4) แปลงข้อความ "1กข234" → list ของตัวเลข [1, 24, 25, 2, 3, 4]
        # encode() อยู่ใน charset.py ใช้ CHAR_TO_IDX map
        target_tensor = torch.tensor(encode(text))

        return image_tensor, target_tensor, text


def collate(batch):
    """
    Collate function = วิธีรวม sample หลายๆ ตัวเป็น batch เดียว
    DataLoader จะเรียกฟังก์ชันนี้หลังจากดึง __getitem__ ทีละตัว

    batch คือ list ของ (image, target, text) ที่ได้จาก __getitem__
    """
    imgs, targets, texts = zip(*batch)

    # length ของ target แต่ละตัวอาจไม่เท่ากัน (บาง plate มี 5 ตัว บางใบ 7)
    # CTC loss ต้องรู้ความยาว target ของแต่ละ sample
    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)

    # stack ภาพทั้ง batch เป็น tensor เดียว shape: (BATCH, 1, H, W)
    # cat target ทั้งหมดต่อกันเป็น vector ยาวๆ (CTC loss ทำงานแบบนี้)
    return torch.stack(imgs), torch.cat(targets), target_lengths, texts


# ============================================================
# ส่วนที่ 3: DECODING (แปลผลที่โมเดลทำนายกลับเป็นข้อความ)
# ============================================================

def greedy_decode(logits: torch.Tensor) -> list[str]:
    """
    CTC greedy decode: argmax → collapse repeats → drop blanks

    Logits คืออะไร?
      โมเดลทำนายไม่ใช่ตัวอักษรตรงๆ แต่เป็น "ความน่าจะเป็น" ของทุก class
      shape: (W, B, C)  W=ตำแหน่งใน sequence, B=batch, C=จำนวน class

    ตัวอย่าง logits ของตำแหน่งหนึ่ง (53 class):
      [0.001, 0.002, ..., 0.94, 0.01, ...]
                           ↑
                       class "ก" = 0.94

    Greedy = แค่หยิบ class ที่ probability สูงสุด ที่แต่ละตำแหน่ง

    Collapse repeats: CTC ออกแบบให้ทำนายซ้ำได้เพื่อ align กับภาพ
       เช่น "กกก ข ข ขข" (space = blank) → "กข ขข" → "กขข"
       ดังนั้นต้อง: collapse ซ้ำ → ทิ้ง blank
    """
    args = logits.argmax(2).permute(1, 0).tolist()   # (B, W) แปลงเป็น Python list
    out = []
    for seq in args:
        collapsed, prev = [], 0
        for idx in seq:
            # idx != prev: ไม่ใช่ตัวซ้ำกับก่อนหน้า
            # idx != 0: ไม่ใช่ blank token (เก็บไว้เป็น class 0)
            if idx != prev and idx != 0:
                collapsed.append(idx)
            prev = idx
        out.append(decode(collapsed))
    return out


def levenshtein(a: str, b: str) -> int:
    """
    คำนวณ edit distance ระหว่าง 2 string
    คือ "ต้องแก้กี่ตัวอักษร" เพื่อแปลง a เป็น b

    ใช้คำนวณ CER (Character Error Rate) = แม่นยำระดับตัวอักษร
    """
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1,
                        prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[n]


# ============================================================
# ส่วนที่ 4: EVALUATION (วัดความเก่งของนักเรียนตอนจบ epoch)
# ============================================================

@torch.no_grad()
def evaluate(model, loader):
    """
    @torch.no_grad() = ปิด autograd ระหว่าง eval
       ปกติทุก operation PyTorch จะจำไว้เพื่อคำนวณ gradient
       แต่ตอน eval เราไม่ปรับ weights แล้ว ปิดได้ เร็วขึ้น+ประหยัด RAM
    """
    model.eval()
    # model.eval() = บอกโมเดลว่า "นี่คือโหมดทดสอบ"
    # บาง layer เช่น Dropout, BatchNorm จะ behave ต่างกันใน train vs eval

    exact = total = cer_num = cer_den = 0
    for imgs, _, _, texts in loader:
        # forward pass: เอาภาพเข้าโมเดล แล้วได้ predict
        # .to(device) = ย้าย tensor ไป GPU/CPU
        # .cpu() = ย้ายกลับมา CPU เพื่อ decode (decoding ทำใน Python ไม่ใช่ GPU)
        preds = greedy_decode(model(imgs.to(device)).cpu())

        for p, g in zip(preds, texts):
            total += 1
            exact += int(p == g)                    # นับ exact match
            cer_num += levenshtein(p, g)           # ผิดกี่ตัว
            cer_den += max(len(g), 1)              # ความยาวจริง
    return exact / total, cer_num / cer_den


def log(msg: str):
    """พิมพ์ message ทั้งใน console และ append ใน log file"""
    print(msg, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# ============================================================
# ส่วนที่ 5: ⭐ THE TRAINING LOOP ⭐ (ใจกลางของ "การเทรน")
# ============================================================
# ตรงนี้คือที่ที่ AI "เรียน" จริงๆ ทุกบรรทัดมีความหมาย

def main():
    # Seed = ตั้งเลขสุ่มให้คงที่ ทำให้รันแล้วได้ผลเดิม (reproducible)
    torch.manual_seed(42)
    random.seed(42)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    log(f"Device: {device} | classes: {NUM_CLASSES}")

    # ---- 5.1 สร้าง DataLoader ที่จะ feed ข้อมูลเป็น batch ----
    # shuffle=True ใน train เพื่อให้ AI ไม่จำลำดับของข้อมูล
    train_loader = DataLoader(OCRDataset("train"), batch_size=BATCH,
                              shuffle=True, collate_fn=collate)
    val_loader = DataLoader(OCRDataset("val"), batch_size=BATCH, collate_fn=collate)

    # ---- 5.2 สร้าง 3 องค์ประกอบหลักของ training ----

    # MODEL = นักเรียน (ตอนนี้ weights ทั้ง 600,000+ ตัว สุ่มมา)
    model = CRNN(NUM_CLASSES).to(device)

    # LOSS FUNCTION = "วิธีวัดว่าผิดแค่ไหน"
    # CTC = Connectionist Temporal Classification
    # ออกแบบมาเพื่อ problem ที่ output มีหลายตัว แต่ไม่รู้แต่ละตัวอยู่ตำแหน่งไหน
    # (perfect สำหรับ OCR ที่ตัวอักษรในภาพไม่ align กับ timesteps ตรงๆ)
    ctc = torch.nn.CTCLoss(blank=0, zero_infinity=True)

    # OPTIMIZER = "วิธีปรับ weights"
    # Adam = ตัวที่ใช้กันมากสุดในปี 2026 (ปรับ learning rate อัตโนมัติต่อ weight)
    opt = torch.optim.Adam(model.parameters(), lr=LR)

    # SCHEDULER = "วิธีลด learning rate เมื่อเวลาผ่านไป"
    # ตอนเริ่มก้าวใหญ่ ตอนใกล้จบก้าวเล็กให้ละเอียด
    # Cosine = ลดแบบ cosine curve (smooth, ใช้กันเยอะ)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS, eta_min=1e-5)

    best = 0.0
    stale = 0

    # ---- 5.3 ⭐ EPOCH LOOP (วงนอก ทบทวนทั้ง dataset 25 ครั้ง) ⭐ ----
    for epoch in range(1, EPOCHS + 1):
        model.train()
        # model.train() = บอกโมเดลว่า "นี่คือโหมดเรียน"
        # เปิด Dropout, ใช้ BatchNorm running stats แบบที่ถูก

        t0, running = time.time(), 0.0

        # ---- 5.4 ⭐ BATCH LOOP (วงใน ดูทีละ 96 ภาพ) ⭐ ----
        for imgs, targets, target_lengths, _ in train_loader:

            # ----- ขั้นตอน A: FORWARD PASS -----
            # เอาภาพเข้าโมเดล → ได้ logits ออกมา
            # นี่คือ "นักเรียนทาย"
            logits = model(imgs.to(device))                       # shape: (W, B, C)

            # input_lengths บอก CTC ว่า sequence ยาวเท่าไหร่ (timesteps)
            # ของเราคงที่ที่ W เพราะภาพคงที่
            input_lengths = torch.full((imgs.size(0),),
                                       logits.size(0), dtype=torch.long)

            # ----- ขั้นตอน B: COMPUTE LOSS -----
            # คำนวณ "ผิดแค่ไหน" เทียบ predict กับ ground truth
            # นี่คือ "ครูเช็คคำตอบ"
            loss = ctc(logits, targets, input_lengths, target_lengths)

            # ----- ขั้นตอน C: BACKWARD PASS (★ สำคัญที่สุด ★) -----
            # นี่คือ "นักเรียนเรียนรู้จากความผิด"

            opt.zero_grad()
            # ล้าง gradient เก่าทิ้ง (PyTorch สะสม gradient ถ้าไม่ล้าง)

            loss.backward()
            # ★ MAGIC HAPPENS HERE ★
            # คำสั่งนี้ทำสิ่งซับซ้อนมากในบรรทัดเดียว:
            #   1. คำนวณว่า weights ทุกตัวควรขยับทิศไหนเพื่อลด loss
            #   2. ทำด้วย chain rule ของแคลคูลัส (backpropagation)
            #   3. เก็บผลไว้ใน .grad ของทุก parameter
            # ถ้าเข้าใจบรรทัดนี้ลึก = เข้าใจ neural network 80%

            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            # ตัด gradient ที่ใหญ่เกิน 5 ทิ้ง
            # กัน "exploding gradient" ที่ทำ training พัง

            opt.step()
            # ★ อัปเดต weights จริง! ★
            # ใช้ gradient ที่คำนวณไว้ * learning rate มาขยับทุก parameter
            # หลังบรรทัดนี้ weights ของโมเดล "ดีขึ้น" นิดนึง

            running += loss.item()
            # .item() แปลง tensor 1 ตัว → Python float (สำหรับ logging)

        # ---- 5.5 จบ epoch: ลด learning rate + ประเมินผล ----
        sched.step()                                # ลด LR ตาม schedule

        # ดูว่าตอนนี้นักเรียนเก่งแค่ไหนบน val set (ข้อมูลที่ไม่เคยเห็น)
        acc, cer = evaluate(model, val_loader)
        log(f"epoch {epoch:2d}/{EPOCHS} | loss {running / len(train_loader):.3f} "
            f"| val_acc {acc * 100:.2f}% | val_CER {cer * 100:.2f}% "
            f"| {time.time() - t0:.0f}s")

        # ---- 5.6 บันทึก best model + early stop ----
        if acc > best:
            best = acc
            stale = 0
            # ★ SAVE MODEL ★
            # บันทึก weights ทั้งหมด + metadata ลงไฟล์ .pt
            # นี่คือ "เปิดสมุดสมองนักเรียนเก็บ"
            # ทุกครั้งที่ดีขึ้นเขียนทับของเก่า → ได้ best version
            torch.save({"model_state": model.state_dict(),
                        "num_classes": NUM_CLASSES,
                        "img_height": IMG_H, "img_width": IMG_W},
                       MODEL_PATH)
        else:
            stale += 1
            if stale >= EARLY_STOP_PATIENCE:
                log(f"Early stop at epoch {epoch}: no improvement "
                    f"for {EARLY_STOP_PATIENCE} epochs.")
                break

    log(f"DONE. best val_acc {best * 100:.2f}% -> {MODEL_PATH}")


if __name__ == "__main__":
    main()


# ============================================================
# สรุปวงจรการเทรน (ท่องให้ได้ขึ้นใจ)
# ============================================================
#
# for each EPOCH:                        ← ทบทวนตำราทั้งเล่ม
#     for each BATCH of data:            ← ดูทีละ 96 ภาพ
#         1. forward pass                ← นักเรียนทาย
#         2. compute loss                ← วัดว่าผิดแค่ไหน
#         3. backward pass               ← คำนวณว่าควรปรับยังไง
#         4. optimizer.step()            ← ปรับ weights จริง
#     evaluate on val set                ← ดูว่าเก่งขึ้นไหม
#     save if improved                   ← เก็บ best
#
# คือทั้งหมดเลย. ทุก deep learning task ในโลก ตั้งแต่ ChatGPT ถึงรถอัตโนมัติ
# ใช้วงจรนี้แทบจะเหมือนกันหมด. ต่างกันแค่ model, data, loss function
# ============================================================
