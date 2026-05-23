"""SQLite storage for the Thai ALPR access-control system.

Tables:
    users               operator / admin accounts (hashed passwords)
    registered_vehicles  the whitelist -- residents, staff, registered visitors
    blacklist            flagged plates
    access_events        every passage: plate, decision, owner, image, time

A fresh connection is opened per call so the store is safe to share between
the detection-pipeline thread and the FastAPI request threads.
"""
import hashlib
import secrets
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    display_name  TEXT,
    role          TEXT NOT NULL DEFAULT 'operator',   -- admin | operator
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registered_vehicles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    plate        TEXT NOT NULL,
    owner_name   TEXT,
    unit         TEXT,
    vehicle_type TEXT DEFAULT 'resident',             -- resident | staff | visitor
    brand_model  TEXT,
    color        TEXT,
    vehicle_year INTEGER,
    province     TEXT,
    valid_until  TEXT,
    status       TEXT DEFAULT 'active',               -- active | suspended
    note         TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rv_plate ON registered_vehicles(plate);

CREATE TABLE IF NOT EXISTS blacklist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    plate      TEXT NOT NULL,
    reason     TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bl_plate ON blacklist(plate);

CREATE TABLE IF NOT EXISTS access_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    plate         TEXT NOT NULL,
    decision      TEXT NOT NULL,                      -- granted | denied | alert
    direction     TEXT DEFAULT 'in',
    reason        TEXT,
    owner_name    TEXT,
    vehicle_type  TEXT,
    brand_model   TEXT,                               -- from DB lookup (registered only)
    vehicle_color TEXT,                               -- HSV-detected on every event
    vehicle_year  INTEGER,                            -- from DB lookup
    province      TEXT,                               -- read from plate (mock) / DB lookup
    color_conf    REAL,
    speed_kmh     REAL,
    confidence    REAL,
    gate          TEXT,
    image_path    TEXT,
    track_id      INTEGER,
    timestamp     TEXT NOT NULL,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ae_plate ON access_events(plate);
CREATE INDEX IF NOT EXISTS idx_ae_decision ON access_events(decision);
"""


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """PBKDF2-SHA256 password hash. Returns (hash_hex, salt)."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return digest.hex(), salt


