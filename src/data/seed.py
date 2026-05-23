"""Seed the database with mockup data for the access-control demo.

Creates: login accounts, registered vehicles, a blacklist, and a week of
historical access events. Registrations are tied to the plates that appear in
the mock video, so a live pipeline run produces a realistic mix of
granted / denied / alert decisions.

Run:  python src/data/seed.py
"""
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from alpr.config import CONFIG, resolve          # noqa: E402
from alpr.storage.database import Database        # noqa: E402
from data.plate_generator import random_registration  # noqa: E402

THAI_FIRST = ["สมชาย", "สมหญิง", "ธนกร", "ปิยะดา", "วราภรณ์", "ณัฐพล", "กมลชนก",
              "อนุชา", "พิมพ์ชนก", "ศิริพร", "ชัยวัฒน์", "สุดารัตน์", "ภาณุพงศ์",
              "กฤษณะ", "อรอุมา", "ธีรเดช", "นภัสสร", "วิชัย", "เบญจวรรณ", "ฐิติพงษ์"]
THAI_LAST = ["ใจดี", "รุ่งเรือง", "ศรีสุข", "วงศ์สว่าง", "ทองคำ", "พัฒนกุล",
             "มั่นคง", "เจริญสุข", "แสงทอง", "บุญมี", "สุขสันต์", "ไพบูลย์"]
BRANDS = ["Toyota Vios", "Honda Civic", "Mazda 2", "Toyota Yaris", "Honda CR-V",
          "Isuzu D-Max", "Ford Ranger", "Nissan Almera", "MG ZS", "BMW 320d",
          "Tesla Model 3", "Toyota Fortuner", "Honda City", "Mitsubishi Xpander"]
COLORS = ["ขาว", "ดำ", "เทา", "เงิน", "แดง", "น้ำเงิน", "น้ำตาล"]
BL_REASONS = ["ค้างชำระค่าส่วนกลาง", "ยกเลิกสิทธิ์เข้าออก",
              "แจ้งระงับโดยนิติบุคคล", "เคยก่อเหตุในพื้นที่"]


def _name():
    return f"{random.choice(THAI_FIRST)} {random.choice(THAI_LAST)}"


def _unit():
    return random.choice("ABCD") + "/" + str(random.randint(101, 912))


def main():
    random.seed(2026)
    db_path = resolve(CONFIG.storage.db_path)
    if db_path.exists():
        db_path.unlink()                          # fresh seed
    cap_dir = resolve(CONFIG.storage.image_dir)   # clear old plate crops
    if cap_dir.exists():
        for old in cap_dir.glob("*.jpg"):
            old.unlink()
    db = Database(db_path)

    # --- login accounts ---------------------------------------------------
    db.create_user("admin", "admin123", "ผู้ดูแลระบบ", "admin")
    db.create_user("operator", "operator123", "เจ้าหน้าที่ รปภ.", "operator")
    print("users      : admin / admin123   ·   operator / operator123")

    # --- plates from the mock video --------------------------------------
    video = resolve(CONFIG.capture.source)
    sidecar = video.with_name(video.stem + ".plates.json")
    video_plates = []
    plate_province = {}                              # plate -> province
    if sidecar.exists():
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        for recs in data["frames"].values():
            for r in recs:
                plate_province.setdefault(r["registration"], r.get("province"))
        video_plates = sorted(plate_province.keys())
    random.shuffle(video_plates)
    # 30-province pool for plates we invent (not from the video)
    PROVINCES_POOL = [
        "กรุงเทพมหานคร", "นนทบุรี", "ปทุมธานี", "สมุทรปราการ", "นครปฐม",
        "เชียงใหม่", "เชียงราย", "ขอนแก่น", "นครราชสีมา", "อุดรธานี",
        "ชลบุรี", "ระยอง", "ภูเก็ต", "สงขลา", "สุราษฎร์ธานี",
    ]

    # ~65% of video plates registered, 2 blacklisted, rest left unknown
    n_reg = int(len(video_plates) * 0.65)
    registered = video_plates[:n_reg]
    blacklisted = video_plates[n_reg:n_reg + 2]

    # --- registered vehicles (video plates + extra residents) ------------
    reg_records = []
    pool = registered + [random_registration() for _ in range(40)]
    for plate in pool:
        vtype = random.choices(["resident", "staff", "visitor"],
                               weights=[0.7, 0.2, 0.1])[0]
        valid = ""
        if vtype == "visitor":
            valid = (datetime.now() + timedelta(days=random.randint(1, 30))
                     ).strftime("%Y-%m-%d")
        rec = {"plate": plate, "owner_name": _name(), "unit": _unit(),
               "vehicle_type": vtype, "brand_model": random.choice(BRANDS),
               "color": random.choice(COLORS),
               "vehicle_year": random.randint(2015, 2025),
               "province": plate_province.get(plate)
                           or random.choice(PROVINCES_POOL),
               "valid_until": valid, "status": "active"}
        db.add_vehicle(rec)
        reg_records.append(rec)
    print(f"vehicles   : {len(reg_records)} registered")

    # --- blacklist --------------------------------------------------------
    for plate in blacklisted:
        db.add_blacklist(plate, random.choice(BL_REASONS))
    for _ in range(3):
        db.add_blacklist(random_registration(), random.choice(BL_REASONS))
    print(f"blacklist  : {len(blacklisted) + 3} plates")

    # --- a week of historical access events ------------------------------
    bl_plates = blacklisted + [random_registration() for _ in range(2)]
    n_history = 170
    for _ in range(n_history):
        roll = random.random()
        if roll < 0.10:                            # denied
            plate = random.choice(bl_plates)
            decision, owner, vtype = "denied", None, None
            reason = "Blacklisted vehicle"
        elif roll < 0.26:                          # alert (unknown)
            plate = random_registration()
            decision, owner, vtype = "alert", None, None
            reason = "Unregistered vehicle"
        else:                                      # granted
            rec = random.choice(reg_records)
            plate, owner, vtype = rec["plate"], rec["owner_name"], rec["vehicle_type"]
            decision, reason = "granted", f"Registered {vtype}"
        ts = datetime.now() - timedelta(days=random.uniform(0, 6.9),
                                        hours=random.uniform(0, 24))
        db.insert_event({
            "plate": plate, "decision": decision, "direction": "in",
            "reason": reason, "owner_name": owner, "vehicle_type": vtype,
            "province": plate_province.get(plate)
                        or random.choice(PROVINCES_POOL),
            "vehicle_color": random.choice(COLORS),
            "speed_kmh": round(random.uniform(8, 34), 1),
            "confidence": round(random.uniform(0.86, 0.99), 3),
            "gate": "MAIN 01", "image_path": "", "track_id": 0,
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        })
    print(f"history    : {n_history} access events over 7 days")
    print(f"database   : {db_path}")
    print("done.")


if __name__ == "__main__":
    main()
