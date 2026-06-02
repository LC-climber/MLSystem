"""
P1 Systemwise Experiment Runner

Drives sklearn / Spark / PyTorch LR & MLP through the shared 5-fold CV loop
(src.training.cv.run_cv) on feat_v1 or feat_v2, then writes the P1 Table 2 rows.
Optionally logs each (system, algo, feature, cohort) run to MLflow.

Same feat / folds / seed / class_weight policy for every system → fair comparison.

Usage:
  python -m src.experiments.run_p1_systemwise
  python -m src.experiments.run_p1_systemwise --feature v2 --mlflow
  python -m src.experiments.run_p1_systemwise --feature v2 --cohort actigraphy
  python -m src.experiments.run_p1_systemwise --systems spark --folds 1
"""

import argparse
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.config import (
    SEED, N_SPLITS, REPORTS_DIR, TARGET_CLASSES,
    MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_P1, PROJECT_ROOT,
)
from src.data.constants import ID_COL
from src.data.feature_engineering import load_feat_v1, load_feat_v2
from src.data.splits import load_fold_assignment
from src.training.cv import run_cv, format_cv_row
from src.utils.io import write_csv
from src.utils.logging import get_logger

logger = get_logger(__name__)

NUM_CLASSES = len(TARGET_CLASSES)

FEATURE_ALIASES = {
    "v1": "v1",
    "feat_v1": "v1",
    "v1_tabular": "v1",
    "v2": "v2",
    "feat_v2": "v2",
    "v2_biosensing": "v2",
}


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


def _setup_mlflow(enabled: bool):
    if not enabled:
        return None
    no_proxy_hosts = "localhost,127.0.0.1"
    for key in ("NO_PROXY", "no_proxy"):
        current = os.environ.get(key, "")
        parts = [p.strip() for p in current.split(",") if p.strip()]
        for host in no_proxy_hosts.split(","):
            if host not in parts:
                parts.append(host)
        os.environ[key] = ",".join(parts)
    try:
        import mlflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_P1)
        return mlflow
    except Exception as exc:
        logger.warning("MLflow HTTP tracking unavailable (%s); falling back to local sqlite", exc)
        try:
            import mlflow
            mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlruns.db'}")
            mlflow.set_experiment(MLFLOW_EXPERIMENT_P1)
            return mlflow
        except Exception as sqlite_exc:
            logger.warning("MLflow disabled (%s)", sqlite_exc)
            return None


def _canonical_feature(name: str) -> str:
    try:
        return FEATURE_ALIASES[name]
    except KeyError:
        valid = ", ".join(sorted(FEATURE_ALIASES))
        raise ValueError(f"unknown feature={name!r}; valid aliases: {valid}")


def _actigraphy_ids() -> set:
    feat_v2 = load_feat_v2()
    return set(feat_v2.loc[feat_v2["act_enmo_mean"].notna(), ID_COL])


def _load_feature_and_assignment(feature_arg: str, cohort: str):
    feature = _canonical_feature(feature_arg)
    if cohort not in ("all", "actigraphy"):
        raise ValueError("cohort must be one of: all, actigraphy")

    if feature == "v1":
        feat = load_feat_v1()
        feat_version = "v1_tabular"
        feature_slug = "feat_v1"
    else:
        feat = load_feat_v2()
        feat_version = "v2_biosensing"
        feature_slug = "feat_v2"

    assignment = load_fold_assignment()
    if cohort == "actigraphy":
        keep = _actigraphy_ids()
        feat = feat[feat[ID_COL].isin(keep)].reset_index(drop=True)
        assignment = assignment[assignment[ID_COL].isin(keep)].reset_index(drop=True)
        if assignment.empty:
            raise RuntimeError("actigraphy cohort has no labeled rows")

    return feat, assignment, feat_version, feature_slug


def _model_parts(model_name: str):
    system, algo = model_name.split("_", 1)
    return system, algo


def _log_mlflow(mlflow, probe, result, n_folds, feat_version, feature_slug, cohort,
                n_samples, n_features):
    run_name = f"{feature_slug}_{cohort}_{result['model_name']}"
    with mlflow.start_run(run_name=run_name):
        params = probe.get_params()
        params["n_folds"] = n_folds
        params["feat_version"] = feat_version
        params["feature_slug"] = feature_slug
        params["cohort"] = cohort
        params["n_samples"] = n_samples
        params["n_features"] = n_features
        mlflow.log_params({k: str(v) for k, v in params.items()})
        for key, value in result["summary"].items():
            try:
                mlflow.log_metric(key, float(value))
            except (TypeError, ValueError):
                pass


def _write_table(results, feature_slug: str, cohort: str, feat_version: str):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in results:
        system, algo = _model_parts(r["model_name"])
        rows.append({
            "feature": feature_slug,
            "feat_version": feat_version,
            "cohort": cohort,
            "system": system,
            "algo": algo,
            "model": r["model_name"],
            **r["summary"],
        })
    df = pd.DataFrame(rows)
    suffix = feature_slug if cohort == "all" else f"{feature_slug}_{cohort}"
    out = REPORTS_DIR / f"p1_systemwise_{suffix}.csv"
    write_csv(df, out)
    logger.info("wrote %s", out)

    view_cols = [c for c in [
        "feature", "cohort", "system", "algo",
        "macro_f1_mean", "qwk_mean", "balanced_accuracy_mean",
        "train_time_s_mean", "inference_latency_us_mean",
    ] if c in df.columns]
    print(f"\n===== P1 Table 2 — {feature_slug} / {cohort} (mean over folds) =====")
    print(df[view_cols].to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description="P1 systemwise comparison")
    ap.add_argument("--systems", default="sklearn,spark,pytorch",
                    help="comma list of: sklearn,spark,pytorch")
    ap.add_argument("--feature", default="v1",
                    help="feature version: v1/v1_tabular or v2/v2_biosensing")
    ap.add_argument("--cohort", default="all", choices=["all", "actigraphy"],
                    help="all rows, or only rows with actigraphy coverage")
    ap.add_argument("--folds", type=int, default=N_SPLITS)
    ap.add_argument("--no-system-metrics", action="store_true",
                    help="skip latency/RSS/size measurement (faster)")
    ap.add_argument("--mlflow", action="store_true", help="log runs to MLflow")
    args = ap.parse_args()

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    feat, assignment, feat_version, feature_slug = _load_feature_and_assignment(
        args.feature, args.cohort
    )
    n_features = feat.shape[1] - 2
    logger.info(
        "%s cohort=%s feat=%s assignment=%s folds=%d systems=%s",
        feature_slug, args.cohort, feat.shape, assignment.shape,
        args.folds, systems,
    )

    factories = build_factories(systems)
    if not factories:
        logger.error("no valid systems selected: %s", systems)
        return 1

    mlflow = _setup_mlflow(args.mlflow)

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
            _log_mlflow(
                mlflow, factory(), result, args.folds,
                feat_version, feature_slug, args.cohort,
                n_samples=len(feat), n_features=n_features,
            )

    _write_table(results, feature_slug, args.cohort, feat_version)

    if "spark" in systems:
        from src.utils.spark import stop_spark
        stop_spark()
    return 0


if __name__ == "__main__":
    sys.exit(main())
