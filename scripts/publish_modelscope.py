"""Publish the champion model to ModelScope (魔搭社区).

Pipeline (see 00_docs/MODEL_PUBLISHING_GUIDE.md):
1. Export the champion (models:/piu-risk@champion) from the local MLflow registry
2. Package a self-contained repo folder under publish/modelscope/<repo-name>/
   (model.joblib + model card + standalone inference.py + requirements)
3. Smoke-test the packaged model with a sample request
4. Optionally upload with --upload (needs `pip install modelscope` and a token
   from https://modelscope.cn/my/myaccesstoken via env MODELSCOPE_API_TOKEN
   or a prior `modelscope login`)

Usage:
    python scripts/publish_modelscope.py                # export + package + smoke test
    python scripts/publish_modelscope.py --upload       # ... then upload to ModelScope
    python scripts/publish_modelscope.py --repo-id <owner>/<name>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import mlflow
import numpy as np
import pandas as pd
from mlflow.tracking import MlflowClient

from src.config import MODELSCOPE_REPO

MODEL_NAME = "piu-risk"
ALIAS = "champion"
PUBLISH_ROOT = PROJECT_ROOT / "publish" / "modelscope"
LABEL_NAMES = ["None", "Mild", "Moderate", "Severe"]


def export_champion(out_dir: Path) -> dict:
    """Pull the champion version's artifacts out of the local MLflow registry."""
    mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlruns.db'}")
    client = MlflowClient()

    mv = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
    run = client.get_run(mv.run_id)
    print(f"Champion: {MODEL_NAME} v{mv.version} (run {mv.run_id})")
    print(f"  {mv.description}")

    # model_bundle/<role>_<name>.joblib -> model.joblib
    bundle_dir = Path(mlflow.artifacts.download_artifacts(f"runs:/{mv.run_id}/model_bundle"))
    bundles = list(bundle_dir.glob("*.joblib"))
    if len(bundles) != 1:
        raise RuntimeError(f"Expected exactly 1 joblib bundle in {bundle_dir}, got {bundles}")
    shutil.copy2(bundles[0], out_dir / "model.joblib")

    # feature names / classes / params / CV summary
    meta_path = Path(mlflow.artifacts.download_artifacts(f"runs:/{mv.run_id}/model_metadata.json"))
    shutil.copy2(meta_path, out_dir / "model_metadata.json")
    metadata = json.loads((out_dir / "model_metadata.json").read_text())

    return {
        "version": mv.version,
        "run_id": mv.run_id,
        **metadata,  # feature_names, target_classes, summary (+ partial params)
        "params": run.data.params,  # full run params take precedence
        "metrics": run.data.metrics,
    }


def write_model_card(out_dir: Path, meta: dict, repo_id: str) -> None:
    m = meta["metrics"]
    p = meta["params"]
    card = f"""---
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

- Registry source: MLflow `models:/{MODEL_NAME}@{ALIAS}` (version {meta['version']})
- Architecture: sklearn `Pipeline(SimpleImputer(median) -> StandardScaler -> LogisticRegression)`
- Hyperparameters: `C={float(p['C']):.4f}`, `max_iter={p['max_iter']}` (selected by Optuna, study `p2-formal-mlops`)
- Features: {meta['params']['n_features']} numeric features (feature set `{p['feature_version']}`)
- Training data: Child Mind Institute PIU dataset (Kaggle snapshot), {p['n_samples']} labeled samples
- Final model refit on all labeled samples after 5-fold CV model selection (seed={p['seed']})

## Cross-Validation Metrics (5-fold StratifiedGroupKFold)

| Metric | Mean | Std |
| --- | ---: | ---: |
| QWK (Cohen's kappa, quadratic) | {m['qwk_mean']:.4f} | {m['qwk_std']:.4f} |
| Macro-F1 | {m['macro_f1_mean']:.4f} | {m['macro_f1_std']:.4f} |
| Balanced Accuracy | {m['balanced_accuracy_mean']:.4f} | {m['balanced_accuracy_std']:.4f} |
| Log Loss | {m['log_loss_mean']:.4f} | {m['log_loss_std']:.4f} |

## Usage

```python
from modelscope import snapshot_download
from inference import PiuRiskClassifier

model_dir = snapshot_download("{repo_id}")
model = PiuRiskClassifier(model_dir)

result = model.predict({{
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5,
    "cgas_score": 75.0,
    "computerinternet_hoursday": 3.0,
}})
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
@software{{piu_risk_classifier_2026,
  title  = {{PIU Risk Classifier (MLsystem course project)}},
  year   = {{2026}},
  url    = {{https://modelscope.cn/models/{repo_id}}}
}}
```
"""
    (out_dir / "README.md").write_text(card, encoding="utf-8")


