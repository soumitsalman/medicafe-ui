from datetime import date
from typing import Optional
from uuid import NAMESPACE_OID, UUID, uuid5

import duckdb

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

_CASE_COLUMNS = (
    "case_id",
    "facility_id",
    "provider_id",
    "service_date",
    "service_time",
    "case_pos",
    "patient_id",
    "patient_name",
    "patient_dob",
    "dx",
    "cpt",
    "eye",
    "minutes",
    "status",
    "sub_status",
    "note",
)

_UPDATE_COLUMNS = tuple(c for c in _CASE_COLUMNS if c != "case_id")
_COLS_CSV = ", ".join(_CASE_COLUMNS)
_ROW_PLACEHOLDERS = "(" + ", ".join("?" * len(_CASE_COLUMNS)) + ")"
_UPDATE_SET_CLAUSE = ", ".join(
    f"{c} = COALESCE(v.{c}, cases.{c})" for c in _UPDATE_COLUMNS
)


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

    @classmethod
    def _row_tuple(cls, case: CaseInfo) -> tuple:
        """Fixed-width row; unset/None fields become SQL NULL (not applied on update)."""
        data = case.model_dump(exclude_none=True)
        return tuple(data.get(col) for col in _CASE_COLUMNS)

    @classmethod
    def _values_clause(cls, n: int) -> str:
        return ", ".join(_ROW_PLACEHOLDERS for _ in range(n))

    def store_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        if not cases:
            return []
        cases = self._prepare_for_storage(cases)
        params: list = []
        for case in cases:
            params.extend(self._row_tuple(case))
        rows = self.conn.execute(
            f"""
            INSERT INTO cases ({_COLS_CSV})
            VALUES {self._values_clause(len(cases))}
            ON CONFLICT DO NOTHING
            RETURNING case_id
            """,
            params,
        ).fetchall()
        return [row[0] for row in rows]

    def update_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        cases = [c for c in cases if c.case_id]
        if not cases:
            return []
        params: list = []
        for case in cases:
            params.extend(self._row_tuple(case))
        rows = self.conn.execute(
            f"""
            UPDATE cases SET {_UPDATE_SET_CLAUSE}
            FROM (VALUES {self._values_clause(len(cases))}) AS v({_COLS_CSV})
            WHERE cases.case_id = v.case_id
            RETURNING cases.case_id
            """,
            params,
        ).fetchall()
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
        result = self.conn.execute(f"SELECT * FROM cases {where}", params)
        columns = [desc[0] for desc in result.description]
        return [
            CaseInfo.model_validate(dict(zip(columns, row)))
            for row in result.fetchall()
        ]

    def close(self):
        self.conn.close()
