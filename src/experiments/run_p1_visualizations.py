"""
W3 P1 Visualization Runner

Creates publication/PPT-ready figures from the completed P1 reports without
retraining models.

Outputs (SVG + PNG) under reports/figures/:
  - p1_table2_metric_bars
  - p1_system_costs
  - p1_a6_spark_parallelism
  - p1_a5_coverage
  - p1_confusion_sklearn_lr
  - p1_feature_lineage

Usage:
  python -m src.experiments.run_p1_visualizations
"""

import argparse
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# The home config dir can be read-only under sandboxed runs.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mlsystem-matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src.config import N_SPLITS, REPORTS_DIR, SEED, TARGET_CLASSES
from src.data.constants import ID_COL, TARGET_COL
from src.data.feature_engineering import (
    get_feature_matrix_columns,
    load_feat_v1,
    load_feat_v2,
    make_preprocessing_pipeline,
)
from src.data.splits import get_fold_indices, load_fold_assignment
from src.models.sklearn_baselines import SklearnLogisticRegression
from src.utils.logging import get_logger
from src.utils.reproducibility import set_seed

logger = get_logger(__name__)

FIGURES_DIR = REPORTS_DIR / "figures"
TABLE2_FILE = REPORTS_DIR / "p1_systemwise_table2.csv"
A6_FILE = REPORTS_DIR / "p1_spark_parallelism_feat_v2.csv"
A5_COVERAGE_FILE = REPORTS_DIR / "p1_ablation_a5_coverage.csv"
A5_FOLD_FILE = REPORTS_DIR / "p1_ablation_a5_fold_coverage.csv"

SYSTEM_COLORS = {
    "sklearn": "#4C78A8",
    "spark": "#E45756",
    "pytorch": "#54A24B",
}
FEATURE_COLORS = {
    "feat_v1": "#4C78A8",
    "feat_v2": "#F58518",
}


def _setup_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.8,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.frameon": False,
        "savefig.bbox": "tight",
    })


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")


def _load_reports() -> dict[str, pd.DataFrame]:
    for path in [TABLE2_FILE, A6_FILE, A5_COVERAGE_FILE, A5_FOLD_FILE]:
        _require_file(path)
    return {
        "table2": pd.read_csv(TABLE2_FILE),
        "a6": pd.read_csv(A6_FILE),
        "a5": pd.read_csv(A5_COVERAGE_FILE),
        "a5_fold": pd.read_csv(A5_FOLD_FILE),
    }


def _save(fig, stem: str, formats: list[str]) -> list[Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for fmt in formats:
        path = FIGURES_DIR / f"{stem}.{fmt}"
        kwargs = {"dpi": 180} if fmt == "png" else {}
        fig.savefig(path, **kwargs)
        paths.append(path)
    plt.close(fig)
    logger.info("wrote %s", ", ".join(str(p) for p in paths))
    return paths


def _config_order(df: pd.DataFrame) -> list[tuple[str, str]]:
    return [
        ("sklearn", "lr"), ("spark", "lr"), ("pytorch", "lr"),
        ("sklearn", "mlp"), ("spark", "mlp"), ("pytorch", "mlp"),
    ]


def plot_table2_metric_bars(table2: pd.DataFrame, formats: list[str]) -> list[Path]:
    metrics = [
        ("macro_f1_mean", "Macro-F1"),
        ("qwk_mean", "QWK"),
        ("balanced_accuracy_mean", "Balanced Acc."),
    ]
    order = _config_order(table2)
    labels = [f"{s}\n{a.upper()}" for s, a in order]
    x = np.arange(len(order))
    width = 0.36

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), sharey=True)
    for ax, (metric, title) in zip(axes, metrics):
        for j, feature in enumerate(["feat_v1", "feat_v2"]):
            vals = []
            for system, algo in order:
                row = table2[
                    (table2["feature"] == feature)
                    & (table2["cohort"] == "all")
                    & (table2["system"] == system)
                    & (table2["algo"] == algo)
                ]
                vals.append(float(row[metric].iloc[0]))
            offset = (j - 0.5) * width
            ax.bar(
                x + offset,
                vals,
                width=width,
                label=feature.replace("feat_", "feat "),
                color=FEATURE_COLORS[feature],
                alpha=0.9,
            )
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0.0, 0.5)
        ax.axhline(0.35, color="#777777", linewidth=0.8, linestyle="--", alpha=0.5)
    axes[0].set_ylabel("5-fold mean")
    axes[-1].legend(loc="upper right")
    fig.suptitle("P1 Table 2: model quality by system, algorithm, and feature set", y=1.02)
    fig.tight_layout()
    return _save(fig, "p1_table2_metric_bars", formats)


