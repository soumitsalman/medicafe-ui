# Service Line Input remote v0 proposal

## Decision

Remote v0 is a small boundary adapter over the existing Service Line Input
(SLI) model. It is not a remote copy of the DOCX index, local sidecar, DAT,
837P, or billing state.

Use one idempotent upsert operation for both the initial upload and later local
updates, plus a cursor-based GET for provider-authored changes:

| Operation | Endpoint | Purpose |
| --- | --- | --- |
| Initial and later local state | `POST /v0/sli/rows:upsert` | Idempotently create or sparsely update rows. |
| Provider changes | `GET /v0/sli/changes?cursor=<opaque>` | Return provider patches after the supplied cursor. Omit `cursor` for the first poll. |

No acknowledgement endpoint is needed in v0. The XP client advances its
locally persisted cursor only after every returned change has been durably
written to the local SLI sidecar. Repeating a GET with the old cursor must
return the same changes.

## Minimum upload envelope

```json
{
  "schema": "sli.remote_upsert.v0",
  "batch_id": "xp-a-initial-0001",
  "rows": [
    {
      "key": {
        "patient_id": "90001",
        "dos": "08-03-2026",
        "service_line_kind": "anesthesia",
        "line_ordinal": 1
      },
      "local_revision": 1,
      "patch": {
        "patient_name": "Avery Sample",
        "diagnosis": "H25.11",
        "eye": "R",
        "femto": "",
        "docx_position": 1,
        "status": "needs_review"
      }
    }
  ]
}
```

Required envelope fields:

- `schema`: exact contract discriminator.
- `batch_id`: client-generated idempotency key for the whole POST.
- `rows`: one or more independently addressable row upserts.

Required row fields:

- `key`: the existing durable SLI identity. `docx_position` is context, never
  identity.
- `local_revision`: monotonically increasing integer for this row. Replaying
  the same revision and content is idempotent. Reusing a revision with
  different content is a conflict. A lower revision is stale.
- `patch`: fields present are updated; fields absent express no opinion.

Allowed patch fields in v0:

| Field | Type | Notes |
| --- | --- | --- |
| `patient_name` | string | Remote display only; not row identity. |
| `diagnosis` | string or null | Existing SLI normalization applies after download. |
| `cpt` | string or null | A local suggestion is context, not provider confirmation. |
| `minutes` | integer or null | Keep numeric on the wire; existing SLI domain validation applies. |
| `eye` | string or null | Schedule context. |
| `femto` | string or null | Preserve the source's small textual category in v0. |
| `docx_position` | integer or null | Matching/display aid only. |
| `status` | string or null | SLI review disposition; see the code-backed definitions below. |
| `note` | string or null | Short provider/local coordination note; recommended maximum 2,000 characters. |

### SLI status definitions

These values describe the disposition of an SLI **review row**. They do not
describe billing custody, charge entry, DAT mutation, 837P generation, or claim
completion.

| Wire status | Meaning in the existing SLI flow | Code-backed scenario |
| --- | --- | --- |
| `needs_review` | The row still requires a person to decide or supply SLI values. It is nonterminal. `normalize_service_line_review_status()` preserves `needs_review`, while `normalize_service_line_row_status()` maps it to the default row state `pending`. It therefore increments the completion summary's `pending` count and keeps `service_line_input_review_complete=false`. | Use for a newly uploaded schedule row awaiting minutes, diagnosis/CPT review, or a decision to skip/cancel. This matches the UI's initial `PENDING` rows: they remain promptable, and a DOS is not accepted while pending rows remain. |
| `review_complete` | A person has completed the SLI review for the row. The model normalizes it to review status `review_complete` and row status `entered`; it sets `service_line_review_complete=true`. This is terminal for the SLI review lane only. | Use after the provider has supplied/confirmed the applicable values, such as minutes and any diagnosis/CPT correction. Existing tests pass `COMPLETED` with minutes and assert `review_complete`, while also asserting `claims_completion=false` and `mutates_billing_state=false`. |
| `skipped` | A deliberate decision not to enter SLI values for this row in this review pass. The UI's `s` action clears minutes, sets `SKIPPED`, advances to the next row, and displays `SKIPPED`. It is counted separately from entered rows but is terminal for review-completion accounting. | Use when the reviewer intentionally declines or determines the row should not receive SLI input. Do not use it merely because data has not arrived yet; that remains `needs_review`. A skipped row can help a DOS review reach completion because only pending or invalid rows block completion. |
| `cancelled` | The row is not to proceed through SLI entry because its input context makes entry inapplicable or unsafe. It is counted separately from skipped rows and is terminal for review-completion accounting. | The current concrete automatic scenario is a DOCX-matched row whose diagnosis is `Unknown`: MediBot marks it `CANCELLED` with `status_reason=docx_diagnosis_unknown`, does not prompt for it, and persists the more specific internal review status `auto_cancelled`. A provider-authored cancellation should therefore include a short `note` explaining the reason until v0 adds a dedicated reason code. |

