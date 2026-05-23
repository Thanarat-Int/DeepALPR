"""HSV-based vehicle color classifier.

We don't need ML for this: ~10 canonical colors covers the entire passenger
fleet on Thai roads (white, black, grey, silver, red, blue, green, yellow,
orange, brown). HSV is more stable than RGB across lighting changes because
brightness is on its own axis (V), so we can detect "this is red" even when
the photo is dim.

Returns:
    (label, confidence)   confidence is a rough 0..1 score based on how many
                          pixels matched the dominant bin.
"""
from __future__ import annotations

import cv2
import numpy as np

# Canonical palette (label, Thai label, hue_range[s], min_saturation, brightness_range)
# Hue in OpenCV: 0..179 (red wraps around 0 and 179).
_COLORS = [
    # (label_en, label_th, hue_ranges, sat_min, val_min, val_max)
    ("white",  "ขาว",     [],                       0,    195, 255),  # near-white
    ("black",  "ดำ",      [],                       0,    0,   40),   # very dark
    ("gray",   "เทา",     [],                       0,    50,  170),  # mid grey
    ("silver", "เงิน",    [],                       0,    170, 220),  # bright grey
    ("red",    "แดง",     [(0, 10), (160, 179)],    70,   60,  255),
    ("orange", "ส้ม",     [(10, 22)],               70,   80,  255),
    ("yellow", "เหลือง",  [(22, 35)],               70,   100, 255),
    ("green",  "เขียว",   [(35, 85)],               40,   40,  255),
    ("blue",   "น้ำเงิน", [(85, 130)],              40,   30,  255),
    ("brown",  "น้ำตาล",  [(8, 25)],                50,   30,  100),
]


def _vehicle_roi(crop: np.ndarray) -> np.ndarray:
    """Trim the crop to the body area (avoid wheels + ground).

    Keep the middle horizontal band: top 15% off (cuts roof/sky), bottom 30%
    off (cuts wheels/shadow). That leaves the side/hood/door panels where the
    paint is most clearly visible.
    """
    h, w = crop.shape[:2]
    y1 = int(h * 0.15)
    y2 = int(h * 0.70)
    x1 = int(w * 0.10)
    x2 = int(w * 0.90)
    if y2 <= y1 or x2 <= x1:
        return crop
    return crop[y1:y2, x1:x2]


def classify_color(bgr_crop: np.ndarray) -> tuple[str, str, float]:
    """Return (label_en, label_th, confidence) for a vehicle crop.

    bgr_crop is the OpenCV-format vehicle region (NOT the plate -- it should
    cover body panels). Returns ('unknown', '', 0.0) if the crop is empty.
    """
    if bgr_crop is None or bgr_crop.size == 0:
        return "unknown", "", 0.0

    roi = _vehicle_roi(bgr_crop)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    total = H.size

    scores = []
    for label_en, label_th, hue_ranges, sat_min, val_min, val_max in _COLORS:
        if not hue_ranges:                 # achromatic (white/black/gray/silver)
            # Treat near-zero saturation as "no hue" -> classify by brightness
            mask = (S < 45) & (V >= val_min) & (V <= val_max)
        else:
            hue_mask = np.zeros_like(H, dtype=bool)
            for lo, hi in hue_ranges:
                hue_mask |= (H >= lo) & (H <= hi)
            mask = hue_mask & (S >= sat_min) & (V >= val_min) & (V <= val_max)
        scores.append((mask.sum() / total, label_en, label_th))

    scores.sort(reverse=True)
    best_ratio, best_en, best_th = scores[0]
    # Require >= 18% of pixels in the dominant bin to commit to a colour;
    # below that the lighting is too ambiguous and we keep "unknown" rather
    # than report a wrong colour confidently.
    if best_ratio < 0.18:
        return "unknown", "", float(best_ratio)
    return best_en, best_th, float(min(best_ratio * 2.2, 1.0))


def vehicle_bbox_from_plate(plate_bbox, frame_shape) -> tuple[int, int, int, int]:
    """Estimate the vehicle bounding box from the plate bbox.

    The Thai plate sits at the front-low (or rear-low) of the vehicle. The
    vehicle body extends mostly UPWARD and a little sideways. This heuristic
    expands the plate box by an empirical multiplier; it works well enough for
    sampling colour pixels without running a separate vehicle detector.
    """
    fh, fw = frame_shape[:2]
    x1, y1, x2, y2 = (int(v) for v in plate_bbox)
    w, h = x2 - x1, y2 - y1
    # vehicle is roughly 5x wider and 6x taller than the plate, centered
    cx = (x1 + x2) // 2
    vw = int(w * 5.0)
    vh = int(h * 7.0)
    # plate sits about 25% from the bottom of the vehicle
    bottom_offset = int(h * 1.5)
    vx1 = max(0, cx - vw // 2)
    vx2 = min(fw, cx + vw // 2)
    vy2 = min(fh, y2 + bottom_offset)
    vy1 = max(0, vy2 - vh)
    return vx1, vy1, vx2, vy2
