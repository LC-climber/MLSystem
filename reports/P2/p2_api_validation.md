# P2 API Validation

Validated on 2026-06-11 using direct FastAPI endpoint function calls after loading `models:/piu-risk@champion`.

## Results

- `load_model("champion")`: passed
- `health_check()`: `healthy`, model loaded
- `get_model_info()`: model version `9`, alias `champion`
- `predict(sample)`: returned class `2` (`Moderate`) with probability vector
- Sparse pyfunc request with only `age`, `sex`, `bmi`: passed

Sample prediction:

```json
{
  "prediction": 2,
  "prediction_label": "Moderate",
  "probabilities": [
    0.0008785883685978258,
    0.0012483043759998849,
    0.9970727063456853,
    0.000800400909716932
  ],
  "confidence": 0.9970727063456853
}
```

Sparse request prediction:

```json
{
  "prediction": 0,
  "confidence": 0.44544458811268356
}
```

Note: binding a live `uvicorn` server on ports `8000` and `8010` failed in the sandbox because the ports were unavailable, but model loading and endpoint logic were verified through the FastAPI app functions. The MLflow pyfunc model was re-registered without a strict input signature so sparse API requests can be completed by the wrapper's missing-feature handling.
