"""The sklearn preprocessing pipeline.

Imputation, scaling and encoding all live inside a ColumnTransformer that is
fitted as part of the model pipeline, so the exact same transformation is
replayed at prediction time with no chance of train/serve skew.
"""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    """Median-impute and scale numbers; mode-impute and one-hot encode categories."""
    transformers = []

    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        # Median survives the skew and outliers we warn about in profiling.
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )

    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        # Unseen categories at predict time must not raise.
                        (
                            "encode",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical,
            )
        )

    return ColumnTransformer(transformers=transformers, remainder="drop")


def describe_preprocessing(numeric: list[str], categorical: list[str]) -> list[dict]:
    """Plain-language account of what the pipeline does, for the UI."""
    steps = []
    if numeric:
        steps.append(
            {
                "step": "Numeric imputation",
                "detail": f"Filled missing values in {len(numeric)} numeric column(s) with the median.",
            }
        )
        steps.append(
            {
                "step": "Scaling",
                "detail": "Standardised numeric features to zero mean and unit variance.",
            }
        )
    if categorical:
        steps.append(
            {
                "step": "Categorical imputation",
                "detail": f"Filled missing values in {len(categorical)} categorical column(s) with the most frequent value.",
            }
        )
        steps.append(
            {
                "step": "One-hot encoding",
                "detail": "Expanded categories into indicator columns, ignoring unseen values at prediction time.",
            }
        )
    return steps


def prepare_target(y: pd.Series, is_classification: bool) -> pd.Series:
    """Normalise the target so metrics and models agree on its type."""
    if is_classification:
        return y.astype(str)
    return pd.to_numeric(y, errors="coerce")


def clean_training_rows(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Drop rows whose target is missing — they teach the model nothing."""
    mask = y.notna()
    if hasattr(y, "replace"):
        # A stringified NaN target ("nan") is still a missing target.
        mask &= y.astype(str).str.lower() != "nan"
    return X.loc[mask], y.loc[mask]


def feature_names_from(preprocessor: ColumnTransformer) -> list[str]:
    """Output column names after encoding, used to label feature importances."""
    try:
        return [str(name) for name in preprocessor.get_feature_names_out()]
    except Exception:
        # A step without name support: fall back to positional labels.
        width = int(getattr(preprocessor, "n_features_in_", 0) or 0)
        return [f"feature_{index}" for index in range(width)]
