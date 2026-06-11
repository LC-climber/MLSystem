#!/usr/bin/env python3
"""Re-register P2 final models without rerunning CV/Optuna."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.experiments.run_p2_full_pipeline import (
    CVResult,
    register_result_model,
    setup_mlflow,
)


def result_from_row(row: pd.Series) -> CVResult:
    feature_path = PROJECT_ROOT / "data" / "processed" / (
        "feat_v1__seed42.parquet" if row["feature_version"] == "v1" else "feat_v2__cpu__seed42.parquet"
    )
    feat = pd.read_parquet(feature_path)
    feature_names = [c for c in feat.columns if c not in ("id", "sii")]
    params = {
        "model_type": row["model_type"],
        "C": 1.0 if row["role"] == "baseline" else 1.115861961007209,
        "max_iter": 1000,
    }
    summary = {
        "macro_f1_mean": float(row["macro_f1_mean"]),
        "macro_f1_std": float(row["macro_f1_std"]),
        "qwk_mean": float(row["qwk_mean"]),
        "qwk_std": float(row["qwk_std"]),
        "balanced_accuracy_mean": float(row["balanced_accuracy_mean"]),
        "balanced_accuracy_std": float(row["balanced_accuracy_std"]),
        "log_loss_mean": float(row["log_loss_mean"]),
        "log_loss_std": float(row["log_loss_std"]),
        "train_time_s_mean": float(row["train_time_s_mean"]),
        "train_time_s_std": float(row["train_time_s_std"]),
    }
    return CVResult(
        name=row["model_name"],
        params=params,
        feature_version=row["feature_version"],
        summary=summary,
        per_fold=[],
        y_true=pd.Series(dtype=int).to_numpy(),
        y_pred=pd.Series(dtype=int).to_numpy(),
        y_proba=pd.DataFrame().to_numpy(),
        feature_names=feature_names,
        n_samples=int(row["n_samples"]),
        n_features=int(row["n_features"]),
        train_time_s=float(row["train_time_s_mean"]),
    )


def main() -> int:
    setup_mlflow()
    df = pd.read_csv(PROJECT_ROOT / "reports" / "P2" / "p2_model_comparison.csv")
    baseline = result_from_row(df[df["role"] == "baseline"].iloc[0])
    champion = result_from_row(df[df["role"] == "champion"].iloc[0])

    baseline_version = register_result_model(baseline, role="baseline_reregistered", alias="baseline")
    candidate_version = register_result_model(champion, role="candidate_reregistered", alias="candidate")
    champion_version = register_result_model(champion, role="champion_reregistered", alias="champion")

    print(f"baseline={baseline_version} candidate={candidate_version} champion={champion_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
