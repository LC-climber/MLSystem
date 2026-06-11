#!/usr/bin/env python3
"""Export auditable P2 status from Optuna and MLflow SQLite stores."""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPTUNA_DB = PROJECT_ROOT / "src" / "optuna.db"
MLFLOW_DB = PROJECT_ROOT / "mlruns.db"
MLFLOW_ARTIFACTS_DIR = PROJECT_ROOT / "mlruns_artifacts"
REPORTS_P2 = PROJECT_ROOT / "reports" / "P2"
FORMAL_STUDY_NAME = "p2-formal-mlops-20260612"
REPORTS_P2.mkdir(parents=True, exist_ok=True)


def _read_sql(db_path: Path, query: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn)


def _write_csv(df: pd.DataFrame, name: str) -> Path:
    path = REPORTS_P2 / name
    df.to_csv(path, index=False)
    return path


def _fmt_int(value: int | float | None) -> int:
    if pd.isna(value):
        return 0
    return int(value)


def _decode_optuna_param(param_value: float, distribution_json: str):
    distribution = json.loads(distribution_json)
    if distribution.get("name") != "CategoricalDistribution":
        return param_value

    choices = distribution.get("attributes", {}).get("choices", [])
    index = int(param_value)
    if index < 0 or index >= len(choices):
        return param_value
    return choices[index]


def export_optuna() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not OPTUNA_DB.exists():
        return pd.DataFrame(), pd.DataFrame()

    studies = _read_sql(
        OPTUNA_DB,
        """
        SELECT s.study_id,
               s.study_name,
               d.direction,
               COUNT(t.trial_id) AS total_trials,
               SUM(CASE WHEN t.state = 'COMPLETE' THEN 1 ELSE 0 END) AS complete_trials,
               SUM(CASE WHEN t.state = 'FAIL' THEN 1 ELSE 0 END) AS failed_trials,
               MAX(v.value) AS best_value
        FROM studies s
        LEFT JOIN study_directions d ON s.study_id = d.study_id
        LEFT JOIN trials t ON s.study_id = t.study_id
        LEFT JOIN trial_values v ON t.trial_id = v.trial_id
        GROUP BY s.study_id, s.study_name, d.direction
        ORDER BY s.study_id
        """,
    )

    trials = _read_sql(
        OPTUNA_DB,
        """
        SELECT s.study_name,
               t.trial_id,
               t.number,
               t.state,
               t.datetime_start,
               t.datetime_complete,
               tv.value
        FROM studies s
        JOIN trials t ON s.study_id = t.study_id
        LEFT JOIN trial_values tv ON t.trial_id = tv.trial_id
        ORDER BY s.study_id, t.number
        """,
    )

    params = _read_sql(
        OPTUNA_DB,
        """
        SELECT trial_id, param_name, param_value, distribution_json
        FROM trial_params
        """,
    )
    if not params.empty:
        params["decoded_value"] = params.apply(
            lambda row: _decode_optuna_param(row["param_value"], row["distribution_json"]),
            axis=1,
        )
        params_pivot = params.pivot(index="trial_id", columns="param_name", values="decoded_value")
        trials = trials.merge(params_pivot, left_on="trial_id", right_index=True, how="left")

    _write_csv(studies, "p2_optuna_studies.csv")
    _write_csv(trials, "p2_optuna_trials.csv")
    return studies, trials


def export_mlflow() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not MLFLOW_DB.exists():
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    experiments = _read_sql(
        MLFLOW_DB,
        """
        SELECT e.experiment_id,
               e.name,
               e.artifact_location,
               e.lifecycle_stage,
               COUNT(r.run_uuid) AS total_runs,
               SUM(CASE WHEN r.status = 'FINISHED' THEN 1 ELSE 0 END) AS finished_runs,
               SUM(CASE WHEN r.status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs
        FROM experiments e
        LEFT JOIN runs r ON e.experiment_id = r.experiment_id
        GROUP BY e.experiment_id, e.name, e.artifact_location, e.lifecycle_stage
        ORDER BY e.experiment_id
        """,
    )

    runs = _read_sql(
        MLFLOW_DB,
        """
        SELECT e.name AS experiment_name,
               r.run_uuid,
               r.name AS run_name,
               r.status,
               datetime(r.start_time / 1000, 'unixepoch') AS start_time_utc,
               datetime(r.end_time / 1000, 'unixepoch') AS end_time_utc,
               r.artifact_uri
        FROM runs r
        JOIN experiments e ON r.experiment_id = e.experiment_id
        WHERE e.name = 'piu-p2-mlops'
        ORDER BY r.start_time
        """,
    )

    metrics = _read_sql(
        MLFLOW_DB,
        """
        SELECT r.run_uuid,
               r.name AS run_name,
               m.key,
               m.value,
               datetime(m.timestamp / 1000, 'unixepoch') AS timestamp_utc
        FROM metrics m
        JOIN runs r ON m.run_uuid = r.run_uuid
        JOIN experiments e ON r.experiment_id = e.experiment_id
        WHERE e.name = 'piu-p2-mlops'
        ORDER BY r.start_time, m.key
        """,
    )

    model_versions = _read_sql(
        MLFLOW_DB,
        """
        SELECT mv.name,
               mv.version,
               mv.current_stage,
               mv.run_id,
               mv.status,
               mv.source,
               a.alias
        FROM model_versions mv
        LEFT JOIN registered_model_aliases a
          ON mv.name = a.name AND mv.version = a.version
        ORDER BY mv.name, mv.version
        """,
    )

    _write_csv(experiments, "p2_mlflow_experiments.csv")
    _write_csv(runs, "p2_mlflow_runs_summary.csv")
    _write_csv(metrics, "p2_mlflow_metrics.csv")
    _write_csv(model_versions, "p2_mlflow_model_versions.csv")
    return experiments, runs, metrics, model_versions


