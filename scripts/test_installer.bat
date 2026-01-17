@echo off
chcp 65001 >nul
echo ============================================================
echo Anime1 Windows 安装包测试脚本
echo ============================================================

REM 检查是否安装了 NSIS
where makensis >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 正在安装 NSIS...
    choco install nsis -y
    if %errorlevel% neq 0 (
        echo [ERROR] NSIS 安装失败，请手动安装后重试
        echo 安装命令: choco install nsis -y
        pause
        exit /b 1
    )
    echo [OK] NSIS 安装完成
    echo.
)

REM 切换到脚本所在目录
cd /d "%~dp0.."

echo [BUILD] 正在构建应用...
python build.py --clean
if %errorlevel% neq 0 (
    echo [ERROR] 应用构建失败
    pause
    exit /b 1
)

echo [INFO] 正在生成图标...
python scripts/generate_icons.py

echo [BUILD] 正在创建安装包...
python scripts/create_windows_installer.py
if %errorlevel% neq 0 (
    echo [ERROR] 安装包创建失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 测试完成！
echo ============================================================
echo 安装包位置: release\anime1-windows-x64-setup.exe

if exist "release\anime1-windows-x64-setup.exe" (
    for %%I in (release\anime1-windows-x64-setup.exe) do (
        echo 文件大小: %%~zI bytes
    )
    echo.
    echo 是否立即运行安装程序？(y/n)
    set /p choice=""
    if "!choice!"=="y" (
        start "" "release\anime1-windows-x64-setup.exe"
    )
)

pause
