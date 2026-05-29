"""
Data Loader

Handles loading of raw data from the PIU dataset including:
- Tabular data (train.csv, test.csv)
- Time series data (actigraphy parquet files)
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from src.data.constants import (
    TRAIN_CSV, TEST_CSV, SERIES_TRAIN_DIR, SERIES_TEST_DIR,
    ID_COL, TARGET_COL, LEAKAGE_COL_PREFIXES
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def load_train_data(nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Load training tabular data.

    Args:
        nrows: Number of rows to load (for testing). None = load all.

    Returns:
        DataFrame with training data
    """
    logger.info(f"Loading training data from {TRAIN_CSV}")

    if not TRAIN_CSV.exists():
        raise FileNotFoundError(
            f"Training data not found at {TRAIN_CSV}. "
            "Please run: bash scripts/fetch_data.sh"
        )

    df = pd.read_csv(TRAIN_CSV, nrows=nrows)
    logger.info(f"Loaded {len(df)} training samples with {len(df.columns)} columns")

    return df


def load_test_data(nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Load test tabular data.

    Args:
        nrows: Number of rows to load (for testing). None = load all.

    Returns:
        DataFrame with test data
    """
    logger.info(f"Loading test data from {TEST_CSV}")

    if not TEST_CSV.exists():
        raise FileNotFoundError(
            f"Test data not found at {TEST_CSV}. "
            "Please run: bash scripts/fetch_data.sh"
        )

    df = pd.read_csv(TEST_CSV, nrows=nrows)
    logger.info(f"Loaded {len(df)} test samples with {len(df.columns)} columns")

    return df


def load_actigraphy_data(
    participant_id: str,
    data_dir: Path = SERIES_TRAIN_DIR
) -> pd.DataFrame:
    """
    Load actigraphy time series data for a specific participant.

    Args:
        participant_id: Participant ID
        data_dir: Directory containing parquet files

    Returns:
        DataFrame with actigraphy time series
    """
    parquet_file = data_dir / f"{participant_id}.parquet"

    if not parquet_file.exists():
        raise FileNotFoundError(
            f"Actigraphy data not found for participant {participant_id} "
            f"at {parquet_file}"
        )

    df = pd.read_parquet(parquet_file)
    logger.debug(f"Loaded {len(df)} actigraphy records for participant {participant_id}")

    return df


def load_all_actigraphy_ids(data_dir: Path = SERIES_TRAIN_DIR) -> list:
    """
    Get list of all participant IDs with actigraphy data.

    Args:
        data_dir: Directory containing parquet files

    Returns:
        List of participant IDs
    """
    if not data_dir.exists():
        logger.warning(f"Actigraphy directory not found: {data_dir}")
        return []

    parquet_files = list(data_dir.glob("*.parquet"))
    participant_ids = [f.stem for f in parquet_files]

    logger.info(f"Found {len(participant_ids)} participants with actigraphy data")

    return participant_ids


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Get summary statistics for a DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with summary statistics
    """
    summary = {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "missing_counts": df.isnull().sum().to_dict(),
        "missing_rates": (df.isnull().sum() / len(df)).to_dict()
    }

    if TARGET_COL in df.columns:
        summary["target_distribution"] = df[TARGET_COL].value_counts().to_dict()

    return summary


def validate_data_integrity(df: pd.DataFrame, is_train: bool = True) -> bool:
    """
    Validate data integrity.

    Args:
        df: DataFrame to validate
        is_train: Whether this is training data (has target column)

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    # Check required columns
    if ID_COL not in df.columns:
        raise ValueError(f"Missing required column: {ID_COL}")

    if is_train and TARGET_COL not in df.columns:
        raise ValueError(f"Missing required column: {TARGET_COL}")

    # Check for duplicate IDs
    if df[ID_COL].duplicated().any():
        n_duplicates = df[ID_COL].duplicated().sum()
        raise ValueError(f"Found {n_duplicates} duplicate IDs")

    # Check target values (if training data)
    # NOTE: PIU's `sii` target legitimately contains NaN for ~31% of participants
    # (label/actigraphy missingness is a known dataset characteristic, see v2 doc O13).
    # NaN labels are valid here; only non-NaN values must fall in {0, 1, 2, 3}.
    if is_train:
        labeled = df[TARGET_COL].dropna()
        invalid_targets = ~labeled.isin([0, 1, 2, 3])
        if invalid_targets.any():
            n_invalid = int(invalid_targets.sum())
            raise ValueError(
                f"Found {n_invalid} invalid target values. "
                "Expected values: 0, 1, 2, 3 (or NaN)"
            )

        n_missing = int(df[TARGET_COL].isna().sum())
        if n_missing > 0:
            logger.warning(
                f"{n_missing}/{len(df)} ({n_missing/len(df)*100:.1f}%) samples "
                f"have missing '{TARGET_COL}' labels (expected for PIU)"
            )

    logger.info("Data integrity validation passed")
    return True


def get_leakage_columns(df: pd.DataFrame) -> list:
    """
    Identify label-leakage columns that must be excluded from features.

    The PIU `sii` target is derived by binning `PCIAT-PCIAT_Total`, so every
    PCIAT-* column perfectly encodes the answer. These must never be used as
    model inputs. See src/data/constants.py LEAKAGE_COL_PREFIXES.

    Args:
        df: DataFrame to inspect

    Returns:
        List of column names that leak the target
    """
    leakage_cols = [
        col for col in df.columns
        if any(col.startswith(prefix) for prefix in LEAKAGE_COL_PREFIXES)
    ]

    if leakage_cols:
        logger.info(
            f"Identified {len(leakage_cols)} label-leakage columns to exclude "
            f"(prefixes={LEAKAGE_COL_PREFIXES})"
        )

    return leakage_cols


def get_feature_columns(df: pd.DataFrame, is_train: bool = True) -> list:
    """
    Get the list of valid feature columns (excluding ID, target, and leakage).

    Args:
        df: DataFrame to inspect
        is_train: Whether this is training data (excludes TARGET_COL)

    Returns:
        List of usable feature column names
    """
    exclude = set(get_leakage_columns(df)) | {ID_COL}
    if is_train:
        exclude.add(TARGET_COL)

    feature_cols = [col for col in df.columns if col not in exclude]
    return feature_cols
