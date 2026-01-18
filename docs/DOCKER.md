# Docker 部署指南 (NAS)

Anime1 Desktop 提供 Docker 版本，适合在 NAS（群晖、威联通等）或任何支持 Docker 的服务器上运行。

## 特点

- 🐳 无需 GUI 依赖，纯 Web 服务
- 📦 支持 amd64 和 arm64 架构（适配各类 NAS）
- 💾 数据持久化存储
- 🔄 健康检查和自动重启
- 🔒 非 root 用户运行

## 快速开始

### 方式一：使用 Docker Compose（推荐）

1. 创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  anime1:
    image: ghcr.io/elfgzp/anime1-desktop:latest
    container_name: anime1
    restart: unless-stopped
    ports:
      - "5172:5172"
    volumes:
      - anime1_data:/app/data
    environment:
      - TZ=Asia/Shanghai

volumes:
  anime1_data:
```

2. 启动服务：

```bash
docker-compose up -d
```

3. 访问 `http://你的NAS地址:5172`

### 方式二：使用 Docker CLI

```bash
# 拉取镜像
docker pull ghcr.io/elfgzp/anime1-desktop:latest

# 创建数据卷
docker volume create anime1_data

# 运行容器
docker run -d \
  --name anime1 \
  --restart unless-stopped \
  -p 5172:5172 \
  -v anime1_data:/app/data \
  -e TZ=Asia/Shanghai \
  ghcr.io/elfgzp/anime1-desktop:latest
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TZ` | `UTC` | 时区设置，建议设置为 `Asia/Shanghai` |
| `ANIME1_HOST` | `0.0.0.0` | 监听地址 |
| `ANIME1_PORT` | `5172` | 监听端口 |
| `ANIME1_DATA_DIR` | `/app/data` | 数据存储目录 |

### 端口映射

- `5172`: Web 服务端口

### 数据持久化

建议挂载 `/app/data` 目录以持久化存储：
- 数据库文件
- 收藏列表
- 播放历史
- 缓存数据

## NAS 部署指南

### 群晖 (Synology DSM)

1. 打开 **Container Manager** (Docker)
2. **注册表** → 搜索 `ghcr.io/elfgzp/anime1-desktop`
3. 下载 `latest` 标签
4. **映像** → 选择下载的映像 → **启动**
5. 配置设置：
   - 端口设置：本地端口 `5172` → 容器端口 `5172`
   - 存储空间设置：装载本地文件夹 → `/app/data`
   - 环境：添加 `TZ=Asia/Shanghai`
6. 完成并启动

### 威联通 (QNAP)

1. 打开 **Container Station**
2. **创建** → **从 Docker Hub 提取**
3. 输入 `ghcr.io/elfgzp/anime1-desktop:latest`
4. 配置：
   - 网络：端口映射 `5172:5172`
   - 共享文件夹：挂载到 `/app/data`
   - 环境变量：`TZ=Asia/Shanghai`
5. 创建并启动

### UnRAID

1. 在 **Docker** 标签页点击 **Add Container**
2. 配置：
   ```
   Repository: ghcr.io/elfgzp/anime1-desktop:latest
   Network Type: Bridge
   Port Mappings: 5172 -> 5172
   Path: /mnt/user/appdata/anime1 -> /app/data
   Variable: TZ=Asia/Shanghai
   ```
3. 点击 **Apply**

## 本地构建

如果你想自己构建镜像：

```bash
# 克隆仓库
git clone https://github.com/elfgzp/anime1-desktop.git
cd anime1-desktop

# 构建镜像
make docker-build

# 或使用 docker-compose
docker-compose build

# 启动
make docker-run
```

## 更新

### 使用 Docker Compose

```bash
# 拉取最新镜像
docker-compose pull

# 重新创建容器
docker-compose up -d
```

### 使用 Docker CLI

```bash
# 停止并删除旧容器
docker stop anime1
docker rm anime1

# 拉取最新镜像
docker pull ghcr.io/elfgzp/anime1-desktop:latest

# 重新运行
docker run -d \
  --name anime1 \
  --restart unless-stopped \
  -p 5172:5172 \
  -v anime1_data:/app/data \
  -e TZ=Asia/Shanghai \
  ghcr.io/elfgzp/anime1-desktop:latest
```

## 故障排除

### 查看日志

```bash
# Docker Compose
docker-compose logs -f

# Docker CLI
docker logs -f anime1
```

### 容器无法启动

1. 检查端口是否被占用：
   ```bash
   netstat -tlnp | grep 5172
   ```

2. 检查数据目录权限：
   ```bash
   docker exec anime1 ls -la /app/data
   ```

### 网络问题

如果无法访问 anime1.me，检查 NAS 的 DNS 设置和网络连接。

## 资源限制

对于资源有限的 NAS，可以添加资源限制：

```yaml
services:
  anime1:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1'
        reservations:
          memory: 128M
```

## 反向代理配置

### Nginx

```nginx
server {
    listen 80;
    server_name anime1.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5172;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Traefik (Docker Labels)

```yaml
services:
  anime1:
    # ... 其他配置
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.anime1.rule=Host(`anime1.yourdomain.com`)"
      - "traefik.http.services.anime1.loadbalancer.server.port=5172"
```

## 相关链接

- [项目主页](https://github.com/elfgzp/anime1-desktop)
- [问题反馈](https://github.com/elfgzp/anime1-desktop/issues)
- [Docker Hub](https://ghcr.io/elfgzp/anime1-desktop)
