from typing import Optional
from uuid import NAMESPACE_OID, UUID, uuid5
from pydantic import BaseModel, Field
from db import CaseStatus

DEFAULT_FACILITY_ID = uuid5(NAMESPACE_OID, "default-facility")
DEFAULT_PROVIDER_ID = uuid5(NAMESPACE_OID, "default-provider")

from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import date
from typing_extensions import Annotated


class CaseKey(BaseModel):
    """Composite identity for a scheduled case before a UUID `case_id` exists.

    Agents: use this key (not `case_id`) when calling POST/PATCH `/cases/schedules`.
    Uniqueness = (`patient_id`, `dos`).
    """
    patient_id: str = Field(
        description="Patient MRN / medical record number. Required. Part of the case composite key."
    )
    dos: str = Field(
        description=(
            "Date of service in MM-DD-YYYY format (e.g. '08-03-2026'). "
            "Required. Part of the case composite key. "
            "Do NOT use ISO YYYY-MM-DD here — that format is only for query params and CaseInfo.service_date."
        )
    )


class CasePatch(BaseModel):
    """Mutable fields applied to a case (and optionally its patient) on schedule ingest/update.

    Agents: omit a field to leave it unchanged on PATCH; send null/empty string to clear nullable string fields.
    `status` is only meaningful on PATCH — POST `/schedules` always forces status=`scheduled`.
    """
    patient_name: Optional[str] = Field(
        default=None,
        description="Patient display name, preferably 'LAST, FIRST'. Upserts into the patients table when present.",
    )
    diagnosis: Optional[str] = Field(
        default=None,
        description="Diagnosis / DX code (e.g. 'H25.812'). Maps to CaseInfo.diagnosis.",
    )
    cpt: Optional[str] = Field(
        default=None,
        description="CPT procedure code (e.g. '00142'). Usually derived from diagnosis upstream.",
    )
    eye: Optional[str] = Field(
        default=None,
        description="Laterality / eye side (e.g. 'LEFT', 'RIGHT', 'BOTH'). Usually derived from diagnosis upstream.",
    )
    minutes: Optional[int] = Field(
        default=None,
        description=(
            "Suggested procedure minutes. "
            "Semantics once documented by the provider UI: null=undocumented/scheduled, 0=cancelled, >0=billable or mission."
        ),
    )
    docx_position: Optional[int] = Field(
        default=None,
        description=(
            "Sort order for the day's schedule (maps to CaseInfo.case_position). "
            "UI-only ordering; lower values appear first. Not a clinical field."
        ),
    )
    status: Optional[str] = Field(
        default=None,
        description=(
            "Case lifecycle status. Accepted values on schedule routes: "
            "`scheduled` | `skipped` | `mission` | `billable`. "
            "Other values (including `cancelled`) are ignored/nullified by the router. "
            "On POST `/schedules` this field is overwritten to `scheduled`."
        ),
    )
    note: Optional[str] = Field(
        default=None,
        description="Free-text case note. Empty/null clears or omits the note.",
    )


class CaseRow(BaseModel):
    """One schedule row: identity key + fields to apply.

    Agents: every row MUST include `key` with both `patient_id` and `dos`. Missing either yields HTTP 422.
    """
    key: CaseKey = Field(description="Composite case identity: patient_id + dos (MM-DD-YYYY).")
    patch: CasePatch = Field(description="Fields to insert (POST) or update/insert (PATCH) for this case/patient.")


class CaseSchedules(BaseModel):
    """Request body for POST and PATCH `/cases/schedules`.

    Agents:
    - Use POST for brand-new incoming schedule loads (idempotent insert; existing keys skipped).
    - Use PATCH to update existing cases and backfill previously missing rows.
    - `rows` must be non-empty (min_length=1).
    """
    rows: list[CaseRow] = Field(
        ...,
        min_length=1,
        description="Non-empty list of case rows to schedule or update. Each row is keyed by patient_id + dos.",
    )


CaseUpdateResult = dict[str, list[UUID]]
"""Mutation response shape: keys like `inserted` and/or `updated` mapping to lists of case UUID strings.

Agents: treat listed UUIDs as the durable `case_id` values for later billable operations.
"""

# class CaseInsert(BaseModel):
#     diagnosis: str
#     eye: str
#     position: str = Field(description="Case position. This should ideally be a number but upstream system has bugs")
#     patient_name: Optional[str] = None
#     patient_dob: Optional[str] = Field(default=None, description="Date of birth (MM-dd-yyyy)")

# class PatientCaseInserts(BaseModel):
#     patients: dict[str, CaseInsert] = Field(description="Scheduled cases for the shift. Keyed by patient ID.")

# class CurrentScheduleInserts(BaseModel):
#     current: PatientCaseInserts

# class ScheduleInsertsPayload(BaseModel):
#     schedules: dict[str, CurrentScheduleInserts] = Field(description="Scheduled cases for the shift. Keyed by date (MM-dd-yyyy).")

# class CaseUpdate(BaseModel):
#     patient_id: str = None
#     dos: str = Field(description="Date of service (MM-dd-yyyy)")
       
#     patient_display_name: Optional[str] = None
#     patient_dob: Optional[str] = Field(default=None, description="Date of birth (MM-dd-yyyy)") 
#     diagnosis: Optional[str] = None
#     cpt: Optional[str] = None
#     docx_position: Optional[int] = None
#     status: Optional[CaseStatus] = None

# class CaseUpdatesPayloads(BaseModel):
#     rows: dict[str, CaseUpdate] = Field(description="Cases to update. Keyed by patient ID and date (MM-dd-yyyy).")