def plot_system_costs(table2: pd.DataFrame, formats: list[str]) -> list[Path]:
    df = table2[(table2["feature"] == "feat_v2") & (table2["cohort"] == "all")].copy()
    df["_order"] = df.apply(
        lambda r: _config_order(df).index((r["system"], r["algo"])), axis=1
    )
    df = df.sort_values("_order")
    labels = [f"{r.system}\n{r.algo.upper()}" for r in df.itertuples()]
    colors = [SYSTEM_COLORS[s] for s in df["system"]]
    x = np.arange(len(df))

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2))
    axes[0].bar(x, df["train_time_s_mean"], color=colors, alpha=0.9)
    axes[0].set_title("Training time")
    axes[0].set_ylabel("seconds / fold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)

    axes[1].bar(x, df["inference_latency_us_mean"], color=colors, alpha=0.9)
    axes[1].set_title("Single-row inference latency")
    axes[1].set_ylabel("microseconds (log scale)")
    axes[1].set_yscale("log")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)

    handles = [
        plt.Line2D([0], [0], color=color, lw=7, label=system)
        for system, color in SYSTEM_COLORS.items()
    ]
    axes[1].legend(handles=handles, loc="upper left")
    fig.suptitle("P1 system cost on feat_v2/all", y=1.02)
    fig.tight_layout()
    return _save(fig, "p1_system_costs", formats)


def plot_a6_spark_parallelism(a6: pd.DataFrame, formats: list[str]) -> list[Path]:
    df = a6.sort_values("local_cores")
    x = df["local_cores"].to_numpy()

    fig, ax1 = plt.subplots(figsize=(7.2, 4.2))
    ax2 = ax1.twinx()
    ax1.plot(x, df["wall_time_s"], marker="o", color="#4C78A8", linewidth=2.4,
             label="wall time")
    ax2.plot(x, df["peak_rss_gb_process_tree"], marker="s", color="#E45756",
             linewidth=2.4, label="peak RSS")
    ax1.set_title("A6: Spark local parallelism scan")
    ax1.set_xlabel("Spark local cores")
    ax1.set_ylabel("wall time (s)", color="#4C78A8")
    ax2.set_ylabel("peak process-tree RSS (GB)", color="#E45756")
    ax1.set_xticks(x)
    ax1.grid(True, axis="y")
    ax2.grid(False)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper left")
    fig.tight_layout()
    return _save(fig, "p1_a6_spark_parallelism", formats)


