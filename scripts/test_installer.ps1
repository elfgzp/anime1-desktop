#!/usr/bin/env pwsh
# Anime1 Windows 安装包测试脚本

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Anime1 Windows 安装包测试脚本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 NSIS
$makensis = Get-Command "makensis" -ErrorAction SilentlyContinue
if (-not $makensis) {
    Write-Host "[INFO] 正在安装 NSIS..." -ForegroundColor Yellow
    choco install nsis -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] NSIS 安装失败，请手动安装后重试" -ForegroundColor Red
        Write-Host "安装命令: choco install nsis -y" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[OK] NSIS 安装完成" -ForegroundColor Green
    Write-Host ""
}

# 获取项目根目录
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# 构建应用
Write-Host "[BUILD] 正在构建应用..." -ForegroundColor Yellow
Push-Location $projectRoot
try {
    python build.py --clean
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] 应用构建失败" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# 生成图标
Write-Host "[INFO] 正在生成图标..." -ForegroundColor Yellow
python "$PSScriptRoot/generate_icons.py"

# 创建安装包
Write-Host "[BUILD] 正在创建安装包..." -ForegroundColor Yellow
python "$PSScriptRoot/create_windows_installer.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 安装包创建失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

$installerPath = "$projectRoot\release\anime1-windows-x64-setup.exe"
if (Test-Path $installerPath) {
    $size = (Get-Item $installerPath).Length / 1MB
    Write-Host "安装包位置: $installerPath" -ForegroundColor White
    Write-Host "文件大小: $([math]::Round($size, 2)) MB" -ForegroundColor White
    Write-Host ""

    $choice = Read-Host "是否立即运行安装程序？(y/n)"
    if ($choice.ToLower() -eq "y") {
        Start-Process $installerPath
    }
} else {
    Write-Host "[WARNING] 安装包未找到" -ForegroundColor Yellow
}

Write-Host ""
pause
