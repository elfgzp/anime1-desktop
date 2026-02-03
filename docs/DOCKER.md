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
| `ANIME1_DOWNLOAD_PATH` | `/app/data/downloads` | **自动下载路径**（Docker 默认已设置，无需修改） |

### 端口映射

- `5172`: Web 服务端口

### 数据持久化

建议挂载 `/app/data` 目录以持久化存储：
- 数据库文件
- 收藏列表
- 播放历史
- 缓存数据
- 自动下载配置

#### 数据目录结构

容器内 `/app/data` 目录结构：

```
/app/data/
├── anime1.db                 # 主数据库（收藏、历史记录等）
├── auto_download_config.json # 自动下载配置
├── auto_download_history.json# 自动下载历史
└── downloads/                # 默认下载目录（自动创建）
    ├── 2024/
    │   └── 番剧名称/
    │       └── 第01集.mp4
    └── 2025/
        └── ...
```

#### 目录映射配置（推荐）

为了便于管理和备份，建议将数据目录映射到宿主机明确的路径：

**Linux / NAS 推荐配置：**

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
      # 数据目录（配置、数据库）
      - /opt/anime1/data:/app/data
      # 下载目录（番剧文件）- 独立挂载便于管理
      - /mnt/downloads/anime:/app/data/downloads
    environment:
      - TZ=Asia/Shanghai
```

**各平台路径示例：**

| 平台 | 数据路径 | 下载路径 |
|------|----------|----------|
| Linux | `/opt/anime1/data` | `/mnt/downloads/anime` |
| 群晖 DSM | `/volume1/docker/anime1/data` | `/volume1/downloads/anime` |
| 威联通 QNAP | `/share/Container/anime1/data` | `/share/Downloads/anime` |
| UnRAID | `/mnt/user/appdata/anime1` | `/mnt/user/media/anime` |

### 自动下载配置

容器支持自动下载功能，可以定期检查和下载新番剧。

#### 启用自动下载

1. **通过 Web UI 配置**（推荐）：
   - 访问 `http://你的NAS地址:5172`
   - 点击左侧菜单「自动下载」
   - 开启「启用自动下载」
   - 配置下载路径（容器内默认为 `/app/data/downloads`）
   - 设置检查间隔（默认每6小时检查一次）
   - 保存配置

2. **通过环境变量预配置**：

```yaml
services:
  anime1:
    image: ghcr.io/elfgzp/anime1-desktop:latest
    container_name: anime1
    restart: unless-stopped
    ports:
      - "5172:5172"
    volumes:
      - anime1_data:/app/data
      # 可选：将下载目录挂载到主机
      - ./downloads:/app/data/downloads
    environment:
      - TZ=Asia/Shanghai
      # 预配置自动下载（通过API或UI配置更灵活）
      - ANIME1_AUTO_DOWNLOAD_ENABLED=true
      - ANIME1_AUTO_DOWNLOAD_PATH=/app/data/downloads
```

#### 自动下载目录挂载

如果要将下载的文件保存到 NAS 的特定目录，需要额外挂载下载目录：

```yaml
volumes:
  # 数据持久化
  - anime1_data:/app/data
  # 下载目录（替换为你NAS上的实际路径）
  - /volume1/downloads/anime:/app/data/downloads
```

**Linux 宿主机路径映射注意事项：**

1. **权限设置**：容器以 UID 1000 运行，确保宿主机目录有正确权限

```bash
# 创建目录
sudo mkdir -p /opt/anime1/data /mnt/downloads/anime

# 设置权限（UID 1000 对应容器内 anime1 用户）
sudo chown -R 1000:1000 /opt/anime1/data /mnt/downloads/anime

# 或者设置为当前用户
sudo chown -R $(id -u):$(id -g) /opt/anime1/data /mnt/downloads/anime
```

2. **SELinux 用户（RHEL/CentOS/Fedora）**：

如果使用 SELinux，需要添加 `:Z` 或 `:z` 标签：

```yaml
volumes:
  - /opt/anime1/data:/app/data:Z
  - /mnt/downloads/anime:/app/data/downloads:Z
```

3. **路径说明**：

| 容器内路径 | 用途 | 是否必须挂载 |
|-----------|------|-------------|
| `/app/data` | 数据库和配置文件 | 是 |
| `/app/data/downloads` | 番剧下载目录 | 可选（建议单独挂载） |

**重要提示**：如果仅挂载 `/app/data/downloads` 而不挂载父目录 `/app/data`，需要确保 `/app/data` 有持久化存储（使用命名卷或挂载其他目录），否则配置会丢失。

#### 自动下载配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 启用自动下载 | 开启/关闭自动下载功能 | false |
| 下载路径 | 番剧下载保存位置 | `/app/data/downloads`（已通过环境变量预设） |
| 检查间隔 | 多久检查一次新番剧 | 6小时 |
| 自动下载新番 | 自动下载最新番剧 | true |
| 自动下载追番 | 自动下载收藏列表中的番剧 | false |
| 年份过滤 | 只下载指定年份的番剧 | 全部 |
| 季节过滤 | 只下载指定季节的番剧 | 全部 |
| 排除关键词 | 标题包含这些关键词的番剧不会下载 | 空 |

