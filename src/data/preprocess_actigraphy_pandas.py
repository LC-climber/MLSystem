"""
Actigraphy Preprocessing — pandas (single-machine reference)

Computes the feat_v2 actigraphy block (src.data.actigraphy_features) per
participant. This is the REFERENCE implementation: the Spark version
(preprocess_actigraphy_spark) must reproduce its output column-for-column
(03_plan_p1_v2.md §4: column-level diff < 1e-6).

This is also the pandas side of the P1 "where does Spark belong?" experiment —
the actigraphy stage is the one place Spark has a real shot (raw series is far
larger than the ~3000-row tabular), so this stage is timed against Spark.

MEMORY: the series is ~315M rows / 996 participants. Loading it all at once with
`pd.read_parquet(series_root)` peaks at ~36 GB (the `id` partition column alone is
~20 GB as object strings) and OOMs a 31 GiB box — see PROGRESS.md §3. Since the
dataset is already Hive-partitioned by `id`, we STREAM one participant at a time
(largest partition ~756k rows ≈ 31 MB), so peak memory stays in the tens of MB.
The sequential per-participant pass is also an honest single-machine wall-clock to
time against Spark's distributed aggregation.

Run:  python -m src.data.preprocess_actigraphy_pandas
"""

import glob
import os
import time

import pandas as pd

from src.config import SEED
from src.data.actigraphy_features import (
    SIGNALS, QUANTILES, NS_PER_HOUR, NIGHT_START_HOUR, NIGHT_END_HOUR,
    quantile_tag, actigraphy_feature_columns, FEAT_V2_CPU_FILE,
)
from src.data.constants import ID_COL, SERIES_TRAIN_DIR
from src.data.feature_engineering import load_feat_v1
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Columns actually read per partition (device-housekeeping cols step/battery_voltage/
# weekday/quarter are dropped — not in the feat_v2 spec — which keeps each read small).
_NEEDED = SIGNALS + ["non-wear_flag", "relative_date_PCIAT", "time_of_day"]


def _participant_aggregates(pdf: pd.DataFrame) -> dict:
    """The 47 actigraphy aggregates for ONE participant's series.

    Signals are cast to float64 before reducing so the moments/quantiles match
    Spark's double-precision aggregation (the parquet stores them as float32, and
    summing 300k float32 values drifts past the 1e-6 equivalence budget).
    """
    out = {}
    for sig in SIGNALS:
        s = pdf[sig].astype("float64")
        out[f"act_{sig}_mean"] = s.mean()
        out[f"act_{sig}_std"] = s.std()            # ddof=1 == Spark stddev_samp
        out[f"act_{sig}_min"] = s.min()
        out[f"act_{sig}_max"] = s.max()
        q = s.quantile(QUANTILES)                  # linear interpolation
        for qv in QUANTILES:
            out[f"act_{sig}_{quantile_tag(qv)}"] = q.loc[qv]

    out["act_non_wear_fraction"] = pdf["non-wear_flag"].astype("float64").mean()
    out["act_n_records"] = len(pdf)
    out["act_n_days"] = int(pdf["relative_date_PCIAT"].nunique())  # nunique drops NaN

    hour = pdf["time_of_day"] / NS_PER_HOUR
    is_night = (hour >= NIGHT_START_HOUR) | (hour < NIGHT_END_HOUR)
    enmo = pdf["enmo"].astype("float64")
    out["act_night_enmo_mean"] = enmo[is_night].mean()
    out["act_day_enmo_mean"] = enmo[~is_night].mean()
    return out


def aggregate_actigraphy_pandas(series_root=SERIES_TRAIN_DIR, log_every: int = 200,
                                limit: int = None) -> pd.DataFrame:
    """Per-participant actigraphy aggregates → DataFrame[id, act_*] (one row per id).

    Streams one Hive partition (= one participant) at a time so peak memory stays
    tiny (see module docstring). `limit` caps the number of participants (smoke test).
    """
    part_dirs = sorted(glob.glob(os.path.join(str(series_root), "id=*")))
    if not part_dirs:
        raise RuntimeError(
            f"No 'id=*' partitions under {series_root}; expected a Hive-partitioned "
            "dataset (id=<hash>/part-0.parquet)."
        )
    if limit is not None:
        part_dirs = part_dirs[:limit]

    rows = []
    for i, d in enumerate(part_dirs, 1):
        sid = os.path.basename(d).split("=", 1)[1]
        pdf = pd.read_parquet(d, columns=_NEEDED)  # reads the partition's part-*.parquet
        agg = _participant_aggregates(pdf)
        agg[ID_COL] = sid
        rows.append(agg)
        if i % log_every == 0 or i == len(part_dirs):
            logger.info("  aggregated %d/%d participants", i, len(part_dirs))

    feat = pd.DataFrame(rows).set_index(ID_COL)
    feat = feat.reindex(columns=actigraphy_feature_columns())
    feat.index.name = ID_COL
    return feat.reset_index()


def build_feat_v2_cpu(save: bool = True) -> pd.DataFrame:
    """feat_v1 (all rows) LEFT JOIN actigraphy block → feat_v2__cpu parquet."""
    feat_v1 = load_feat_v1()
    t0 = time.perf_counter()
    act = aggregate_actigraphy_pandas()
    agg_time = time.perf_counter() - t0
    logger.info(
        "pandas actigraphy aggregation: %d participants, %d features, %.2fs",
        len(act), len(act.columns) - 1, agg_time,
    )

    feat_v2 = feat_v1.merge(act, on=ID_COL, how="left")
    covered = feat_v2["act_enmo_mean"].notna().sum()
    logger.info(
        "feat_v2__cpu: %s (%d/%d rows have actigraphy)",
        feat_v2.shape, covered, len(feat_v2),
    )

    if save:
        FEAT_V2_CPU_FILE.parent.mkdir(parents=True, exist_ok=True)
        feat_v2.to_parquet(FEAT_V2_CPU_FILE, index=False)
        logger.info("wrote %s", FEAT_V2_CPU_FILE)
    return feat_v2


def main():
    logger.info("Building feat_v2__cpu (seed=%d)", SEED)
    build_feat_v2_cpu(save=True)


if __name__ == "__main__":
    main()
