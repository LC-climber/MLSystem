# P2 MLOps Final Report

Generated: 2026-06-11

## Status

P2 is complete for the local reproducible MLOps workflow: experiment tracking, hyperparameter search, model registry aliases, artifacts, API-compatible model packaging, and report visualizations are present.

## Experiment Setup

- Dataset: Child Mind Institute PIU local project snapshot
- Split: canonical StratifiedGroupKFold assignment, 5-fold CV
- Tracking backend: `mlruns.db`
- Artifact root: `mlruns_artifacts/`
- Optuna study: `p2-formal-mlops-20260612`
- Formal Optuna trials: 10 local trials

## Results

| model_name          | role     | feature_version   | model_type   |   n_samples |   n_features |   macro_f1_mean |   macro_f1_std |   qwk_mean |   qwk_std |   balanced_accuracy_mean |   balanced_accuracy_std |   log_loss_mean |   log_loss_std |   train_time_s_mean |   train_time_s_std |
|:--------------------|:---------|:------------------|:-------------|------------:|-------------:|----------------:|---------------:|-----------:|----------:|-------------------------:|------------------------:|----------------:|---------------:|--------------------:|-------------------:|
| baseline_logreg_v1  | baseline | v1                | logreg       |        2736 |           98 |        0.361901 |      0.0128233 |   0.365059 | 0.018499  |                 0.403557 |               0.0313831 |         1.17438 |      0.0391217 |             8.69533 |           0.631405 |
| candidate_logreg_v1 | champion | v1                | logreg       |        2736 |           98 |        0.362384 |      0.0133719 |   0.367216 | 0.0188636 |                 0.403604 |               0.0315481 |         1.17792 |      0.0399939 |             9.03726 |           0.718175 |

## Champion Decision

- Baseline: `baseline_logreg_v1`, QWK=0.3651
- Best Optuna candidate: `candidate_logreg_v1`, QWK=0.3672
- Champion: `candidate_logreg_v1`, QWK=0.3672

The champion is selected by highest 5-fold mean QWK. The improvement is small (`+0.0022` QWK), so the correct interpretation is that P2 demonstrates a complete MLOps loop rather than a major modeling breakthrough.

## Registry

- Registered model: `piu-risk`
- baseline alias: version 7
- candidate alias: version 8
- champion alias: version 9
- Champion load URI: `models:/piu-risk@champion`

## Visual Evidence

| Figure | Purpose |
| --- | --- |
| `figures/p2_metric_comparison.png` | Baseline vs candidate/champion CV metrics |
| `figures/p2_optuna_trace.png` | Trial-by-trial Optuna objective and best-so-far curve |
| `figures/p2_champion_confusion_matrix.png` | Champion CV confusion matrix |
| `figures/p2_mlflow_run_status.png` | MLflow run status summary |

## Best Optuna Trial

```json
{
  "number": 7,
  "value": 0.3672157731618791,
  "model_type": "logreg",
  "feature_version": "v1",
  "C": 1.115861961007209
}
```

## Reproduction

```bash
python -m src.experiments.run_p2_full_pipeline --trials 10 --folds 5 --study-name p2-formal-mlops-20260612
python scripts/export_p2_reports.py
```

## Caveats

- The formal search is 10 local Optuna trials rather than the earlier aspirational 100-trial plan.
- Earlier smoke/failed P2 trials remain in `src/optuna.db` and `mlruns.db` for audit history; use `p2-formal-mlops-20260612` for final reporting.
- Docker build validation was not rerun during the final experiment run.
