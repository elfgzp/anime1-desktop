"""
集成测试配置 - 这些测试需要在本地手动运行，不会在 CI 中执行

包含需要实际运行 Anime1.exe 的测试脚本：
- test_exit.py: 测试退出流程
- test_final.py: 完整更新流程测试
- test_update_flow.py: Windows 更新流程测试
- test_update_simple.py: 简单更新测试
- test_windows_update.py: Windows 更新测试
- quick_test.py: 快速测试脚本
- test_current_version.py: 当前版本更新测试
- test_restart.py: 重启状态检查
"""

import pytest
import os


def pytest_collection_modifyitems(items):
    """跳过集成测试目录下的测试（因为它们需要 Anime1.exe）"""
    integration_dir = os.path.dirname(os.path.abspath(__file__))
    for item in items:
        # 只跳过 tests/integration 目录下的测试
        if os.path.dirname(item.fspath) == integration_dir:
            item.add_marker(pytest.mark.skip(reason="需要运行 Anime1.exe，手动测试用"))
