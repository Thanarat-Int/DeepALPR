# Deep ALPR · build a clean release package for the customer.
# Run from project root:   .\package_release.ps1
# Output: deep_alpr_release/ folder + deep_alpr_release.zip

$ErrorActionPreference = "Stop"
$ROOT    = $PSScriptRoot
$RELEASE = Join-Path $ROOT "deep_alpr_release"
$ZIP     = "$RELEASE.zip"

if (Test-Path $RELEASE) { Remove-Item $RELEASE -Recurse -Force }
if (Test-Path $ZIP)     { Remove-Item $ZIP -Force }
New-Item -ItemType Directory -Path $RELEASE | Out-Null

Write-Host "Packaging release ..." -ForegroundColor Cyan

# --- models -------------------------------------------------------------
New-Item -ItemType Directory -Path "$RELEASE\models" | Out-Null
Copy-Item "$ROOT\models\ocr_crnn.pt"        "$RELEASE\models\" -Force
if (Test-Path "$ROOT\models\plate_detector.pt") {
    Copy-Item "$ROOT\models\plate_detector.pt" "$RELEASE\models\" -Force
}
Copy-Item "$ROOT\yolov8n.pt" "$RELEASE\" -Force

# --- source code (skip __pycache__) ------------------------------------
robocopy "$ROOT\src" "$RELEASE\src" /E /XD __pycache__ /NFL /NDL /NJH /NJS /NC /NS | Out-Null

# --- dashboard ---------------------------------------------------------
robocopy "$ROOT\dashboard" "$RELEASE\dashboard" /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null

# --- config + entry ----------------------------------------------------
Copy-Item "$ROOT\config.yaml"     "$RELEASE\" -Force
Copy-Item "$ROOT\requirements.txt" "$RELEASE\" -Force
Copy-Item "$ROOT\run_service.py"  "$RELEASE\" -Force

# --- docs (optional but useful) ----------------------------------------
if (Test-Path "$ROOT\docs") {
    Copy-Item "$ROOT\docs" "$RELEASE\" -Recurse -Force
}
if (Test-Path "$ROOT\README.md") {
    Copy-Item "$ROOT\README.md" "$RELEASE\" -Force
}

# --- empty data folders that the app expects at runtime ----------------
New-Item -ItemType Directory -Path "$RELEASE\data\captures" | Out-Null
"# Captured plate images go here at runtime." |
    Out-File "$RELEASE\data\captures\.gitkeep" -Encoding utf8

# --- write a deploy note -----------------------------------------------
@'
Deep ALPR · Release Package
============================

To run on the target machine:
1) Install Python 3.11+
2) pip install -r requirements.txt
3) Edit config.yaml as needed (camera source, gate hardware, retention).
4) python run_service.py
5) Open http://127.0.0.1:8000 in a browser.

Default demo accounts (change immediately):
    admin    / admin123
    operator / operator123

Trained models included:
    models/ocr_crnn.pt        ← Thai plate OCR (CRNN)
    models/plate_detector.pt  ← plate detector
    yolov8n.pt                ← vehicle detector

See docs/production_checklist_th.txt for the go-live checklist.
'@ | Out-File "$RELEASE\DEPLOY_README.txt" -Encoding utf8

# --- summary -----------------------------------------------------------
$size = [math]::Round(((Get-ChildItem $RELEASE -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 1)
Write-Host ""
Write-Host "Release built at: $RELEASE" -ForegroundColor Green
Write-Host "Total size: $size MB" -ForegroundColor Green

# --- zip it ------------------------------------------------------------
Compress-Archive -Path "$RELEASE\*" -DestinationPath $ZIP -Force
$zipSize = [math]::Round(((Get-Item $ZIP).Length / 1MB), 1)
Write-Host "Zip created: $ZIP  ($zipSize MB)" -ForegroundColor Green
