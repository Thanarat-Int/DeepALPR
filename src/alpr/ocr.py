"""CRNN OCR inference for Thai plates.

Wraps the trained CRNN model and exposes read() -> (text, confidence) on a
single plate crop. The pipeline calls this once per frame per track; combining
those readings (multi-frame voting) happens in tracking.Track.
"""
from pathlib import Path

import cv2
import numpy as np
import torch

from alpr.charset import decode
from alpr.crnn import CRNN


class PlateOCR:
    def __init__(self, model_path):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"OCR model not found: {model_path}. "
                f"Run: python src/training/train_ocr.py")
        ckpt = torch.load(model_path, map_location="cpu")
        self.img_h = ckpt["img_height"]
        self.img_w = ckpt["img_width"]
        self.model = CRNN(ckpt["num_classes"])
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        if image.ndim == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.resize(image, (self.img_w, self.img_h))
        arr = (image.astype(np.float32) / 255.0 - 0.5) / 0.5
        return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)

    @torch.no_grad()
    def read(self, image) -> tuple[str, float]:
        """Recognise one plate crop. Returns (text, mean_confidence)."""
        if image is None or getattr(image, "size", 0) == 0:
            return "", 0.0

        logits = self.model(self._preprocess(image))   # (W, 1, C), log-probs
        probs = logits.exp()[:, 0, :]                  # (W, C)
        max_p, args = probs.max(1)

        # CTC greedy decode: collapse repeats, drop blanks, keep char confidences.
        chars, confs, prev = [], [], 0
        for idx, p in zip(args.tolist(), max_p.tolist()):
            if idx != prev and idx != 0:
                chars.append(idx)
                confs.append(p)
            prev = idx

        text = decode(chars)
        confidence = float(np.mean(confs)) if confs else 0.0
        return text, confidence
