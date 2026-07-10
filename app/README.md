# Medicafe UI

Nuxt 4 + Nuxt UI front end for end-of-shift case documentation (Schedule → Send to Office) and billing history.

## Directory structure

```
app/
├── app/                    # Nuxt app source
│   ├── app.config.ts       # Nuxt UI color aliases (Soft Medical palette)
│   ├── app.vue             # Root shell
│   ├── assets/             # CSS + brand image
│   ├── components/
│   │   ├── billing/        # Billing day summary cards
│   │   ├── case/           # Schedule card, issue modal, send summary, billing case row
│   │   ├── layout/         # Top bar/nav, page container, brand footer
│   │   └── schedule/       # Schedule queue view
│   ├── composables/        # useCaseApi, useBillingApi, useCaseQueue
│   ├── layouts/            # default layout
│   ├── pages/              # schedule, billing, settings, index
│   ├── settings/           # UI constants
│   ├── types/              # CaseInfo / billing JSDoc types
│   └── utils/              # apiFetch, caseSelectors, billingSelectors, dxLookup, duration
├── public/                 # Static assets (favicon)
├── nuxt.config.ts          # Modules, runtimeConfig, redirects
├── package.json            # Scripts + deps (pnpm)
├── Dockerfile              # Multi-stage production image (port 8080)
├── .env                    # Local NUXT_PUBLIC_API_BASE / NUXT_PUBLIC_API_KEY (gitignored)
└── eslint.config.mjs / tsconfig.json / pnpm-*.yaml
```

Repo root `docker-compose.yml` builds this package as service `app` (`./app`) alongside `./api`.

## API contract

Env (`app/.env` or container env → Nuxt `runtimeConfig.public` via `NUXT_PUBLIC_*`):

| Env var | Runtime key | Role |
|---|---|---|
| `NUXT_PUBLIC_API_BASE` | `apiBase` | API origin (required at deploy; empty if unset → UI shows nothing) |
| `NUXT_PUBLIC_API_KEY` | `apiKey` | Optional; sent as `X-API-KEY` when set |

These are **runtime / deploy-time only** — never Docker build `ARG`/`ENV`. Do not assign them in Nitro plugins (server `runtimeConfig` is read-only).

### Required paths

| Method | Path | Used by |
|---|---|---|
| `GET` | `/cases/schedules` | Schedule queue load |
| `POST` | `/cases/billables` | Send to Office |
| `GET` | `/cases/billables` | Billing history |

### Expected data

**`GET /cases/schedules` → `CaseInfo[]`**

Each case includes at least:

- `case_id`, `service_date` (`YYYY-MM-DD`), `case_pos`
- `patient_id`, `patient_name`, `patient_dob`
- `diagnosis`, `cpt`, `eye`, `minutes`, `status`
- optional: `facility_id`, `provider_id`, `service_time`, `sub_status`, `note`

UI adds local-only `mission: false` on load. Card edits stay in memory until Send to Office.

**`POST /cases/billables` body → `CaseInfo[]`**

Serialized queue (omits UI-only `mission`). Empty `note` / `sub_status` sent as `null`.

**`POST /cases/billables` response**

```json
{ "updated": ["case-uuid-1", "case-uuid-2"] }
```

Summary modal counts come from local cases whose `case_id` appears in `updated`.

**`GET /cases/billables` → billable case list**

Aggregated client-side into day summaries (`billingSelectors.js`).

Statuses used by the UI: `scheduled` | `billable` | `mission` | `cancelled` | `skipped`. Issue types in `sub_status`: `identity_issue` | `needs_review`.

## Self-host

### Local dev

```bash
cd app
# create .env with:
#   NUXT_PUBLIC_API_BASE=http://localhost:8000
#   NUXT_PUBLIC_API_KEY=          # optional
pnpm install
pnpm dev               # http://localhost:3000
```

Point `NUXT_PUBLIC_API_BASE` at a running API (e.g. `http://localhost:8000`).

### Production build (Node)

```bash
cd app
pnpm install
pnpm build
NUXT_PUBLIC_API_BASE=http://localhost:8000 NUXT_PUBLIC_API_KEY= \
  HOST=0.0.0.0 PORT=8080 node .output/server/index.mjs
```

### Docker Compose (repo root)

```bash
# from repo root — set NUXT_PUBLIC_API_BASE / NUXT_PUBLIC_API_KEY in shell or .env
docker compose up --build
```

- UI: `http://localhost:3000` (host) → container port `8080`
- API: `http://localhost:8000`

`NUXT_PUBLIC_API_BASE` should be the URL the **browser** uses to reach the API (typically `http://localhost:8000`).

### Docker image only

```bash
cd app
docker build -t medicafe-ui .
docker run --rm -p 3000:8080 \
  -e NUXT_PUBLIC_API_BASE=http://localhost:8000 \
  -e NUXT_PUBLIC_API_KEY= \
  medicafe-ui
```
