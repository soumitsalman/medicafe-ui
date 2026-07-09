import asyncio
from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, Request

from .models import DEFAULT_FACILITY_ID, DEFAULT_PROVIDER_ID, BillableCasesQueryResponse, ScheduledCasesSubmissionPayload, ScheduledCasesSubmissionResponse, BillableCasesSubmissionResponse
from db import CaseInfo, CasesDB

router = APIRouter(prefix="/cases", tags=["cases"])

def get_cases_db(request: Request) -> CasesDB:
    return request.app.state.db

CaseDBDependency = Annotated[CasesDB, Depends(get_cases_db)]

@router.post("/schedules")
async def post_schedules(payload: ScheduledCasesSubmissionPayload, cases_db: CaseDBDependency) -> ScheduledCasesSubmissionResponse:
    schedules = [ 
        CaseInfo(
            **case.model_dump(),
            status="scheduled",
            facility_id=payload.facility_id,
            provider_id=payload.provider_id,
            service_date=payload.service_date
        )
        for case in payload.cases
    ]
    ids = await asyncio.to_thread(cases_db.store_cases, schedules)
    return ScheduledCasesSubmissionResponse(scheduled=ids)


@router.get("/schedules")
async def get_schedules(cases_db: CaseDBDependency) -> list[CaseInfo]:
    return await asyncio.to_thread(
        cases_db.query_cases, 
        facility_id=DEFAULT_FACILITY_ID,
        provider_id=DEFAULT_PROVIDER_ID,
        status=["scheduled"]
    )


@router.post("/billables")
async def post_billables(payload: list[CaseInfo], cases_db: CaseDBDependency) -> BillableCasesSubmissionResponse:
    await asyncio.to_thread(cases_db.update_cases, payload)
    return BillableCasesSubmissionResponse(
        billable=[case.case_id for case in payload if case.status == "billable"],
        mission=[case.case_id for case in payload if case.status == "mission"],
        cancelled=[case.case_id for case in payload if case.status == "cancelled"],
        issues=[case.case_id for case in payload if case.status == "issue"]
    )


@router.get("/billables")
async def get_billables(cases_db: CaseDBDependency) -> BillableCasesQueryResponse:
    cases = await asyncio.to_thread(
        cases_db.query_cases, 
        facility_id=DEFAULT_FACILITY_ID,
        provider_id=DEFAULT_PROVIDER_ID,
        status=["billable", "mission", "cancelled", "issue"]
    )
    return BillableCasesQueryResponse(
        service_date=max(case.service_date for case in cases if case.service_date),
        cases=cases
    )