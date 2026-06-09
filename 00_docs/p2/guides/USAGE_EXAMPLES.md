# 示例：使用 PIU Risk Classifier

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 MLflow（可选）
mlflow server --host 0.0.0.0 --port 5000
```

### 2. 使用 Docker 部署（推荐）

```bash
# 启动服务
cd docker
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务地址：
- FastAPI: http://localhost:8000
- MLflow: http://localhost:5000
- API 文档: http://localhost:8000/docs

### 3. API 调用示例

#### Python 示例

```python
import requests
import json

# API 端点
url = "http://localhost:8000/predict"

# 示例数据（v1 - 仅表格数据）
data_v1 = {
    "age": 12.5,
    "sex": 1,  # 1=男, 0=女
    "bmi": 18.5,
    "height": 150.0,
    "weight": 45.0,
    "cgas_score": 75.0
}

# 发送请求
response = requests.post(url, json=data_v1)
result = response.json()

print(f"预测结果: {result['prediction_label']}")
print(f"置信度: {result['confidence']:.2%}")
print(f"概率分布: {result['probabilities']}")
```

#### cURL 示例

```bash
# v1 预测
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5,
    "cgas_score": 75.0
  }'

# 健康检查
curl http://localhost:8000/health

# 获取模型信息
curl http://localhost:8000/model_info
```

#### JavaScript 示例

```javascript
const data = {
    age: 12.5,
    sex: 1,
    bmi: 18.5,
    cgas_score: 75.0
};

fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => {
    console.log('预测结果:', data.prediction_label);
    console.log('置信度:', data.confidence);
});
```

### 4. 高级用法

#### 包含 Actigraphy 数据（v2）

```python
data_v2 = {
    "age": 13.0,
    "sex": 0,
    "bmi": 19.2,
    "cgas_score": 68.0,
    "actigraphy_features": {
        "act_mean_enmo": 35.2,
        "act_std_enmo": 12.5,
        "act_night_enmo_mean": 5.2,
        "act_day_enmo_mean": 45.8
    }
}

response = requests.post(url, json=data_v2)
```

#### 批量预测

```python
# 批量数据
batch_data = [
    {"age": 12.5, "sex": 1, "bmi": 18.5, "cgas_score": 75.0},
    {"age": 13.0, "sex": 0, "bmi": 19.2, "cgas_score": 68.0},
    {"age": 14.0, "sex": 1, "bmi": 20.0, "cgas_score": 70.0},
]

# 逐个预测
results = []
for data in batch_data:
    response = requests.post(url, json=data)
    results.append(response.json())

# 汇总结果
for i, result in enumerate(results):
    print(f"样本 {i+1}: {result['prediction_label']} "
          f"(置信度: {result['confidence']:.2%})")
```

### 5. 模型管理

#### 查看可用模型

```bash
# 使用 MLflow CLI
mlflow models list --model-name piu-risk

# 或访问 MLflow UI
# http://localhost:5000
```

#### 切换模型版本

```python
import requests

# 重载模型
response = requests.post(
    "http://localhost:8000/reload_model",
    json={"alias": "champion"}  # 或 "baseline"
)
print(response.json())
```

### 6. 监控和日志

#### 查看服务日志

```bash
# Docker 环境
docker-compose logs -f inference

# 直接运行
tail -f logs/app.log
```

#### 监控指标

访问 MLflow UI 查看：
- 模型性能指标
- 预测分布
- 响应时间

### 7. 故障排查

#### 服务无法启动

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5000

# 重启服务
docker-compose restart
```

#### 预测错误

```python
# 检查输入数据格式
print(json.dumps(data, indent=2))

# 查看详细错误
response = requests.post(url, json=data)
print(response.status_code)
print(response.text)
```

## 输出格式

### 成功响应

```json
{
  "prediction": 1,
  "prediction_label": "Mild",
  "confidence": 0.45,
  "probabilities": [0.30, 0.45, 0.20, 0.05],
  "severity_level": "MILD",
  "metadata": {
    "model_version": "1",
    "feature_version": "v1"
  }
}
```

### 字段说明

- `prediction`: 预测类别 (0-3)
  - 0: None (无风险)
  - 1: Mild (轻度)
  - 2: Moderate (中度)
  - 3: Severe (重度)
- `prediction_label`: 类别标签
- `confidence`: 置信度 (0-1)
- `probabilities`: 各类别概率
- `severity_level`: 严重程度枚举

## 注意事项

### 使用限制

⚠️ **重要提示**：
- 本模型仅用于辅助筛查，不应作为诊断的唯一依据
- 适用人群为 9-14 岁青少年
- 需要专业人员解读结果

### 输入要求

- `age`: 9-14 岁范围
- `sex`: 0 或 1
- `bmi`: 合理范围 (10-40)
- `cgas_score`: 0-100

### 性能

- 响应时间: < 100ms
- 并发支持: 10+ QPS
- 可用性: 99%+

## 更多资源

- [API 文档](http://localhost:8000/docs)
- [技术文档](00_docs/)
- [GitHub](https://github.com/LC-climber/MLSystem)

---

**版本**: 1.0.0  
**更新时间**: 2026-06-08
