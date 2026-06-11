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
| QWK | 0.3651 | 0.0185 |
| Macro-F1 | 0.3619 | 0.0128 |
| Balanced Accuracy | 0.4036 | 0.0314 |
| Log Loss | 1.1744 | 0.0391 |

## Limitations

- Trained on the course project snapshot of the Kaggle Child Mind Institute PIU dataset.
- Input examples with only a few fields rely on training-set imputation for missing features.
- The model is for MLOps demonstration and research, not standalone medical decision making.
