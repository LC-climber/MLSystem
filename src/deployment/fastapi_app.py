"""
FastAPI 推理服务应用

提供 PIU 风险分类模型的 REST API 接口。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import mlflow
import numpy as np
import logging
from typing import Optional

from src.deployment.schemas import (
    PredictionRequest,
    PredictionResponse,
    ModelInfo,
    HealthResponse,
    ErrorResponse,
    SeverityLevel,
)
from src.config import MLFLOW_TRACKING_URI
from src.mlflow_utils.registry import get_model_by_alias, get_model_metadata

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量存储加载的模型
_model = None
_model_metadata = None
_model_alias = "champion"  # 默认使用 champion 模型


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时加载模型
    logger.info("Loading model...")
    await load_model(_model_alias)
    logger.info("Model loaded successfully")

    yield

    # 关闭时清理
    logger.info("Shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title="PIU Risk Classification API",
    description="REST API for Problematic Internet Use (PIU) risk classification",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def load_model(alias: str = "champion"):
    """加载模型"""
    global _model, _model_metadata, _model_alias

    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

        # 加载模型
        _model = get_model_by_alias("piu-risk", alias)

        # 加载元数据
        _model_metadata = get_model_metadata("piu-risk", alias)

        _model_alias = alias

        logger.info(f"Model loaded: piu-risk@{alias}")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        _model = None
        _model_metadata = None
        raise


def prepare_features(request: PredictionRequest) -> np.ndarray:
    """
    从请求中准备特征向量

    注意：这是一个简化版本，实际需要根据训练时的特征工程来构建
    """
    features = []

    # 基本特征
    features.append(request.age)
    features.append(request.sex)

    # 可选特征
    features.append(request.bmi if request.bmi is not None else -1)
    features.append(request.height if request.height is not None else -1)
    features.append(request.weight if request.weight is not None else -1)
    features.append(request.cgas_score if request.cgas_score is not None else -1)

    # 如果有 actigraphy 特征，添加它们
    if request.actigraphy_features:
        for key in sorted(request.actigraphy_features.keys()):
            features.append(request.actigraphy_features[key])

    # 如果有其他特征，添加它们
    if request.additional_features:
        for key in sorted(request.additional_features.keys()):
            features.append(request.additional_features[key])

    # 转换为 numpy 数组
    return np.array([features])


@app.get("/", tags=["Root"])
async def root():
    """根端点"""
    return {
        "message": "PIU Risk Classification API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy" if _model is not None else "unhealthy",
        model_loaded=_model is not None,
        model_name=f"piu-risk@{_model_alias}" if _model is not None else None
    )


@app.get("/model_info", response_model=ModelInfo, tags=["Model"])
async def get_model_info():
    """获取模型信息"""
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if _model_metadata is None:
        raise HTTPException(status_code=500, detail="Model metadata not available")

    return ModelInfo(
        model_name="piu-risk",
        model_version=str(_model_metadata.get("version", "unknown")),
        model_alias=_model_alias,
        mlflow_run_id=_model_metadata.get("run_id", "unknown"),
        training_metrics=_model_metadata.get("metrics", {}),
        feature_version="v1",  # 需要从元数据中获取
        n_features=100  # 需要从元数据中获取
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    """预测端点"""
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 准备特征
        features = prepare_features(request)

        # 预测
        prediction = _model.predict(features)[0]
        probabilities = _model.predict_proba(features)[0].tolist()
        confidence = float(max(probabilities))

        # 映射到标签
        severity_labels = [SeverityLevel.NONE, SeverityLevel.MILD,
                          SeverityLevel.MODERATE, SeverityLevel.SEVERE]
        prediction_label = severity_labels[int(prediction)]

        return PredictionResponse(
            prediction=int(prediction),
            prediction_label=prediction_label,
            probabilities=probabilities,
            confidence=confidence
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/reload_model", tags=["Model"])
async def reload_model(alias: str = "champion"):
    """重新加载模型"""
    try:
        await load_model(alias)
        return {"message": f"Model reloaded: piu-risk@{alias}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
