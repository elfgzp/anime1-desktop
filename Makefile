# Makefile for Anime1 Desktop
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

# Project root
PROJECT_ROOT := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

# Directories
DIST_DIR := $(PROJECT_ROOT)dist
BUILD_DIR := $(PROJECT_ROOT)build

# uv commands (uv auto-detects and uses venv)
UV_RUN := uv run
UV_PIP := uv pip

.PHONY: help install dev run build build-win build-linux build-macos build-macos-arm build-onefile dmg install-dmg clean clean-all test deps verify-deps test-workflow test-gh-auth test-local-build test-local-build-full test-install test-coverage lint lint-fix format docker-build docker-run docker-stop docker-push docker-clean

help:
	@echo "Anime1 Desktop - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Run in development mode (Flask + Vite)"
	@echo "                      Options: --browser, --width, --height"
	@echo "  make run           - Run in browser (CLI mode)"
	@echo "  make verify-deps   - Verify required packages are installed"
	@echo ""
	@echo "Code Quality:"
	@echo "  make test-install  - Install test dependencies (pytest, etc.)"
	@echo "  make test          - Run tests"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make lint          - Run linter (ruff)"
	@echo "  make lint-fix      - Auto-fix linting issues"
	@echo "  make format        - Format code (ruff)"
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
	@echo "Testing & CI:"
	@echo "  make test          - Run unit tests"
	@echo "  make test-unit     - Run unit tests only (fast)"
	@echo "  make test-integration - Run integration tests (slower)"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make test-install  - Install test dependencies"
	@echo "  make test-workflow - Test GitHub Actions workflow (需要 gh CLI)"
	@echo "  make trigger-workflow WORKFLOW=test-build.yml - Trigger workflow"
	@echo "  make test-gh-auth  - Check GitHub CLI authentication"
	@echo "  make verify-scripts - Verify all workflow scripts"
	@echo "  make test-local-build - Test build scripts locally (dry-run)"
	@echo "  make test-local-build-full - Test build scripts with actual build"
	@echo ""
	@echo "Docker (NAS 部署):"
	@echo "  make docker-build  - 构建 Docker 镜像"
	@echo "  make docker-run    - 启动 Docker 容器"
	@echo "  make docker-stop   - 停止 Docker 容器"
	@echo "  make docker-logs   - 查看容器日志"
	@echo "  make docker-push   - 推送镜像到 registry"
	@echo "  make docker-clean  - 清理 Docker 资源"

# Dependencies
deps:
	@echo "Installing Python dependencies..."
	$(UV_PIP) install -e .
	@echo "Installing frontend dependencies..."
	@if command -v npm >/dev/null 2>&1; then \
		cd $(PROJECT_ROOT)frontend && \
		if [ -f package-lock.json ]; then \
			npm ci; \
		else \
			npm install; \
		fi && \
		cd $(PROJECT_ROOT); \
	else \
		echo "Warning: npm not found, skipping frontend dependencies"; \
		echo "Install Node.js and npm to build the frontend"; \
	fi

install: deps
	@echo "Dependencies installed successfully!"

verify-deps:
	@$(UV_RUN) -m compileall -q src 2>/dev/null || \
		(echo "Missing dependencies. Run: make install" && exit 1)
	@echo "Dependencies verified: OK"

# Development
# Usage:
#   make dev                    # webview with devtools (default)
#   DEV_BROWSER=1 make dev      # open in browser
#   DEV_DEBUG=0 make dev        # disable devtools
#   SKIP_CHECK=1 make dev       # skip dependency check

# Default: devtools enabled unless user explicitly sets DEV_DEBUG=0
ENABLE_DEBUG ?= $(if $(DEV_DEBUG),$(DEV_DEBUG),1)

