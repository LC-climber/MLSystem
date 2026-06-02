"""
Actigraphy Feature Specification (feat_v2)

Single source of truth for the per-participant actigraphy aggregates, referenced
by BOTH the pandas and Spark implementations so their outputs are column-for-column
comparable (03_plan_p1_v2.md §4: feat_v2 must ship as feat_v2__cpu and
feat_v2__spark with column-level diff < 1e-6).

Per participant, over their full actigraphy series (5-second epochs):
  - 6 sensor signals × {mean, std(ddof=1), min, max, p25, p50, p75}      = 42
  - non_wear_fraction, n_records, n_days                                  =  3
  - night_enmo_mean, day_enmo_mean  (circadian movement contrast)         =  2
                                                                          ----
                                                                            47

`time_of_day` is nanoseconds since midnight; hour = time_of_day / 3.6e12.
Night = hour >= 22 or hour < 6.

NOTE: stats are computed over ALL epochs (non-wear not masked) and non_wear_fraction
is kept as its own feature, so no information is lost and both backends aggregate
the identical row set — which keeps the equivalence check clean.
"""

from src.config import DATA_PROCESSED_DIR

# Sensor channels aggregated (battery_voltage/step excluded — device housekeeping).
SIGNALS = ["enmo", "anglez", "light", "X", "Y", "Z"]
MOMENT_STATS = ["mean", "std", "min", "max"]
QUANTILES = [0.25, 0.50, 0.75]

# time_of_day is ns since midnight.
NS_PER_HOUR = 3_600_000_000_000
NIGHT_START_HOUR = 22  # night = hour >= 22 ...
NIGHT_END_HOUR = 6     # ... or hour < 6

FEAT_V2_CPU_FILE = DATA_PROCESSED_DIR / "feat_v2__cpu__seed42.parquet"
FEAT_V2_SPARK_FILE = DATA_PROCESSED_DIR / "feat_v2__spark__seed42.parquet"


def quantile_tag(q: float) -> str:
    """0.25 -> 'p25'."""
    return f"p{int(round(q * 100))}"


def actigraphy_feature_columns() -> list:
    """Ordered list of all 47 actigraphy feature column names (act_* prefix)."""
    cols = []
    for sig in SIGNALS:
        for stat in MOMENT_STATS:
            cols.append(f"act_{sig}_{stat}")
        for q in QUANTILES:
            cols.append(f"act_{sig}_{quantile_tag(q)}")
    cols += ["act_non_wear_fraction", "act_n_records", "act_n_days",
             "act_night_enmo_mean", "act_day_enmo_mean"]
    return cols
