"""Run the complete P2 MLOps pipeline.

This script produces the P2 evidence chain:
- baseline CV and MLflow Registry alias
- Optuna hyperparameter search with nested MLflow trial runs
- candidate/champion selection
- final model artifact registration
- report CSV/Markdown and visualization figures
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mlsystem-matplotlib")

import joblib
import mlflow
import numpy as np
import optuna
import pandas as pd
from matplotlib import pyplot as plt
from mlflow.tracking import MlflowClient
from optuna.pruners import MedianPruner
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from src.config import (
    PROJECT_ROOT,
    P2_REPORTS_DIR,
    SEED,
    TARGET_CLASSES,
    MLFLOW_EXPERIMENT_P2,
)
from src.data.constants import ID_COL, TARGET_COL
from src.data.feature_engineering import (
    get_feature_matrix_columns,
    load_feat_v1,
    load_feat_v2,
    make_preprocessing_pipeline,
)
from src.data.splits import get_fold_indices, load_fold_assignment
from src.deployment.pyfunc_model import PIURiskPyFuncModel
from src.evaluation.metrics import compute_classification_metrics, summarize_cv_metrics
from src.utils.logging import get_logger
from src.utils.reproducibility import set_seed


logger = get_logger(__name__)

MLFLOW_DB = PROJECT_ROOT / "mlruns.db"
MLFLOW_ARTIFACTS = PROJECT_ROOT / "mlruns_artifacts"
OPTUNA_DB = PROJECT_ROOT / "src" / "optuna.db"
MODEL_NAME = "piu-risk"
FIGURES_DIR = P2_REPORTS_DIR / "figures"


@dataclass
class CVResult:
    name: str
    params: Dict[str, Any]
    feature_version: str
    summary: Dict[str, float]
    per_fold: list[Dict[str, float]]
    y_true: np.ndarray
    y_pred: np.ndarray
    y_proba: np.ndarray
    feature_names: list[str]
    n_samples: int
    n_features: int
    train_time_s: float


def setup_mlflow() -> None:
    MLFLOW_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB}")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_P2)
    logger.info("MLflow tracking URI: %s", tracking_uri)


def load_feature_data(feature_version: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    if feature_version == "v1":
        feat = load_feat_v1()
    elif feature_version == "v2":
        feat = load_feat_v2()
    else:
        raise ValueError(f"unsupported feature_version={feature_version}")

    assignment = load_fold_assignment()
    labeled_ids = set(assignment[ID_COL])
    feat = feat[feat[ID_COL].isin(labeled_ids)].reset_index(drop=True)
    feature_names = get_feature_matrix_columns(feat)
    return feat, assignment, feature_names


def make_estimator(model_type: str, params: Dict[str, Any]):
    if model_type == "logreg":
        return LogisticRegression(
            max_iter=int(params.get("max_iter", 1000)),
            C=float(params.get("C", 1.0)),
            solver="lbfgs",
            class_weight="balanced",
            random_state=SEED,
        )
    if model_type == "mlp":
        hidden_dim_1 = int(params.get("hidden_dim_1", 128))
        hidden_dim_2 = int(params.get("hidden_dim_2", 64))
        return MLPClassifier(
            hidden_layer_sizes=(hidden_dim_1, hidden_dim_2),
            activation="relu",
            solver="adam",
            alpha=float(params.get("alpha", 1e-4)),
            batch_size=int(params.get("batch_size", 128)),
            learning_rate_init=float(params.get("learning_rate_init", 1e-3)),
            max_iter=int(params.get("max_iter", 200)),
            early_stopping=True,
            validation_fraction=0.1,
            random_state=SEED,
        )
    raise ValueError(f"unsupported model_type={model_type}")


def make_pipeline(model_type: str, params: Dict[str, Any]) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", make_preprocessing_pipeline()),
            ("model", make_estimator(model_type, params)),
        ]
    )


def run_cv_pipeline(
    name: str,
    feature_version: str,
    model_type: str,
    params: Dict[str, Any],
    n_folds: int,
) -> CVResult:
    set_seed(SEED)
    feat, assignment, feature_names = load_feature_data(feature_version)
    X_all = feat[feature_names]
    y_all = feat[TARGET_COL].astype(int).to_numpy()

    fold_metrics: list[Dict[str, float]] = []
    y_true_all: list[np.ndarray] = []
    y_pred_all: list[np.ndarray] = []
    y_proba_all: list[np.ndarray] = []
    total_train_time = 0.0

    for fold in range(n_folds):
        train_idx, val_idx = get_fold_indices(feat, assignment, fold)
        X_train, y_train = X_all.iloc[train_idx], y_all[train_idx]
        X_val, y_val = X_all.iloc[val_idx], y_all[val_idx]

        pipeline = make_pipeline(model_type, params)
        start = time.perf_counter()
        pipeline.fit(X_train, y_train)
        train_time_s = time.perf_counter() - start
        total_train_time += train_time_s

        y_pred = pipeline.predict(X_val)
        y_proba = pipeline.predict_proba(X_val)
        metrics = compute_classification_metrics(y_val, y_pred, y_proba)
        metrics["train_time_s"] = train_time_s
        fold_metrics.append(metrics)

        y_true_all.append(y_val)
        y_pred_all.append(y_pred)
        y_proba_all.append(y_proba)

        logger.info(
            "%s fold %d: qwk=%.4f macro_f1=%.4f train=%.2fs",
            name,
            fold,
            metrics["qwk"],
            metrics["macro_f1"],
            train_time_s,
        )

    summary = summarize_cv_metrics(fold_metrics)
    return CVResult(
        name=name,
        params={**params, "model_type": model_type},
        feature_version=feature_version,
        summary=summary,
        per_fold=fold_metrics,
        y_true=np.concatenate(y_true_all),
        y_pred=np.concatenate(y_pred_all),
        y_proba=np.vstack(y_proba_all),
        feature_names=feature_names,
        n_samples=len(feat),
        n_features=len(feature_names),
        train_time_s=total_train_time,
    )


def log_cv_result(result: CVResult, alias_role: str | None = None) -> str:
    with mlflow.start_run(run_name=result.name) as run:
        mlflow.log_params(
            {
                **{k: str(v) for k, v in result.params.items()},
                "feature_version": result.feature_version,
                "n_samples": result.n_samples,
                "n_features": result.n_features,
                "seed": SEED,
                "alias_role": alias_role or "",
            }
        )
        for key, value in result.summary.items():
            mlflow.log_metric(key, float(value))
        mlflow.log_dict(result.per_fold, "cv_per_fold_metrics.json")
        return run.info.run_id


def objective(trial: optuna.Trial, n_folds: int) -> float:
    model_type = trial.suggest_categorical("model_type", ["logreg", "mlp"])
    feature_version = trial.suggest_categorical("feature_version", ["v1", "v2"])

    if model_type == "logreg":
        params = {
            "C": trial.suggest_float("C", 0.05, 10.0, log=True),
            "max_iter": 1000,
        }
    else:
        params = {
            "hidden_dim_1": trial.suggest_categorical("hidden_dim_1", [64, 128, 256]),
            "hidden_dim_2": trial.suggest_categorical("hidden_dim_2", [32, 64, 128]),
            "alpha": trial.suggest_float("alpha", 1e-5, 1e-2, log=True),
            "learning_rate_init": trial.suggest_float("learning_rate_init", 1e-4, 1e-2, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [64, 128, 256]),
            "max_iter": trial.suggest_int("max_iter", 80, 200, step=40),
        }

    result = run_cv_pipeline(
        name=f"trial_{trial.number}_{model_type}_{feature_version}",
        feature_version=feature_version,
        model_type=model_type,
        params=params,
        n_folds=n_folds,
    )

    with mlflow.start_run(run_name=f"optuna_trial_{trial.number}", nested=True):
        mlflow.log_params(
            {
                "trial_number": trial.number,
                "model_type": model_type,
                "feature_version": feature_version,
                **{k: str(v) for k, v in params.items()},
            }
        )
        for key, value in result.summary.items():
            mlflow.log_metric(key, float(value))

    qwk = result.summary["qwk_mean"]
    trial.set_user_attr("macro_f1_mean", result.summary["macro_f1_mean"])
    trial.set_user_attr("balanced_accuracy_mean", result.summary["balanced_accuracy_mean"])
    trial.set_user_attr("log_loss_mean", result.summary.get("log_loss_mean", float("nan")))
    trial.set_user_attr("train_time_s_mean", result.summary["train_time_s_mean"])
    trial.report(qwk, step=0)
    if trial.should_prune():
        raise optuna.TrialPruned()
    return qwk


def run_optuna(study_name: str, n_trials: int, n_folds: int, timeout: int | None) -> optuna.Study:
    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",
        pruner=MedianPruner(n_startup_trials=max(3, min(10, n_trials // 3))),
        storage=f"sqlite:///{OPTUNA_DB}",
        load_if_exists=True,
    )
    with mlflow.start_run(run_name=f"optuna_{study_name}") as run:
        mlflow.log_params({"study_name": study_name, "n_trials": n_trials, "n_folds": n_folds})
        study.optimize(lambda trial: objective(trial, n_folds), n_trials=n_trials, timeout=timeout)
        if study.best_trial:
            mlflow.log_metric("best_qwk", float(study.best_value))
            mlflow.log_params({f"best_{k}": str(v) for k, v in study.best_trial.params.items()})
            mlflow.set_tag("p2_parent_run_id", run.info.run_id)
    return study


def params_from_trial(trial: optuna.Trial) -> tuple[str, str, Dict[str, Any]]:
    model_type = trial.params["model_type"]
    feature_version = trial.params["feature_version"]
    if model_type == "logreg":
        params = {"C": trial.params["C"], "max_iter": 1000}
    else:
        params = {
            "hidden_dim_1": trial.params["hidden_dim_1"],
            "hidden_dim_2": trial.params["hidden_dim_2"],
            "alpha": trial.params["alpha"],
            "learning_rate_init": trial.params["learning_rate_init"],
            "batch_size": trial.params["batch_size"],
            "max_iter": trial.params["max_iter"],
        }
    return model_type, feature_version, params


def fit_full_model(result: CVResult) -> Pipeline:
    feat, _, _ = load_feature_data(result.feature_version)
    X = feat[result.feature_names]
    y = feat[TARGET_COL].astype(int).to_numpy()
    pipeline = make_pipeline(result.params["model_type"], result.params)
    pipeline.fit(X, y)
    return pipeline


def make_model_card(result: CVResult, role: str) -> str:
    metrics = result.summary
    return f"""# Model Card: {MODEL_NAME} ({role})

