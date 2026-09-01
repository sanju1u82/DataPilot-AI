"""Data quality scoring.

Turns the raw profile into four 0-100 dimension scores plus a weighted overall
health score, and a severity-ranked list of concrete issues. The scores are what
the dashboard's progress bars render.
"""

from __future__ import annotations

from app.core.serialization import round_or_none
from app.services.profiling_service import IDENTIFIER, TEXT

# Weights for the overall health score. Completeness and uniqueness dominate
# because missing values and duplicated rows do the most damage downstream.
WEIGHTS = {
    "completeness": 0.35,
    "uniqueness": 0.25,
    "consistency": 0.25,
    "type_integrity": 0.15,
}

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _grade(score: float) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 60:
        return "fair"
    return "poor"


def _completeness_score(profile: dict) -> float:
    return max(0.0, 100.0 - float(profile["overview"]["missing_percentage"] or 0))


def _uniqueness_score(profile: dict) -> float:
    return max(0.0, 100.0 - float(profile["overview"]["duplicate_percentage"] or 0))


def _consistency_score(profile: dict) -> float:
    """Share of columns that carry usable, varying information."""
    columns = profile["columns"]
    if not columns:
        return 0.0
    unusable = sum(1 for column in columns if column["is_constant"] or column["is_empty"])
    return (len(columns) - unusable) / len(columns) * 100


def _type_integrity_score(profile: dict) -> float:
    """Share of columns that landed on a modelling-friendly type."""
    columns = profile["columns"]
    if not columns:
        return 0.0
    ambiguous = sum(
        1 for column in columns if column["semantic_type"] in (TEXT, IDENTIFIER)
    )
    return (len(columns) - ambiguous) / len(columns) * 100


def _collect_issues(profile: dict) -> list[dict]:
    """Concrete, individually fixable problems, worst first."""
    issues: list[dict] = []
    overview = profile["overview"]

    missing_pct = float(overview["missing_percentage"] or 0)
    if missing_pct > 0:
        affected = len(profile["missing_by_column"])
        issues.append(
            {
                "type": "missing_values",
                "severity": "high" if missing_pct >= 20 else "medium" if missing_pct >= 5 else "low",
                "title": "Missing values",
                "message": (
                    f"{missing_pct}% of all cells are empty, "
                    f"across {affected} column{'s' if affected != 1 else ''}."
                ),
                "recommendation": "Impute or drop the affected rows before modelling.",
            }
        )

    duplicates = int(overview["duplicate_rows"] or 0)
    if duplicates > 0:
        duplicate_pct = float(overview["duplicate_percentage"] or 0)
        issues.append(
            {
                "type": "duplicate_rows",
                "severity": "high" if duplicate_pct >= 10 else "medium",
                "title": "Duplicate rows",
                "message": f"{duplicates:,} rows ({duplicate_pct}%) are exact duplicates.",
                "recommendation": "Drop duplicates so they don't bias the model.",
            }
        )

    constant = [c["name"] for c in profile["columns"] if c["is_constant"] and not c["is_empty"]]
    if constant:
        issues.append(
            {
                "type": "constant_columns",
                "severity": "medium",
                "title": "Constant columns",
                "message": f"{', '.join(constant[:5])} never change value.",
                "recommendation": "Drop them — they carry no information.",
            }
        )

    empty = [c["name"] for c in profile["columns"] if c["is_empty"]]
    if empty:
        issues.append(
            {
                "type": "empty_columns",
                "severity": "high",
                "title": "Empty columns",
                "message": f"{', '.join(empty[:5])} contain no values at all.",
                "recommendation": "Remove these columns from the dataset.",
            }
        )

    identifiers = [c["name"] for c in profile["columns"] if c["is_identifier"]]
    if identifiers:
        issues.append(
            {
                "type": "identifier_columns",
                "severity": "low",
                "title": "Identifier columns",
                "message": f"{', '.join(identifiers[:5])} hold a unique value per row.",
                "recommendation": "Exclude them from training — they can't generalise.",
            }
        )

    high_missing = [
        c["name"] for c in profile["columns"]
        if not c["is_empty"] and (c["missing_percentage"] or 0) >= 40
    ]
    if high_missing:
        issues.append(
            {
                "type": "sparse_columns",
                "severity": "high",
                "title": "Sparse columns",
                "message": f"{', '.join(high_missing[:5])} are more than 40% empty.",
                "recommendation": "Consider dropping them rather than imputing.",
            }
        )

    issues.sort(key=lambda issue: SEVERITY_ORDER[issue["severity"]])
    return issues


def generate_quality_report(profile: dict) -> dict:
    """Dimension scores, overall health and the ranked issue list."""
    scores = {
        "completeness": _completeness_score(profile),
        "uniqueness": _uniqueness_score(profile),
        "consistency": _consistency_score(profile),
        "type_integrity": _type_integrity_score(profile),
    }

    overall = sum(scores[key] * WEIGHTS[key] for key in WEIGHTS)
    issues = _collect_issues(profile)

    return {
        "overall_score": round_or_none(overall, 1),
        "grade": _grade(overall),
        "dimensions": [
            {
                "key": key,
                "label": label,
                "score": round_or_none(scores[key], 1),
                "grade": _grade(scores[key]),
                "description": description,
            }
            for key, label, description in (
                ("completeness", "Completeness", "How much of the data is actually filled in"),
                ("uniqueness", "Uniqueness", "How free the dataset is of duplicate rows"),
                ("consistency", "Consistency", "How many columns carry varying, usable values"),
                ("type_integrity", "Type integrity", "How many columns have a clear, modellable type"),
            )
        ],
        "issues": issues,
        "issue_counts": {
            "high": sum(1 for i in issues if i["severity"] == "high"),
            "medium": sum(1 for i in issues if i["severity"] == "medium"),
            "low": sum(1 for i in issues if i["severity"] == "low"),
        },
    }
