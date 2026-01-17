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
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
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


def process_directory(directory: Path, pattern: str = "*.js"):
    """处理目录中的所有匹配文件"""
    if not directory.exists():
        print(f"[WARN] Directory not found: {directory}")
        return 0

    files = list(directory.rglob(pattern))

    print(f"[INFO] Found {len(files)} {pattern} files in {directory}")

    count = 0
    for js_file in files:
        if remove_unicode_from_js(js_file):
            count += 1

    return count


def main():
    project_root = Path(__file__).parent.parent

    # 处理 static 目录
    static_dir = project_root / "static"
    print(f"[INFO] Processing static directory: {static_dir}")
    static_count = process_directory(static_dir, "*.js")

    # 处理 frontend/node_modules (如果存在)
    frontend_modules = project_root / "frontend" / "node_modules"
    if frontend_modules.exists():
        print(f"[INFO] Processing node_modules: {frontend_modules}")
        # 只处理 video.js 和 hls.js 相关文件
        video_js_files = list(frontend_modules.rglob("video.js/**/*.js"))
        hls_js_files = list(frontend_modules.rglob("hls.js/**/*.js"))
        videojs_dirs = list((frontend_modules / "video.js").glob("*"))
        for d in videojs_dirs:
            if d.is_dir() and d.name not in ['dist', 'es', 'src']:
                video_js_files.extend(list(d.rglob("*.js")))
        modules_count = process_directory(frontend_modules, "*.js")
        print(f"[INFO] Cleaned {modules_count} files in node_modules")
    else:
        print(f"[INFO] No node_modules found at {frontend_modules}")

    total = static_count
    print(f"[OK] Unicode cleanup complete. Total files processed: {total}")


if __name__ == "__main__":
    main()
