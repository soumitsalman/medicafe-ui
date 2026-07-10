from typing import Optional
from uuid import NAMESPACE_OID, uuid5
from pydantic import BaseModel, Field

DEFAULT_FACILITY_ID = uuid5(NAMESPACE_OID, "default-facility")
DEFAULT_PROVIDER_ID = uuid5(NAMESPACE_OID, "default-provider")

class CaseInsert(BaseModel):
    diagnosis: str
    eye: str
    position: str = Field(description="Case position. This should ideally be a number but upstream system has bugs")
    patient_name: Optional[str] = None
    patient_dob: Optional[str] = Field(default=None, description="Date of birth (MM-dd-yyyy)")

class PatientCaseInserts(BaseModel):
    patients: dict[str, CaseInsert] = Field(description="Scheduled cases for the shift. Keyed by patient ID.")

class CurrentScheduleInserts(BaseModel):
    current: PatientCaseInserts

class ScheduleInsertsPayload(BaseModel):
    schedules: dict[str, CurrentScheduleInserts] = Field(description="Scheduled cases for the shift. Keyed by date (MM-dd-yyyy).")

class CaseUpdate(BaseModel):
    patient_id: str = None
    dos: str = Field(description="Date of service (MM-dd-yyyy)")
       
    patient_display_name: Optional[str] = None
    patient_dob: Optional[str] = Field(default=None, description="Date of birth (MM-dd-yyyy)") 
    diagnosis: Optional[str] = None
    cpt: Optional[str] = None
    docx_position: Optional[int] = None

class CaseUpdatesPayloads(BaseModel):
    rows: dict[str, CaseUpdate] = Field(description="Cases to update. Keyed by patient ID and date (MM-dd-yyyy).")
