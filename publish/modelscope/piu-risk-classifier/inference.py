"""Standalone inference for the PIU Risk Classifier.

Only requires: scikit-learn, joblib, numpy, pandas (see requirements.txt).
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

LABEL_NAMES = ["None", "Mild", "Moderate", "Severe"]

# Friendly request keys -> raw training feature columns
REQUEST_FIELD_MAP = {
    "age": "Basic_Demos-Age",
    "sex": "Basic_Demos-Sex",
    "bmi": "Physical-BMI",
    "height": "Physical-Height",
    "weight": "Physical-Weight",
    "waist_circumference": "Physical-Waist_Circumference",
    "diastolic_bp": "Physical-Diastolic_BP",
    "systolic_bp": "Physical-Systolic_BP",
    "heart_rate": "Physical-HeartRate",
    "cgas_score": "CGAS-CGAS_Score",
    "computerinternet_hoursday": "PreInt_EduHx-computerinternet_hoursday",
}


class PiuRiskClassifier:
    """Loads model.joblib + model_metadata.json from a local directory."""

    def __init__(self, model_dir: str | Path = "."):
        model_dir = Path(model_dir)
        self.pipeline = joblib.load(model_dir / "model.joblib")
        meta = json.loads((model_dir / "model_metadata.json").read_text())
        self.feature_names = list(meta["feature_names"])

    @classmethod
    def from_pretrained(cls, repo_id_or_dir: str) -> "PiuRiskClassifier":
        path = Path(repo_id_or_dir)
        if path.exists():
            return cls(path)
        from modelscope import snapshot_download  # optional dependency

        return cls(snapshot_download(repo_id_or_dir))

    def _to_frame(self, record: dict) -> pd.DataFrame:
        row = {name: np.nan for name in self.feature_names}
        for key, value in record.items():
            if key in row:
                row[key] = value
            elif key in REQUEST_FIELD_MAP and REQUEST_FIELD_MAP[key] in row:
                row[REQUEST_FIELD_MAP[key]] = value
        return pd.DataFrame([row], columns=self.feature_names)

    def predict(self, record: dict) -> dict:
        features = self._to_frame(record)
        proba = self.pipeline.predict_proba(features)[0]
        classes = [int(c) for c in self.pipeline.classes_]
        pred = int(self.pipeline.predict(features)[0])
        return {
            "prediction": pred,
            "label": LABEL_NAMES[pred],
            "confidence": float(proba.max()),
            "probabilities": {
                LABEL_NAMES[cls]: float(p) for cls, p in zip(classes, proba)
            },
        }
