"""
Evaluation Metrics

Project-wide metric definitions (see 06_risk_and_eval_v2.md §2.4). All systems
(sklearn / Spark / PyTorch) and both projects report the SAME metrics computed the
SAME way, so cross-system tables are comparable.

- P1 primary: Macro-F1; secondary: QWK, Balanced Accuracy
- P2 primary: QWK;      secondary: Macro-F1, Log Loss
"""

import numpy as np
from typing import Optional, Dict
from sklearn.metrics import (
    f1_score,
    cohen_kappa_score,
    balanced_accuracy_score,
    log_loss,
)

from src.data.constants import TARGET_CLASSES


def compute_macro_f1(y_true, y_pred) -> float:
    """Macro-averaged F1 (P1 primary metric)."""
    return float(f1_score(y_true, y_pred, average="macro"))


def compute_qwk(y_true, y_pred) -> float:
    """Quadratic Weighted Kappa (P2 primary, Kaggle official metric)."""
    return float(cohen_kappa_score(y_true, y_pred, weights="quadratic"))


def compute_balanced_accuracy(y_true, y_pred) -> float:
    """Balanced accuracy (mean recall per class)."""
    return float(balanced_accuracy_score(y_true, y_pred))


def compute_log_loss(y_true, y_proba) -> float:
    """Multiclass log loss over the fixed label set (P2 secondary)."""
    return float(log_loss(y_true, y_proba, labels=TARGET_CLASSES))


def compute_classification_metrics(
    y_true,
    y_pred,
    y_proba: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Compute the full classification metric suite.

    Args:
        y_true: Ground-truth labels
        y_pred: Predicted labels
        y_proba: Optional predicted probabilities (n_samples, n_classes) for log loss

    Returns:
        Dict with macro_f1, qwk, balanced_accuracy, and (if y_proba) log_loss
    """
    metrics = {
        "macro_f1": compute_macro_f1(y_true, y_pred),
        "qwk": compute_qwk(y_true, y_pred),
        "balanced_accuracy": compute_balanced_accuracy(y_true, y_pred),
    }
    if y_proba is not None:
        metrics["log_loss"] = compute_log_loss(y_true, y_proba)
    return metrics


def summarize_cv_metrics(fold_metrics: list) -> Dict[str, float]:
    """
    Aggregate per-fold metrics into mean/std (report format: mean ± std, n=5).

    Args:
        fold_metrics: List of per-fold metric dicts

    Returns:
        Dict with <metric>_mean and <metric>_std for every metric key
    """
    if not fold_metrics:
        return {}

    keys = fold_metrics[0].keys()
    summary = {}
    for key in keys:
        values = [m[key] for m in fold_metrics if key in m]
        summary[f"{key}_mean"] = float(np.mean(values))
        summary[f"{key}_std"] = float(np.std(values))
    return summary
