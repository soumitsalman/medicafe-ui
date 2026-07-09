from datetime import date
from typing import Optional
from uuid import NAMESPACE_OID, UUID, uuid5

import duckdb
import pandas as pd

from .models import CaseInfo, CaseStatus

_CASES_DDL = """
CREATE TABLE IF NOT EXISTS cases (
    case_id       UUID PRIMARY KEY,
    facility_id   UUID,
    provider_id   UUID,
    service_date  DATE,
    service_time  TIME,
    case_pos      INTEGER,
    patient_id    VARCHAR,
    patient_name  VARCHAR,
    patient_dob   DATE,
    dx            VARCHAR,
    cpt           VARCHAR,
    eye           VARCHAR,
    minutes       INTEGER,
    status        VARCHAR,
    sub_status    VARCHAR[],
    note          VARCHAR
)
"""


class CasesDB:
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path or ":memory:")
        self.conn.execute(_CASES_DDL)

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
        df = pd.DataFrame([c.model_dump() for c in cases])
        rows = self.conn.execute("""
            INSERT INTO cases BY NAME SELECT * FROM df
            ON CONFLICT DO NOTHING
            RETURNING case_id
        """).fetchall()
        return [row[0] for row in rows]

    def update_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        df = pd.DataFrame([c.model_dump() for c in cases if c.case_id])
        if df.empty:
            return []
        rows = self.conn.execute("""
            UPDATE cases SET
                facility_id  = COALESCE(df.facility_id,  cases.facility_id),
                provider_id  = COALESCE(df.provider_id,  cases.provider_id),
                service_date = COALESCE(df.service_date, cases.service_date),
                service_time = COALESCE(df.service_time, cases.service_time),
                case_pos     = COALESCE(df.case_pos,     cases.case_pos),
                patient_id   = COALESCE(df.patient_id,   cases.patient_id),
                patient_name = COALESCE(df.patient_name, cases.patient_name),
                patient_dob  = COALESCE(df.patient_dob,  cases.patient_dob),
                dx           = COALESCE(df.dx,           cases.dx),
                cpt          = COALESCE(df.cpt,          cases.cpt),
                eye          = COALESCE(df.eye,          cases.eye),
                minutes      = COALESCE(df.minutes,      cases.minutes),
                status       = COALESCE(df.status,       cases.status),
                sub_status   = COALESCE(df.sub_status,   cases.sub_status),
                note         = COALESCE(df.note,         cases.note)
            FROM df
            WHERE cases.case_id = df.case_id
            RETURNING cases.case_id
        """).fetchall()
        return [row[0] for row in rows]

    def query_cases(
        self,
        facility_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        service_date: Optional[date] = None,
        status: Optional[list[CaseStatus]] = None,
    ) -> list[CaseInfo]:
        clauses, params = [], []
        if facility_id:
            clauses.append("facility_id = ?")
            params.append(facility_id)
        if provider_id:
            clauses.append("provider_id = ?")
            params.append(provider_id)
        if service_date:
            clauses.append("service_date = ?")
            params.append(service_date)
        if status:
            clauses.append(f"status IN ({', '.join('?' * len(status))})")
            params.extend(status)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        df = self.conn.execute(f"SELECT * FROM cases {where}", params).df()
        return [CaseInfo.model_validate(row) for row in df.to_dict(orient="records")]

    def close(self):
        self.conn.close()
