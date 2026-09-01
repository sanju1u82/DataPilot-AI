"""FastAPI application entry point.

Wires up CORS, error handling, the API routers and — when a frontend build is
present — the React app itself. All business logic lives in `services` and
`ml`; this module only assembles the app.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.automl import router as automl_router
from app.api.dataset import router as dataset_router
from app.api.upload import router as upload_router
from app.config import get_allowed_origin_regex, get_allowed_origins
from app.core.errors import register_exception_handlers
from app.core.frontend import mount_frontend

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="DataPilot AI",
    description="AI-powered AutoML and data analysis platform",
    version="2.0.0",
)

allowed_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # The regex covers Codespaces and Gitpod, whose hostnames are generated per
    # container and so cannot be listed ahead of time.
    allow_origin_regex=get_allowed_origin_regex(),
    # A wildcard origin and credentials are mutually exclusive under the CORS
    # spec; browsers reject the combination outright.
    allow_credentials="*" not in allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(upload_router)
app.include_router(dataset_router)
app.include_router(automl_router)


@app.get("/health", tags=["meta"])
def health():
    """Liveness check, and a quick way to confirm CORS is configured."""
    return {"status": "ok", "allowed_origins": allowed_origins}


# Must come after every API route: when a frontend build is present this claims
# the remaining paths, including "/", and serves the React app from them.
frontend_mounted = mount_frontend(app)

if not frontend_mounted:
    @app.get("/", tags=["meta"])
    def root():
        return {
            "name": "DataPilot AI",
            "version": app.version,
            "docs": "/docs",
            "message": "Welcome to DataPilot AI",
        }
