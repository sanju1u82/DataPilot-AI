"""Dataset and training-run storage.

Datasets are written to disk (CSV plus a small JSON sidecar) so they survive a
server reload, which is what makes the GET /dataset/{id}/... endpoints usable.
Parsed DataFrames are cached in memory and re-read from disk on a miss.

Training runs are kept in memory only; a run that was interrupted by a restart
is not worth resuming.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import UPLOAD_DIR
from app.core.errors import DatasetNotFoundError, RunNotFoundError

_lock = threading.Lock()

# dataset_id -> parsed DataFrame
_frames: dict[str, pd.DataFrame] = {}
# dataset_id -> cached analysis payloads, keyed by section name
_analysis_cache: dict[str, dict[str, Any]] = {}
# run_id -> training run record
_runs: dict[str, dict[str, Any]] = {}

# How many parsed DataFrames to hold in memory at once.
_MAX_CACHED_FRAMES = 8


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _csv_path(dataset_id: str) -> Path:
    return UPLOAD_DIR / f"{dataset_id}.csv"


def _meta_path(dataset_id: str) -> Path:
    return UPLOAD_DIR / f"{dataset_id}.json"


def create_dataset(filename: str, raw: bytes, df: pd.DataFrame) -> dict[str, Any]:
    """Persist an uploaded dataset and return its metadata record."""
    dataset_id = uuid.uuid4().hex[:12]

    _csv_path(dataset_id).write_bytes(raw)

    meta = {
        "dataset_id": dataset_id,
        "filename": filename,
        "uploaded_at": _now(),
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "size_bytes": len(raw),
    }
    _meta_path(dataset_id).write_text(json.dumps(meta, indent=2), encoding="utf-8")

    with _lock:
        _frames[dataset_id] = df
        _analysis_cache[dataset_id] = {}
        _evict_frames_if_needed(keep=dataset_id)

    return meta


def _evict_frames_if_needed(keep: str) -> None:
    """Drop the oldest cached frames once we hold too many. Caller holds the lock."""
    while len(_frames) > _MAX_CACHED_FRAMES:
        for key in _frames:
            if key != keep:
                _frames.pop(key)
                break
        else:
            return


def get_metadata(dataset_id: str) -> dict[str, Any]:
    path = _meta_path(dataset_id)
    if not path.exists():
        raise DatasetNotFoundError()
    return json.loads(path.read_text(encoding="utf-8"))


def get_dataframe(dataset_id: str) -> pd.DataFrame:
    """Return the parsed dataset, reading it back from disk on a cache miss."""
    with _lock:
        cached = _frames.get(dataset_id)
    if cached is not None:
        return cached

    path = _csv_path(dataset_id)
    if not path.exists():
        raise DatasetNotFoundError()

    df = pd.read_csv(path)
    with _lock:
        _frames[dataset_id] = df
        _analysis_cache.setdefault(dataset_id, {})
        _evict_frames_if_needed(keep=dataset_id)
    return df


def cached_analysis(dataset_id: str, section: str, build) -> Any:
    """Return a memoized analysis section, computing it on first request.

    Profiling a wide dataset is not free, and the dashboard asks for several
    sections at once, so each one is computed only the first time.
    """
    with _lock:
        section_cache = _analysis_cache.setdefault(dataset_id, {})
        if section in section_cache:
            return section_cache[section]

    value = build()

    with _lock:
        _analysis_cache.setdefault(dataset_id, {})[section] = value
    return value


# --- training runs -------------------------------------------------------


def create_run(dataset_id: str, target: str) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:12]
    run = {
        "run_id": run_id,
        "dataset_id": dataset_id,
        "target": target,
        "status": "queued",
        "stage": "Queued",
        "progress": 0,
        "created_at": _now(),
        "result": None,
        "error": None,
    }
    with _lock:
        _runs[run_id] = run
    return dict(run)


def update_run(run_id: str, **fields: Any) -> None:
    with _lock:
        run = _runs.get(run_id)
        if run is None:
            return
        run.update(fields)
        run["updated_at"] = _now()


def get_run(run_id: str) -> dict[str, Any]:
    with _lock:
        run = _runs.get(run_id)
        if run is None:
            raise RunNotFoundError()
        return dict(run)


def list_runs(dataset_id: str) -> list[dict[str, Any]]:
    with _lock:
        runs = [dict(r) for r in _runs.values() if r["dataset_id"] == dataset_id]
    runs.sort(key=lambda r: r["created_at"], reverse=True)
    return runs
