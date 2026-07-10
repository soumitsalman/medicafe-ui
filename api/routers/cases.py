import asyncio
from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query

from .models import (
    DEFAULT_FACILITY_ID,
    DEFAULT_PROVIDER_ID,
    ScheduleInsertsPayload,
    CaseUpdatesPayloads,
)
from db import CaseInfo, CasesDB, PatientInfo

router = APIRouter(prefix="/cases", tags=["cases"])

_MDY = "%m-%d-%Y"


def get_cases_db(request: Request) -> CasesDB:
    return request.app.state.db

CaseDBDependency = Annotated[CasesDB, Depends(get_cases_db)]


def _null_str(value: Optional[str]) -> Optional[str]:
    """Map null / empty string fields from router models to schema null."""
    if value is None or value == "":
        return None
    return value


def _parse_mdy(value: Optional[str]) -> Optional[date]:
    value = _null_str(value)
    if value is None:
        return None
    return datetime.strptime(value, _MDY).date()


def _parse_position(value: Optional[str]) -> Optional[int]:
    value = _null_str(value)
    if value is None:
        return None
    text = value.strip()
    if text.isdigit():
        return int(text)
    return None


def _require_case_keys(patient_id: Optional[str], service_date: Optional[date]) -> None:
    if not patient_id:
        raise HTTPException(status_code=422, detail="patient_id cannot be null")
    if service_date is None:
        raise HTTPException(status_code=422, detail="service_date cannot be null")


def _split_case_inserts(
    payload: ScheduleInsertsPayload,
) -> tuple[list[CaseInfo], list[PatientInfo]]:
    cases: list[CaseInfo] = []
    patients: list[PatientInfo] = []
    for date_key, day in payload.schedules.items():
        service_date = _parse_mdy(date_key)
        for raw_patient_id, incoming in day.current.patients.items():
            patient_id = _null_str(raw_patient_id)
            _require_case_keys(patient_id, service_date)
            cases.append(
                CaseInfo(
                    facility_id=DEFAULT_FACILITY_ID,
                    provider_id=DEFAULT_PROVIDER_ID,
                    service_date=service_date,
                    patient_id=patient_id,
                    diagnosis=_null_str(incoming.diagnosis),
                    eye=_null_str(incoming.eye),
                    case_position=_parse_position(incoming.position),
                    status="scheduled",
                )
            )
            patients.append(
                PatientInfo(
                    patient_id=patient_id,
                    patient_name=_null_str(incoming.patient_name),
                    patient_dob=_parse_mdy(incoming.patient_dob),
                    facility_id=DEFAULT_FACILITY_ID,
                )
            )
    return cases, patients


def _split_case_updates(
    payload: CaseUpdatesPayloads,
) -> tuple[list[CaseInfo], list[PatientInfo]]:
    cases: list[CaseInfo] = []
    patients: list[PatientInfo] = []
    for row in payload.rows.values():
        patient_id = _null_str(row.patient_id)
        service_date = _parse_mdy(row.dos)
        _require_case_keys(patient_id, service_date)
        patient_name = _null_str(row.patient_display_name)
        patient_dob = _parse_mdy(row.patient_dob)
        case = CaseInfo(
            facility_id=DEFAULT_FACILITY_ID,
            provider_id=DEFAULT_PROVIDER_ID,
            patient_id=patient_id,
            service_date=service_date,
            diagnosis=_null_str(row.diagnosis),
            cpt=_null_str(row.cpt),
            case_position=row.docx_position,
        )
        case.case_id = CasesDB._create_case_id(case)
        cases.append(case)
        if patient_name or patient_dob:
            patients.append(
                PatientInfo(
                    patient_id=patient_id,
                    patient_name=patient_name,
                    patient_dob=patient_dob,
                    facility_id=DEFAULT_FACILITY_ID,
                )
            )
    return cases, patients


@router.post("/schedules")
async def post_schedules(cases_db: CaseDBDependency, payload: ScheduleInsertsPayload) -> list[UUID]:
    cases, patients = _split_case_inserts(payload)
    # DuckDB connection is not safe for concurrent writers on the same handle.
    await asyncio.to_thread(cases_db.store_patients, patients)
    return await asyncio.to_thread(cases_db.store_cases, cases)


@router.patch("/schedules")
async def patch_schedules(cases_db: CaseDBDependency, payload: CaseUpdatesPayloads) -> list[UUID]:
    cases, patients = _split_case_updates(payload)
    if patients:
        await asyncio.to_thread(cases_db.store_patients, patients)
    return await asyncio.to_thread(cases_db.store_cases, cases)


@router.get("/schedules")
async def get_schedules(cases_db: CaseDBDependency, service_date: date = Query(default=None)) -> list[CaseInfo]:
    items = await asyncio.to_thread(
        cases_db.query_cases,
        status=["scheduled"],
        service_date=service_date
    )
    items.sort(key=lambda x: x.case_position or 0)
    return items


@router.post("/billables")
async def post_billables(payload: list[CaseInfo], cases_db: CaseDBDependency) -> list[UUID]:
    for case in payload:
        _require_case_keys(case.patient_id, case.service_date)
    return await asyncio.to_thread(cases_db.store_cases, payload)


@router.get("/billables")
async def get_billables(cases_db: CaseDBDependency, service_date: date = Query(default=None)) -> list[CaseInfo]:
    return await asyncio.to_thread(
        cases_db.query_cases,
        status=["billable", "mission", "cancelled", "issue"],
        service_date=service_date
    )
