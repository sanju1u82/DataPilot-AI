"""Serving predictions from a trained run.

Reuses the exact feature spec and fitted pipeline saved by `training`, so new
rows go through the same transformations the model was trained on.
"""

from __future__ import annotations

import joblib
import pandas as pd

from app.core.errors import RunNotFoundError
from app.core.serialization import round_or_none, to_native
from app.ml import feature_engineering
from app.ml.problem_detection import REGRESSION
from app.ml.training import model_path

# Cap on rows per prediction request, so one call can't monopolise the worker.
MAX_PREDICTION_ROWS = 1000


def load_model(run_id: str) -> dict:
    path = model_path(run_id)
    if not path.exists():
        raise RunNotFoundError(
            "That model is no longer available. Train the dataset again to recreate it."
        )
    return joblib.load(path)


def required_columns(run_id: str) -> dict:
    """The input fields a caller must supply to get a prediction."""
    artifact = load_model(run_id)
    spec = artifact["spec"]
    return {
        "run_id": run_id,
        "model": artifact["model_name"],
        "target": artifact["problem"]["target"],
        "problem_type": artifact["problem"]["problem_type"],
        # Date columns are expanded internally, so callers pass the original column.
        "numeric": [c for c in spec["numeric"] if c not in spec["derived"]],
        "categorical": spec["categorical"],
        "datetime": spec["datetime_source"],
    }


def predict(run_id: str, rows: list[dict]) -> dict:
    """Score new rows with a previously trained model."""
    if not rows:
        return {"run_id": run_id, "predictions": []}

    rows = rows[:MAX_PREDICTION_ROWS]

    artifact = load_model(run_id)
    pipeline = artifact["pipeline"]
    spec = artifact["spec"]
    problem = artifact["problem"]

    frame = pd.DataFrame(rows)
    X = feature_engineering.build_feature_frame(frame, spec)
    raw_predictions = pipeline.predict(X)

    predictions: list[dict] = []
    probabilities = None
    if problem["problem_type"] != REGRESSION and hasattr(pipeline, "predict_proba"):
        try:
            probabilities = pipeline.predict_proba(X)
            classes = [str(label) for label in pipeline.named_steps["model"].classes_]
        except (AttributeError, ValueError):
            probabilities = None

    for index, value in enumerate(raw_predictions):
        entry: dict = {"row": index, "prediction": to_native(value)}
        if probabilities is not None:
            row_probabilities = probabilities[index]
            entry["confidence"] = round_or_none(float(max(row_probabilities)), 4)
            entry["class_probabilities"] = {
                label: round_or_none(float(probability), 4)
                for label, probability in zip(classes, row_probabilities)
            }
        predictions.append(entry)

    return {
        "run_id": run_id,
        "target": problem["target"],
        "model": artifact["model_name"],
        "problem_type": problem["problem_type"],
        "predictions": predictions,
    }
