"""Webhook delivery -- pushes plate events to the client's endpoint.

Per the brief the payload carries the registration, the timestamp and the
plate image (base64-encoded). Delivery runs in a background thread with
exponential-backoff retries so it never blocks the detection pipeline.
"""
import base64
import logging
import threading
import time
from pathlib import Path

import requests

log = logging.getLogger("alpr.webhook")


class WebhookSender:
    def __init__(self, url, retries=3, timeout=5, enabled=True):
        self.url = url or ""
        self.retries = retries
        self.timeout = timeout
        self.enabled = bool(enabled and self.url)

    def send(self, event: dict):
        """Fire-and-forget delivery in a daemon thread."""
        if not self.enabled:
            log.info("webhook disabled -- '%s' not pushed (set webhook.url)",
                     event.get("plate"))
            return
        threading.Thread(target=self._deliver, args=(dict(event),),
                         daemon=True).start()

    def _build_payload(self, event: dict) -> dict:
        payload = {
            "plate": event.get("plate"),
            "timestamp": event.get("timestamp"),
            "speed_kmh": event.get("speed_kmh"),
            "confidence": event.get("confidence"),
            "province": event.get("province"),
        }
        img = event.get("image_path")
        if img and Path(img).exists():
            payload["image_base64"] = base64.b64encode(
                Path(img).read_bytes()).decode("ascii")
        return payload

    def _deliver(self, event: dict):
        payload = self._build_payload(event)
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.post(self.url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                log.info("webhook delivered: %s (attempt %d)",
                         event.get("plate"), attempt)
                return
            except Exception as exc:  # noqa: BLE001 -- log and retry any failure
                log.warning("webhook attempt %d/%d failed: %s",
                            attempt, self.retries, exc)
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 10))
        log.error("webhook gave up after %d attempts: %s",
                  self.retries, event.get("plate"))
