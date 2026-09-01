"""AutoML endpoints: target suggestion, training, run status and prediction.

Training runs in a background task and the frontend polls the run, so a long
run never holds an HTTP request open.
"""

import logging

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from app.core import store
from app.core.errors import DataPilotError
from app.core.serialization import to_native
from app.ml import prediction, training
from app.ml.problem_detection import suggest_targets
from app.services import profiling_service

logger = logging.getLogger("datapilot")

router = APIRouter(tags=["automl"])


class TrainRequest(BaseModel):
    target: str = Field(..., min_length=1, description="Column to predict")


class PredictRequest(BaseModel):
    rows: list[dict] = Field(default_factory=list)


def _execute_run(run_id: str, dataset_id: str, target: str) -> None:
    """Background worker for one training run."""
    def on_progress(stage: str, percent: int) -> None:
        store.update_run(run_id, stage=stage, progress=percent)

    store.update_run(run_id, status="running", stage="Starting", progress=5)
    try:
        df = store.get_dataframe(dataset_id)
        result = training.run_training(df, target, run_id, on_progress)
        store.update_run(
            run_id,
            status="completed",
            stage="Completed",
            progress=100,
            result=to_native(result),
        )
    except DataPilotError as exc:
        store.update_run(
            run_id, status="failed", stage="Failed", progress=100, error=exc.message
        )
    except Exception as exc:
        logger.exception("Training run %s crashed", run_id)
        store.update_run(
            run_id,
            status="failed",
            stage="Failed",
            progress=100,
            error="Training failed unexpectedly. Please try a different target column.",
        )


@router.get("/dataset/{dataset_id}/targets")
def get_target_suggestions(dataset_id: str):
    """Columns that would make sensible prediction targets."""
    df = store.get_dataframe(dataset_id)
    profile = store.cached_analysis(
        dataset_id, "profile", lambda: profiling_service.generate_profile(df)
    )
    return {"success": True, "targets": to_native(suggest_targets(profile))}


@router.post("/dataset/{dataset_id}/train")
def start_training(dataset_id: str, body: TrainRequest, background: BackgroundTasks):
    """Kick off an AutoML run and return the run to poll."""
    store.get_dataframe(dataset_id)  # fail fast if the dataset is gone
    run = store.create_run(dataset_id, body.target)
    background.add_task(_execute_run, run["run_id"], dataset_id, body.target)
    return {"success": True, "run": run}


@router.get("/dataset/{dataset_id}/runs")
def list_dataset_runs(dataset_id: str):
    return {"success": True, "runs": to_native(store.list_runs(dataset_id))}


@router.get("/run/{run_id}")
def get_run(run_id: str):
    """Status and, once finished, the full result of a training run."""
    return {"success": True, "run": to_native(store.get_run(run_id))}


@router.get("/run/{run_id}/schema")
def get_prediction_schema(run_id: str):
    """The input fields this run's model needs in order to predict."""
    return {"success": True, "schema": to_native(prediction.required_columns(run_id))}


@router.post("/run/{run_id}/predict")
def predict(run_id: str, body: PredictRequest):
    return {"success": True, **to_native(prediction.predict(run_id, body.rows))}
