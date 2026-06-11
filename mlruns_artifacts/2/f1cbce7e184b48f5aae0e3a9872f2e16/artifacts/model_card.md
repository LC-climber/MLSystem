# Model Card: piu-risk (baseline)

Generated: 2026-06-11

## Intended Use

Research prototype for PIU severity screening. It is not a clinical diagnostic device.

## Model

- Role: baseline
- Feature version: v1
- Model type: logreg
- Samples: 2736
- Features: 98
- Seed: 42

## Cross-Validation Metrics

| Metric | Mean | Std |
| --- | ---: | ---: |
| QWK | 0.3773 | 0.0015 |
| Macro-F1 | 0.3707 | 0.0024 |
| Balanced Accuracy | 0.4194 | 0.0007 |
| Log Loss | 1.1752 | 0.0483 |

## Limitations

- Trained on the course project snapshot of the Kaggle Child Mind Institute PIU dataset.
- Input examples with only a few fields rely on training-set imputation for missing features.
- The model is for MLOps demonstration and research, not standalone medical decision making.
