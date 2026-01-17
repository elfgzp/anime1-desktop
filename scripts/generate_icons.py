#!/usr/bin/env python3
"""
Generate Windows ICO icon from PNG.

Usage:
    python scripts/generate_icons.py
"""
from PIL import Image
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PNG_PATH = PROJECT_ROOT / "static" / "favicon.png"
ICO_PATH = PROJECT_ROOT / "static" / "app.ico"


def generate_ico():
    """Generate Windows ICO icon from PNG."""
    if not PNG_PATH.exists():
        print(f"[ERROR] Source PNG not found: {PNG_PATH}")
        return False

    try:
        img = Image.open(PNG_PATH)

        # ICO sizes (Windows standard)
        sizes = [16, 32, 48, 64, 128, 256]

        # Create resized images
        img_list = []
        for size in sizes:
            if size <= img.size[0] or size <= img.size[1]:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                img_list.append(resized)
            else:
                # For sizes larger than original, use the largest available
                pass

        # Also include the original size if it's not too large
        max_size = 256
        if img.size[0] <= max_size and img.size[1] <= max_size:
            img_list.append(img)

        # Remove duplicates (same size)
        seen = set()
        unique_list = []
        for im in img_list:
            size = im.size
            if size not in seen:
                seen.add(size)
                unique_list.append(im)

        # Save as ICO
        ICO_PATH.parent.mkdir(parents=True, exist_ok=True)
        img.save(ICO_PATH, format='ICO', sizes=[im.size for im in unique_list], append_images=[])

        print(f"[OK] Generated Windows ICO: {ICO_PATH}")
        print(f"     Sizes: {[im.size for im in unique_list]}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to generate ICO: {e}")
        return False


if __name__ == "__main__":
    generate_ico()
