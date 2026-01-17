#!/usr/bin/env python3
"""
注入 Vite 构建后的资源路径到 Flask 模板。

Vite 构建后会生成 manifest.json，包含所有资源的映射关系。
此脚本读取 manifest 并更新 templates/index.html 中的资源路径。
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "static" / "dist" / "manifest.json"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "index.html"


def inject_assets():
    """读取 manifest 并更新模板中的资源路径。"""
    if not MANIFEST_PATH.exists():
        print(f"Warning: Manifest not found at {MANIFEST_PATH}")
        print("Skipping asset injection. Make sure to run 'npm run build' first.")
        return
    
    # 读取 manifest
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 查找主入口文件
    # Vite 的 manifest 中，index.html 是 key
    main_entry = None
    for key, value in manifest.items():
        if key.endswith('.html') or 'index' in key.lower():
            main_entry = value
            break
    
    if not main_entry:
        # 尝试查找第一个入口
        main_entry = list(manifest.values())[0] if manifest else None
    
    if not main_entry:
        print("Warning: Could not find main entry in manifest")
        return
    
    # 读取模板
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
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
    
    # 更新模板
    # 替换 CSS 链接
    if css_files:
        css_links = '\n'.join([f'    <link rel="stylesheet" href="{css}">' for css in css_files])
        # 查找并替换现有的 CSS 链接
        import re
        template_content = re.sub(
            r'    <link rel="stylesheet" href="/static/dist/assets/index\.css">',
            css_links,
            template_content
        )
    
    # 替换 JS 脚本
    if js_files:
        js_scripts = '\n'.join([f'    <script type="module" src="{js}"></script>' for js in js_files])
        # 查找并替换现有的 JS 脚本
        import re
        template_content = re.sub(
            r'    <script type="module" src="/static/dist/assets/index\.js"></script>',
            js_scripts,
            template_content
        )
    
    # 写回模板
    with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✓ Injected {len(css_files)} CSS files and {len(js_files)} JS files into template")


if __name__ == "__main__":
    try:
        inject_assets()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
