"""The candidate models DataPilot tries for each problem type.

Adding a model means adding one entry here — nothing in training or evaluation
needs to change.
"""

from __future__ import annotations

from typing import Callable

from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from app.ml.problem_detection import REGRESSION

RANDOM_STATE = 42


class Candidate:
    """One model the AutoML run will train and score."""

    def __init__(self, key: str, name: str, description: str, factory: Callable):
        self.key = key
        self.name = name
        self.description = description
        self.factory = factory

    def build(self):
        return self.factory()


CLASSIFIERS = [
    Candidate(
        "logistic_regression",
        "Logistic Regression",
        "Fast linear baseline. Easy to interpret, struggles with non-linear patterns.",
        lambda: LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    ),
    Candidate(
        "decision_tree",
        "Decision Tree",
        "Human-readable rules. Prone to overfitting on its own.",
        lambda: DecisionTreeClassifier(max_depth=12, random_state=RANDOM_STATE),
    ),
    Candidate(
        "random_forest",
        "Random Forest",
        "Many trees voting together. Strong general-purpose default.",
        lambda: RandomForestClassifier(
            n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1
        ),
    ),
    Candidate(
        "gradient_boosting",
        "Gradient Boosting",
        "Trees built to correct each other. Usually the most accurate, slower to train.",
        lambda: GradientBoostingClassifier(random_state=RANDOM_STATE),
    ),
]

REGRESSORS = [
    Candidate(
        "linear_regression",
        "Linear Regression",
        "Straight-line baseline. Interpretable coefficients.",
        lambda: LinearRegression(),
    ),
    Candidate(
        "ridge",
        "Ridge Regression",
        "Linear regression with regularisation, steadier when features correlate.",
        lambda: Ridge(random_state=RANDOM_STATE),
    ),
    Candidate(
        "decision_tree",
        "Decision Tree",
        "Captures non-linear splits. Prone to overfitting on its own.",
        lambda: DecisionTreeRegressor(max_depth=12, random_state=RANDOM_STATE),
    ),
    Candidate(
        "random_forest",
        "Random Forest",
        "Many trees averaged together. Strong general-purpose default.",
        lambda: RandomForestRegressor(
            n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1
        ),
    ),
    Candidate(
        "gradient_boosting",
        "Gradient Boosting",
        "Trees built to correct each other. Usually the most accurate, slower to train.",
        lambda: GradientBoostingRegressor(random_state=RANDOM_STATE),
    ),
]


def candidates_for(problem_type: str) -> list[Candidate]:
    return REGRESSORS if problem_type == REGRESSION else CLASSIFIERS
