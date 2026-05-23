"""Entry point -- runs the Deep ALPR access-control service.

Starts the detection pipeline (worker thread) together with the REST API and
the web app (Operator Console + Admin Panel).

    python run_service.py            ->  http://127.0.0.1:8000

First run -- seed the demo data:
    python src/data/seed.py
"""
import logging
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from alpr.access import AccessController          # noqa: E402
from alpr.api.server import create_app            # noqa: E402
from alpr.api.webhook import WebhookSender        # noqa: E402
from alpr.config import CONFIG, resolve           # noqa: E402
from alpr.pipeline import ALPRPipeline            # noqa: E402
from alpr.retention import start_retention        # noqa: E402
from alpr.storage.database import Database         # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-14s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("alpr.service")


def main():
    import uvicorn

    db = Database(resolve(CONFIG.storage.db_path))
    if db.count_users() == 0:
        db.create_user("admin", "admin123", "Administrator", "admin")
        log.warning("no users found -- created default admin/admin123. "
                    "Run 'python src/data/seed.py' for the full demo dataset.")

    start_retention(CONFIG, db)        # auto-purge old capture images

    access = AccessController(db)
    webhook = WebhookSender(CONFIG.webhook.url, CONFIG.webhook.retries,
                            CONFIG.webhook.timeout_seconds, CONFIG.webhook.enabled)
    gate_id = CONFIG.gate.get("id", "MAIN-01")
    gate_direction = CONFIG.gate.get("direction", "in")

    pipeline_holder = {}    # forward-ref so on_event can call pipeline methods

    def on_event(plate_event):
        """Pipeline read -> access decision -> store -> webhook."""
        result = access.evaluate(plate_event.plate)
        record = {
            "plate": plate_event.plate,
            "decision": result.decision,
            "direction": gate_direction,
            "reason": result.reason,
            "owner_name": result.owner_name,
            "vehicle_type": result.vehicle_type,
            "brand_model": result.brand_model,
            # Detected colour from image is authoritative; if AI could not
            # decide (e.g. nighttime) fall back to the registered colour.
            "vehicle_color": (plate_event.vehicle_color_th
                              or plate_event.vehicle_color
                              or result.registered_color),
            "vehicle_year": result.vehicle_year,
            # Province: prefer what the camera read; fall back to registered.
            "province": plate_event.province or result.registered_province,
            "color_conf": plate_event.color_conf,
            "speed_kmh": plate_event.speed_kmh,
            "confidence": plate_event.confidence,
            "gate": gate_id,
            "image_path": plate_event.image_path,
            "track_id": plate_event.track_id,
            "timestamp": plate_event.timestamp,
        }
        db.insert_event(record)
        webhook.send(record)
        if pipeline_holder.get("p"):
            pipeline_holder["p"].set_latest_event(record)
        log.info("%-8s %s  (%s)", result.decision.upper(),
                 plate_event.plate, result.reason)

    pipeline = ALPRPipeline(CONFIG, on_event=on_event)
    pipeline_holder["p"] = pipeline

    loop_video = bool(CONFIG.capture.get("loop", False))

    def run_pipeline():
        try:
            pipeline.run(loop=loop_video)
            log.info("pipeline finished -- API stays up for queries")
        except Exception:                          # noqa: BLE001
            log.exception("pipeline crashed")

    threading.Thread(target=run_pipeline, daemon=True, name="pipeline").start()
    log.info("console + API ready at http://%s:%d",
             CONFIG.api.host, CONFIG.api.port)

    app = create_app(db, CONFIG, pipeline=pipeline)
    uvicorn.run(app, host=CONFIG.api.host, port=CONFIG.api.port,
                log_level="warning")


if __name__ == "__main__":
    main()