INFERENCE_PY = '''"""Standalone inference for the PIU Risk Classifier.

Only requires: scikit-learn, joblib, numpy, pandas (see requirements.txt).
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

LABEL_NAMES = ["None", "Mild", "Moderate", "Severe"]

# Friendly request keys -> raw training feature columns
REQUEST_FIELD_MAP = {
    "age": "Basic_Demos-Age",
    "sex": "Basic_Demos-Sex",
    "bmi": "Physical-BMI",
    "height": "Physical-Height",
    "weight": "Physical-Weight",
    "waist_circumference": "Physical-Waist_Circumference",
    "diastolic_bp": "Physical-Diastolic_BP",
    "systolic_bp": "Physical-Systolic_BP",
    "heart_rate": "Physical-HeartRate",
    "cgas_score": "CGAS-CGAS_Score",
    "computerinternet_hoursday": "PreInt_EduHx-computerinternet_hoursday",
}


class PiuRiskClassifier:
    """Loads model.joblib + model_metadata.json from a local directory."""

    def __init__(self, model_dir: str | Path = "."):
        model_dir = Path(model_dir)
        self.pipeline = joblib.load(model_dir / "model.joblib")
        meta = json.loads((model_dir / "model_metadata.json").read_text())
        self.feature_names = list(meta["feature_names"])

    @classmethod
    def from_pretrained(cls, repo_id_or_dir: str) -> "PiuRiskClassifier":
        path = Path(repo_id_or_dir)
        if path.exists():
            return cls(path)
        from modelscope import snapshot_download  # optional dependency

        return cls(snapshot_download(repo_id_or_dir))

    def _to_frame(self, record: dict) -> pd.DataFrame:
        row = {name: np.nan for name in self.feature_names}
        for key, value in record.items():
            if key in row:
                row[key] = value
            elif key in REQUEST_FIELD_MAP and REQUEST_FIELD_MAP[key] in row:
                row[REQUEST_FIELD_MAP[key]] = value
        return pd.DataFrame([row], columns=self.feature_names)

    def predict(self, record: dict) -> dict:
        features = self._to_frame(record)
        proba = self.pipeline.predict_proba(features)[0]
        classes = [int(c) for c in self.pipeline.classes_]
        pred = int(self.pipeline.predict(features)[0])
        return {
            "prediction": pred,
            "label": LABEL_NAMES[pred],
            "confidence": float(proba.max()),
            "probabilities": {
                LABEL_NAMES[cls]: float(p) for cls, p in zip(classes, proba)
            },
        }
'''

EXAMPLE_PY = '''"""Minimal usage example (run inside the model directory)."""

from inference import PiuRiskClassifier

model = PiuRiskClassifier(".")
result = model.predict(
    {
        "age": 12.5,
        "sex": 1,
        "bmi": 18.5,
        "height": 150.0,
        "weight": 45.0,
        "cgas_score": 75.0,
        "computerinternet_hoursday": 3.0,
    }
)
print(f"Risk level : {result['label']} (class {result['prediction']})")
print(f"Confidence : {result['confidence']:.2%}")
print(f"Probabilities: {result['probabilities']}")
'''

