# Deep ALPR - one-shot installer for Windows.
# Run from PowerShell as Administrator:   .\install.ps1
#
# This sets up everything the customer needs in one command:
#   1. checks Python + GPU
#   2. creates venv
#   3. installs PyTorch CUDA + dependencies
#   4. registers the system as a Windows Service that auto-starts
#   5. opens firewall for dashboard
#
# Total time: ~15-20 minutes (most of it is pip install).

$ErrorActionPreference = "Stop"
$APP_NAME = "DeepALPR"
$ROOT = $PSScriptRoot
$VENV = Join-Path $ROOT "venv"
$NSSM = Join-Path $ROOT "tools\nssm.exe"
$LOG_DIR = Join-Path $ROOT "logs"

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "    FAIL: $msg" -ForegroundColor Red }

# --- 0. require admin --------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Err "Please re-run this script as Administrator."
    exit 1
}

# --- 1. check Python ---------------------------------------------------------
Write-Step "Step 1/6: Checking Python"
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) {
    Write-Err "Python not found. Install Python 3.11 from python.org first."
    Write-Err "Make sure to tick 'Add Python to PATH' during installation."
    exit 1
}
$pyVer = & python --version
Write-Ok "Found $pyVer at $py"

# --- 2. check NVIDIA GPU -----------------------------------------------------
Write-Step "Step 2/6: Checking NVIDIA GPU"
try {
    $gpu = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
    Write-Ok "GPU detected: $gpu"
} catch {
    Write-Host "    WARN: nvidia-smi not found. System will run on CPU (much slower)." -ForegroundColor Yellow
}

# --- 3. create venv + install dependencies ----------------------------------
Write-Step "Step 3/6: Creating Python virtual environment"
if (-not (Test-Path $VENV)) {
    & python -m venv $VENV
}
$pip = Join-Path $VENV "Scripts\pip.exe"
$pyExe = Join-Path $VENV "Scripts\python.exe"
Write-Ok "venv at $VENV"

Write-Step "Step 4/6: Installing PyTorch (CUDA) + dependencies (large download, please wait)"
& $pip install --upgrade pip
& $pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
& $pip install -r (Join-Path $ROOT "requirements.txt")
Write-Ok "Dependencies installed"

# Verify CUDA inside the venv
$cudaCheck = & $pyExe -c "import torch; print(torch.cuda.is_available())"
if ($cudaCheck -eq "True") {
    Write-Ok "PyTorch can access GPU"
} else {
    Write-Host "    WARN: PyTorch running on CPU. Performance will suffer." -ForegroundColor Yellow
}

# --- 4. download NSSM if missing --------------------------------------------
Write-Step "Step 5/6: Setting up Windows Service"
if (-not (Test-Path $NSSM)) {
    New-Item -ItemType Directory -Path (Split-Path $NSSM) -Force | Out-Null
    Write-Host "    Downloading NSSM ..."
    $tmp = Join-Path $env:TEMP "nssm.zip"
    Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile $tmp -UseBasicParsing
    Expand-Archive -Path $tmp -DestinationPath (Split-Path $NSSM) -Force
    Move-Item (Join-Path (Split-Path $NSSM) "nssm-2.24\win64\nssm.exe") $NSSM -Force
    Remove-Item (Join-Path (Split-Path $NSSM) "nssm-2.24") -Recurse -Force
    Remove-Item $tmp -Force
}
Write-Ok "NSSM ready"

# Remove old service if exists
if (Get-Service -Name $APP_NAME -ErrorAction SilentlyContinue) {
    & $NSSM stop $APP_NAME confirm 2>$null | Out-Null
    & $NSSM remove $APP_NAME confirm 2>$null | Out-Null
}

# Install service
New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
& $NSSM install $APP_NAME $pyExe (Join-Path $ROOT "run_service.py")
& $NSSM set $APP_NAME AppDirectory $ROOT
& $NSSM set $APP_NAME AppStdout (Join-Path $LOG_DIR "service.log")
& $NSSM set $APP_NAME AppStderr (Join-Path $LOG_DIR "service.err.log")
& $NSSM set $APP_NAME AppRotateFiles 1
& $NSSM set $APP_NAME AppRotateBytes 52428800   # rotate at 50 MB
& $NSSM set $APP_NAME Start SERVICE_AUTO_START   # start at boot
& $NSSM set $APP_NAME AppExit Default Restart
& $NSSM set $APP_NAME AppRestartDelay 5000

& $NSSM start $APP_NAME
Start-Sleep -Seconds 3
$status = (Get-Service $APP_NAME).Status
Write-Ok "Service status: $status"

# --- 5. firewall rule -------------------------------------------------------
Write-Step "Step 6/6: Configuring firewall"
$ruleName = "$APP_NAME Dashboard"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound -Protocol TCP -LocalPort 8000 `
        -Action Allow -Profile Private,Domain | Out-Null
}
Write-Ok "Firewall: port 8000 open on private network"

# --- 6. final summary -------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Deep ALPR installation complete." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
$ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" `
       -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress
if (-not $ip) {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 `
           | Where-Object { $_.IPAddress -notlike "169.*" -and $_.IPAddress -ne "127.0.0.1" } `
           | Select-Object -First 1).IPAddress
}

Write-Host ""
Write-Host "Open the dashboard in any browser on this network:" -ForegroundColor White
Write-Host "    http://localhost:8000" -ForegroundColor Yellow
if ($ip) { Write-Host "    http://$ip:8000" -ForegroundColor Yellow }
Write-Host ""
Write-Host "Default login (change immediately):" -ForegroundColor White
Write-Host "    Username: admin    Password: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "Service management:" -ForegroundColor White
Write-Host "    Get-Service $APP_NAME        # status" -ForegroundColor Gray
Write-Host "    Restart-Service $APP_NAME    # restart" -ForegroundColor Gray
Write-Host "    Get-Content '$LOG_DIR\service.log' -Tail 50    # logs" -ForegroundColor Gray
Write-Host ""
Write-Host "Service will auto-start on every reboot." -ForegroundColor White
Write-Host ""
