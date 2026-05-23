"""Generate the synthetic OCR dataset: train / val / test splits.

Run:  python src/data/make_dataset.py

Output under data/ocr_dataset/:
    train/ val/ test/          grayscale plate crops (PNG)
    {split}_labels.txt         "<filename>\\t<registration>" per line
    {split}_meta.txt           "<filename>\\t<plate_type>" per line (audit only)

The test split is held out -- its registration strings never appear in
train or val -- so accuracy measured on it is a fair generalisation check.

Sampling is stratified across all 8 Thai plate types defined in
plate_generator.PLATE_STYLES so the OCR model sees every visual style
during training. Each type gets at least 5% of the split.
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from data.plate_generator import (  # noqa: E402
    PLATE_STYLES, PROVINCES, crop_registration, random_registration,
    render_full_plate, _augment,
)
from PIL import Image  # noqa: E402

OUT = ROOT / "data" / "ocr_dataset"
SPLITS = {"train": 50000, "val": 5000, "test": 5000}

# Minimum 5% of any split must come from each type so rare types still get
# enough training signal. Above that, weights from PLATE_STYLES decide.
MIN_FRACTION = 0.05


def stratified_type_plan(n: int) -> list[str]:
    """Return a length-n list of plate-type strings, stratified per
    PLATE_STYLES weights with a floor of MIN_FRACTION per type."""
    types = list(PLATE_STYLES)
    weights = [PLATE_STYLES[t]["weight"] for t in types]
    floor = max(1, int(n * MIN_FRACTION))
    counts = {t: floor for t in types}
    remaining = n - floor * len(types)
    if remaining > 0:
        total_w = sum(weights)
        extra = [int(remaining * (w / total_w)) for w in weights]
        for t, e in zip(types, extra):
            counts[t] += e
        # distribute rounding leftover into the most-weighted type
        leftover = n - sum(counts.values())
        counts[types[weights.index(max(weights))]] += leftover
    plan = []
    for t, c in counts.items():
        plan.extend([t] * c)
    random.shuffle(plan)
    return plan


def render_ocr_sample_of_type(text: str, plate_type: str) -> Image.Image:
    """Render an OCR training crop for a specific plate type."""
    plate = {"registration": text,
             "province": random.choice(PROVINCES),
             "plate_type": plate_type}
    crop = crop_registration(render_full_plate(plate)).convert("L")
    # Simulate camera distance: shrink to a random small size; the OCR
    # preprocessor upscales it back to a fixed size before inference.
    if random.random() < 0.75:
        sw = random.randint(70, crop.width)
        sh = max(10, round(sw * crop.height / crop.width))
        crop = crop.resize((sw, sh))
    return _augment(crop)


def main():
    random.seed(42)
    train_strings: set[str] = set()
    val_strings: set[str] = set()

    for split, n in SPLITS.items():
        split_dir = OUT / split
        split_dir.mkdir(parents=True, exist_ok=True)
        labels = []
        meta = []
        type_plan = stratified_type_plan(n)
        type_counts = {t: 0 for t in PLATE_STYLES}

        for i in range(n):
            text = random_registration()
            if split == "val":
                while text in train_strings:
                    text = random_registration()
                val_strings.add(text)
            elif split == "test":
                while text in train_strings or text in val_strings:
                    text = random_registration()
            else:
                train_strings.add(text)

            plate_type = type_plan[i]
            type_counts[plate_type] += 1
            fname = f"{split}_{i:05d}.png"
            render_ocr_sample_of_type(text, plate_type).save(split_dir / fname)
            labels.append(f"{fname}\t{text}")
            meta.append(f"{fname}\t{plate_type}")

            if (i + 1) % 5000 == 0:
                print(f"  {split} {i + 1}/{n}")

        (OUT / f"{split}_labels.txt").write_text("\n".join(labels), encoding="utf-8")
        (OUT / f"{split}_meta.txt").write_text("\n".join(meta), encoding="utf-8")
        print(f"{split:5s}: {n} samples  ->  {split_dir}")
        for t, c in type_counts.items():
            print(f"         {t:11s} {c:>6} ({c*100/n:.1f}%)")

    print(f"Done. Dataset at {OUT}")


if __name__ == "__main__":
    main()
