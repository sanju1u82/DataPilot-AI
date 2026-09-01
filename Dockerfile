# DataPilot AI — single-image build.
#
# Stage 1 builds the React app; stage 2 runs FastAPI and serves that build from
# the same process. One service, one origin, so CORS never applies in production.

# --- Stage 1: build the frontend ----------------------------------------
# Vite 8 requires Node 20.19+ / 22.12+.
FROM node:22-alpine AS frontend

WORKDIR /build

# Copy manifests first so the dependency layer is cached across source edits.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# No VITE_API_URL: a production build talks to its own origin.
RUN npm run build


# --- Stage 2: runtime ----------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DATAPILOT_FRONTEND_DIST=/app/frontend_dist \
    DATAPILOT_UPLOAD_DIR=/app/uploads

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend /build/dist ./frontend_dist

# Run unprivileged, and make the upload directory writable by that user —
# several hosts (Hugging Face Spaces among them) run containers as uid 1000.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Shell form so ${PORT} is expanded — hosts inject the port they want.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
