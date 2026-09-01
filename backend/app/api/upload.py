"""Dataset upload endpoint."""

from fastapi import APIRouter, File, UploadFile

from app.services import csv_service

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Accept a CSV, validate and store it, and return its identifier.

    Only the identifier and headline numbers come back here; the dashboard
    fetches the analysis by id, so a page refresh does not need a re-upload.
    """
    raw = await file.read()
    metadata = csv_service.ingest_csv(file.filename, raw)

    return {"success": True, "dataset": metadata}
