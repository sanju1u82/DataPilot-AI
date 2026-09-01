"""Automated dataset profiling.

Produces the structural picture of a dataset: shape, per-column semantic types,
missingness, cardinality, and the problem columns worth warning about. The
numeric and categorical deep-dives live in `statistics_service`, and the scoring
built on top of this lives in `quality_service`.
"""

from __future__ import annotations

import re

import pandas as pd

from app.config import MAX_CATEGORICAL_CARDINALITY
from app.core.serialization import round_or_none, to_native

# Semantic types, which are what the UI groups and colours by. They are coarser
# than pandas dtypes: an int column of 0/1 is more useful to the user as a
# boolean-ish categorical than as "int64".
NUMERIC = "numeric"
CATEGORICAL = "categorical"
DATETIME = "datetime"
BOOLEAN = "boolean"
TEXT = "text"
IDENTIFIER = "identifier"

_DATE_HINT = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}|\d{4}-\d{2}-\d{2}")


def _looks_like_datetime(series: pd.Series) -> bool:
    """Cheap check for object columns holding dates.

    Only columns whose values actually look date-shaped are handed to the
    parser, which keeps plain numbers and free text from being misread as dates.
    """
    sample = series.dropna().astype(str).head(100)
    if sample.empty:
        return False
    if sample.str.contains(_DATE_HINT, regex=True).mean() < 0.8:
        return False

    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return bool(parsed.notna().mean() >= 0.9)


def classify_column(series: pd.Series, row_count: int) -> str:
    """Assign one of the semantic types above to a column."""
    non_null = series.dropna()
    unique = int(non_null.nunique())

    if pd.api.types.is_bool_dtype(series):
        return BOOLEAN
    if pd.api.types.is_datetime64_any_dtype(series):
        return DATETIME

    if pd.api.types.is_numeric_dtype(series):
        # A 0/1 or two-valued numeric column behaves like a flag, not a measure.
        if unique <= 2 and row_count > 2:
            return BOOLEAN
        return NUMERIC

    if _looks_like_datetime(series):
        return DATETIME

    # Every value distinct across a non-trivial table: an ID, not a category.
    if row_count > 10 and unique == len(non_null) and unique == row_count:
        return IDENTIFIER
    if unique <= MAX_CATEGORICAL_CARDINALITY:
        return CATEGORICAL
    return TEXT


def profile_column(series: pd.Series, row_count: int) -> dict:
    """Structural facts about one column."""
    missing = int(series.isna().sum())
    non_null = series.dropna()
    unique = int(non_null.nunique())
    semantic_type = classify_column(series, row_count)

    return {
        "name": str(series.name),
        "dtype": str(series.dtype),
        "semantic_type": semantic_type,
        "missing": missing,
        "missing_percentage": round_or_none(
            (missing / row_count * 100) if row_count else 0, 2
        ),
        "unique": unique,
        "unique_percentage": round_or_none(
            (unique / row_count * 100) if row_count else 0, 2
        ),
        "is_constant": unique <= 1,
        "is_empty": missing == row_count,
        "is_identifier": semantic_type == IDENTIFIER,
        "sample_values": [to_native(value) for value in non_null.head(5).tolist()],
    }


def find_problem_columns(columns: list[dict]) -> list[dict]:
    """Columns that will cause trouble downstream, with the reason why."""
    problems = []
    for column in columns:
        reasons = []
        if column["is_empty"]:
            reasons.append("Contains no values at all")
        elif column["is_constant"]:
            reasons.append("Every row has the same value")
        if not column["is_empty"] and (column["missing_percentage"] or 0) >= 40:
            reasons.append(f"{column['missing_percentage']}% of values are missing")
        if column["is_identifier"]:
            reasons.append("Every value is unique — looks like an ID column")
        if column["semantic_type"] == TEXT:
            reasons.append("High-cardinality free text — needs encoding before modelling")

        if reasons:
            problems.append({"column": column["name"], "reasons": reasons})
    return problems


def generate_profile(df: pd.DataFrame) -> dict:
    """The full structural profile of a dataset."""
    row_count, column_count = int(df.shape[0]), int(df.shape[1])
    columns = [profile_column(df[name], row_count) for name in df.columns]

    groups: dict[str, list[str]] = {
        NUMERIC: [],
        CATEGORICAL: [],
        DATETIME: [],
        BOOLEAN: [],
        TEXT: [],
        IDENTIFIER: [],
    }
    for column in columns:
        groups[column["semantic_type"]].append(column["name"])

    total_cells = row_count * column_count
    missing_cells = int(sum(column["missing"] for column in columns))
    duplicate_rows = int(df.duplicated().sum())

    return {
        "overview": {
            "rows": row_count,
            "columns": column_count,
            "total_cells": total_cells,
            "missing_cells": missing_cells,
            "missing_percentage": round_or_none(
                (missing_cells / total_cells * 100) if total_cells else 0, 2
            ),
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": round_or_none(
                (duplicate_rows / row_count * 100) if row_count else 0, 2
            ),
            "memory_usage_kb": round_or_none(
                df.memory_usage(deep=True).sum() / 1024, 2
            ),
            "numeric_columns": len(groups[NUMERIC]),
            "categorical_columns": len(groups[CATEGORICAL]) + len(groups[BOOLEAN]),
            "datetime_columns": len(groups[DATETIME]),
            "text_columns": len(groups[TEXT]),
        },
        "column_groups": groups,
        "columns": columns,
        "missing_by_column": {
            column["name"]: column["missing"]
            for column in columns
            if column["missing"] > 0
        },
        "problem_columns": find_problem_columns(columns),
    }
