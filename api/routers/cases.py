import asyncio
from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query

from .models import *
from db import CaseInfo, CasesDB, PatientInfo, CaseView

router = APIRouter(prefix="/cases", tags=["cases"])

def _null_str(value: Optional[str]) -> Optional[str]:
    """Normalize optional strings: empty/falsy → None; otherwise return the value."""
    if value: return value

def _parse_status(value: Optional[str]) -> Optional[CaseStatus]:
    """Parse schedule-route status. Accepts only scheduled|skipped|mission|billable; else None."""
    value = _null_str(value)    
    if value in ["scheduled", "skipped", "mission", "billable"]: return value

_MDY = "%m-%d-%Y"
def _parse_mdy(value: Optional[str]) -> Optional[date]:
    """Parse MM-DD-YYYY date-of-service strings from CaseKey.dos into a date object."""
    value = _null_str(value)
    if value: return datetime.strptime(value, _MDY).date()

def _require_case_keys(
    *,
    case_id: Optional[UUID] = None,
    patient_id: Optional[str] = None,
    service_date: Optional[date] = None,
) -> None:
    """Validate identity: either `case_id` OR both `patient_id` and `service_date` must be present (else 422)."""
    if case_id is not None:
        return
    if not patient_id:
        raise HTTPException(status_code=422, detail="patient_id cannot be null")
    if service_date is None:
        raise HTTPException(status_code=422, detail="service_date cannot be null")

def _stamp_scheduled(cases: list[CaseInfo]) -> list[CaseInfo]:
    """Force every case status to `scheduled` (used by POST /schedules only)."""
    for case in cases:
        case.status = "scheduled"
    return cases

def _split_case_schedules(payload: CaseSchedules) -> tuple[list[CaseInfo], list[PatientInfo]]:
    """Convert CaseSchedules rows into parallel CaseInfo and PatientInfo lists for DB writes.

    Validates each row's composite key (patient_id + dos). Maps patch fields onto schema models.
    """
    cases: list[CaseInfo] = []
    patients: list[PatientInfo] = []
    for row in payload.rows:
        patient_id = _null_str(row.key.patient_id)
        service_date = _parse_mdy(row.key.dos)
        _require_case_keys(patient_id=patient_id, service_date=service_date)
        
        cases.append(CaseInfo(
            provider_id=DEFAULT_PROVIDER_ID,
            patient_id=patient_id,
            service_date=service_date,
            diagnosis=_null_str(row.patch.diagnosis),
            cpt=_null_str(row.patch.cpt),
            eye=_null_str(row.patch.eye),
            minutes=row.patch.minutes,
            case_position=row.patch.docx_position,
            status=_parse_status(row.patch.status),
            note=_null_str(row.patch.note),
        ))
               
        patients.append(PatientInfo(
            patient_id=patient_id,
            patient_name=_null_str(row.patch.patient_name),
        ))
    return cases, patients

def get_cases_db(request: Request) -> CasesDB:
    """FastAPI dependency: resolve the CasesDB instance from app state."""
    return request.app.state.db

CaseDBDependency = Annotated[CasesDB, Depends(get_cases_db)]

@router.post(
    "/schedules", 
    summary="Insert new scheduled cases",
    description=(
        "PURPOSE: Ingest brand-new cases for a shift into the schedule queue.\n\n"
        "WHEN TO USE: Upstream schedule feed / first-time load of the day's cases. "
        "Do NOT use this to update existing cases — use PATCH /cases/schedules instead.\n\n"
        "IDENTITY: Each row keyed by (patient_id, dos) where dos is MM-DD-YYYY. "
        "Patients keyed by patient_id.\n\n"
        "BEHAVIOR:\n"
        "- Always forces status=`scheduled` (ignores any status in the payload).\n"
        "- Inserts new cases and patients; silently skips rows that already exist (idempotent).\n"
        "- Does not update existing records.\n\n"
        "RETURNS: `{ \"inserted\": [<case_id UUID>, ...] }` — UUIDs of newly inserted cases only."
    )
)
async def post_schedules(cases_db: CaseDBDependency, payload: CaseSchedules) -> CaseUpdateResult:
    """Insert new scheduled cases and patients; return inserted case_ids. Existing keys are ignored."""
    cases, patients = _split_case_schedules(payload)
    cases = _stamp_scheduled(cases)
    _, case_ids = await asyncio.gather(
        asyncio.to_thread(cases_db.insert_patients, patients),
        asyncio.to_thread(cases_db.insert_cases, cases),
    )
    return CaseUpdateResult(inserted=case_ids)


