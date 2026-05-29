"""
scikit-learn Baseline Models

Single-machine system in the P1 comparison. Implements LR and MLP (see
03_plan_p1_v2.md §5.4). Hyperparameters come from src/config.py so all three
systems reference the same intended settings.
"""

from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from src.config import LR_CONFIG, MLP_SKLEARN_CONFIG
from src.models.base import BaseModel


class SklearnLogisticRegression(BaseModel):
    """LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced')."""

    system = "sklearn"
    algorithm = "lr"

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SklearnLogisticRegression":
        params = {**LR_CONFIG, "random_state": self.seed, "class_weight": self.class_weight}
        self.model = LogisticRegression(**params)
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def get_params(self):
        return {**super().get_params(), **LR_CONFIG}

    def save(self, path: Path) -> None:
        import joblib
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)


class SklearnMLP(BaseModel):
    """
    MLPClassifier(hidden=(128,64), relu, adam, early_stopping).

    NOTE: sklearn's MLPClassifier supports neither class_weight nor sample_weight,
    so the imbalance handling that LR gets via class_weight='balanced' is NOT
    available here. This is a genuine system-level difference, not an algorithm
    difference — reported per R-SYS-3 (06_risk_and_eval_v2.md §1.2).
    """

    system = "sklearn"
    algorithm = "mlp"

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SklearnMLP":
        params = {**MLP_SKLEARN_CONFIG, "random_state": self.seed}
        self.model = MLPClassifier(**params)
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def get_params(self):
        # class_weight not applicable for sklearn MLP — mark explicitly
        params = {**super().get_params(), **MLP_SKLEARN_CONFIG}
        params["class_weight"] = "not_supported"
        return params

    def save(self, path: Path) -> None:
        import joblib
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
