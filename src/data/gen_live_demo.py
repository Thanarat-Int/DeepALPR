"""Generate a static demo image for the Live Camera card.

This replaces the looping mock video. The image is a stylised "frame" with
a Thai plate composited onto it so the dashboard always has something
plausible to show -- even when no real CCTV is wired up.

Run:  python src/data/gen_live_demo.py
Output: dashboard/img/live_demo.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from data.plate_generator import render_full_plate, get_font   # noqa: E402

OUT = ROOT / "dashboard" / "img" / "live_demo.jpg"
W, H = 1280, 560
PLATE = {"registration": "1กข234",
         "province": "กรุงเทพมหานคร",
         "plate_type": "private"}


def _gradient(w, h, top, bottom):
    """Vertical gradient from top to bottom (RGB tuples)."""
    img = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # --- background: dusk sky + road -----------------------------------------
    bg = _gradient(W, H, (28, 42, 70), (16, 22, 38))
    draw = ImageDraw.Draw(bg)
    # road tarmac
    road_top = int(H * 0.55)
    road = _gradient(W, H - road_top, (40, 44, 56), (22, 25, 33))
    bg.paste(road, (0, road_top))
    # centre lane line
    for x in range(W // 2 - 220, W // 2 + 220, 60):
        draw.rectangle([x, H - 40, x + 28, H - 34], fill=(180, 180, 180))
    # gate barrier on the right
    draw.rectangle([W - 100, H - 240, W - 80, H - 80], fill=(220, 60, 60))
    draw.rectangle([W - 320, H - 122, W - 100, H - 110], fill=(220, 200, 60))

    # --- vehicle silhouette --------------------------------------------------
    veh = Image.new("RGBA", (520, 280), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(veh)
    # body
    vdraw.rounded_rectangle([20, 80, 500, 250], radius=40, fill=(48, 105, 200))
    # cabin
    vdraw.rounded_rectangle([110, 30, 410, 130], radius=30, fill=(60, 130, 230))
    # windows
    vdraw.rounded_rectangle([130, 50, 250, 120], radius=10, fill=(20, 28, 50))
    vdraw.rounded_rectangle([270, 50, 390, 120], radius=10, fill=(20, 28, 50))
    # wheels
    vdraw.ellipse([60, 200, 160, 280], fill=(20, 20, 20))
    vdraw.ellipse([360, 200, 460, 280], fill=(20, 20, 20))
    # headlights
    vdraw.rounded_rectangle([460, 130, 500, 165], radius=8, fill=(255, 240, 180))
    vdraw.rounded_rectangle([20, 130, 60, 165], radius=8, fill=(255, 240, 180))
    veh = veh.filter(ImageFilter.GaussianBlur(0.5))
    bg.paste(veh, ((W - veh.width) // 2, road_top - 50), veh)

    # --- license plate -------------------------------------------------------
    plate = render_full_plate(PLATE, width=260, height=120)
    bg.paste(plate, ((W - plate.width) // 2, road_top + 90))

    # --- detection bbox ------------------------------------------------------
    px = (W - plate.width) // 2
    py = road_top + 90
    draw.rectangle([px - 4, py - 4, px + plate.width + 4, py + plate.height + 4],
                   outline=(50, 220, 120), width=4)
    # plate text label above the bbox
    label_font = get_font(28)
    label = PLATE["registration"]
    bbox = draw.textbbox((0, 0), label, font=label_font)
    tw = bbox[2] - bbox[0]
    draw.rectangle([px - 4, py - 44, px - 4 + tw + 24, py - 4],
                   fill=(50, 220, 120))
    draw.text((px + 8, py - 40), label,
              font=label_font, fill=(8, 18, 12))
    # speed below
    small = get_font(20)
    draw.text((px - 4, py + plate.height + 8), "12 km/h",
              font=small, fill=(50, 220, 120))

    # --- timestamp + camera label (corner overlays) --------------------------
    corner = get_font(22)
    draw.text((24, 20), "MAIN 01", font=corner, fill=(220, 230, 255))
    draw.text((24, 50), "Live preview", font=corner, fill=(160, 180, 220))

    bg.convert("RGB").save(OUT, "JPEG", quality=88)
    print(f"wrote {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
