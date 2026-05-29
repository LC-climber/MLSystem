"""
Tabular Data Preprocessing

Handles preprocessing of tabular features including:
- Missing value imputation
- Type conversion
- Outlier detection
- Feature scaling
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from src.config import IMPUTATION_STRATEGY, SCALER_TYPE
from src.data.constants import ID_COL, TARGET_COL, MAX_MISSING_RATE
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TabularPreprocessor:
    """
    Preprocessor for tabular data.

    Handles missing values, scaling, and type conversion.
    """

    def __init__(
        self,
        imputation_strategy: str = IMPUTATION_STRATEGY,
        scaler_type: str = SCALER_TYPE,
        drop_high_missing: bool = True,
        max_missing_rate: float = MAX_MISSING_RATE
    ):
        """
        Initialize preprocessor.

        Args:
            imputation_strategy: Strategy for imputing missing values
            scaler_type: Type of scaler to use
            drop_high_missing: Whether to drop columns with high missing rates
            max_missing_rate: Maximum allowed missing rate for columns
        """
        self.imputation_strategy = imputation_strategy
        self.scaler_type = scaler_type
        self.drop_high_missing = drop_high_missing
        self.max_missing_rate = max_missing_rate

        self.imputer = None
        self.scaler = None
        self.feature_names_ = None
        self.dropped_cols_ = []
        self.numerical_cols_ = []
        self.categorical_cols_ = []

    def fit(self, df: pd.DataFrame, exclude_cols: list = None) -> "TabularPreprocessor":
        """
        Fit preprocessor on training data.

        Args:
            df: Training DataFrame
            exclude_cols: Columns to exclude from preprocessing

        Returns:
            Self
        """
        if exclude_cols is None:
            exclude_cols = [ID_COL, TARGET_COL]

        # Get feature columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        # Identify numerical and categorical columns
        self.numerical_cols_ = df[feature_cols].select_dtypes(
            include=[np.number]
        ).columns.tolist()

        self.categorical_cols_ = df[feature_cols].select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        logger.info(
            f"Identified {len(self.numerical_cols_)} numerical "
            f"and {len(self.categorical_cols_)} categorical columns"
        )

        # Drop columns with high missing rates
        if self.drop_high_missing:
            missing_rates = df[feature_cols].isnull().mean()
            high_missing = missing_rates[missing_rates > self.max_missing_rate]

            if len(high_missing) > 0:
                self.dropped_cols_ = high_missing.index.tolist()
                logger.warning(
                    f"Dropping {len(self.dropped_cols_)} columns with "
                    f">{self.max_missing_rate*100}% missing values: "
                    f"{self.dropped_cols_}"
                )

                # Update feature lists
                self.numerical_cols_ = [
                    col for col in self.numerical_cols_
                    if col not in self.dropped_cols_
                ]
                self.categorical_cols_ = [
                    col for col in self.categorical_cols_
                    if col not in self.dropped_cols_
                ]

        # Fit imputer on numerical columns
        if len(self.numerical_cols_) > 0:
            self.imputer = SimpleImputer(strategy=self.imputation_strategy)
            self.imputer.fit(df[self.numerical_cols_])
            logger.info(f"Fitted imputer with strategy: {self.imputation_strategy}")

        # Fit scaler on numerical columns
        if len(self.numerical_cols_) > 0:
            if self.scaler_type == "standard":
                self.scaler = StandardScaler()
            elif self.scaler_type == "robust":
                self.scaler = RobustScaler()
            elif self.scaler_type == "minmax":
                self.scaler = MinMaxScaler()
            else:
                raise ValueError(f"Unknown scaler type: {self.scaler_type}")

            # Fit scaler on imputed data
            imputed_data = self.imputer.transform(df[self.numerical_cols_])
            self.scaler.fit(imputed_data)
            logger.info(f"Fitted scaler: {self.scaler_type}")

        self.feature_names_ = self.numerical_cols_ + self.categorical_cols_

        return self

    def transform(self, df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
        """
        Transform data using fitted preprocessor.

        Args:
            df: DataFrame to transform
            exclude_cols: Columns to exclude from preprocessing

        Returns:
            Transformed DataFrame
        """
        if exclude_cols is None:
            exclude_cols = [ID_COL, TARGET_COL]

        df_transformed = df.copy()

        # Drop high missing columns
        if len(self.dropped_cols_) > 0:
            df_transformed = df_transformed.drop(columns=self.dropped_cols_, errors="ignore")

        # Impute and scale numerical columns
        if len(self.numerical_cols_) > 0 and self.imputer is not None:
            imputed_data = self.imputer.transform(df_transformed[self.numerical_cols_])

            if self.scaler is not None:
                scaled_data = self.scaler.transform(imputed_data)
                df_transformed[self.numerical_cols_] = scaled_data
            else:
                df_transformed[self.numerical_cols_] = imputed_data

        # Handle categorical columns (simple forward fill for now)
        if len(self.categorical_cols_) > 0:
            for col in self.categorical_cols_:
                if col in df_transformed.columns:
                    df_transformed[col] = df_transformed[col].fillna("missing")

        return df_transformed

    def fit_transform(self, df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
        """
        Fit and transform in one step.

        Args:
            df: DataFrame to fit and transform
            exclude_cols: Columns to exclude from preprocessing

        Returns:
            Transformed DataFrame
        """
        return self.fit(df, exclude_cols).transform(df, exclude_cols)

    def get_feature_names(self) -> list:
        """Get list of feature names after preprocessing."""
        return self.feature_names_


def detect_outliers(
    df: pd.DataFrame,
    columns: list,
    method: str = "iqr",
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    Detect outliers in numerical columns.

    Args:
        df: Input DataFrame
        columns: Columns to check for outliers
        method: Detection method ("iqr" or "zscore")
        threshold: Threshold for outlier detection

    Returns:
        DataFrame with outlier flags
    """
    outlier_flags = pd.DataFrame(index=df.index)

    for col in columns:
        if col not in df.columns:
            continue

        if method == "iqr":
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outlier_flags[f"{col}_outlier"] = (
                (df[col] < lower_bound) | (df[col] > upper_bound)
            )
        elif method == "zscore":
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outlier_flags[f"{col}_outlier"] = z_scores > threshold
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")

    n_outliers = outlier_flags.sum().sum()
    logger.info(f"Detected {n_outliers} outliers using {method} method")

    return outlier_flags


def get_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get summary of missing values.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with missing value statistics
    """
    missing_counts = df.isnull().sum()
    missing_rates = df.isnull().mean()

    summary = pd.DataFrame({
        "missing_count": missing_counts,
        "missing_rate": missing_rates,
        "dtype": df.dtypes
    })

    summary = summary[summary["missing_count"] > 0].sort_values(
        "missing_rate", ascending=False
    )

    return summary
