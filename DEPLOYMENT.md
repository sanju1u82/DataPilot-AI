# Deploying DataPilot AI

The whole app ships as **one Docker image**: the React build is served by the
FastAPI process, so there is a single service on a single origin. Nothing to
wire between two deployments, and CORS never applies in production.

```
Dockerfile
├── stage 1  node:22-alpine   npm ci && npm run build   → frontend/dist
└── stage 2  python:3.12-slim pip install -r requirements.txt
                              + /app/frontend_dist       → uvicorn on $PORT
```

---

## Before you deploy: run it once

Nothing in this repo has been executed yet. A cloud build failing at step 40 is
a slow way to find a typo, so verify locally first — Codespaces already has
Python and Node:

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run build && npm run dev
```

`npm run build` is the one that matters here — it's exactly what stage 1 of the
Docker build runs. If it passes and the app works against the local API, the
image will almost certainly build.

---

## Option A — Render (recommended)

Free, no credit card, deploys straight from the repo.

1. Push this branch and merge it to `main` (Render's free tier deploys a branch
   you choose; `main` is the least surprising).
2. Sign in at [render.com](https://render.com) with your GitHub account.
3. **New → Blueprint**, pick `sanju1u82/DataPilot-AI`. Render reads
   `render.yaml` and proposes one Docker web service.
4. **Apply**. First build takes roughly 5–10 minutes (installing pandas and
   scikit-learn is the slow part).
5. You get `https://datapilot-ai.onrender.com` (or similar). `/health` should
   return `{"status":"ok"}` and `/docs` gives you the API explorer.

**What the free tier costs you.** The service sleeps after 15 minutes of
inactivity, so the first request after a nap takes ~50 seconds — the app looks
broken until it wakes. Disk is ephemeral: uploaded CSVs and trained models are
wiped on every restart and redeploy, so a dataset id from yesterday will 404.
And 512 MB RAM is genuinely tight for pandas plus scikit-learn — a Random
Forest on a large upload can get OOM-killed. All fine for a portfolio demo; not
fine for real users.

## Option B — Hugging Face Spaces

Better fit if you care about the AutoML actually completing: free tier gives
**16 GB RAM and 2 vCPU** versus Render's 512 MB, and it doesn't sleep the same
way. Also no credit card.

1. [huggingface.co/new-space](https://huggingface.co/new-space) → SDK **Docker**
   → blank template.
2. Push this repo to the Space's git remote (or link the GitHub repo).
3. The Space's own `README.md` needs this frontmatter so it knows the port:

   ```yaml
   ---
   title: DataPilot AI
   emoji: 🚀
   sdk: docker
   app_port: 8000
   ---
   ```

Storage is still ephemeral — uploads don't survive a restart.

## Option C — Anywhere else

The `Dockerfile` is host-agnostic and reads `$PORT`. Railway, Fly.io, Google
Cloud Run and Azure Container Apps all take it as-is. Railway and Fly want a
card on file even on their free allowances.

---

## Making uploads survive a restart

Every free tier above has ephemeral disk. Two ways out, in order of effort:

1. **Attach a persistent disk** mounted at `/app/uploads` (Render calls these
   Disks; it's a paid feature). `DATAPILOT_UPLOAD_DIR` already points there, so
   nothing in the code changes.
2. **Swap the store for object storage or a database.** Everything that touches
   persistence lives in `backend/app/core/store.py` — replacing the file reads
   and writes there with S3 or Postgres touches that one module and nothing else.

---

## Deploying the two halves separately

If you'd rather host the frontend on Vercel or Netlify and the API elsewhere,
that still works — the single-image setup is a default, not a constraint:

- Build the frontend with `VITE_API_URL=https://your-api-host` set. That
  overrides the same-origin default in `frontend/src/services/api.js`.
- Set `DATAPILOT_ALLOWED_ORIGINS=https://your-frontend-host` on the API, since
  CORS now does apply. See `backend/.env.example`.