**注意**：Docker 版本已自动设置 `ANIME1_DOWNLOAD_PATH=/app/data/downloads`，确保下载的文件保存在持久化卷中。如果你希望下载到其他位置，可以在 Web UI 中修改配置，或者挂载额外的卷。

#### Docker 中自动下载测试验证

测试自动下载是否正常工作：

```bash
# 1. 启动容器
docker run -d \
  --name anime1 \
  -p 5172:5172 \
  -v anime1_data:/app/data \
  ghcr.io/elfgzp/anime1-desktop:latest

# 2. 检查自动下载状态
curl http://localhost:5172/api/auto-download/status
# 应返回 download_path: "/app/data/downloads"

# 3. 启用自动下载并测试
curl -X POST http://localhost:5172/api/auto-download/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "auto_download_new": true}'
```

#### 查看下载进度

在 Web UI 的「自动下载」页面可以：
- 查看当前下载进度
- 查看下载历史记录
- 手动触发立即检查
- 测试下载配置
- 预览符合条件的番剧列表

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

### Linux 服务器（通用）

适用于 Ubuntu、Debian、CentOS 等 Linux 发行版：

1. **创建目录结构**：

```bash
sudo mkdir -p /opt/anime1/{data,downloads}
sudo chown -R 1000:1000 /opt/anime1
```

2. **创建 docker-compose.yml**：

```bash
cat > /opt/anime1/docker-compose.yml << 'EOF'
version: '3.8'

services:
  anime1:
    image: ghcr.io/elfgzp/anime1-desktop:latest
    container_name: anime1
    restart: unless-stopped
    ports:
      - "5172:5172"
    volumes:
      - /opt/anime1/data:/app/data
      - /opt/anime1/downloads:/app/data/downloads
    environment:
      - TZ=Asia/Shanghai
EOF
```

3. **启动服务**：

```bash
cd /opt/anime1
sudo docker-compose up -d
```

4. **设置自动启动**：

```bash
# 确保 Docker 服务开机自启
sudo systemctl enable docker

# 容器已通过 restart: unless-stopped 配置自动启动
```

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

## 更新与升级

### 安全更新策略（推荐）

由于数据已挂载到宿主机，更新容器不会丢失任何数据：

```bash
# 1. 查看当前运行状态
docker-compose ps

# 2. 备份数据（可选但推荐）
cp -r /opt/anime1/data /opt/anime1/data.backup.$(date +%Y%m%d)

# 3. 拉取最新镜像
docker-compose pull

# 4. 重新创建容器（数据会保留）
docker-compose up -d

# 5. 验证更新
docker-compose logs --tail=20
```

### 使用 Docker Compose 更新

```bash
# 拉取最新镜像
docker-compose pull

# 重新创建容器（数据卷会自动挂载）
docker-compose up -d

# 清理旧镜像（可选）
docker image prune -f
```

### 使用 Docker CLI 更新

```bash
# 停止并删除旧容器（数据卷不会删除）
docker stop anime1
docker rm anime1

# 拉取最新镜像
docker pull ghcr.io/elfgzp/anime1-desktop:latest

# 重新运行（使用相同的数据卷）
docker run -d \
  --name anime1 \
  --restart unless-stopped \
  -p 5172:5172 \
  -v anime1_data:/app/data \
  -e TZ=Asia/Shanghai \
  ghcr.io/elfgzp/anime1-desktop:latest
```

### 更新后数据验证

更新后验证数据完整性：

```bash
# 检查数据库文件
docker exec anime1 ls -la /app/data/

# 检查自动下载配置
docker exec anime1 cat /app/data/auto_download_config.json

# 检查下载的文件
docker exec anime1 ls -la /app/data/downloads/
```

## 备份与恢复

### 备份数据

**方法1：备份挂载目录（推荐）**

如果使用的是主机目录映射：

```bash
# 停止容器确保数据一致性
docker-compose stop

# 备份整个数据目录
tar -czvf anime1_backup_$(date +%Y%m%d).tar.gz /opt/anime1/data

# 或者仅备份数据库和配置
tar -czvf anime1_config_backup_$(date +%Y%m%d).tar.gz \
  /opt/anime1/data/anime1.db \
  /opt/anime1/data/*.json
```

**方法2：从容器内备份**

如果使用命名卷：

```bash
# 创建临时容器备份数据
docker run --rm \
  -v anime1_data:/data \
  -v $(pwd):/backup \
  alpine tar -czvf /backup/anime1_backup.tar.gz -C /data .
```

### 恢复数据

```bash
# 停止容器
docker-compose stop

# 恢复数据（确保先备份当前数据）
tar -xzvf anime1_backup_20240115.tar.gz -C /opt/anime1/

# 重启容器
docker-compose start
```

### 自动备份脚本

可以设置定时任务自动备份：

```bash
#!/bin/bash
# /opt/anime1/backup.sh

BACKUP_DIR="/opt/anime1/backups"
DATA_DIR="/opt/anime1/data"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

# 创建备份
tar -czvf "$BACKUP_DIR/anime1_$(date +%Y%m%d_%H%M%S).tar.gz" -C "$DATA_DIR" .

# 删除旧备份
find "$BACKUP_DIR" -name "anime1_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $(date)"
```

添加到 crontab（每天凌晨3点备份）：

```bash
0 3 * * * /opt/anime1/backup.sh >> /var/log/anime1_backup.log 2>&1
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
