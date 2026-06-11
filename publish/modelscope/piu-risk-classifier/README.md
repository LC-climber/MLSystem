---
license: mit
tasks:
- tabular-classification
tags:
- tabular
- mental-health
- problematic-internet-use
- scikit-learn
- mlops-course-project
language:
- en
- zh
metrics:
- cohen-kappa
- macro-f1
- balanced-accuracy
---

# PIU Risk Classifier (piu-risk @ champion)

Research prototype that screens adolescent Problematic Internet Use (PIU)
severity into 4 ordinal levels: **None / Mild / Moderate / Severe**.
It is a course MLOps project artifact, **not a clinical diagnostic device**.

本模型用于青少年网络成瘾 (PIU) 风险等级的研究性筛查（4 级），为课程 MLOps
项目产物，**不可用于临床诊断**。

## Model

- Registry source: MLflow `models:/piu-risk@champion` (version 9)
- Architecture: sklearn `Pipeline(SimpleImputer(median) -> StandardScaler -> LogisticRegression)`
- Hyperparameters: `C=1.1159`, `max_iter=1000` (selected by Optuna, study `p2-formal-mlops`)
- Features: 98 numeric features (feature set `v1`)
- Training data: Child Mind Institute PIU dataset (Kaggle snapshot), 2736 labeled samples
- Final model refit on all labeled samples after 5-fold CV model selection (seed=42)

## Cross-Validation Metrics (5-fold StratifiedGroupKFold)

| Metric | Mean | Std |
| --- | ---: | ---: |
| QWK (Cohen's kappa, quadratic) | 0.3672 | 0.0189 |
| Macro-F1 | 0.3624 | 0.0134 |
| Balanced Accuracy | 0.4036 | 0.0315 |
| Log Loss | 1.1779 | 0.0400 |

## Usage

```python
from modelscope import snapshot_download
from inference import PiuRiskClassifier

model_dir = snapshot_download("ICTclimber/piu-risk-classifier")
model = PiuRiskClassifier(model_dir)

result = model.predict({
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5,
    "cgas_score": 75.0,
    "computerinternet_hoursday": 3.0,
})
print(result["label"], result["confidence"])
```

Missing fields are median-imputed by the bundled preprocessing pipeline
(statistics learned on the training fold), so sparse requests are accepted
but degrade prediction quality.

## Limitations / 限制

- Trained on a US adolescent cohort; not validated for other populations.
- Weak on the rare `Severe` class (~1% of training labels).
- Predictions must be interpreted by qualified professionals; research use only.
- PCIAT questionnaire items are deliberately excluded from features (the target
  `sii` is derived from them — using them would be label leakage).

## Citation

```bibtex
@software{piu_risk_classifier_2026,
  title  = {PIU Risk Classifier (MLsystem course project)},
  year   = {2026},
  url    = {https://modelscope.cn/models/ICTclimber/piu-risk-classifier}
}
```
