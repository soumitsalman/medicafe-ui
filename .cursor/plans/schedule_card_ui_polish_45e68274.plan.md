---
name: Schedule Card UI Polish
overview: Add date-fns for DOB+age display, move status to icon+colored name on row 1, add conditional editable note row for issue cases, fix action button colors, and update AGENTS.md to document the new card UX.
todos:
  - id: date-fns
    content: Install date-fns; refactor duration.js with formatDob + formatDobWithAge using differenceInYears
    status: completed
  - id: status-util
    content: Add warning color to app.config.ts; add statusDisplayFromCase to caseSelectors.js
    status: completed
  - id: schedule-card-ui
    content: Update CaseScheduleCard.vue — status icon+color on name, DOB with age, note row, issue button warning, remove row 2 labels
    status: completed
  - id: agents-md
    content: Update AGENTS.md — card layout, theming, date-fns guideline
    status: completed
isProject: false
---

# Schedule Card UI Polish

## Scope

Incremental UX updates on top of the completed business-logic overhaul. No store/API changes required — `patchCase({ note })` already exists in [`app/mock/store.js`](app/mock/store.js).

---

## 1. Add `date-fns`

Install dependency:

```bash
pnpm add date-fns
```

Update [`package.json`](package.json) / lockfile.

---

## 2. DOB + age utility — [`app/utils/duration.js`](app/utils/duration.js)

Replace hand-rolled `formatDob` with date-fns. Add `formatDobWithAge(dob, shiftDate)`:

```js
import { differenceInYears, format, parse } from 'date-fns'

export function formatDob(dob) {
  return format(parse(dob, 'yyyy-MM-dd', new Date()), 'MM/dd/yyyy')
}

/** @param {string} dob YYYY-MM-DD @param {string} shiftDate MM-DD-YYYY */
export function formatDobWithAge(dob, shiftDate) {
  const birth = parse(dob, 'yyyy-MM-dd', new Date())
  const ref = parse(shiftDate, 'MM-dd-yyyy', new Date())
  const age = differenceInYears(ref, birth)
  return `${format(birth, 'MM/dd/yyyy')} (${age}y)`
}
```

- Use **`differenceInYears`** (full years, accounts for birthday) — not `differenceInCalendarYears`
- Reference date = `caseItem.date` (shift date from receiving contract), not `Date.now()`

**Example:** `dob: "1950-01-01"`, `date: "01-20-2026"` → `01/01/1950 (76y)`

---

## 3. Status display helper — new util or inline computed

Add `statusDisplayFromCase(status)` in [`app/utils/caseSelectors.js`](app/utils/caseSelectors.js) (keeps derivation out of template):

| Status | Name color | Icon | Card border |
|---|---|---|---|
| `pending` | `text-highlighted` | none | none |
| `entered` | `text-primary` | `i-lucide-check-circle-2` | `border-primary` |
| `mission` | `text-secondary` | `i-lucide-heart` | `border-secondary` |
| `cancelled` | `text-error` | `i-lucide-x-circle` | `border-error` |
| `identity_issue` / `needs_review` | `text-warning` | `i-lucide-circle-alert` | `border-warning` |

Returns `{ icon, textClass, borderClass }`.

---

## 4. Warning color — [`app/app.config.ts`](app/app.config.ts)

Add warning alias so `text-warning` / `border-warning` / `color="warning"` resolve:

```ts
colors: {
  primary: 'teal',
  secondary: 'sky',
  neutral: 'zinc',
  warning: 'amber'
}
```

---

## 5. Redesign [`app/components/case/CaseScheduleCard.vue`](app/components/case/CaseScheduleCard.vue)

### Row 1 — status on name

**Before:** plain name + `formatDob(dob)`

**After:**
```
[patient_id badge] [icon?] NAME (colored)   MM/DD/YYYY (Ny)   [minutes]
```

- Import `formatDobWithAge` instead of `formatDob`
- Use `statusDisplay` computed from `caseItem.status`
- Render `UIcon` before name when `statusDisplay.icon` is set
- Apply `statusDisplay.textClass` to name
- DOB caption: `formatDobWithAge(caseItem.dob, caseItem.date)` — keep `text-muted`

### Row 2 — dx / cpt / eye only

- **Remove** all right-aligned status text labels (`Pending`, `Entered`, etc.) — status now lives on row 1

### Row 2b — conditional note (new)

Visible when: `isIssue && caseItem.note.trim().length > 0`

```vue
<div v-if="showNoteRow" class="mt-3 flex w-full items-start gap-2">
  <UTextarea v-model="noteInput" ... @update:model-value="onNoteChange" />
  <UButton icon="i-lucide-x" color="neutral" variant="ghost" @click="onClearNote" />
</div>
```

- Sync `noteInput` from `caseItem.note` via `watch`
- Debounced `patchCase({ note })` on edit
- **X** clears note → `patchCase({ note: '' })` → row hides

### Row 3 — action button colors

| Button | Color | Change |
|---|---|---|
| Cancel | `error` | no change |
| Undo | `neutral` | no change |
| Issue | **`warning`** | change from `neutral` |

### Card border

Replace per-status `:class` booleans with dynamic `statusDisplay.borderClass`.

---

## 6. Card layout (final)

```
┌────────────────────────────────────────────────────────────┐
│ [id] [✓] NAME (primary)     01/01/1950 (76y)  │  [minutes] │  row 1
│ [dx ▼]  [cpt]  [eye]                                       │  row 2
│ [editable note textarea]                            [X]    │  row 2b (conditional)
├────────────────────────────────────────────────────────────┤
│ ☐ Mission                    Cancel  Undo  Issue           │  row 3
└────────────────────────────────────────────────────────────┘
```

---

## 7. Update [`AGENTS.md`](AGENTS.md)

### Schedule Card Layout section
- Row 1: status icon + colored name; DOB `MM/DD/YYYY (Ny)` via date-fns + shift date
- Row 2: dx/cpt/eye only (no status label)
- Row 2b: editable note when issue status + non-empty note
- Action button colors: Cancel=`error`, Issue=`warning`, Undo=`neutral`

### Theming section
- `entered` → `primary` + check icon before name
- `pending` → default text, no icon
- `cancelled` → `error` + x icon
- `identity_issue` / `needs_review` → `warning` + alert icon
- `mission` → `secondary` + heart icon

### Coding Guideline
- Add note: use **date-fns** (`differenceInYears`, `format`, `parse`) for DOB formatting and age — do not hand-roll age math

---

## 8. Files touched

| File | Change |
|---|---|
| [`package.json`](package.json) | add `date-fns` |
| [`app/utils/duration.js`](app/utils/duration.js) | date-fns `formatDob` + `formatDobWithAge` |
| [`app/utils/caseSelectors.js`](app/utils/caseSelectors.js) | add `statusDisplayFromCase` |
| [`app/app.config.ts`](app/app.config.ts) | add `warning: 'amber'` |
| [`app/components/case/CaseScheduleCard.vue`](app/components/case/CaseScheduleCard.vue) | full card UX update |
| [`AGENTS.md`](AGENTS.md) | card layout + theming + date-fns note |

No changes to store, schedule page, or modals.

---

## 9. Verification

1. Pending case: no icon, default name color, DOB shows age
2. Entered case: primary check icon + colored name
3. Cancelled: error x icon
4. Issue with note from modal: warning alert icon + note row appears; X clears note
5. Issue button is warning-colored
6. `npx nuxt build` passes
