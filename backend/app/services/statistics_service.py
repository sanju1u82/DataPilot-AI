"""Per-column descriptive statistics.

Numeric columns get the usual five-number summary plus shape and outlier
counts; categorical columns get cardinality and a frequency distribution the
frontend can chart directly.
"""

from __future__ import annotations

import pandas as pd

from app.core.serialization import round_or_none, to_native
from app.services.profiling_service import (
    BOOLEAN,
    CATEGORICAL,
    DATETIME,
    NUMERIC,
    classify_column,
)

# How many categories to return per column for the distribution chart.
TOP_CATEGORIES = 10


def numeric_summary(series: pd.Series) -> dict:
    """Five-number summary, distribution shape and IQR-based outlier count."""
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"name": str(series.name), "count": 0, "all_missing": True}

    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1

    # Tukey's fences: anything beyond 1.5 IQR from the quartiles.
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    outliers = int(((values < lower_fence) | (values > upper_fence)).sum())

    return {
        "name": str(series.name),
        "count": int(values.count()),
        "all_missing": False,
        "mean": round_or_none(values.mean()),
        "median": round_or_none(values.median()),
        "std": round_or_none(values.std()),
        "min": round_or_none(values.min()),
        "max": round_or_none(values.max()),
        "range": round_or_none(values.max() - values.min()),
        "q1": round_or_none(q1),
        "q3": round_or_none(q3),
        "iqr": round_or_none(iqr),
        # skew/kurtosis are undefined for very small samples.
        "skewness": round_or_none(values.skew()) if values.count() > 2 else None,
        "kurtosis": round_or_none(values.kurtosis()) if values.count() > 3 else None,
        "zeros": int((values == 0).sum()),
        "negatives": int((values < 0).sum()),
        "outliers": outliers,
        "outlier_percentage": round_or_none(outliers / values.count() * 100, 2),
    }


def categorical_summary(series: pd.Series, row_count: int) -> dict:
    """Cardinality and the most frequent values."""
    values = series.dropna()
    if values.empty:
        return {"name": str(series.name), "count": 0, "all_missing": True}

    counts = values.value_counts()
    top = counts.head(TOP_CATEGORIES)

    distribution = [
        {
            "value": to_native(value),
            "count": int(count),
            "percentage": round_or_none(count / len(values) * 100, 2),
        }
        for value, count in top.items()
    ]

    return {
        "name": str(series.name),
        "count": int(values.count()),
        "all_missing": False,
        "unique": int(counts.size),
        "top_value": to_native(counts.index[0]),
        "top_count": int(counts.iloc[0]),
        "top_percentage": round_or_none(counts.iloc[0] / len(values) * 100, 2),
        "distribution": distribution,
        "other_categories": max(int(counts.size) - len(distribution), 0),
        "is_imbalanced": bool(counts.iloc[0] / len(values) > 0.9 and counts.size > 1),
    }


def datetime_summary(series: pd.Series) -> dict:
    """Range and span of a date column."""
    if pd.api.types.is_datetime64_any_dtype(series):
        values = series.dropna()
    else:
        # Only string columns reach here, and their formats may vary row to row.
        values = pd.to_datetime(series, errors="coerce", format="mixed").dropna()

    if values.empty:
        return {"name": str(series.name), "count": 0, "all_missing": True}

    return {
        "name": str(series.name),
        "count": int(values.count()),
        "all_missing": False,
        "min": to_native(values.min()),
        "max": to_native(values.max()),
        "span_days": int((values.max() - values.min()).days),
        "unique": int(values.nunique()),
    }


def histogram(series: pd.Series, bins: int = 20) -> dict | None:
    """Binned counts for a numeric column, for the distribution chart."""
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.count() < 2 or values.nunique() < 2:
        return None

    counts, edges = pd.cut(values, bins=bins, retbins=True)
    frequencies = counts.value_counts().sort_index()

    return {
        "name": str(series.name),
        "bins": [
            {
                "start": round_or_none(edges[index], 4),
                "end": round_or_none(edges[index + 1], 4),
                "count": int(frequency),
            }
            for index, frequency in enumerate(frequencies.tolist())
        ],
    }


def generate_statistics(df: pd.DataFrame) -> dict:
    """Statistics for every column, split by semantic type."""
    row_count = int(df.shape[0])

    numeric: list[dict] = []
    categorical: list[dict] = []
    datetime_columns: list[dict] = []
    histograms: list[dict] = []

    for name in df.columns:
        series = df[name]
        semantic_type = classify_column(series, row_count)

        if semantic_type == NUMERIC:
            numeric.append(numeric_summary(series))
            chart = histogram(series)
            if chart:
                histograms.append(chart)
        elif semantic_type in (CATEGORICAL, BOOLEAN):
            categorical.append(categorical_summary(series, row_count))
        elif semantic_type == DATETIME:
            datetime_columns.append(datetime_summary(series))

    return {
        "numeric": numeric,
        "categorical": categorical,
        "datetime": datetime_columns,
        "histograms": histograms,
    }