Generated: 2026-06-11

## Intended Use

Research prototype for PIU severity screening. It is not a clinical diagnostic device.

## Model

- Role: {role}
- Feature version: {result.feature_version}
- Model type: {result.params['model_type']}
- Samples: {result.n_samples}
- Features: {result.n_features}
- Seed: {SEED}

## Cross-Validation Metrics

| Metric | Mean | Std |
| --- | ---: | ---: |
| QWK | {metrics['qwk_mean']:.4f} | {metrics['qwk_std']:.4f} |
| Macro-F1 | {metrics['macro_f1_mean']:.4f} | {metrics['macro_f1_std']:.4f} |
| Balanced Accuracy | {metrics['balanced_accuracy_mean']:.4f} | {metrics['balanced_accuracy_std']:.4f} |
| Log Loss | {metrics.get('log_loss_mean', float('nan')):.4f} | {metrics.get('log_loss_std', float('nan')):.4f} |

## Limitations

- Trained on the course project snapshot of the Kaggle Child Mind Institute PIU dataset.
- Input examples with only a few fields rely on training-set imputation for missing features.
- The model is for MLOps demonstration and research, not standalone medical decision making.
"""


def register_result_model(result: CVResult, role: str, alias: str) -> int:
    pipeline = fit_full_model(result)
    pyfunc_model = PIURiskPyFuncModel(
        pipeline=pipeline,
        feature_names=result.feature_names,
        class_labels=TARGET_CLASSES,
    )
    sample_input = {
        "age": 12.5,
        "sex": 1.0,
        "bmi": 18.5,
        "height": 150.0,
        "weight": 45.0,
        "cgas_score": 75.0,
    }

    with mlflow.start_run(run_name=f"register_{role}_{result.name}") as run:
        mlflow.log_params(
            {
                **{k: str(v) for k, v in result.params.items()},
                "feature_version": result.feature_version,
                "n_samples": result.n_samples,
                "n_features": result.n_features,
                "role": role,
                "seed": SEED,
            }
        )
        for key, value in result.summary.items():
            mlflow.log_metric(key, float(value))

        model_dir = P2_REPORTS_DIR / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib_path = model_dir / f"{role}_{result.name}.joblib"
        joblib.dump(pipeline, joblib_path)
        mlflow.log_artifact(str(joblib_path), artifact_path="model_bundle")
        mlflow.log_text(make_model_card(result, role), "model_card.md")
        mlflow.log_dict(
            {
                "feature_names": result.feature_names,
                "target_classes": TARGET_CLASSES,
                "params": result.params,
                "summary": result.summary,
            },
            "model_metadata.json",
        )
        mlflow.log_dict(sample_input, "sample_input.json")
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=pyfunc_model,
            registered_model_name=MODEL_NAME,
        )
        run_id = run.info.run_id

    client = MlflowClient()
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    matching_versions = [int(v.version) for v in versions if v.run_id == run_id]
    if not matching_versions:
        raise RuntimeError(f"No registered model version found for run_id={run_id}")
    version = max(matching_versions)
    client.set_registered_model_alias(MODEL_NAME, alias, version)
    client.set_model_version_tag(MODEL_NAME, str(version), "role", role)
    client.set_model_version_tag(MODEL_NAME, str(version), "feature_version", result.feature_version)
    client.update_model_version(
        name=MODEL_NAME,
        version=str(version),
        description=f"{role}: {result.name}, QWK={result.summary['qwk_mean']:.4f}",
    )
    logger.info("Registered %s as %s version %s", result.name, alias, version)
    return version


def write_tables(baseline: CVResult, candidate: CVResult, champion: CVResult, study: optuna.Study) -> None:
    P2_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for role, result in [("baseline", baseline), ("candidate", candidate)]:
        rows.append(
            {
                "model_name": result.name,
                "role": role,
                "feature_version": result.feature_version,
                "model_type": result.params["model_type"],
                "n_samples": result.n_samples,
                "n_features": result.n_features,
                **result.summary,
            }
        )
    if champion.name != candidate.name:
        rows.append(
            {
                "model_name": champion.name,
                "role": "champion",
                "feature_version": champion.feature_version,
                "model_type": champion.params["model_type"],
                "n_samples": champion.n_samples,
                "n_features": champion.n_features,
                **champion.summary,
            }
        )
    else:
        rows.append({**rows[-1], "role": "champion"})
    pd.DataFrame(rows).to_csv(P2_REPORTS_DIR / "p2_model_comparison.csv", index=False)

    trial_rows = []
    for trial in study.trials:
        row = {
            "number": trial.number,
            "state": trial.state.name,
            "value": trial.value,
            **trial.params,
            **trial.user_attrs,
        }
        trial_rows.append(row)
    pd.DataFrame(trial_rows).to_csv(P2_REPORTS_DIR / "p2_formal_optuna_trials.csv", index=False)


def _save_fig(fig, stem: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGURES_DIR / f"{stem}.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_metric_comparison(results: list[CVResult]) -> None:
    rows = []
    for result in results:
        rows.append(
            {
                "model": result.name,
                "QWK": result.summary["qwk_mean"],
                "Macro-F1": result.summary["macro_f1_mean"],
                "Balanced Acc.": result.summary["balanced_accuracy_mean"],
            }
        )
    df = pd.DataFrame(rows).set_index("model")
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    df.plot(kind="bar", ax=ax, color=["#2F6F6D", "#C45A3A", "#4F6FA8"])
    ax.set_ylim(0, max(0.5, float(df.max().max()) + 0.05))
    ax.set_ylabel("5-fold CV mean")
    ax.set_title("P2 Baseline vs Candidate/Champion Metrics")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper right")
    _save_fig(fig, "p2_metric_comparison")


def plot_confusion(result: CVResult) -> None:
    cm = confusion_matrix(result.y_true, result.y_pred, labels=TARGET_CLASSES)
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    ConfusionMatrixDisplay(cm, display_labels=["None", "Mild", "Moderate", "Severe"]).plot(
        ax=ax,
        cmap="Blues",
        colorbar=False,
    )
    ax.set_title(f"P2 Champion CV Confusion Matrix: {result.name}")
    _save_fig(fig, "p2_champion_confusion_matrix")


def plot_optuna(study: optuna.Study) -> None:
    complete = [t for t in study.trials if t.value is not None]
    if not complete:
        return
    numbers = [t.number for t in complete]
    values = [t.value for t in complete]
    best_so_far = np.maximum.accumulate(values)
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    ax.plot(numbers, values, marker="o", label="trial QWK", color="#597A8C")
    ax.plot(numbers, best_so_far, marker="s", label="best so far", color="#C45A3A")
    ax.set_xlabel("Optuna trial")
    ax.set_ylabel("QWK")
    ax.set_title("P2 Optuna Optimization Trace")
    ax.grid(alpha=0.25)
    ax.legend()
    _save_fig(fig, "p2_optuna_trace")


def plot_run_status() -> None:
    client = MlflowClient()
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENT_P2)
    if experiment is None:
        return
    runs = client.search_runs([experiment.experiment_id], max_results=500)
    counts: Dict[str, int] = {}
    for run in runs:
        counts[run.info.status] = counts.get(run.info.status, 0) + 1
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.bar(counts.keys(), counts.values(), color="#6C8F5D")
    ax.set_title("P2 MLflow Run Status")
    ax.set_ylabel("Run count")
    ax.grid(axis="y", alpha=0.25)
    _save_fig(fig, "p2_mlflow_run_status")


def write_final_report(
    baseline: CVResult,
    candidate: CVResult,
    champion: CVResult,
    study: optuna.Study,
    versions: Dict[str, int],
) -> None:
    P2_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison = pd.read_csv(P2_REPORTS_DIR / "p2_model_comparison.csv")
    best = study.best_trial
    report = f"""# P2 MLOps Final Report

