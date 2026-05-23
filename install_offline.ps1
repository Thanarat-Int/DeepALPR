# Deep ALPR · OFFLINE installer
# Run this on customer PC from the USB drive folder, as Administrator.
# No internet required.

$ErrorActionPreference = "Stop"
$APP   = "DeepALPR"
$KIT   = $PSScriptRoot
$DEST  = "C:\DeepALPR"

function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Ok($msg)       { Write-Host "    OK: $msg" -ForegroundColor Green }

# 0. require admin
if (-not ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please right-click this file and choose 'Run as Administrator'" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 1. install Python if missing
Step 1 "Installing Python 3.11 (silent)"
$pythonExe = "C:\Program Files\Python311\python.exe"
if (-not (Test-Path $pythonExe)) {
    & "$KIT\python-3.11.9-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 | Out-Null
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    Ok "Python installed"
} else {
    Ok "Python already present"
}

# 2. unzip the app
Step 2 "Extracting app to $DEST"
if (Test-Path $DEST) {
    Stop-Service $APP -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}
New-Item -ItemType Directory -Path $DEST -Force | Out-Null
Expand-Archive -Path "$KIT\app.zip" -DestinationPath $DEST -Force
Ok "App extracted"

# 3. create venv and install wheels from local folder
Step 3 "Creating Python venv and installing dependencies (offline)"
$pyExe = "C:\Program Files\Python311\python.exe"
& $pyExe -m venv "$DEST\venv"
$pip = "$DEST\venv\Scripts\pip.exe"
$venvPy = "$DEST\venv\Scripts\python.exe"

& $pip install --upgrade pip --no-index --find-links "$KIT\wheels"
& $pip install --no-index --find-links "$KIT\wheels" torch torchvision
& $pip install --no-index --find-links "$KIT\wheels" -r "$DEST\requirements.txt"
Ok "Dependencies installed offline"

# 4. verify GPU
Step 4 "Verifying GPU"
$cuda = & $venvPy -c "import torch; print(torch.cuda.is_available())"
if ($cuda -eq "True") {
    $gpuName = & $venvPy -c "import torch; print(torch.cuda.get_device_name(0))"
    Ok "GPU works: $gpuName"
} else {
    Write-Host "    WARN: GPU not detected. Check NVIDIA driver." -ForegroundColor Yellow
}

# 5. extract NSSM and install service
Step 5 "Registering Windows Service"
$nssmDir = "$DEST\tools"
New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
Expand-Archive -Path "$KIT\nssm.zip" -DestinationPath $nssmDir -Force
$nssm = (Get-ChildItem -Recurse -Path $nssmDir -Filter "nssm.exe" |
         Where-Object { $_.FullName -like "*win64*" } | Select-Object -First 1).FullName

# Remove old service if exists
if (Get-Service $APP -ErrorAction SilentlyContinue) {
    & $nssm stop $APP confirm 2>$null | Out-Null
    & $nssm remove $APP confirm 2>$null | Out-Null
}

New-Item -ItemType Directory -Path "$DEST\logs" -Force | Out-Null
& $nssm install $APP $venvPy "$DEST\run_service.py"
& $nssm set $APP AppDirectory $DEST
& $nssm set $APP AppStdout "$DEST\logs\service.log"
& $nssm set $APP AppStderr "$DEST\logs\service.err.log"
& $nssm set $APP AppRotateFiles 1
& $nssm set $APP AppRotateBytes 52428800
& $nssm set $APP Start SERVICE_AUTO_START
& $nssm set $APP AppExit Default Restart
& $nssm set $APP AppRestartDelay 5000

& $nssm start $APP
Start-Sleep -Seconds 3
$status = (Get-Service $APP).Status
Ok "Service: $status"

# 6. firewall
Step 6 "Opening firewall port 8000"
if (-not (Get-NetFirewallRule -DisplayName "$APP Dashboard" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "$APP Dashboard" `
        -Direction Inbound -Protocol TCP -LocalPort 8000 `
        -Action Allow -Profile Any | Out-Null
}
Ok "Firewall configured"

# Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " Deep ALPR installed and running." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
$ip = (Get-NetIPAddress -AddressFamily IPv4 `
       | Where-Object { $_.IPAddress -notlike "169.*" -and $_.IPAddress -ne "127.0.0.1" } `
       | Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "Open browser:"
Write-Host "  http://localhost:8000" -ForegroundColor Yellow
if ($ip) { Write-Host "  http://$ip:8000     (from other PCs in LAN)" -ForegroundColor Yellow }
Write-Host ""
Write-Host "Default login (CHANGE IMMEDIATELY):"
Write-Host "  admin / admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "Service auto-starts at every boot."
Write-Host "Useful commands:"
Write-Host "  Restart-Service $APP    # restart service"
Write-Host "  Get-Content $DEST\logs\service.log -Tail 50    # view logs"
Write-Host ""
Read-Host "Press Enter to exit"
