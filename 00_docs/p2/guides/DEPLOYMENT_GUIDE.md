# 部署指南

**项目**: PIU Risk Classifier  
**版本**: v1.0.0  
**更新日期**: 2026-06-08

---

## 概述

本指南提供完整的部署说明，涵盖开发、测试和生产环境。

---

## 🚀 快速部署（推荐）

### 使用 Docker Compose

这是最简单的部署方式，适合快速启动和测试。

```bash
# 1. 克隆仓库
git clone https://github.com/LC-climber/MLSystem.git
cd MLSystem

# 2. 启动服务
cd docker
docker-compose up -d

# 3. 验证服务
curl http://localhost:8000/health
```

**服务地址**:
- FastAPI: http://localhost:8000
- MLflow: http://localhost:5000
- API 文档: http://localhost:8000/docs

---

## 📦 部署选项

### 选项 1: Docker Compose（推荐）

**适用场景**: 快速部署、开发测试

**优点**:
- 一键启动所有服务
- 环境隔离
- 易于管理

**步骤**:

1. **准备环境**
   ```bash
   # 安装 Docker 和 Docker Compose
   # Linux
   curl -fsSL https://get.docker.com | sh
   sudo apt-get install docker-compose-plugin
   
   # macOS
   brew install docker docker-compose
   ```

2. **配置**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑配置（可选）
   vim .env
   ```

3. **启动**
   ```bash
   cd docker
   docker-compose up -d
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f
   ```

5. **停止服务**
   ```bash
   docker-compose down
   ```

---

### 选项 2: 本地 Python 环境

**适用场景**: 开发调试

**步骤**:

1. **创建虚拟环境**
   ```bash
   conda create -n mlsystem python=3.11
   conda activate mlsystem
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动 MLflow**
   ```bash
   mlflow server --host 0.0.0.0 --port 5000 &
   ```

4. **启动 FastAPI**
   ```bash
   uvicorn src.deployment.fastapi_app:app --host 0.0.0.0 --port 8000
   ```

---

### 选项 3: Kubernetes（生产环境）

**适用场景**: 大规模生产部署

**资源需求**:
- CPU: 2 cores
- 内存: 4GB
- 存储: 10GB

**配置示例**:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: piu-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: piu-inference
  template:
    metadata:
      labels:
        app: piu-inference
    spec:
      containers:
      - name: inference
        image: piu-inference:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: piu-inference-service
spec:
  selector:
    app: piu-inference
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**部署命令**:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

---

## 🔧 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# MLflow 配置
MLFLOW_TRACKING_URI=http://localhost:5000

# 模型配置
MODEL_NAME=piu-risk
MODEL_ALIAS=champion

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Docker 配置

**docker-compose.yml** 关键配置：

```yaml
services:
  mlflow:
    image: mlflow:latest
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlruns
    
  inference:
    build:
      context: ..
      dockerfile: docker/Dockerfile.infer
    ports:
      - "8000:8000"
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - mlflow
```

---

## 📊 监控和维护

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查模型信息
curl http://localhost:8000/model_info
```

### 日志查看

```bash
# Docker 环境
docker-compose logs -f inference

# 本地环境
tail -f logs/app.log
```

### 性能监控

**关键指标**:
- 响应时间: < 100ms
- QPS: 10+
- 错误率: < 1%
- CPU 使用: < 50%
- 内存使用: < 1GB

---

## 🔒 安全配置

### 生产环境建议

1. **启用 HTTPS**
   ```bash
   # 使用 Nginx 反向代理
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8000;
       }
   }
   ```

2. **添加认证**
   - API Key 认证
   - JWT Token
   - OAuth 2.0

3. **速率限制**
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.post("/predict")
   @limiter.limit("10/minute")
   async def predict(request: Request, data: PredictRequest):
       ...
   ```

---

## 🧪 测试部署

### 冒烟测试

```bash
#!/bin/bash
# test_deployment.sh

echo "Testing health endpoint..."
curl -f http://localhost:8000/health || exit 1

echo "Testing model info..."
curl -f http://localhost:8000/model_info || exit 1

echo "Testing prediction..."
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"age": 12.5, "sex": 1, "bmi": 18.5}' || exit 1

echo "All tests passed!"
```

### 负载测试

```bash
# 使用 Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# 使用 hey
hey -n 1000 -c 10 http://localhost:8000/health
```

---

## 🐛 故障排查

### 常见问题

#### 1. 服务无法启动

**症状**: Docker 容器启动失败

**解决**:
```bash
# 检查日志
docker-compose logs

# 检查端口占用
lsof -i :8000

# 重启服务
docker-compose restart
```

#### 2. 模型加载失败

**症状**: 404 Model Not Found

**解决**:
```bash
# 检查 MLflow
curl http://localhost:5000/api/2.0/mlflow/registered-models/get?name=piu-risk

# 重新注册模型
python scripts/register_baseline.py
```

#### 3. 预测错误

**症状**: 422 Validation Error

**解决**:
- 检查输入数据格式
- 查看 API 文档
- 验证必需字段

---

## 📈 扩展和优化

### 水平扩展

```bash
# Docker Compose 扩展
docker-compose up -d --scale inference=3

# Kubernetes 扩展
kubectl scale deployment piu-inference --replicas=5
```

### 性能优化

1. **启用缓存**
2. **模型优化** (量化、剪枝)
3. **批处理预测**
4. **异步处理**

---

## 📞 支持

- **文档**: 项目 00_docs/ 目录
- **问题**: GitHub Issues
- **邮件**: 项目团队

---

**版本**: 1.0.0  
**最后更新**: 2026-06-08
