from datetime import date
from typing import Optional
from uuid import NAMESPACE_OID, UUID, uuid5
from .models import CaseInfo, CaseStatus
from icecream import ic

class CasesDB:
    def __init__(self, db_path: str):
        self.cases = []

    @classmethod
    def _create_case_id(cls, case: CaseInfo) -> UUID:
        parts = []
        if case.facility_id: parts.append(case.facility_id.hex)
        if case.provider_id: parts.append(case.provider_id.hex)
        if case.service_date: parts.append(case.service_date.strftime("%Y%m%d"))
        if case.service_time: parts.append(case.service_time.strftime("%H%M"))
        if case.patient_id: parts.append(case.patient_id)
        if case.dx: parts.append(case.dx)
        if not parts or len(parts) < 3: 
            raise ValueError("Not enough information to create case ID")
        return uuid5(NAMESPACE_OID, "-".join(parts))

    @classmethod
    def _prepare_for_storage(cls, cases: list[CaseInfo]) -> list[CaseInfo]:
        for case in cases:            
            if not case.case_id: case.case_id = cls._create_case_id(case)
            if not case.status: case.status = "scheduled"
        return cases

    def store_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        cases = self._prepare_for_storage(cases)
        self.cases.extend(cases)
        ic(self.cases)
        return [case.case_id for case in cases]

    def update_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        updates_by_id = {case.case_id: case for case in cases if case.case_id}
        updated: list[UUID] = []
        for i, existing in enumerate(self.cases):
            if existing.case_id in updates_by_id:
                self.cases[i] = updates_by_id[existing.case_id]
                updated.append(existing.case_id)
        ic(self.cases)
        return updated

    def query_cases(
        self,
        facility_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        service_date: Optional[date] = None,
        status: Optional[list[CaseStatus]] = None,
    ) -> list[CaseInfo]:
        def filter_func(case: CaseInfo) -> bool:
            combined = True
            if facility_id: combined = combined and (case.facility_id == facility_id)
            if provider_id: combined = combined and (case.provider_id == provider_id)
            if service_date: combined = combined and (case.service_date == service_date)
            if status: combined = combined and (case.status in status)
            return combined
        return list(filter(filter_func, self.cases))

    def close(self):
        pass

