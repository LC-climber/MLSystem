"""
MLflow 增强追踪工具

提供统一的实验追踪接口，自动记录模型指标、可视化和元数据。
"""

import mlflow
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import os

from src.evaluation.metrics import (
    macro_f1_score,
    quadratic_weighted_kappa,
    balanced_accuracy_score,
)


def log_experiment(
    experiment_name: str,
    run_name: str,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    tags: Optional[Dict[str, str]] = None,
    artifacts: Optional[Dict[str, str]] = None,
) -> str:
    """
    统一的实验记录接口

    Args:
        experiment_name: MLflow experiment 名称
        run_name: Run 显示名称
        params: 超参数字典
        metrics: 指标字典
        tags: 标签字典
        artifacts: 要记录的 artifact 文件路径 {artifact_name: file_path}

    Returns:
        run_id: MLflow run ID
    """
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=run_name) as run:
        # 记录参数
        for key, value in params.items():
            mlflow.log_param(key, value)

        # 记录指标
        for key, value in metrics.items():
            mlflow.log_metric(key, value)

        # 记录标签
        if tags:
            mlflow.set_tags(tags)

        # 记录 artifacts
        if artifacts:
            for artifact_name, file_path in artifacts.items():
                if Path(file_path).exists():
                    mlflow.log_artifact(file_path, artifact_path=artifact_name)

        return run.info.run_id


def log_cv_results(
    y_true_per_fold: List[np.ndarray],
    y_pred_per_fold: List[np.ndarray],
    y_proba_per_fold: List[np.ndarray],
    fold_metrics: List[Dict[str, float]],
    prefix: str = "cv",
) -> Dict[str, float]:
    """
    记录交叉验证结果

    Args:
        y_true_per_fold: 每个 fold 的真实标签
        y_pred_per_fold: 每个 fold 的预测标签
        y_proba_per_fold: 每个 fold 的预测概率
        fold_metrics: 每个 fold 的指标字典列表
        prefix: 指标前缀

    Returns:
        汇总指标字典
    """
    n_folds = len(fold_metrics)

    # 汇总每个指标的均值和标准差
    summary_metrics = {}

    if fold_metrics:
        metric_names = fold_metrics[0].keys()
        for metric_name in metric_names:
            values = [fold[metric_name] for fold in fold_metrics]
            mean_val = np.mean(values)
            std_val = np.std(values)

            summary_metrics[f"{prefix}_{metric_name}_mean"] = mean_val
            summary_metrics[f"{prefix}_{metric_name}_std"] = std_val

            # 记录到 MLflow
            mlflow.log_metric(f"{prefix}_{metric_name}_mean", mean_val)
            mlflow.log_metric(f"{prefix}_{metric_name}_std", std_val)

    # 记录每个 fold 的指标
    for i, fold_metric in enumerate(fold_metrics):
        for metric_name, value in fold_metric.items():
            mlflow.log_metric(f"{prefix}_fold{i}_{metric_name}", value)

    return summary_metrics


def log_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: Optional[List[str]] = None,
    normalize: bool = False,
    title: str = "Confusion Matrix",
    artifact_path: str = "confusion_matrix.png",
) -> str:
    """
    记录混淆矩阵可视化

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        classes: 类别名称列表
        normalize: 是否归一化
        title: 图表标题
        artifact_path: Artifact 保存路径

    Returns:
        临时文件路径
    """
    from sklearn.metrics import confusion_matrix

    # 计算混淆矩阵
    cm = confusion_matrix(y_true, y_pred)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    # 绘制
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt='.2f' if normalize else 'd',
        cmap='Blues',
        xticklabels=classes if classes else range(cm.shape[1]),
        yticklabels=classes if classes else range(cm.shape[0]),
        cbar_kws={'label': 'Proportion' if normalize else 'Count'}
    )
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()

    # 保存到临时文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, artifact_path)
    plt.savefig(temp_path, dpi=150, bbox_inches='tight')
    plt.close()

    # 记录到 MLflow
    mlflow.log_artifact(temp_path, artifact_path=os.path.dirname(artifact_path) or ".")

    return temp_path


