from fastapi import APIRouter, UploadFile, File
from app.services.csv_service import read_csv_file

router = APIRouter()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    result = read_csv_file(file)
    return result