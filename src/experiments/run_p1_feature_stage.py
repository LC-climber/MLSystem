"""
P1 Feature-Stage Experiment Runner

Builds Table 1 from 03_plan_p1_v2.md §7.2: pandas streaming vs Spark
applyInPandas for feat_v2 actigraphy preprocessing. The script measures wall-clock
time, process-tree peak RSS (so Spark's JVM is counted), raw file MD5, rounded
logical hash, and CPU/Spark equivalence.

Usage:
  python -m src.experiments.run_p1_feature_stage
  python -m src.experiments.run_p1_feature_stage --mlflow
  python -m src.experiments.run_p1_feature_stage --skip-build
  python -m src.experiments.run_p1_feature_stage --spark-master local[4]
"""

import argparse
import hashlib
import math
import os
import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
import psutil

from src.config import (
    MLFLOW_EXPERIMENT_P1,
    MLFLOW_TRACKING_URI,
    PROJECT_ROOT,
    P1_REPORTS_DIR,
    SPARK_CONFIG,
)
from src.data.actigraphy_features import (
    FEAT_V2_CPU_FILE,
    FEAT_V2_SPARK_FILE,
    actigraphy_feature_columns,
)
from src.data.constants import ID_COL
from src.data.preprocess_actigraphy_pandas import build_feat_v2_cpu
from src.data.preprocess_actigraphy_spark import build_feat_v2_spark
from src.utils.io import write_csv
from src.utils.logging import get_logger

logger = get_logger(__name__)

OUT_FILE = P1_REPORTS_DIR / "p1_feature_stage_feat_v2.csv"
EQUIV_THRESHOLD = 1e-6
LOGICAL_HASH_DECIMALS = 9


def _rss_process_tree_gb() -> float:
    """Current RSS of this process plus children, in GiB."""
    rss = 0
    root = psutil.Process(os.getpid())
    for proc in [root] + root.children(recursive=True):
        try:
            rss += proc.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return rss / (1024 ** 3)


def _measure(fn, sample_interval_s: float):
    """Run fn() while sampling process-tree RSS."""
    stop = threading.Event()
    peak = {"rss_gb": _rss_process_tree_gb()}

    def sampler():
        while not stop.is_set():
            peak["rss_gb"] = max(peak["rss_gb"], _rss_process_tree_gb())
            time.sleep(sample_interval_s)

    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    start = time.perf_counter()
    try:
        result = fn()
    finally:
        elapsed = time.perf_counter() - start
        stop.set()
        t.join(timeout=1.0)
        peak["rss_gb"] = max(peak["rss_gb"], _rss_process_tree_gb())
    return result, elapsed, peak["rss_gb"]


def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _logical_md5(df: pd.DataFrame) -> str:
    """Hash stable logical content, rounded so <1e-6 float jitter does not matter."""
    canon = df.sort_values(ID_COL).reset_index(drop=True)
    canon = canon.reindex(columns=sorted(canon.columns))
    float_cols = canon.select_dtypes(include=["float32", "float64"]).columns
    canon[float_cols] = canon[float_cols].round(LOGICAL_HASH_DECIMALS)
    values = pd.util.hash_pandas_object(canon, index=False).values.tobytes()
    return hashlib.md5(values).hexdigest()


def _load_output(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing output: {path}")
    return pd.read_parquet(path)


def _summarize_output(path: Path, df: pd.DataFrame) -> dict:
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "actigraphy_rows": int(df["act_enmo_mean"].notna().sum()),
        "raw_file_md5": _file_md5(path),
        "logical_md5_round9": _logical_md5(df),
    }


def _compare_outputs(cpu: pd.DataFrame, spark: pd.DataFrame) -> dict:
    cols = actigraphy_feature_columns()
    a = cpu.set_index(ID_COL)[cols].sort_index()
    b = spark.set_index(ID_COL)[cols].sort_index()

    diff = (a - b).to_numpy(dtype=float)
    valid = ~np.isnan(diff)
    max_abs = float(np.abs(diff[valid]).max()) if valid.any() else 0.0
    nan_equal = bool(a.isna().equals(b.isna()))
    id_equal = bool(a.index.equals(b.index))
    equivalent = id_equal and nan_equal and max_abs < EQUIV_THRESHOLD
    return {
        "id_sets_equal": id_equal,
        "nan_positions_equal": nan_equal,
        "max_abs_diff_non_nan": max_abs,
        "equivalence_threshold": EQUIV_THRESHOLD,
        "equivalent_to_reference": equivalent,
        "valid_cells_compared": int(valid.sum()),
        "nan_cells": int(np.isnan(a.to_numpy(dtype=float)).sum()),
    }


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


def _log_mlflow(mlflow, row: dict):
    if mlflow is None:
        return
    with mlflow.start_run(run_name=f"feature_stage_{row['backend']}"):
        mlflow.log_params({
            "stage": "feature_preprocessing",
            "feat_version": row["feat_version"],
            "backend": row["backend"],
            "tool": row["tool"],
            "spark_master": row.get("spark_master") or "",
            "spark_driver_memory": row.get("spark_driver_memory") or "",
            "logical_hash_decimals": LOGICAL_HASH_DECIMALS,
        })
        for key, value in row.items():
            if isinstance(value, (int, float)) and not (
                isinstance(value, float) and math.isnan(value)
            ):
                mlflow.log_metric(key, float(value))