def log_feature_importance(
    feature_names: List[str],
    importances: np.ndarray,
    top_k: int = 20,
    title: str = "Feature Importance",
    artifact_path: str = "feature_importance.png",
) -> str:
    """
    记录特征重要性可视化

    Args:
        feature_names: 特征名称列表
        importances: 特征重要性数组
        top_k: 显示 top-k 重要特征
        title: 图表标题
        artifact_path: Artifact 保存路径

    Returns:
        临时文件路径
    """
    # 排序并取 top-k
    indices = np.argsort(importances)[::-1][:top_k]
    top_features = [feature_names[i] for i in indices]
    top_importances = importances[indices]

    # 绘制
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(top_features)), top_importances)
    plt.yticks(range(len(top_features)), top_features)
    plt.xlabel('Importance')
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()

    # 保存到临时文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, artifact_path)
    plt.savefig(temp_path, dpi=150, bbox_inches='tight')
    plt.close()

    # 记录到 MLflow
    mlflow.log_artifact(temp_path, artifact_path=os.path.dirname(artifact_path) or ".")

    return temp_path


def log_training_curve(
    train_losses: List[float],
    val_losses: Optional[List[float]] = None,
    train_metrics: Optional[List[float]] = None,
    val_metrics: Optional[List[float]] = None,
    metric_name: str = "QWK",
    artifact_path: str = "training_curve.png",
) -> str:
    """
    记录训练曲线

    Args:
        train_losses: 训练损失列表（每个 epoch）
        val_losses: 验证损失列表（可选）
        train_metrics: 训练指标列表（可选）
        val_metrics: 验证指标列表（可选）
        metric_name: 指标名称
        artifact_path: Artifact 保存路径

    Returns:
        临时文件路径
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Loss 曲线
    epochs = range(1, len(train_losses) + 1)
    axes[0].plot(epochs, train_losses, 'b-', label='Train Loss')
    if val_losses:
        axes[0].plot(epochs, val_losses, 'r-', label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Metric 曲线
    if train_metrics:
        axes[1].plot(epochs, train_metrics, 'b-', label=f'Train {metric_name}')
    if val_metrics:
        axes[1].plot(epochs, val_metrics, 'r-', label=f'Val {metric_name}')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel(metric_name)
    axes[1].set_title(f'Training and Validation {metric_name}')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存到临时文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, artifact_path)
    plt.savefig(temp_path, dpi=150, bbox_inches='tight')
    plt.close()

    # 记录到 MLflow
    mlflow.log_artifact(temp_path, artifact_path=os.path.dirname(artifact_path) or ".")

    return temp_path


def log_pr_curve(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    class_names: Optional[List[str]] = None,
    artifact_path: str = "pr_curve.png",
) -> str:
    """
    记录 Precision-Recall 曲线（多分类，每个类别一条曲线）

    Args:
        y_true: 真实标签（整数）
        y_proba: 预测概率矩阵 (n_samples, n_classes)
        class_names: 类别名称列表
        artifact_path: Artifact 保存路径

    Returns:
        临时文件路径
    """
    from sklearn.preprocessing import label_binarize
    from sklearn.metrics import precision_recall_curve, average_precision_score

    n_classes = y_proba.shape[1]

    # 转换为 one-hot
    y_true_bin = label_binarize(y_true, classes=range(n_classes))

    # 绘制每个类别的 PR 曲线
    plt.figure(figsize=(10, 8))

    for i in range(n_classes):
        precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_proba[:, i])
        ap = average_precision_score(y_true_bin[:, i], y_proba[:, i])

        label_name = class_names[i] if class_names else f"Class {i}"
        plt.plot(recall, precision, label=f'{label_name} (AP={ap:.3f})')

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve (One-vs-Rest)')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # 保存到临时文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, artifact_path)
    plt.savefig(temp_path, dpi=150, bbox_inches='tight')
    plt.close()

    # 记录到 MLflow
    mlflow.log_artifact(temp_path, artifact_path=os.path.dirname(artifact_path) or ".")

    return temp_path


# 设置 Matplotlib 配置目录为临时目录（避免权限问题）
os.environ.setdefault('MPLCONFIGDIR', '/tmp/mlsystem-matplotlib')
