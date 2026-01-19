#!/usr/bin/env python3
"""
从 git commit 中自动提取 changelog，或从 CHANGELOG.md 中提取
"""
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def run_git_command(cmd: list, cwd=None) -> str:
    """执行 git 命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}", file=sys.stderr)
        return ""


def get_previous_version_tag(current_version: str, repo_path: Path) -> str:
    """获取当前版本之前的最近 tag"""
    # 尝试找到前一个版本 tag
    all_tags = run_git_command(
        ["git", "tag", "-l", "v*", "--sort=-version:refname"], cwd=repo_path
    )
    if not all_tags:
        return ""

    tags = all_tags.split("\n")
    for tag in tags:
        # 跳过当前版本和预发布版本
        clean_tag = tag.lstrip("v")
        if clean_tag != current_version and "-" not in clean_tag:
            return tag

    return ""


def generate_changelog_from_git(current_version: str, repo_path: Path, compact: bool = False) -> str:
    """从 git commit 自动生成 changelog

    Args:
        current_version: 当前版本号
        repo_path: 仓库路径
        compact: 如果 True，不包含版本标题（用于 Release 页面）
    """
    previous_tag = get_previous_version_tag(current_version, repo_path)

    if not previous_tag:
        # 如果没有找到前一个 tag，获取所有 commit
        commits = run_git_command(
            ["git", "log", "--oneline", "-20"],
            cwd=repo_path
        )
    else:
        # 获取从上一个版本到现在的 commit
        commits = run_git_command(
            ["git", "log", f"{previous_tag}..HEAD", "--oneline"],
            cwd=repo_path
        )

    if not commits:
        return ""

    # 按类型分组 commit
    categories = {
        "feat": [],
        "fix": [],
        "perf": [],
        "refactor": [],
        "docs": [],
        "chore": [],
        "other": []
    }

    for line in commits.split("\n"):
        if not line.strip():
            continue

        # 提取 commit hash 和 message
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue

        commit_hash = parts[0]
        message = parts[1].strip()

        # 提取 scope（如有）并清理 message
        scope = ""
        msg_clean = message

        # 处理 Conventional Commits 格式: feat(scope): message 或 feat: message
        match = re.match(r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$', message)
        if match:
            commit_type = match.group(1).lower()
            scope = match.group(2) or ""
            msg_clean = match.group(3).strip()
        else:
            commit_type = "other"

        # 构建带链接的 message
        msg_with_link = f"- {msg_clean} ([{commit_hash[:7]}](https://github.com/elfgzp/anime1-desktop/commit/{commit_hash}))"

        if commit_type in categories:
            categories[commit_type].append(msg_with_link)
        else:
            categories["other"].append(msg_with_link)

    # 生成 changelog
    changelog_lines = []

    # 如果不是简化模式，添加版本标题
    if not compact:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        changelog_lines.append(f"## [{current_version}] - {date}\n")

    # 按顺序添加各类型
    order = ["feat", "fix", "perf", "refactor", "docs", "chore", "other"]
    type_names = {
        "feat": "New Features",
        "fix": "Bug Fixes",
        "perf": "Performance",
        "refactor": "Refactoring",
        "docs": "Documentation",
        "chore": "Maintenance",
        "other": "Other Changes"
    }

    has_content = False
    for commit_type in order:
        if categories[commit_type]:
            has_content = True
            changelog_lines.append(f"### {type_names[commit_type]}")
            changelog_lines.extend(categories[commit_type])
            changelog_lines.append("")  # 空行

    if not has_content:
        return ""

    return "\n".join(changelog_lines)


def extract_changelog_from_file(version: str, changelog_file: Path = Path("CHANGELOG.md")) -> str:
    """从 CHANGELOG.md 文件中提取指定版本的更新内容"""
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

        return ""
    except Exception as e:
        print(f"Error reading changelog: {e}", file=sys.stderr)
        return ""


def extract_changelog(version: str, repo_path: Path = Path("."), compact: bool = False) -> str:
    """
    提取 changelog

    优先从 CHANGELOG.md 文件提取，如果没有则自动从 git commit 生成

    Args:
        version: 版本号
        repo_path: 仓库路径
        compact: 如果 True，不包含版本标题（用于 Release 页面）
    """
    # 首先尝试从文件提取
    changelog = extract_changelog_from_file(version)
    if changelog:
        return changelog

    # 如果文件没有，自动从 git 生成
    changelog = generate_changelog_from_git(version, repo_path, compact)
    if changelog:
        return changelog

    return ""


def main():
    """主函数"""
    version = "test"
    compact = False

    # 解析命令行参数
    for arg in sys.argv[1:]:
        if arg == "--compact":
            compact = True
        elif not arg.startswith("-"):
            version = arg

    repo_path = Path(__file__).parent.parent
    changelog = extract_changelog(version, repo_path, compact)

    if changelog:
        print(changelog)
    else:
        print(f"查看 [CHANGELOG.md](https://github.com/elfgzp/anime1-desktop/blob/main/CHANGELOG.md) 了解详细变更。")


if __name__ == "__main__":
    main()
