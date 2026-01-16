#!/usr/bin/env python3
"""
从 CHANGELOG.md 中提取指定版本的更新内容
"""
import re
import sys
from pathlib import Path


def extract_changelog(version: str, changelog_file: Path = Path("CHANGELOG.md")) -> str:
    """
    从 CHANGELOG.md 中提取指定版本的更新内容
    
    Args:
        version: 版本号（不含 v 前缀）
        changelog_file: CHANGELOG.md 文件路径
    
    Returns:
        提取的 changelog 内容，如果未找到则返回空字符串
    """
    if not changelog_file.exists():
        return ""
    
    try:
        with open(changelog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配版本标题，格式：## [版本号] - 日期
        pattern = rf'^## \[{re.escape(version)}\].*?\n(.*?)(?=^## \[|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        
        if match:
            changelog = match.group(1).strip()
            # 移除开头的空行
            changelog = re.sub(r'^\n+', '', changelog)
            return changelog
        
        # 如果没找到，尝试查找 [Unreleased] 部分
        pattern = r'^## \[Unreleased\].*?\n(.*?)(?=^## \[|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            changelog = match.group(1).strip()
            changelog = re.sub(r'^\n+', '', changelog)
            return changelog
        
        return ""
    except Exception as e:
        print(f"Error reading changelog: {e}", file=sys.stderr)
        return ""


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: extract_changelog.py <version>")
        print("Example: extract_changelog.py 1.0.0")
        sys.exit(1)
    
    version = sys.argv[1]
    changelog = extract_changelog(version)
    
    if changelog:
        print(changelog)
    else:
        # 返回默认消息（会在 workflow 中处理）
        print("")


if __name__ == "__main__":
    main()
