"""Reading, validating and registering uploaded CSV files."""

from __future__ import annotations

import io

import pandas as pd

from app.config import MAX_UPLOAD_BYTES, PREVIEW_ROW_COUNT
from app.core import store
from app.core.errors import (
    EmptyDatasetError,
    FileTooLargeError,
    UnreadableDatasetError,
    UnsupportedFileError,
)
from app.core.serialization import to_native

ALLOWED_EXTENSIONS = (".csv", ".txt", ".tsv")


def validate_upload(filename: str | None, raw: bytes) -> None:
    """Reject anything we cannot analyze before spending time parsing it."""
    if not filename or not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise UnsupportedFileError()

    if not raw:
        raise EmptyDatasetError()

    if len(raw) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise FileTooLargeError(
            f"This file is larger than the {limit_mb} MB limit. "
            "Try uploading a sample of the dataset instead."
        )


def parse_csv(raw: bytes, filename: str) -> pd.DataFrame:
    """Parse raw bytes into a DataFrame, tolerating non-UTF-8 encodings."""
    separator = "\t" if filename.lower().endswith(".tsv") else ","

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(raw), sep=separator, encoding=encoding)
            break
        except pd.errors.EmptyDataError as exc:
            raise EmptyDatasetError() from exc
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            last_error = exc
            continue
    else:
        raise UnreadableDatasetError(detail=str(last_error))

    if df.empty or df.shape[1] == 0:
        raise EmptyDatasetError()

    df.columns = [str(column).strip() for column in df.columns]
    return df


def build_preview(df: pd.DataFrame, limit: int = PREVIEW_ROW_COUNT) -> dict:
    """The first rows of the dataset, shaped for the preview table."""
    head = df.head(limit)
    return {
        "columns": [str(column) for column in df.columns],
        "rows": [
            {str(column): to_native(value) for column, value in record.items()}
            for record in head.to_dict(orient="records")
        ],
        "showing": int(head.shape[0]),
        "total_rows": int(df.shape[0]),
        "data_types": {str(col): str(dtype) for col, dtype in df.dtypes.items()},
    }


def ingest_csv(filename: str | None, raw: bytes) -> dict:
    """Validate, parse and store an upload. Returns the dataset metadata."""
    validate_upload(filename, raw)
    df = parse_csv(raw, filename or "dataset.csv")
    return store.create_dataset(filename or "dataset.csv", raw, df)
