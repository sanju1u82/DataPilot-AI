#initialize the application
#main.py does not get called every time a request comes in.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router

app = FastAPI(
    title="DataPilot AI",
    description="AI-powered AutoML Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://refactored-space-chainsaw-9796q9gqgqx529x4w-5173.app.github.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)

@app.get("/")
def root():
    return {"message": "Welcome to DataPilot AI"}