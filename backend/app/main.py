#initialize the application
#main.py does not get called every time a request comes in.

from fastapi import FastAPI
from app.api.upload import router as upload_router

app = FastAPI(
    title="DataPilot AI",
    description="AI-powered AutoML Platform",
    version="1.0.0"
)

app.include_router(upload_router)


@app.get("/")
def root():
    return {"message": "Welcome to DataPilot AI"}