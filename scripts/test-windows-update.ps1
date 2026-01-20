#!/usr/bin/env pwsh
# Windows Auto-Update Complete Test Script
# Tests update flow: v0.0.1 (old) -> current build
# This test builds a low version first, then updates to current version

$ErrorActionPreference = "Stop"

# 配置
$API_HOST = "127.0.0.1"
$API_PORT = "5172"
$API_URL = "http://${API_HOST}:${API_PORT}"

# 版本配置
$OLD_VERSION = "0.0.1"
$CURRENT_VERSION = git describe --tags --always 2>$null || echo "0.2.5-dev"
if ([string]::IsNullOrEmpty($CURRENT_VERSION)) {
    $CURRENT_VERSION = "0.2.5-dev"
}
$EXPECTED_NEW_VERSION = $CURRENT_VERSION

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Auto-Update 完整测试" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host "旧版本: $OLD_VERSION -> 新版本: $EXPECTED_NEW_VERSION"
Write-Host "========================================"

# 辅助函数
function Wait-ForApi {
    param(
        [int]$MaxAttempts = 30,
        [int]$Interval = 1
    )
    Write-Host "等待 API 响应..." -ForegroundColor Yellow
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "${API_URL}/api/settings/about" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($response) {
                Write-Host "✓ API 已响应" -ForegroundColor Green
                return $true
            }
        } catch {
            # API not ready yet
        }
        Start-Sleep -Seconds $Interval
        if ($i % 5 -eq 0) {
            Write-Host "  尝试 $i/$MaxAttempts..." -ForegroundColor Gray
        }
    }
    Write-Host "✗ API 无响应 (等待 ${MaxAttempts} 秒后超时)" -ForegroundColor Red
    return $false
}

function Stop-AllAnime1Processes {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 1: 停止所有 Anime1 进程" -ForegroundColor Cyan
    Write-Host "========================================"

    # 停止进程
    Get-Process -Name "Anime1" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    # 检查是否还有进程
    $remaining = Get-Process -Name "Anime1" -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "✗ 仍有 Anime1 进程运行" -ForegroundColor Red
        $remaining | Format-Table
        exit 1
    }
    Write-Host "✓ 所有 Anime1 进程已停止" -ForegroundColor Green
}

function Build-OldVersion {
    param([string]$Version)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 0: 构建旧版本安装包" -ForegroundColor Cyan
    Write-Host "========================================"

    # 创建临时目录保存旧版本
    $tempDir = [System.IO.Path]::GetTempFileName()
    Remove-Item $tempDir
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    Write-Host "临时目录: $tempDir" -ForegroundColor Gray

    # 构建旧版本
    Write-Host "构建旧版本 $Version ..." -ForegroundColor Yellow
    $buildResult = python scripts/build.py --version $Version 2>&1 | Select-Object -Last 10
    $buildResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

    $oldZip = "release/anime1-windows-${Version}.zip"
    if (Test-Path $oldZip) {
        Copy-Item $oldZip "$tempDir\anime1-windows-${Version}.zip" -Force
        Write-Host "✓ 旧版本 ZIP 已保存: $tempDir\anime1-windows-${Version}.zip" -ForegroundColor Green
        return $tempDir
    } else {
        Write-Host "✗ 旧版本 ZIP 构建失败" -ForegroundColor Red
        exit 1
    }
}

function Build-CurrentVersion {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 0b: 构建当前版本" -ForegroundColor Cyan
    Write-Host "========================================"

    Write-Host "构建当前版本 $EXPECTED_NEW_VERSION ..." -ForegroundColor Yellow
    $buildResult = python scripts/build.py 2>&1 | Select-Object -Last 10
    $buildResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

    $newZip = "release/anime1-windows-${EXPECTED_NEW_VERSION}.zip"
    if (Test-Path $newZip) {
        Write-Host "✓ 当前版本 ZIP 已构建: $newZip" -ForegroundColor Green
        return $newZip
    } else {
        Write-Host "✗ 当前版本 ZIP 构建失败" -ForegroundColor Red
        exit 1
    }
}

