"""Synthetic Thai license-plate generator -- produces MOCKUP data.

Real CCTV footage of Thai plates is unavailable for this build, so this module
renders plausible synthetic plates instead:

  * registration strings in valid Thai formats (digit + consonants + number)
  * coloured backgrounds per plate type (private / taxi / truck / temporary)
  * a province name on the lower line

Two render paths:
  * render_full_plate()  -> colour plate, for compositing onto the mock video
  * render_ocr_sample()  -> augmented grayscale crop, for OCR model training

NOTE: this is synthetic data. Accuracy measured against it proves the pipeline
and training loop work -- not real-world accuracy. Swap in real labelled crops
under the same folder layout to retrain for production.
"""
from __future__ import annotations

import io
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpr.charset import THAI_CONSONANTS, DIGITS  # noqa: E402

# --- Thai-capable fonts shipped with Windows -------------------------------
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/leelawdb.ttf",   # Leelawadee UI Bold
    "C:/Windows/Fonts/leelawad.ttf",   # Leelawadee UI
    "C:/Windows/Fonts/tahomabd.ttf",   # Tahoma Bold
    "C:/Windows/Fonts/tahoma.ttf",
]


def _find_font() -> str:
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise FileNotFoundError("No Thai-capable font found in C:/Windows/Fonts")


FONT_PATH = _find_font()
_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def get_font(size: int) -> ImageFont.FreeTypeFont:
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = ImageFont.truetype(FONT_PATH, size)
    return _FONT_CACHE[size]


# --- Provinces (subset of the 77 Thai provinces) ---------------------------
PROVINCES = [
    "กรุงเทพมหานคร", "นนทบุรี", "ปทุมธานี", "สมุทรปราการ", "สมุทรสาคร",
    "นครปฐม", "เชียงใหม่", "เชียงราย", "ลำปาง", "พิษณุโลก", "นครสวรรค์",
    "ขอนแก่น", "นครราชสีมา", "อุดรธานี", "อุบลราชธานี", "ชลบุรี", "ระยอง",
    "ฉะเชิงเทรา", "ภูเก็ต", "สงขลา", "สุราษฎร์ธานี", "นครศรีธรรมราช",
    "ประจวบคีรีขันธ์", "เพชรบุรี", "ราชบุรี", "กาญจนบุรี", "พระนครศรีอยุธยา",
    "สระบุรี", "ลพบุรี", "กระบี่",
]

# --- Plate visual styles per type ------------------------------------------
# Eight Thai plate categories covering the public road population.
# bg + fg are RGB; weight is the sampling probability (sum to 1).
# "border" optional, defaults to a dark frame. "invert" plates have light text
# on a dark background -- the CRNN learns polarity invariance from these.
PLATE_STYLES = {
    # private cars: white background, black text (the majority of road traffic)
    "private":     {"bg": (248, 248, 246), "fg": (25, 25, 30),    "weight": 0.30},
    # taxi: bright yellow plate, black text
    "taxi":        {"bg": (243, 201, 48),  "fg": (25, 25, 30),    "weight": 0.10},
    # truck / commercial: muted yellow / cream, black text
    "truck":       {"bg": (250, 196, 78),  "fg": (25, 25, 30),    "weight": 0.10},
    # red plate (newly purchased, awaiting registration)
    "temporary":   {"bg": (250, 250, 250), "fg": (190, 35, 35),
                    "border": (180, 30, 30), "weight": 0.05},
    # motorcycle: white plate similar to private but smaller crop in practice
    "motorcycle":  {"bg": (250, 250, 248), "fg": (25, 25, 30),    "weight": 0.13},
    # government / public agency: white background with grey border accent
    "government":  {"bg": (252, 252, 252), "fg": (25, 25, 30),
                    "border": (120, 120, 120), "weight": 0.07},
    # EV plate: green background, light text (inverse contrast)
    "ev":          {"bg": (50, 140, 80),   "fg": (250, 250, 250),
                    "border": (35, 100, 60), "weight": 0.13, "invert": True},
    # diplomatic / special: orange background, black text
    "diplomatic":  {"bg": (240, 145, 50),  "fg": (25, 25, 30),    "weight": 0.12},
}

# Registration-line sub-region within a full plate, as (x1, y1, x2, y2)
# fractions. The OCR reads ONLY this region; make_mock_video and the OCR
# training crops both use it, so training input == inference input.
REG_REGION = (0.06, 0.05, 0.94, 0.55)


def crop_registration(full_plate: Image.Image) -> Image.Image:
    """Crop the registration-line region out of a full plate image."""
    w, h = full_plate.size
    x1, y1, x2, y2 = REG_REGION
    return full_plate.crop((int(w * x1), int(h * y1),
                            int(w * x2), int(h * y2)))


