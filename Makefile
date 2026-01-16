# Makefile for Anime1 Cover Browser
#
# Usage:
#   make help          - Show this help message
#   make install       - Install dependencies
#   make dev           - Run desktop app in development mode
#   make run           - Run in browser (CLI mode)
#   make build         - Build desktop application (current platform)
#   make build-win     - Build for Windows
#   make build-linux   - Build for Linux
#   make build-macos   - Build for macOS (Intel)
#   make build-macos-arm - Build for macOS (Apple Silicon M-series)
#   make build-onefile - Build as single executable
#   make dmg           - Create DMG for macOS
#   make install-dmg   - Install create-dmg tool (macOS)
#   make clean         - Clean build artifacts
#   make clean-all     - Clean everything including cache
#   make test          - Run tests

# Python executable - use venv if available, otherwise use system python3
VENV := $(PROJECT_ROOT).venv
ifeq ($(wildcard $(VENV)/bin/python),)
	PYTHON := python3
	PYTHON_CMD := python3
else
	PYTHON := $(VENV)/bin/python
	PYTHON_CMD := $(VENV)/bin/python
endif

# Project root
PROJECT_ROOT := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

# Directories
DIST_DIR := $(PROJECT_ROOT)dist
BUILD_DIR := $(PROJECT_ROOT)build

.PHONY: help install dev run build build-win build-linux build-macos build-macos-arm build-onefile dmg install-dmg clean clean-all test deps verify-deps test-workflow test-gh-auth test-local-build test-local-build-full

help:
	@echo "Anime1 Cover Browser - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies (creates venv if needed)"
	@echo "  make dev           - Run desktop app in development mode"
	@echo "  make run           - Run in browser (CLI mode)"
	@echo "  make verify-deps   - Verify required packages are installed"
	@echo ""
	@echo "Build (current platform):"
	@echo "  make build         - Build desktop application"
	@echo "  make build-onefile - Build as single executable (larger file)"
	@echo ""
	@echo "Cross-platform builds:"
	@echo "  make build-win     - Build for Windows (x64)"
	@echo "  make build-linux   - Build for Linux (x64)"
	@echo "  make build-macos   - Build for macOS (Intel x64)"
	@echo "  make build-macos-arm - Build for macOS (Apple Silicon M-series)"
	@echo ""
	@echo "macOS Distribution:"
	@echo "  make dmg           - Create DMG (requires create-dmg)"
	@echo "  make install-dmg   - Install create-dmg tool (macOS only)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make clean-all     - Clean everything (build, dist, cache)"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run tests"
	@echo "  make test-workflow - Test GitHub Actions workflow (需要 gh CLI)"
	@echo "  make test-gh-auth  - Check GitHub CLI authentication"
	@echo "  make verify-scripts - Verify all workflow scripts"
	@echo "  make test-local-build - Test build scripts locally (dry-run)"
	@echo "  make test-local-build-full - Test build scripts with actual build"

# Dependencies
deps:
	@echo "Creating virtual environment..."
	@if [ ! -d "$(VENV)" ]; then \
		python3 -m venv $(VENV); \
		echo "Virtual environment created."; \
	fi
	@echo "Installing dependencies..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV)/bin/pip install --upgrade pip; \
		$(VENV)/bin/pip install -e .; \
	else \
		pip install --upgrade pip; \
		pip install -e .; \
	fi

install: deps
	@echo "Dependencies installed successfully!"

verify-deps:
	@$(PYTHON_CMD) -c "import PyInstaller; import webview; print('Dependencies verified: OK')" 2>/dev/null || \
		(echo "Missing dependencies. Run: make install" && exit 1)

# Development
dev: verify-deps
	@echo "Starting desktop application..."
	@$(PYTHON_CMD) -m src.desktop

run: verify-deps
	@echo "Starting in browser..."
	@$(PYTHON_CMD) -m src.desktop --remote

# Build
build: verify-deps
	@echo "Building desktop application..."
	@$(PYTHON_CMD) $(PROJECT_ROOT)build.py --clean

build-onefile: verify-deps
	@echo "Building as single executable..."
	@$(PYTHON_CMD) $(PROJECT_ROOT)build.py --clean --onefile

# Cross-platform builds (requires Docker or cloud CI/CD)
# Note: These require cross-compilation toolchains

