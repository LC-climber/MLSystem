"""
Spark MLlib Baseline Models

Distributed system in the P1 comparison. LR and MLP via pyspark.ml, wrapped in
the BaseModel numpy-in/numpy-out interface so the shared run_cv loop drives them
identically to sklearn/PyTorch (fair comparison; 03_plan_p1_v2.md §5.4). The
numpy<->Spark DataFrame round-trip lives inside fit/predict on purpose — that
conversion + job-scheduling cost is exactly what P1 measures for Spark at the
training stage of a ~3000-row tabular task (and is expected to lose to sklearn
here; Spark's real value is the actigraphy feat_v2 preprocessing stage).

- LR : LogisticRegression(maxIter=1000, regParam=0, elasticNetParam=0,
       family='multinomial') + per-sample balanced weightCol → parity with
       sklearn LR class_weight='balanced'.
- MLP: MultilayerPerceptronClassifier(layers=[in, 128, 64, num_classes]).
       MLlib's MLP supports no weightCol/sample weights, so — like the sklearn
       MLP — it gets NO class balancing. A genuine system difference, reported
       per R-SYS-3 / P1-R3, not an algorithm choice.

Java: Spark 3.5 ⊄ Java 21; src.utils.spark pins a compatible JDK on import.
"""

import numpy as np

from src.models.base import BaseModel
from src.utils.spark import get_spark_session


def _balanced_sample_weights(y: np.ndarray, num_classes: int) -> np.ndarray:
    """Per-sample weights matching sklearn 'balanced': n / (k * count[class])."""
    counts = np.bincount(y, minlength=num_classes).astype(float)
    counts[counts == 0] = 1.0  # guard absent classes (shouldn't happen w/ stratified folds)
    weight_per_class = len(y) / (num_classes * counts)
    return weight_per_class[y]


class _SparkBaseModel(BaseModel):
    """Shared numpy<->Spark conversion; subclasses set the MLlib estimator in fit()."""

    system = "spark"

    def _to_train_df(self, X: np.ndarray, y: np.ndarray, weights=None):
        from pyspark.ml.linalg import Vectors, VectorUDT
        from pyspark.sql.types import StructType, StructField, DoubleType

        spark = get_spark_session()
        if weights is None:
            schema = StructType([
                StructField("label", DoubleType(), False),
                StructField("features", VectorUDT(), False),
            ])
            rows = [(float(y[i]), Vectors.dense(X[i])) for i in range(len(y))]
        else:
            schema = StructType([
                StructField("label", DoubleType(), False),
                StructField("weight", DoubleType(), False),
                StructField("features", VectorUDT(), False),
            ])
            rows = [(float(y[i]), float(weights[i]), Vectors.dense(X[i])) for i in range(len(y))]
        return spark.createDataFrame(rows, schema)

    def _to_predict_df(self, X: np.ndarray):
        from pyspark.ml.linalg import Vectors, VectorUDT
        from pyspark.sql.types import StructType, StructField, LongType

        spark = get_spark_session()
        schema = StructType([
            StructField("row_id", LongType(), False),
            StructField("features", VectorUDT(), False),
        ])
        rows = [(i, Vectors.dense(X[i])) for i in range(len(X))]
        return spark.createDataFrame(rows, schema)

    def _transform_collect(self, X: np.ndarray):
        """Run model.transform and return (pred[n], proba[n, num_classes]) in input order."""
        df = self._to_predict_df(np.asarray(X, dtype="float64"))
        out = self.model.transform(df).select("row_id", "prediction", "probability").collect()
        out.sort(key=lambda r: r["row_id"])
        pred = np.array([r["prediction"] for r in out], dtype=int)
        proba = np.array([r["probability"].toArray() for r in out], dtype=float)
        # MLlib sizes probability by classes seen in training; pad if a high class was absent.
        if proba.shape[1] < self.num_classes:
            pad = np.zeros((proba.shape[0], self.num_classes - proba.shape[1]))
            proba = np.hstack([proba, pad])
        return pred, proba

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._transform_collect(X)[0]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._transform_collect(X)[1]


class SparkLogisticRegression(_SparkBaseModel):
    """Multinomial LR (maxIter=1000, no regularization) + balanced weightCol."""

    algorithm = "lr"

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SparkLogisticRegression":
        from pyspark.ml.classification import LogisticRegression

        X = np.asarray(X, dtype="float64")
        y = np.asarray(y, dtype=int)
        use_weight = self.class_weight == "balanced"
        weights = _balanced_sample_weights(y, self.num_classes) if use_weight else None
        df = self._to_train_df(X, y, weights)

        kwargs = dict(
            featuresCol="features", labelCol="label",
            maxIter=1000, regParam=0.0, elasticNetParam=0.0, family="multinomial",
        )
        if use_weight:
            kwargs["weightCol"] = "weight"
        self.model = LogisticRegression(**kwargs).fit(df)
        return self

    def get_params(self):
        return {
            **super().get_params(),
            "maxIter": 1000, "regParam": 0.0, "elasticNetParam": 0.0,
            "family": "multinomial",
        }


class SparkMLP(_SparkBaseModel):
    """MultilayerPerceptronClassifier [in, 128, 64, num_classes] (no class weighting)."""

    algorithm = "mlp"

    def __init__(
        self,
        num_classes: int,
        class_weight: str = "balanced",
        seed: int = 42,
        hidden_dims=(128, 64),
        max_iter: int = 200,
        block_size: int = 128,
    ):
        super().__init__(num_classes, class_weight, seed)
        self.hidden_dims = tuple(hidden_dims)
        self.max_iter = max_iter
        self.block_size = block_size

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SparkMLP":
        from pyspark.ml.classification import MultilayerPerceptronClassifier

        X = np.asarray(X, dtype="float64")
        y = np.asarray(y, dtype=int)
        layers = [X.shape[1], *self.hidden_dims, self.num_classes]
        df = self._to_train_df(X, y, weights=None)  # MLlib MLP: no sample/class weighting

        self.model = MultilayerPerceptronClassifier(
            featuresCol="features", labelCol="label",
            layers=layers, blockSize=self.block_size, maxIter=self.max_iter, seed=self.seed,
        ).fit(df)
        return self

    def get_params(self):
        params = {
            **super().get_params(),
            "layers": f"in-{'-'.join(map(str, self.hidden_dims))}-out",
            "maxIter": self.max_iter, "blockSize": self.block_size, "solver": "l-bfgs",
        }
        params["class_weight"] = "not_supported"  # MLlib MLP has no weightCol
        return params
