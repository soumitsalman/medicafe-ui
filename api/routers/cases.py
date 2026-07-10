import asyncio
from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query

from .models import *
from db import CaseInfo, CasesDB, PatientInfo, CaseView

router = APIRouter(prefix="/cases", tags=["cases"])





def _null_str(value: Optional[str]) -> Optional[str]:
    """Map null / empty string fields from router models to schema null."""
    if value: return value

def _parse_status(value: Optional[str]) -> Optional[CaseStatus]:
    value = _null_str(value)
    if value == "skipped": return value

_MDY = "%m-%d-%Y"
def _parse_mdy(value: Optional[str]) -> Optional[date]:
    value = _null_str(value)
    if value: return datetime.strptime(value, _MDY).date()

def _require_case_keys(
    *,
    case_id: Optional[UUID] = None,
    patient_id: Optional[str] = None,
    service_date: Optional[date] = None,
) -> None:
    if case_id is not None:
        return
    if not patient_id:
        raise HTTPException(status_code=422, detail="patient_id cannot be null")
    if service_date is None:
        raise HTTPException(status_code=422, detail="service_date cannot be null")

def _stamp_scheduled(cases: list[CaseInfo]) -> list[CaseInfo]:
    for case in cases:
        case.status = "scheduled"
    return cases

def _split_case_schedules(payload: CaseSchedules) -> tuple[list[CaseInfo], list[PatientInfo]]:
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
    return request.app.state.db

CaseDBDependency = Annotated[CasesDB, Depends(get_cases_db)]

@router.post("/schedules")
async def post_schedules(cases_db: CaseDBDependency, payload: CaseSchedules) -> CaseUpdateResult:
    cases, patients = _split_case_schedules(payload)
    cases = _stamp_scheduled(cases)
    _, case_ids = await asyncio.gather(
        asyncio.to_thread(cases_db.insert_patients, patients),
        asyncio.to_thread(cases_db.insert_cases, cases),
    )
    return CaseUpdateResult(inserted=case_ids)


@router.patch("/schedules")
async def patch_schedules(cases_db: CaseDBDependency, payload: CaseSchedules) -> CaseUpdateResult:
    """Splits the payload into cases and patients. Updates existing first, then inserts new (sequence is very important)."""
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


@router.get("/schedules")
async def get_schedules(cases_db: CaseDBDependency, service_date: date = Query(default=None)) -> list[CaseView]:
    items = await asyncio.to_thread(
        cases_db.query_cases,
        service_date=service_date,
        status=["scheduled"],
    )
    items.sort(key=lambda x: x.case_position or 0)
    return items


@router.post("/billables")
async def post_billables(payload: list[CaseInfo], cases_db: CaseDBDependency) -> CaseUpdateResult:
    for case in payload:
        _require_case_keys(case_id=case.case_id, patient_id=case.patient_id, service_date=case.service_date)
    return CaseUpdateResult(updated=await asyncio.to_thread(cases_db.update_cases, payload))


@router.get("/billables")
async def get_billables(cases_db: CaseDBDependency, service_date: date = Query(default=None)) -> list[CaseView]:
    return await asyncio.to_thread(
        cases_db.query_cases,
        service_date=service_date,
        status=["billable", "mission", "cancelled", "skipped"],
    )