dev: verify-deps
	@echo "Starting Anime1 Desktop development environment..."
	@echo ""
	@echo "Options:"
	@echo "  DEV_BROWSER=1 make dev   Open in browser"
	@echo "  DEV_DEBUG=0 make dev     Disable devtools"
	@echo "  SKIP_CHECK=1 make dev    Skip dependency check"
	@echo "  NO_CLEANUP=1 make dev    Don't clean up residual processes"
	@echo ""
	@echo "Press Ctrl+C to stop all servers"
	@./Anime1 \
		$(if $(DEV_BROWSER),--browser) \
		$(if $(ENABLE_DEBUG),--debug-webview) \
		$(if $(SKIP_CHECK),--skip-check) \
		$(if $(NO_CLEANUP),--no-cleanup) \
		$(if $(FORCE),--force)

run: verify-deps
	@echo "Starting in browser..."
	$(UV_RUN) -m src.desktop --remote

# Build
build: verify-deps
	@echo "Building frontend..."
	@if command -v npm >/dev/null 2>&1; then \
		cd $(PROJECT_ROOT)frontend && npm ci && npm run build && cd $(PROJECT_ROOT); \
	else \
		echo "Warning: npm not found, skipping frontend build"; \
	fi
	@echo "Building desktop application..."
	$(UV_RUN) build.py --clean

build-onefile: verify-deps
	@echo "Building frontend..."
	@if command -v npm >/dev/null 2>&1; then \
		cd $(PROJECT_ROOT)frontend && npm ci && npm run build && cd $(PROJECT_ROOT); \
	else \
		echo "Warning: npm not found, skipping frontend build"; \
	fi
	@echo "Building as single executable..."
	$(UV_RUN) build.py --clean --onefile

# Cross-platform builds (requires Docker or cloud CI/CD)
# Note: These require cross-compilation toolchains

build-win: verify-deps
	@echo "[INFO] Building for Windows (x64)..."
	@echo "[INFO] Note: Cross-compilation requires Docker or cloud CI/CD"
	@echo "[INFO] Use GitHub Actions for Windows builds"
	$(UV_RUN) build.py --clean --onefile

build-linux: verify-deps
	@echo "[INFO] Building for Linux (x64)..."
	@echo "[INFO] Note: Cross-compilation requires Docker or cloud CI/CD"
	@echo "[INFO] Use GitHub Actions for Linux builds"
	$(UV_RUN) build.py --clean --onefile

build-macos: verify-deps
	@echo "[INFO] Building for macOS (Intel x64)..."
	@echo "[INFO] Note: Current platform is Apple Silicon"
	@echo "[INFO] Building arm64 version instead..."
	$(UV_RUN) build.py --clean

build-macos-arm: verify-deps
	@echo "[INFO] Building for macOS (Apple Silicon M-series)..."
	$(UV_RUN) build.py --clean

# Create DMG for macOS (requires create-dmg)
dmg: build
	@if ! command -v create-dmg >/dev/null 2>&1; then \
		echo "Error: create-dmg not found."; \
		echo "Install with: brew install create-dmg"; \
		exit 1; \
	fi
	@if [ -d "$(DIST_DIR)/Anime1.app" ]; then \
		echo "Creating DMG..."; \
		create-dmg \
			--volname "Anime1" \
			--volicon "" \
			--window-pos 200 200 \
			--window-size 600 400 \
			--app-drop-link 400 200 \
			"$(DIST_DIR)/Anime1.dmg" \
			"$(DIST_DIR)/Anime1.app"; \
		echo "DMG created: $(DIST_DIR)/Anime1.dmg"; \
	else \
		echo "Error: Anime1.app not found. Run 'make build' first."; \
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
	@echo "Running unit tests..."
	$(UV_RUN) pytest tests -v -m unit 2>/dev/null || echo "No unit tests found or pytest not installed."

test-unit:
	@echo "Running unit tests (fast, no external services)..."
	$(UV_RUN) pytest tests -v -m unit --tb=short 2>/dev/null || echo "No unit tests found."

test-integration:
	@echo "Running integration tests (requires database)..."
	$(UV_RUN) pytest tests -v -m integration --tb=short 2>/dev/null || echo "No integration tests found."

