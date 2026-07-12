# Medicafe API

FastAPI + DuckDB backend for Modern Workflow. Persists anesthesia schedules and documented billables.

**Flow:** ingest schedule → UI documents locally → submit terminals → billing history.

| Step | Route | Role |
|------|-------|------|
| Ingest new | `POST /cases/schedules` | Insert-only; force `scheduled` |
| Correct/backfill | `PATCH /cases/schedules` | Update then insert missing |
| Active queue | `GET /cases/schedules` | `status=scheduled` |
| Provider inputs | `POST /cases/billables` | Update by `case_id` (terminals only) |
| Billable history | `GET /cases/billables` | `billable\|mission\|cancelled\|skipped` |

Auth: if `API_KEY` set, all routes except `/health` require `X-API-KEY`. Docs: `GET /docs`.

---

## Status & minutes

| Status | Meaning |
|--------|---------|
| `scheduled` | Awaiting triage |
| `billable` | Documented, bill (`minutes > 0`) |
| `mission` | Documented, track only (`minutes > 0`) |
| `cancelled` | Cancelled (`minutes == 0`) |
| `skipped` | Issue-locked; see `sub_status` / `note` |

`sub_status` (when `skipped`): `identity_issue` | `needs_review`.

**Dates:** schedule body `dos` = `MM-DD-YYYY`. Query params + `CaseInfo.service_date` = ISO `YYYY-MM-DD`.

**IDs:** `case_id` = `uuid5(NAMESPACE_OID, "{YYYYMMDD}-{patient_id}")` when omitted. Schedule routes key by `(patient_id, dos)`; billables by `case_id`.

---

## Routes

### `GET /health`
No auth. `{"status":"ok"}`.

### `POST /cases/schedules` — insert new scheduled cases
**When:** first-time shift ingest. **Not** for updates → use PATCH.

**Identity:** `(patient_id, dos MM-DD-YYYY)`. Patients by `patient_id`.

**Behavior:** forces `status=scheduled`; insert cases+patients; existing keys skipped (`ON CONFLICT DO NOTHING`).

**Body:** `CaseSchedules` — `{ "rows": [{ "key": { "patient_id", "dos" }, "patch": { ... } }, ...] }` (`rows` min 1).

**Patch fields:** `patient_name`, `diagnosis`, `cpt`, `eye`, `minutes`, `docx_position`→`case_position`, `status` (ignored/overwritten), `note`.

**Returns:** `{ "inserted": [<case_id>, ...] }`.

Sample request: [SERVICE_LINE_INPUT_REMOTE_V0_PROPOSAL.md](api/SERVICE_LINE_INPUT_REMOTE_V0_PROPOSAL.md)

### `PATCH /cases/schedules` — update or backfill
**When:** enrich/correct existing; backfill skipped rows. Prefer POST for brand-new loads.

**Behavior:** `update_cases` then `insert_cases` (order matters). Patient update only if `patient_name` set; then `insert_patients`. Status accepted: `scheduled|skipped|mission|billable` (else nullified).

**Body:** same `CaseSchedules` as POST.

**Returns:** `{ "updated": [...], "inserted": [...] }`.

Sample request: [SERVICE_LINE_INPUT_REMOTE_V0_PROPOSAL.md](api/SERVICE_LINE_INPUT_REMOTE_V0_PROPOSAL.md)

### `GET /cases/schedules` — list active queue
**Filter:** `?service_date=YYYY-MM-DD` optional. Status fixed to `scheduled`. Sorted by `case_position`.

**Returns:** `CaseView[]` (case + `patient_name`, `patient_dob`).

### `POST /cases/billables` — submit to billing office
**When:** UI Send to Office (all cases terminal).

**Identity:** each item needs `case_id`. Dropped if missing `case_id` or status ∉ `billable|mission|cancelled|skipped`.

**Behavior:** update only; no inserts; unknown IDs ignored.

**Body:** `CaseInfo[]` (include minutes, diagnosis, status, optional `sub_status`/`note` for skipped).

**Returns:** `{ "updated": [<case_id>, ...] }`.

### `GET /cases/billables` — billing history
**Filter:** `?service_date=YYYY-MM-DD` optional. Status ∈ `billable|mission|cancelled|skipped`.

**Returns:** `CaseView[]`.

---

## Request models (`routers/models.py`)

```
CaseSchedules { rows: CaseRow[1..] }
CaseRow { key: CaseKey, patch: CasePatch }
CaseKey { patient_id: str, dos: "MM-DD-YYYY" }
CasePatch {
  patient_name?, diagnosis?, cpt?, eye?,
  minutes?, docx_position?, status?, note?
}
```

`CaseUpdateResult` = `dict[str, list[UUID]]` — keys `inserted` and/or `updated`.

---

## DB (`db/`)

DuckDB file: `{CASES_DB_PATH}/{DEFAULT_FACILITY_ID.hex}.duckdb` (see `main.py` lifespan).

### Tables

**`cases`** PK `case_id`
| Column | Type | Notes |
|--------|------|-------|
| case_id | UUID PK | Deterministic from date+patient if unset |
| service_date | DATE NOT NULL | |
| patient_id | VARCHAR NOT NULL | → patients |
| case_position | INTEGER | UI sort only |
| diagnosis | VARCHAR NOT NULL | |
| cpt, eye | VARCHAR | |
| minutes | INTEGER | null / 0 / >0 semantics above |
| status | VARCHAR NOT NULL | CaseStatus |
| sub_status | VARCHAR[] | IssueType[] |
| note | VARCHAR | |
| ts | TIMESTAMP | stamped on write |
| provider_id | UUID | optional / future |
| service_time | TIME | optional / future |

**`patients`** PK `patient_id`
| Column | Type |
|--------|------|
| patient_id | VARCHAR PK |
| patient_name | VARCHAR |
| patient_dob | DATE |
| ts | TIMESTAMP |

### Pydantic (`db/schemas.py`)

- `CaseInfo` — case row fields (no patient name/dob)
- `PatientInfo` — patient row
- `CaseView` — `CaseInfo` + `patient_name` + `patient_dob` (joined read model; `ts` excluded)

### Operations (`CasesDB`)

| Method | Semantics |
|--------|-----------|
| `insert_cases` | Ensure `case_id`, stamp `ts`. `INSERT … ON CONFLICT (case_id) DO NOTHING RETURNING case_id` |
| `update_cases` | Ensure `case_id`, stamp `ts`. `UPDATE … SET col=COALESCE(v.col, cases.col)` — **nulls do not overwrite** |
| `insert_patients` | Same insert-ignore pattern on `patient_id` |
| `update_patients` | Same COALESCE update on `patient_id` |
| `query_cases` | Optional filters: `patient_id`, `service_date`, `status[]`, `provider_id`. `LEFT JOIN patients`; returns `CaseView[]` |

`create_case_id(case)` (`db/ids.py`): requires `service_date` + `patient_id`; else `ValueError`.

---

## Env

| Var | Default | Notes |
|-----|---------|-------|
| `CASES_DB_PATH` | `.` | Dir for DuckDB file |
| `API_KEY` | unset | Enables `X-API-KEY` gate |

---

## Local / test / Docker

```bash
cd api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export CASES_DB_PATH=./data
fastapi run          # :8000
pytest               # use api/.venv/bin/pytest
```

UI: `NUXT_PUBLIC_API_BASE=http://localhost:8000`, optional `NUXT_PUBLIC_API_KEY` matching `API_KEY`.

```bash
docker build -t medicafe-api .
docker run -d -p 8000:8000 -v medicafe-cases:/data -e API_KEY=secret medicafe-api
```
