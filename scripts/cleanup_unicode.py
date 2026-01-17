#!/usr/bin/env python3
"""
移除 JavaScript 文件中的 Unicode 字符，解决 Windows 构建时的编码问题。
"""
import os
import re
from pathlib import Path


def remove_unicode_from_js(file_path: Path):
    """移除 JavaScript 文件中的 Unicode 符号字符"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 移除常见的 Unicode 符号
        unicode_symbols = [
            '✓',  # U+2713 check mark
            '✔',  # U+2714 heavy check mark
            '✗',  # U+2717 ballot X
            '✘',  # U+2718 heavy ballot X
        ]

        for symbol in unicode_symbols:
            content = content.replace(symbol, '[OK]')

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [OK] Removed Unicode symbols from: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"  [WARN] Failed to process {file_path}: {e}")
        return False


def process_static_directory(static_dir: Path):
    """处理 static 目录中的所有 JS 文件"""
    if not static_dir.exists():
        print(f"[WARN] Static directory not found: {static_dir}")
        return

    js_files = list(static_dir.rglob("*.js"))

    print(f"[INFO] Found {len(js_files)} JavaScript files in {static_dir}")

    for js_file in js_files:
        remove_unicode_from_js(js_file)


def main():
    project_root = Path(__file__).parent.parent
    static_dir = project_root / "static"

    print(f"[INFO] Processing static directory: {static_dir}")
    process_static_directory(static_dir)
    print("[OK] Unicode cleanup complete")


if __name__ == "__main__":
    main()