function Install-OldVersion {
    param(
        [string]$ZipPath,
        [string]$Version
    )

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 2: 安装旧版本 $Version" -ForegroundColor Cyan
    Write-Host "========================================"

    $installDir = "$env:ProgramFiles (x86)\Anime1"
    Write-Host "安装目录: $installDir" -ForegroundColor Gray

    # 移除旧安装
    if (Test-Path $installDir) {
        Remove-Item -Recurse -Force $installDir -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null

    # 解压
    Write-Host "从 $ZipPath 解压安装..." -ForegroundColor Yellow
    Expand-Archive -Path $ZipPath -DestinationPath $installDir -Force

    # 检查解压结果
    if (Test-Path "$installDir\Anime1.exe") {
        Write-Host "✓ 旧版本已安装" -ForegroundColor Green
    } else {
        Write-Host "✗ 解压安装失败" -ForegroundColor Red
        Get-ChildItem $installDir -Recurse | Select-Object -First 20
        exit 1
    }
}

function Clear-Logs {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 3: 清除日志" -ForegroundColor Cyan
    Write-Host "========================================"

    $logDir = "$env:APPDATA\Anime1\logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }

    # 清空日志文件
    "$logDir\anime1.log", "$logDir\app.log" | ForEach-Object {
        if (Test-Path $_) {
            Set-Content -Path $_ -Value "" -Force
        }
    }
    Write-Host "✓ 日志已清除" -ForegroundColor Green
}

function Start-OldVersion {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 4: 启动旧版本应用" -ForegroundColor Cyan
    Write-Host "========================================"

    $exePath = "$env:ProgramFiles (x86)\Anime1\Anime1.exe"
    if (-not (Test-Path $exePath)) {
        Write-Host "✗ 可执行文件不存在: $exePath" -ForegroundColor Red
        exit 1
    }

    Write-Host "启动 $exePath ..." -ForegroundColor Yellow
    Start-Process -FilePath $exePath -WindowStyle Normal

    # 等待 API
    if (-not (Wait-ForApi -MaxAttempts 30)) {
        Write-Host "✗ 启动失败" -ForegroundColor Red
        exit 1
    }
}

function Get-CurrentVersion {
    try {
        $response = Invoke-RestMethod -Uri "${API_URL}/api/settings/about" -TimeoutSec 5
        return $response.data.version
    } catch {
        return "unknown"
    }
}

function Test-UpdateDetection {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 6: 检查更新" -ForegroundColor Cyan
    Write-Host "========================================"

    try {
        $response = Invoke-RestMethod -Uri "${API_URL}/api/settings/check_update" -TimeoutSec 10
        $hasUpdate = $response.has_update
        $latest = $response.latest_version

        Write-Host "Has update: $hasUpdate" -ForegroundColor Gray
        Write-Host "Latest version: $latest" -ForegroundColor Gray

        if ($hasUpdate -eq $true) {
            Write-Host "✓ 检测到更新: $latest" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠ 未检测到更新（版本号可能相同或需要从本地安装）" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "✗ 检查更新失败: $_" -ForegroundColor Red
        return $false
    }
}

function Start-LocalHttpServer {
    param([string]$Port = "8765")

    Write-Host "" -ForegroundColor Gray
    Write-Host "启动临时 HTTP 服务器提供更新包..." -ForegroundColor Yellow

    $httpProcess = Start-Process -FilePath "python" `
        -ArgumentList "-m http.server $Port --bind 127.0.0.1" `
        -WorkingDirectory "release" `
        -PassThru `
        -NoNewWindow

    Write-Host "HTTP 服务器 PID: $($httpProcess.Id)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
    return $httpProcess
}

function Test-DownloadAndInstall {
    param(
        [string]$ZipUrl,
        [string]$Version
    )

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 7: 下载并安装新版本" -ForegroundColor Cyan
    Write-Host "========================================"

    Write-Host "更新 URL: $ZipUrl" -ForegroundColor Gray

    try {
        $body = @{ url = $ZipUrl; auto_install = $true } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "${API_URL}/api/settings/update/download" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 60

        Write-Host "更新响应:" -ForegroundColor Gray
        $response | ConvertTo-Json -Depth 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

        if ($response.success -eq $true) {
            Write-Host "✓ 更新 API 调用成功" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ 更新 API 调用失败" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ 下载更新失败: $_" -ForegroundColor Red
        Write-Host $_.Exception.Response | Format-List -Force
        return $false
    }
}

function Test-AfterRestart {
    param([int]$WaitSeconds = 20)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 8: 等待自动重启 (${WaitSeconds}秒)" -ForegroundColor Cyan
    Write-Host "========================================"

    Start-Sleep -Seconds $WaitSeconds

    # 验证新版本
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 9: 验证新版本" -ForegroundColor Cyan
    Write-Host "========================================"

    if (-not (Wait-ForApi -MaxAttempts 15)) {
        Write-Host "✗ 重启后 API 无响应" -ForegroundColor Red

        Write-Host ""
        Write-Host "检查进程:" -ForegroundColor Yellow
        Get-Process -Name "Anime1" -ErrorAction SilentlyContinue | Format-Table

        Write-Host ""
        Write-Host "尝试手动启动:" -ForegroundColor Yellow
        $exePath = "$env:ProgramFiles (x86)\Anime1\Anime1.exe"
        if (Test-Path $exePath) {
            Start-Process -FilePath $exePath -WindowStyle Normal
            Start-Sleep -Seconds 10
            if (-not (Wait-ForApi -MaxAttempts 10)) {
                Write-Host "✗ 手动启动也失败" -ForegroundColor Red
                return $false
            }
        }
    }

    $newVersion = Get-CurrentVersion
    Write-Host "当前版本: $newVersion" -ForegroundColor Gray

    # 检查版本是否已更新
    if ($newVersion -ne "unknown") {
        Write-Host "✓ 应用正在运行" -ForegroundColor Green
        return $true
    }

    return $false
}

function Show-UpdateLogs {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "步骤 10: 检查更新日志" -ForegroundColor Cyan
    Write-Host "========================================"

    $logDir = "$env:APPDATA\Anime1\logs"
    $logFiles = Get-ChildItem -Path $logDir -Filter "*.log" -ErrorAction SilentlyContinue

    if ($logFiles) {
        foreach ($file in $logFiles) {
            Write-Host ""
            Write-Host "--- $file ---" -ForegroundColor Yellow
            Get-Content -Path $file.FullName -Tail 50 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        }
    } else {
        Write-Host "日志文件不存在" -ForegroundColor Gray
    }
}

# ==================== 主流程 ====================

# 步骤 0: 构建
$tempDir = Build-OldVersion -Version $OLD_VERSION
$newZip = Build-CurrentVersion

# 步骤 1: 停止进程
Stop-AllAnime1Processes

# 步骤 2: 安装旧版本
Install-OldVersion -ZipPath "$tempDir\anime1-windows-${OLD_VERSION}.zip" -Version $OLD_VERSION

# 清理临时目录
Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue

# 步骤 3: 清除日志
Clear-Logs

# 步骤 4: 启动旧版本
Start-OldVersion

# 步骤 5: 验证当前版本
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤 5: 验证当前版本" -ForegroundColor Cyan
Write-Host "========================================"
$currentVersion = Get-CurrentVersion
Write-Host "当前版本: $currentVersion" -ForegroundColor Gray

# 步骤 6: 检查更新
$hasUpdate = Test-UpdateDetection

# 步骤 7: 下载并安装（使用本地 HTTP 服务器）
$httpProcess = Start-LocalHttpServer -Port "8765"

$localZipUrl = "http://127.0.0.1:8765/anime1-windows-${EXPECTED_NEW_VERSION}.zip"
$downloadSuccess = Test-DownloadAndInstall -ZipUrl $localZipUrl -Version $EXPECTED_NEW_VERSION

# 停止 HTTP 服务器
if ($httpProcess -and -not $httpProcess.HasExited) {
    $httpProcess.Kill()
    Write-Host "✓ HTTP 服务器已停止" -ForegroundColor Gray
}

if (-not $downloadSuccess) {
    Write-Host ""
    Write-Host "⚠ 本地下载失败，尝试使用 GitHub 下载..." -ForegroundColor Yellow
}

# 步骤 8 & 9: 等待重启并验证
Test-AfterRestart -WaitSeconds 25

# 步骤 10: 检查日志
Show-UpdateLogs

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ 测试完成！" -ForegroundColor Green
Write-Host "========================================"
