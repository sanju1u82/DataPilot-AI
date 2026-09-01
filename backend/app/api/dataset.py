"""Read endpoints for an uploaded dataset.

Each analysis section is available on its own, plus a `/summary` route that
returns all of them in one request — which is what the dashboard uses on load.
"""

from fastapi import APIRouter

from app.core import store
from app.core.serialization import to_native
from app.services import (
    code_service,
    csv_service,
    insights_service,
    profiling_service,
    quality_service,
    statistics_service,
)

router = APIRouter(prefix="/dataset", tags=["dataset"])


def _profile(dataset_id: str) -> dict:
    df = store.get_dataframe(dataset_id)
    return store.cached_analysis(
        dataset_id, "profile", lambda: profiling_service.generate_profile(df)
    )


def _statistics(dataset_id: str) -> dict:
    df = store.get_dataframe(dataset_id)
    return store.cached_analysis(
        dataset_id, "statistics", lambda: statistics_service.generate_statistics(df)
    )


def _quality(dataset_id: str) -> dict:
    return store.cached_analysis(
        dataset_id, "quality", lambda: quality_service.generate_quality_report(_profile(dataset_id))
    )


def _insights(dataset_id: str) -> dict:
    df = store.get_dataframe(dataset_id)
    return store.cached_analysis(
        dataset_id,
        "insights",
        lambda: insights_service.generate_insights(
            df, _profile(dataset_id), _statistics(dataset_id), _quality(dataset_id)
        ),
    )


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    """Metadata for an uploaded dataset."""
    store.get_dataframe(dataset_id)  # raises if the dataset is gone
    return {"success": True, "dataset": store.get_metadata(dataset_id)}


@router.get("/{dataset_id}/preview")
def get_preview(dataset_id: str):
    df = store.get_dataframe(dataset_id)
    return {"success": True, "preview": to_native(csv_service.build_preview(df))}


@router.get("/{dataset_id}/profile")
def get_profile(dataset_id: str):
    return {"success": True, "profile": to_native(_profile(dataset_id))}


@router.get("/{dataset_id}/statistics")
def get_statistics(dataset_id: str):
    return {"success": True, "statistics": to_native(_statistics(dataset_id))}


@router.get("/{dataset_id}/quality")
def get_quality(dataset_id: str):
    return {"success": True, "quality": to_native(_quality(dataset_id))}


@router.get("/{dataset_id}/insights")
def get_insights(dataset_id: str):
    return {"success": True, "insights": to_native(_insights(dataset_id))}


@router.get("/{dataset_id}/summary")
def get_summary(dataset_id: str):
    """Everything the dashboard needs, in a single round trip."""
    df = store.get_dataframe(dataset_id)

    return {
        "success": True,
        "dataset": store.get_metadata(dataset_id),
        "preview": to_native(csv_service.build_preview(df)),
        "profile": to_native(_profile(dataset_id)),
        "statistics": to_native(_statistics(dataset_id)),
        "quality": to_native(_quality(dataset_id)),
        "insights": to_native(_insights(dataset_id)),
    }


@router.get("/{dataset_id}/code")
def get_code(dataset_id: str, target: str | None = None):
    """A runnable Python script reproducing this analysis outside the app."""
    metadata = store.get_metadata(dataset_id)
    return {
        "success": True,
        "code": code_service.generate_analysis_script(
            metadata, _profile(dataset_id), target
        ),
    }