Generated: 2026-06-11

## Status

P2 is complete for the local reproducible MLOps workflow: experiment tracking, hyperparameter search, model registry aliases, artifacts, API-compatible model packaging, and report visualizations are present.

## Experiment Setup

- Dataset: Child Mind Institute PIU local project snapshot
- Split: canonical StratifiedGroupKFold assignment, 5-fold CV unless otherwise specified
- Tracking backend: `mlruns.db`
- Artifact root: `mlruns_artifacts/`
- Optuna study: `{study.study_name}`
- Formal Optuna trials requested/completed in this run: `{len(study.trials)}`

## Results

{comparison.to_markdown(index=False)}

## Champion Decision

- Baseline: `{baseline.name}`, QWK={baseline.summary['qwk_mean']:.4f}
- Best Optuna candidate: `{candidate.name}`, QWK={candidate.summary['qwk_mean']:.4f}
- Champion: `{champion.name}`, QWK={champion.summary['qwk_mean']:.4f}

The champion is selected by highest 5-fold mean QWK. If the Optuna candidate does not beat the baseline, the baseline remains champion and the Optuna result is retained as `candidate`.

## Registry

- Registered model: `{MODEL_NAME}`
- baseline version: `{versions['baseline']}`
- candidate version: `{versions['candidate']}`
- champion version: `{versions['champion']}`

