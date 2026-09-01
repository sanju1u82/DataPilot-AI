"""Serving the built React app from the API process.

In development Vite serves the frontend on its own port and this does nothing.
In a deployment the built assets sit next to the API, so one service answers
both the app and its API on one origin — which removes CORS from the picture
entirely rather than configuring around it.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIST

logger = logging.getLogger("datapilot")

# First path segments that belong to the API. Anything else is a client-side
# route and must fall through to index.html so a refresh on /dashboard/<id>
# does not 404.
RESERVED_PREFIXES = {
    "upload",
    "dataset",
    "run",
    "health",
    "docs",
    "redoc",
    "openapi.json",
}


def frontend_is_built(dist: Path = FRONTEND_DIST) -> bool:
    return (dist / "index.html").is_file()


def mount_frontend(app: FastAPI, dist: Path = FRONTEND_DIST) -> bool:
    """Serve the built frontend, if there is one. Returns whether it mounted."""
    if not frontend_is_built(dist):
        logger.info("No frontend build at %s — running as an API-only service.", dist)
        return False

    dist = dist.resolve()
    index_html = dist / "index.html"

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    # Registered last, so every API route above already had its chance to match.
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        first_segment = full_path.split("/", 1)[0]
        if first_segment in RESERVED_PREFIXES:
            # An unmatched API path should 404 as JSON, not as the app shell.
            raise HTTPException(status_code=404, detail="Not found")

        if full_path:
            candidate = (dist / full_path).resolve()
            # Only serve files genuinely inside dist — never follow "../" out of it.
            if candidate.is_file() and dist in candidate.parents:
                return FileResponse(candidate)

        return FileResponse(index_html)

    logger.info("Serving frontend from %s", dist)
    return True
