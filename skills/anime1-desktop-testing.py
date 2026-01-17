#!/usr/bin/env python3
"""
Anime1 Desktop 测试技能 - Claude Code Skill

用于自动化测试 Anime1 Desktop 应用的所有功能

## 启动应用
```bash
make dev-server
```
访问: http://localhost:5173

## 功能测试
1. 首页: 搜索、分页、收藏、进入详情
2. 详情页: 返回、播放剧集、收藏
3. 收藏页: 查看列表、移除收藏
4. 设置页: 主题切换、检查更新、关于信息
5. 导航: 侧边栏导航、折叠

## 使用方法
在 Claude Code 中直接描述测试需求即可，例如:
- "测试搜索功能"
- "测试进入详情页并播放"
- "测试主题切换"
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import time


class TestType(Enum):
    HOME = "home"
    DETAIL = "detail"
    FAVORITES = "favorites"
    SETTINGS = "settings"
    NAVIGATION = "navigation"
    ALL = "all"


class Action(Enum):
    START_SERVER = "start_server"
    TAKE_SNAPSHOT = "take_snapshot"
    CLICK = "click"
    INPUT = "input"
    NAVIGATE = "navigate"
    VERIFY = "verify"
    SCROLL = "scroll"
    HOVER = "hover"


@dataclass
class TestCase:
    name: str
    steps: List[Dict[str, Any]]
    expected_result: str
    selectors: Dict[str, str]


# 测试用例定义
TEST_CASES = {
    "home_page": [
        TestCase(
            name="测试搜索功能",
            steps=[
                {"action": "input", "target": "search_input", "value": "进击的巨人"},
                {"action": "click", "target": "search_button"},
                {"action": "wait", "duration": 2},
                {"action": "verify", "target": "anime_grid", "condition": "visible"}
            ],
            expected_result="搜索结果显示番剧列表",
            selectors={
                "search_input": ".search-input input",
                "search_button": ".search-input + button",
                "anime_grid": ".anime-grid",
                "anime_card": ".anime-card"
            }
        ),
        TestCase(
            name="测试分页功能",
            steps=[
                {"action": "click", "target": "page_2"},
                {"action": "wait", "duration": 2},
                {"action": "verify", "target": "pagination", "condition": "visible"}
            ],
            expected_result="切换到第2页",
            selectors={
                "pagination": ".el-pagination",
                "page_2": ".el-pager li:nth-child(2)"
            }
        ),
        TestCase(
            name="测试收藏功能",
            steps=[
                {"action": "hover", "target": "anime_card_1"},
                {"action": "click", "target": "favorite_btn_1"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "favorite_btn_1", "condition": "has_class", "class": "active"}
            ],
            expected_result="收藏按钮变为激活状态",
            selectors={
                "anime_card_1": ".anime-card:nth-child(1)",
                "favorite_btn_1": ".anime-card:nth-child(1) .favorite-btn"
            }
        ),
        TestCase(
            name="测试进入详情页",
            steps=[
                {"action": "click", "target": "card_link_1"},
                {"action": "wait", "duration": 2},
                {"action": "verify", "target": "detail_page", "condition": "visible"}
            ],
            expected_result="进入番剧详情页",
            selectors={
                "card_link_1": ".anime-card:nth-child(1) .card-link",
                "detail_page": ".detail-container"
            }
        )
    ],
    "detail_page": [
        TestCase(
            name="测试返回首页",
            steps=[
                {"action": "click", "target": "back_button"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "home_page", "condition": "visible"}
            ],
            expected_result="返回到首页",
            selectors={
                "back_button": ".back-btn",
                "home_page": ".home-container"
            }
        ),
        TestCase(
            name="测试剧集播放",
            steps=[
                {"action": "click", "target": "episode_2"},
                {"action": "wait", "duration": 3},
                {"action": "verify", "target": "video_player", "condition": "visible"}
            ],
            expected_result="视频播放器显示并加载",
            selectors={
                "episode_2": ".episode-item:nth-child(2)",
                "episode_card_2": ".episode-card:nth-child(2)",
                "video_player": "video",
                "video_container": ".video-container"
            }
        ),
        TestCase(
            name="测试详情页收藏",
            steps=[
                {"action": "click", "target": "detail_favorite_btn"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "detail_favorite_btn", "condition": "has_class", "class": "active"}
            ],
            expected_result="收藏按钮变为激活状态",
            selectors={
                "detail_favorite_btn": ".detail-favorite-btn"
            }
        )
    ],
    "favorites_page": [
        TestCase(
            name="测试收藏列表展示",
            steps=[
                {"action": "navigate", "target": "/favorites"},
                {"action": "wait", "duration": 2},
                {"action": "verify", "target": "favorites_grid", "condition": "visible"}
            ],
            expected_result="显示收藏番剧网格",
            selectors={
                "favorites_grid": ".anime-grid",
                "favorites_page": ".favorites-container"
            }
        ),
        TestCase(
            name="测试移除收藏",
            steps=[
                {"action": "click", "target": "remove_btn_1"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "toast", "condition": "text_contains", "text": "已取消"}
            ],
            expected_result="显示取消收藏提示",
            selectors={
                "remove_btn_1": ".anime-card:nth-child(1) .favorite-btn",
                "toast": ".el-message"
            }
        )
    ],
    "settings_page": [
        TestCase(
            name="测试主题切换",
            steps=[
                {"action": "navigate", "target": "/settings"},
                {"action": "wait", "duration": 1},
                {"action": "click", "target": "theme_select"},
                {"action": "click", "target": "theme_dark"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "body", "condition": "has_class", "class": "dark"}
            ],
            expected_result="切换到暗色主题",
            selectors={
                "theme_select": ".theme-select",
                "theme_dark": ".el-select-dropdown__item:has-text('暗黑模式')",
                "body": "body"
            }
        ),
        TestCase(
            name="测试检查更新",
            steps=[
                {"action": "click", "target": "check_update_btn"},
                {"action": "wait", "duration": 3},
                {"action": "verify", "target": "toast", "condition": "visible"}
            ],
            expected_result="显示版本检查结果",
            selectors={
                "check_update_btn": "button:has-text('检查更新')",
                "toast": ".el-message"
            }
        ),
        TestCase(
            name="测试关于信息展示",
            steps=[
                {"action": "verify", "target": "about_info", "condition": "visible"},
                {"action": "verify", "target": "version_info", "condition": "text_contains", "text": "版本"}
            ],
            expected_result="显示版本和仓库信息",
            selectors={
                "about_info": ".about-info",
                "version_info": ".about-info p:first-child"
            }
        )
    ],
    "navigation": [
        TestCase(
            name="测试侧边栏导航到收藏页",
            steps=[
                {"action": "click", "target": "favorites_menu"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "favorites_url", "condition": "url_contains", "text": "/favorites"}
            ],
            expected_result="URL 变为 /favorites",
            selectors={
                "favorites_menu": ".el-menu-item:has-text('我的追番')",
                "favorites_url": "window.location.pathname"
            }
        ),
        TestCase(
            name="测试侧边栏导航到设置页",
            steps=[
                {"action": "click", "target": "settings_menu"},
                {"action": "wait", "duration": 1},
                {"action": "verify", "target": "settings_url", "condition": "url_contains", "text": "/settings"}
            ],
            expected_result="URL 变为 /settings",
            selectors={
                "settings_menu": ".el-menu-item:has-text('设置')",
                "settings_url": "window.location.pathname"
            }
        ),
        TestCase(
            name="测试侧边栏折叠",
            steps=[
                {"action": "click", "target": "collapse_btn"},
                {"action": "wait", "duration": 0.5},
                {"action": "verify", "target": "sidebar", "condition": "has_class", "class": "sidebar-collapsed"}
            ],
            expected_result="侧边栏收起",
            selectors={
                "collapse_btn": ".collapse-btn",
                "sidebar": ".sidebar"
            }
        )
    ]
}


def get_test_cases(test_type: str) -> List[TestCase]:
    """获取指定类型的测试用例"""
    if test_type == "all":
        all_cases = []
        for cases in TEST_CASES.values():
            all_cases.extend(cases)
        return all_cases
    return TEST_CASES.get(test_type, [])


def generate_test_script(test_type: str) -> str:
    """生成可执行的测试脚本"""
    cases = get_test_cases(test_type)

    script = f'''#!/usr/bin/env python3
"""
Anime1 Desktop {test_type.upper()} 测试脚本
自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import subprocess
import time
import sys