def plot_a5_coverage(a5: pd.DataFrame, fold: pd.DataFrame, formats: list[str]) -> list[Path]:
    coverage = float(a5["coverage_labeled_fraction"].iloc[0])
    total_coverage = float(a5["coverage_total_fraction"].iloc[0])
    x = fold["fold"].to_numpy()

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2))
    axes[0].bar(x, fold["coverage_labeled_fraction"] * 100, color="#72B7B2", alpha=0.9)
    axes[0].axhline(coverage * 100, color="#4C78A8", linestyle="--", linewidth=1.5,
                    label=f"labeled avg {coverage:.1%}")
    axes[0].axhline(total_coverage * 100, color="#A0A0A0", linestyle=":", linewidth=1.5,
                    label=f"all rows {total_coverage:.1%}")
    axes[0].set_title("Actigraphy coverage by fold")
    axes[0].set_xlabel("fold")
    axes[0].set_ylabel("coverage (%)")
    axes[0].set_xticks(x)
    axes[0].set_ylim(0, 45)
    axes[0].legend(loc="upper right")

    class_cols = [f"actigraphy_class_{c}" for c in range(4)]
    bottom = np.zeros(len(fold))
    class_colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756"]
    for c, color in zip(range(4), class_colors):
        vals = fold[f"actigraphy_class_{c}"].to_numpy()
        axes[1].bar(x, vals, bottom=bottom, color=color, alpha=0.9, label=f"class {c}")
        bottom += vals
    axes[1].set_title("Actigraphy cohort class counts")
    axes[1].set_xlabel("fold")
    axes[1].set_ylabel("labeled rows")
    axes[1].set_xticks(x)
    axes[1].legend(loc="upper right", ncols=2)
    axes[1].annotate(
        "fold 4 has no class 3",
        xy=(4, fold.loc[fold["fold"].eq(4), "actigraphy_class_3"].iloc[0]),
        xytext=(2.8, 170),
        arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.2},
        fontsize=9,
    )
    fig.suptitle("A5: actigraphy coverage and class sparsity", y=1.02)
    fig.tight_layout()
    return _save(fig, "p1_a5_coverage", formats)


