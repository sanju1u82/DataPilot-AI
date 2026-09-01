"""Working out what kind of ML problem a target column represents."""

from __future__ import annotations

import pandas as pd

from app.core.errors import InvalidTargetError

BINARY_CLASSIFICATION = "binary_classification"
MULTICLASS_CLASSIFICATION = "multiclass_classification"
REGRESSION = "regression"

# A numeric target with at most this many distinct values is far more likely to
# be an encoded class label than a continuous measurement.
MAX_DISCRETE_NUMERIC_CLASSES = 10

# Above this many classes, the problem is treated as unmodellable rather than as
# a classification with hundreds of near-empty classes.
MAX_CLASSES = 50


def detect_problem_type(df: pd.DataFrame, target: str) -> dict:
    """Classify the modelling problem, or explain why the target won't work."""
    if target not in df.columns:
        raise InvalidTargetError(f"'{target}' is not a column in this dataset.")

    series = df[target]
    non_null = series.dropna()

    if non_null.empty:
        raise InvalidTargetError(f"'{target}' has no values to learn from.")

    unique = int(non_null.nunique())
    if unique < 2:
        raise InvalidTargetError(
            f"'{target}' has the same value in every row, so there is nothing to predict."
        )

    is_numeric = pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)
    # Whole numbers with few distinct values read as class labels, not measures.
    looks_discrete = is_numeric and unique <= MAX_DISCRETE_NUMERIC_CLASSES

    if is_numeric and not looks_discrete:
        problem_type = REGRESSION
    elif unique == 2:
        problem_type = BINARY_CLASSIFICATION
    else:
        problem_type = MULTICLASS_CLASSIFICATION

    if problem_type != REGRESSION and unique > MAX_CLASSES:
        raise InvalidTargetError(
            f"'{target}' has {unique} distinct values — too many to treat as classes, "
            "and it isn't numeric enough to predict as a number."
        )

    result = {
        "target": target,
        "problem_type": problem_type,
        "is_classification": problem_type != REGRESSION,
        "unique_values": unique,
        "missing_in_target": int(series.isna().sum()),
    }

    if problem_type != REGRESSION:
        counts = non_null.value_counts()
        smallest = int(counts.iloc[-1])
        result["classes"] = [str(label) for label in counts.index.tolist()]
        result["class_counts"] = {str(k): int(v) for k, v in counts.items()}
        result["smallest_class_size"] = smallest
        # Stratified splitting needs at least two samples of every class.
        result["can_stratify"] = smallest >= 2
        result["is_imbalanced"] = bool(counts.iloc[0] / counts.iloc[-1] >= 10)

    return result


def suggest_targets(profile: dict) -> list[dict]:
    """Columns that would make sensible prediction targets, best first."""
    suggestions = []

    for column in profile["columns"]:
        if column["is_constant"] or column["is_empty"] or column["is_identifier"]:
            continue
        if column["semantic_type"] == "text":
            continue
        # A target that is mostly missing leaves too few rows to train on.
        if (column["missing_percentage"] or 0) > 30:
            continue

        if column["semantic_type"] == "numeric":
            kind, score = "regression", 2
        elif column["semantic_type"] in ("boolean", "categorical"):
            kind, score = "classification", 3 if column["unique"] <= 10 else 1
        else:
            continue

        suggestions.append(
            {
                "column": column["name"],
                "suggested_problem": kind,
                "unique_values": column["unique"],
                "_score": score,
            }
        )

    suggestions.sort(key=lambda item: item["_score"], reverse=True)
    for item in suggestions:
        item.pop("_score")
    return suggestions
