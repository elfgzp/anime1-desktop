#!/usr/bin/env python3
"""
创建 macOS DMG 文件

使用 create-dmg 工具创建 DMG 安装包，包含修复脚本
"""
import subprocess
import sys
import shutil
import os
from pathlib import Path


def create_dmg(app_path: Path, output_path: Path, app_name: str = "Anime1") -> bool:
    """
    创建 DMG 文件

    Args:
        app_path: .app 目录路径
        output_path: 输出的 DMG 文件路径
        app_name: 应用名称

    Returns:
        是否成功创建
    """
    # 检查 create-dmg 是否安装
    try:
        create_dmg_path = shutil.which('create-dmg')
        if not create_dmg_path:
            result = subprocess.run(
                ['command', '-v', 'create-dmg'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print("Error: create-dmg not found")
                print("Installing create-dmg via brew...")
                install_result = subprocess.run(
                    ['brew', 'install', 'create-dmg'],
                    capture_output=True,
                    text=True
                )
                if install_result.returncode != 0:
                    print(f"Failed to install create-dmg: {install_result.stderr}")
                    print("Please install create-dmg manually: brew install create-dmg")
                    return False
                print("create-dmg installed successfully")
    except FileNotFoundError:
        print("Error: brew not found. Cannot install create-dmg.")
        print("Please install create-dmg manually: brew install create-dmg")
        return False

    # 检查 app 是否存在
    if not app_path.exists():
        print(f"Error: App not found: {app_path}")
        return False

    # 如果输出文件已存在，先删除
    if output_path.exists():
        output_path.unlink()

    # 查找 create-dmg 命令路径
    create_dmg_cmd = shutil.which('create-dmg')
    if not create_dmg_cmd:
        result_check = subprocess.run(
            ['command', '-v', 'create-dmg'],
            capture_output=True,
            text=True
        )
        if result_check.returncode == 0:
            create_dmg_cmd = result_check.stdout.strip()
        else:
            print("Error: create-dmg command not found")
            return False

    # 查找修复脚本（从 app 同级目录或脚本目录）
    script_dir = Path(__file__).parent
    app_parent = app_path.parent

    # 优先从 app 同级目录查找
    fix_script = app_parent / "_fix_scripts" / "fix_signature.command"
    if not fix_script.exists():
        # 回退到脚本目录
        fix_script_src = script_dir / "fix_signature.sh"
        if fix_script_src.exists():
            fix_script = app_parent / "fix_signature.command"
            shutil.copy2(fix_script_src, fix_script)
            os.chmod(fix_script, 0o755)

    use_fix_script = fix_script.exists() and fix_script.is_file()
    if use_fix_script:
        print(f"[INFO] Found fix script: {fix_script}")

    # 创建 DMG
    print(f"Creating DMG: {output_path}")
    print(f"  App: {app_path}")
    print(f"  Using: {create_dmg_cmd}")

    cmd = [create_dmg_cmd]

    # 如果有修复脚本，先添加到 DMG
    # 格式: --add-file <target_name> <source> <x> <y>
    if use_fix_script:
        cmd.extend([
            '--add-file', '安装完成后请执行！.command', str(fix_script), '600', '100',
            '--app-drop-link', '150', '100'
        ])

    # 添加其他选项和必需参数
    cmd.extend([
        '--volname', app_name,
        '--window-pos', '200', '120',
        '--window-size', '800', '500',
        '--icon-size', '100',
        str(output_path),
        str(app_path)
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error creating DMG: {result.stderr}")
        return False

    print(f"DMG created successfully: {output_path}")
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  Size: {size_mb:.2f} MB")

    return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Create macOS DMG file')
    parser.add_argument('app_path', type=Path, help='Path to .app directory')
    parser.add_argument('output_path', type=Path, help='Output DMG file path')
    parser.add_argument('--app-name', default='Anime1', help='Application name')

    args = parser.parse_args()

    if not create_dmg(args.app_path, args.output_path, args.app_name):
        sys.exit(1)


if __name__ == "__main__":
    main()
