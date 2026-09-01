# DataPilot AI

AI-powered AutoML platform for dataset profiling, preprocessing, model training,
evaluation, explainability, and code generation.

Upload a CSV and DataPilot profiles it, scores its quality, explains what it
found in plain language, trains and compares several models, and hands you a
runnable Python script for the whole thing.

---

## Running it

Backend and frontend run independently.

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

### In GitHub Codespaces

Both commands are the same. Two things matter:

1. **Set port 8000 to Public.** Open the **Ports** tab, right-click port 8000 →
   *Port Visibility* → *Public*. While it is Private the browser is redirected to
   a GitHub login page, and that shows up in the console as a CORS error even
   though CORS is configured correctly. This is the single most common cause of
   "CORS is broken" in this project.
2. **Don't hardcode URLs.** The frontend derives the API URL from whatever host
   it is served from, swapping the forwarded port (`-5173` → `-8000`), and the
   backend allows any `*.app.github.dev` origin by regex. Both survive a
   Codespace rebuild. Override with `VITE_API_URL` only if you need something
   unusual — see `frontend/.env.example` and `backend/.env.example`.

### Try it

`samples/employees.csv` is included to exercise every code path: numeric,
categorical, boolean and date columns, a constant column (`legacy_flag`), a
mostly-empty column (`notes`), missing values in `satisfaction_score`, two exact
duplicate rows, and correlated numerics. Good targets to train on are
`department` (multiclass) or `salary` (regression).

---

## Architecture

```
React + Vite (5173)  ──HTTP──>  FastAPI (8000)
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
                 services/        ml/           core/
              profiling         training       store
              statistics        evaluation     errors
              quality           preprocessing  serialization
              insights          prediction
              csv / code
```

`main.py` only wires up CORS, error handling and routers. All logic lives in
`services/` (analysis) and `ml/` (modelling), so either can be changed or tested
without touching the API layer.

### Backend layout

```
backend/app/
├── main.py                  FastAPI app assembly
├── config.py                environment-driven settings (no hardcoded hosts)
├── api/
│   ├── upload.py            POST /upload
│   ├── dataset.py           GET /dataset/{id}/...
│   └── automl.py            training, run status, prediction
├── core/
│   ├── errors.py            typed errors → clean JSON, never a traceback
│   ├── store.py             dataset + run persistence
│   └── serialization.py     numpy/pandas → JSON-safe values
├── services/
│   ├── csv_service.py       validation, parsing, preview
│   ├── profiling_service.py shape, semantic types, missingness, cardinality
│   ├── statistics_service.py per-column summaries and histograms
│   ├── quality_service.py   dimension scores and ranked issues
│   ├── insights_service.py  plain-language findings
│   └── code_service.py      generated Python script
└── ml/
    ├── problem_detection.py classification vs regression, target suggestions
    ├── feature_engineering.py feature selection, date expansion
    ├── preprocessing.py     impute / scale / encode pipeline
    ├── model_selection.py   the candidate models
    ├── training.py          the AutoML run
    ├── evaluation.py        metrics, ranking, feature importance
    └── prediction.py        serving predictions
```

### API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/upload` | Upload a CSV, get a `dataset_id` |
| `GET` | `/dataset/{id}` | Dataset metadata |
| `GET` | `/dataset/{id}/preview` | First rows and dtypes |
| `GET` | `/dataset/{id}/profile` | Structure, types, missingness |
| `GET` | `/dataset/{id}/statistics` | Per-column stats and histograms |
| `GET` | `/dataset/{id}/quality` | Scores and ranked issues |
| `GET` | `/dataset/{id}/insights` | Plain-language findings |
| `GET` | `/dataset/{id}/summary` | All of the above in one request |
| `GET` | `/dataset/{id}/code` | Generated Python script |
| `GET` | `/dataset/{id}/targets` | Suggested prediction targets |
| `POST` | `/dataset/{id}/train` | Start an AutoML run |
| `GET` | `/dataset/{id}/runs` | Runs for a dataset |
| `GET` | `/run/{run_id}` | Run status and result |
| `GET` | `/run/{run_id}/schema` | Input fields the model needs |
| `POST` | `/run/{run_id}/predict` | Predict on new rows |

---

## What it does

**Profiling** — row/column counts, memory, duplicates, and per column: pandas
dtype plus a *semantic* type (numeric, categorical, boolean, datetime, text,
identifier), missing count and percentage, cardinality, and flags for constant,
empty and ID-like columns.

**Statistics** — mean, median, std, min/max, quartiles, IQR, skew, kurtosis,
zero and negative counts, and IQR-rule outliers for numeric columns; cardinality,
top values and frequency distributions for categorical ones; range and span for
dates.

**Quality** — completeness, uniqueness, consistency and type integrity scored
0–100 and combined into a weighted health score, alongside a severity-ranked
issue list with a recommendation for each.

**Insights** — findings in sentences: which columns are missing values, how
skewed a distribution is, which categories dominate, which numeric pairs are
nearly redundant.

**AutoML** — detects whether the target is binary, multiclass or regression;
selects features and explains every exclusion; imputes, scales and one-hot
encodes; trains four to five candidate models; ranks them on a held-out split;
and reports feature importance for the winner. The trained model is saved and can
predict on new rows.

**Code generation** — the same analysis as a standalone pandas/scikit-learn
script, optionally including a full model pipeline for a chosen target.

---

## Storage

Uploaded CSVs and trained models are written to `backend/uploads/` (git-ignored)
with a small JSON sidecar per dataset, so datasets survive a server reload.
Training runs are held in memory and do not.

This is deliberately file-based rather than a database — enough for single-user
development, and isolated behind `core/store.py` so swapping in a real database
touches one module.
