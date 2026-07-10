from datetime import date, datetime, time
from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, Field

IssueType = Literal["identity_issue", "needs_review"]
CaseStatus = Literal["scheduled", "billable", "mission", "cancelled", "issue"]


class CaseInfo(BaseModel):
    case_id: Optional[UUID] = Field(default=None, description="Case ID")
    patient_id: Optional[str] = Field(default=None, description="Patient MRN / identifier")
    service_date: Optional[date] = Field(default=None, description="Service date (YYYY-MM-DD)")
    
    case_position: Optional[int] = Field(default=None, description="Optional ordering position")    
    diagnosis: Optional[str] = Field(default=None, description="Diagnosis code")
    cpt: Optional[str] = Field(default=None, description="CPT code (optional on receive, required on document)")
    eye: Optional[str] = Field(default=None, description="Eye side (optional on receive, required on document)")
    
    minutes: Optional[int] = Field(default=None, description="Procedure minutes (suggested on receive, required on document)")
    status: Optional[CaseStatus] = Field(default=None, description="Terminal case status")
    sub_status: Optional[list[IssueType]] = Field(default=None, description="Issue types when status is issue")
    note: Optional[str] = Field(default=None, description="Optional case note")
    
    # internal maintainence fields
    ts: Optional[datetime] = Field(default=None, description="Timestamp of entry or update")

    # future extension fields
    provider_id: Optional[UUID] = Field(default=None, description="Provider ID")    
    service_time: Optional[time] = Field(default=None, description="Service time (HH:MM)")

class PatientInfo(BaseModel):
    patient_id: Optional[str] = Field(default=None, description="Patient MRN / identifier")
    patient_name: Optional[str] = Field(default=None, description="Patient name (LAST, FIRST)")
    patient_dob: Optional[date] = Field(default=None, description="Date of birth (YYYY-MM-DD)")

    # internal maintainence fields
    ts: Optional[datetime] = Field(default=None, description="Timestamp of entry or update")


class CaseView(CaseInfo):
    """Read model: case row + joined patient fields."""

    patient_name: Optional[str] = Field(default=None, description="Patient name (LAST, FIRST)")
    patient_dob: Optional[date] = Field(default=None, description="Date of birth (YYYY-MM-DD)")