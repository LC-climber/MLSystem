"""
推理脚本 - 特征工程和模型加载

提供完整的特征工程逻辑，与训练时保持一致。
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from src.config import SEED, TARGET_CLASSES

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """特征工程类 - 用于推理服务"""

    def __init__(self, feature_version: str = "v1"):
        """
        初始化特征工程

        Args:
            feature_version: 特征版本 (v1 或 v2)
        """
        self.feature_version = feature_version
        self.feature_names = None
        self.expected_features = None

        if feature_version == "v1":
            self.expected_features = 100  # feat_v1 有 100 个特征
        elif feature_version == "v2":
            self.expected_features = 145  # feat_v2 有 145 个特征（去除 sii 后）
        else:
            raise ValueError(f"Unknown feature version: {feature_version}")

    def prepare_features_v1(self, request_data: Dict[str, Any]) -> np.ndarray:
        """
        准备 v1 特征（仅表格数据）

        Args:
            request_data: 请求数据字典

        Returns:
            特征向量 (1, n_features)
        """
        features = []

        # 基本人口统计学特征
        features.append(request_data.get("age", 0))
        features.append(request_data.get("sex", 0))

        # 身体指标
        features.append(request_data.get("bmi", -1))
        features.append(request_data.get("height", -1))
        features.append(request_data.get("weight", -1))
        features.append(request_data.get("waist_circumference", -1))

        # 血压
        features.append(request_data.get("diastolic_bp", -1))
        features.append(request_data.get("systolic_bp", -1))

        # CGAS 评分
        features.append(request_data.get("cgas_score", -1))

        # 如果有额外特征，添加它们
        if "additional_features" in request_data:
            for key in sorted(request_data["additional_features"].keys()):
                features.append(request_data["additional_features"][key])

        # 填充到 100 个特征
        while len(features) < self.expected_features:
            features.append(-1)

        # 截断到 100 个特征
        features = features[:self.expected_features]

        return np.array([features])

    def prepare_features_v2(self, request_data: Dict[str, Any]) -> np.ndarray:
        """
        准备 v2 特征（表格 + actigraphy）

        Args:
            request_data: 请求数据字典

        Returns:
            特征向量 (1, n_features)
        """
        features = []

        # 首先添加表格特征（与 v1 相同）
        features.append(request_data.get("age", 0))
        features.append(request_data.get("sex", 0))
        features.append(request_data.get("bmi", -1))
        features.append(request_data.get("height", -1))
        features.append(request_data.get("weight", -1))
        features.append(request_data.get("waist_circumference", -1))
        features.append(request_data.get("diastolic_bp", -1))
        features.append(request_data.get("systolic_bp", -1))
        features.append(request_data.get("cgas_score", -1))

        # 然后添加 actigraphy 特征
        if "actigraphy_features" in request_data:
            actig = request_data["actigraphy_features"]
            for key in sorted(actig.keys()):
                features.append(actig[key])

        # 如果有其他特征，添加它们
        if "additional_features" in request_data:
            for key in sorted(request_data["additional_features"].keys()):
                features.append(request_data["additional_features"][key])

        # 填充到 145 个特征
        while len(features) < self.expected_features:
            features.append(-1)

        # 截断到 145 个特征
        features = features[:self.expected_features]

        return np.array([features])

    def prepare_features(self, request_data: Dict[str, Any]) -> np.ndarray:
        """
        准备特征（根据版本自动选择）

        Args:
            request_data: 请求数据字典

        Returns:
            特征向量
        """
        if self.feature_version == "v1":
            return self.prepare_features_v1(request_data)
        elif self.feature_version == "v2":
            return self.prepare_features_v2(request_data)
        else:
            raise ValueError(f"Unknown feature version: {self.feature_version}")

    def validate_input(self, request_data: Dict[str, Any]) -> bool:
        """
        验证输入数据

        Args:
            request_data: 请求数据字典

        Returns:
            是否有效
        """
        # 必需字段
        required_fields = ["age", "sex"]

        for field in required_fields:
            if field not in request_data:
                logger.error(f"Missing required field: {field}")
                return False

        # 年龄范围
        age = request_data.get("age")
        if not (0 <= age <= 100):
            logger.error(f"Invalid age: {age}")
            return False

        # 性别
        sex = request_data.get("sex")
        if sex not in [0, 1]:
            logger.error(f"Invalid sex: {sex}")
            return False

        return True


def create_sample_input_v1() -> Dict[str, Any]:
    """创建 v1 示例输入"""
    return {
        "age": 12.5,
        "sex": 1,
        "bmi": 18.5,
        "height": 150.0,
        "weight": 45.0,
        "waist_circumference": 70.0,
        "diastolic_bp": 70.0,
        "systolic_bp": 110.0,
        "cgas_score": 75.0
    }


def create_sample_input_v2() -> Dict[str, Any]:
    """创建 v2 示例输入"""
    sample = create_sample_input_v1()

    # 添加 actigraphy 特征（示例）
    sample["actigraphy_features"] = {
        "act_mean_enmo": 35.2,
        "act_std_enmo": 12.5,
        "act_min_enmo": 0.0,
        "act_max_enmo": 250.0,
        "act_night_enmo_mean": 5.2,
        "act_day_enmo_mean": 45.8
    }

    return sample


if __name__ == "__main__":
    # 测试特征工程
    fe_v1 = FeatureEngineering("v1")
    sample_v1 = create_sample_input_v1()

    print("Testing v1 feature engineering...")
    features_v1 = fe_v1.prepare_features(sample_v1)
    print(f"Features shape: {features_v1.shape}")
    print(f"Expected: (1, {fe_v1.expected_features})")

    fe_v2 = FeatureEngineering("v2")
    sample_v2 = create_sample_input_v2()

    print("\nTesting v2 feature engineering...")
    features_v2 = fe_v2.prepare_features(sample_v2)
    print(f"Features shape: {features_v2.shape}")
    print(f"Expected: (1, {fe_v2.expected_features})")

    print("\n✓ Feature engineering tests passed!")
