#!/usr/bin/env python3
"""
注入 Vite 构建后的资源路径到 Vue index.html。

Vite 构建后会生成 manifest.json，包含所有资源的映射关系。
此脚本读取 manifest 并更新 static/dist/index.html 中的资源路径。
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIST = PROJECT_ROOT / "static" / "dist"
INDEX_HTML_PATH = STATIC_DIST / "index.html"

# Vite 5 生成 manifest.json 在 .vite/ 目录下
MANIFEST_PATH = STATIC_DIST / ".vite" / "manifest.json"


def inject_assets():
    """读取 manifest 并更新 index.html 中的资源路径。"""
    if not MANIFEST_PATH.exists():
        print(f"Warning: Manifest not found at {MANIFEST_PATH}")
        print("Skipping asset injection. Make sure to run 'npm run build' first.")
        return

    if not INDEX_HTML_PATH.exists():
        print(f"Warning: Vue index.html not found at {INDEX_HTML_PATH}")
        return

    # 读取 manifest
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # 读取 index.html
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 查找 CSS 和 JS 文件
    css_files = []
    js_files = []

    for key, value in manifest.items():
        if isinstance(value, dict):
            file_path = value.get('file', '')
            if file_path.endswith('.css'):
                css_files.append(f"/static/dist/{file_path}")
            elif file_path.endswith('.js'):
                js_files.append(f"/static/dist/{file_path}")

    # 更新 HTML
    # 替换 CSS 链接
    if css_files:
        css_links = '\n'.join([f'    <link rel="stylesheet" href="{css}">' for css in css_files])
        import re
        html_content = re.sub(
            r'    <link rel="stylesheet" href="/static/dist/assets/index\.css">',
            css_links,
            html_content
        )

    # 替换 JS 脚本
    if js_files:
        js_scripts = '\n'.join([f'    <script type="module" src="{js}"></script>' for js in js_files])
        import re
        html_content = re.sub(
            r'    <script type="module" src="/static/dist/assets/index\.js"></script>',
            js_scripts,
            html_content
        )

    # 写回 index.html
    with open(INDEX_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] Injected {len(css_files)} CSS files and {len(js_files)} JS files into index.html")


if __name__ == "__main__":
    try:
        inject_assets()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
