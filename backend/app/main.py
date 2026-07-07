#initialize the application
#main.py does not get called every time a request comes in.

from fastapi import FastAPI

app = FastAPI(
    title="DataPilot AI",
    description="AI-powered AutoML platform",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Welcome to DataPilot AI"}