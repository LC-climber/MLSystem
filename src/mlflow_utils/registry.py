"""
MLflow Model Registry 管理工具

提供模型注册、别名管理和模型加载功能。
"""

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry import ModelVersion
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# 默认模型名称
DEFAULT_MODEL_NAME = "piu-risk"

# 支持的别名
VALID_ALIASES = ["baseline", "candidate", "champion", "demo"]


def init_registry(model_name: str = DEFAULT_MODEL_NAME) -> None:
    """
    初始化 Model Registry（创建注册模型条目）

    Args:
        model_name: 注册模型名称
    """
    client = MlflowClient()

    try:
        # 尝试获取已有模型
        client.get_registered_model(model_name)
        logger.info(f"Model '{model_name}' already exists in registry")
    except mlflow.exceptions.RestException:
        # 模型不存在，创建新的
        client.create_registered_model(
            model_name,
            description="PIU (Problematic Internet Use) risk classification model"
        )
        logger.info(f"Created registered model '{model_name}'")


def register_model(
    run_id: str,
    model_name: str = DEFAULT_MODEL_NAME,
    alias: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    description: Optional[str] = None,
) -> ModelVersion:
    """
    注册模型到 MLflow Model Registry

    Args:
        run_id: MLflow run ID
        model_name: 注册模型名称
        alias: 可选的别名（baseline/candidate/champion/demo）
        tags: 附加标签
        description: 版本描述

    Returns:
        ModelVersion 对象
    """
    client = MlflowClient()

    # 确保 registry 存在
    init_registry(model_name)

    # 构建 model URI
    model_uri = f"runs:/{run_id}/model"

    # 注册模型
    model_version = mlflow.register_model(model_uri, model_name)

    logger.info(
        f"Registered model '{model_name}' version {model_version.version} "
        f"from run {run_id}"
    )

    # 添加描述
    if description:
        client.update_model_version(
            name=model_name,
            version=model_version.version,
            description=description
        )

    # 添加标签
    if tags:
        for key, value in tags.items():
            client.set_model_version_tag(
                name=model_name,
                version=model_version.version,
                key=key,
                value=str(value)
            )

    # 设置别名（如果提供）
    if alias:
        set_alias(model_name, model_version.version, alias)

    return model_version


def set_alias(
    model_name: str,
    version: int,
    alias: str,
) -> None:
    """
    设置或更新模型别名

    Args:
        model_name: 注册模型名称
        version: 模型版本号
        alias: 别名（baseline/candidate/champion/demo）
    """
    if alias not in VALID_ALIASES:
        raise ValueError(
            f"Invalid alias '{alias}'. Must be one of {VALID_ALIASES}"
        )

    client = MlflowClient()

    # 设置别名
    client.set_registered_model_alias(
        name=model_name,
        alias=alias,
        version=version
    )

    logger.info(f"Set alias '{alias}' for model '{model_name}' version {version}")


def get_model_by_alias(
    model_name: str,
    alias: str,
) -> mlflow.pyfunc.PyFuncModel:
    """
    按别名加载模型

    Args:
        model_name: 注册模型名称
        alias: 别名（baseline/candidate/champion/demo）

    Returns:
        加载的模型（MLflow PyFunc 格式）
    """
    if alias not in VALID_ALIASES:
        raise ValueError(
            f"Invalid alias '{alias}'. Must be one of {VALID_ALIASES}"
        )

    model_uri = f"models:/{model_name}@{alias}"

    try:
        model = mlflow.pyfunc.load_model(model_uri)
        logger.info(f"Loaded model '{model_name}' with alias '{alias}'")
        return model
    except Exception as e:
        logger.error(f"Failed to load model with alias '{alias}': {e}")
        raise


def get_model_by_version(
    model_name: str,
    version: int,
) -> mlflow.pyfunc.PyFuncModel:
    """
    按版本号加载模型

    Args:
        model_name: 注册模型名称
        version: 模型版本号

    Returns:
        加载的模型（MLflow PyFunc 格式）
    """
    model_uri = f"models:/{model_name}/{version}"

    try:
        model = mlflow.pyfunc.load_model(model_uri)
        logger.info(f"Loaded model '{model_name}' version {version}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model version {version}: {e}")
        raise


def list_models_by_tag(
    model_name: str,
    tag_key: str,
    tag_value: Optional[str] = None,
) -> List[ModelVersion]:
    """
    按标签筛选模型版本

    Args:
        model_name: 注册模型名称
        tag_key: 标签键
        tag_value: 标签值（可选，如果为 None 则返回所有包含该键的版本）

    Returns:
        符合条件的 ModelVersion 列表
    """
    client = MlflowClient()

    try:
        # 获取所有版本
        versions = client.search_model_versions(f"name='{model_name}'")

        # 筛选
        matching_versions = []
        for version in versions:
            if tag_key in version.tags:
                if tag_value is None or version.tags[tag_key] == tag_value:
                    matching_versions.append(version)

        logger.info(
            f"Found {len(matching_versions)} versions with tag {tag_key}={tag_value}"
        )
        return matching_versions

    except Exception as e:
        logger.error(f"Failed to list models by tag: {e}")
        raise


def promote_model(
    model_name: str,
    from_alias: str,
    to_alias: str,
) -> None:
    """
    模型晋升（例如 candidate → champion）

    Args:
        model_name: 注册模型名称
        from_alias: 源别名
        to_alias: 目标别名
    """
    client = MlflowClient()

    # 获取源别名对应的版本
    try:
        model_version = client.get_model_version_by_alias(model_name, from_alias)
        version = model_version.version

        # 设置新别名
        set_alias(model_name, version, to_alias)

        logger.info(
            f"Promoted model '{model_name}' version {version} "
            f"from '{from_alias}' to '{to_alias}'"
        )
    except Exception as e:
        logger.error(f"Failed to promote model: {e}")
        raise


def get_alias_info(model_name: str) -> Dict[str, Optional[int]]:
    """
    获取所有别名的当前指向版本

    Args:
        model_name: 注册模型名称

    Returns:
        别名 -> 版本号映射字典
    """
    client = MlflowClient()
    alias_info = {}

    for alias in VALID_ALIASES:
        try:
            model_version = client.get_model_version_by_alias(model_name, alias)
            alias_info[alias] = model_version.version
        except mlflow.exceptions.RestException:
            # 别名不存在
            alias_info[alias] = None

    return alias_info


def get_model_metadata(
    model_name: str,
    alias: str,
) -> Dict:
    """
    获取模型元数据（包括训练时的参数和指标）

    Args:
        model_name: 注册模型名称
        alias: 别名

    Returns:
        包含 run_id、params、metrics、tags 的字典
    """
    client = MlflowClient()

    # 获取模型版本
    model_version = client.get_model_version_by_alias(model_name, alias)
    run_id = model_version.run_id

    # 获取 run 详情
    run = client.get_run(run_id)

    return {
        "run_id": run_id,
        "version": model_version.version,
        "params": run.data.params,
        "metrics": run.data.metrics,
        "tags": run.data.tags,
        "model_uri": f"models:/{model_name}@{alias}",
    }
