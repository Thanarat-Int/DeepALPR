# Deep ALPR · คู่มือติดตั้งที่ไซต์ลูกค้า

อัปเดต: 2026-05-23
สำหรับ: PC ลูกค้า (Windows 10/11 + NVIDIA RTX 4060)

---

## เช็คก่อนเริ่ม (Site survey)

ก่อนเดินทางไปไซต์ ตรวจกับลูกค้า:

1. **PC spec ขั้นต่ำ**
   - CPU: Intel i5 / AMD Ryzen 5 ขึ้นไป (4 cores+)
   - RAM: 16 GB ขึ้นไป
   - GPU: RTX 4060 (ลูกค้ามีแล้ว) หรือดีกว่า
   - Storage: SSD 256 GB ว่างขั้นต่ำ 100 GB
   - Network: Gigabit LAN

2. **กล้อง IP**
   - รุ่นใด ผลิตจากใคร (Hikvision, Dahua, Axis, etc.)
   - มี RTSP stream URL ไหม
   - ติดที่ไหน มุมไหน (ส่งภาพมาให้ดูล่วงหน้า)

3. **ไม้กั้น / Gate controller**
   - ยี่ห้อ รุ่น
   - รับ signal แบบไหน (Wiegand 26/34, RS485 Modbus, Relay dry contact, HTTP API)
   - มี documentation ไหม

4. **เครือข่าย**
   - PC + กล้อง + ไม้กั้น อยู่ network เดียวกันไหม
   - มี firewall บล็อกอะไรบ้าง
   - ต้องการ remote access ไหม

---

## ขั้นตอนติดตั้ง

### ขั้นที่ 1: เตรียมระบบ (30 นาที)

```powershell
# 1.1 อัปเดต Windows ให้ใหม่
Settings > Windows Update > Check for updates

# 1.2 ติดตั้ง NVIDIA Driver ล่าสุด
# Download จาก: https://www.nvidia.com/download/index.aspx
# Studio Driver แนะนำกว่า Game Driver (เสถียรกว่า)

# 1.3 verify GPU เห็น
nvidia-smi
# ต้องเห็น RTX 4060 + driver version 550+

# 1.4 ติดตั้ง CUDA Toolkit 12.4
# Download: https://developer.nvidia.com/cuda-12-4-0-download-archive

# 1.5 ติดตั้ง Python 3.11
# Download: https://www.python.org/downloads/release/python-3119/
# ติ๊ก "Add Python to PATH" ตอน install
```

### ขั้นที่ 2: Deploy application (15 นาที)

```powershell
# 2.1 เปิด PowerShell as Administrator
# สร้างโฟลเดอร์
mkdir C:\DeepALPR
cd C:\DeepALPR

# 2.2 แตก zip package ที่ผมเตรียมไว้
Expand-Archive -Path "deep_alpr_release.zip" -DestinationPath .

# 2.3 สร้าง virtual environment (สำคัญ ป้องกัน package ชนกัน)
python -m venv venv
.\venv\Scripts\activate

# 2.4 ติดตั้ง PyTorch CUDA build (สำคัญที่สุด)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# 2.5 ติดตั้ง dependencies อื่นๆ
pip install -r requirements.txt

# 2.6 ทดสอบว่า GPU ทำงาน
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
# ต้องเห็น: CUDA: True / NVIDIA GeForce RTX 4060
```

### ขั้นที่ 3: ตั้งค่ากล้อง + ไม้กั้น (1-2 ชั่วโมง)

แก้ไฟล์ `config.yaml`:

```yaml
camera:
  source: "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101"
  # ขอจากเอกสารกล้อง หรือใช้ ONVIF Device Manager scan หา

detection:
  plate_mode: "model"           # เปลี่ยนจาก "mock" เป็น "model"
  plate_model: "models/plate_detector.pt"

gate:
  id: "MAIN 01"
  # ขึ้นกับ controller รุ่นไหน
  controller_type: "http"       # http / wiegand / rs485 / modbus
  controller_url: "http://192.168.1.50/api/open"
  controller_token: "your-controller-secret"

storage:
  database: "data/alpr.db"
  image_dir: "data/captures"

retention:
  image_days: 90
```