def _oof_sklearn_lr(feat_df: pd.DataFrame, assignment: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Out-of-fold predictions for representative confusion matrices."""
    labeled_ids = set(assignment[ID_COL])
    feat_df = feat_df[feat_df[ID_COL].isin(labeled_ids)].reset_index(drop=True)
    feat_cols = get_feature_matrix_columns(feat_df)
    x_all = feat_df[feat_cols].to_numpy(dtype="float64")
    y_all = feat_df[TARGET_COL].astype(int).to_numpy()

    y_true, y_pred = [], []
    for fold in range(N_SPLITS):
        set_seed(SEED)
        train_idx, val_idx = get_fold_indices(feat_df, assignment, fold)
        pre = make_preprocessing_pipeline()
        x_train = pre.fit_transform(x_all[train_idx])
        x_val = pre.transform(x_all[val_idx])
        model = SklearnLogisticRegression(num_classes=len(TARGET_CLASSES), seed=SEED)
        model.fit(x_train, y_all[train_idx])
        pred = model.predict(x_val)
        y_true.append(y_all[val_idx])
        y_pred.append(pred)
    return np.concatenate(y_true), np.concatenate(y_pred)


def _confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    mat = np.zeros((len(TARGET_CLASSES), len(TARGET_CLASSES)), dtype=int)
    class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}
    for t, p in zip(y_true, y_pred):
        mat[class_to_idx[int(t)], class_to_idx[int(p)]] += 1
    return mat


def plot_confusion_sklearn_lr(formats: list[str]) -> list[Path]:
    assignment = load_fold_assignment()
    cases = [
        ("feat_v1/all", load_feat_v1()),
        ("feat_v2/all", load_feat_v2()),
    ]
    cms = []
    for label, feat in cases:
        logger.info("building out-of-fold confusion matrix for sklearn LR %s", label)
        y_true, y_pred = _oof_sklearn_lr(feat, assignment)
        cms.append((label, _confusion_matrix(y_true, y_pred)))

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), sharey=True)
    vmax = max(cm.max() for _, cm in cms)
    for ax, (label, cm) in zip(axes, cms):
        row_sum = cm.sum(axis=1, keepdims=True)
        pct = np.divide(cm, row_sum, out=np.zeros_like(cm, dtype=float), where=row_sum != 0)
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=vmax)
        ax.set_title(label)
        ax.set_xlabel("predicted class")
        ax.set_xticks(range(len(TARGET_CLASSES)))
        ax.set_xticklabels(TARGET_CLASSES)
        ax.set_yticks(range(len(TARGET_CLASSES)))
        ax.set_yticklabels(TARGET_CLASSES)
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                color = "white" if cm[i, j] > vmax * 0.55 else "#222222"
                ax.text(j, i, f"{cm[i, j]}\n{pct[i, j] * 100:.0f}%",
                        ha="center", va="center", fontsize=8, color=color)
    axes[0].set_ylabel("true class")
    fig.suptitle("Representative out-of-fold confusion matrices: sklearn LR", y=1.02)
    fig.tight_layout()
    return _save(fig, "p1_confusion_sklearn_lr", formats)


def _box(ax, xy, text, color, width=1.55, height=0.42):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.025,rounding_size=0.035",
        linewidth=1.1,
        edgecolor=color,
        facecolor=color,
        alpha=0.14,
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center",
            fontsize=9.5, color="#222222")
    return patch


def _arrow(ax, start, end, color="#555555"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=11,
                                 linewidth=1.2, color=color))


def plot_feature_lineage(formats: list[str]) -> list[Path]:
    fig, ax = plt.subplots(figsize=(12.0, 4.4))
    ax.set_axis_off()
    ax.set_xlim(0, 10.9)
    ax.set_ylim(0, 4.0)

    ax.text(0.15, 3.35, "pandas streaming", fontsize=11, fontweight="bold",
            color="#4C78A8")
    ax.text(0.15, 1.35, "Spark applyInPandas", fontsize=11, fontweight="bold",
            color="#E45756")

    pandas_boxes = [
        ((1.25, 3.05), "Hive partitions\nid=*"),
        ((3.2, 3.05), "one participant\nat a time"),
        ((5.15, 3.05), "pandas reducer\n47 act_* cols"),
        ((7.1, 3.05), "feat_v2__cpu\nreference"),
        ((9.05, 3.05), "Table 1\nbaseline"),
    ]
    spark_boxes = [
        ((1.25, 1.05), "Parquet dataset\n315M rows"),
        ((3.2, 1.05), "Spark groupBy(id)\nshuffle"),
        ((5.15, 1.05), "same pandas reducer\ninside workers"),
        ((7.1, 1.05), "feat_v2__spark\ncandidate"),
        ((9.05, 1.05), "diff/hash\ncheck"),
    ]
    for xy, text in pandas_boxes:
        _box(ax, xy, text, "#4C78A8")
    for xy, text in spark_boxes:
        _box(ax, xy, text, "#E45756")
    for boxes, color in [(pandas_boxes, "#4C78A8"), (spark_boxes, "#E45756")]:
        for (a_xy, _), (b_xy, _) in zip(boxes[:-1], boxes[1:]):
            _arrow(ax, (a_xy[0] + 1.55, a_xy[1] + 0.21), (b_xy[0], b_xy[1] + 0.21),
                   color=color)
    _arrow(ax, (7.88, 2.98), (7.88, 1.52), color="#777777")
    ax.text(8.05, 2.1, "equivalent\nmax diff < 1e-6", fontsize=9, va="center",
            color="#555555")
    ax.text(0.15, 3.78, "P1 feat_v2 actigraphy feature lineage", fontsize=13,
            fontweight="bold")
    ax.text(0.15, 0.25,
            "Finding: Spark is valuable as a distributed ETL substrate, but exact per-participant "
            "aggregation still needs algorithm-aware implementation and measured parallelism.",
            fontsize=9, color="#444444")
    fig.tight_layout()
    return _save(fig, "p1_feature_lineage", formats)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate P1 W3 visualizations")
    ap.add_argument("--formats", default="svg,png",
                    help="comma list of output formats (default: svg,png)")
    args = ap.parse_args()

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    valid = {"svg", "png", "pdf"}
    invalid = sorted(set(formats) - valid)
    if invalid:
        raise ValueError(f"unsupported formats: {invalid}; valid={sorted(valid)}")

    _setup_style()
    reports = _load_reports()
    written = []
    written += plot_table2_metric_bars(reports["table2"], formats)
    written += plot_system_costs(reports["table2"], formats)
    written += plot_a6_spark_parallelism(reports["a6"], formats)
    written += plot_a5_coverage(reports["a5"], reports["a5_fold"], formats)
    written += plot_confusion_sklearn_lr(formats)
    written += plot_feature_lineage(formats)

    print("\n===== W3 P1 visualizations =====")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
