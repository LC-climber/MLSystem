"""
P2 Optuna 超参数优化实验

使用 Optuna 对 PyTorch MLP 进行超参数搜索，所有 trials 自动记录到 MLflow。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import numpy as np
import mlflow
import optuna
from optuna.pruners import MedianPruner
import logging
from typing import Dict, Any

import pandas as pd
from src.data.feature_engineering import load_feat_v1, load_feat_v2
from src.data.splits import load_fold_assignment
from src.training.cv import run_cv
from src.models.configurable_torch_mlp import ConfigurableTorchMLP  # 使用可配置版本
from src.config import MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_P2, SEED, TARGET_CLASSES
from src.data.constants import ID_COL, TARGET_COL
from src.mlflow_utils.registry import register_model

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def objective(
    trial: optuna.Trial,
    X: np.ndarray,
    y: np.ndarray,
    fold_df,
    feature_version: str,
    n_folds: int = 5,
) -> float:
    """
    Optuna 优化目标函数

    Args:
        trial: Optuna trial 对象
        X: 特征矩阵
        y: 标签向量
        fold_df: Fold 分配 DataFrame
        feature_version: 特征版本
        n_folds: CV 折数

    Returns:
        目标指标值 (QWK mean)
    """
    # 定义搜索空间
    hidden_dim_1 = trial.suggest_categorical("hidden_dim_1", [64, 128, 256, 512])
    hidden_dim_2 = trial.suggest_categorical("hidden_dim_2", [32, 64, 128, 256])
    dropout = trial.suggest_float("dropout", 0.0, 0.5, step=0.1)
    lr = trial.suggest_float("lr", 1e-4, 1e-2, log=True)
    weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True)
    batch_size = trial.suggest_categorical("batch_size", [64, 128, 256, 512])

    # 固定参数
    max_epochs = 100
    patience = 10

    # 创建模型实例
    num_classes = len(TARGET_CLASSES)
    model = ConfigurableTorchMLP(
        num_classes=num_classes,
        hidden_dim_1=hidden_dim_1,
        hidden_dim_2=hidden_dim_2,
        dropout=dropout,
        learning_rate=lr,
        weight_decay=weight_decay,
        batch_size=batch_size,
        max_epochs=max_epochs,
        patience=patience,
        device="cuda",
        seed=SEED,
    )

    # 启动 MLflow run
    with mlflow.start_run(nested=True, run_name=f"trial_{trial.number}"):
        # 记录超参数
        mlflow.log_params(trial.params)
        mlflow.log_params({
            "trial_number": trial.number,
            "feature_version": feature_version,
            "model_type": "pytorch_mlp",
            "max_epochs": max_epochs,
            "patience": patience,
        })
        mlflow.set_tag("optuna_study", trial.study.study_name)

        try:
            # 运行 CV（使用 P1 的 run_cv 接口）
            results = run_cv(
                model_factory=lambda: model,
                feat_df=merged,
                assignment=merged[[ID_COL, 'fold', TARGET_COL]],
                n_splits=n_folds,
                seed=SEED,
                preprocess=False,  # 数据已经预处理
                measure_system=False,  # 减少开销
            )

            # 提取 QWK mean
            qwk_mean = results["cv_metrics"]["qwk_mean"]
            qwk_std = results["cv_metrics"]["qwk_std"]

            # 记录指标
            mlflow.log_metric("val_qwk_mean", qwk_mean)
            mlflow.log_metric("val_qwk_std", qwk_std)
            mlflow.log_metric("val_macro_f1_mean", results["cv_metrics"]["macro_f1_mean"])
            mlflow.log_metric("val_balanced_accuracy_mean", results["cv_metrics"]["balanced_accuracy_mean"])

            logger.info(f"Trial {trial.number}: QWK = {qwk_mean:.4f} ± {qwk_std:.4f}")

            # 中间值报告（用于 pruning）
            trial.report(qwk_mean, step=0)

            # 检查是否应该剪枝
            if trial.should_prune():
                raise optuna.TrialPruned()

            return qwk_mean

        except Exception as e:
            logger.error(f"Trial {trial.number} failed: {e}")
            raise


def run_optuna_optimization(
    feature_version: str = "v2",
    n_trials: int = 100,
    study_name: str = "piu-mlp-optimization",
    n_folds: int = 5,
    timeout: int = None,
) -> optuna.Study:
    """
    运行 Optuna 超参数优化

    Args:
        feature_version: 特征版本 (v1/v2/v3)
        n_trials: 试验次数
        study_name: Study 名称
        n_folds: CV 折数
        timeout: 超时时间（秒）

    Returns:
        完成的 Optuna Study
    """
    logger.info(f"Starting Optuna optimization: {n_trials} trials")
    logger.info(f"Feature version: {feature_version}")
    logger.info(f"Study name: {study_name}")

    # 设置 MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_P2)

    # 加载数据
    logger.info("Loading data...")

    # 根据 feature version 加载对应的特征
    if feature_version == "v1":
        feat_df = load_feat_v1()
    elif feature_version == "v2":
        feat_df = load_feat_v2()
    else:
        raise ValueError(f"Unknown feature version: {feature_version}")

    # 加载 fold 分配（包含 id, sii, fold）
    fold_df = load_fold_assignment()

    # feat_df 可能包含 sii 列，需要删除以避免重复
    if TARGET_COL in feat_df.columns:
        feat_df = feat_df.drop(columns=[TARGET_COL])

    # 合并：fold_df 提供标签和 fold，feat_df 提供特征
    merged = fold_df.merge(feat_df, on=ID_COL, how='inner')

    # 提取特征和标签
    exclude_cols = [ID_COL, TARGET_COL, 'fold']
    feature_cols = [c for c in merged.columns if c not in exclude_cols]

    X_all = merged[feature_cols].values
    y_all = merged[TARGET_COL].values.astype(int)

    logger.info(f"Data shape: {X_all.shape}")
    logger.info(f"Classes: {np.unique(y_all)}")

    # 创建 Optuna study
    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",  # 最大化 QWK
        pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=0),
        storage=f"sqlite:///{project_root}/optuna.db",
        load_if_exists=True,
    )

    logger.info(f"Study storage: sqlite:///{project_root}/optuna.db")

    # 启动父 MLflow run
    with mlflow.start_run(run_name=f"optuna_{study_name}"):
        mlflow.log_params({
            "study_name": study_name,
            "n_trials": n_trials,
            "feature_version": feature_version,
            "n_folds": n_folds,
        })

        # 运行优化
        study.optimize(
            lambda trial: objective(
                trial,
                X=X_all,
                y=y_all,
                fold_df=fold_df,
                feature_version=feature_version,
                n_folds=n_folds,
            ),
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True,
        )

        # 记录最佳结果
        best_trial = study.best_trial
        logger.info(f"\nBest trial: {best_trial.number}")
        logger.info(f"  QWK: {best_trial.value:.4f}")
        logger.info(f"  Params: {best_trial.params}")

        mlflow.log_params({f"best_{k}": v for k, v in best_trial.params.items()})
        mlflow.log_metric("best_qwk", best_trial.value)

    return study


def main():
    parser = argparse.ArgumentParser(description="Run Optuna hyperparameter optimization")
    parser.add_argument(
        "--feature",
        type=str,
        default="v2",
        choices=["v1", "v2", "v3"],
        help="Feature version"
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=100,
        help="Number of Optuna trials"
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default="piu-mlp-optimization",
        help="Optuna study name"
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=5,
        help="Number of CV folds"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds"
    )

    args = parser.parse_args()

    # 运行优化
    study = run_optuna_optimization(
        feature_version=args.feature,
        n_trials=args.trials,
        study_name=args.study_name,
        n_folds=args.folds,
        timeout=args.timeout,
    )

    # 打印总结
    logger.info("\n" + "="*60)
    logger.info("OPTIMIZATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Number of finished trials: {len(study.trials)}")
    logger.info(f"Best trial: {study.best_trial.number}")
    logger.info(f"Best QWK: {study.best_value:.4f}")
    logger.info(f"Best params:")
    for key, value in study.best_trial.params.items():
        logger.info(f"  {key}: {value}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
