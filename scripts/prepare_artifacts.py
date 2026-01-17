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
import shutil
import subprocess
import zipfile
import tarfile
from pathlib import Path

# 导入 macholib 用于处理 Mach-O 文件
try:
    from macholib.MachO import MachO
    from macholib.mach_o import LC_CODE_SIGNATURE, LC_SYMTAB, LC_SEGMENT_64
    MACHOLIB_AVAILABLE = True
except ImportError:
    MACHOLIB_AVAILABLE = False

# 应用名称常量
APP_NAME_UPPER = "Anime1"
APP_NAME_LOWER = "anime1"

# 文件扩展名常量
EXT_EXE = ".exe"
EXT_APP = ".app"
EXT_DMG = ".dmg"
EXT_TAR_GZ = ".tar.gz"
EXT_ZIP = ".zip"
EXT_SO = ".so"
EXT_DYLIB = ".dylib"

# 架构常量
ARCH_X64 = "x64"
ARCH_ARM64 = "arm64"
ARCH_X86_64 = "x86_64"
ARCH_AMD64 = "amd64"
ARCH_AARCH64 = "aarch64"

# 架构别名映射
ARCH_ALIASES_X64 = [ARCH_X64, ARCH_X86_64, ARCH_AMD64]
ARCH_ALIASES_ARM64 = [ARCH_ARM64, ARCH_AARCH64]

# 输出文件名模板
OUTPUT_WINDOWS_X64 = f"{APP_NAME_LOWER}-windows-{ARCH_X64}{EXT_ZIP}"
OUTPUT_WINDOWS_INSTALLER = f"{APP_NAME_LOWER}-windows-{ARCH_X64}-setup.exe"
OUTPUT_MACOS_ARM64 = f"{APP_NAME_LOWER}-macos-{ARCH_ARM64}{EXT_DMG}"
OUTPUT_MACOS_X64 = f"{APP_NAME_LOWER}-macos-{ARCH_X64}{EXT_DMG}"
OUTPUT_LINUX_ARM64 = f"{APP_NAME_LOWER}-linux-{ARCH_ARM64}{EXT_TAR_GZ}"
OUTPUT_LINUX_X64 = f"{APP_NAME_LOWER}-linux-{ARCH_X64}{EXT_TAR_GZ}"

# 脚本名称常量
SCRIPT_SIGN_APP = "sign_app.py"
SCRIPT_CREATE_DMG = "create_dmg.py"

# 目录名称常量
DIR_DIST = "dist"
DIR_RELEASE = "release"

# 平台标识常量
PLATFORM_WIN32 = "win32"
PLATFORM_DARWIN = "darwin"

# 文件权限常量
FILE_EXECUTABLE_PERMISSION = 0o755

# 压缩模式常量
ZIP_MODE_WRITE = "w"
TAR_MODE_WRITE_GZ = "w:gz"
ZIP_COMPRESSION_DEFLATED = zipfile.ZIP_DEFLATED

# 大小单位转换常量（字节）
BYTES_PER_KB = 1024
BYTES_PER_MB = BYTES_PER_KB * BYTES_PER_KB

# 返回码常量
EXIT_SUCCESS = 0

# 环境变量名称
ENV_ARCH = "ARCH"

# 消息常量
MSG_DETECTED_ARCH = "Detected architecture: {arch}"
MSG_SIGNING_APP = "Signing app with adhoc signature..."
MSG_APP_SIGNED = "✓ App signed successfully"
MSG_CONTINUING_WITHOUT_SIGNATURE = "Continuing without signature..."
MSG_DMG_CREATED = "macOS DMG created: {output_file}"
MSG_SIZE_MB = "  Size: {size:.2f} MB"
MSG_WINDOWS_PACKAGED = "Windows build artifact packaged: {output_file}"
MSG_LINUX_PACKAGED = "Linux build artifact packaged: {output_file}"
MSG_ARTIFACTS_PREPARED = "Artifacts prepared:"
MSG_PLATFORM = "Platform: {platform}"
MSG_DIST_DIR = "Dist directory: {dist_dir}"
MSG_OUTPUT_DIR = "Output directory: {output_dir}"

