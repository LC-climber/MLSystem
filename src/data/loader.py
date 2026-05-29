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
    ID_COL, TARGET_COL
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
    if is_train:
        invalid_targets = ~df[TARGET_COL].isin([0, 1, 2, 3])
        if invalid_targets.any():
            n_invalid = invalid_targets.sum()
            raise ValueError(
                f"Found {n_invalid} invalid target values. "
                "Expected values: 0, 1, 2, 3"
            )

    logger.info("Data integrity validation passed")
    return True
