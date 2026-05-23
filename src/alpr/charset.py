"""Shared character set for Thai license-plate OCR.

Used by both the synthetic data generator and the CRNN model so that label
encoding stays consistent between training and inference.
"""

# Thai consonants that appear on registration plates (common set).
THAI_CONSONANTS = "กขคฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"
DIGITS = "0123456789"

# CTC vocabulary. Index 0 is reserved as the blank label required by CTC loss.
VOCAB = ["<blank>"] + list(DIGITS) + list(THAI_CONSONANTS)
NUM_CLASSES = len(VOCAB)

CHAR_TO_IDX = {c: i for i, c in enumerate(VOCAB)}
IDX_TO_CHAR = {i: c for i, c in enumerate(VOCAB)}


def encode(text: str) -> list[int]:
    """Text -> list of class indices (for CTC targets)."""
    return [CHAR_TO_IDX[c] for c in text]


def decode(indices) -> str:
    """Class indices -> text, dropping the blank label."""
    return "".join(IDX_TO_CHAR[int(i)] for i in indices if int(i) != 0)