ทดสอบว่ากล้องเชื่อมต่อได้ก่อน:
```powershell
python -c "import cv2; cap = cv2.VideoCapture('rtsp://...'); ret, frame = cap.read(); print('OK' if ret else 'FAIL'); print(frame.shape if ret else '')"
```

### ขั้นที่ 4: ทดสอบ pipeline ก่อนเปิดเป็น service (30 นาที)

```powershell
# รันแบบ foreground เพื่อดู log
.\venv\Scripts\activate
python run_service.py

# เปิด browser ไปที่ http://localhost:8000
# Login: admin / admin123 (เปลี่ยนรหัสทันที!)
# ลองให้รถวิ่งผ่านกล้องดู event ขึ้นใน dashboard ไหม
```

ถ้าทุกอย่างทำงาน:
- หยุดด้วย Ctrl+C
- ไปขั้นที่ 5

### ขั้นที่ 5: เปลี่ยนรหัสผ่าน + เพิ่ม admin จริง (10 นาที)

```powershell
# เปิด dashboard ไปที่ Settings
# 1. คลิก "Change password" เปลี่ยน admin/admin123 → รหัสจริง
# 2. ลบ user "operator" demo
# 3. สร้าง user จริงของลูกค้า ทั้ง admin + operator
# 4. ลบ user "admin" demo (หลังจากสร้าง admin จริงแล้วเท่านั้น)
```

### ขั้นที่ 6: ทำให้เป็น Windows Service อัตโนมัติ (30 นาที)

ใช้ **NSSM** (Non-Sucking Service Manager) ฟรี.

```powershell
# Download NSSM: https://nssm.cc/download
# แตกแล้ววางที่ C:\Tools\nssm\

# ติดตั้ง service
C:\Tools\nssm\nssm.exe install DeepALPR

# ใน GUI ที่เด้งขึ้นกรอก:
#   Path:           C:\DeepALPR\venv\Scripts\python.exe
#   Startup dir:    C:\DeepALPR
#   Arguments:      run_service.py
#
# Tab "I/O":
#   Output: C:\DeepALPR\logs\service.log
#   Error:  C:\DeepALPR\logs\service.err.log
#
# Tab "Exit actions":
#   Restart action: Restart application
#   Delay:          5000 ms

# Start service
nssm start DeepALPR

# Verify
Get-Service DeepALPR
# Status: Running
```

### ขั้นที่ 7: ตั้งค่า Firewall (10 นาที)

```powershell
# อนุญาตให้ device ใน LAN เข้าถึง dashboard ผ่าน port 8000
New-NetFirewallRule -DisplayName "DeepALPR Dashboard" `
  -Direction Inbound -Protocol TCP -LocalPort 8000 `
  -Action Allow -Profile Private
```

ถ้าต้องการ remote access จากนอก office:
- ใช้ Cloudflare Tunnel (ฟรี ไม่ต้องเปิด port)
- หรือ Tailscale (ฟรี private network)
- หรือ VPN ของลูกค้าเอง

### ขั้นที่ 8: Backup setup (15 นาที)

```powershell
# สร้าง scheduled task backup DB ทุกคืน
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-Command Copy-Item C:\DeepALPR\data\alpr.db C:\Backup\alpr_$(Get-Date -Format yyyyMMdd).db"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "DeepALPR Backup" -Action $action -Trigger $trigger
```

ถ้ามี NAS แนะนำ rsync ขึ้น NAS หรือ cloud (AWS S3, Backblaze B2 ราคาถูก).

---

## หลัง deploy เสร็จ

### Health check ปกติ
```powershell
# 1. service ทำงาน
Get-Service DeepALPR
# 2. API ตอบ
Invoke-WebRequest http://localhost:8000/health
# 3. GPU usage ปกติ 30-60% ตอนมีรถวิ่ง
nvidia-smi
# 4. log ไม่มี ERROR
Get-Content C:\DeepALPR\logs\service.log -Tail 50
```

### ปัญหาที่เจอบ่อย + วิธีแก้

