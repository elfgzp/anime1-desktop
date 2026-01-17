#!/usr/bin/env python3
"""
macOS 应用签名修复脚本

用于修复从 GitHub Actions 下载的 DMG 安装后无法运行的问题。
此问题通常是由于代码签名 Team ID 不匹配导致的。

使用方法:
    # 自动修复
    python scripts/fix_signature.py

    # 指定应用路径
    python scripts/fix_signature.py /Applications/Anime1.app

    # 仅移除 quarantine 属性（不重新签名）
    python scripts/fix_signature.py --quarantine-only
"""
import os
import shutil
import subprocess
import sys
import argparse
from pathlib import Path


def remove_quarantine(app_path: Path) -> bool:
    """移除 com.apple.quarantine 属性"""
    print(f"[1/2] Removing quarantine attribute from {app_path}")

    try:
        result = subprocess.run(
            ["xattr", "-r", "-d", "com.apple.quarantine", str(app_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  [OK] Quarantine attribute removed")
            return True
        else:
            print(f"  [WARN] {result.stderr}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def remove_signatures(app_path: Path) -> bool:
    """移除所有现有的代码签名"""
    print(f"[2/3] Removing existing code signatures from {app_path}")

    # 首先移除 Python.framework 内部的签名（关键步骤）
    python_framework = app_path / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.11"
    if python_framework.exists():
        # 移除 Python.framework 内部的 _CodeSignature
        code_sig_dir = python_framework / "_CodeSignature"
        if code_sig_dir.exists():
            try:
                shutil.rmtree(code_sig_dir)
                print("  [OK] Removed Python.framework _CodeSignature")
            except Exception as e:
                print(f"  [WARN] Could not remove Python.framework _CodeSignature: {e}")

        # 移除 Python 二进制文件的签名
        python_binary = python_framework / "Python"
        if python_binary.exists():
            try:
                subprocess.run(
                    ["codesign", "--remove-signature", str(python_binary)],
                    capture_output=True,
                    text=True
                )
                print("  [OK] Removed Python binary signature")
            except Exception as e:
                print(f"  [WARN] Could not remove Python binary signature: {e}")

        # 移除 libpython 相关的签名（如果有）
        for lib_file in python_framework.glob("libpython*"):
            if lib_file.is_file():
                try:
                    subprocess.run(
                        ["codesign", "--remove-signature", str(lib_file)],
                        capture_output=True,
                        text=True
                    )
                    print(f"  [OK] Removed signature from {lib_file.name}")
                except Exception:
                    pass

    # 移除主应用的签名
    try:
        result = subprocess.run(
            ["codesign", "--remove-signature", str(app_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  [OK] Main app signature removed")
        else:
            print(f"  [INFO] {result.stderr}")
    except Exception as e:
        print(f"  [WARN] Could not remove main signature: {e}")

    # 递归删除 CodeSignature 和 _CodeSignature 目录
    for root, dirs, files in os.walk(str(app_path)):
        for d in dirs:
            if d in ("CodeSignature", "_CodeSignature"):
                code_sig_path = Path(root) / d
                try:
                    shutil.rmtree(code_sig_path)
                    print(f"  [OK] Removed {code_sig_path.name}: {code_sig_path.relative_to(app_path)}")
                except Exception as e:
                    print(f"  [WARN] Could not remove {code_sig_path}: {e}")

    return True


def re_sign_app(app_path: Path) -> bool:
    """使用 adhoc 签名重新签名应用"""
    print(f"[3/3] Re-signing app with adhoc signature...")

    # 先签名嵌套的二进制文件
    for root, dirs, files in os.walk(str(app_path)):
        for file in files:
            file_path = Path(root) / file
            # 检查是否是 Mach-O 可执行文件
            try:
                result = subprocess.run(
                    ["file", str(file_path)],
                    capture_output=True,
                    text=True
                )
                if "Mach-O" in result.stdout:
                    cmd = [
                        "codesign",
                        "--force",
                        "--sign", "-",
                        "--options", "runtime",
                        "--timestamp",
                        str(file_path)
                    ]
                    sign_result = subprocess.run(
                        cmd, capture_output=True, text=True
                    )
                    if sign_result.returncode != 0:
                        print(f"  [WARN] Failed to sign: {file_path.relative_to(app_path)}")
            except Exception:
                pass

    # 然后签名主应用
    cmd = [
        "codesign",
        "--force",
        "--sign", "-",
        "--options", "runtime",
        "--timestamp",
        str(app_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("  [OK] App re-signed successfully")

        # 验证签名
        verify_result = subprocess.run(
            ["codesign", "--verify", str(app_path)],
            capture_output=True,
            text=True
        )
        if verify_result.returncode == 0:
            print("  [OK] Signature verified")
            return True
        else:
            print(f"  [WARN] Verification: {verify_result.stderr}")
            return True  # 签名可能仍然有效
    else:
        print(f"  [ERROR] {result.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix macOS code signature issues for downloaded apps"
    )
    parser.add_argument(
        "app_path",
        nargs="?",
        default="/Applications/Anime1.app",
        help="Path to the app (default: /Applications/Anime1.app)"
    )
    parser.add_argument(
        "--quarantine-only",
        action="store_true",
        help="Only remove quarantine attribute, don't re-sign"
    )
    parser.add_argument(
        "--sign-only",
        action="store_true",
        help="Only re-sign, don't remove quarantine"
    )

    args = parser.parse_args()

    app_path = Path(args.app_path)

    print("=" * 60)
    print("Anime1 Signature Fix Script")
    print("=" * 60)
    print()

    if not app_path.exists():
        print(f"[ERROR] App not found: {app_path}")
        print()
        print("Please make sure Anime1 is installed at:")
        print("  /Applications/Anime1.app")
        print()
        print("Or specify the path:")
        print("  python scripts/fix_signature.py /path/to/Anime1.app")
        sys.exit(1)

    if not app_path.is_dir():
        print(f"[ERROR] Not a directory: {app_path}")
        sys.exit(1)

    print(f"App path: {app_path}")
    print()

    if args.quarantine_only:
        remove_quarantine(app_path)
    elif args.sign_only:
        remove_signatures(app_path)
        re_sign_app(app_path)
    else:
        # 完整修复流程
        remove_quarantine(app_path)
        print()
        remove_signatures(app_path)
        print()
        re_sign_app(app_path)

    print()
    print("=" * 60)
    print("Fix completed!")
    print()
    print("Now try to run Anime1 again:")
    print("  open /Applications/Anime1.app")
    print()
    print("If you still see a warning:")
    print("  1. Right-click Anime1 → 'Open'")
    print("  2. Or go to System Settings → Privacy & Security → 'Open Anyway'")


if __name__ == "__main__":
    main()