## Visual Evidence

- `figures/p2_metric_comparison.png`
- `figures/p2_optuna_trace.png`
- `figures/p2_champion_confusion_matrix.png`
- `figures/p2_mlflow_run_status.png`

## Best Optuna Trial

```json
{json.dumps({"number": best.number, "value": best.value, "params": best.params}, indent=2)}
```

## Reproduction

```bash
python -m src.experiments.run_p2_full_pipeline --trials {len(study.trials)} --folds 5 --study-name {study.study_name}
python scripts/export_p2_reports.py
```
"""
    (P2_REPORTS_DIR / "p2_final_report.md").write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run complete P2 MLOps pipeline")
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--study-name", default="p2-formal-mlops")
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args()

    setup_mlflow()
    P2_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    baseline = run_cv_pipeline(
        name="baseline_logreg_v1",
        feature_version="v1",
        model_type="logreg",
        params={"C": 1.0, "max_iter": 1000},
        n_folds=args.folds,
    )
    log_cv_result(baseline, alias_role="baseline")

    study = run_optuna(args.study_name, args.trials, args.folds, args.timeout)
    model_type, feature_version, params = params_from_trial(study.best_trial)
    candidate = run_cv_pipeline(
        name=f"candidate_{model_type}_{feature_version}",
        feature_version=feature_version,
        model_type=model_type,
        params=params,
        n_folds=args.folds,
    )
    log_cv_result(candidate, alias_role="candidate")

    champion = candidate if candidate.summary["qwk_mean"] > baseline.summary["qwk_mean"] else baseline
    versions = {
        "baseline": register_result_model(baseline, role="baseline", alias="baseline"),
        "candidate": register_result_model(candidate, role="candidate", alias="candidate"),
    }
    champion_alias_source = "candidate" if champion is candidate else "baseline"
    versions["champion"] = register_result_model(champion, role=f"champion_from_{champion_alias_source}", alias="champion")

    write_tables(baseline, candidate, champion, study)
    plot_metric_comparison([baseline, candidate, champion])
    plot_confusion(champion)
    plot_optuna(study)
    plot_run_status()
    write_final_report(baseline, candidate, champion, study, versions)

    logger.info("P2 pipeline complete. Reports: %s", P2_REPORTS_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
