# API 参考文档

## FastAPI 端点

Base URL: `http://localhost:8000`

---

## 端点列表

### 1. 健康检查

**GET** `/health`

检查服务健康状态。

#### 响应

```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2026-06-08T20:00:00Z"
}
```

#### 状态码
- `200`: 服务正常
- `500`: 服务异常

---

### 2. 获取模型信息

**GET** `/model_info`

获取当前加载模型的信息。

#### 响应

```json
{
  "model_name": "piu-risk",
  "model_version": "1",
  "model_alias": "champion",
  "feature_version": "v1",
  "n_features": 100,
  "classes": ["None", "Mild", "Moderate", "Severe"]
}
```

#### 状态码
- `200`: 成功
- `500`: 服务器错误

---

### 3. 风险预测

**POST** `/predict`

预测 PIU 风险等级。

#### 请求体

```json
{
  "age": 12.5,
  "sex": 1,
  "bmi": 18.5,
  "height": 150.0,
  "weight": 45.0,
  "cgas_score": 75.0,
  "actigraphy_features": {
    "act_mean_enmo": 35.2,
    "act_std_enmo": 12.5
  }
}
```

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| age | float | 是 | 年龄 (9-14) |
| sex | int | 是 | 性别 (0=女, 1=男) |
| bmi | float | 否 | BMI 指数 |
| height | float | 否 | 身高 (cm) |
| weight | float | 否 | 体重 (kg) |
| cgas_score | float | 否 | CGAS 评分 (0-100) |
| actigraphy_features | object | 否 | 活动记录特征 |

#### 响应

```json
{
  "prediction": 1,
  "prediction_label": "Mild",
  "confidence": 0.45,
  "probabilities": [0.30, 0.45, 0.20, 0.05],
  "severity_level": "MILD",
  "metadata": {
    "model_version": "1",
    "feature_version": "v1",
    "timestamp": "2026-06-08T20:00:00Z"
  }
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| prediction | int | 预测类别 (0-3) |
| prediction_label | string | 类别标签 |
| confidence | float | 置信度 (0-1) |
| probabilities | array | 各类别概率 |
| severity_level | string | 严重程度 |
| metadata | object | 元数据 |

#### 状态码
- `200`: 预测成功
- `422`: 请求参数错误
- `500`: 服务器错误

---

### 4. 批量预测

**POST** `/batch_predict`

批量预测多个样本。

#### 请求体

```json
{
  "samples": [
    {
      "age": 12.5,
      "sex": 1,
      "bmi": 18.5,
      "cgas_score": 75.0
    },
    {
      "age": 13.0,
      "sex": 0,
      "bmi": 19.2,
      "cgas_score": 68.0
    }
  ]
}
```

#### 响应

```json
{
  "predictions": [
    {
      "prediction": 1,
      "prediction_label": "Mild",
      "confidence": 0.45
    },
    {
      "prediction": 2,
      "prediction_label": "Moderate",
      "confidence": 0.38
    }
  ],
  "count": 2,
  "timestamp": "2026-06-08T20:00:00Z"
}
```

#### 状态码
- `200`: 成功
- `422`: 参数错误
- `500`: 服务器错误

---

### 5. 重新加载模型

**POST** `/reload_model`

重新加载模型（需要管理员权限）。

#### 请求体

```json
{
  "alias": "champion"
}
```

#### 响应

```json
{
  "status": "success",
  "message": "Model reloaded successfully",
  "model_version": "2"
}
```

#### 状态码
- `200`: 成功
- `403`: 权限不足
- `500`: 重载失败

---

## 数据模型

### PredictRequest

```python
class PredictRequest(BaseModel):
    age: float
    sex: int  # 0 or 1
    bmi: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    cgas_score: Optional[float] = None
    actigraphy_features: Optional[Dict[str, float]] = None
```

### PredictResponse

```python
class PredictResponse(BaseModel):
    prediction: int
    prediction_label: str
    confidence: float
    probabilities: List[float]
    severity_level: str
    metadata: Dict[str, Any]
```

---

## 错误响应

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Server Error

```json
{
  "detail": "Internal server error",
  "error": "Model prediction failed"
}
```

---

## 认证

当前版本不需要认证。生产环境建议添加：
- API Key 认证
- JWT Token
- OAuth 2.0

---

## 速率限制

当前无限制。生产环境建议：
- 每 IP: 100 请求/分钟
- 批量预测: 最多 100 样本/请求

---

## SDK 示例

### Python SDK

```python
import requests

class PIURiskClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def predict(self, **kwargs):
        response = requests.post(
            f"{self.base_url}/predict",
            json=kwargs
        )
        return response.json()
    
    def health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# 使用
client = PIURiskClient()
result = client.predict(age=12.5, sex=1, bmi=18.5)
```

---

## 更多信息

- **OpenAPI 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **GitHub**: https://github.com/LC-climber/MLSystem

---

**版本**: 1.0.0  
**更新时间**: 2026-06-08