class Database:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)
            self._migrate(c)

    @staticmethod
    def _migrate(c):
        """Add new columns to existing DBs (no-op if already present)."""
        for table, col, decl in [
            ("registered_vehicles", "vehicle_year",  "INTEGER"),
            ("registered_vehicles", "province",      "TEXT"),
            ("access_events",       "brand_model",   "TEXT"),
            ("access_events",       "vehicle_color", "TEXT"),
            ("access_events",       "vehicle_year",  "INTEGER"),
            ("access_events",       "province",      "TEXT"),
            ("access_events",       "color_conf",    "REAL"),
        ]:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
            except sqlite3.OperationalError:
                pass        # column already exists

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # --- users ------------------------------------------------------------
    def create_user(self, username, password, display_name, role="operator"):
        pw_hash, salt = hash_password(password)
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO users (username, password_hash, salt, display_name, role) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, pw_hash, salt, display_name, role))
            return cur.lastrowid

    def verify_user(self, username, password) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM users WHERE username = ?",
                            (username,)).fetchone()
        if not row:
            return None
        expected, _ = hash_password(password, row["salt"])
        if not secrets.compare_digest(expected, row["password_hash"]):
            return None
        return {"id": row["id"], "username": row["username"],
                "display_name": row["display_name"], "role": row["role"]}

    def list_users(self) -> list[dict]:
        with self._conn() as c:
            return [{"id": r["id"], "username": r["username"],
                     "display_name": r["display_name"], "role": r["role"],
                     "created_at": r["created_at"]}
                    for r in c.execute("SELECT * FROM users ORDER BY id").fetchall()]

    def count_users(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def get_user_by_id(self, user_id: int) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT id, username, display_name, role, created_at "
                            "FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def update_user(self, user_id: int, display_name=None, role=None, password=None):
        fields, args = [], []
        if display_name is not None:
            fields.append("display_name = ?"); args.append(display_name)
        if role is not None:
            fields.append("role = ?"); args.append(role)
        if password:
            pw_hash, salt = hash_password(password)
            fields.append("password_hash = ?"); args.append(pw_hash)
            fields.append("salt = ?"); args.append(salt)
        if not fields:
            return
        args.append(user_id)
        with self._conn() as c:
            c.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", args)

    def delete_user(self, user_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def change_password(self, user_id: int, new_password: str):
        pw_hash, salt = hash_password(new_password)
        with self._conn() as c:
            c.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                      (pw_hash, salt, user_id))

    # --- registered vehicles ---------------------------------------------
    def add_vehicle(self, data: dict) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO registered_vehicles "
                "(plate, owner_name, unit, vehicle_type, brand_model, color, "
                " vehicle_year, province, valid_until, status, note) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (data["plate"], data.get("owner_name"), data.get("unit"),
                 data.get("vehicle_type", "resident"), data.get("brand_model"),
                 data.get("color"), data.get("vehicle_year"),
                 data.get("province"), data.get("valid_until"),
                 data.get("status", "active"), data.get("note")))
            return cur.lastrowid

    def update_vehicle(self, vid: int, data: dict):
        fields = ["plate", "owner_name", "unit", "vehicle_type", "brand_model",
                  "color", "vehicle_year", "province",
                  "valid_until", "status", "note"]
        sets = ", ".join(f"{f} = ?" for f in fields if f in data)
        if not sets:
            return
        args = [data[f] for f in fields if f in data] + [vid]
        with self._conn() as c:
            c.execute(f"UPDATE registered_vehicles SET {sets} WHERE id = ?", args)

    def delete_vehicle(self, vid: int):
        with self._conn() as c:
            c.execute("DELETE FROM registered_vehicles WHERE id = ?", (vid,))

    def list_vehicles(self, search=None, limit=200, offset=0) -> list[dict]:
        query = "SELECT * FROM registered_vehicles"
        args: list = []
        if search:
            query += " WHERE plate LIKE ? OR owner_name LIKE ? OR unit LIKE ?"
            args += [f"%{search}%"] * 3
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        args += [limit, offset]
        with self._conn() as c:
            return [dict(r) for r in c.execute(query, args).fetchall()]

    def find_registered(self, plate: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM registered_vehicles "
                "WHERE plate = ? AND status = 'active' "
                "AND (valid_until IS NULL OR valid_until = '' OR valid_until >= date('now')) "
                "LIMIT 1", (plate,)).fetchone()
            return dict(row) if row else None

    # --- blacklist --------------------------------------------------------
    def add_blacklist(self, plate, reason) -> int:
        with self._conn() as c:
            cur = c.execute("INSERT INTO blacklist (plate, reason) VALUES (?, ?)",
                            (plate, reason))
            return cur.lastrowid

    def delete_blacklist(self, bid: int):
        with self._conn() as c:
            c.execute("DELETE FROM blacklist WHERE id = ?", (bid,))

    def list_blacklist(self) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT * FROM blacklist ORDER BY id DESC").fetchall()]

    def find_blacklist(self, plate: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM blacklist WHERE plate = ? LIMIT 1",
                            (plate,)).fetchone()
            return dict(row) if row else None

    # --- access events ----------------------------------------------------
    def insert_event(self, event: dict) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO access_events "
                "(plate, decision, direction, reason, owner_name, vehicle_type, "
                " brand_model, vehicle_color, vehicle_year, province, color_conf, "
                " speed_kmh, confidence, gate, image_path, track_id, timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (event["plate"], event["decision"], event.get("direction", "in"),
                 event.get("reason"), event.get("owner_name"),
                 event.get("vehicle_type"),
                 event.get("brand_model"), event.get("vehicle_color"),
                 event.get("vehicle_year"), event.get("province"),
                 event.get("color_conf"),
                 event.get("speed_kmh"),
                 event.get("confidence"), event.get("gate"),
                 event.get("image_path"), event.get("track_id"),
                 event["timestamp"]))
            return cur.lastrowid

    def list_events(self, limit=50, offset=0, plate=None,
                    decision=None, since_id=None) -> list[dict]:
        query = "SELECT * FROM access_events"
        clauses, args = [], []
        if plate:
            clauses.append("plate LIKE ?"); args.append(f"%{plate}%")
        if decision:
            clauses.append("decision = ?"); args.append(decision)
        if since_id:
            clauses.append("id > ?"); args.append(since_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        args += [limit, offset]
        with self._conn() as c:
            return [dict(r) for r in c.execute(query, args).fetchall()]

    def get_event(self, event_id: int) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM access_events WHERE id = ?",
                            (event_id,)).fetchone()
            return dict(row) if row else None

    def update_event_decision(self, event_id: int, decision: str, reason: str):
        with self._conn() as c:
            c.execute("UPDATE access_events SET decision = ?, reason = ? "
                      "WHERE id = ?", (decision, reason, event_id))

    def delete_events_before(self, cutoff_iso: str) -> int:
        """Delete event records older than an ISO timestamp. Returns the count."""
        with self._conn() as c:
            cur = c.execute("DELETE FROM access_events WHERE timestamp < ?",
                            (cutoff_iso,))
            return cur.rowcount

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM access_events").fetchone()[0]
            today = c.execute(
                "SELECT COUNT(*) FROM access_events "
                "WHERE date(timestamp) = date('now')").fetchone()[0]
            by_decision = {r[0]: r[1] for r in c.execute(
                "SELECT decision, COUNT(*) FROM access_events "
                "GROUP BY decision").fetchall()}
            vehicles = c.execute(
                "SELECT COUNT(*) FROM registered_vehicles").fetchone()[0]
            blacklisted = c.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
        return {
            "total_events": total,
            "today_events": today,
            "granted": by_decision.get("granted", 0),
            "denied": by_decision.get("denied", 0),
            "alert": by_decision.get("alert", 0),
            "registered_vehicles": vehicles,
            "blacklisted": blacklisted,
        }

    def report_daily(self, days=7) -> list[dict]:
        """Per-day passage counts for the last N days."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT date(timestamp) AS day, decision, COUNT(*) AS n "
                "FROM access_events WHERE timestamp >= datetime('now', ?) "
                "GROUP BY day, decision", (f"-{days} days",)).fetchall()
        buckets: dict[str, dict] = {}
        for r in rows:
            day = buckets.setdefault(r["day"], {"day": r["day"], "granted": 0,
                                                "denied": 0, "alert": 0})
            day[r["decision"]] = r["n"]
        return sorted(buckets.values(), key=lambda d: d["day"])

    def report_hourly(self, days=7) -> list[dict]:
        """Hour-of-day distribution over the last N days (0..23)."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS hour, "
                "COUNT(*) AS n FROM access_events "
                "WHERE timestamp >= datetime('now', ?) "
                "GROUP BY hour", (f"-{days} days",)).fetchall()
        counts = {r["hour"]: r["n"] for r in rows}
        return [{"hour": h, "n": counts.get(h, 0)} for h in range(24)]

    def report_top_plates(self, limit=10, days=30) -> list[dict]:
        """Most frequent plates with their decision split."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT plate, owner_name, vehicle_type, COUNT(*) AS total, "
                "SUM(CASE WHEN decision='granted' THEN 1 ELSE 0 END) AS granted, "
                "SUM(CASE WHEN decision='denied'  THEN 1 ELSE 0 END) AS denied, "
                "SUM(CASE WHEN decision='alert'   THEN 1 ELSE 0 END) AS alert, "
                "MAX(timestamp) AS last_seen "
                "FROM access_events "
                "WHERE timestamp >= datetime('now', ?) "
                "GROUP BY plate ORDER BY total DESC LIMIT ?",
                (f"-{days} days", limit)).fetchall()
            return [dict(r) for r in rows]

    def report_speed_buckets(self, days=30) -> list[dict]:
        """Distribution of detected speeds in fixed buckets (km/h)."""
        edges = [(0, 10), (10, 20), (20, 30), (30, 35), (35, 999)]
        labels = ["0-10", "10-20", "20-30", "30-35", "35+"]
        out = []
        with self._conn() as c:
            for (lo, hi), label in zip(edges, labels):
                n = c.execute(
                    "SELECT COUNT(*) FROM access_events "
                    "WHERE timestamp >= datetime('now', ?) "
                    "AND speed_kmh >= ? AND speed_kmh < ?",
                    (f"-{days} days", lo, hi)).fetchone()[0]
                out.append({"label": label, "n": n, "over_limit": lo >= 35})
        return out

    def report_ocr_buckets(self, days=30) -> list[dict]:
        """OCR confidence distribution in 10% buckets from 60%..100%."""
        edges = [(0.0, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 1.01)]
        labels = ["<70%", "70-80%", "80-90%", "90-95%", "95-100%"]
        out = []
        with self._conn() as c:
            for (lo, hi), label in zip(edges, labels):
                n = c.execute(
                    "SELECT COUNT(*) FROM access_events "
                    "WHERE timestamp >= datetime('now', ?) "
                    "AND confidence >= ? AND confidence < ?",
                    (f"-{days} days", lo, hi)).fetchone()[0]
                out.append({"label": label, "n": n})
        return out

    def iter_events_for_export(self, date_from=None, date_to=None, decision=None):
        """Stream rows for CSV export. Yields sqlite3.Row objects."""
        clauses, args = [], []
        if date_from:
            clauses.append("date(timestamp) >= ?"); args.append(date_from)
        if date_to:
            clauses.append("date(timestamp) <= ?"); args.append(date_to)
        if decision:
            clauses.append("decision = ?"); args.append(decision)
        sql = ("SELECT id, timestamp, plate, decision, reason, owner_name, "
               "vehicle_type, speed_kmh, confidence, gate, image_path "
               "FROM access_events")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC"
        conn = self._conn()
        try:
            for r in conn.execute(sql, args):
                yield r
        finally:
            conn.close()
