"""The AutoML training run.

Detects the problem, prepares features, trains every candidate model, scores
them on a held-out split, ranks them, and persists the winner so it can serve
predictions later.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.config import MAX_TRAINING_ROWS, UPLOAD_DIR
from app.core.errors import TrainingFailedError
from app.core.serialization import round_or_none
from app.ml import evaluation, feature_engineering, model_selection, preprocessing
from app.ml.model_selection import RANDOM_STATE
from app.ml.problem_detection import REGRESSION, detect_problem_type

logger = logging.getLogger("datapilot")

MODEL_DIR = UPLOAD_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TEST_SIZE = 0.2
# Below this many rows a holdout split leaves too little to train or score on.
MIN_TRAINING_ROWS = 20


def model_path(run_id: str) -> Path:
    return MODEL_DIR / f"{run_id}.joblib"


def _split(X: pd.DataFrame, y: pd.Series, problem: dict):
    """Hold out a test set, stratifying when every class can afford it."""
    stratify = y if problem["is_classification"] and problem.get("can_stratify") else None
    try:
        return train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=stratify
        )
    except ValueError:
        # Stratification fails when a class is too small for both sides of the split.
        return train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)


def _train_one(candidate, preprocessor, X_train, y_train, X_test, y_test, problem) -> dict:
    """Fit and score a single candidate, converting a failure into a result row."""
    started = time.perf_counter()
    try:
        pipeline = Pipeline(
            [("preprocess", preprocessor), ("model", candidate.build())]
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        probabilities = None
        if problem["problem_type"] != REGRESSION and hasattr(pipeline, "predict_proba"):
            try:
                probabilities = pipeline.predict_proba(X_test)[:, -1]
            except (AttributeError, IndexError, ValueError):
                probabilities = None

        metrics = evaluation.evaluate(
            y_test, predictions, problem["problem_type"], probabilities
        )

        return {
            "key": candidate.key,
            "name": candidate.name,
            "description": candidate.description,
            "status": "success",
            "metrics": metrics,
            "training_seconds": round_or_none(time.perf_counter() - started, 2),
            "_pipeline": pipeline,
        }

    except Exception as exc:
        logger.warning("Model %s failed to train: %s", candidate.key, exc)
        return {
            "key": candidate.key,
            "name": candidate.name,
            "description": candidate.description,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "metrics": {},
            "training_seconds": round_or_none(time.perf_counter() - started, 2),
        }


def run_training(
    df: pd.DataFrame,
    target: str,
    run_id: str,
    on_progress=lambda stage, percent: None,
) -> dict:
    """Execute a full AutoML run and return the leaderboard and best model."""
    on_progress("Detecting problem type", 10)
    problem = detect_problem_type(df, target)

    on_progress("Selecting features", 20)
    spec = feature_engineering.select_features(df, target)
    if spec["feature_count"] == 0:
        raise TrainingFailedError(
            "No usable feature columns are left after dropping IDs, empty and "
            "constant columns. This dataset needs more informative fields."
        )

    on_progress("Preparing data", 30)
    working = df
    sampled_from = None
    if len(working) > MAX_TRAINING_ROWS:
        sampled_from = int(len(working))
        working = working.sample(n=MAX_TRAINING_ROWS, random_state=RANDOM_STATE)

    X = feature_engineering.build_feature_frame(working, spec)
    y = preprocessing.prepare_target(working[target], problem["is_classification"])
    X, y = preprocessing.clean_training_rows(X, y)

    if len(X) < MIN_TRAINING_ROWS:
        raise TrainingFailedError(
            f"Only {len(X)} rows have a usable target value — at least "
            f"{MIN_TRAINING_ROWS} are needed to train and evaluate a model."
        )

    X_train, X_test, y_train, y_test = _split(X, y, problem)
    preprocessor = preprocessing.build_preprocessor(spec["numeric"], spec["categorical"])

    candidates = model_selection.candidates_for(problem["problem_type"])
    results = []
    for index, candidate in enumerate(candidates):
        on_progress(
            f"Training {candidate.name}",
            40 + int(index / len(candidates) * 45),
        )
        results.append(
            _train_one(candidate, preprocessor, X_train, y_train, X_test, y_test, problem)
        )

    on_progress("Comparing models", 90)
    ranked = evaluation.rank_models(results, problem["problem_type"])

    successful = [r for r in ranked if r["status"] == "success"]
    if not successful:
        first_error = next(
            (r.get("error") for r in ranked if r.get("error")), "unknown error"
        )
        raise TrainingFailedError(
            "Every candidate model failed to train on this dataset.",
            detail=first_error,
        )

    best = successful[0]
    best_pipeline = best["_pipeline"]

    on_progress("Saving best model", 95)
    joblib.dump(
        {
            "pipeline": best_pipeline,
            "spec": spec,
            "problem": problem,
            "model_key": best["key"],
            "model_name": best["name"],
        },
        model_path(run_id),
    )

    fitted_preprocessor = best_pipeline.named_steps["preprocess"]
    feature_names = preprocessing.feature_names_from(fitted_preprocessor)
    importance = evaluation.extract_feature_importance(
        best_pipeline.named_steps["model"], feature_names
    )

    # The fitted pipelines are not JSON serialisable and only the winner is kept.
    leaderboard = [{k: v for k, v in r.items() if k != "_pipeline"} for r in ranked]

    metric_key, metric_label = evaluation.PRIMARY_METRIC[problem["problem_type"]]

    on_progress("Done", 100)
    return {
        "problem": problem,
        "features": spec,
        "preprocessing": preprocessing.describe_preprocessing(
            spec["numeric"], spec["categorical"]
        ),
        "training": {
            "rows_used": int(len(X)),
            "sampled_from": sampled_from,
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "test_size": TEST_SIZE,
            "encoded_feature_count": len(feature_names),
        },
        "primary_metric": {"key": metric_key, "label": metric_label},
        "leaderboard": leaderboard,
        "best_model": {
            "key": best["key"],
            "name": best["name"],
            "description": best["description"],
            "metrics": best["metrics"],
            "score": best["metrics"].get(metric_key),
        },
        "feature_importance": importance,
    }
