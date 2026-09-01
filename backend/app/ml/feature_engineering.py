"""Feature derivation and selection.

Runs as plain pandas before the sklearn pipeline, so the same function can be
replayed at prediction time against a single row of new data.
"""

from __future__ import annotations

import pandas as pd

from app.services.profiling_service import (
    BOOLEAN,
    CATEGORICAL,
    DATETIME,
    IDENTIFIER,
    NUMERIC,
    TEXT,
    classify_column,
)

DATE_PARTS = ("year", "month", "day", "dayofweek", "quarter")


def expand_datetime_columns(df: pd.DataFrame, datetime_columns: list[str]) -> pd.DataFrame:
    """Replace each date column with numeric parts a model can actually use."""
    if not datetime_columns:
        return df

    result = df.copy()
    for name in datetime_columns:
        if name not in result.columns:
            continue

        if pd.api.types.is_datetime64_any_dtype(result[name]):
            parsed = result[name]
        else:
            parsed = pd.to_datetime(result[name], errors="coerce", format="mixed")

        # Mixed timezones can leave `to_datetime` returning object dtype, which
        # has no `.dt` accessor. Emit empty parts rather than raising.
        if pd.api.types.is_datetime64_any_dtype(parsed):
            for part in DATE_PARTS:
                result[f"{name}__{part}"] = getattr(parsed.dt, part)
        else:
            for part in DATE_PARTS:
                result[f"{name}__{part}"] = pd.NA

        result = result.drop(columns=[name])

    return result


def select_features(df: pd.DataFrame, target: str) -> dict:
    """Decide which columns to train on and why the others were dropped.

    Returning the reasons matters as much as the selection — the UI shows the
    user what was excluded so the result doesn't look arbitrary.
    """
    row_count = int(df.shape[0])

    numeric: list[str] = []
    categorical: list[str] = []
    datetime_columns: list[str] = []
    dropped: list[dict] = []

    for name in df.columns:
        if name == target:
            continue

        series = df[name]
        semantic_type = classify_column(series, row_count)
        non_null = series.dropna()

        if non_null.empty:
            dropped.append({"column": name, "reason": "Column is entirely empty"})
        elif non_null.nunique() <= 1:
            dropped.append({"column": name, "reason": "Column has only one value"})
        elif semantic_type == IDENTIFIER:
            dropped.append({"column": name, "reason": "Looks like an ID — unique per row"})
        elif semantic_type == TEXT:
            dropped.append(
                {"column": name, "reason": "High-cardinality free text"}
            )
        elif semantic_type == NUMERIC:
            numeric.append(name)
        elif semantic_type == DATETIME:
            datetime_columns.append(name)
        elif semantic_type in (CATEGORICAL, BOOLEAN):
            categorical.append(name)
        else:
            dropped.append({"column": name, "reason": "Unsupported column type"})

    # Date columns become numeric parts, so they join the numeric feature list.
    derived = [f"{name}__{part}" for name in datetime_columns for part in DATE_PARTS]

    return {
        "numeric": numeric + derived,
        "categorical": categorical,
        "datetime_source": datetime_columns,
        "derived": derived,
        "dropped": dropped,
        "feature_count": len(numeric) + len(derived) + len(categorical),
    }


def build_feature_frame(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """Apply the selection to a frame, producing the exact model input columns."""
    frame = expand_datetime_columns(df, spec["datetime_source"])
    wanted = spec["numeric"] + spec["categorical"]

    # New data at prediction time may be missing columns the model expects.
    for column in wanted:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame = frame[wanted].copy()

    # One-hot encoding sorts each column's categories, which raises if a column
    # mixes strings and numbers. Normalising to string keeps that comparison safe.
    for column in spec["categorical"]:
        frame[column] = frame[column].where(frame[column].isna(), frame[column].astype(str))

    for column in spec["numeric"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame
