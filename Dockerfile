# Anime1 Desktop - Docker Version (NAS)
# 无需 webview，纯 Web 服务

# Build stage - 构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖（需要 devDependencies 来构建）
RUN npm ci

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build

# Python runtime stage
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户，并配置 sudo 免密
RUN useradd -m -u 1000 anime1 && \
    mkdir -p /app/data /app/static && \
    chown -R anime1:anime1 /app && \
    echo "anime1 ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

# 复制 Python 依赖文件
COPY pyproject.toml ./

# 安装 Python 依赖（排除 pywebview 和 pyinstaller）
RUN pip install --no-cache-dir \
    flask>=2.3.0 \
    flask-cors>=4.0.0 \
    beautifulsoup4>=4.12.0 \
    requests>=2.31.0 \
    pillow>=10.0.0 \
    hanziconv>=0.3.2 \
    peewee>=3.17.0 \
    m3u8>=3.0.0 \
    jinja2>=3.1.0 \
    markupsafe>=2.1.0 \
    werkzeug>=3.0.0 \
    urllib3>=2.0.0 \
    certifi>=2023.0.0 \
    soupsieve>=2.5.0

# 复制后端源码
COPY src/ ./src/

# 从构建阶段复制前端产物
COPY --from=frontend-builder /app/frontend/dist ./static/dist/

# 复制 entrypoint 脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ANIME1_HOST=0.0.0.0 \
    ANIME1_PORT=5172 \
    ANIME1_DATA_DIR=/app/data

# 切换到非 root 用户
USER anime1

# 暴露端口
EXPOSE 5172

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5172/api/anime?page=1 || exit 1

# 设置 entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# 启动命令
CMD ["python", "-m", "src.app", "--host", "0.0.0.0", "--port", "5172", "--no-browser"]