def run_test(test_name, action, target, value=None):
    """执行测试操作"""
    print(f"执行: {test_name} - {action} - {target}")
    # 这里可以集成 chrome-devtools MCP 工具
    pass

'''

    for case in cases:
        script += f'''
def test_{case.name.replace(' ', '_').replace('(', '').replace(')', '')}():
    """{case.name}"""
    print("\\n=== {case.name} ===")
'''
        for step in case.steps:
            action = step.get('action', '')
            target = step.get('target', '')
            value = step.get('value', '')
            condition = step.get('condition', '')
            duration = step.get('duration', 0)

            if action == 'input':
                script += f'    run_test("{case.name}", "input", "{target}", "{value}")\n'
            elif action == 'click':
                script += f'    run_test("{case.name}", "click", "{target}")\n'
            elif action == 'wait':
                script += f'    time.sleep({duration})\n'
            elif action == 'verify':
                script += f'    run_test("{case.name}", "verify", "{target}", "{condition}")\n'
            elif action == 'navigate':
                script += f'    run_test("{case.name}", "navigate", "{target}", "{value}")\n'

        script += f'    print("预期结果: {case.expected_result}")\n'

    script += '''

if __name__ == "__main__":
    print("Anime1 Desktop 测试")
    print("请确保已启动开发服务器: make dev-server")
    print("访问地址: http://localhost:5173")
