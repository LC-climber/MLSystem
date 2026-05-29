"""
P1 Systemwise Experiment Runner

Drives sklearn / Spark / PyTorch LR & MLP through the shared 5-fold CV loop
(src.training.cv.run_cv) on feat_v1, then prints comparison Table 1 and writes
reports/p1_systemwise_feat_v1.csv. Optionally logs each (system, algo) run to
MLflow (03_plan_p1_v2.md §7; W2 deliverable: "Spark job 结果记录 MLflow").

Same feat / folds / seed / class_weight policy for every system → fair comparison.

Usage:
  python -m src.experiments.run_p1_systemwise                   # all three systems
  python -m src.experiments.run_p1_systemwise --systems spark   # just spark
  python -m src.experiments.run_p1_systemwise --folds 1         # quick fold-0 check
  python -m src.experiments.run_p1_systemwise --mlflow          # + MLflow logging
"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.config import (
    SEED, N_SPLITS, REPORTS_DIR, TARGET_CLASSES,
    MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_P1,
)
from src.data.feature_engineering import load_feat_v1
from src.data.splits import load_fold_assignment
from src.training.cv import run_cv, format_cv_row
from src.utils.logging import get_logger

logger = get_logger(__name__)

NUM_CLASSES = len(TARGET_CLASSES)


def build_factories(systems):
    """Return {name: (model_factory, latency_warmup, latency_iters)} for the chosen systems."""
    factories = {}
    if "sklearn" in systems:
        from src.models.sklearn_baselines import SklearnLogisticRegression, SklearnMLP
        factories["sklearn_lr"] = (lambda: SklearnLogisticRegression(NUM_CLASSES, seed=SEED), 20, 200)
        factories["sklearn_mlp"] = (lambda: SklearnMLP(NUM_CLASSES, seed=SEED), 20, 200)
    if "spark" in systems:
        from src.models.spark_baselines import SparkLogisticRegression, SparkMLP
        # Each Spark predict() is a full job → tiny latency-iter count (still honest, just fewer).
        factories["spark_lr"] = (lambda: SparkLogisticRegression(NUM_CLASSES, seed=SEED), 2, 10)
        factories["spark_mlp"] = (lambda: SparkMLP(NUM_CLASSES, seed=SEED), 2, 10)
    if "pytorch" in systems:
        from src.models.torch_baselines import TorchLogisticRegression, TorchMLP
        factories["pytorch_lr"] = (lambda: TorchLogisticRegression(NUM_CLASSES, seed=SEED), 20, 200)
        factories["pytorch_mlp"] = (lambda: TorchMLP(NUM_CLASSES, seed=SEED), 20, 200)
    return factories


def _log_mlflow(mlflow, probe, result, n_folds):
    with mlflow.start_run(run_name=result["model_name"]):
        params = probe.get_params()
        params["n_folds"] = n_folds
        params["feat_version"] = "v1_tabular"
        mlflow.log_params({k: str(v) for k, v in params.items()})
        for key, value in result["summary"].items():
            try:
                mlflow.log_metric(key, float(value))
            except (TypeError, ValueError):
                pass


def _write_table(results):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([{"model": r["model_name"], **r["summary"]} for r in results])
    out = REPORTS_DIR / "p1_systemwise_feat_v1.csv"
    df.to_csv(out, index=False)
    logger.info("wrote %s", out)

    view_cols = [c for c in [
        "model", "macro_f1_mean", "qwk_mean", "balanced_accuracy_mean",
        "train_time_s_mean", "inference_latency_us_mean",
    ] if c in df.columns]
    print("\n===== P1 Table 1 — feat_v1 (mean over folds) =====")
    print(df[view_cols].to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description="P1 systemwise comparison on feat_v1")
    ap.add_argument("--systems", default="sklearn,spark,pytorch",
                    help="comma list of: sklearn,spark,pytorch")
    ap.add_argument("--folds", type=int, default=N_SPLITS)
    ap.add_argument("--no-system-metrics", action="store_true",
                    help="skip latency/RSS/size measurement (faster)")
    ap.add_argument("--mlflow", action="store_true", help="log runs to MLflow")
    args = ap.parse_args()

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    feat = load_feat_v1()
    assignment = load_fold_assignment()
    logger.info("feat_v1=%s folds=%d systems=%s", feat.shape, args.folds, systems)

    factories = build_factories(systems)
    if not factories:
        logger.error("no valid systems selected: %s", systems)
        return 1

    mlflow = None
    if args.mlflow:
        try:
            import mlflow as _mlflow
            _mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            _mlflow.set_experiment(MLFLOW_EXPERIMENT_P1)
            mlflow = _mlflow
        except Exception as exc:  # server down / not installed → keep running without it
            logger.warning("MLflow disabled (%s)", exc)

    results = []
    for name, (factory, lat_warmup, lat_iters) in factories.items():
        logger.info("=== %s ===", name)
        result = run_cv(
            factory, feat, assignment,
            n_splits=args.folds, seed=SEED, preprocess=True,
            measure_system=not args.no_system_metrics,
            latency_warmup=lat_warmup, latency_iters=lat_iters,
        )
        results.append(result)
        print(format_cv_row(result))
        if mlflow is not None:
            _log_mlflow(mlflow, factory(), result, args.folds)

    _write_table(results)

    if "spark" in systems:
        from src.utils.spark import stop_spark
        stop_spark()
    return 0


if __name__ == "__main__":
    sys.exit(main())
