"""Automatic data retention.

Periodically deletes capture images, and optionally event records, that are
older than the configured age, so disk usage stays bounded over time.
Configured under the `retention` section of config.yaml.
"""
import logging
import threading
import time
from datetime import datetime, timedelta

from alpr.config import resolve

log = logging.getLogger("alpr.retention")


def purge_once(config, db) -> tuple[int, int]:
    """Run one retention pass. Returns (images_removed, events_removed)."""
    image_days = config.retention.get("image_days", 0) or 0
    event_days = config.retention.get("event_days", 0) or 0
    images = events = 0

    if image_days > 0:
        cutoff = time.time() - image_days * 86400
        image_dir = resolve(config.storage.image_dir)
        if image_dir.exists():
            for f in image_dir.glob("*.jpg"):
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                        images += 1
                except OSError:
                    pass

    if event_days > 0:
        cutoff_iso = (datetime.now() - timedelta(days=event_days)
                      ).strftime("%Y-%m-%dT%H:%M:%S")
        events = db.delete_events_before(cutoff_iso)

    if images or events:
        log.info("retention: removed %d images, %d event records", images, events)
    return images, events


def start_retention(config, db, interval_hours=6):
    """Run retention now, then every interval_hours, in a daemon thread."""
    if not (config.retention.get("image_days", 0) or
            config.retention.get("event_days", 0)):
        return

    def loop():
        while True:
            try:
                purge_once(config, db)
            except Exception:                       # noqa: BLE001
                log.exception("retention pass failed")
            time.sleep(interval_hours * 3600)

    threading.Thread(target=loop, daemon=True, name="retention").start()
    log.info("retention scheduler started (image_days=%s, every %dh)",
             config.retention.get("image_days", 0), interval_hours)
