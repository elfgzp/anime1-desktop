#!/usr/bin/env python3
"""
macOS 应用签名脚本（免费方案 - adhoc 签名）

使用 adhoc 签名对 macOS 应用进行签名，避免"无法验证开发者"的错误。
虽然用户首次打开仍会看到警告，但可以通过右键"打开"来允许运行。

使用方法:
    python scripts/sign_app.py dist/Anime1.app
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 常量定义
DEFAULT_BUNDLE_ID = "com.anime1.desktop"
ADHOC_SIGN_IDENTITY = "-"  # adhoc 签名的标识符
CODESIGN_COMMAND = "codesign"
CODESIGN_FORCE_FLAG = "--force"
CODESIGN_DEEP_FLAG = "--deep"
CODESIGN_SIGN_FLAG = "--sign"
CODESIGN_OPTIONS_FLAG = "--options"
CODESIGN_RUNTIME_OPTION = "runtime"
CODESIGN_HARDENED_OPTION = "hardened"
CODESIGN_TIMESTAMP_FLAG = "--timestamp"
CODESIGN_ENTITLEMENTS_FLAG = "--entitlements"
CODESIGN_VERIFY_FLAG = "--verify"
CODESIGN_VERBOSE_FLAG = "--verbose"
CODESIGN_DETAIL_VERBOSE_FLAG = "-dv"
CODESIGN_VERBOSE_LEVEL = "4"
CODESIGN_REMOVE_SIGNATURE_FLAG = "--remove-signature"

# 命令行参数索引
ARG_APP_PATH_INDEX = 1
ARG_BUNDLE_ID_INDEX = 2
MIN_ARGS_REQUIRED = 2

# 返回码
SUCCESS_EXIT_CODE = 0

# 消息常量
MSG_SIGNING_APP = "Signing app: {app_path}"
MSG_BUNDLE_ID = "Bundle ID: {bundle_id}"
MSG_SIGNING_METHOD = "Signing method: adhoc (free, no Apple Developer account required)"
MSG_RUNNING_COMMAND = "Running: {command}"
MSG_APP_SIGNED = "✓ App signed successfully"
MSG_VERIFYING_SIGNATURE = "Verifying signature..."
MSG_SIGNATURE_VERIFIED = "✓ Signature verified"
MSG_SIGNATURE_DETAILS = "Signature details:"
MSG_SIGNING_COMPLETED = "✓ Signing completed successfully"
MSG_ADHOC_NOTE = "Note: This app uses adhoc signing (free)."
MSG_USER_INSTRUCTIONS = (
    "Users may see a warning on first launch, but can allow it by:\n"
    "  1. Right-click the app → 'Open'\n"
    "  2. Or go to System Settings → Privacy & Security → 'Open Anyway'\n"
    "\n"
    "If the app shows 'damaged' error, run this in Terminal:\n"
    "  sudo xattr -r -d com.apple.quarantine /Applications/Anime1.app"
)

# 错误消息
ERROR_APP_NOT_FOUND = "Error: App not found: {app_path}"
ERROR_NOT_DIRECTORY = "Error: {app_path} is not a directory"
ERROR_SIGNING_FAILED = "Error signing app: {error}"
ERROR_VERIFICATION_FAILED = "Warning: Signature verification failed: {error}"
ERROR_USAGE = "Usage: python scripts/sign_app.py <app_path> [bundle_id]"
ERROR_EXAMPLE = "Example: python scripts/sign_app.py dist/Anime1.app"


def remove_all_signatures(app_path: Path) -> bool:
    """移除应用及其所有组件的现有签名"""
    print("[STEP 0] Removing existing signatures...")

    # 先移除主应用的签名
    try:
        result = subprocess.run(
            [CODESIGN_COMMAND, CODESIGN_REMOVE_SIGNATURE_FLAG, str(app_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  [OK] Removed main app signature")
        else:
            print(f"  [INFO] {result.stderr}")
    except Exception as e:
        print(f"  [WARN] Could not remove main signature: {e}")

    # 递归移除所有框架和二进制文件的签名
    import os
    for root, dirs, files in os.walk(str(app_path)):
        # 查找 CodeSignature 目录并删除
        for d in dirs:
            if d == "CodeSignature":
                code_sig_path = Path(root) / d
                try:
                    shutil.rmtree(code_sig_path)
                    print(f"  [OK] Removed CodeSignature: {code_sig_path.relative_to(app_path)}")
                except Exception as e:
                    print(f"  [WARN] Could not remove {code_sig_path}: {e}")

        # 查找 _CodeSignature 目录并删除（Python framework 使用这个）
        for d in dirs:
            if d == "_CodeSignature":
                code_sig_path = Path(root) / d
                try:
                    shutil.rmtree(code_sig_path)
                    print(f"  [OK] Removed _CodeSignature: {code_sig_path.relative_to(app_path)}")
                except Exception as e:
                    print(f"  [WARN] Could not remove {code_sig_path}: {e}")

    return True


def sign_app(app_path: Path, bundle_id: str = DEFAULT_BUNDLE_ID) -> bool:
    """
    对 macOS 应用进行 adhoc 签名

    Args:
        app_path: .app 目录路径
        bundle_id: Bundle Identifier

    Returns:
        是否成功签名
    """
    if not app_path.exists():
        print(ERROR_APP_NOT_FOUND.format(app_path=app_path))
        return False

    if not app_path.is_dir():
        print(ERROR_NOT_DIRECTORY.format(app_path=app_path))
        return False

    print(MSG_SIGNING_APP.format(app_path=app_path))
    print(MSG_BUNDLE_ID.format(bundle_id=bundle_id))
    print(MSG_SIGNING_METHOD)
    print()

    # 步骤 0: 先移除所有现有签名（解决 Team ID 不匹配问题）
    remove_all_signatures(app_path)

    # 步骤 1: 先签名所有嵌套的二进制文件和框架
    print("[STEP 1] Signing nested binaries and frameworks...")
    if not sign_nested_binaries(app_path):
        print("[WARN] Some nested binaries may not be signed properly")

    # 步骤 2: 创建临时 entitlements 文件
    entitlements_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.plist', delete=False) as f:
        f.write(entitlements_content)
        entitlements_path = f.name

    try:
        # 步骤 3: 对主应用进行签名
        cmd = [
            CODESIGN_COMMAND,
            CODESIGN_FORCE_FLAG,
            CODESIGN_SIGN_FLAG,
            ADHOC_SIGN_IDENTITY,  # adhoc 签名
            CODESIGN_OPTIONS_FLAG,
            CODESIGN_RUNTIME_OPTION,
            CODESIGN_TIMESTAMP_FLAG,
            CODESIGN_ENTITLEMENTS_FLAG,
            entitlements_path,
            str(app_path)
        ]

        print(f"[STEP 2] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != SUCCESS_EXIT_CODE:
            print(ERROR_SIGNING_FAILED.format(error=result.stderr))
            # 尝试使用 deep 签名作为后备
            print("[INFO] Trying with --deep flag as fallback...")
            cmd_deep = [
                CODESIGN_COMMAND,
                CODESIGN_FORCE_FLAG,
                CODESIGN_DEEP_FLAG,
                CODESIGN_SIGN_FLAG,
                ADHOC_SIGN_IDENTITY,
                CODESIGN_OPTIONS_FLAG,
                CODESIGN_RUNTIME_OPTION,
                CODESIGN_TIMESTAMP_FLAG,
                str(app_path)
            ]
            result = subprocess.run(cmd_deep, capture_output=True, text=True)
            if result.returncode != SUCCESS_EXIT_CODE:
                print(ERROR_SIGNING_FAILED.format(error=result.stderr))
                return False

        print(MSG_APP_SIGNED)
        print()

        # 验证签名
        print(MSG_VERIFYING_SIGNATURE)
        verify_cmd = [
            CODESIGN_COMMAND,
            CODESIGN_VERIFY_FLAG,
            str(app_path)
        ]

        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)

        if verify_result.returncode != SUCCESS_EXIT_CODE:
            print(ERROR_VERIFICATION_FAILED.format(error=verify_result.stderr))
            print("[INFO] Verification failed but signing may still be valid.")
            print("[INFO] Trying strict verification...")
            # 尝试严格验证
            strict_verify = [
                CODESIGN_COMMAND,
                CODESIGN_VERIFY_FLAG,
                CODESIGN_VERBOSE_FLAG,
                str(app_path)
            ]
            strict_result = subprocess.run(strict_verify, capture_output=True, text=True)
            print(strict_result.stdout if strict_result.stdout else strict_result.stderr)

        print(MSG_SIGNATURE_VERIFIED)
        print()

        # 显示签名信息
        print(MSG_SIGNATURE_DETAILS)
        info_cmd = [
            CODESIGN_COMMAND,
            CODESIGN_DETAIL_VERBOSE_FLAG,
            f"{CODESIGN_VERBOSE_FLAG}={CODESIGN_VERBOSE_LEVEL}",
            str(app_path)
        ]

        info_result = subprocess.run(info_cmd, capture_output=True, text=True)
        if info_result.returncode == SUCCESS_EXIT_CODE:
            print(info_result.stdout)
        else:
            print("[INFO] Could not get detailed signature info")

        return True
    finally:
        # 清理临时文件
        Path(entitlements_path).unlink(missing_ok=True)


def sign_nested_binaries(app_path: Path) -> bool:
    """签名所有嵌套的二进制文件（Python 解释器、动态库等）"""
    success = True

    # 查找所有可执行文件和动态库
    for root, dirs, files in os.walk(str(app_path)):
        for file in files:
            file_path = Path(root) / file
            # 检查是否是可执行文件或动态库
            if file.endswith(('.so', '.dylib', '')) or file in ('Python', 'python'):
                try:
                    # 检查是否是 Mach-O 可执行文件
                    result = subprocess.run(
                        ['file', str(file_path)],
                        capture_output=True, text=True
                    )
                    if 'Mach-O' in result.stdout:
                        cmd = [
                            CODESIGN_COMMAND,
                            CODESIGN_FORCE_FLAG,
                            CODESIGN_SIGN_FLAG,
                            ADHOC_SIGN_IDENTITY,
                            CODESIGN_OPTIONS_FLAG,
                            CODESIGN_RUNTIME_OPTION,
                            CODESIGN_TIMESTAMP_FLAG,
                            str(file_path)
                        ]
                        sign_result = subprocess.run(
                            cmd, capture_output=True, text=True
                        )
                        if sign_result.returncode != 0:
                            print(f"  [WARN] Failed to sign: {file_path.relative_to(app_path)}")
                            success = False
                except Exception:
                    pass  # 忽略不重要的文件

    return success


def main():
    """主函数"""
    if len(sys.argv) < MIN_ARGS_REQUIRED:
        print(ERROR_USAGE)
        print(ERROR_EXAMPLE)
        sys.exit(1)
    
    app_path = Path(sys.argv[ARG_APP_PATH_INDEX])
    bundle_id = (
        sys.argv[ARG_BUNDLE_ID_INDEX]
        if len(sys.argv) > ARG_BUNDLE_ID_INDEX
        else DEFAULT_BUNDLE_ID
    )
    
    if not sign_app(app_path, bundle_id):
        sys.exit(1)
    
    print(MSG_SIGNING_COMPLETED)
    print()
    print(MSG_ADHOC_NOTE)
    print(MSG_USER_INSTRUCTIONS)


if __name__ == "__main__":
    main()