MIT_LICENSE = """MIT License

Copyright (c) 2026 MLsystem course project (mlsys-2026s)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def write_support_files(out_dir: Path, meta: dict) -> None:
    import sklearn

    (out_dir / "inference.py").write_text(INFERENCE_PY, encoding="utf-8")
    (out_dir / "example.py").write_text(EXAMPLE_PY, encoding="utf-8")
    (out_dir / "LICENSE").write_text(MIT_LICENSE, encoding="utf-8")
    (out_dir / "requirements.txt").write_text(
        f"scikit-learn=={sklearn.__version__}\n"
        f"joblib>={joblib.__version__}\n"
        "numpy>=1.26\n"
        "pandas>=2.0\n",
        encoding="utf-8",
    )
    # Minimal ModelScope repo descriptor
    (out_dir / "configuration.json").write_text(
        json.dumps({"framework": "scikit-learn", "task": "tabular-classification"}, indent=2),
        encoding="utf-8",
    )


def smoke_test(out_dir: Path) -> None:
    """Load the packaged model exactly the way a downstream user would."""
    sys.path.insert(0, str(out_dir))
    try:
        import importlib

        inference = importlib.import_module("inference")
        importlib.reload(inference)  # in case of stale module cache
        model = inference.PiuRiskClassifier(out_dir)
        result = model.predict(
            {"age": 12.5, "sex": 1, "bmi": 18.5, "cgas_score": 75.0, "computerinternet_hoursday": 3.0}
        )
        assert result["label"] in LABEL_NAMES and 0.0 < result["confidence"] <= 1.0
        print(f"Smoke test OK: label={result['label']} confidence={result['confidence']:.2%}")
        print(f"  probabilities={ {k: round(v, 4) for k, v in result['probabilities'].items()} }")
    finally:
        sys.path.remove(str(out_dir))
        shutil.rmtree(out_dir / "__pycache__", ignore_errors=True)  # keep upload folder clean


def upload(out_dir: Path, repo_id: str, meta: dict) -> None:
    try:
        from modelscope.hub.api import HubApi
    except ImportError:
        raise SystemExit(
            "modelscope SDK not installed. Run: pip install modelscope\n"
            "Then re-run with --upload."
        )

    api = HubApi()
    token = os.environ.get("MODELSCOPE_API_TOKEN")
    if token:
        api.login(token)
    # else: rely on credentials cached by a prior `modelscope login`

    try:
        api.create_model(model_id=repo_id, visibility=5, license="MIT")  # 5 = public
        print(f"Created repo {repo_id}")
    except Exception as exc:  # already exists or perms issue — surface and continue
        print(f"create_model: {exc} (continuing — repo may already exist)")

    api.upload_folder(
        repo_id=repo_id,
        folder_path=str(out_dir),
        commit_message=(
            f"Release piu-risk champion v{meta['version']} "
            f"(QWK {meta['metrics']['qwk_mean']:.4f}, {meta['params']['model_type']} {meta['params']['feature_version']})"
        ),
    )
    print(f"Uploaded to https://modelscope.cn/models/{repo_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Package (and optionally upload) the champion model for ModelScope")
    parser.add_argument("--repo-id", default=MODELSCOPE_REPO, help=f"ModelScope <owner>/<name> (default: {MODELSCOPE_REPO})")
    parser.add_argument("--upload", action="store_true", help="Upload to ModelScope after packaging")
    args = parser.parse_args()

    out_dir = PUBLISH_ROOT / args.repo_id.split("/")[-1]
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = export_champion(out_dir)
    write_model_card(out_dir, meta, args.repo_id)
    write_support_files(out_dir, meta)
    smoke_test(out_dir)

    print(f"\nPackaged: {out_dir}")
    for f in sorted(out_dir.iterdir()):
        print(f"  {f.name:24s} {f.stat().st_size:>8,} B")

    if args.upload:
        upload(out_dir, args.repo_id, meta)
    else:
        print(
            "\nNext steps to publish:\n"
            "  1. pip install modelscope\n"
            "  2. Get a token: https://modelscope.cn/my/myaccesstoken\n"
            "  3. export MODELSCOPE_API_TOKEN=<your token>   (or: modelscope login)\n"
            f"  4. python scripts/publish_modelscope.py --upload --repo-id <your-username>/{args.repo_id.split('/')[-1]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
