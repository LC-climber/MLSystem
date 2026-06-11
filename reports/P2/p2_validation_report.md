# P2 Validation Report

Generated: 2026-06-11

## Commands Run

```bash
python -m py_compile \
  src/experiments/run_p2_full_pipeline.py \
  src/experiments/run_p2_optuna.py \
  src/deployment/pyfunc_model.py \
  src/deployment/fastapi_app.py \
  src/deployment/schemas.py \
  scripts/export_p2_reports.py \
  scripts/build_p2_final_ppt.py
```

Result: passed.

```bash
python -m pytest tests/test_data_loading.py tests/test_pipeline_smoke.py -q
```

Result: `2 passed, 2 warnings`.

Warnings: both legacy tests return `bool`; pytest recommends using assertions and returning `None`.

## Champion Load Test

```python
import mlflow
import pandas as pd
from src.config import MLFLOW_TRACKING_URI

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
model = mlflow.pyfunc.load_model("models:/piu-risk@champion")
model.predict(pd.DataFrame([{"age": 12.5, "sex": 1.0, "bmi": 18.5}]))
```

Result: passed.

## API Logic Validation

Direct FastAPI endpoint function validation passed:

- `load_model("champion")`
- `health_check()`
- `get_model_info()`
- `predict(PredictionRequest(...))`

Live `uvicorn` binding on ports `8000` and `8010` failed in the sandbox because the ports were unavailable, but the application loaded the champion model successfully before bind failure.
