"""
Actigraphy Preprocessing — Spark (distributed, the P1 "Spark value" experiment)

Produces feat_v2__spark to match feat_v2__cpu (03_plan_p1_v2.md §4). The actigraphy
stage (~315M rows) is the one place Spark has a real shot vs single-machine pandas —
the wall-clock / RSS comparison is the heart of P1.

WHY applyInPandas instead of native Spark agg + `percentile`:
Spark's exact `percentile` is a TypedImperativeAggregate that boxes every value into
an OpenHashMap per group. On 315M rows × 18 percentile aggregates that buffers/boxes
hundreds of millions of Doubles and dies with "GC overhead limit exceeded" even at a
12g driver heap (percentile_approx would avoid this but is NOT exact → fails the
< 1e-6 equivalence check). So we let Spark do what it's actually good at here —
SHARD the work by participant and run the *identical* pandas reducer on each shard
(reusing _participant_aggregates). Memory is bounded per group (largest ~756k rows),
and the output is bit-identical to the pandas reference by construction. This is the
canonical Spark pattern for exact per-entity aggregation.

(Finding for the report: at this scale Spark's native exact-quantile path is the
 bottleneck, not the moments — see PROGRESS.md §3.)

Run:  python -m src.data.preprocess_actigraphy_spark
"""

import time

import pandas as pd

from src.config import SEED
from src.data.actigraphy_features import (
    actigraphy_feature_columns, FEAT_V2_SPARK_FILE,
)
from src.data.constants import ID_COL, SERIES_TRAIN_DIR
from src.data.feature_engineering import load_feat_v1
from src.data.preprocess_actigraphy_pandas import _participant_aggregates, _NEEDED
from src.utils.logging import get_logger
from src.utils.spark import get_spark_session, stop_spark

logger = get_logger(__name__)

# Only these two aggregates are integer-valued; everything else is a double.
_LONG_COLS = {"act_n_records", "act_n_days"}


def _output_schema():
    """StructType for the applyInPandas result: id + 47 actigraphy columns."""
    from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
    fields = [StructField(ID_COL, StringType(), False)]
    for c in actigraphy_feature_columns():
        fields.append(StructField(c, LongType() if c in _LONG_COLS else DoubleType(), True))
    return StructType(fields)


def _agg_group(pdf: pd.DataFrame) -> pd.DataFrame:
    """One participant's rows (pandas) → one-row DataFrame of the 47 aggregates.

    Reuses the pandas reference reducer verbatim, so the Spark output is identical
    to feat_v2__cpu (NaN-skipping, linear-interp quantiles, ddof=1 std all match).
    """
    row = _participant_aggregates(pdf)
    row[ID_COL] = pdf[ID_COL].iloc[0]
    return pd.DataFrame([row])[[ID_COL] + actigraphy_feature_columns()]


def aggregate_actigraphy_spark(series_root=SERIES_TRAIN_DIR, master="local[8]"):
    """Per-participant actigraphy aggregates via Spark → pandas DataFrame[id, act_*].

    Spark shards by participant and runs the identical pandas reducer per shard
    (applyInPandas). master=local[8] is plenty here — the work is I/O + shuffle
    bound, and per-group memory is tiny; the parallelism sweep is ablation A6.
    """
    spark = get_spark_session(app_name="mlsys-p1-actigraphy", master=master)
    # Keep all-digit ids as strings (no leading-zero stripping on the join key).
    spark.conf.set("spark.sql.sources.partitionColumnTypeInference.enabled", "false")

    df = spark.read.parquet(str(series_root))  # Hive partition → restores `id` column
    if ID_COL not in df.columns:
        raise RuntimeError(f"'{ID_COL}' partition column missing from {series_root}.")

    sel = df.select(ID_COL, *_NEEDED)  # ship only the 9 columns the reducer reads
    result = sel.groupBy(ID_COL).applyInPandas(_agg_group, schema=_output_schema())
    act = result.toPandas()
    return act[[ID_COL] + actigraphy_feature_columns()]  # enforce spec order


def build_feat_v2_spark(save: bool = True, stop: bool = True):
    """feat_v1 (all rows) LEFT JOIN Spark actigraphy block → feat_v2__spark parquet."""
    feat_v1 = load_feat_v1()
    t0 = time.perf_counter()
    act = aggregate_actigraphy_spark()
    agg_time = time.perf_counter() - t0
    logger.info(
        "spark actigraphy aggregation: %d participants, %d features, %.2fs",
        len(act), len(act.columns) - 1, agg_time,
    )

    feat_v2 = feat_v1.merge(act, on=ID_COL, how="left")
    covered = feat_v2["act_enmo_mean"].notna().sum()
    logger.info(
        "feat_v2__spark: %s (%d/%d rows have actigraphy)",
        feat_v2.shape, covered, len(feat_v2),
    )

    if save:
        FEAT_V2_SPARK_FILE.parent.mkdir(parents=True, exist_ok=True)
        feat_v2.to_parquet(FEAT_V2_SPARK_FILE, index=False)
        logger.info("wrote %s", FEAT_V2_SPARK_FILE)
    if stop:
        stop_spark()
    return feat_v2


def main():
    logger.info("Building feat_v2__spark (seed=%d)", SEED)
    build_feat_v2_spark(save=True)


if __name__ == "__main__":
    main()
