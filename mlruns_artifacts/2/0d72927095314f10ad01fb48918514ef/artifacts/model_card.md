# Model Card: piu-risk (candidate)

Generated: 2026-06-11

## Intended Use

Research prototype for PIU severity screening. It is not a clinical diagnostic device.

## Model

- Role: candidate
- Feature version: v1
- Model type: logreg
- Samples: 2736
- Features: 98
- Seed: 42

## Cross-Validation Metrics

| Metric | Mean | Std |
| --- | ---: | ---: |
| QWK | 0.3858 | 0.0011 |
| Macro-F1 | 0.3698 | 0.0012 |
| Balanced Accuracy | 0.4172 | 0.0022 |
| Log Loss | 1.2850 | 0.0699 |

## Limitations

- Trained on the course project snapshot of the Kaggle Child Mind Institute PIU dataset.
- Input examples with only a few fields rely on training-set imputation for missing features.
- The model is for MLOps demonstration and research, not standalone medical decision making.
