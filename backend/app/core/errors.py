"""Application errors and their HTTP representation.

Every failure the user can cause has a matching class here with a message that
is safe to show in the UI. Anything else is caught by the catch-all handler and
reported generically, so a Python traceback never reaches the browser.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("datapilot")


class DataPilotError(Exception):
    """Base class for failures we can explain to the user."""

    status_code = 400
    code = "error"
    message = "Something went wrong."

    def __init__(self, message: str | None = None, detail: str | None = None):
        self.message = message or self.message
        self.detail = detail
        super().__init__(self.message)

    def to_payload(self) -> dict:
        payload = {"success": False, "code": self.code, "message": self.message}
        if self.detail:
            payload["detail"] = self.detail
        return payload


class UnsupportedFileError(DataPilotError):
    status_code = 415
    code = "unsupported_file"
    message = "This file format isn't supported. Please upload a CSV file."


class FileTooLargeError(DataPilotError):
    status_code = 413
    code = "file_too_large"
    message = "This file is too large to analyze."


class EmptyDatasetError(DataPilotError):
    status_code = 422
    code = "empty_dataset"
    message = (
        "The uploaded dataset appears to be empty. "
        "Please upload a dataset containing data."
    )


class UnreadableDatasetError(DataPilotError):
    status_code = 422
    code = "unreadable_dataset"
    message = (
        "We couldn't read this file as a CSV. "
        "Check that it is comma-separated and has a header row."
    )


class DatasetNotFoundError(DataPilotError):
    status_code = 404
    code = "dataset_not_found"
    message = "We couldn't find that dataset. It may have expired — try uploading it again."


class RunNotFoundError(DataPilotError):
    status_code = 404
    code = "run_not_found"
    message = "We couldn't find that training run."


class InvalidTargetError(DataPilotError):
    status_code = 422
    code = "invalid_target"
    message = "That column can't be used as a prediction target."


class TrainingFailedError(DataPilotError):
    status_code = 422
    code = "training_failed"
    message = "We couldn't train a model on this dataset."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DataPilotError)
    async def handle_known_error(_: Request, exc: DataPilotError):
        logger.info("Handled error: %s (%s)", exc.code, exc.detail or exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        # Full detail to the server log, a generic message to the browser.
        logger.exception("Unhandled error on %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "internal_error",
                "message": "We couldn't analyze this dataset. Please try again.",
            },
        )