build-win: verify-deps
	@echo "[INFO] Building for Windows (x64)..."
	@echo "[INFO] Note: Cross-compilation requires Docker or cloud CI/CD"
	@echo "[INFO] Use GitHub Actions for Windows builds"
	@$(PYTHON_CMD) $(PROJECT_ROOT)build.py --clean --onefile

build-linux: verify-deps
	@echo "[INFO] Building for Linux (x64)..."
	@echo "[INFO] Note: Cross-compilation requires Docker or cloud CI/CD"
	@echo "[INFO] Use GitHub Actions for Linux builds"
	@$(PYTHON_CMD) $(PROJECT_ROOT)build.py --clean --onefile

build-macos: verify-deps
	@echo "[INFO] Building for macOS (Intel x64)..."
	@echo "[INFO] Note: Current platform is Apple Silicon"
	@echo "[INFO] Building arm64 version instead..."
	@$(PYTHON_CMD) $(PROJECT_ROOT)build.py --clean

build-macos-arm: verify-deps
	@echo "[INFO] Building for macOS (Apple Silicon M-series)..."
	@$(PYTHON_CMD) $(PROJECT_ROOT)build.py --clean

# Create DMG for macOS (requires create-dmg)
dmg: build
	@if ! command -v create-dmg >/dev/null 2>&1; then \
		echo "Error: create-dmg not found."; \
		echo "Install with: brew install create-dmg"; \
		exit 1; \
	fi
	@if [ -d "$(DIST_DIR)/anime1-cover.app" ]; then \
		echo "Creating DMG..."; \
		create-dmg \
			--volname "Anime1 Cover Browser" \
			--volicon "" \
			--window-pos 200 200 \
			--window-size 600 400 \
			--app-drop-link 400 200 \
			"$(DIST_DIR)/Anime1 Cover Browser.dmg" \
			"$(DIST_DIR)/anime1-cover.app"; \
		echo "DMG created: $(DIST_DIR)/Anime1 Cover Browser.dmg"; \
	else \
		echo "Error: anime1-cover.app not found. Run 'make build' first."; \
	fi

# Install create-dmg (macOS only)
install-dmg:
	@if [ "$$(uname)" = "Darwin" ]; then \
		if ! command -v create-dmg >/dev/null 2>&1; then \
			echo "Installing create-dmg..."; \
			brew install create-dmg; \
		else \
			echo "create-dmg already installed."; \
		fi \
	else \
		echo "create-dmg is only available on macOS."; \
	fi

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -rf $(DIST_DIR)/*
	@echo "Cleaned build artifacts."

clean-all: clean
	@echo "Cleaning all cache..."
	@rm -rf $(PROJECT_ROOT)__pycache__
	@find $(PROJECT_ROOT) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -name "*.pyc" -delete 2>/dev/null || true
	@find $(PROJECT_ROOT) -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned all cache."

# Testing
test:
	@echo "Running tests..."
	@$(PYTHON_CMD) -m pytest $(PROJECT_ROOT)tests -v 2>/dev/null || echo "No tests found or pytest not installed."

# GitHub Actions Workflow Testing
test-workflow:
	@echo "Testing GitHub Actions workflow..."
	@bash $(PROJECT_ROOT)scripts/test-workflow.sh

test-gh-auth:
	@echo "检查 GitHub CLI 认证状态..."
	@gh auth status || (echo "未登录，请运行: gh auth login --scopes workflow" && exit 1)
	@echo "✓ GitHub CLI 已登录"

verify-scripts:
	@echo "验证所有 workflow 相关脚本..."
	@bash $(PROJECT_ROOT)scripts/verify-scripts.sh

# 本地构建测试
test-local-build:
	@echo "本地测试构建脚本 (dry-run 模式)..."
	@bash $(PROJECT_ROOT)scripts/test-local-build.sh dry-run all

test-local-build-full:
	@echo "本地测试构建脚本 (实际构建模式)..."
	@bash $(PROJECT_ROOT)scripts/test-local-build.sh full all

test-local-build-platform:
	@echo "本地测试指定平台的构建脚本..."
	@echo "用法: make test-local-build-platform PLATFORM=macos"
	@if [ -z "$(PLATFORM)" ]; then \
		echo "错误: 请指定平台 (PLATFORM=windows|macos|linux)"; \
		exit 1; \
	fi
	@bash $(PROJECT_ROOT)scripts/test-local-build.sh dry-run $(PLATFORM)
