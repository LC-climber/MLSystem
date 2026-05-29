"""
Cross-Validation Splits

Implements StratifiedGroupKFold for the PIU dataset to ensure:
1. Stratification by target class (SII)
2. Grouping by participant ID (no data leakage)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List
from sklearn.model_selection import StratifiedGroupKFold
from src.config import N_SPLITS, SEED, DATA_SPLITS_DIR
from src.data.constants import ID_COL, TARGET_COL
from src.utils.logging import get_logger
from src.utils.io import write_csv, read_csv

logger = get_logger(__name__)


def create_stratified_group_kfold(
    df: pd.DataFrame,
    n_splits: int = N_SPLITS,
    random_state: int = SEED
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Create stratified group k-fold splits.

    Args:
        df: DataFrame with ID_COL and TARGET_COL
        n_splits: Number of folds
        random_state: Random seed

    Returns:
        List of (train_indices, val_indices) tuples
    """
    logger.info(f"Creating {n_splits}-fold stratified group splits")

    # Validate required columns
    if ID_COL not in df.columns or TARGET_COL not in df.columns:
        raise ValueError(f"DataFrame must contain {ID_COL} and {TARGET_COL} columns")

    # Create splitter
    sgkf = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state
    )

    # Generate splits
    splits = []
    for fold_idx, (train_idx, val_idx) in enumerate(
        sgkf.split(df, df[TARGET_COL], groups=df[ID_COL])
    ):
        splits.append((train_idx, val_idx))

        # Log split statistics
        train_dist = df.iloc[train_idx][TARGET_COL].value_counts().sort_index()
        val_dist = df.iloc[val_idx][TARGET_COL].value_counts().sort_index()

        logger.info(
            f"Fold {fold_idx + 1}: "
            f"Train={len(train_idx)} ({train_dist.to_dict()}), "
            f"Val={len(val_idx)} ({val_dist.to_dict()})"
        )

    return splits


def save_splits(
    df: pd.DataFrame,
    splits: List[Tuple[np.ndarray, np.ndarray]],
    output_dir: Path = DATA_SPLITS_DIR
) -> None:
    """
    Save split indices to CSV files.

    Args:
        df: Original DataFrame
        splits: List of (train_indices, val_indices) tuples
        output_dir: Directory to save split files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        # Create split DataFrames with ID and fold assignment
        train_df = df.iloc[train_idx][[ID_COL, TARGET_COL]].copy()
        train_df["fold"] = fold_idx
        train_df["split"] = "train"

        val_df = df.iloc[val_idx][[ID_COL, TARGET_COL]].copy()
        val_df["fold"] = fold_idx
        val_df["split"] = "val"

        # Save to CSV
        fold_file = output_dir / f"fold_{fold_idx}.csv"
        fold_df = pd.concat([train_df, val_df], ignore_index=True)
        write_csv(fold_df, fold_file)

        logger.info(f"Saved fold {fold_idx} to {fold_file}")

    # Save summary
    summary_file = output_dir / "splits_summary.txt"
    with open(summary_file, "w") as f:
        f.write(f"Number of folds: {len(splits)}\n")
        f.write(f"Random seed: {SEED}\n")
        f.write(f"Total samples: {len(df)}\n\n")

        for fold_idx, (train_idx, val_idx) in enumerate(splits):
            f.write(f"Fold {fold_idx}:\n")
            f.write(f"  Train: {len(train_idx)} samples\n")
            f.write(f"  Val: {len(val_idx)} samples\n")

            train_dist = df.iloc[train_idx][TARGET_COL].value_counts().sort_index()
            val_dist = df.iloc[val_idx][TARGET_COL].value_counts().sort_index()

            f.write(f"  Train distribution: {train_dist.to_dict()}\n")
            f.write(f"  Val distribution: {val_dist.to_dict()}\n\n")

    logger.info(f"Saved splits summary to {summary_file}")


def load_splits(
    fold_idx: int,
    splits_dir: Path = DATA_SPLITS_DIR
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load train and validation splits for a specific fold.

    Args:
        fold_idx: Fold index (0-based)
        splits_dir: Directory containing split files

    Returns:
        Tuple of (train_df, val_df)
    """
    fold_file = splits_dir / f"fold_{fold_idx}.csv"

    if not fold_file.exists():
        raise FileNotFoundError(
            f"Split file not found: {fold_file}. "
            "Please run create_stratified_group_kfold() first."
        )

    fold_df = read_csv(fold_file)

    train_df = fold_df[fold_df["split"] == "train"].copy()
    val_df = fold_df[fold_df["split"] == "val"].copy()

    logger.info(
        f"Loaded fold {fold_idx}: "
        f"Train={len(train_df)}, Val={len(val_df)}"
    )

    return train_df, val_df


def get_fold_indices(
    df: pd.DataFrame,
    fold_idx: int,
    splits_dir: Path = DATA_SPLITS_DIR
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get train and validation indices for a specific fold.

    Args:
        df: Original DataFrame
        fold_idx: Fold index (0-based)
        splits_dir: Directory containing split files

    Returns:
        Tuple of (train_indices, val_indices)
    """
    train_df, val_df = load_splits(fold_idx, splits_dir)

    # Get indices by matching IDs
    train_idx = df[df[ID_COL].isin(train_df[ID_COL])].index.to_numpy()
    val_idx = df[df[ID_COL].isin(val_df[ID_COL])].index.to_numpy()

    return train_idx, val_idx


def verify_no_leakage(
    splits: List[Tuple[np.ndarray, np.ndarray]],
    df: pd.DataFrame
) -> bool:
    """
    Verify that there is no participant ID leakage between train and val sets.

    Args:
        splits: List of (train_indices, val_indices) tuples
        df: DataFrame with ID_COL

    Returns:
        True if no leakage detected

    Raises:
        ValueError: If leakage is detected
    """
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        train_ids = set(df.iloc[train_idx][ID_COL].unique())
        val_ids = set(df.iloc[val_idx][ID_COL].unique())

        overlap = train_ids & val_ids

        if overlap:
            raise ValueError(
                f"Fold {fold_idx}: Found {len(overlap)} participant IDs "
                f"in both train and val sets: {overlap}"
            )

    logger.info("No participant ID leakage detected across all folds")
    return True