| อาการ | สาเหตุ | แก้ |
|---|---|---|
| Service หยุดบ่อย | RAM ไม่พอ / GPU OOM | ลด batch size ใน config |
| กล้อง stream หลุด | network ลุ่ม / กล้อง restart | เพิ่ม reconnect logic |
| ไม้กั้นไม่เปิด | controller URL ผิด | ตรวจ config + ping controller |
| OCR เพี้ยน | กล้องเบลอ / มุมไม่ดี | ปรับมุมกล้อง + เลนส์ |
| Dashboard เข้าไม่ได้ | firewall block | เช็คขั้นที่ 7 |
| ช้า / FPS ตก | กล้องส่งเฟรมเยอะเกิน | ลด FPS การ process ลง |

### Maintenance schedule

| ความถี่ | งาน |
|---|---|
| ทุกวัน | check service running + dashboard เข้าได้ |
| ทุกสัปดาห์ | review event log มี anomaly ไหม |
| ทุกเดือน | เช็ดเลนส์กล้อง + ตรวจ alignment |
| ทุก 3 เดือน | retrain model ด้วยข้อมูลใหม่จากที่เก็บไว้ |
| ทุก 6 เดือน | OS update + dependency update (test ใน staging ก่อน) |
| ทุก 1 ปี | hardware health check + DB vacuum |

---

## Architecture choices สำหรับ scale-up

ถ้าวันหน้าลูกค้าจะขยายมี 5-10 ประตู:

**ทางเลือก A: PC เดียวรับหลายกล้อง** (ถ้ารถไม่เยอะ)
- RTX 4060 รับได้ ~3-4 กล้อง 1080p @ 15 fps
- เพิ่มกล้องใน config.yaml

**ทางเลือก B: PC ละประตู + central server**
- กล้อง 1 ตัว = PC 1 ตัว ทำ inference ที่ edge
- ส่ง event ไป central server ที่รวม dashboard + DB
- เหมาะกับ site ใหญ่ใจกลางเมือง

**ทางเลือก C: ใช้ NVIDIA Jetson** (low cost)
- Jetson Orin Nano 8GB ราคา ~15,000 บาท
- รับ 1-2 กล้อง real-time ได้สบาย
- กินไฟแค่ 7-15W ใส่ in กล่องเล็กๆ ติดข้างกล้องได้

---

## Disaster recovery

ถ้า PC ลูกค้าพัง:

1. ซื้อ PC spec เดียวกัน
2. ลง Windows + driver + Python (ขั้นที่ 1-2)
3. Copy เฉพาะ 2 อย่าง:
   - `C:\DeepALPR\` (ทั้งโฟลเดอร์)
   - `data/alpr.db` (จาก backup ล่าสุด)
4. รัน service กลับมาเหมือนเดิม
5. **เวลารวม** ~3 ชั่วโมง

ระบบ stateless เกือบหมด ของที่สำคัญจริงๆ คือ database + config + model files. backup ดี = recovery ง่าย.

---

## Cost estimate (สำหรับลูกค้ารายนี้)

| รายการ | ราคา (บาท) | หมายเหตุ |
|---|---|---|
| PC + RTX 4060 | 0 | ลูกค้ามีแล้ว |
| Software install + config | 0 | open source ทั้งหมด |
| Software development | (คิดในข้อเสนอ) | งานของเรา |
| Camera (ถ้าไม่มี) | 3,000-8,000 / กล้อง | Hikvision DS-2CD รุ่นกลาง |
| Gate controller integration | ขึ้นกับยี่ห้อ | ส่วนใหญ่ 5,000-15,000 |
| Annotation จ้าง 5,000 ภาพ | 15,000-35,000 | สำหรับ retrain |
| **รวม hardware ส่วนเพิ่ม** | **~30,000-60,000** | ต่อ 1 ประตู |

ถ้าเทียบกับ ALPR commercial:
- Plate Recognizer / Genetec: 2,000-5,000 บาท/เดือน/กล้อง × 36 เดือน = 70,000-180,000
- ของเรา one-time cost ถูกกว่ามาก หลังจากนั้นไม่เสียเพิ่ม

นี่คือ value proposition ที่ดีของโซลูชั่นเรา.

---

## Contact

ระหว่าง deploy ติดปัญหา ติดต่อ: (ใส่ข้อมูล team support)

หลัง go-live SLA: ตามที่ตกลงใน [production_checklist_th.txt](production_checklist_th.txt) ข้อ 8.