# --- Registration string generation ----------------------------------------
def random_registration() -> str:
    """Build a modern Thai registration string, e.g. 'กก1234' or '1ขค234'.

    Format: an optional leading digit, exactly two Thai consonants, then a
    2-4 digit running number -- a maximum of 7 characters, matching real
    Thai plates.
    """
    parts: list[str] = []
    if random.random() < 0.40:                       # newer plates lead with a digit
        parts.append(random.choice(DIGITS))
    c1 = random.choice(THAI_CONSONANTS)
    # ~35% of plates use a repeated consonant (กก, ขข, ...). Oversampling these
    # gives the CTC model enough practice decoding adjacent duplicate letters,
    # which it would otherwise collapse into one.
    c2 = c1 if random.random() < 0.35 else random.choice(THAI_CONSONANTS)
    parts.append(c1 + c2)
    n_dig = random.choices([2, 3, 4], weights=[0.15, 0.42, 0.43])[0]
    parts.append("".join(random.choice(DIGITS) for _ in range(n_dig)))
    return "".join(parts)


def random_plate() -> dict:
    """A full plate record: registration + province + type."""
    types = list(PLATE_STYLES)
    weights = [PLATE_STYLES[t]["weight"] for t in types]
    return {
        "registration": random_registration(),
        "province": random.choice(PROVINCES),
        "plate_type": random.choices(types, weights=weights)[0],
    }


# --- Full colour plate (for compositing / detector training) ---------------
def render_full_plate(plate: dict, width: int = 380, height: int = 180) -> Image.Image:
    style = PLATE_STYLES[plate["plate_type"]]
    bg = style["bg"]
    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    border_col = style.get("border", (30, 30, 30))
    border_w = 4 if plate["plate_type"] != "temporary" else 5
    draw.rectangle([2, 2, width - 3, height - 3], outline=border_col, width=border_w)

    reg_font = get_font(int(height * 0.42))
    bbox = draw.textbbox((0, 0), plate["registration"], font=reg_font)
    draw.text(((width - (bbox[2] - bbox[0])) // 2 - bbox[0], int(height * 0.07)),
              plate["registration"], fill=style["fg"], font=reg_font)

    prov_font = get_font(int(height * 0.19))
    pb = draw.textbbox((0, 0), plate["province"], font=prov_font)
    draw.text(((width - (pb[2] - pb[0])) // 2 - pb[0], int(height * 0.63)),
              plate["province"], fill=style["fg"], font=prov_font)
    return img


# --- Augmentation for OCR crops --------------------------------------------
def _augment(img: Image.Image) -> Image.Image:
    """Simulate a real plate crop: rotation, mild perspective, blur, lighting,
    sensor noise and video compression -- the artifacts the pipeline crop
    carries after the frame has been H.264/MP4 encoded.
    """
    fill = int(np.asarray(img).mean())
    img = img.rotate(random.uniform(-4, 4), resample=Image.BILINEAR, fillcolor=fill)

    # Mild perspective skew (camera not perfectly head-on)
    if random.random() < 0.45:
        w, h = img.size
        dx = random.randint(-int(w * 0.04), int(w * 0.04))
        dy = random.randint(-int(h * 0.06), int(h * 0.06))
        coeffs = (1, dy / max(h, 1), 0,  dx / max(w, 1), 1, 0,  0, 0)
        img = img.transform(img.size, Image.AFFINE, coeffs,
                            resample=Image.BILINEAR, fillcolor=fill)

    if random.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(random.uniform(0.2, 1.2)))

    arr = np.asarray(img).astype(np.float32)
    arr *= random.uniform(0.65, 1.25)                       # brightness
    arr += random.uniform(-25, 25)                          # exposure shift
    arr += np.random.normal(0, random.uniform(2, 10), arr.shape)  # sensor noise
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    if random.random() < 0.75:                              # video compression
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(18, 75))
        buf.seek(0)
        img = Image.open(buf).convert("L")
    return img


def render_ocr_sample(text: str, augment: bool = True) -> Image.Image:
    """Render a grayscale OCR training crop.

    The crop is the registration-line region of a full plate -- exactly what
    the pipeline extracts at inference time -- so training and inference see
    the same distribution (background colour, tight framing, scale).
    """
    plate = {
        "registration": text,
        "province": random.choice(PROVINCES),
        "plate_type": random.choices(
            list(PLATE_STYLES),
            weights=[PLATE_STYLES[t]["weight"] for t in PLATE_STYLES])[0],
    }
    crop = crop_registration(render_full_plate(plate)).convert("L")
    if augment:
        # Simulate camera distance: shrink to a random small size (the OCR
        # preprocessor upscales it back to a fixed size before inference).
        if random.random() < 0.75:
            sw = random.randint(70, crop.width)
            sh = max(10, round(sw * crop.height / crop.width))
            crop = crop.resize((sw, sh))
        crop = _augment(crop)
    return crop


if __name__ == "__main__":
    # Quick visual smoke test -> writes a few samples to data/_preview/
    out = Path(__file__).resolve().parents[2] / "data" / "_preview"
    out.mkdir(parents=True, exist_ok=True)
    for i in range(6):
        p = random_plate()
        render_full_plate(p).save(out / f"plate_{i}_{p['plate_type']}.png")
        render_ocr_sample(p["registration"]).save(out / f"ocr_{i}.png")
    print(f"Wrote preview samples to {out}")
