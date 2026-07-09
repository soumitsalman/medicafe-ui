from datetime import date, time
from typing import Optional
from uuid import NAMESPACE_OID, UUID, uuid5
from db.models import CaseInfo
from pydantic import BaseModel, Field

DEFAULT_FACILITY_ID = uuid5(NAMESPACE_OID, "default-facility")
DEFAULT_PROVIDER_ID = uuid5(NAMESPACE_OID, "default-provider")
_DEFAULT_DUMP_KWARGS = {"exclude_none": True}

class CaseInfoPayloadBase(BaseModel):
    service_time: Optional[time] = Field(default=None, description="Service time (HH:MM)")
    patient_id: str = Field(default=None, description="Patient MRN / identifier")
    patient_name: str = Field(default=None, description="Patient name (LAST, FIRST)")
    patient_dob: date = Field(default=None, description="Date of birth (YYYY-MM-DD)")
    dx: str = Field(default=None, description="Diagnosis code")
    cpt: str = Field(default=None, description="CPT code (optional on receive, required on document)")
    eye: str = Field(default=None, description="Eye side (optional on receive, required on document)")
    minutes: int = Field(default=None, description="Procedure minutes (suggested on receive, required on document)")
    
    def model_dump(self, **kwargs) -> dict:
        return super().model_dump(**(_DEFAULT_DUMP_KWARGS | kwargs))

class ScheduledCasesSubmissionPayload(BaseModel):
    class ScheduledCaseInfo(CaseInfoPayloadBase):
        case_pos: Optional[int] = Field(default=None, description="Optional ordering position")
        minutes: Optional[int] = Field(default=None, description="Procedure minutes (suggested on receive, required on document)")

    facility_id: Optional[UUID] = Field(default=DEFAULT_FACILITY_ID, description="Facility ID")
    provider_id: Optional[UUID] = Field(default=DEFAULT_PROVIDER_ID, description="Provider ID")
    service_date: date = Field(description="Shift date (MM-dd-yyyy)")
    cases: list[ScheduledCaseInfo] = Field(description="Scheduled cases for the shift")

class ScheduledCasesSubmissionResponse(BaseModel):
    scheduled: list[UUID] = Field(description="Scheduled case IDs")

class BillableCasesSubmissionResponse(BaseModel):
    billable: list[UUID] = Field(description="Billed case IDs")
    mission: list[UUID] = Field(description="Mission case IDs")
    cancelled: list[UUID] = Field(description="Cancelled case IDs")
    issues: list[UUID] = Field(description="Issue case IDs")
    
class BillableCasesQueryResponse(BaseModel):
    facility_id: Optional[UUID] = Field(default=DEFAULT_FACILITY_ID, description="Facility ID")
    provider_id: Optional[UUID] = Field(default=DEFAULT_PROVIDER_ID, description="Provider ID")
    service_date: Optional[date] = Field(default=None, description="Shift date (MM-dd-yyyy)")
    cases: list[CaseInfo] = Field(description="Billable cases for the shift")

