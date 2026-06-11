"""MLflow pyfunc wrapper for PIU risk models."""

from __future__ import annotations

from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd
import mlflow.pyfunc


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


class PIURiskPyFuncModel(mlflow.pyfunc.PythonModel):
    """Wrap a fitted sklearn pipeline as a request-friendly MLflow model."""

    def __init__(self, pipeline, feature_names: Iterable[str], class_labels: Iterable[int]):
        self.pipeline = pipeline
        self.feature_names = list(feature_names)
        self.class_labels = list(class_labels)

    def _coerce_records(self, model_input: Any) -> list[Dict[str, Any]]:
        if isinstance(model_input, pd.DataFrame):
            return model_input.to_dict(orient="records")
        if isinstance(model_input, dict):
            return [model_input]
        if isinstance(model_input, list):
            return model_input
        if isinstance(model_input, np.ndarray):
            if model_input.ndim == 1:
                model_input = model_input.reshape(1, -1)
            if model_input.shape[1] == len(self.feature_names):
                return [
                    dict(zip(self.feature_names, row.tolist()))
                    for row in model_input
                ]
        raise TypeError(f"Unsupported model input type/shape: {type(model_input)}")

    def _records_to_features(self, records: list[Dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for record in records:
            row = {name: np.nan for name in self.feature_names}

            for key, value in record.items():
                if key in row:
                    row[key] = value

            for request_key, feature_key in REQUEST_FIELD_MAP.items():
                if request_key in record and feature_key in row:
                    row[feature_key] = record[request_key]

            for container_key in ("additional_features", "actigraphy_features"):
                nested = record.get(container_key)
                if isinstance(nested, dict):
                    for key, value in nested.items():
                        if key in row:
                            row[key] = value

            rows.append(row)

        return pd.DataFrame(rows, columns=self.feature_names)

    def predict(self, context, model_input):
        records = self._coerce_records(model_input)
        features = self._records_to_features(records)
        predictions = self.pipeline.predict(features)
        probabilities = self.pipeline.predict_proba(features)
        confidences = probabilities.max(axis=1)

        return pd.DataFrame(
            {
                "prediction": predictions.astype(int),
                "probabilities": [row.tolist() for row in probabilities],
                "confidence": confidences.astype(float),
            }
        )