The existing model also knows `pending`, `invalid`, and internal
`auto_cancelled`. Remote v0 intentionally exposes `needs_review` instead of
`pending` as the clearer provider-facing request state; the adapter maps it to
the local pending row state. `invalid` is an adapter/validation outcome, not a
normal provider choice. `auto_cancelled` remains local derived state; the wire
uses `cancelled` and the local adapter may derive `auto_cancelled` when the
known `docx_diagnosis_unknown` condition applies.

An explicit `null` clears a nullable field. An omitted field does not modify
it. Empty source strings may remain empty strings when that distinction is
meaningful (for example, the observed `femto` shape).

The authenticated machine determines tenant/site scope, so v0 does not repeat
`origin`, `system`, or `site_id` in every payload. The endpoint direction and
revision identify local versus provider provenance, so v0 also omits actor
objects, timestamps, requested-field lists, and per-field provenance maps.

## Minimum GET response

```json
{
  "schema": "sli.remote_changes.v0",
  "next_cursor": "cursor-demo-0007",
  "changes": [
    {
      "change_id": "change-demo-0006",
      "key": {
        "patient_id": "90001",
        "dos": "08-03-2026",
        "service_line_kind": "anesthesia",
        "line_ordinal": 1
      },
      "base_local_revision": 2,
      "patch": {
        "minutes": 24,
        "cpt": "00142",
        "status": "review_complete",
        "note": "Provider confirmed the final values."
      }
    }
  ]
}
```

- `change_id` is the immutable download deduplication key.
- `base_local_revision` records which uploaded local row the provider edited.
  If the current local revision is newer, the XP adapter must mark a conflict
  for review rather than silently overwrite local state.
- `next_cursor` is opaque. Persist it only after all changes in the response
  have been durably and coherently applied or recorded as conflicts.
- An empty page still returns a stable `next_cursor` and `changes: []`.

The web app must retain changes until requested and must not POST to the XP
machine. A cursor page is at-least-once delivery: retries are expected and safe.

## Boundary requirements

Downloaded patches must pass through the existing SLI identity builders,
normalizers, status mapping, forbidden-mutation filtering, and preview-boundary
sanitization before sidecar persistence. Remote data remains review-only:

- `workflow_name=service_line_input`
- `workflow_boundary=preview_only_review_required`
- no DAT mutation
- no generated 837P mutation
- no `charges_entered` or claim-completion claim

Reject or fail closed on an unknown schema, incomplete key, unsupported patch
field, invalid value, reused `change_id` with different content, stale/conflict
revision, cursor regression, or target mismatch. A partial page must not be
described as hydrated merely because some rows were accepted.

## Deliberately deferred from v0

- actor identity and audit timestamps
- per-field provenance maps
- requested-field negotiation
- a separate initial-request endpoint
- acknowledgement POST
- deletion/tombstone semantics
- remote billing, DAT, 837P, charge-entry, or claim-completion state

These can be added only when a concrete requirement outweighs their metadata
and compatibility cost.

## Sanitized local-data experiment

`tools/build_sanitized_sli_remote_v0_samples.py` was run against a local DOCX
schedule index with PHI. It inspected the real storage shape in memory and
emitted no source identifiers, DOS values, names, or clinical values. The
source index contained 339 DOS schedule entries; the three selected DOS held 38
patient rows. The sample retained the observed nesting/cardinality pattern for
three DOS and six rows while replacing every sensitive value with synthetic
data.

One rebuilt index with 710 file records but zero schedules was also tested and
correctly treated as unusable for an initial payload. The complete sanitized
examples are in `docs/samples/sli_remote_v0_payloads.sanitized.json`.
