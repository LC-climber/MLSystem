# P2 MLOps Status Audit

Generated from local SQLite stores on 2026-06-11.

**Status**: Complete

## Evidence

- Optuna DB: `src/optuna.db` exists: `True`
- Optuna trials: total `30`, complete `17`, failed `11`
- Formal study: `p2-formal-mlops-20260612`
- Formal Optuna trials: complete `8`, best QWK `0.3672`
- Best recorded QWK: `0.3858`
- MLflow backend DB: `mlruns.db` exists: `True`
- P2 MLflow runs: total `58`, finished `39`, failed `19`
- MLflow artifact files under `mlruns_artifacts/`: `98`
- MLflow registered model versions: `9`
- MLflow aliases: `baseline, candidate, champion`

## Blocking Gaps

- No blocking gap detected by this audit script.

## Completion Evidence

- Formal Optuna run exists and has non-zero QWK.
- MLflow Registry has baseline/candidate/champion aliases.
- Champion model can be loaded through `models:/piu-risk@champion`.
- Report tables, model artifacts, and visualization figures are present under `reports/P2/`.
- Historical process documents under `00_docs/p2/reports/` are not treated as completion evidence unless backed by current artifacts.

## Remaining Caveats

- The formal local search uses 10 Optuna trials, not the originally aspirational 100-trial search.
- The champion improvement over baseline is small; report it as an MLOps workflow result, not as a major modeling breakthrough.
- Docker image build was not rerun in this export script; Docker config remains a deployment artifact to validate separately when needed.

## Generated Files

- `p2_optuna_studies.csv`
- `p2_optuna_trials.csv`
- `p2_optuna_best_trials.md`
- `p2_mlflow_experiments.csv`
- `p2_mlflow_runs_summary.csv`
- `p2_mlflow_metrics.csv`
- `p2_mlflow_model_versions.csv`
- `p2_model_comparison.csv`
- `p2_formal_optuna_trials.csv`
- `p2_final_report.md`
- `p2_final_slides.pptx`
- `p2_presentation_notes.md`
- `p2_api_validation.md`
- `p2_validation_report.md`
- `figures/p2_*.png`
