"""Scoring trained models and ranking them.

Each problem type has one primary metric that decides the leaderboard, plus
supporting metrics shown alongside it.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from app.core.serialization import round_or_none
from app.ml.problem_detection import BINARY_CLASSIFICATION, REGRESSION

# The metric the leaderboard sorts on, per problem type.
PRIMARY_METRIC = {
    "regression": ("r2", "R² score"),
    "binary_classification": ("f1", "F1 score"),
    "multiclass_classification": ("f1", "F1 score"),
}


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    """MAPE, skipped when any actual value is zero (it divides by the actual)."""
    y_true = np.asarray(y_true, dtype=float)
    non_zero = y_true != 0
    if not non_zero.any():
        return None
    y_pred = np.asarray(y_pred, dtype=float)
    return float(
        np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100
    )


def evaluate_regression(y_true, y_pred) -> dict:
    mse = mean_squared_error(y_true, y_pred)
    return {
        "r2": round_or_none(r2_score(y_true, y_pred)),
        "mae": round_or_none(mean_absolute_error(y_true, y_pred)),
        "mse": round_or_none(mse),
        # Computed from MSE so this works across sklearn versions.
        "rmse": round_or_none(float(np.sqrt(mse))),
        "mape": round_or_none(_safe_mape(y_true, y_pred), 2),
    }


def evaluate_classification(y_true, y_pred, y_proba=None, problem_type: str = "") -> dict:
    labels = sorted(set(map(str, y_true)) | set(map(str, y_pred)))

    metrics = {
        "accuracy": round_or_none(accuracy_score(y_true, y_pred)),
        "precision": round_or_none(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "recall": round_or_none(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "f1": round_or_none(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "labels": labels,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }

    # ROC AUC needs probabilities, and only has a single unambiguous form for
    # two classes, so it is reported for binary problems only.
    if problem_type == BINARY_CLASSIFICATION and y_proba is not None:
        try:
            positive = labels[-1]
            binary_true = [1 if str(value) == positive else 0 for value in y_true]
            metrics["roc_auc"] = round_or_none(roc_auc_score(binary_true, y_proba))
        except (ValueError, IndexError):
            metrics["roc_auc"] = None

    return metrics


def evaluate(y_true, y_pred, problem_type: str, y_proba=None) -> dict:
    if problem_type == REGRESSION:
        return evaluate_regression(y_true, y_pred)
    return evaluate_classification(y_true, y_pred, y_proba, problem_type)


def rank_models(results: list[dict], problem_type: str) -> list[dict]:
    """Sort successful models best-first and stamp each with its rank."""
    metric_key, _ = PRIMARY_METRIC[problem_type]

    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]

    # A None score means the metric could not be computed; sort those last.
    successful.sort(
        key=lambda r: (r["metrics"].get(metric_key) is not None, r["metrics"].get(metric_key) or 0),
        reverse=True,
    )

    for index, result in enumerate(successful):
        result["rank"] = index + 1
        result["is_best"] = index == 0

    return successful + failed


def extract_feature_importance(model, feature_names: list[str], limit: int = 15) -> list[dict]:
    """Per-feature influence, from tree importances or linear coefficients."""
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_, dtype=float)
        kind = "importance"
    elif hasattr(model, "coef_"):
        coefficients = np.asarray(model.coef_, dtype=float)
        # Multiclass models give one coefficient row per class; average their magnitude.
        values = np.abs(coefficients).mean(axis=0) if coefficients.ndim > 1 else np.abs(coefficients)
        kind = "coefficient magnitude"
    else:
        return []

    if len(values) != len(feature_names):
        return []

    total = float(values.sum())
    ranked = sorted(zip(feature_names, values), key=lambda pair: pair[1], reverse=True)

    return [
        {
            "feature": name,
            "value": round_or_none(value),
            "percentage": round_or_none((value / total * 100) if total else 0, 2),
            "kind": kind,
        }
        for name, value in ranked[:limit]
    ]
