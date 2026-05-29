"""
Cross-Validation Splits

StratifiedGroupKFold(K=5) for the PIU dataset:
- stratify by `sii`, group by participant `id` (no participant leakage across folds)
- ONLY labeled samples (sii not NaN) are split; unlabeled samples (~31%) are
  excluded from supervised P1 experiments (they may be used semi-supervised in P2)
- persisted as a SINGLE file: data/splits/stratified_group_kfold_seed42.csv
  with columns [id, sii, fold], where `fold` is the validation-fold index (0..K-1)

This file format is the project-wide contract (see 03_plan_p1_v2.md §5.1,
06_risk_and_eval_v2.md §2.3): every model in every system reads the same file.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple
from sklearn.model_selection import StratifiedGroupKFold
from src.config import N_SPLITS, SEED, DATA_SPLITS_DIR
from src.data.constants import ID_COL, TARGET_COL
from src.utils.logging import get_logger
from src.utils.io import write_csv, read_csv

logger = get_logger(__name__)

# Project-wide canonical split file (name fixed by 03_plan_p1_v2.md §5.1)
SPLITS_FILE = DATA_SPLITS_DIR / "stratified_group_kfold_seed42.csv"


def build_fold_assignment(
    df: pd.DataFrame,
    n_splits: int = N_SPLITS,
    seed: int = SEED,
) -> pd.DataFrame:
    """
    Build a StratifiedGroupKFold assignment over labeled samples.

    Args:
        df: DataFrame with ID_COL and TARGET_COL (TARGET_COL may contain NaN)
        n_splits: Number of folds
        seed: Random seed

    Returns:
        DataFrame [id, sii, fold] covering only labeled rows; `fold` is the
        validation-fold index each row belongs to.
    """
    if ID_COL not in df.columns or TARGET_COL not in df.columns:
        raise ValueError(f"DataFrame must contain {ID_COL} and {TARGET_COL}")

    labeled = df[df[TARGET_COL].notna()].copy().reset_index(drop=True)
    n_dropped = len(df) - len(labeled)
    if n_dropped > 0:
        logger.warning(
            f"Excluding {n_dropped}/{len(df)} unlabeled samples from CV splits "
            f"(supervised P1 uses labeled samples only)"
        )

    y = labeled[TARGET_COL].astype(int).to_numpy()
    groups = labeled[ID_COL].to_numpy()

    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    labeled["fold"] = -1
    for fold_idx, (_, val_idx) in enumerate(sgkf.split(labeled, y, groups)):
        labeled.loc[val_idx, "fold"] = fold_idx

    if (labeled["fold"] < 0).any():
        raise RuntimeError("Some samples were not assigned to any fold")

    assignment = labeled[[ID_COL, TARGET_COL, "fold"]].copy()
    assignment[TARGET_COL] = assignment[TARGET_COL].astype(int)

    # Log per-fold distribution
    logger.info(f"Built {n_splits}-fold assignment over {len(assignment)} labeled samples")
    for fold_idx in range(n_splits):
        fold_mask = assignment["fold"] == fold_idx
        dist = assignment.loc[fold_mask, TARGET_COL].value_counts().sort_index().to_dict()
        logger.info(f"  Fold {fold_idx}: val={fold_mask.sum()} samples, sii dist={dist}")

    return assignment


def save_fold_assignment(
    assignment: pd.DataFrame,
    path: Path = SPLITS_FILE,
) -> None:
    """Save the fold assignment to the canonical CSV file."""
    write_csv(assignment, path)
    logger.info(f"Saved fold assignment to {path}")


def load_fold_assignment(path: Path = SPLITS_FILE) -> pd.DataFrame:
    """Load the canonical fold assignment file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Split file not found: {path}. "
            "Generate it first: python -m src.data.splits"
        )
    assignment = read_csv(path)
    logger.info(f"Loaded fold assignment ({len(assignment)} samples) from {path}")
    return assignment


def get_fold_ids(
    assignment: pd.DataFrame,
    fold: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get train/val participant IDs for a given fold.

    Args:
        assignment: Fold assignment DataFrame [id, sii, fold]
        fold: Validation fold index

    Returns:
        (train_ids, val_ids) as numpy arrays
    """
    val_ids = assignment.loc[assignment["fold"] == fold, ID_COL].to_numpy()
    train_ids = assignment.loc[assignment["fold"] != fold, ID_COL].to_numpy()
    return train_ids, val_ids


def get_fold_indices(
    df: pd.DataFrame,
    assignment: pd.DataFrame,
    fold: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get positional train/val indices into `df` for a given fold.

    Args:
        df: Feature DataFrame containing ID_COL
        assignment: Fold assignment DataFrame
        fold: Validation fold index

    Returns:
        (train_idx, val_idx) positional indices into df
    """
    train_ids, val_ids = get_fold_ids(assignment, fold)
    train_id_set, val_id_set = set(train_ids), set(val_ids)

    id_series = df[ID_COL]
    train_idx = np.where(id_series.isin(train_id_set))[0]
    val_idx = np.where(id_series.isin(val_id_set))[0]
    return train_idx, val_idx


def verify_no_leakage(assignment: pd.DataFrame) -> bool:
    """
    Verify each participant ID is assigned to exactly one fold.

    Args:
        assignment: Fold assignment DataFrame [id, sii, fold]

    Returns:
        True if no leakage

    Raises:
        ValueError: If any ID spans multiple folds
    """
    folds_per_id = assignment.groupby(ID_COL)["fold"].nunique()
    multi = folds_per_id[folds_per_id > 1]
    if len(multi) > 0:
        raise ValueError(
            f"{len(multi)} participant IDs span multiple folds (leakage): "
            f"{multi.index.tolist()[:5]}..."
        )
    logger.info("No participant ID leakage: every ID in exactly one fold")
    return True


def main():
    """Generate and persist the canonical fold assignment file."""
    from src.data.loader import load_train_data

    df = load_train_data()
    assignment = build_fold_assignment(df)
    verify_no_leakage(assignment)
    save_fold_assignment(assignment)
    print(f"\n✅ Split file written: {SPLITS_FILE}")
    print(f"   {len(assignment)} labeled samples across {N_SPLITS} folds")


if __name__ == "__main__":
    main()
