"""Unit tests for the Deep ALPR system (code correctness, not model accuracy)."""
from alpr.charset import decode, encode
from alpr.events import is_valid_thai_plate
from alpr.tracking import PlateTracker, iou


# --- charset ---------------------------------------------------------------
def test_charset_roundtrip():
    for s in ["1กก234", "ขข1234", "8ฮฮ99"]:
        assert decode(encode(s)) == s


# --- Thai plate validation -------------------------------------------------
def test_valid_plate_accepts_real_formats():
    assert is_valid_thai_plate("1กก234")
    assert is_valid_thai_plate("ขข1234")


def test_valid_plate_rejects_garbage():
    assert not is_valid_thai_plate("")
    assert not is_valid_thai_plate("1234")        # no consonant
    assert not is_valid_thai_plate("กกก")         # fewer than two digits
    assert not is_valid_thai_plate("ABC123")      # non-plate characters


# --- tracking --------------------------------------------------------------
def test_iou():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0
    assert 0.0 < iou((0, 0, 10, 10), (5, 5, 15, 15)) < 1.0


def test_tracker_keeps_stable_id_across_frames():
    tracker = PlateTracker(iou_threshold=0.3, max_age=5)
    active, _ = tracker.update([(0, 0, 40, 20)], frame_idx=0)
    track_id = active[0].id
    active, _ = tracker.update([(3, 2, 43, 22)], frame_idx=1)   # small move
    assert active[0].id == track_id
    assert active[0].hits == 2


def test_tracker_retires_lost_tracks():
    tracker = PlateTracker(iou_threshold=0.3, max_age=2)
    tracker.update([(0, 0, 40, 20)], 0)
    retired_all = []
    for f in range(1, 6):                          # no detections -> ages out
        _, retired = tracker.update([], f)
        retired_all += retired
    assert any(t.id == 1 for t in retired_all)


def test_speed_estimation_is_positive_when_moving():
    tracker = PlateTracker(iou_threshold=0.1)
    tracker.update([(0, 0, 40, 20)], 0)
    track = tracker.tracks[0]
    for f in range(1, 11):                          # glide 8 px/frame (boxes overlap)
        x = f * 8
        tracker.update([(x, 0, x + 40, 20)], f)
    speed = track.estimate_speed(fps=30.0, meters_per_pixel=0.05)
    assert speed > 0


# --- synthetic data generator ---------------------------------------------
def test_generator_emits_valid_registrations():
    from data.plate_generator import random_registration
    for _ in range(60):
        assert is_valid_thai_plate(random_registration())


# --- access control --------------------------------------------------------
def test_access_controller_decisions(tmp_path):
    from alpr.access import AccessController
    from alpr.storage.database import Database

    db = Database(tmp_path / "t.db")
    db.add_vehicle({"plate": "1กก234", "owner_name": "เจ้าของ",
                    "vehicle_type": "resident"})
    db.add_blacklist("9ขฮ99", "test")
    ac = AccessController(db)

    assert ac.evaluate("1กก234").decision == "granted"
    assert ac.evaluate("9ขฮ99").decision == "denied"
    assert ac.evaluate("ออ1111").decision == "alert"


def test_password_hash_roundtrip():
    from alpr.storage.database import hash_password
    h, salt = hash_password("secret")
    assert hash_password("secret", salt)[0] == h
    assert hash_password("wrong", salt)[0] != h


# --- REST API --------------------------------------------------------------
def test_api_endpoints(tmp_path):
    from fastapi.testclient import TestClient

    from alpr.api.server import create_app
    from alpr.config import CONFIG
    from alpr.storage.database import Database

    db = Database(tmp_path / "test.db")
    db.create_user("admin", "pw123", "Admin", "admin")
    db.insert_event({"plate": "1กก234", "decision": "granted",
                     "timestamp": "2026-01-01T08:00:00"})
    client = TestClient(create_app(db, CONFIG))
    key = CONFIG.api.api_key

    # public health
    assert client.get("/health").json()["status"] == "ok"
    # auth required
    assert client.get("/api/events").status_code == 401
    # static X-API-Key works for machine integration
    events = client.get("/api/events", headers={"X-API-Key": key})
    assert events.status_code == 200 and events.json()[0]["plate"] == "1กก234"
    # username/password login -> bearer token
    login = client.post("/api/auth/login",
                        json={"username": "admin", "password": "pw123"})
    assert login.status_code == 200
    token = login.json()["token"]
    stats = client.get("/api/stats",
                       headers={"Authorization": f"Bearer {token}"}).json()
    assert stats["total_events"] == 1 and stats["granted"] == 1
    # wrong password rejected
    assert client.post("/api/auth/login",
                       json={"username": "admin", "password": "x"}).status_code == 401
