# FastAPI 推理服务文档

## 概述

PIU 风险分类模型的 REST API 服务，使用 FastAPI 构建。

## 安装依赖

```bash
pip install fastapi uvicorn pydantic
```

## 启动服务

```bash
# 开发模式
uvicorn src.deployment.fastapi_app:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.deployment.fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 端点

### 1. 根端点
```
GET /
```

返回 API 基本信息。

### 2. 健康检查
```
GET /health
```

检查服务和模型状态。

**响应示例**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "piu-risk@champion"
}
```

### 3. 模型信息
```
GET /model_info
```

获取当前加载模型的详细信息。

**响应示例**:
```json
{
  "model_name": "piu-risk",
  "model_version": "1",
  "model_alias": "champion",
  "mlflow_run_id": "abc123...",
  "training_metrics": {
    "qwk": 0.365,
    "macro_f1": 0.362,
    "balanced_accuracy": 0.404
  },
  "feature_version": "v1",
  "n_features": 100
}
```

### 4. 预测
```
POST /predict
```

对输入数据进行 PIU 风险预测。

**请求体**:
```json
{
  "age": 12.5,
  "sex": 1,
  "bmi": 18.5,
  "height": 150.0,
  "weight": 45.0,
  "cgas_score": 75.0
}
```

**响应示例**:
```json
{
  "prediction": 1,
  "prediction_label": "Mild",
  "probabilities": [0.25, 0.50, 0.20, 0.05],
  "confidence": 0.50
}
```

### 5. 重新加载模型
```
POST /reload_model?alias=champion
```

重新加载指定别名的模型。

## 使用示例

### Python 客户端

```python
import requests

# 健康检查
response = requests.get("http://localhost:8000/health")
print(response.json())

# 预测
data = {
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5,
    "cgas_score": 75.0
}

response = requests.post("http://localhost:8000/predict", json=data)
result = response.json()

print(f"Prediction: {result['prediction_label']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### cURL

```bash
# 健康检查
curl http://localhost:8000/health

# 预测
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5,
    "cgas_score": 75.0
  }'
```

## 交互式文档

FastAPI 自动生成交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 注意事项

1. **模型加载**: 服务启动时自动从 MLflow Registry 加载 `champion` 别名的模型
2. **特征工程**: 当前 `prepare_features` 是简化版本，需要根据实际训练时的特征工程调整
3. **CORS**: 生产环境应限制允许的域名
4. **错误处理**: 已实现基本错误处理，可根据需要扩展

## 部署建议

### Docker 部署
参见 `docker/Dockerfile.infer`

### 使用 Gunicorn + Uvicorn
```bash
gunicorn src.deployment.fastapi_app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 监控

建议添加：
- Prometheus metrics
- 请求日志
- 性能监控
- 错误追踪（如 Sentry）
