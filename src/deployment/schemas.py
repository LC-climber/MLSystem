"""
FastAPI 推理服务 - 数据模型定义

使用 Pydantic 定义请求和响应的数据结构。
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class SeverityLevel(str, Enum):
    """PIU 严重程度级别"""
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"


class PredictionRequest(BaseModel):
    """预测请求"""

    # 基本人口统计学特征
    age: float = Field(..., ge=0, le=100, description="年龄（岁）")
    sex: int = Field(..., ge=0, le=1, description="性别 (0=女, 1=男)")

    # 身体指标
    bmi: Optional[float] = Field(None, ge=10, le=50, description="BMI")
    height: Optional[float] = Field(None, ge=50, le=250, description="身高（cm）")
    weight: Optional[float] = Field(None, ge=10, le=200, description="体重（kg）")

    # CGAS 评分
    cgas_score: Optional[float] = Field(None, ge=0, le=100, description="CGAS 评分")

    # 可选：actigraphy 特征（如果使用 feat_v2）
    actigraphy_features: Optional[Dict[str, float]] = Field(None, description="Actigraphy 特征字典")

    # 可选：其他特征
    additional_features: Optional[Dict[str, float]] = Field(None, description="其他特征")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 12.5,
                "sex": 1,
                "bmi": 18.5,
                "height": 150.0,
                "weight": 45.0,
                "cgas_score": 75.0
            }
        }


class PredictionResponse(BaseModel):
    """预测响应"""

    prediction: int = Field(..., ge=0, le=3, description="预测类别 (0=None, 1=Mild, 2=Moderate, 3=Severe)")
    prediction_label: SeverityLevel = Field(..., description="预测标签")
    probabilities: List[float] = Field(..., description="各类别概率 [P(None), P(Mild), P(Moderate), P(Severe)]")
    confidence: float = Field(..., ge=0, le=1, description="置信度（最大概率）")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 1,
                "prediction_label": "Mild",
                "probabilities": [0.25, 0.50, 0.20, 0.05],
                "confidence": 0.50
            }
        }


class ModelInfo(BaseModel):
    """模型信息"""

    model_name: str = Field(..., description="模型名称")
    model_version: str = Field(..., description="模型版本")
    model_alias: str = Field(..., description="模型别名")
    mlflow_run_id: str = Field(..., description="MLflow Run ID")

    # 训练指标
    training_metrics: Dict[str, float] = Field(..., description="训练指标")

    # 特征信息
    feature_version: str = Field(..., description="特征版本")
    n_features: int = Field(..., description="特征数量")

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    model_loaded: bool = Field(..., description="模型是否已加载")
    model_name: Optional[str] = Field(None, description="当前加载的模型名称")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "model_name": "piu-risk@champion"
            }
        }


class ErrorResponse(BaseModel):
    """错误响应"""

    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "PredictionError",
                "message": "Failed to predict",
                "detail": "Model not loaded"
            }
        }
