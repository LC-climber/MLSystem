"""
End-to-End Pipeline Smoke Test

Verifies the W2 data pipeline is wired correctly by training one sklearn Logistic
Regression on fold 0 of feat_v1 and reporting metrics. This is NOT the formal
experiment (that's src/experiments/run_p1_systemwise.py) — it just proves:

  feat_v1 + splits + per-fold anti-leakage preprocessing + LR + metrics

all connect and produce sane numbers.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.config import SEED
from src.data.constants import ID_COL, TARGET_COL
from src.data.feature_engineering import (
    load_feat_v1,
    make_preprocessing_pipeline,
    get_feature_matrix_columns,
)
from src.data.splits import load_fold_assignment, get_fold_indices
from src.evaluation.metrics import compute_classification_metrics
from src.utils.logging import get_logger
from src.utils.reproducibility import set_seed

logger = get_logger(__name__)


def test_pipeline_smoke():
    set_seed(SEED)
    logger.info("=" * 60)
    logger.info("End-to-End Pipeline Smoke Test (fold 0, sklearn LR)")
    logger.info("=" * 60)

    try:
        # 1. Load feat_v1 and split assignment
        feat = load_feat_v1()
        assignment = load_fold_assignment()

        # 2. Keep only labeled rows (those present in the split assignment)
        labeled_ids = set(assignment[ID_COL])
        feat = feat[feat[ID_COL].isin(labeled_ids)].reset_index(drop=True)
        logger.info(f"feat_v1 (labeled): {feat.shape}")

        # 3. Fold 0 train/val split
        train_idx, val_idx = get_fold_indices(feat, assignment, fold=0)
        logger.info(f"Fold 0: train={len(train_idx)}, val={len(val_idx)}")

        feat_cols = get_feature_matrix_columns(feat)
        X = feat[feat_cols].to_numpy()
        y = feat[TARGET_COL].astype(int).to_numpy()

        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        # 4. Per-fold anti-leakage preprocessing (fit on train only)
        pre = make_preprocessing_pipeline()
        X_train_p = pre.fit_transform(X_train)
        X_val_p = pre.transform(X_val)
        assert not np.isnan(X_train_p).any(), "NaN remains after imputation (train)"
        assert not np.isnan(X_val_p).any(), "NaN remains after imputation (val)"

        # 5. Train LR (class_weight balanced per §5.4)
        clf = LogisticRegression(
            max_iter=1000, C=1.0, class_weight="balanced", random_state=SEED
        )
        clf.fit(X_train_p, y_train)

        # 6. Predict + metrics
        y_pred = clf.predict(X_val_p)
        y_proba = clf.predict_proba(X_val_p)
        metrics = compute_classification_metrics(y_val, y_pred, y_proba)

        logger.info("Fold 0 validation metrics:")
        for k, v in metrics.items():
            logger.info(f"  {k:20s}: {v:.4f}")

        # 7. Sanity assertions
        assert 0.0 <= metrics["macro_f1"] <= 1.0
        assert -1.0 <= metrics["qwk"] <= 1.0
        # A trivial-but-real signal: should beat random (4-class) macro-F1 ~0.25
        assert metrics["macro_f1"] > 0.20, "macro_f1 suspiciously low"

        logger.info("=" * 60)
        logger.info("✅ Pipeline smoke test passed!")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"❌ Smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    sys.exit(0 if test_pipeline_smoke() else 1)
