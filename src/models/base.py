"""
Model Base Class

Unified interface for all models across the three systems (sklearn / Spark /
PyTorch). A common interface lets the same 5-fold CV loop drive every system,
which is what makes the P1 cross-system comparison fair (same feat / fold /
class_weight / seed; see 03_plan_p1_v2.md §5.4).

All models take/return numpy arrays. System-specific representations (Spark
DataFrames, torch tensors) are handled internally — the conversion cost is part
of what P1 measures at the training stage.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
import numpy as np


class BaseModel(ABC):
    """Abstract base for all P1/P2 models."""

    # Subclasses set these (used as MLflow params / table rows)
    system: str = "base"      # "sklearn" | "spark" | "pytorch"
    algorithm: str = "base"   # "lr" | "mlp"

    def __init__(self, num_classes: int, class_weight: str = "balanced", seed: int = 42):
        self.num_classes = num_classes
        self.class_weight = class_weight
        self.seed = seed
        self.model: Any = None

    @property
    def name(self) -> str:
        """Identifier like 'sklearn_lr' used in tables and MLflow."""
        return f"{self.system}_{self.algorithm}"

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseModel":
        """Train on (X, y). Returns self."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels, shape (n_samples,)."""
        raise NotImplementedError

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities, shape (n_samples, num_classes)."""
        raise NotImplementedError

    def get_params(self) -> Dict[str, Any]:
        """Hyperparameters for MLflow logging."""
        return {
            "system": self.system,
            "algorithm": self.algorithm,
            "num_classes": self.num_classes,
            "class_weight": self.class_weight,
            "seed": self.seed,
        }

    def save(self, path: Path) -> None:
        """Serialize model to disk (override per system)."""
        raise NotImplementedError

    def load(self, path: Path) -> "BaseModel":
        """Load model from disk (override per system)."""
        raise NotImplementedError