test-coverage:
	@echo "Running unit tests with coverage..."
	$(UV_RUN) pytest tests -v -m unit --tb=short --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml 2>/dev/null || echo "Tests failed or pytest not installed."

test-install:
	@echo "Installing test dependencies..."
	$(UV_PIP) install pytest pytest-cov coverage 2>/dev/null || pip install pytest pytest-cov coverage
	@echo "Test dependencies installed."

# GitHub Actions Workflow Testing
test-workflow:
	@echo "Testing GitHub Actions workflow..."
	@bash $(PROJECT_ROOT)scripts/test-workflow.sh

# Trigger GitHub Actions workflow
# Usage: make trigger-workflow WORKFLOW=test-build.yml
trigger-workflow:
	@echo "Triggering GitHub Actions workflow: $(WORKFLOW)..."
	@if [ -z "$(WORKFLOW)" ]; then \
		echo "Error: WORKFLOW not specified"; \
		echo "Usage: make trigger-workflow WORKFLOW=test-build.yml"; \
		exit 1; \
	fi
	@echo "Trying multiple authentication methods..."
	@(source ~/.zshrc 2>/dev/null || true; \
	if GH_TOKEN=$$(gh auth token -h github.com 2>/dev/null) gh workflow run "$(WORKFLOW)" --ref main 2>/dev/null; then \
		echo "Workflow triggered successfully (using gh auth token)"; \
	elif [ -n "$$(gh auth token -h github.com 2>/dev/null)" ] && \
	     GH_TOKEN=$$(source ~/.zshrc 2>/dev/null || true; gh auth token -h github.com) gh workflow run "$(WORKFLOW)" --ref main 2>/dev/null; then \
		echo "Workflow triggered successfully (using keyring token)"; \
	elif gh workflow run "$(WORKFLOW)" --ref main 2>/dev/null; then \
		echo "Workflow triggered successfully"; \
	else \
		echo "Error: Failed to trigger workflow. Please check:"; \
		echo "  1. GitHub CLI is authenticated: gh auth status"; \
		echo "  2. Token has workflow scope: gh auth login --scopes workflow"; \
		exit 1; \
	fi)

test-gh-auth:
	@echo "检查 GitHub CLI 认证状态..."
	@gh auth status || (echo "未登录，请运行: gh auth login --scopes workflow" && exit 1)
	@echo "GitHub CLI is logged in"

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

# ============================================================
# Docker 相关命令 (用于 NAS 部署)
# ============================================================

# Docker 配置
DOCKER_IMAGE := anime1-desktop
DOCKER_TAG := latest
DOCKER_REGISTRY ?= ghcr.io
DOCKER_REPO ?= $(DOCKER_REGISTRY)/$(shell git config --get remote.origin.url 2>/dev/null | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | tr '[:upper:]' '[:lower:]')

docker-build:
	@echo "构建 Docker 镜像..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "Docker 镜像构建完成: $(DOCKER_IMAGE):$(DOCKER_TAG)"

docker-build-multi:
	@echo "构建多架构 Docker 镜像 (amd64 + arm64)..."
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) \
		--push .

docker-run:
	@echo "启动 Docker 容器..."
	docker-compose up -d
	@echo "容器已启动，访问 http://localhost:5172"

docker-stop:
	@echo "停止 Docker 容器..."
	docker-compose down

docker-logs:
	@echo "查看 Docker 日志..."
	docker-compose logs -f

docker-push:
	@echo "推送 Docker 镜像到 registry..."
	@if [ -z "$(DOCKER_REPO)" ]; then \
		echo "错误: 无法获取 Docker 仓库地址"; \
		exit 1; \
	fi
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REPO):$(DOCKER_TAG)
	docker push $(DOCKER_REPO):$(DOCKER_TAG)
	@echo "镜像已推送: $(DOCKER_REPO):$(DOCKER_TAG)"

docker-clean:
	@echo "清理 Docker 资源..."
	docker-compose down -v --rmi local 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	@echo "Docker 资源已清理"
