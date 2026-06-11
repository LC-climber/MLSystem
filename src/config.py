"""
MLsystem Project - Global Configuration

This module defines all global constants, paths, and hyperparameters
used across the project to ensure consistency and reproducibility.
"""

import os
from pathlib import Path

# ============================================================================
# Reproducibility
# ============================================================================
SEED = 42

# ============================================================================
# Project Paths
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_INTERIM_DIR = DATA_DIR / "interim"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SPLITS_DIR = DATA_DIR / "splits"

MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
P1_REPORTS_DIR = REPORTS_DIR / "P1"
P2_REPORTS_DIR = REPORTS_DIR / "P2"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# ============================================================================
# MLflow Configuration
# ============================================================================
MLFLOW_TRACKING_URI = os.environ.get(
    "MLFLOW_TRACKING_URI",
    f"sqlite:///{PROJECT_ROOT / 'mlruns.db'}",
)
MLFLOW_EXPERIMENT_P1 = "piu-p1-systemwise"
MLFLOW_EXPERIMENT_P2 = "piu-p2-mlops"

# ============================================================================
# Feature Versions
# ============================================================================
FEATURE_VERSIONS = ["v1_tabular", "v2_biosensing", "v3_fusion"]

# ============================================================================
# Evaluation Metrics
# ============================================================================
# Project 1: Multi-system comparison
PRIMARY_METRIC_P1 = "macro_f1"
SECONDARY_METRICS_P1 = ["qwk", "balanced_accuracy"]

# Project 2: MLOps pipeline
PRIMARY_METRIC_P2 = "qwk"
SECONDARY_METRICS_P2 = ["macro_f1", "log_loss"]

# System metrics (both projects)
SYSTEM_METRICS = [
    "train_time_s",
    "epoch_time_s",
    "inference_latency_us",
    "inference_throughput_sps",
    "peak_rss_gb",
    "peak_gpu_mem_gb",
    "model_size_mb"
]

# ============================================================================
# Cross-Validation Configuration
# ============================================================================
N_SPLITS = 5
GROUP_COL = "participant_id"
STRATIFY_COL = "sii"

# ============================================================================
# Data Schema
# ============================================================================
# Target variable (Severity Impairment Index)
TARGET_COL = "sii"
TARGET_CLASSES = [0, 1, 2, 3]  # None, Mild, Moderate, Severe

# Participant identifier
ID_COL = "id"

# ============================================================================
# Model Hyperparameters (Defaults)
# ============================================================================
# Logistic Regression
LR_CONFIG = {
    "max_iter": 1000,
    "random_state": SEED,
    "class_weight": "balanced",
    "solver": "lbfgs"
}

# MLP (sklearn)
MLP_SKLEARN_CONFIG = {
    "hidden_layer_sizes": (128, 64),
    "activation": "relu",
    "solver": "adam",
    "alpha": 0.0001,
    "batch_size": 128,
    "learning_rate_init": 0.001,
    "max_iter": 200,
    "random_state": SEED,
    "early_stopping": True,
    "validation_fraction": 0.1
}

# MLP (PyTorch)
MLP_TORCH_CONFIG = {
    "hidden_dims": [128, 64],
    "dropout": 0.2,
    "activation": "relu",
    "lr": 0.001,
    "batch_size": 128,
    "epochs": 100,
    "early_stopping_patience": 10,
    "device": "cuda" if True else "cpu"  # Will be set dynamically
}

# ============================================================================
# Spark Configuration
# ============================================================================
SPARK_CONFIG = {
    # Exact `percentile` aggregates buffer every value per group → heap-hungry.
    # NOTE: in local mode this only takes effect via PYSPARK_SUBMIT_ARGS (see
    # src/utils/spark.py::pin_driver_memory); builder.config() is too late.
    "spark.driver.memory": "12g",
    "spark.executor.memory": "12g",
    "spark.sql.shuffle.partitions": "20",
    "spark.local.dir": str(PROJECT_ROOT / "spark_tmp")
}

# ============================================================================
# Data Processing
# ============================================================================
# Imputation strategies
IMPUTATION_STRATEGY = "median"  # Options: "mean", "median", "most_frequent"

# Scaling
SCALER_TYPE = "standard"  # Options: "standard", "minmax", "robust"

# ============================================================================
# Optuna Configuration (P2)
# ============================================================================
OPTUNA_N_TRIALS = 100
OPTUNA_TIMEOUT = None  # seconds, None = no timeout
OPTUNA_N_JOBS = 1  # Parallel trials

# ============================================================================
# Deployment Configuration (P2)
# ============================================================================
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000

# Model Registry Aliases
REGISTRY_ALIASES = ["baseline", "candidate", "champion", "demo"]

# Publishing
MODELSCOPE_REPO = "ICTclimber/piu-risk-classifier"  # published 2026-06-12 (champion v9)
HUGGINGFACE_REPO = "mlsys-2026s/piu-risk-classifier"