@router.patch(
    "/schedules", 
    summary="Update or backfill scheduled cases",
    description=(
        "PURPOSE: Update existing scheduled cases/patients, and retroactively insert rows that were previously missing.\n\n"
        "WHEN TO USE: Correcting or enriching cases already in the system. "
        "For brand-new incoming schedules, prefer POST /cases/schedules.\n\n"
        "IDENTITY: Each row keyed by (patient_id, dos) where dos is MM-DD-YYYY. "
        "Patients keyed by patient_id.\n\n"
        "BEHAVIOR:\n"
        "- Updates matching cases first, then inserts any that did not exist (order matters).\n"
        "- Updates patients only when patient_name is present; always attempts patient insert for new IDs.\n"
        "- Status accepted only if in [`scheduled`, `skipped`, `mission`, `billable`]; other values ignored.\n\n"
        "RETURNS: `{ \"updated\": [<UUID>, ...], \"inserted\": [<UUID>, ...] }`."
    )
)
async def patch_schedules(cases_db: CaseDBDependency, payload: CaseSchedules) -> CaseUpdateResult:
    """Update existing cases/patients, then insert any missing ones. Returns updated and inserted case_ids."""
    cases, patients = _split_case_schedules(payload)
    
    result = dict(
        updated=await asyncio.to_thread(cases_db.update_cases, cases),
        inserted=await asyncio.to_thread(cases_db.insert_cases, cases)
    )
    
    # update patients only if there is something to update
    if update_patients := [p for p in patients if p.patient_name]:
        await asyncio.to_thread(cases_db.update_patients, update_patients)
    await asyncio.to_thread(cases_db.insert_patients, patients)

    return result


@router.get(
    "/schedules", 
    summary="List scheduled cases",
    description=(
        "PURPOSE: Fetch the active documentation queue — cases still in status=`scheduled`.\n\n"
        "WHEN TO USE: Provider UI Schedule page load. These are cases awaiting minutes/dx/mission/cancel/issue triage.\n\n"
        "FILTERS:\n"
        "- `service_date` (optional, ISO YYYY-MM-DD): limit to one day. Omit to return all scheduled cases.\n\n"
        "BEHAVIOR: Results sorted ascending by case_position.\n\n"
        "RETURNS: list[CaseView] — case fields plus patient_name and patient_dob."
    )
)
async def get_schedules(
    cases_db: CaseDBDependency,
    service_date: date = Query(
        default=None,
        description="Optional service date filter (ISO YYYY-MM-DD). Omit to return all scheduled cases.",
    ),
) -> list[CaseView]:
    """Return cases with status=`scheduled`, optionally filtered by service_date, sorted by case_position."""
    items = await asyncio.to_thread(
        cases_db.query_cases,
        service_date=service_date,
        status=["scheduled"],
    )
    items.sort(key=lambda x: x.case_position or 0)
    return items


@router.post(
    "/billables", 
    summary="Submit cases to billing office",
    description=(
        "PURPOSE: Persist provider-documented terminal outcomes so the billing office can process them.\n\n"
        "WHEN TO USE: After the provider UI 'Send to Office' — every case in the local queue is terminal.\n\n"
        "IDENTITY: Each item MUST include `case_id` (UUID from GET /schedules). "
        "Rows without case_id are dropped.\n\n"
        "ACCEPTED STATUS (only these are written): `billable` | `mission` | `cancelled` | `skipped`.\n"
        "- `billable`: minutes > 0, billable work\n"
        "- `mission`: minutes > 0, tracked but not billed\n"
        "- `cancelled`: minutes == 0\n"
        "- `skipped`: issue-locked; inspect sub_status / note\n\n"
        "BEHAVIOR: Silently ignores unknown case_ids and rows with non-accepted status. "
        "Does not insert new cases.\n\n"
        "RETURNS: `{ \"updated\": [<case_id UUID>, ...] }`."
    )
)
async def post_billables(cases_db: CaseDBDependency, payload: list[CaseInfo]) -> CaseUpdateResult:
    """Update cases keyed by case_id when status is billable|mission|cancelled|skipped. Return updated IDs."""
    payload = list(filter(lambda x: x.case_id and x.status in ["mission", "billable", "cancelled", "skipped"], payload))
    return CaseUpdateResult(updated=await asyncio.to_thread(cases_db.update_cases, payload))


@router.get(
    "/billables", 
    summary="List billing-office cases",
    description=(
        "PURPOSE: Fetch cases already submitted for billing-office processing/review.\n\n"
        "WHEN TO USE: Provider UI Billing history page.\n\n"
        "FILTERS:\n"
        "- `service_date` (optional, ISO YYYY-MM-DD): limit to one day. Omit to return all matching cases.\n\n"
        "INCLUDED STATUS: `billable` | `mission` | `cancelled` | `skipped` "
        "(excludes `scheduled`).\n\n"
        "RETURNS: list[CaseView] — case fields plus patient_name and patient_dob."
    )
)
async def get_billables(
    cases_db: CaseDBDependency,
    service_date: date = Query(
        default=None,
        description="Optional service date filter (ISO YYYY-MM-DD). Omit to return all billable-office cases.",
    ),
) -> list[CaseView]:
    """Return cases with status in billable|mission|cancelled|skipped, optionally filtered by service_date."""
    return await asyncio.to_thread(
        cases_db.query_cases,
        service_date=service_date,
        status=["billable", "mission", "cancelled", "skipped"],
    )
