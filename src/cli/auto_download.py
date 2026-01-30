"""CLI commands for auto download functionality.

This module provides command-line interface for managing auto downloads:
- Start/stop auto download service
- Configure download settings
- Trigger manual downloads
- View download status and history
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.auto_download_service import (
    get_auto_download_service,
    DownloadConfig,
    DownloadFilter,
    DownloadStatus,
)
from src.services.video_downloader import get_video_downloader
from src.services.anime_cache_service import get_anime_list_cache
from src.utils.app_dir import ensure_app_data_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_status(args):
    """Show auto download status."""
    service = get_auto_download_service()
    status = service.get_status()

    print("\n" + "=" * 50)
    print("自动下载状态")
    print("=" * 50)
    print(f"启用状态: {'已启用' if status['enabled'] else '已禁用'}")
    print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
    print(f"下载路径: {status['download_path']}")
    print(f"检查间隔: {status['check_interval_hours']} 小时")
    print("\n筛选条件:")
    filters = status['filters']
    if filters.get('min_year'):
        print(f"  最小年份: {filters['min_year']}")
    if filters.get('max_year'):
        print(f"  最大年份: {filters['max_year']}")
    if filters.get('specific_years'):
        print(f"  指定年份: {', '.join(map(str, filters['specific_years']))}")
    if filters.get('seasons'):
        print(f"  指定季度: {', '.join(filters['seasons'])}")
    if filters.get('min_episodes'):
        print(f"  最少集数: {filters['min_episodes']}")
    if filters.get('include_patterns'):
        print(f"  包含模式: {', '.join(filters['include_patterns'])}")
    if filters.get('exclude_patterns'):
        print(f"  排除模式: {', '.join(filters['exclude_patterns'])}")

    print("\n下载统计:")
    counts = status['status_counts']
    print(f"  待下载: {counts['pending']}")
    print(f"  下载中: {counts['downloading']}")
    print(f"  已完成: {counts['completed']}")
    print(f"  失败: {counts['failed']}")
    print(f"  已跳过: {counts['skipped']}")

    if status['recent_downloads']:
        print("\n最近下载:")
        for record in status['recent_downloads'][:5]:
            print(f"  [{record['status']}] {record['anime_title']} - EP{record['episode_num']}")
    print("=" * 50)


def cmd_enable(args):
    """Enable auto download."""
    service = get_auto_download_service()
    config = service.get_config()
    config.enabled = True

    if service.update_config(config):
        service.start_scheduler()
        print("✓ 自动下载已启用")
        print(f"  下载路径: {service.get_download_path()}")
        print(f"  检查间隔: {config.check_interval_hours} 小时")
    else:
        print("✗ 启用失败")
        return 1
    return 0


def cmd_disable(args):
    """Disable auto download."""
    service = get_auto_download_service()
    config = service.get_config()
    config.enabled = False

    if service.update_config(config):
        service.stop_scheduler()
        print("✓ 自动下载已禁用")
    else:
        print("✗ 禁用失败")
        return 1
    return 0


def cmd_config(args):
    """Configure auto download settings."""
    service = get_auto_download_service()
    config = service.get_config()

    # Update download path
    if args.download_path:
        path = Path(args.download_path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        config.download_path = str(path)
        print(f"✓ 下载路径已设置为: {path}")

    # Update check interval
    if args.interval:
        config.check_interval_hours = args.interval
        print(f"✓ 检查间隔已设置为: {args.interval} 小时")

    # Update year filter
    if args.min_year is not None:
        config.filters.min_year = args.min_year
        print(f"✓ 最小年份已设置为: {args.min_year}")

    if args.max_year is not None:
        config.filters.max_year = args.max_year
        print(f"✓ 最大年份已设置为: {args.max_year}")

    if args.years:
        config.filters.specific_years = args.years
        print(f"✓ 指定年份已设置为: {args.years}")

    # Update season filter
    if args.seasons:
        valid_seasons = ["冬季", "春季", "夏季", "秋季"]
        seasons = [s for s in args.seasons if s in valid_seasons]
        config.filters.seasons = seasons
        print(f"✓ 指定季度已设置为: {seasons}")

    # Update episode filter
    if args.min_episodes is not None:
        config.filters.min_episodes = args.min_episodes
        print(f"✓ 最少集数已设置为: {args.min_episodes}")

    # Save config
    if service.update_config(config):
        print("✓ 配置已保存")
    else:
        print("✗ 保存失败")
        return 1
    return 0


def cmd_preview(args):
    """Preview which anime would match current filters."""
    service = get_auto_download_service()
    all_anime = get_anime_list_cache()
    all_anime_dicts = [a.to_dict() for a in all_anime]

    filtered = service.filter_anime(all_anime_dicts)

    print("\n" + "=" * 50)
    print(f"筛选预览 (共 {len(filtered)}/{len(all_anime_dicts)} 部番剧匹配)")
    print("=" * 50)

    config = service.get_config()
    filters = config.filters

    print("\n当前筛选条件:")
    if filters.min_year:
        print(f"  最小年份: {filters.min_year}")
    if filters.max_year:
        print(f"  最大年份: {filters.max_year}")
    if filters.specific_years:
        print(f"  指定年份: {filters.specific_years}")
    if filters.seasons:
        print(f"  指定季度: {filters.seasons}")
    if filters.min_episodes:
        print(f"  最少集数: {filters.min_episodes}")

    print("\n匹配的番剧:")
    for i, anime in enumerate(filtered[:20], 1):
        year = anime.get('year', 'N/A')
        season = anime.get('season', 'N/A')
        episode = anime.get('episode', 0)
        print(f"  {i}. {anime['title']}")
        print(f"     年份: {year}, 季度: {season}, 集数: {episode}")

    if len(filtered) > 20:
        print(f"\n  ... 还有 {len(filtered) - 20} 部番剧")

    print("=" * 50)


def cmd_download(args):
    """Download a specific episode."""
    from src.parser.anime1_parser import Anime1Parser

    service = get_auto_download_service()
    download_path = service.get_download_path()

    print(f"下载路径: {download_path}")

    # Get episode info
    episode_url = args.url
    if not episode_url.startswith("http"):
        episode_url = f"https://anime1.me/{episode_url}"

    print(f"解析视频信息: {episode_url}")

    # Create downloader
    downloader = get_video_downloader(download_path, max_concurrent=1)

    # Get anime info
    parser = Anime1Parser()
    try:
        # Try to get anime title from episode page
        html = downloader._http.get(episode_url)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title_elem = soup.find("h2", class_="entry-title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Extract episode number
            import re
            ep_match = re.search(r'\[(\d+(?:\.\d+)?)\]', title_text)
            if ep_match:
                episode_num = ep_match.group(1)
                anime_title = re.sub(r'\s*\[\d+(?:\.\d+)?\]\s*$', '', title_text).strip()
            else:
                episode_num = "1"
                anime_title = title_text
        else:
            anime_title = "Unknown"
            episode_num = "1"
    except Exception as e:
        logger.warning(f"Could not parse anime info: {e}")
        anime_title = "Unknown"
        episode_num = "1"
    finally:
        parser.close()

    # Extract episode ID from URL
    episode_id = episode_url.split("/")[-1].split("?")[0]

    print(f"番剧: {anime_title}")
    print(f"集数: {episode_num}")
    print("开始下载...")

    # Download
    def on_progress(progress):
        if progress.total_bytes > 0:
            percent = progress.percent
            downloaded_mb = progress.downloaded_bytes / (1024 * 1024)
            total_mb = progress.total_bytes / (1024 * 1024)
            speed_mbps = progress.speed_bytes_per_sec / (1024 * 1024)
            print(f"\r进度: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB) "
                  f"速度: {speed_mbps:.2f} MB/s", end="", flush=True)

    progress = downloader.download(
        episode_id=episode_id,
        episode_url=episode_url,
        anime_title=anime_title,
        episode_num=episode_num,
        progress_callback=on_progress,
    )

    print()  # New line after progress

    if progress.status == "completed":
        print(f"✓ 下载完成: {progress.file_path}")
        return 0
    else:
        print(f"✗ 下载失败: {progress.error_message}")
        return 1


def cmd_history(args):
    """Show download history."""
    service = get_auto_download_service()

    status_filter = None
    if args.status:
        try:
            status_filter = DownloadStatus(args.status)
        except ValueError:
            print(f"无效的状态: {args.status}")
            print("有效状态: pending, downloading, completed, failed, skipped")
            return 1

    history = service.get_history(limit=args.limit, status=status_filter)

    print("\n" + "=" * 80)
    print("下载历史")
    print("=" * 80)

    if not history:
        print("暂无下载记录")
    else:
        print(f"{'时间':<20} {'状态':<10} {'番剧':<30} {'集数':<10}")
        print("-" * 80)
        for record in history:
            time_str = record.created_at[:19] if len(record.created_at) > 19 else record.created_at
            status_str = record.status.value
            title = record.anime_title[:28] if len(record.anime_title) > 28 else record.anime_title
            print(f"{time_str:<20} {status_str:<10} {title:<30} {record.episode_num:<10}")

    print("=" * 80)
    return 0


def cmd_run_once(args):
    """Run auto download check once."""
    service = get_auto_download_service()

    print("开始检查下载...")
    print("获取番剧列表...")

    all_anime = get_anime_list_cache()
    all_anime_dicts = [a.to_dict() for a in all_anime]

    print(f"共有 {len(all_anime_dicts)} 部番剧")

    filtered = service.filter_anime(all_anime_dicts)
    print(f"筛选后: {len(filtered)} 部番剧")

    if args.dry_run:
        print("\n模拟运行模式，不实际下载:")
        for anime in filtered[:10]:
            print(f"  - {anime['title']} ({anime.get('year', 'N/A')})")
        if len(filtered) > 10:
            print(f"  ... 还有 {len(filtered) - 10} 部")
    else:
        print("\n开始下载检查...")
        # This would trigger actual downloads
        # For now, just show what would be downloaded
        for anime in filtered[:5]:
            print(f"  检查: {anime['title']}")

    print("\n检查完成")
    return 0


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Anime1 自动下载管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看状态
  python -m src.cli.auto_download status

  # 启用自动下载
  python -m src.cli.auto_download enable

  # 配置下载路径和年份筛选
  python -m src.cli.auto_download config --path ~/Downloads/Anime --min-year 2024

  # 预览匹配的番剧
  python -m src.cli.auto_download preview

  # 下载单集
  python -m src.cli.auto_download download https://anime1.me/12345

  # 查看下载历史
  python -m src.cli.auto_download history --limit 20
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # status command
    status_parser = subparsers.add_parser("status", help="显示自动下载状态")
    status_parser.set_defaults(func=cmd_status)

    # enable command
    enable_parser = subparsers.add_parser("enable", help="启用自动下载")
    enable_parser.set_defaults(func=cmd_enable)

    # disable command
    disable_parser = subparsers.add_parser("disable", help="禁用自动下载")
    disable_parser.set_defaults(func=cmd_disable)

    # config command
    config_parser = subparsers.add_parser("config", help="配置自动下载设置")
    config_parser.add_argument("--path", "--download-path", dest="download_path",
                               help="下载路径")
    config_parser.add_argument("--interval", type=int,
                               help="检查间隔（小时）")
    config_parser.add_argument("--min-year", type=int,
                               help="最小年份")
    config_parser.add_argument("--max-year", type=int,
                               help="最大年份")
    config_parser.add_argument("--years", nargs="+", type=int,
                               help="指定年份列表（如 2023 2024）")
    config_parser.add_argument("--seasons", nargs="+",
                               choices=["冬季", "春季", "夏季", "秋季"],
                               help="指定季度")
    config_parser.add_argument("--min-episodes", type=int,
                               help="最少集数")
    config_parser.set_defaults(func=cmd_config)

    # preview command
    preview_parser = subparsers.add_parser("preview", help="预览匹配的番剧")
    preview_parser.set_defaults(func=cmd_preview)

    # download command
    download_parser = subparsers.add_parser("download", help="下载单集")
    download_parser.add_argument("url", help="剧集URL或ID")
    download_parser.set_defaults(func=cmd_download)

    # history command
    history_parser = subparsers.add_parser("history", help="查看下载历史")
    history_parser.add_argument("--limit", type=int, default=50,
                                help="显示记录数量")
    history_parser.add_argument("--status",
                                choices=["pending", "downloading", "completed", "failed", "skipped"],
                                help="按状态筛选")
    history_parser.set_defaults(func=cmd_history)

    # run-once command
    run_parser = subparsers.add_parser("run", help="运行一次下载检查")
    run_parser.add_argument("--dry-run", action="store_true",
                            help="模拟运行，不实际下载")
    run_parser.set_defaults(func=cmd_run_once)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
