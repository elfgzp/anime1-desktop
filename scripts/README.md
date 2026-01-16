# Scripts 目录说明

本目录包含 GitHub Actions workflow 使用的所有脚本。

## 脚本列表

### 构建相关

- **`build.sh`** - 根据平台构建应用
  - 参数: 平台名称 (Windows/macOS/Linux)
  - 功能: 根据平台调用 `build.py` 并传递正确的参数

### 打包相关

- **`prepare_artifacts.py`** - 准备构建产物
  - 功能: 根据平台和架构将构建产物打包为相应格式
  - Windows: zip
  - macOS: dmg
  - Linux: tar.gz

- **`create_dmg.py`** - 创建 macOS DMG 文件
  - 功能: 使用 create-dmg 工具创建 DMG 安装包

- **`prepare_release_assets.py`** - 准备 Release 资源
  - 功能: 从 artifacts 目录收集所有构建产物

### 版本和变更日志

- **`extract_version.sh`** - 提取版本号和 tag 名称
  - 参数: event_name, input_version, github_ref
  - 输出: tag_name, version

- **`extract_changelog.sh`** - 提取 CHANGELOG 内容
  - 参数: version, repository
  - 功能: 从 CHANGELOG.md 提取对应版本的更新内容

- **`extract_changelog.py`** - Python 版本的 CHANGELOG 提取器
  - 功能: 从 CHANGELOG.md 中提取指定版本的更新内容

### 测试相关

- **`test-workflow.sh`** - Workflow 测试脚本
  - 功能: 
    - 检查依赖和 Git 状态
    - 触发 workflow 测试
    - 持续监测运行状态
    - 验证所有平台的构建结果

## 使用方式

### 本地测试脚本

```bash
# 测试构建脚本
bash scripts/build.sh macOS

# 测试版本提取
bash scripts/extract_version.sh workflow_dispatch 1.0.0-test refs/heads/main
```

### 在 GitHub Actions 中使用

所有脚本都会在 workflow 中自动调用，无需手动执行。

## 注意事项

- 所有 bash 脚本都已设置执行权限
- Python 脚本需要 Python 3.8+
- macOS DMG 创建需要 `create-dmg` 工具（workflow 中会自动安装）
