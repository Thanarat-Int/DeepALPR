"""Plate event model and Thai registration validation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from alpr.charset import DIGITS, THAI_CONSONANTS

_CONS = set(THAI_CONSONANTS)
_DIG = set(DIGITS)


@dataclass
class PlateEvent:
    """A confirmed plate reading, ready for storage / API / webhook."""
    plate: str
    speed_kmh: float
    confidence: float
    timestamp: str
    image_path: str
    track_id: int
    province: str | None = None
    plate_type: str | None = None
    vehicle_color: str | None = None       # HSV-detected ("white", "red", ...)
    vehicle_color_th: str | None = None    # Thai label ("ขาว", "แดง", ...)
    color_conf: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def is_valid_thai_plate(text: str) -> bool:
    """Heuristic sanity check: a Thai registration has at least one consonant,
    at least two digits, contains only plate characters, and is 3-9 chars long.
    Filters OCR garbage before an event is emitted."""
    if not (3 <= len(text) <= 9):
        return False
    cons = sum(c in _CONS for c in text)
    digs = sum(c in _DIG for c in text)
    return cons >= 1 and digs >= 2 and cons + digs == len(text)