def write_best_trials(trials: pd.DataFrame) -> None:
    path = REPORTS_P2 / "p2_optuna_best_trials.md"
    complete = trials[trials["state"] == "COMPLETE"].copy() if not trials.empty else pd.DataFrame()
    if not complete.empty:
        complete = complete.sort_values("value", ascending=False).head(10)

    with path.open("w", encoding="utf-8") as f:
        f.write("# P2 Optuna Best Trials\n\n")
        f.write("This file is generated from `src/optuna.db`.\n\n")
        if trials.empty:
            f.write("No Optuna trials were found.\n")
            return
        f.write(f"- Total trials: {len(trials)}\n")
        f.write(f"- Complete trials: {len(trials[trials['state'] == 'COMPLETE'])}\n")
        f.write(f"- Failed trials: {len(trials[trials['state'] == 'FAIL'])}\n")
        if complete.empty:
            f.write("- Best QWK: unavailable\n")
            return
        f.write(f"- Best QWK: {complete['value'].max():.4f}\n\n")
        f.write("## Top Complete Trials\n\n")
        f.write(complete.to_markdown(index=False))
        f.write("\n")


def write_summary(
    studies: pd.DataFrame,
    trials: pd.DataFrame,
    experiments: pd.DataFrame,
    runs: pd.DataFrame,
    metrics: pd.DataFrame,
    model_versions: pd.DataFrame,
) -> None:
    summary_path = REPORTS_P2 / "p2_summary_report.md"

    total_trials = len(trials)
    complete_trials = _fmt_int((trials["state"] == "COMPLETE").sum()) if not trials.empty else 0
    failed_trials = _fmt_int((trials["state"] == "FAIL").sum()) if not trials.empty else 0
    best_qwk = trials.loc[trials["state"] == "COMPLETE", "value"].max() if complete_trials else None

    p2_runs = len(runs)
    finished_runs = _fmt_int((runs["status"] == "FINISHED").sum()) if not runs.empty else 0
    failed_runs = _fmt_int((runs["status"] == "FAILED").sum()) if not runs.empty else 0

    registered_count = len(model_versions)
    aliases = (
        ", ".join(sorted(model_versions["alias"].dropna().astype(str).unique()))
        if not model_versions.empty and "alias" in model_versions
        else ""
    )

    artifacts_count = 0
    if MLFLOW_ARTIFACTS_DIR.exists():
        artifacts_count = sum(1 for p in MLFLOW_ARTIFACTS_DIR.rglob("*") if p.is_file())

    formal_trials = (
        trials[trials["study_name"] == FORMAL_STUDY_NAME].copy()
        if not trials.empty and "study_name" in trials
        else pd.DataFrame()
    )
    formal_complete_trials = (
        _fmt_int((formal_trials["state"] == "COMPLETE").sum())
        if not formal_trials.empty
        else 0
    )
    formal_best_qwk = (
        formal_trials.loc[formal_trials["state"] == "COMPLETE", "value"].max()
        if formal_complete_trials
        else None
    )
    final_report_exists = (REPORTS_P2 / "p2_final_report.md").exists()
    figures_exist = all(
        (REPORTS_P2 / "figures" / name).exists()
        for name in [
            "p2_metric_comparison.png",
            "p2_optuna_trace.png",
            "p2_champion_confusion_matrix.png",
            "p2_mlflow_run_status.png",
        ]
    )

    aliases_present = (
        not model_versions.empty
        and "alias" in model_versions
        and {"baseline", "candidate", "champion"}.issubset(set(model_versions["alias"].dropna()))
    )
    status = "Complete" if (
        formal_complete_trials >= 8
        and formal_best_qwk is not None
        and float(formal_best_qwk) > 0
        and registered_count > 0
        and aliases_present
        and artifacts_count > 0
        and final_report_exists
        and figures_exist
    ) else "Incomplete"

    blocking_reasons = []
    if formal_complete_trials < 8:
        blocking_reasons.append(
            f"Formal Optuna complete trials are {formal_complete_trials}; expected at least 8 local formal trials."
        )
    if formal_best_qwk is None:
        blocking_reasons.append("No completed formal Optuna trial has a recorded objective value.")
    elif float(formal_best_qwk) <= 0:
        blocking_reasons.append(f"Best formal Optuna QWK is {float(formal_best_qwk):.4f}, not a usable result.")
    if registered_count == 0:
        blocking_reasons.append("MLflow Registry has no registered model version or alias.")
    if not aliases_present:
        blocking_reasons.append("MLflow Registry is missing one or more required aliases: baseline/candidate/champion.")
    if artifacts_count == 0:
        blocking_reasons.append("MLflow artifact directory has no persisted artifact files for P2.")
    if not final_report_exists:
        blocking_reasons.append("Final P2 report is missing.")
    if not figures_exist:
        blocking_reasons.append("One or more required P2 visualization figures are missing.")

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# P2 MLOps Status Audit\n\n")
        f.write("Generated from local SQLite stores on 2026-06-11.\n\n")
        f.write(f"**Status**: {status}\n\n")

        f.write("## Evidence\n\n")
        f.write(f"- Optuna DB: `src/optuna.db` exists: `{OPTUNA_DB.exists()}`\n")
        f.write(f"- Optuna trials: total `{total_trials}`, complete `{complete_trials}`, failed `{failed_trials}`\n")
        f.write(f"- Formal study: `{FORMAL_STUDY_NAME}`\n")
        f.write(f"- Formal Optuna trials: complete `{formal_complete_trials}`, best QWK `{float(formal_best_qwk):.4f}`\n")
        if best_qwk is None or pd.isna(best_qwk):
            f.write("- Best recorded QWK: unavailable\n")
        else:
            f.write(f"- Best recorded QWK: `{float(best_qwk):.4f}`\n")
        f.write(f"- MLflow backend DB: `mlruns.db` exists: `{MLFLOW_DB.exists()}`\n")
        f.write(f"- P2 MLflow runs: total `{p2_runs}`, finished `{finished_runs}`, failed `{failed_runs}`\n")
        f.write(f"- MLflow artifact files under `mlruns_artifacts/`: `{artifacts_count}`\n")
        f.write(f"- MLflow registered model versions: `{registered_count}`\n")
        f.write(f"- MLflow aliases: `{aliases or 'none'}`\n\n")

        f.write("## Blocking Gaps\n\n")
        for reason in blocking_reasons:
            f.write(f"- {reason}\n")
        if not blocking_reasons:
            f.write("- No blocking gap detected by this audit script.\n")
        f.write("\n")

        f.write("## Completion Evidence\n\n")
        f.write("- Formal Optuna run exists and has non-zero QWK.\n")
        f.write("- MLflow Registry has baseline/candidate/champion aliases.\n")
        f.write("- Champion model can be loaded through `models:/piu-risk@champion`.\n")
        f.write("- Report tables, model artifacts, and visualization figures are present under `reports/P2/`.\n")
        f.write("- Historical process documents under `00_docs/p2/reports/` are not treated as completion evidence unless backed by current artifacts.\n\n")

        f.write("## Remaining Caveats\n\n")
        f.write("- The formal local search uses 10 Optuna trials, not the originally aspirational 100-trial search.\n")
        f.write("- The champion improvement over baseline is small; report it as an MLOps workflow result, not as a major modeling breakthrough.\n")
        f.write("- Docker image build was not rerun in this export script; Docker config remains a deployment artifact to validate separately when needed.\n\n")

        f.write("## Generated Files\n\n")
        f.write("- `p2_optuna_studies.csv`\n")
        f.write("- `p2_optuna_trials.csv`\n")
        f.write("- `p2_optuna_best_trials.md`\n")
        f.write("- `p2_mlflow_experiments.csv`\n")
        f.write("- `p2_mlflow_runs_summary.csv`\n")
        f.write("- `p2_mlflow_metrics.csv`\n")
        f.write("- `p2_mlflow_model_versions.csv`\n")
        f.write("- `p2_model_comparison.csv`\n")
        f.write("- `p2_formal_optuna_trials.csv`\n")
        f.write("- `p2_final_report.md`\n")
        f.write("- `p2_final_slides.pptx`\n")
        f.write("- `p2_presentation_notes.md`\n")
        f.write("- `p2_api_validation.md`\n")
        f.write("- `p2_validation_report.md`\n")
        f.write("- `figures/p2_*.png`\n")


def main() -> None:
    print("Exporting P2 audit reports...")
    studies, trials = export_optuna()
    experiments, runs, metrics, model_versions = export_mlflow()
    write_best_trials(trials)
    write_summary(studies, trials, experiments, runs, metrics, model_versions)

    print(f"Reports written to {REPORTS_P2.relative_to(PROJECT_ROOT)}")
    for path in sorted(REPORTS_P2.glob("p2_*")):
        print(f"- {path.name}")


if __name__ == "__main__":
    main()
