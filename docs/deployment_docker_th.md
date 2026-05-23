# Deep ALPR · Deploy ด้วย Docker

อัปเดต: 2026-05-23
ทางเลือกแทน [deployment_guide_th.md](deployment_guide_th.md) (native install)

---

## เลือกอันไหนระหว่าง Native vs Docker

| ลูกค้าแบบไหน | แนะนำ |
|---|---|
| 1 PC 1 ประตู ลูกค้า IT ระดับพื้นฐาน | Native Windows + NSSM |
| 1 PC 1 ประตู ลูกค้ามี DevOps | Docker |
| หลาย PC หลายไซต์ | Docker (ใช้ image เดียว) |
| ต้องการ update บ่อย | Docker |
| ลูกค้ามี Linux server | Docker (no question) |
| Windows server อย่างเดียว มี GPU | ทั้งคู่ทำได้ Docker ตั้งยากแต่บำรุงง่าย |

---

## ความต้องการ Host (PC ลูกค้า)

### ทางเลือก 1: Windows + Docker Desktop

1. Windows 10/11 Pro หรือ Enterprise (Home ก็ได้ตอนนี้)
2. WSL2 เปิดใช้งาน
3. **Docker Desktop for Windows** ติดตั้ง https://docker.com/products/docker-desktop
4. NVIDIA Driver ≥ 550 (ลูกค้าน่าจะมีแล้ว)
5. ตั้ง Docker Desktop > Settings > Resources > GPU > Enable GPU support

### ทางเลือก 2: Linux + Docker (แนะนำสำหรับ production จริง)

1. Ubuntu 22.04 LTS หรือ Debian 12
2. Docker Engine + Docker Compose v2
3. nvidia-container-toolkit ติดตั้ง:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## Verify GPU passthrough ทำงาน

```bash
# ทดสอบว่า container เห็น GPU
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
# ต้องเห็น RTX 4060 + driver version
```

ถ้าไม่เห็น → แก้ก่อนทำขั้นต่อไป (ไม่งั้น app จะรันบน CPU ช้ามาก).

---

## Deploy 4 ขั้นตอน

### 1. ส่ง project ไปที่ PC ลูกค้า

```powershell
# จาก zip ที่ผมเตรียม
cd C:\
Expand-Archive deep_alpr_release.zip -DestinationPath C:\DeepALPR
cd C:\DeepALPR
```

ต้องมี Dockerfile, docker-compose.yml, .dockerignore ครบ (ใส่ใน release package ให้แล้ว).

### 2. แก้ config.yaml

แก้แบบเดียวกับ native install:
- camera.source = RTSP URL
- detection.plate_mode = "model"
- gate.controller_url = ที่อยู่ไม้กั้น

### 3. Build + Start

```bash
# Build image ครั้งแรก (ใช้เวลา 5-10 นาที + download 4-5 GB)
docker compose build

# Start service (รัน background)
docker compose up -d

# ดู log แบบ live
docker compose logs -f
```

หยุดด้วย Ctrl+C ตอนดู log จะไม่ stop service. ใช้:
```bash
docker compose down       # stop + remove container
docker compose stop       # stop ค้างไว้ start ใหม่ได้
```

### 4. Verify ทำงาน

```bash
# Container ขึ้น
docker compose ps
# STATUS ต้องเป็น "Up (healthy)"

# Endpoint ตอบ
curl http://localhost:8000/health
# {"status":"ok","service":"deep-alpr","version":"2.0.0"}

# GPU ถูกใช้
docker compose exec deep-alpr python -c "import torch; print(torch.cuda.is_available())"
# True

# เปิด browser ไปที่ http://<IP-ของ-PC>:8000
```

---

## งานบำรุงรักษาผ่าน Docker

### Update รุ่นใหม่
```bash
# ผม push image ใหม่ลง registry แล้ว
docker compose pull
docker compose up -d
# Done. Downtime ~30 วินาที
```

### Rollback ถ้าพัง
```bash
docker compose down
# แก้ docker-compose.yml ให้ image: deep-alpr:1.2.3 (version เก่า)
docker compose up -d
```

### ดู log ย้อนหลัง
```bash
docker compose logs --tail 200
docker compose logs --since 1h
```

### Backup
```bash
# Database + รูป
tar -czf backup-$(date +%Y%m%d).tar.gz ./data
# upload ไป NAS / cloud
```

### Restart auto ตอน PC boot
```bash
# ใน docker-compose.yml มี restart: unless-stopped อยู่แล้ว
# ใน Docker Desktop > Settings > Start Docker Desktop when you log in
```

---

## ข้อดี + ข้อเสีย เทียบกับ native

### ข้อดี Docker
- 1 คำสั่ง start/stop/update
- isolated ไม่กระทบ Python อื่นบนเครื่อง
- log มี rotation ในตัว
- migrate ไปเครื่องอื่นง่าย (copy compose + volumes)
- ขยายเป็น multi-container ในอนาคตได้ (เพิ่ม Redis, PostgreSQL, monitoring)

### ข้อเสีย Docker บน Windows
- ลงครั้งแรกยากกว่า (WSL2 + Docker Desktop + GPU toolkit)
- Docker Desktop ใช้ RAM ของ host 2-4 GB ตลอด
- update WSL2 บางครั้ง break GPU passthrough ต้อง troubleshoot
- ตอน debug ปัญหา network/RTSP ยากกว่า native

---

## คำแนะนำสุดท้าย สำหรับลูกค้ารายนี้

จากที่คุยมา ลูกค้ามี PC ตัวเดียว Windows + RTX 4060. ผมแนะนำ:

**ถ้าลูกค้าไม่มีทีม DevOps → ใช้ Native + NSSM** ([deployment_guide_th.md](deployment_guide_th.md))
- ตั้งครั้งเดียวจบ
- update น้อยครั้ง
- support ง่าย

**ถ้าลูกค้ามี DevOps หรืออยากเทคโนโลยีใหม่ → ใช้ Docker** (ไฟล์นี้)
- standardized
- update รัวๆ ได้
- ใน 2026 คือ best practice ของวงการ

---

## ทางเลือกที่ 3: Hybrid (ที่ผมจริงๆ ใช้กับลูกค้าใหญ่)

- Deploy ครั้งแรกแบบ Docker ที่ Linux VM (Ubuntu Server)
- VM นั้นเป็น VM บน Windows host ของลูกค้า (ใช้ Hyper-V)
- ได้ best of both: Docker isolation + Linux stability + ลูกค้ายังเห็นเครื่อง Windows ที่คุ้นเคย

แต่ทำได้เมื่อลูกค้า IT ระดับกลาง+ ขึ้นไปเท่านั้น.

---

## ไฟล์ที่เกี่ยวข้อง

- [Dockerfile](../Dockerfile) — image definition
- [docker-compose.yml](../docker-compose.yml) — orchestration
- [.dockerignore](../.dockerignore) — exclude files from image
- [deployment_guide_th.md](deployment_guide_th.md) — ทางเลือก native (อ่าน parallel)
- [production_checklist_th.txt](production_checklist_th.txt) — 10 ข้อก่อน go-live
