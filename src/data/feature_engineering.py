"""
Feature Engineering

Builds the project's tabular feature versions. This module owns `feat_v1_tabular`
(see 03_plan_p1_v2.md §5.2). Actigraphy-based features (`feat_v2_biosensing`) live
in preprocess_actigraphy_{pandas,spark}.py; fusion (`feat_v3_fusion`) is assembled
downstream.

Design note (anti-leakage, see §10.2): feat_v1 only applies transforms that do NOT
depend on training-set statistics — namely one-hot encoding of categorical (Season)
columns. Missing-value imputation and scaling are deliberately DEFERRED to a
per-fold sklearn Pipeline (see make_preprocessing_pipeline) so the imputer/scaler is
fit on the training fold only. This also enables ablations A1 (imputer) and A2
(scaling) without regenerating features.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.config import SEED, DATA_PROCESSED_DIR, IMPUTATION_STRATEGY, SCALER_TYPE
from src.data.actigraphy_features import FEAT_V2_CPU_FILE
from src.data.constants import ID_COL, TARGET_COL
from src.data.loader import load_train_data, get_feature_columns
from src.utils.logging import get_logger
from src.utils.io import write_parquet, read_parquet

logger = get_logger(__name__)

# Canonical feat_v1 file (name fixed by 03_plan_p1_v2.md §5.2)
FEAT_V1_FILE = DATA_PROCESSED_DIR / "feat_v1__seed42.parquet"


def build_feat_v1(df: pd.DataFrame, dummy_na: bool = True) -> pd.DataFrame:
    """
    Build feat_v1_tabular: tabular-only features with categorical one-hot encoding.

    Leakage columns (PCIAT-*) are excluded via get_feature_columns. Numeric columns
    keep their NaNs (imputation deferred to per-fold pipeline). Categorical Season
    columns are one-hot encoded (no train-set statistics involved).

    Args:
        df: Raw tabular DataFrame (train.csv)
        dummy_na: If True, add an explicit indicator column for missing categoricals

    Returns:
        DataFrame [id, sii, <numeric features...>, <one-hot features...>]
    """
    feature_cols = get_feature_columns(df, is_train=True)
    X = df[feature_cols].copy()

    str_cols = X.select_dtypes(include=["object"]).columns.tolist()
    logger.info(f"feat_v1: one-hot encoding {len(str_cols)} categorical columns")

    X = pd.get_dummies(X, columns=str_cols, dummy_na=dummy_na, dtype="float64")

    # Reattach id and target
    meta = df[[ID_COL, TARGET_COL]].reset_index(drop=True)
    out = pd.concat([meta, X.reset_index(drop=True)], axis=1)

    logger.info(
        f"feat_v1 built: {len(out)} rows x {out.shape[1]} cols "
        f"({len(feature_cols)} raw features -> {X.shape[1]} encoded features)"
    )
    return out


def make_preprocessing_pipeline(
    imputation_strategy: str = IMPUTATION_STRATEGY,
    scaler_type: str = SCALER_TYPE,
) -> Pipeline:
    """
    Build a per-fold preprocessing pipeline (impute -> scale) for numeric matrices.

    Fit this on the TRAINING fold only, then transform train/val — this keeps the
    imputer/scaler statistics leakage-free. One-hot columns pass through unchanged
    (imputation on 0/1 is a no-op; scaling them is harmless and keeps it simple).

    Args:
        imputation_strategy: SimpleImputer strategy ("median", "mean", ...)
        scaler_type: "standard" (others can be added for ablations)

    Returns:
        Unfitted sklearn Pipeline
    """
    if scaler_type != "standard":
        raise NotImplementedError(f"scaler_type={scaler_type} not wired yet")

    return Pipeline([
        ("imputer", SimpleImputer(strategy=imputation_strategy)),
        ("scaler", StandardScaler()),
    ])


def get_feature_matrix_columns(feat_df: pd.DataFrame) -> list:
    """Return the feature column names (everything except id and target)."""
    return [c for c in feat_df.columns if c not in (ID_COL, TARGET_COL)]


def save_feat_v1(feat_df: pd.DataFrame, path: Path = FEAT_V1_FILE) -> None:
    """Persist feat_v1 to parquet."""
    write_parquet(feat_df, path)
    logger.info(f"Saved feat_v1 to {path}")


def load_feat_v1(path: Path = FEAT_V1_FILE) -> pd.DataFrame:
    """Load feat_v1 from parquet."""
    if not path.exists():
        raise FileNotFoundError(
            f"feat_v1 not found: {path}. Generate it: python -m src.data.feature_engineering"
        )
    return read_parquet(path)


def load_feat_v2(path: Path = FEAT_V2_CPU_FILE) -> pd.DataFrame:
    """Load canonical feat_v2 (CPU reference; Spark copy is equivalence-checked)."""
    if not path.exists():
        raise FileNotFoundError(
            f"feat_v2 not found: {path}. Generate it: "
            "python -m src.data.preprocess_actigraphy_pandas"
        )
    return read_parquet(path)


def main():
    """Generate and persist feat_v1__seed42.parquet."""
    df = load_train_data()
    feat_v1 = build_feat_v1(df)
    save_feat_v1(feat_v1)

    feat_cols = get_feature_matrix_columns(feat_v1)
    n_with_nan = int(feat_v1[feat_cols].isna().any(axis=0).sum())
    print(f"\n✅ feat_v1 written: {FEAT_V1_FILE}")
    print(f"   shape: {feat_v1.shape} ({len(feat_cols)} feature columns)")
    print(f"   {n_with_nan} columns still contain NaN (imputed per-fold at train time)")


if __name__ == "__main__":
    main()
