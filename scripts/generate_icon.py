#!/usr/bin/env python3
"""
生成多尺寸 ICO 文件（用于 Windows）
"""
from PIL import Image
import sys
from pathlib import Path

def generate_ico():
    # 路径
    source_png = Path(__file__).parent.parent / 'resources' / 'icon.png'
    target_ico = Path(__file__).parent.parent / 'resources' / 'icon.ico'
    
    print(f'Generating icon.ico from {source_png}...')
    
    # 打开源图片
    img = Image.open(source_png)
    
    # 转换为 RGBA 模式（如果需要）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 生成多尺寸图标
    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    
    # 保存为 ICO
    img.save(target_ico, format='ICO', sizes=[(s, s) for s in sizes])
    
    print(f'✅ Icon generated successfully: {target_ico}')
    print(f'   Included sizes: {sizes}')

if __name__ == '__main__':
    try:
        generate_ico()
    except Exception as e:
        print(f'❌ Failed to generate icon: {e}')
        sys.exit(1)
