# Docker 部署指南

## 概述

本项目提供两个 Docker 镜像：
1. **推理镜像** (`Dockerfile.infer`) - CPU 版本，用于生产推理
2. **训练镜像** (`Dockerfile.train`) - GPU 版本，用于模型训练

## 快速开始

### 使用 docker-compose（推荐）

```bash
# 启动 MLflow + 推理服务
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务地址：
- 推理 API: http://localhost:8000
- MLflow UI: http://localhost:5000

### 手动构建和运行

#### 推理镜像

```bash
# 构建镜像
docker build -f docker/Dockerfile.infer -t piu-infer:latest .

# 运行容器
docker run -d \
  --name piu-inference \
  -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://localhost:5000 \
  -e MODEL_ALIAS=champion \
  piu-infer:latest

# 测试
curl http://localhost:8000/health
```

#### 训练镜像

```bash
# 构建镜像
docker build -f docker/Dockerfile.train -t piu-train:latest .

# 运行容器（需要 GPU）
docker run -d \
  --gpus all \
  --name piu-training \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -e MLFLOW_TRACKING_URI=http://localhost:5000 \
  piu-train:latest

# 进入容器
docker exec -it piu-training bash

# 运行训练
python -m src.experiments.run_p2_optuna \
  --feature v2 \
  --trials 100 \
  --folds 5
```

## 镜像说明

### 推理镜像特点

- **基础镜像**: Python 3.11 slim
- **PyTorch**: CPU 版本
- **多阶段构建**: 优化镜像大小
- **非 root 用户**: 安全性增强
- **健康检查**: 自动监控服务状态
- **预期大小**: ~1.5 GB

### 训练镜像特点

- **基础镜像**: NVIDIA CUDA 12.1 + cuDNN 8
- **PyTorch**: GPU 版本 (CUDA 12.8)
- **完整依赖**: 包含 MLflow, Optuna, PySpark
- **数据挂载**: 支持本地数据挂载
- **预期大小**: ~8 GB

## 环境变量

### 推理服务

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow 服务地址 |
| `MODEL_ALIAS` | `champion` | 加载的模型别名 |
| `PYTHONUNBUFFERED` | `1` | Python 输出不缓冲 |

### 训练服务

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000` | MLflow 服务地址 |
| `CUDA_VISIBLE_DEVICES` | `0` | 使用的 GPU 设备 |

## 数据卷挂载

### 推理服务（可选）

```bash
docker run -d \
  -v $(pwd)/models:/app/models \
  piu-infer:latest
```

### 训练服务（推荐）

```bash
docker run -d \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/logs:/app/logs \
  piu-train:latest
```

## 生产部署建议

### 1. 使用环境变量文件

```bash
# .env
MLFLOW_TRACKING_URI=http://mlflow.example.com:5000
MODEL_ALIAS=champion
```

```bash
docker run -d --env-file .env piu-infer:latest
```

### 2. 使用反向代理

推荐使用 Nginx 或 Traefik 作为反向代理：

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 配置日志

```bash
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  piu-infer:latest
```

### 4. 资源限制

```bash
docker run -d \
  --cpus="2.0" \
  --memory="4g" \
  piu-infer:latest
```

## 故障排查

### 查看日志

```bash
# docker-compose
docker-compose logs -f inference

# 手动运行
docker logs -f piu-inference
```

### 进入容器调试

```bash
docker exec -it piu-inference bash
```

### 健康检查失败

```bash
# 检查服务是否运行
docker exec piu-inference curl http://localhost:8000/health

# 检查模型是否加载
docker exec piu-inference python -c "
from src.mlflow_utils.registry import get_model_by_alias
model = get_model_by_alias('piu-risk', 'champion')
print('Model loaded successfully')
"
```

### GPU 不可用

```bash
# 检查 NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# 确认 docker-compose 配置
# 取消注释 runtime: nvidia
```

## 清理

```bash
# 停止并删除容器
docker-compose down -v

# 删除镜像
docker rmi piu-infer:latest piu-train:latest

# 清理未使用的镜像
docker image prune -a
```

## 镜像优化建议

1. **多阶段构建**: 已实现，分离依赖安装和应用构建
2. **.dockerignore**: 添加以排除不必要文件
3. **缓存利用**: 依赖文件单独复制，利用 Docker 缓存
4. **安全扫描**: 使用 `docker scan` 检查漏洞
5. **镜像压缩**: 使用 `docker-slim` 进一步优化

## CI/CD 集成

### GitHub Actions 示例

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: docker/Dockerfile.infer
    push: true
    tags: ghcr.io/username/piu-infer:latest
```

## 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)
