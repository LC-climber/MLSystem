"""
W3 A6: Spark Parallelism Scan for feat_v2 Feature Preprocessing

Runs the Spark actigraphy preprocessing path under several local masters and
compares every output to the canonical pandas feat_v2 reference. This is the
ablation requested in 03_plan_p1_v2.md §7.3 A6:

  Spark local[4] / local[8] / local[20] parallelism scan, with a time curve.

The script writes after every master so long Spark runs can be resumed or audited
even if a later configuration fails.

Usage:
  python -m src.experiments.run_p1_spark_parallelism
  python -m src.experiments.run_p1_spark_parallelism --masters local[4],local[8],local[20] --mlflow
"""

import argparse
import math
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.config import P1_REPORTS_DIR, SPARK_CONFIG
from src.data.actigraphy_features import FEAT_V2_CPU_FILE, FEAT_V2_SPARK_FILE
from src.data.preprocess_actigraphy_spark import build_feat_v2_spark
from src.experiments.run_p1_feature_stage import (
    EQUIV_THRESHOLD,
    LOGICAL_HASH_DECIMALS,
    _compare_outputs,
    _load_output,
    _measure,
    _setup_mlflow,
    _summarize_output,
)
from src.utils.io import write_csv
from src.utils.logging import get_logger
from src.utils.spark import stop_spark

logger = get_logger(__name__)

OUT_FILE = P1_REPORTS_DIR / "p1_spark_parallelism_feat_v2.csv"
DEFAULT_MASTERS = "local[4],local[8],local[20]"


def _parse_local_cores(master: str) -> int:
    """Extract N from local[N]; returns 0 for non-local or wildcard masters."""
    m = re.fullmatch(r"local\[(\d+)\]", master)
    return int(m.group(1)) if m else 0


def _empty_result(master: str) -> dict:
    return {
        "stage": "W3_A6_spark_parallelism",
        "feat_version": "feat_v2",
        "backend": "spark",
        "tool": "spark_applyInPandas",
        "spark_master": master,
        "local_cores": _parse_local_cores(master),
        "spark_driver_memory": SPARK_CONFIG.get("spark.driver.memory", ""),
        "spark_executor_memory": SPARK_CONFIG.get("spark.executor.memory", ""),
        "spark_shuffle_partitions": SPARK_CONFIG.get("spark.sql.shuffle.partitions", ""),
        "logical_hash_decimals": LOGICAL_HASH_DECIMALS,
        "equivalence_threshold": EQUIV_THRESHOLD,
        "status": "pending",
        "wall_time_s": math.nan,
        "peak_rss_gb_process_tree": math.nan,
        "rows": math.nan,
        "cols": math.nan,
        "actigraphy_rows": math.nan,
        "raw_file_md5": "",
        "logical_md5_round9": "",
        "id_sets_equal": False,
        "nan_positions_equal": False,
        "max_abs_diff_non_nan": math.nan,
        "equivalent_to_reference": False,
        "valid_cells_compared": math.nan,
        "nan_cells": math.nan,
        "consistency": "not_run",
        "error_message": "",
    }


def _log_mlflow(mlflow, row: dict) -> None:
    if mlflow is None:
        return
    run_name = f"spark_parallelism_{row['spark_master'].replace('[', '_').replace(']', '')}"
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({
            "stage": row["stage"],
            "feat_version": row["feat_version"],
            "backend": row["backend"],
            "tool": row["tool"],
            "spark_master": row["spark_master"],
            "local_cores": row["local_cores"],
            "spark_driver_memory": row["spark_driver_memory"],
            "spark_executor_memory": row["spark_executor_memory"],
            "spark_shuffle_partitions": row["spark_shuffle_partitions"],
            "status": row["status"],
            "logical_hash_decimals": LOGICAL_HASH_DECIMALS,
        })
        for key, value in row.items():
            if isinstance(value, (int, float)) and not (
                isinstance(value, float) and math.isnan(value)
            ):
                mlflow.log_metric(key, float(value))


def _scan_one(master: str, cpu: pd.DataFrame, sample_interval_s: float) -> dict:
    row = _empty_result(master)
    logger.info("A6 Spark parallelism scan: running %s", master)
    try:
        _, wall_time_s, peak_rss_gb = _measure(
            lambda: build_feat_v2_spark(save=True, stop=True, master=master),
            sample_interval_s=sample_interval_s,
        )
        spark = _load_output(FEAT_V2_SPARK_FILE)
        comparison = _compare_outputs(cpu, spark)
        row.update({
            "status": "finished",
            "wall_time_s": wall_time_s,
            "peak_rss_gb_process_tree": peak_rss_gb,
            "consistency": (
                f"max_abs_diff={comparison['max_abs_diff_non_nan']:.3e}; "
                f"nan_equal={comparison['nan_positions_equal']}"
            ),
        })
        row.update(_summarize_output(FEAT_V2_SPARK_FILE, spark))
        row.update(comparison)
    except Exception as exc:
        row.update({
            "status": "failed",
            "error_message": f"{type(exc).__name__}: {exc}",
            "consistency": "failed",
        })
        logger.exception("A6 run failed for %s", master)
    finally:
        stop_spark()
    return row


def _write_report(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df = df.sort_values(["local_cores", "spark_master"], kind="stable")
    write_csv(df, OUT_FILE)
    return df


def main() -> int:
    ap = argparse.ArgumentParser(description="W3 A6: Spark local parallelism scan for feat_v2")
    ap.add_argument("--masters", default=DEFAULT_MASTERS,
                    help=f"comma list of Spark masters (default: {DEFAULT_MASTERS})")
    ap.add_argument("--sample-interval-s", type=float, default=0.1,
                    help="RSS sampling interval for process-tree memory measurement")
    ap.add_argument("--mlflow", action="store_true", help="log rows to MLflow")
    ap.add_argument("--log-existing-report", action="store_true",
                    help="log the existing report CSV to MLflow without rebuilding")
    args = ap.parse_args()

    masters = [m.strip() for m in args.masters.split(",") if m.strip()]
    if not masters:
        raise ValueError("--masters must contain at least one Spark master")

    mlflow = _setup_mlflow(args.mlflow)
    if args.log_existing_report:
        if not OUT_FILE.exists():
            raise FileNotFoundError(f"missing report: {OUT_FILE}")
        df = pd.read_csv(OUT_FILE)
        for _, row in df.iterrows():
            _log_mlflow(mlflow, row.to_dict())
        logger.info("logged existing A6 report rows from %s", OUT_FILE)
        return 0

    cpu = _load_output(FEAT_V2_CPU_FILE)
    rows = []
    for master in masters:
        row = _scan_one(master, cpu, args.sample_interval_s)
        rows.append(row)
        _write_report(rows)
        _log_mlflow(mlflow, row)
        logger.info("A6 partial report updated: %s", OUT_FILE)

    df = _write_report(rows)
    view_cols = [
        "spark_master", "status", "wall_time_s", "peak_rss_gb_process_tree",
        "rows", "cols", "actigraphy_rows", "logical_md5_round9", "consistency",
    ]
    print("\n===== W3 A6 — Spark parallelism feat_v2 =====")
    print(df[view_cols].to_string(index=False))

    failed = df["status"].ne("finished").any()
    unequal = df["equivalent_to_reference"].ne(True).any()
    return 1 if failed or unequal else 0


if __name__ == "__main__":
    sys.exit(main())
