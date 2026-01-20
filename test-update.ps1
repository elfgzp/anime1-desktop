#!/usr/bin/env pwsh
# Quick test script for Windows update

$ErrorActionPreference = "Stop"

$installDir = "C:\Program Files (x86)\Anime1"
$oldZip = "C:\Users\74142\Github\anime1-desktop\release\anime1-windows-0.0.1.zip"
$newZip = "C:\Users\74142\Github\anime1-desktop\release\anime1-windows-0.2.7.zip"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Update Test" -ForegroundColor Cyan
Write-Host "========================================"

# Stop all Anime1 processes
Write-Host ""
Write-Host "[1] Stopping Anime1 processes..." -ForegroundColor Yellow
Get-Process -Name "Anime1" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "✓ Done" -ForegroundColor Green

# Clear logs
Write-Host ""
Write-Host "[2] Clearing logs..." -ForegroundColor Yellow
$logDir = "$env:APPDATA\Anime1\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"","" | Set-Content -Path "$logDir\anime1.log" -Force
"","" | Set-Content -Path "$logDir\app.log" -Force
Write-Host "✓ Done" -ForegroundColor Green

# Install old version
Write-Host ""
Write-Host "[3] Installing old version v0.0.1..." -ForegroundColor Yellow
if (Test-Path $installDir) {
    Remove-Item -Recurse -Force $installDir
}
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Use Python to extract (PowerShell Expand-Archive has issues with Chinese paths)
$python = python
& $python -c "import zipfile; import shutil; import sys; zf=zipfile.ZipFile(r'$oldZip'); zf.extractall(r'$installDir')"
Write-Host "✓ Old version installed to: $installDir" -ForegroundColor Green

# Start old version
Write-Host ""
Write-Host "[4] Starting old version..." -ForegroundColor Yellow
$exePath = "$installDir\Anime1.exe"
Start-Process -FilePath $exePath -WindowStyle Normal

# Wait for API
Write-Host "Waiting for API..." -ForegroundColor Gray
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5172/api/settings/about" -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($response) {
            Write-Host "✓ API is responding!" -ForegroundColor Green
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
    if ($i % 5 -eq 0) { Write-Host "  Attempt $i..." -ForegroundColor Gray }
}

# Check version
$version = Invoke-RestMethod -Uri "http://127.0.0.1:5172/api/settings/about"
Write-Host "Current version: $($version.data.version)" -ForegroundColor Gray

# Start local HTTP server
Write-Host ""
Write-Host "[5] Starting local HTTP server..." -ForegroundColor Yellow
$httpProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m http.server 8765 --bind 127.0.0.1" `
    -WorkingDirectory "C:\Users\74142\Github\anime1-desktop\release" `
    -PassThru -NoNewWindow
Start-Sleep -Seconds 2
Write-Host "✓ HTTP server started (PID: $($httpProcess.Id))" -ForegroundColor Green

# Trigger update
Write-Host ""
Write-Host "[6] Triggering update..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:5172/api/settings/update/download" `
        -Method Post `
        -ContentType "application/json" `
        -Body '{"url": "http://127.0.0.1:8765/anime1-windows-0.2.7.zip", "auto_install": true}' `
        -TimeoutSec 60

    Write-Host "Response:" -ForegroundColor Gray
    $response | ConvertTo-Json -Depth 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

    if ($response.success -eq $true) {
        Write-Host "✓ Update triggered successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Update failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Stop HTTP server
if (-not $httpProcess.HasExited) {
    $httpProcess.Kill()
    Write-Host "✓ HTTP server stopped" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[7] Waiting for restart (20 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Check if new version is running
Write-Host ""
Write-Host "[8] Checking new version..." -ForegroundColor Yellow
try {
    $newVersion = Invoke-RestMethod -Uri "http://127.0.0.1:5172/api/settings/about" -TimeoutSec 5
    Write-Host "New version: $($newVersion.data.version)" -ForegroundColor Green
    Write-Host "✓ Update successful!" -ForegroundColor Green
} catch {
    Write-Host "✗ Could not get version (app may have crashed)" -ForegroundColor Red
}

# Show recent logs
Write-Host ""
Write-Host "[9] Recent logs:" -ForegroundColor Yellow
$logFile = "$env:APPDATA\Anime1\anime1.log"
if (Test-Path $logFile) {
    Get-Content -Path $logFile -Tail 30 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Cyan
Write-Host "========================================"
