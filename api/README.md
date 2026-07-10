# Medicafe API

FastAPI backend for the **Modern Workflow** UI. Persists anesthesia case schedules and documented billables in a local [DuckDB](https://duckdb.org/) file.

## What it does

1. **Ingest schedules** — external systems POST a shift’s scheduled cases; the API stores them with `status: scheduled` and deterministic UUIDs.
2. **Serve the active queue** — the UI loads today’s scheduled cases via `GET /cases/schedules`.
3. **Accept documentation** — after end-of-shift triage, the UI POSTs terminal cases (`billable`, `mission`, `cancelled`, `skipped`) via `POST /cases/billables`.
4. **Expose billing history** — the Billing page reads submitted cases via `GET /cases/billables`.

Case IDs are derived from facility, provider, service date/time, patient, and diagnosis when not supplied. Re-posting the same schedule payload upserts (`ON CONFLICT DO UPDATE` with `COALESCE` so null fields leave existing values).

---

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness check (no auth) |
| `POST` | `/cases/schedules` | Ingest scheduled cases for a shift |
| `GET` | `/cases/schedules` | List scheduled cases (default facility/provider) |
| `POST` | `/cases/billables` | Update cases to terminal statuses |
| `GET` | `/cases/billables` | List submitted billable/mission/cancelled/skipped cases |

Interactive docs: `GET /docs` (Swagger UI) when the server is running.

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /cases/schedules`

Ingest cases for a service date. Each case is stored as `scheduled`.

**Request body:**

```json
{
  "service_date": "2026-01-20",
  "facility_id": "273f4ea2-ec1c-593c-9e13-1894c9bd1369",
  "provider_id": "9e69728e-4848-5917-8fb0-600ec0451f6b",
  "cases": [
    {
      "case_pos": 1,
      "patient_id": "10001",
      "patient_name": "TEST, PATIENT",
      "patient_dob": "1960-05-05",
      "dx": "H25.812",
      "cpt": "00142",
      "eye": "LEFT",
      "minutes": 15
    }
  ]
}
```

`facility_id` and `provider_id` default to deterministic UUIDs when omitted. `minutes` on ingest is a suggested default only.

**Response:**

```json
{
  "scheduled": ["a334ad13-d199-5585-bbe4-0accd3da64b9"]
}
```

Returns only newly inserted case IDs; duplicates return an empty `scheduled` array.

### `GET /cases/schedules`

Returns all cases with `status: scheduled` for the default facility and provider.

**Response:** `CaseInfo[]`

```json
[
  {
    "case_id": "a334ad13-d199-5585-bbe4-0accd3da64b9",
    "service_date": "2026-01-20",
    "case_pos": 1,
    "patient_id": "10001",
    "patient_name": "TEST, PATIENT",
    "patient_dob": "1960-05-05",
    "dx": "H25.812",
    "cpt": "00142",
    "eye": "LEFT",
    "minutes": 15,
    "status": "scheduled"
  }
]
```

### `POST /cases/billables`

Update documented cases. Body is a `CaseInfo[]` with terminal `status` values.

**Request body:**

```json
[
  {
    "case_id": "a334ad13-d199-5585-bbe4-0accd3da64b9",
    "service_date": "2026-01-20",
    "case_pos": 1,
    "patient_id": "10001",
    "patient_name": "TEST, PATIENT",
    "patient_dob": "1960-05-05",
    "dx": "H25.812",
    "cpt": "00142",
    "eye": "LEFT",
    "minutes": 22,
    "status": "billable",
    "note": ""
  }
]
```

Skipped cases may include `sub_status` (`identity_issue`, `needs_review`) and `note`.

**Response:**

```json
{
  "billable": ["a334ad13-d199-5585-bbe4-0accd3da64b9"],
  "mission": [],
  "cancelled": [],
  "issues": []
}
```

### `GET /cases/billables`

Returns submitted cases (`billable`, `mission`, `cancelled`, `skipped`) grouped with the latest service date.

**Response:**

```json
{
  "facility_id": "273f4ea2-ec1c-593c-9e13-1894c9bd1369",
  "provider_id": "9e69728e-4848-5917-8fb0-600ec0451f6b",
  "service_date": "2026-01-20",
  "cases": []
}
```

### Case status values

| Status | Meaning |
|--------|---------|
| `scheduled` | Awaiting documentation |
| `billable` | Documented, billable minutes |
| `mission` | Documented mission case |
| `cancelled` | Cancelled (`minutes: 0`) |
| `skipped` | Flagged for office review |

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CASES_DB_PATH` | `:memory:` (local) / `/data/cases.duckdb` (Docker) | DuckDB file path |
| `CASES_DB_API_KEY` | — | Preferred API key; enables `X-API-KEY` gate when set |
| `API_KEY` | — | Legacy alias for `CASES_DB_API_KEY` |

When an API key env var is set, all routes except `/health` require header `X-API-KEY: <key>`. `CASES_DB_API_KEY` takes precedence over `API_KEY`.

---

## Local development

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export CASES_DB_PATH=./data/cases.duckdb   # optional; omit for in-memory DB
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Point the UI at this server via `ui/.env`:

```
BACKEND_BASE_URL=http://localhost:8000
BACKEND_API_KEY=          # optional; must match API CASES_DB_API_KEY if set
```

---

## Tests

```bash
cd api
pytest
```

Fixtures live in `tests/*.json`. Tests use a temporary DuckDB file per run.

---

## Docker deployment

Build from the `api/` directory:

```bash
cd api
docker build -t medicafe-api .
```

Run with a persistent data volume:

```bash
docker run -d \
  --name medicafe-api \
  -p 8000:8000 \
  -v medicafe-cases:/data \
  -e CASES_DB_API_KEY=your-secret \
  medicafe-api
```

The image listens on `0.0.0.0:8000` and stores the database at `/data/cases.duckdb`.

### Pairing with the UI

UI API settings are **runtime only** (never Docker build args). See `ui/Dockerfile` / `ui/README.md`:

```bash
docker run --rm -p 3000:8080 \
  -e BACKEND_BASE_URL=https://api.example.com \
  -e BACKEND_API_KEY=your-secret \
  medicafe-ui
```

### Health checks

```bash
curl http://localhost:8000/health
```

With API key enabled:

```bash
curl -H "X-API-KEY: your-secret" http://localhost:8000/cases/schedules
```
