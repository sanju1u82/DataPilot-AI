"""Human-readable insights.

Translates the numeric output of the other services into plain sentences a
non-technical user can act on. Each insight carries a category and a tone so the
frontend can badge it consistently.
"""

from __future__ import annotations

import pandas as pd

from app.core.serialization import round_or_none

# Above this absolute Pearson correlation, two numeric columns are close to
# redundant and worth mentioning.
CORRELATION_THRESHOLD = 0.85

# |skew| above this means the distribution leans hard to one side.
SKEW_THRESHOLD = 1.0


def _insight(category: str, tone: str, message: str) -> dict:
    return {"category": category, "tone": tone, "message": message}


def _shape_insights(profile: dict) -> list[dict]:
    overview = profile["overview"]
    rows, columns = overview["rows"], overview["columns"]

    insights = [
        _insight(
            "shape",
            "neutral",
            f"The dataset has {rows:,} rows and {columns} columns "
            f"({overview['numeric_columns']} numerical, "
            f"{overview['categorical_columns']} categorical).",
        )
    ]

    if rows < 100:
        insights.append(
            _insight(
                "shape",
                "warning",
                f"Only {rows} rows — that is small for reliable model training.",
            )
        )
    if columns > rows:
        insights.append(
            _insight(
                "shape",
                "warning",
                "There are more columns than rows, which makes overfitting very likely.",
            )
        )
    return insights


def _missing_insights(profile: dict) -> list[dict]:
    missing_by_column = profile["missing_by_column"]
    if not missing_by_column:
        return [_insight("quality", "positive", "No missing values anywhere in the dataset.")]

    count = len(missing_by_column)
    worst = max(missing_by_column.items(), key=lambda item: item[1])
    worst_column = next(c for c in profile["columns"] if c["name"] == worst[0])

    return [
        _insight(
            "quality",
            "warning",
            f"{count} column{'s' if count != 1 else ''} contain missing values; "
            f"{worst[0]} is the worst at {worst_column['missing_percentage']}%.",
        )
    ]


def _duplicate_insights(profile: dict) -> list[dict]:
    overview = profile["overview"]
    duplicates = overview["duplicate_rows"]
    if not duplicates:
        return [_insight("quality", "positive", "Every row in the dataset is unique.")]
    return [
        _insight(
            "quality",
            "warning",
            f"{overview['duplicate_percentage']}% of rows ({duplicates:,}) are exact duplicates.",
        )
    ]


def _numeric_insights(statistics: dict) -> list[dict]:
    insights: list[dict] = []

    for column in statistics["numeric"]:
        if column.get("all_missing"):
            continue

        if column["outliers"] and column["outlier_percentage"] >= 5:
            insights.append(
                _insight(
                    "distribution",
                    "warning",
                    f"{column['name']} contains {column['outliers']:,} potential outliers "
                    f"({column['outlier_percentage']}% of its values).",
                )
            )

        skew = column.get("skewness")
        if skew is not None and abs(skew) >= SKEW_THRESHOLD:
            direction = "right" if skew > 0 else "left"
            insights.append(
                _insight(
                    "distribution",
                    "neutral",
                    f"{column['name']} is strongly {direction}-skewed "
                    f"(skew {skew}) — a log transform may help.",
                )
            )

        if column["count"] and column["zeros"] / column["count"] >= 0.5:
            insights.append(
                _insight(
                    "distribution",
                    "neutral",
                    f"More than half of {column['name']}'s values are zero.",
                )
            )

    return insights


def _categorical_insights(statistics: dict) -> list[dict]:
    insights: list[dict] = []

    for column in statistics["categorical"]:
        if column.get("all_missing"):
            continue

        insights.append(
            _insight(
                "categories",
                "neutral",
                f"{column['name']} contains {column['unique']} unique "
                f"categor{'ies' if column['unique'] != 1 else 'y'}; "
                f"'{column['top_value']}' covers {column['top_percentage']}% of rows.",
            )
        )

        if column["is_imbalanced"]:
            insights.append(
                _insight(
                    "categories",
                    "warning",
                    f"{column['name']} is heavily imbalanced — one value accounts for "
                    f"{column['top_percentage']}% of the data.",
                )
            )

    return insights


def _correlation_insights(df: pd.DataFrame, profile: dict) -> list[dict]:
    """Pairs of numeric columns that carry nearly the same signal."""
    numeric_columns = profile["column_groups"]["numeric"]
    if len(numeric_columns) < 2:
        return []

    numeric = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    correlations = numeric.corr(numeric_only=True)

    insights: list[dict] = []
    seen: set[frozenset] = set()

    for left in correlations.columns:
        for right in correlations.columns:
            if left == right or frozenset((left, right)) in seen:
                continue
            value = correlations.loc[left, right]
            if pd.isna(value) or abs(value) < CORRELATION_THRESHOLD:
                continue
            seen.add(frozenset((left, right)))
            insights.append(
                _insight(
                    "relationships",
                    "neutral",
                    f"{left} and {right} are highly correlated "
                    f"({round_or_none(value, 2)}) — they may be redundant.",
                )
            )

    return insights[:5]


def generate_insights(
    df: pd.DataFrame, profile: dict, statistics: dict, quality: dict
) -> dict:
    """The full insight list, plus a one-line headline for the dashboard."""
    insights: list[dict] = []
    insights += _shape_insights(profile)
    insights += _missing_insights(profile)
    insights += _duplicate_insights(profile)
    insights += _numeric_insights(statistics)
    insights += _categorical_insights(statistics)
    insights += _correlation_insights(df, profile)

    high_severity = quality["issue_counts"]["high"]
    if high_severity:
        headline = (
            f"This dataset scores {quality['overall_score']}/100 and has "
            f"{high_severity} issue{'s' if high_severity != 1 else ''} worth fixing first."
        )
    else:
        headline = (
            f"This dataset scores {quality['overall_score']}/100 — "
            f"{quality['grade']} quality, ready to work with."
        )

    return {"headline": headline, "insights": insights, "count": len(insights)}
