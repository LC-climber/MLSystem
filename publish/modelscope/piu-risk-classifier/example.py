"""Minimal usage example (run inside the model directory)."""

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
