#!/usr/bin/env python3
"""
macOS 应用签名脚本（免费方案 - adhoc 签名）

使用 adhoc 签名对 macOS 应用进行签名，避免"无法验证开发者"的错误。
虽然用户首次打开仍会看到警告，但可以通过右键"打开"来允许运行。

使用方法:
    python scripts/sign_app.py dist/Anime1.app
"""
import subprocess
import sys
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
CODESIGN_TIMESTAMP_FLAG = "--timestamp"
CODESIGN_ENTITLEMENTS_FLAG = "--entitlements"
CODESIGN_VERIFY_FLAG = "--verify"
CODESIGN_VERBOSE_FLAG = "--verbose"
CODESIGN_DETAIL_VERBOSE_FLAG = "-dv"
CODESIGN_VERBOSE_LEVEL = "4"

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
    "  2. Or go to System Settings → Privacy & Security → 'Open Anyway'"
)

# 错误消息
ERROR_APP_NOT_FOUND = "Error: App not found: {app_path}"
ERROR_NOT_DIRECTORY = "Error: {app_path} is not a directory"
ERROR_SIGNING_FAILED = "Error signing app: {error}"
ERROR_VERIFICATION_FAILED = "Warning: Signature verification failed: {error}"
ERROR_USAGE = "Usage: python scripts/sign_app.py <app_path> [bundle_id]"
ERROR_EXAMPLE = "Example: python scripts/sign_app.py dist/Anime1.app"


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
    
    # 使用 adhoc 签名（- 表示使用临时签名）
    # 这会创建一个有效的签名，但不会通过 Apple 的公证
    cmd = [
        CODESIGN_COMMAND,
        CODESIGN_FORCE_FLAG,
        CODESIGN_DEEP_FLAG,
        CODESIGN_SIGN_FLAG,
        ADHOC_SIGN_IDENTITY,  # adhoc 签名
        CODESIGN_OPTIONS_FLAG,
        CODESIGN_RUNTIME_OPTION,  # 启用 hardened runtime（可选，但推荐）
        CODESIGN_TIMESTAMP_FLAG,  # 添加时间戳
        CODESIGN_ENTITLEMENTS_FLAG,
        ADHOC_SIGN_IDENTITY,  # 使用默认 entitlements
        str(app_path)
    ]
    
    print(MSG_RUNNING_COMMAND.format(command=" ".join(cmd)))
    result = subprocess.run(cmd, capture_output=True, text=True)
    
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
        CODESIGN_VERBOSE_FLAG,
        str(app_path)
    ]
    
    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
    
    if verify_result.returncode != SUCCESS_EXIT_CODE:
        print(ERROR_VERIFICATION_FAILED.format(error=verify_result.stderr))
        return False
    
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
    
    return True


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
