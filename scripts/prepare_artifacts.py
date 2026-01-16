#!/usr/bin/env python3
"""
准备构建产物脚本

根据平台和架构将构建产物打包为相应的格式：
- Windows: 打包 exe 为 zip
- macOS: 打包 app 为 zip (区分 Intel x64 和 Apple Silicon arm64)
- Linux: 打包可执行文件为 tar.gz
"""
import os
import sys
import platform
import zipfile
import tarfile
from pathlib import Path


def find_exe_file(dist_dir: Path) -> Path | None:
    """查找 exe 文件"""
    candidates = [
        dist_dir / "Anime1.exe",
        dist_dir / "anime1.exe",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # 查找所有 exe 文件
    exe_files = list(dist_dir.rglob("*.exe"))
    if exe_files:
        return exe_files[0]
    
    return None


def find_binary_file(dist_dir: Path) -> Path | None:
    """查找可执行文件（Linux）"""
    candidates = [
        dist_dir / "Anime1",
        dist_dir / "anime1",
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    
    # 查找所有可执行文件
    for file in dist_dir.rglob("*"):
        if file.is_file() and os.access(file, os.X_OK):
            # 排除 .so 和 .dylib 文件
            if not file.suffix in ['.so', '.dylib']:
                return file
    
    return None


def find_app_dir(dist_dir: Path) -> Path | None:
    """查找 app 目录（macOS）"""
    app_path = dist_dir / "Anime1.app"
    if app_path.exists() and app_path.is_dir():
        return app_path
    return None


def package_windows(dist_dir: Path, output_dir: Path):
    """打包 Windows 构建产物"""
    exe_file = find_exe_file(dist_dir)
    if not exe_file:
        print(f"Error: No exe file found in {dist_dir}")
        print(f"Files in dist/: {list(dist_dir.iterdir())}")
        sys.exit(1)
    
    output_file = output_dir / "anime1-windows-x64.zip"
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_file, exe_file.name)
    
    print(f"Windows build artifact packaged: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


def get_architecture() -> str:
    """获取系统架构"""
    # 优先从环境变量获取（GitHub Actions 设置）
    arch = os.environ.get('ARCH', '').lower()
    if arch in ['x64', 'x86_64', 'amd64']:
        return 'x64'
    elif arch in ['arm64', 'aarch64']:
        return 'arm64'
    
    # 从平台信息检测
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        return 'x64'
    elif machine in ['arm64', 'aarch64']:
        return 'arm64'
    
    # 默认返回检测到的架构，如果无法识别则使用 x64
    print(f"Warning: Unknown architecture '{machine}', defaulting to x64")
    return 'x64' if not machine else machine


def package_macos(dist_dir: Path, output_dir: Path):
    """打包 macOS 构建产物为 DMG"""
    app_dir = find_app_dir(dist_dir)
    if not app_dir:
        print(f"Warning: Anime1.app not found in {dist_dir}")
        print(f"Files in dist/: {list(dist_dir.iterdir())}")
        sys.exit(1)
    
    # 检测架构
    arch = get_architecture()
    if arch == 'arm64':
        output_file = output_dir / "anime1-macos-arm64.dmg"
    else:
        output_file = output_dir / "anime1-macos-x64.dmg"
    
    print(f"Detected architecture: {arch}")
    
    # 使用 create_dmg 脚本创建 DMG
    create_dmg_script = Path(__file__).parent / "create_dmg.py"
    if not create_dmg_script.exists():
        print(f"Error: create_dmg.py not found at {create_dmg_script}")
        sys.exit(1)
    
    import subprocess
    result = subprocess.run(
        [sys.executable, str(create_dmg_script), str(app_dir), str(output_file)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error creating DMG: {result.stderr}")
        print(f"Output: {result.stdout}")
        sys.exit(1)
    
    print(result.stdout)
    if output_file.exists():
        print(f"macOS DMG created: {output_file}")
        print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"Error: DMG file not created: {output_file}")
        sys.exit(1)


def package_linux(dist_dir: Path, output_dir: Path):
    """打包 Linux 构建产物"""
    binary_file = find_binary_file(dist_dir)
    if not binary_file:
        print(f"Error: No executable file found in {dist_dir}")
        print(f"Files in dist/: {list(dist_dir.iterdir())}")
        sys.exit(1)
    
    # 确保可执行权限
    os.chmod(binary_file, 0o755)
    
    # 检测架构
    arch = get_architecture()
    if arch == 'arm64':
        output_file = output_dir / "anime1-linux-arm64.tar.gz"
    else:
        output_file = output_dir / "anime1-linux-x64.tar.gz"
    
    print(f"Detected architecture: {arch}")
    
    with tarfile.open(output_file, 'w:gz') as tf:
        tf.add(binary_file, arcname=binary_file.name)
    
    print(f"Linux build artifact packaged: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    """主函数"""
    platform = sys.platform
    dist_dir = Path("dist")
    output_dir = Path("release")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not dist_dir.exists():
        print(f"Error: dist directory not found: {dist_dir}")
        sys.exit(1)
    
    print(f"Platform: {platform}")
    print(f"Dist directory: {dist_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    if platform == "win32":
        package_windows(dist_dir, output_dir)
    elif platform == "darwin":
        package_macos(dist_dir, output_dir)
    else:
        package_linux(dist_dir, output_dir)
    
    print()
    print("Artifacts prepared:")
    for file in output_dir.iterdir():
        if file.is_file():
            print(f"  {file.name}")


if __name__ == "__main__":
    main()