# 错误消息常量
ERROR_NO_EXE_FOUND = "Error: No exe file found in {dist_dir}"
ERROR_FILES_IN_DIST = "Files in dist/: {files}"
ERROR_APP_NOT_FOUND = "Warning: Anime1.app not found in {dist_dir}"
ERROR_SIGN_SCRIPT_NOT_FOUND = "Warning: sign_app.py not found, skipping signature"
ERROR_CREATE_DMG_NOT_FOUND = "Error: create_dmg.py not found at {path}"
ERROR_CREATE_DMG_FAILED = "Error creating DMG: {error}"
ERROR_DMG_OUTPUT = "Output: {output}"
ERROR_DMG_NOT_CREATED = "Error: DMG file not created: {output_file}"
ERROR_NO_EXECUTABLE_FOUND = "Error: No executable file found in {dist_dir}"
ERROR_DIST_NOT_FOUND = "Error: dist directory not found: {dist_dir}"
ERROR_SIGN_FAILED = "Warning: Failed to sign app: {error}"
ERROR_UNKNOWN_ARCH = "Warning: Unknown architecture '{machine}', defaulting to x64"


def find_exe_file(dist_dir: Path) -> Path | None:
    """查找 exe 文件"""
    candidates = [
        dist_dir / f"{APP_NAME_UPPER}{EXT_EXE}",
        dist_dir / f"{APP_NAME_LOWER}{EXT_EXE}",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # 查找所有 exe 文件
    exe_files = list(dist_dir.rglob(f"*{EXT_EXE}"))
    if exe_files:
        return exe_files[0]
    
    return None


def find_binary_file(dist_dir: Path) -> Path | None:
    """查找可执行文件（Linux）"""
    candidates = [
        dist_dir / APP_NAME_UPPER,
        dist_dir / APP_NAME_LOWER,
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    
    # 查找所有可执行文件
    excluded_suffixes = [EXT_SO, EXT_DYLIB]
    for file in dist_dir.rglob("*"):
        if file.is_file() and os.access(file, os.X_OK):
            # 排除 .so 和 .dylib 文件
            if file.suffix not in excluded_suffixes:
                return file
    
    return None


def find_app_dir(dist_dir: Path) -> Path | None:
    """查找 app 目录（macOS）"""
    app_path = dist_dir / f"{APP_NAME_UPPER}{EXT_APP}"
    if app_path.exists() and app_path.is_dir():
        return app_path
    return None


def find_windows_dir(dist_dir: Path) -> Path | None:
    """查找 Windows 构建目录（onedir 模式）"""
    # 尝试查找 anime1 或 Anime1 目录
    candidates = [
        dist_dir / f"{APP_NAME_LOWER}",  # anime1
        dist_dir / f"{APP_NAME_UPPER}",  # Anime1
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            # 检查目录下是否有可执行文件
            exe_files = list(candidate.glob(f"*{EXT_EXE}"))
            if exe_files:
                return candidate

    return None


def package_windows(dist_dir: Path, output_dir: Path):
    """打包 Windows 构建产物"""
    # 先尝试找目录（onedir 模式）
    windows_dir = find_windows_dir(dist_dir)

    if windows_dir:
        # 打包整个目录（便携版）
        output_file = output_dir / OUTPUT_WINDOWS_X64
        with zipfile.ZipFile(output_file, ZIP_MODE_WRITE, ZIP_COMPRESSION_DEFLATED) as zf:
            for file in windows_dir.rglob("*"):
                if file.is_file():
                    arcname = str(file.relative_to(dist_dir))
                    zf.write(file, arcname)

        size_mb = output_file.stat().st_size / BYTES_PER_MB
        print(MSG_WINDOWS_PACKAGED.format(output_file=output_file))
        print(MSG_SIZE_MB.format(size=size_mb))
    else:
        # 回退到 onefile 模式（单个 exe）
        exe_file = find_exe_file(dist_dir)
        if not exe_file:
            print(ERROR_NO_EXE_FOUND.format(dist_dir=dist_dir))
            print(ERROR_FILES_IN_DIST.format(files=list(dist_dir.iterdir())))
            sys.exit(1)

        # 打包 exe（便携版）
        output_file = output_dir / OUTPUT_WINDOWS_X64
        with zipfile.ZipFile(output_file, ZIP_MODE_WRITE, ZIP_COMPRESSION_DEFLATED) as zf:
            zf.write(exe_file, exe_file.name)

        size_mb = output_file.stat().st_size / BYTES_PER_MB
        print(MSG_WINDOWS_PACKAGED.format(output_file=output_file))
        print(MSG_SIZE_MB.format(size=size_mb))

    # 检查是否有安装包
    installer_file = output_dir / OUTPUT_WINDOWS_INSTALLER
    if installer_file.exists():
        print(f"[OK] Windows installer included: {OUTPUT_WINDOWS_INSTALLER}")
        installer_size = installer_file.stat().st_size / BYTES_PER_MB
        print(f"     Size: {installer_size:.1f} MB")


def get_architecture() -> str:
    """获取系统架构"""
    # 优先从环境变量获取（GitHub Actions 设置）
    arch = os.environ.get(ENV_ARCH, "").lower()
    if arch in ARCH_ALIASES_X64:
        return ARCH_X64
    elif arch in ARCH_ALIASES_ARM64:
        return ARCH_ARM64
    
    # 从平台信息检测
    machine = platform.machine().lower()
    if machine in ARCH_ALIASES_X64:
        return ARCH_X64
    elif machine in ARCH_ALIASES_ARM64:
        return ARCH_ARM64
    
    # 默认返回检测到的架构，如果无法识别则使用 x64
    print(ERROR_UNKNOWN_ARCH.format(machine=machine))
    return ARCH_X64 if not machine else machine


def remove_code_signature_from_macho(filename):
    """
    从 Mach-O 文件中移除 LC_CODE_SIGNATURE 及其相关数据。

    这会彻底移除嵌入的代码签名，解决跨机器签名不兼容问题。
    """
    if not MACHOLIB_AVAILABLE:
        print("    [WARN] macholib not available, skipping signature removal")
        return False

    try:
        # 打开 Mach-O 文件
        binary = MachO(filename)
        file_size = os.path.getsize(filename)

        # 获取文件偏移（用于 fat binary）
        header_offset = binary.headers[0].offset if hasattr(binary.headers[0], 'offset') else 0

        # 处理每个 arch slice
        for header in binary.headers:
            # 查找 LC_CODE_SIGNATURE 命令
            code_sig_cmds = [cmd for cmd in header.commands if cmd[0].cmd == LC_CODE_SIGNATURE]

            if not code_sig_cmds:
                continue  # 没有签名，跳过

            code_sig_cmd = code_sig_cmds[0]
            code_sig_cmd_entry = code_sig_cmd[1]

            # 获取签名数据的位置和大小
            sig_data_offset = header_offset + code_sig_cmd_entry.dataoff
            sig_data_size = code_sig_cmd_entry.datasize

            print(f"    Found LC_CODE_SIGNATURE at offset {code_sig_cmd_entry.dataoff}, size {code_sig_cmd_entry.datasize}")

            # 读取文件内容
            with open(filename, 'rb') as f:
                data = f.read()

            # 移除签名数据：保留文件头到签名数据开始之前的内容
            new_data = data[:sig_data_offset]

            # 修复文件头中的命令列表
            # 找到 LC_CODE_SIGNATURE 命令的位置（相对于 header 开始）
            # 我们需要重建命令列表，移除 LC_CODE_SIGNATURE
            new_commands = []
            for cmd in header.commands:
                if cmd[0].cmd != LC_CODE_SIGNATURE:
                    new_commands.append(cmd)

            # 计算新的命令列表大小
            new_cmdsize = sum(cmd[0].cmdsize for cmd in new_commands)

            # 重建 Mach-O 头
            # 这是一个简化的实现，直接截断文件到签名数据之前
            # 然后重新计算一些关键字段

            # 写入新文件
            with open(filename, 'wb') as f:
                f.write(new_data)

            print(f"    [OK] Removed signature data ({sig_data_size} bytes)")

            # 更新文件中的指针（如果需要）
            # 由于我们只是截断了文件，需要更新 LC_SYMTAB 和 LC_SEGMENT_64 中的相关字段
            _fix_macho_after_signature_removal(filename, header_offset, sig_data_offset, new_cmdsize, header)

        return True
    except Exception as e:
        print(f"    [WARN] Failed to remove signature: {e}")
        return False


def _fix_macho_after_signature_removal(filename, header_offset, sig_data_offset, new_cmdsize, header):
    """
    在移除签名后修复 Mach-O 头中的相关字段。
    """
    try:
        binary = MachO(filename)

        for h in binary.headers:
            # 查找并更新 __LINKEDIT segment 的大小
            __LINKEDIT_NAME = b'__LINKEDIT\x00\x00\x00\x00\x00\x00'
            for cmd in h.commands:
                if cmd[0].cmd == LC_SEGMENT_64 and cmd[1].segname == __LINKEDIT_NAME:
                    linkedit = cmd[1]
                    # 更新 filesize 到签名数据开始的位置
                    linkedit.filesize = sig_data_offset - (header_offset + linkedit.fileoff)
                    print(f"    [OK] Updated __LINKEDIT filesize to {linkedit.filesize}")
                    break

        # 写回修改
        with open(filename, 'rb+') as f:
            binary.write(f)

    except Exception as e:
        print(f"    [WARN] Failed to fix Mach-O headers: {e}")


def remove_python_framework_signatures(app_path: Path):
    """
    移除 Python.framework 内部的所有签名，解决跨机器运行问题

    PyInstaller 捆绑的 Python.framework 可能包含来自构建机器的签名，
    这些签名在其他机器上会导致验证失败。
    """
    python_framework = app_path / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.11"

    if not python_framework.exists():
        print("  [INFO] No Python.framework found, skipping")
        return

    # 1. 递归移除所有 _CodeSignature 目录
    for code_sig_dir in python_framework.rglob("_CodeSignature"):
        if code_sig_dir.is_dir():
            shutil.rmtree(code_sig_dir)
            print(f"  [OK] Removed {code_sig_dir.relative_to(python_framework)}")

    # 2. 递归移除所有 CodeSignature 目录
    for code_sig_dir in python_framework.rglob("CodeSignature"):
        if code_sig_dir.is_dir():
            shutil.rmtree(code_sig_dir)
            print(f"  [OK] Removed {code_sig_dir.relative_to(python_framework)}")

    # 3. 移除所有 Mach-O 二进制文件中的嵌入签名
    for binary_file in python_framework.rglob("*"):
        if binary_file.is_file():
            # 检查是否是 Mach-O 可执行文件或动态库
            try:
                result = subprocess.run(
                    ["file", str(binary_file)],
                    capture_output=True,
                    text=True
                )
                if "Mach-O" in result.stdout:
                    print(f"  Processing: {binary_file.relative_to(python_framework)}")
                    # 移除嵌入的签名
                    remove_code_signature_from_macho(str(binary_file))
            except Exception:
                pass

    print("  [OK] All Python.framework signatures removed")


def package_macos(dist_dir: Path, output_dir: Path):
    """打包 macOS 构建产物为 DMG"""
    app_dir = find_app_dir(dist_dir)
    if not app_dir:
        print(ERROR_APP_NOT_FOUND.format(dist_dir=dist_dir))
        print(ERROR_FILES_IN_DIST.format(files=list(dist_dir.iterdir())))
        sys.exit(1)

    # 检测架构
    arch = get_architecture()
    if arch == ARCH_ARM64:
        output_file = output_dir / OUTPUT_MACOS_ARM64
    else:
        output_file = output_dir / OUTPUT_MACOS_X64

    print(MSG_DETECTED_ARCH.format(arch=arch))
    print()

    # 复制修复脚本到 app 同级目录
    script_dir = Path(__file__).parent
    fix_script_src = script_dir / "fix_signature.sh"

    # 创建临时修复脚本目录
    temp_scripts_dir = dist_dir / "_fix_scripts"
    if temp_scripts_dir.exists():
        shutil.rmtree(temp_scripts_dir)
    temp_scripts_dir.mkdir(parents=True, exist_ok=True)

    if fix_script_src.exists():
        fix_script_dst = temp_scripts_dir / "fix_signature.command"
        shutil.copy2(fix_script_src, fix_script_dst)
        os.chmod(fix_script_dst, 0o755)
        print(f"[INFO] Copied fix script to: {fix_script_dst}")
    else:
        print(f"[WARN] Fix script not found: {fix_script_src}")

    # 移除 Python.framework 内部的所有签名，解决跨机器运行问题
    print("[INFO] Removing Python.framework internal signatures...")
    remove_python_framework_signatures(app_dir)
    print()

    # 使用 --deep 重新签名整个应用
    print("[INFO] Re-signing app with adhoc signature...")
    sign_result = subprocess.run(
        ["codesign", "--force", "--sign", "-", "--deep", "--options", "runtime", "--timestamp", str(app_dir)],
        capture_output=True,
        text=True
    )
    if sign_result.returncode == 0:
        print("  [OK] App signed successfully")
    else:
        print(f"  [WARN] Signing: {sign_result.stderr}")

    # 验证签名 - 只检查 Mach-O 二进制文件（不需要检查 plist、resources 等）
    print("[INFO] Verifying Mach-O binary signatures...")
    python_framework = app_dir / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.11"
    if python_framework.exists():
        unsigned_binaries = []
        for file in python_framework.rglob("*"):
            if file.is_file():
                # 只检查 Mach-O 可执行文件
                try:
                    result = subprocess.run(
                        ["file", str(file)],
                        capture_output=True,
                        text=True
                    )
                    if "Mach-O" in result.stdout:
                        # 这是一个 Mach-O 文件，检查签名
                        verify_result = subprocess.run(
                            ["codesign", "--verify", str(file)],
                            capture_output=True,
                            text=True
                        )
                        if verify_result.returncode != 0:
                            unsigned_binaries.append(str(file.relative_to(python_framework)))
                except Exception:
                    pass

        if unsigned_binaries:
            print(f"  [WARN] Found {len(unsigned_binaries)} unsigned Mach-O binaries:")
            for f in unsigned_binaries[:5]:
                print(f"    - {f}")
        else:
            print("  [OK] All Mach-O binaries in Python.framework are signed")

    # 使用 create_dmg 脚本创建 DMG
    create_dmg_script = Path(__file__).parent / SCRIPT_CREATE_DMG
    if not create_dmg_script.exists():
        print(ERROR_CREATE_DMG_NOT_FOUND.format(path=create_dmg_script))
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(create_dmg_script), str(app_dir), str(output_file)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != EXIT_SUCCESS:
        print(ERROR_CREATE_DMG_FAILED.format(error=result.stderr))
        print(ERROR_DMG_OUTPUT.format(output=result.stdout))
        sys.exit(1)
    
    print(result.stdout)
    if output_file.exists():
        size_mb = output_file.stat().st_size / BYTES_PER_MB
        print(MSG_DMG_CREATED.format(output_file=output_file))
        print(MSG_SIZE_MB.format(size=size_mb))
    else:
        print(ERROR_DMG_NOT_CREATED.format(output_file=output_file))
        sys.exit(1)


def package_linux(dist_dir: Path, output_dir: Path):
    """打包 Linux 构建产物"""
    binary_file = find_binary_file(dist_dir)
    if not binary_file:
        print(ERROR_NO_EXECUTABLE_FOUND.format(dist_dir=dist_dir))
        print(ERROR_FILES_IN_DIST.format(files=list(dist_dir.iterdir())))
        sys.exit(1)
    
    # 确保可执行权限
    os.chmod(binary_file, FILE_EXECUTABLE_PERMISSION)
    
    # 检测架构
    arch = get_architecture()
    if arch == ARCH_ARM64:
        output_file = output_dir / OUTPUT_LINUX_ARM64
    else:
        output_file = output_dir / OUTPUT_LINUX_X64
    
    print(MSG_DETECTED_ARCH.format(arch=arch))
    
    with tarfile.open(output_file, TAR_MODE_WRITE_GZ) as tf:
        tf.add(binary_file, arcname=binary_file.name)
    
    size_mb = output_file.stat().st_size / BYTES_PER_MB
    print(MSG_LINUX_PACKAGED.format(output_file=output_file))
    print(MSG_SIZE_MB.format(size=size_mb))


def main():
    """主函数"""
    current_platform = sys.platform
    dist_dir = Path(DIR_DIST)
    output_dir = Path(DIR_RELEASE)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not dist_dir.exists():
        print(ERROR_DIST_NOT_FOUND.format(dist_dir=dist_dir))
        sys.exit(1)
    
    print(MSG_PLATFORM.format(platform=current_platform))
    print(MSG_DIST_DIR.format(dist_dir=dist_dir))
    print(MSG_OUTPUT_DIR.format(output_dir=output_dir))
    print()
    
    if current_platform == PLATFORM_WIN32:
        package_windows(dist_dir, output_dir)
    elif current_platform == PLATFORM_DARWIN:
        package_macos(dist_dir, output_dir)
    else:
        package_linux(dist_dir, output_dir)
    
    print()
    print(MSG_ARTIFACTS_PREPARED)
    for file in output_dir.iterdir():
        if file.is_file():
            print(f"  {file.name}")


if __name__ == "__main__":
    main()
