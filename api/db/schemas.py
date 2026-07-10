from datetime import date, datetime, time
from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, Field

IssueType = Literal["identity_issue", "needs_review"]
CaseStatus = Literal["scheduled", "billable", "mission", "cancelled", "skipped"]


class CaseInfo(BaseModel):
    case_id: Optional[UUID] = Field(default=None, description="Case ID")
    patient_id: Optional[str] = Field(default=None, description="Patient MRN / identifier")
    service_date: Optional[date] = Field(default=None, description="Service date (YYYY-MM-DD)")
    
    case_position: Optional[int] = Field(default=None, description="Optional ordering position in schedule. Used for UI ONLY.")    
    diagnosis: Optional[str] = Field(default=None, description="Diagnosis code")
    cpt: Optional[str] = Field(default=None, description="CPT code")
    eye: Optional[str] = Field(default=None, description="Eye side")
    
    minutes: Optional[int] = Field(default=None, description="Procedure minutes")
    status: Optional[CaseStatus] = Field(
        default=None, 
        description=(
            "`scheduled` -> still needs triage, minutes, mission, cpt etc. and other details input from provider.\n"
            "`billable` -> all details are input from provider and these should be billed.\n"
            "`mission` -> all details are input from provider and these should not be billed but tracked.\n"
            "`cancelled` -> case was cancelled by provider/facilty/patient. minutes == 0 for this case.\n"
            "`skipped` -> case was skipped by provider because there is some issue. Look into sub_status and notes for more details."
        )
    )
    sub_status: Optional[list[IssueType]] = Field(default=None, description="Issue types when status is `skipped`")
    note: Optional[str] = Field(default=None, description="Optional case note")
    
    # internal maintainence fields
    ts: Optional[datetime] = Field(default=None, description="Timestamp of entry or update. Internal use only.")

    # future extension fields
    provider_id: Optional[UUID] = Field(default=None, description="Provider ID. Ignore for now.")    
    service_time: Optional[time] = Field(default=None, description="Service time (HH:MM). Ignore for now.")

class PatientInfo(BaseModel):
    patient_id: Optional[str] = Field(default=None, description="Patient MRN / identifier")
    patient_name: Optional[str] = Field(default=None, description="Patient name (LAST, FIRST)")
    patient_dob: Optional[date] = Field(default=None, description="Date of birth (YYYY-MM-DD)")

    # internal maintainence fields
    ts: Optional[datetime] = Field(default=None, description="Timestamp of entry or update")


class CaseView(CaseInfo):
    """Aggregated details related to a case."""
    patient_name: Optional[str] = Field(default=None, description="Patient name (LAST, FIRST)")
    patient_dob: Optional[date] = Field(default=None, description="Date of birth (YYYY-MM-DD)")
    ts: Optional[datetime] = Field(default=None, exclude=True)