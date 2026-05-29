"""
Data Constants

Defines all data-related constants including column names, class mappings,
and data paths for the PIU (Problematic Internet Use) dataset.
"""

from pathlib import Path
from src.config import DATA_RAW_DIR, DATA_INTERIM_DIR, DATA_PROCESSED_DIR

# ============================================================================
# File Paths
# ============================================================================
TRAIN_CSV = DATA_RAW_DIR / "train.csv"
TEST_CSV = DATA_RAW_DIR / "test.csv"
SERIES_TRAIN_DIR = DATA_RAW_DIR / "series_train.parquet"
SERIES_TEST_DIR = DATA_RAW_DIR / "series_test.parquet"

# ============================================================================
# Column Names
# ============================================================================
# Identifier
ID_COL = "id"

# Target variable (Severity Impairment Index)
TARGET_COL = "sii"

# Grouping variable for cross-validation
GROUP_COL = "id"  # Each participant is a group

# Actigraphy time series columns
ACTIGRAPHY_COLS = ["X", "Y", "Z", "enmo", "anglez", "non_wear_flag"]
TIMESTAMP_COL = "step"

# ============================================================================
# Target Classes
# ============================================================================
# SII (Severity Impairment Index) classes
SII_CLASSES = {
    0: "None",
    1: "Mild",
    2: "Moderate",
    3: "Severe"
}

NUM_CLASSES = len(SII_CLASSES)

# ============================================================================
# Data Schema
# ============================================================================
# Expected dtypes for train.csv
TRAIN_DTYPES = {
    ID_COL: str,
    TARGET_COL: int
}

# Categorical columns (to be identified from data)
CATEGORICAL_COLS = []  # Will be populated after data exploration

# Numerical columns (to be identified from data)
NUMERICAL_COLS = []  # Will be populated after data exploration

# ============================================================================
# Data Validation
# ============================================================================
# Expected value ranges
SII_RANGE = (0, 3)  # Inclusive

# Missing value thresholds
MAX_MISSING_RATE = 0.95  # Drop columns with >95% missing values

# ============================================================================
# Feature Engineering
# ============================================================================
# Actigraphy aggregation window (in steps)
ACTIGRAPHY_WINDOW_SIZE = 1440  # 24 hours if 1 step = 1 minute

# Statistical features to extract from actigraphy
ACTIGRAPHY_STATS = ["mean", "std", "min", "max", "median", "q25", "q75"]
