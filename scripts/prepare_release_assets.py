#!/usr/bin/env python3
"""
准备 Release 资源脚本

从 artifacts 目录中收集所有构建产物并复制到 release-assets 目录
"""
import sys
import shutil
from pathlib import Path


def main():
    """主函数"""
    artifacts_dir = Path("artifacts")
    output_dir = Path("release-assets")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not artifacts_dir.exists():
        print(f"Error: artifacts directory not found: {artifacts_dir}")
        sys.exit(1)
    
    # 查找所有构建产物
    # Windows: zip (便携版) + exe (安装包)
    # macOS: dmg
    # Linux: tar.gz
    files_found = []
    for pattern in ["*.zip", "*.dmg", "*.tar.gz", "*.exe"]:
        for file in artifacts_dir.rglob(pattern):
            if file.is_file():
                dest = output_dir / file.name
                shutil.copy2(file, dest)
                files_found.append(dest)
    
    if not files_found:
        print("Error: No release assets found!")
        print(f"Artifacts structure:")
        for item in artifacts_dir.rglob("*"):
            if item.is_file():
                print(f"  {item}")
        sys.exit(1)
    
    print("Release assets prepared:")
    for file in sorted(files_found):
        size_mb = file.stat().st_size / 1024 / 1024
        print(f"  {file.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    import sys
    main()
