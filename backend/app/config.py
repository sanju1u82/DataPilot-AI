"""Application configuration.

Everything environment-dependent lives here so that no hostname, port or path
is hardcoded inside application logic. In Codespaces the frontend origin changes
every time the container is rebuilt, so it is read from the environment instead.
"""

import os
from pathlib import Path

# backend/app/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = Path(os.getenv("DATAPILOT_UPLOAD_DIR", BACKEND_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Largest CSV we accept, in bytes. Keeps a stray 2 GB file from taking the app down.
MAX_UPLOAD_BYTES = int(os.getenv("DATAPILOT_MAX_UPLOAD_MB", "100")) * 1024 * 1024

# Rows sent to the frontend for the preview table.
PREVIEW_ROW_COUNT = 20

# Above this row count, model training works on a random sample so that a large
# upload does not block the worker for minutes.
MAX_TRAINING_ROWS = 20_000

# A column with more distinct values than this is treated as free text / an ID
# rather than as a categorical feature.
MAX_CATEGORICAL_CARDINALITY = 50


def _split_env_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def get_allowed_origins() -> list[str]:
    """Origins the browser may call this API from.

    Set DATAPILOT_ALLOWED_ORIGINS to a comma-separated list to override. The
    default covers local Vite plus any GitHub Codespaces or Gitpod host, which
    is what makes this survive a Codespace rebuild.
    """
    configured = os.getenv("DATAPILOT_ALLOWED_ORIGINS", "")
    if configured.strip() == "*":
        return ["*"]
    if configured.strip():
        return _split_env_list(configured)

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]


def get_allowed_origin_regex() -> str | None:
    """Regex fallback for hosts whose name is not known ahead of time.

    Codespaces forwards ports as https://<name>-<port>.app.github.dev, and the
    name is generated per container, so it cannot be listed explicitly.
    """
    configured = os.getenv("DATAPILOT_ALLOWED_ORIGIN_REGEX", "")
    if configured.strip():
        return configured.strip()

    return r"https://.*\.(app\.github\.dev|githubpreview\.dev|gitpod\.io)"
