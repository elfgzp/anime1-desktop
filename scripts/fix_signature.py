#!/usr/bin/env python3
"""
Anime1 签名修复脚本

用于修复从 GitHub Actions 下载的 DMG 安装后无法运行的问题。
此问题通常是由于代码签名 Team ID 不匹配导致的。

使用方法:
    # 自动修复
    python scripts/fix_signature.py

    # 指定应用路径
    python scripts/fix_signature.py /Applications/Anime1.app
"""
import os
import shutil
import subprocess
import struct
import sys
from pathlib import Path


def remove_code_signature_from_macho(filename):
    """从 Mach-O 文件中直接移除 LC_CODE_SIGNATURE 及其相关数据"""
    try:
        with open(filename, 'rb') as f:
            data = bytearray(f.read())

        if len(data) < 32:
            print(f"    [WARN] 文件太短，无法是有效的 Mach-O")
            return False

        # 解析 mach_header_64
        magic = struct.unpack('<I', data[0:4])[0]
        cputype = struct.unpack('<I', data[4:8])[0]
        cpusubtype = struct.unpack('<I', data[8:12])[0]
        filetype = struct.unpack('<I', data[12:16])[0]
        ncmds = struct.unpack('<I', data[16:20])[0]
        sizeofcmds = struct.unpack('<I', data[20:24])[0]
        flags = struct.unpack('<I', data[24:28])[0]
        reserved = struct.unpack('<I', data[28:32])[0]

        # 读取所有命令
        cmd_offset = 32
        cmds = []
        for i in range(ncmds):
            cmd = struct.unpack('<I', data[cmd_offset:cmd_offset+4])[0]
            cmdsize = struct.unpack('<I', data[cmd_offset+4:cmd_offset+8])[0]
            cmds.append({
                'cmd': cmd,
                'cmdsize': cmdsize,
                'offset': cmd_offset,
                'data': data[cmd_offset:cmd_offset+cmdsize]
            })
            cmd_offset += cmdsize

        # 查找 LC_CODE_SIGNATURE
        sig_idx = None
        for i, c in enumerate(cmds):
            if c['cmd'] == 0x1d:  # LC_CODE_SIGNATURE
                sig_idx = i
                break

        if sig_idx is None:
            print(f"    [INFO] 没有找到 LC_CODE_SIGNATURE")
            return True

        sig_cmd = cmds[sig_idx]
        sig_data_off = struct.unpack('<I', sig_cmd['data'][8:12])[0]
        sig_data_size = struct.unpack('<I', sig_cmd['data'][12:16])[0]

        print(f"    找到 LC_CODE_SIGNATURE: offset={sig_data_off}, size={sig_data_size}")

        # 移除 LC_CODE_SIGNATURE
        cmds = [c for c in cmds if c['cmd'] != 0x1d]
        new_ncmds = len(cmds)
        new_sizeofcmds = sum(c['cmdsize'] for c in cmds)

        # 更新 __LINKEDIT segment 的 filesize 和 vmsize
        for cmd in cmds:
            if cmd['cmd'] == 0x19:  # LC_SEGMENT_64
                segname = cmd['data'][:16]
                if b'__LINKEDIT' in segname:
                    fileoff = struct.unpack('<Q', cmd['data'][32:40])[0]
                    new_filesize = sig_data_off - fileoff
                    print(f"    更新 __LINKEDIT filesize: {new_filesize}")
                    # filesize 在 offset + 48
                    struct.pack_into('<Q', cmd['data'], 48, new_filesize)
                    # vmsize 在 offset + 24
                    struct.pack_into('<Q', cmd['data'], 24, new_filesize)
                    break

        # 重建文件
        new_data = bytearray()
        new_data.extend(struct.pack('<I', magic))
        new_data.extend(struct.pack('<I', cputype))
        new_data.extend(struct.pack('<I', cpusubtype))
        new_data.extend(struct.pack('<I', filetype))
        new_data.extend(struct.pack('<I', new_ncmds))
        new_data.extend(struct.pack('<I', new_sizeofcmds))
        new_data.extend(struct.pack('<I', flags))
        new_data.extend(struct.pack('<I', reserved))

        # 添加剩余命令
        for c in cmds:
            new_data.extend(c['data'])

        # 添加命令之后、签名数据之前的原始内容
        content_end = 32 + sizeofcmds  # 原始 sizeofcmds
        new_data.extend(data[content_end:sig_data_off])

        # 写回文件
        with open(filename, 'wb') as f:
            f.write(new_data)

        print(f"    [OK] 已移除签名数据, 新文件大小: {len(new_data)}")
        return True

    except Exception as e:
        print(f"    [WARN] 移除签名失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def remove_quarantine(app_path):
    """移除 quarantine 属性"""
    try:
        result = subprocess.run(
            ['xattr', '-rd', 'com.apple.quarantine', str(app_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  [OK] 已移除 quarantine 属性")
            return True
        else:
            print(f"  [WARN] 移除 quarantine 失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"  [WARN] 移除 quarantine 出错: {e}")
        return False


def remove_signatures(app_path):
    """移除应用中的所有代码签名"""
    # 移除 _CodeSignature 目录
    for code_sig_dir in app_path.rglob("_CodeSignature"):
        if code_sig_dir.is_dir():
            shutil.rmtree(code_sig_dir)
            print(f"  [OK] 已删除 {code_sig_dir.relative_to(app_path)}")

    # 移除 CodeSignature 目录
    for code_sig_dir in app_path.rglob("CodeSignature"):
        if code_sig_dir.is_dir():
            shutil.rmtree(code_sig_dir)
            print(f"  [OK] 已删除 {code_sig_dir.relative_to(code_sig_dir)}")

    # 处理所有 Mach-O 二进制
    python_framework = app_path / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.11"

    if not python_framework.exists():
        print("  [INFO] 未找到 Python.framework")
        return

    macho_binaries = []
    for binary_file in python_framework.rglob("*"):
        if binary_file.is_file():
            try:
                result = subprocess.run(
                    ["file", str(binary_file)],
                    capture_output=True,
                    text=True
                )
                if "Mach-O" in result.stdout:
                    macho_binaries.append(binary_file)
            except Exception:
                pass

    print(f"  [INFO] 找到 {len(macho_binaries)} 个 Mach-O 二进制文件")

    for binary_file in macho_binaries:
        print(f"  处理: {binary_file.relative_to(python_framework)}")
        remove_code_signature_from_macho(str(binary_file))


def re_sign_app(app_path):
    """重新签名应用"""
    print("  [INFO] 重新签名所有二进制文件...")

    # 收集所有 Mach-O 二进制
    python_framework = app_path / "Contents" / "Frameworks" / "Python.framework" / "Versions" / "3.11"

    if not python_framework.exists():
        print("  [WARN] 未找到 Python.framework")
        return False

    macho_binaries = []
    for binary_file in python_framework.rglob("*"):
        if binary_file.is_file():
            try:
                result = subprocess.run(
                    ["file", str(binary_file)],
                    capture_output=True,
                    text=True
                )
                if "Mach-O" in result.stdout:
                    macho_binaries.append(binary_file)
            except Exception:
                pass

    # 签名 Python 二进制
    python_bin = python_framework / "3.11" / "Python"
    if python_bin.exists():
        print(f"  签名: Python")
        subprocess.run(
            ["codesign", "--force", "--sign", "-", "--options", "runtime", "--timestamp", str(python_bin)],
            capture_output=True
        )

    # 签名主应用
    main_bin = app_path / "Contents" / "MacOS" / "Anime1"
    if main_bin.exists():
        print(f"  签名: Anime1")
        subprocess.run(
            ["codesign", "--force", "--sign", "-", "--options", "runtime", "--timestamp", str(main_bin)],
            capture_output=True
        )

    # 使用 --deep 签名整个应用
    print(f"  签名: 整个应用 (--deep)")
    result = subprocess.run(
        ["codesign", "--force", "--sign", "-", "--deep", "--options", "runtime", "--timestamp", str(app_path)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("  [OK] 应用签名完成")
        return True
    else:
        print(f"  [WARN] 签名失败: {result.stderr}")
        return False


def test_app(app_path):
    """测试应用是否能运行"""
    print("  [INFO] 测试应用...")

    main_bin = app_path / "Contents" / "MacOS" / "Anime1"
    if not main_bin.exists():
        print("  [WARN] 未找到主可执行文件")
        return False

    # 尝试运行应用
    result = subprocess.run(
        [str(main_bin), "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode == 0:
        print(f"  [OK] 应用运行成功")
        print(f"       输出: {result.stdout.strip()}")
        return True
    else:
        print(f"  [WARN] 应用运行失败")
        print(f"       错误: {result.stderr.strip()}")
        return False


def main():
    """主函数"""
    # 确定应用路径
    if len(sys.argv) > 1:
        app_path = Path(sys.argv[1])
    else:
        app_path = Path("/Applications/Anime1.app")

    if not app_path.exists():
        print(f"错误: 应用不存在 {app_path}")
        print("请指定正确的应用路径:")
        print(f"  python {sys.argv[0]} /Applications/Anime1.app")
        sys.exit(1)

    print(f"修复签名: {app_path}")
    print()

    # 移除 quarantine 属性
    print("1. 移除 quarantine 属性...")
    remove_quarantine(app_path)
    print()

    # 移除签名
    print("2. 移除代码签名...")
    remove_signatures(app_path)
    print()

    # 重新签名
    print("3. 重新签名...")
    re_sign_app(app_path)
    print()

    # 测试
    print("4. 测试应用...")
    if test_app(app_path):
        print()
        print("修复完成！应用应该可以正常运行了。")
    else:
        print()
        print("警告: 应用测试失败。请查看错误信息。")
        print("可能需要重启电脑后再次尝试。")

    # 清理临时文件
    if app_path / "Contents" / "_CodeSignature" in list(app_path.rglob("_CodeSignature")):
        pass  # 已经在 remove_signatures 中清理了


if __name__ == "__main__":
    main()
