# Deep ALPR · production container image
#
# Build:    docker build -t deep-alpr:latest .
# Run:      docker compose up -d
#
# Image is ~5 GB because PyTorch + CUDA + Ultralytics are heavy. The base
# nvidia/cuda image gives us the GPU runtime libraries the wheel expects.

FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# --- system packages ---------------------------------------------------------
# python3.11 because it is the most stable for PyTorch and OpenCV in 2026
# libgl1 + libglib2 are needed by OpenCV for video decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3-pip \
        libgl1 \
        libglib2.0-0 \
        ffmpeg \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Use Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
 && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app

# --- Python deps -------------------------------------------------------------
# Install PyTorch CUDA 12.4 build separately (large, cache this layer)
RUN pip install --no-cache-dir torch torchvision \
        --index-url https://download.pytorch.org/whl/cu124

# App requirements (lighter, change more often)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- application code --------------------------------------------------------
# Order matters: copy code AFTER pip installs so a code change does not
# invalidate the heavy dep layers above.
COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY models/ ./models/
COPY yolov8n.pt ./
COPY config.yaml ./
COPY run_service.py ./

# Persistent state lives in /data, mounted as a volume by docker compose.
RUN mkdir -p /data/captures /data/db /logs

# --- runtime -----------------------------------------------------------------
EXPOSE 8000

# Healthcheck so Docker can mark the container unhealthy and trigger a restart.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "run_service.py"]
