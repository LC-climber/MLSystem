"""
Cross-Validation Runner

The single 5-fold CV loop shared by all three systems. Given a model factory
(a zero-arg callable returning a fresh BaseModel), it runs the same protocol for
every system → fair comparison (03_plan_p1_v2.md §5.4, §7).

Per fold it records model metrics (Macro-F1 / QWK / Balanced Accuracy / Log Loss)
and system metrics (train time, peak RSS, inference latency, model size), then
aggregates to mean ± std across folds.

Anti-leakage: the impute+scale pipeline is fit on the training fold only.
"""

import time
import tempfile
from pathlib import Path
from typing import Callable, Dict, Any
import numpy as np
import pandas as pd

from src.config import N_SPLITS, SEED
from src.data.constants import ID_COL, TARGET_COL
from src.data.feature_engineering import (
    make_preprocessing_pipeline,
    get_feature_matrix_columns,
)
from src.data.splits import get_fold_indices
from src.evaluation.metrics import compute_classification_metrics, summarize_cv_metrics
from src.models.base import BaseModel
from src.utils.logging import get_logger
from src.utils.reproducibility import set_seed
from src.utils.system_metrics import (
    get_peak_rss_gb,
    measure_inference_latency,
    get_model_size_mb,
)

logger = get_logger(__name__)


def _measure_model_size_mb(model: BaseModel) -> float:
    """Save model to a temp file and measure its serialized size; None if unsupported."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.bin"
            model.save(path)
            # PyTorch/Spark may save a directory; fall back to summing if needed
            if path.exists():
                return get_model_size_mb(path)
            return None
    except Exception:
        return None


def run_cv(
    model_factory: Callable[[], BaseModel],
    feat_df: pd.DataFrame,
    assignment: pd.DataFrame,
    n_splits: int = N_SPLITS,
    seed: int = SEED,
    preprocess: bool = True,
    measure_system: bool = True,
) -> Dict[str, Any]:
    """
    Run 5-fold CV for one model across all folds.

    Args:
        model_factory: Zero-arg callable returning a fresh BaseModel each fold
        feat_df: Feature DataFrame [id, sii, <features>] (may contain unlabeled rows)
        assignment: Fold assignment [id, sii, fold]
        n_splits: Number of folds
        seed: Random seed (re-applied each fold for reproducibility)
        preprocess: If True, fit impute+scale on train fold and transform
        measure_system: If True, collect system metrics (latency, size)

    Returns:
        {'model_name', 'per_fold': [...], 'summary': {...}}
    """
    # Restrict to labeled rows present in the assignment
    labeled_ids = set(assignment[ID_COL])
    feat_df = feat_df[feat_df[ID_COL].isin(labeled_ids)].reset_index(drop=True)

    feat_cols = get_feature_matrix_columns(feat_df)
    X_all = feat_df[feat_cols].to_numpy(dtype="float64")
    y_all = feat_df[TARGET_COL].astype(int).to_numpy()

    probe = model_factory()
    model_name = probe.name
    logger.info(f"[{model_name}] running {n_splits}-fold CV on {len(feat_df)} samples")

    per_fold = []
    for fold in range(n_splits):
        set_seed(seed)  # reproducibility per fold

        train_idx, val_idx = get_fold_indices(feat_df, assignment, fold)
        X_train, y_train = X_all[train_idx], y_all[train_idx]
        X_val, y_val = X_all[val_idx], y_all[val_idx]

        if preprocess:
            pre = make_preprocessing_pipeline()
            X_train = pre.fit_transform(X_train)
            X_val = pre.transform(X_val)

        # Train (timed)
        model = model_factory()
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_time_s = time.perf_counter() - t0

        # Predict + metrics
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)
        fold_metrics = compute_classification_metrics(y_val, y_pred, y_proba)

        # System metrics
        if measure_system:
            fold_metrics["train_time_s"] = train_time_s
            fold_metrics["peak_rss_gb"] = get_peak_rss_gb()
            try:
                fold_metrics["inference_latency_us"] = measure_inference_latency(
                    model.predict, X_val[:1], n_warmup=20, n_iterations=200
                )
            except Exception:
                fold_metrics["inference_latency_us"] = float("nan")
            size = _measure_model_size_mb(model)
            if size is not None:
                fold_metrics["model_size_mb"] = size

        per_fold.append(fold_metrics)
        logger.info(
            f"[{model_name}] fold {fold}: "
            f"macro_f1={fold_metrics['macro_f1']:.4f} "
            f"qwk={fold_metrics['qwk']:.4f} "
            f"train_time={train_time_s:.2f}s"
        )

    summary = summarize_cv_metrics(per_fold)
    logger.info(
        f"[{model_name}] CV done: "
        f"macro_f1={summary['macro_f1_mean']:.4f}±{summary['macro_f1_std']:.4f} "
        f"qwk={summary['qwk_mean']:.4f}±{summary['qwk_std']:.4f}"
    )

    return {"model_name": model_name, "per_fold": per_fold, "summary": summary}


def format_cv_row(result: Dict[str, Any]) -> str:
    """Format a CV result as one human-readable line (mean±std)."""
    s = result["summary"]
    return (
        f"{result['model_name']:18s} "
        f"MacroF1={s['macro_f1_mean']:.3f}±{s['macro_f1_std']:.3f}  "
        f"QWK={s['qwk_mean']:.3f}±{s['qwk_std']:.3f}  "
        f"BalAcc={s['balanced_accuracy_mean']:.3f}±{s['balanced_accuracy_std']:.3f}  "
        f"train={s.get('train_time_s_mean', float('nan')):.2f}s"
    )
