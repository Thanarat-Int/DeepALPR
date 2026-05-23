"""Configuration loader. Reads config.yaml and resolves paths against the project root."""
from pathlib import Path
import yaml

# config.py -> src/alpr/config.py ; parents[2] == project root
ROOT = Path(__file__).resolve().parents[2]


class Config:
    """Dict wrapper allowing attribute access: cfg.ocr.img_height."""

    def __init__(self, data: dict):
        self._data = data or {}

    def __getattr__(self, key):
        if key not in self._data:
            raise AttributeError(f"config has no key '{key}'")
        val = self._data[key]
        return Config(val) if isinstance(val, dict) else val

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __repr__(self):
        return f"Config({self._data!r})"


def load_config(path: str | None = None) -> Config:
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return Config(yaml.safe_load(f))


def resolve(path: str) -> Path:
    """Resolve a config-relative path against the project root."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


# Module-level singleton — import as `from alpr.config import CONFIG`
CONFIG = load_config()
