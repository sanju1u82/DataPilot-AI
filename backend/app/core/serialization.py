"""Conversion of pandas/numpy values into JSON-safe Python types.

NumPy scalars (np.int64, np.float32, np.bool_) are not JSON serializable, and
NaN/Infinity are not valid JSON, so every value leaving a service goes through
`to_native` before it reaches a response.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def to_native(value: Any) -> Any:
    """Recursively convert a value into something `json.dumps` accepts."""
    if value is None or isinstance(value, (str, bool)):
        return value

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, (int, np.integer)):
        return int(value)

    if isinstance(value, (float, np.floating)):
        number = float(value)
        # NaN and +/-Infinity have no JSON representation.
        return None if math.isnan(number) or math.isinf(number) else number

    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()

    if isinstance(value, pd.Timedelta):
        return str(value)

    if value is pd.NaT:
        return None

    if isinstance(value, dict):
        return {str(to_native(k)): to_native(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set, np.ndarray, pd.Index)):
        return [to_native(item) for item in value]

    if isinstance(value, pd.Series):
        return {str(to_native(k)): to_native(v) for k, v in value.items()}

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return str(value)


def round_or_none(value: Any, digits: int = 4) -> float | None:
    """Round a numeric value, collapsing NaN/Inf/non-numeric to None."""
    native = to_native(value)
    if isinstance(native, bool) or not isinstance(native, (int, float)):
        return None
    return round(float(native), digits)