'''

    return script


def get_skill_description() -> Dict[str, Any]:
    """获取技能描述"""
    return {
        "name": "anime1-desktop-testing",
        "description": "Anime1 Desktop 应用自动化测试技能",
        "version": "1.0.0",
        "author": "Claude Code",
        "instructions": [
            "启动开发服务器: make dev-server",
            "访问地址: http://localhost:5173",
            "测试前先确认页面加载完成",
            "测试完成后验证功能是否符合预期"
        ],
        "test_types": {
            "home": "首页功能测试(搜索、分页、收藏、进入详情)",
            "detail": "详情页功能测试(返回、播放、收藏)",
            "favorites": "收藏页功能测试(列表展示、移除收藏)",
            "settings": "设置页功能测试(主题、更新、关于)",
            "navigation": "导航功能测试(侧边栏菜单、折叠)",
            "all": "全部测试"
        },
        "common_targets": {
            "search_input": "搜索框输入框",
            "search_button": "搜索按钮",
            "pagination": "分页器",
            "anime_card": "番剧卡片",
            "favorite_btn": "收藏按钮",
            "back_button": "返回按钮",
            "episode_item": "剧集列表项",
            "episode_card": "剧集卡片",
            "video_player": "视频播放器",
            "sidebar": "侧边栏",
            "favorites_menu": "我的追番菜单",
            "settings_menu": "设置菜单",
            "theme_select": "主题选择器",
            "check_update_btn": "检查更新按钮"
        }
    }


def main():
    """主函数"""
    print("=" * 60)
    print("Anime1 Desktop 测试技能")
    print("=" * 60)

    desc = get_skill_description()
    print(f"\\n名称: {desc['name']}")
    print(f"描述: {desc['description']}")
    print(f"版本: {desc['version']}")

    print("\\n使用说明:")
    for instruction in desc['instructions']:
        print(f"  - {instruction}")

    print("\\n测试类型:")
    for test_type, description in desc['test_types'].items():
        print(f"  - {test_type}: {description}")

    print("\\n常用操作目标:")
    for target, description in desc['common_targets'].items():
        print(f"  - {target}: {description}")

    print("\\n" + "=" * 60)
    print("使用前请确保已启动开发服务器!")
    print("命令: make dev-server")
    print("=" * 60)


if __name__ == "__main__":
    main()
