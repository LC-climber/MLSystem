"""
I/O Utilities

Handles file reading/writing operations, especially for Parquet files.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union


def read_parquet(
    file_path: Union[str, Path],
    columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Read a Parquet file into a pandas DataFrame.

    Args:
        file_path: Path to Parquet file
        columns: Optional list of columns to read

    Returns:
        DataFrame
    """
    return pd.read_parquet(file_path, columns=columns)


def write_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    compression: str = "snappy"
) -> None:
    """
    Write a DataFrame to Parquet format.

    Args:
        df: DataFrame to write
        file_path: Output file path
        compression: Compression algorithm (default: snappy)
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, compression=compression, index=False)


def read_csv(
    file_path: Union[str, Path],
    **kwargs
) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame.

    Args:
        file_path: Path to CSV file
        **kwargs: Additional arguments for pd.read_csv

    Returns:
        DataFrame
    """
    return pd.read_csv(file_path, **kwargs)


def write_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False,
    **kwargs
) -> None:
    """
    Write a DataFrame to CSV format.

    Args:
        df: DataFrame to write
        file_path: Output file path
        index: Whether to write row index
        **kwargs: Additional arguments for df.to_csv
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=index, **kwargs)