def _backend_rows(args) -> list:
    rows = []
    backends = [b.strip() for b in args.backends.split(",") if b.strip()]
    valid = {"pandas", "spark"}
    invalid = sorted(set(backends) - valid)
    if invalid:
        raise ValueError(f"invalid backend(s): {invalid}; expected pandas,spark")

    for backend in backends:
        if backend == "pandas":
            path = FEAT_V2_CPU_FILE
            if args.skip_build:
                wall_time_s = float("nan")
                peak_rss_gb = float("nan")
            else:
                _, wall_time_s, peak_rss_gb = _measure(
                    lambda: build_feat_v2_cpu(save=True),
                    sample_interval_s=args.sample_interval_s,
                )
            df = _load_output(path)
            row = {
                "feat_version": "feat_v2",
                "backend": "pandas",
                "tool": "pandas_streaming",
                "spark_master": "",
                "spark_driver_memory": "",
                "wall_time_s": wall_time_s,
                "peak_rss_gb_process_tree": peak_rss_gb,
                "consistency": "reference",
            }
            row.update(_summarize_output(path, df))
            rows.append(row)

        if backend == "spark":
            path = FEAT_V2_SPARK_FILE
            if args.skip_build:
                wall_time_s = float("nan")
                peak_rss_gb = float("nan")
            else:
                _, wall_time_s, peak_rss_gb = _measure(
                    lambda: build_feat_v2_spark(save=True, master=args.spark_master),
                    sample_interval_s=args.sample_interval_s,
                )
            df = _load_output(path)
            row = {
                "feat_version": "feat_v2",
                "backend": "spark",
                "tool": "spark_applyInPandas",
                "spark_master": args.spark_master,
                "spark_driver_memory": SPARK_CONFIG.get("spark.driver.memory", ""),
                "wall_time_s": wall_time_s,
                "peak_rss_gb_process_tree": peak_rss_gb,
                "consistency": "pending",
            }
            row.update(_summarize_output(path, df))
            rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(description="P1 Table 1: feat_v2 feature-stage comparison")
    ap.add_argument("--backends", default="pandas,spark",
                    help="comma list of backends to build: pandas,spark")
    ap.add_argument("--skip-build", action="store_true",
                    help="read existing feat_v2 outputs instead of rebuilding them")
    ap.add_argument("--spark-master", default="local[8]",
                    help="Spark master for the Spark backend (default: local[8])")
    ap.add_argument("--sample-interval-s", type=float, default=0.1,
                    help="RSS sampling interval for process-tree memory measurement")
    ap.add_argument("--mlflow", action="store_true", help="log rows to MLflow")
    ap.add_argument("--log-existing-report", action="store_true",
                    help="log the existing report CSV to MLflow without rebuilding or rewriting it")
    args = ap.parse_args()

    mlflow = _setup_mlflow(args.mlflow)
    if args.log_existing_report:
        if not OUT_FILE.exists():
            raise FileNotFoundError(f"missing report: {OUT_FILE}")
        df = pd.read_csv(OUT_FILE)
        for _, row in df.iterrows():
            _log_mlflow(mlflow, row.to_dict())
        logger.info("logged existing report rows from %s", OUT_FILE)
        return 0

    rows = _backend_rows(args)

    cpu = _load_output(FEAT_V2_CPU_FILE)
    spark = _load_output(FEAT_V2_SPARK_FILE)
    comparison = _compare_outputs(cpu, spark)

    for row in rows:
        if row["backend"] == "spark":
            row.update(comparison)
            row["consistency"] = (
                f"max_abs_diff={comparison['max_abs_diff_non_nan']:.3e}; "
                f"nan_equal={comparison['nan_positions_equal']}"
            )
        else:
            row.update({
                "id_sets_equal": True,
                "nan_positions_equal": True,
                "max_abs_diff_non_nan": 0.0,
                "equivalence_threshold": EQUIV_THRESHOLD,
                "equivalent_to_reference": True,
                "valid_cells_compared": comparison["valid_cells_compared"],
                "nan_cells": comparison["nan_cells"],
            })
        _log_mlflow(mlflow, row)

    df = pd.DataFrame(rows)
    view_cols = [
        "feat_version", "backend", "tool", "spark_master", "wall_time_s",
        "peak_rss_gb_process_tree", "rows", "cols", "actigraphy_rows",
        "logical_md5_round9", "consistency",
    ]
    print("\n===== P1 Table 1 — feature stage feat_v2 =====")
    print(df[view_cols].to_string(index=False))
    if args.skip_build:
        logger.info("skip-build: not overwriting %s (run without --skip-build to refresh it)", OUT_FILE)
    else:
        write_csv(df, OUT_FILE)
        logger.info("wrote %s", OUT_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
