"""FastAPI application for the Deep ALPR access-control system.

Serves:
  * the single-page web app (Operator Console + Admin Panel) from dashboard/
  * a JSON REST API under /api

Auth: UI clients log in for a bearer token; machine integrations may use the
static X-API-Key header instead. Write operations require the admin role.
"""
import logging
from pathlib import Path

import csv
import io
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from alpr.api.auth import identity_from_request, issue_token, revoke_token
from alpr.config import ROOT, resolve

log = logging.getLogger("alpr.api")


class LoginIn(BaseModel):
    username: str
    password: str


def create_app(db, config, pipeline=None) -> FastAPI:
    app = FastAPI(title="Deep ALPR Access Control API", version="2.0.0")
    api_key = config.api.api_key
    image_dir = resolve(config.storage.image_dir)
    dashboard_dir = ROOT / "dashboard"
    app.state.pipeline = pipeline

    # --- auth dependencies ------------------------------------------------
    def require_auth(authorization: str = Header(None),
                     x_api_key: str = Header(None)) -> dict:
        identity = identity_from_request(authorization, x_api_key, api_key)
        if not identity:
            raise HTTPException(401, "authentication required")
        return identity

    def require_admin(identity: dict = Depends(require_auth)) -> dict:
        if identity.get("role") != "admin":
            raise HTTPException(403, "admin role required")
        return identity

    # --- auth -------------------------------------------------------------
    @app.post("/api/auth/login")
    def login(body: LoginIn):
        user = db.verify_user(body.username, body.password)
        if not user:
            raise HTTPException(401, "invalid username or password")
        return {"token": issue_token(user), "user": user}

    @app.post("/api/auth/logout")
    def logout(authorization: str = Header(None)):
        if authorization and authorization.startswith("Bearer "):
            revoke_token(authorization[7:])
        return {"ok": True}

    @app.get("/api/auth/me")
    def me(identity: dict = Depends(require_auth)):
        return identity

    # --- health / dashboard data -----------------------------------------
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "deep-alpr", "version": "2.0.0"}

    @app.get("/api/stats")
    def stats(_: dict = Depends(require_auth)):
        return db.stats()

    @app.get("/api/reports/daily")
    def reports_daily(days: int = Query(7, ge=1, le=31),
                      _: dict = Depends(require_auth)):
        return db.report_daily(days)

    @app.get("/api/reports/hourly")
    def reports_hourly(days: int = Query(7, ge=1, le=31),
                       _: dict = Depends(require_auth)):
        return db.report_hourly(days)

    @app.get("/api/reports/top-plates")
    def reports_top_plates(limit: int = Query(10, ge=1, le=50),
                           days: int = Query(30, ge=1, le=365),
                           _: dict = Depends(require_auth)):
        return db.report_top_plates(limit=limit, days=days)

    @app.get("/api/reports/speed-distribution")
    def reports_speed(days: int = Query(30, ge=1, le=365),
                      _: dict = Depends(require_auth)):
        return db.report_speed_buckets(days)

    @app.get("/api/reports/ocr-distribution")
    def reports_ocr(days: int = Query(30, ge=1, le=365),
                    _: dict = Depends(require_auth)):
        return db.report_ocr_buckets(days)

    @app.get("/api/reports/export")
    def reports_export(date_from: str = Query(None, alias="from"),
                       date_to: str = Query(None, alias="to"),
                       decision: str = Query(None),
                       _: dict = Depends(require_auth)):
        """Stream the filtered access_events table as a CSV download."""

        def row_iter():
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                "id", "timestamp", "plate", "decision", "reason", "owner_name",
                "vehicle_type", "speed_kmh", "confidence", "gate", "image_path",
            ])
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)
            for row in db.iter_events_for_export(date_from, date_to, decision):
                writer.writerow([row[k] if row[k] is not None else "" for k in (
                    "id", "timestamp", "plate", "decision", "reason",
                    "owner_name", "vehicle_type", "speed_kmh", "confidence",
                    "gate", "image_path",
                )])
                yield buf.getvalue()
                buf.seek(0); buf.truncate(0)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return StreamingResponse(
            row_iter(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition":
                     f'attachment; filename="deep_alpr_events_{stamp}.csv"'},
        )

    # --- access events ----------------------------------------------------
    @app.get("/api/events")
    def list_events(limit: int = Query(50, ge=1, le=200), offset: int = 0,
                    plate: str = None, decision: str = None,
                    since_id: int = None, _: dict = Depends(require_auth)):
        return db.list_events(limit=limit, offset=offset, plate=plate,
                              decision=decision, since_id=since_id)

    @app.get("/api/events/{event_id}")
    def get_event(event_id: int, _: dict = Depends(require_auth)):
        event = db.get_event(event_id)
        if not event:
            raise HTTPException(404, "event not found")
        return event

    @app.patch("/api/events/{event_id}")
    def override_event(event_id: int, body: dict,
                       identity: dict = Depends(require_auth)):
        """Operator manually resolves an event (e.g. grants an alert)."""
        if not db.get_event(event_id):
            raise HTTPException(404, "event not found")
        decision = body.get("decision", "granted")
        reason = f"Manual override by {identity.get('display_name', 'operator')}"
        db.update_event_decision(event_id, decision, reason)
        return {"ok": True, "decision": decision}

    @app.get("/api/captures/{name}", include_in_schema=False)
    def capture_image(name: str):
        path = image_dir / Path(name).name        # basename only (no traversal)
        if not path.exists():
            raise HTTPException(404, "image not found")
        return FileResponse(path)

    # --- live camera (real-time annotated frame + last event) ------------
    @app.get("/api/live/snapshot", include_in_schema=False)
    def live_snapshot(_: dict = Depends(require_auth)):
        """Return the latest annotated JPEG produced by the pipeline."""
        p = app.state.pipeline
        if p is None:
            raise HTTPException(503, "pipeline not running")
        jpeg = p.latest_snapshot()
        if jpeg is None:
            raise HTTPException(404, "no frame yet")
        return Response(content=jpeg, media_type="image/jpeg",
                        headers={"Cache-Control": "no-store"})

    @app.get("/api/live/state")
    def live_state(_: dict = Depends(require_auth)):
        """Lightweight JSON status for the Live Camera card (no image)."""
        p = app.state.pipeline
        if p is None:
            return {"running": False, "last_event": None}
        return {
            "running": True,
            "has_frame": p.latest_snapshot() is not None,
            "last_event": p.get_latest_event(),
        }

    # --- gate (simulated) -------------------------------------------------
    @app.post("/api/gate/open")
    def open_gate(body: dict = None, identity: dict = Depends(require_auth)):
        plate = (body or {}).get("plate", "")
        log.info("gate opened manually by %s for %s",
                 identity.get("username"), plate or "-")
        return {"ok": True, "message": "Barrier opened (simulated)"}

    # --- registered vehicles ---------------------------------------------
    @app.get("/api/vehicles")
    def list_vehicles(search: str = None, limit: int = Query(200, ge=1, le=500),
                      offset: int = 0, _: dict = Depends(require_auth)):
        return db.list_vehicles(search=search, limit=limit, offset=offset)

    @app.post("/api/vehicles")
    def add_vehicle(body: dict, _: dict = Depends(require_admin)):
        if not body.get("plate"):
            raise HTTPException(400, "plate is required")
        return {"id": db.add_vehicle(body)}

    @app.put("/api/vehicles/{vehicle_id}")
    def update_vehicle(vehicle_id: int, body: dict,
                       _: dict = Depends(require_admin)):
        db.update_vehicle(vehicle_id, body)
        return {"ok": True}

    @app.delete("/api/vehicles/{vehicle_id}")
    def delete_vehicle(vehicle_id: int, _: dict = Depends(require_admin)):
        db.delete_vehicle(vehicle_id)
        return {"ok": True}

    # --- blacklist --------------------------------------------------------
    @app.get("/api/blacklist")
    def list_blacklist(_: dict = Depends(require_auth)):
        return db.list_blacklist()

    @app.post("/api/blacklist")
    def add_blacklist(body: dict, _: dict = Depends(require_admin)):
        if not body.get("plate"):
            raise HTTPException(400, "plate is required")
        return {"id": db.add_blacklist(body["plate"], body.get("reason", ""))}

    @app.delete("/api/blacklist/{entry_id}")
    def delete_blacklist(entry_id: int, _: dict = Depends(require_admin)):
        db.delete_blacklist(entry_id)
        return {"ok": True}

    # --- users ------------------------------------------------------------
    @app.get("/api/users")
    def list_users(_: dict = Depends(require_admin)):
        return db.list_users()

    @app.post("/api/users")
    def add_user(body: dict, _: dict = Depends(require_admin)):
        if not body.get("username") or not body.get("password"):
            raise HTTPException(400, "username and password are required")
        return {"id": db.create_user(
            body["username"], body["password"],
            body.get("display_name", body["username"]),
            body.get("role", "operator"))}

    @app.put("/api/users/{user_id}")
    def edit_user(user_id: int, body: dict, _: dict = Depends(require_admin)):
        if not db.get_user_by_id(user_id):
            raise HTTPException(404, "user not found")
        db.update_user(user_id,
                       display_name=body.get("display_name"),
                       role=body.get("role"),
                       password=body.get("password") or None)
        return {"ok": True}

    @app.delete("/api/users/{user_id}")
    def remove_user(user_id: int, identity: dict = Depends(require_admin)):
        target = db.get_user_by_id(user_id)
        if not target:
            raise HTTPException(404, "user not found")
        if target["username"] == identity.get("username"):
            raise HTTPException(400, "cannot delete your own account")
        db.delete_user(user_id)
        return {"ok": True}

    @app.post("/api/auth/change-password")
    def change_my_password(body: dict, identity: dict = Depends(require_auth)):
        current = body.get("current_password", "")
        new_pw = body.get("new_password", "")
        if len(new_pw) < 6:
            raise HTTPException(400, "password must be at least 6 characters")
        user = db.verify_user(identity.get("username"), current)
        if not user:
            raise HTTPException(401, "current password is incorrect")
        db.change_password(user["id"], new_pw)
        return {"ok": True}

    # --- webhook test sink -----------------------------------------------
    app.state.webhook_log = []

    @app.post("/api/webhook-sink", include_in_schema=False)
    def webhook_sink(payload: dict):
        app.state.webhook_log.append(payload.get("plate"))
        return {"received": payload.get("plate")}

    # --- static SPA (registered last so /api/* and /health win) ----------
    app.mount("/", StaticFiles(directory=str(dashboard_dir), html=True),
              name="dashboard")
    return app
