# Build a self-contained deployment USB kit for the customer site.
# Run on YOUR dev PC (with internet). Output: deployment_kit/ + zip.
# Copy the folder to a USB drive (~5 GB).
#
# At the customer site, no internet needed. Just:
#   1. Plug USB into customer PC
#   2. Run install_offline.ps1 as Administrator

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$KIT  = Join-Path $ROOT "deployment_kit"

if (Test-Path $KIT) { Remove-Item $KIT -Recurse -Force }
New-Item -ItemType Directory -Path $KIT | Out-Null

Write-Host "Building deployment kit ..." -ForegroundColor Cyan

# --- 1. release package (app + models) -----------------------------------
Write-Host "[1/5] Packaging app + models"
.\package_release.ps1 | Out-Null
Copy-Item "deep_alpr_release.zip" "$KIT\app.zip"

# --- 2. download Python 3.11 installer -----------------------------------
Write-Host "[2/5] Downloading Python 3.11"
Invoke-WebRequest `
    -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" `
    -OutFile "$KIT\python-3.11.9-amd64.exe" -UseBasicParsing

# --- 3. download NSSM ----------------------------------------------------
Write-Host "[3/5] Downloading NSSM"
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" `
    -OutFile "$KIT\nssm.zip" -UseBasicParsing

# --- 4. pre-download all Python wheels (offline pip install) ------------
Write-Host "[4/5] Pre-downloading Python wheels (large, ~3 GB)"
$wheels = Join-Path $KIT "wheels"
New-Item -ItemType Directory -Path $wheels | Out-Null

# PyTorch CUDA wheels
& pip download torch torchvision `
    --index-url https://download.pytorch.org/whl/cu124 `
    --dest $wheels --no-deps
# Get torch dependencies too (NOT from CUDA index)
& pip download torch torchvision `
    --index-url https://download.pytorch.org/whl/cu124 `
    --dest $wheels

# App requirements
& pip download -r requirements.txt --dest $wheels

# --- 5. installer + cheat sheet ------------------------------------------
Write-Host "[5/5] Adding offline installer + Thai cheat sheet"
Copy-Item "install_offline.ps1" "$KIT\install_offline.ps1"
Copy-Item "docs\DEPLOY_CHEATSHEET_TH.txt" "$KIT\!!_อ่านก่อน_!!.txt"

# Zip the whole kit for transport
$zip = "deployment_kit.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path "$KIT\*" -DestinationPath $zip -Force

$size = [math]::Round(((Get-Item $zip).Length / 1MB), 0)
Write-Host ""
Write-Host "Done. Kit ready at:" -ForegroundColor Green
Write-Host "  Folder: $KIT" -ForegroundColor Green
Write-Host "  Zip:    $zip ($size MB)" -ForegroundColor Green
Write-Host ""
Write-Host "Copy '$KIT' to a USB drive and you can install on any Windows PC" -ForegroundColor Yellow
Write-Host "with RTX GPU, OFFLINE, in 15 minutes." -ForegroundColor Yellow
