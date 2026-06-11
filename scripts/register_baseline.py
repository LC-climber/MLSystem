#!/usr/bin/env python3
"""
注册 P1 Baseline 模型到 MLflow Registry

从 P1 实验结果中选择最佳模型并注册为 baseline。
"""

import sys
import mlflow
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import MLFLOW_TRACKING_URI, SEED, TARGET_CLASSES
from src.models.sklearn_baselines import SklearnLogisticRegression
from src.data.feature_engineering import load_feat_v1
from src.data.splits import load_fold_assignment
from src.data.constants import ID_COL, TARGET_COL
import numpy as np
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_and_register_baseline():
    """训练并注册 baseline 模型"""

    logger.info("="*70)
    logger.info("注册 P1 Baseline 模型")
    logger.info("="*70)

    # 设置 MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("piu-p2-mlops")

    # 加载数据
    logger.info("加载数据...")
    feat_df = load_feat_v1()
    fold_df = load_fold_assignment()

    # 去除 sii（如果存在）
    if TARGET_COL in feat_df.columns:
        feat_df = feat_df.drop(columns=[TARGET_COL])

    # 合并
    merged = fold_df.merge(feat_df, on=ID_COL, how='inner')

    # 提取特征和标签
    exclude_cols = [ID_COL, TARGET_COL, 'fold']
    feature_cols = [c for c in merged.columns if c not in exclude_cols]

    X = merged[feature_cols].values
    y = merged[TARGET_COL].values.astype(int)

    logger.info(f"数据形状: {X.shape}")
    logger.info(f"类别分布: {np.unique(y, return_counts=True)}")

    # 开始 MLflow run
    with mlflow.start_run(run_name="baseline-sklearn-lr"):
        logger.info("\n训练 Baseline 模型...")

        # 创建模型
        model = SklearnLogisticRegression(
            num_classes=len(TARGET_CLASSES),
            seed=SEED
        )

        # 训练（使用全部数据，因为这是 baseline）
        model.fit(X, y)

        # 评估（在训练集上）
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)

        # 计算指标
        from sklearn.metrics import cohen_kappa_score, f1_score, balanced_accuracy_score

        qwk = cohen_kappa_score(y, y_pred, weights='quadratic')
        macro_f1 = f1_score(y, y_pred, average='macro')
        balanced_acc = balanced_accuracy_score(y, y_pred)

        logger.info(f"\n性能指标:")
        logger.info(f"  QWK: {qwk:.4f}")
        logger.info(f"  Macro F1: {macro_f1:.4f}")
        logger.info(f"  Balanced Accuracy: {balanced_acc:.4f}")

        # 记录参数
        mlflow.log_params({
            "model_type": "sklearn",
            "algorithm": "logistic_regression",
            "feature_version": "v1",
            "n_features": X.shape[1],
            "n_samples": X.shape[0],
            "seed": SEED
        })

        # 记录指标
        mlflow.log_metrics({
            "qwk": qwk,
            "macro_f1": macro_f1,
            "balanced_accuracy": balanced_acc
        })

        # 记录模型
        logger.info("\n保存模型...")
        mlflow.sklearn.log_model(
            model.model,
            "model",
            registered_model_name="piu-risk"
        )

        run_id = mlflow.active_run().info.run_id
        logger.info(f"Run ID: {run_id}")

        # 注册为 baseline
        logger.info("\n注册为 baseline...")
        model_uri = f"runs:/{run_id}/model"

        client = mlflow.MlflowClient()

        # 获取最新版本
        versions = client.search_model_versions(f"name='piu-risk'")
        if versions:
            latest_version = max([int(v.version) for v in versions])

            # 设置 baseline 别名
            client.set_registered_model_alias(
                name="piu-risk",
                alias="baseline",
                version=str(latest_version)
            )

            logger.info(f"✓ 模型版本 {latest_version} 已设置为 baseline")

            # 更新描述
            client.update_model_version(
                name="piu-risk",
                version=str(latest_version),
                description=f"P1 Baseline: sklearn LR, QWK={qwk:.4f}"
            )

        logger.info("\n" + "="*70)
        logger.info("✓ Baseline 注册完成！")
        logger.info("="*70)
        logger.info(f"模型名称: piu-risk")
        logger.info(f"别名: baseline")
        logger.info(f"QWK: {qwk:.4f}")
        logger.info(f"Run ID: {run_id}")
        logger.info("="*70)

        return run_id


if __name__ == "__main__":
    try:
        run_id = train_and_register_baseline()
        print(f"\n✓ 成功！Run ID: {run_id}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n✗ 失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
