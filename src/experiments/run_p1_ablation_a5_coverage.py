"""
W3 A5: Actigraphy Coverage / Subset Analysis

This analysis explains why feat_v2_biosensing does not improve the main all-row
Table 2 despite adding 47 actigraphy features: only a subset has real actigraphy
coverage, and the actigraphy-only cohort is smaller and class-imbalanced.

Inputs:
  - reports/p1_systemwise_table2.csv
  - reports/p1_systemwise_feat_v2_actigraphy.csv
  - data/processed/feat_v2__cpu__seed42.parquet
  - data/splits/stratified_group_kfold_seed42.csv

Outputs:
  - reports/p1_ablation_a5_coverage.csv
  - reports/p1_ablation_a5_fold_coverage.csv

Usage:
  python -m src.experiments.run_p1_ablation_a5_coverage
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.config import REPORTS_DIR, TARGET_CLASSES
from src.data.constants import ID_COL
from src.data.feature_engineering import load_feat_v2
from src.data.splits import load_fold_assignment
from src.utils.io import write_csv
from src.utils.logging import get_logger

logger = get_logger(__name__)

TABLE2_FILE = REPORTS_DIR / "p1_systemwise_table2.csv"
ACTIGRAPHY_FILE = REPORTS_DIR / "p1_systemwise_feat_v2_actigraphy.csv"
OUT_FILE = REPORTS_DIR / "p1_ablation_a5_coverage.csv"
FOLD_OUT_FILE = REPORTS_DIR / "p1_ablation_a5_fold_coverage.csv"

METRICS = {
    "macro_f1_mean": "macro_f1",
    "qwk_mean": "qwk",
    "balanced_accuracy_mean": "balanced_accuracy",
    "train_time_s_mean": "train_time_s",
    "inference_latency_us_mean": "inference_latency_us",
}


def _load_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    return pd.read_csv(path)


def _covered_labeled_frames():
    feat_v2 = load_feat_v2()
    assignment = load_fold_assignment()
    covered_ids = set(feat_v2.loc[feat_v2["act_enmo_mean"].notna(), ID_COL])
    covered_assignment = assignment[assignment[ID_COL].isin(covered_ids)].copy()
    return feat_v2, assignment, covered_assignment


def _coverage_numbers(feat_v2: pd.DataFrame, assignment: pd.DataFrame,
                      covered_assignment: pd.DataFrame) -> dict:
    n_total = len(feat_v2)
    n_total_actigraphy = int(feat_v2["act_enmo_mean"].notna().sum())
    n_labeled = len(assignment)
    n_labeled_actigraphy = len(covered_assignment)
    fold4_class3 = int(
        ((covered_assignment["fold"] == 4) & (covered_assignment["sii"] == 3)).sum()
    )
    return {
        "n_total_rows": n_total,
        "n_total_actigraphy_rows": n_total_actigraphy,
        "coverage_total_fraction": n_total_actigraphy / n_total,
        "n_labeled_rows": n_labeled,
        "n_labeled_actigraphy_rows": n_labeled_actigraphy,
        "coverage_labeled_fraction": n_labeled_actigraphy / n_labeled,
        "actigraphy_fold4_class3_count": fold4_class3,
    }


def _fold_coverage(assignment: pd.DataFrame, covered_assignment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fold in sorted(assignment["fold"].unique()):
        all_fold = assignment[assignment["fold"] == fold]
        act_fold = covered_assignment[covered_assignment["fold"] == fold]
        row = {
            "fold": int(fold),
            "n_labeled_all": len(all_fold),
            "n_labeled_actigraphy": len(act_fold),
            "coverage_labeled_fraction": len(act_fold) / len(all_fold),
            "missing_classes_in_actigraphy": ",".join(
                str(c) for c in TARGET_CLASSES if c not in set(act_fold["sii"].astype(int))
            ),
        }
        for c in TARGET_CLASSES:
            row[f"all_class_{c}"] = int((all_fold["sii"] == c).sum())
            row[f"actigraphy_class_{c}"] = int((act_fold["sii"] == c).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def _select_protocol_rows(table2: pd.DataFrame, actigraphy: pd.DataFrame):
    v1_all = table2[(table2["feature"] == "feat_v1") & (table2["cohort"] == "all")]
    v2_all = table2[(table2["feature"] == "feat_v2") & (table2["cohort"] == "all")]
    v2_act = actigraphy[
        (actigraphy["feature"] == "feat_v2") & (actigraphy["cohort"] == "actigraphy")
    ]
    expected = {("sklearn", "lr"), ("sklearn", "mlp"), ("spark", "lr"),
                ("spark", "mlp"), ("pytorch", "lr"), ("pytorch", "mlp")}
    for name, df in [("v1/all", v1_all), ("v2/all", v2_all), ("v2/actigraphy", v2_act)]:
        got = set(zip(df["system"], df["algo"]))
        missing = expected - got
        if missing:
            raise RuntimeError(f"{name} report missing rows: {sorted(missing)}")
    return v1_all, v2_all, v2_act


def _build_metric_summary(coverage: dict, v1_all: pd.DataFrame, v2_all: pd.DataFrame,
                          v2_act: pd.DataFrame) -> pd.DataFrame:
    merged = (
        v1_all.set_index(["system", "algo"])
        .join(v2_all.set_index(["system", "algo"]), lsuffix="_v1_all", rsuffix="_v2_all")
        .join(v2_act.set_index(["system", "algo"]).add_suffix("_v2_actigraphy"))
        .reset_index()
    )

    rows = []
    for _, r in merged.iterrows():
        row = {
            "ablation": "A5_actigraphy_coverage",
            "system": r["system"],
            "algo": r["algo"],
            **coverage,
            "main_protocol": "v1/all vs v2/all: same 2736 labeled rows and original 5-fold",
            "subset_protocol": "v2/actigraphy: 996 labeled rows with actigraphy only",
            "subset_warning": (
                "supplemental only; fold 4 has zero class-3 validation samples "
                "in the actigraphy cohort"
            ),
        }
        for src, tag in [("v1_all", "v1_all"), ("v2_all", "v2_all"),
                         ("v2_actigraphy", "v2_actigraphy")]:
            for metric_col, metric_name in METRICS.items():
                row[f"{tag}_{metric_name}"] = r[f"{metric_col}_{src}"]

        for metric_col, metric_name in METRICS.items():
            row[f"delta_v2_all_minus_v1_all_{metric_name}"] = (
                r[f"{metric_col}_v2_all"] - r[f"{metric_col}_v1_all"]
            )
            row[f"delta_v2_actigraphy_minus_v2_all_{metric_name}"] = (
                r[f"{metric_col}_v2_actigraphy"] - r[f"{metric_col}_v2_all"]
            )
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    table2 = _load_required_csv(TABLE2_FILE)
    actigraphy = _load_required_csv(ACTIGRAPHY_FILE)
    feat_v2, assignment, covered_assignment = _covered_labeled_frames()
    coverage = _coverage_numbers(feat_v2, assignment, covered_assignment)
    fold_df = _fold_coverage(assignment, covered_assignment)
    v1_all, v2_all, v2_act = _select_protocol_rows(table2, actigraphy)
    summary = _build_metric_summary(coverage, v1_all, v2_all, v2_act)

    write_csv(summary, OUT_FILE)
    write_csv(fold_df, FOLD_OUT_FILE)
    logger.info("wrote %s", OUT_FILE)
    logger.info("wrote %s", FOLD_OUT_FILE)

    view = summary[[
        "system", "algo",
        "delta_v2_all_minus_v1_all_macro_f1",
        "delta_v2_all_minus_v1_all_qwk",
        "v2_actigraphy_macro_f1",
        "v2_actigraphy_qwk",
    ]].copy()
    print("\n===== W3 A5 — actigraphy coverage analysis =====")
    print(
        f"total coverage={coverage['coverage_total_fraction']:.1%} "
        f"({coverage['n_total_actigraphy_rows']}/{coverage['n_total_rows']} rows); "
        f"labeled coverage={coverage['coverage_labeled_fraction']:.1%} "
        f"({coverage['n_labeled_actigraphy_rows']}/{coverage['n_labeled_rows']} rows)"
    )
    print(fold_df.to_string(index=False))
    print(view.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
