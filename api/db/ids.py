from uuid import UUID, uuid5, NAMESPACE_OID

from .schemas import CaseInfo

def create_case_id(case: CaseInfo) -> UUID:
    parts = []
    if case.service_date: parts.append(case.service_date.strftime("%Y%m%d"))
    if case.patient_id: parts.append(case.patient_id)

    if len(parts) < 2:
        raise ValueError("Not enough information to determine case ID")
    return uuid5(NAMESPACE_OID, "-".join(parts))