from datetime import date, datetime
from typing import Optional
from uuid import UUID

import duckdb

from .ids import create_case_id
from .schemas import CaseInfo, CaseStatus, CaseView, IssueType, PatientInfo

_DB_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cases (
    case_id       UUID PRIMARY KEY,    
    service_date  DATE NOT NULL,
    patient_id    VARCHAR NOT NULL, -- foreign key to patients table
    
    case_position INTEGER,
    diagnosis     VARCHAR NOT NULL,
    cpt           VARCHAR,
    eye           VARCHAR,

    minutes       INTEGER,
    status        VARCHAR NOT NULL,
    sub_status    VARCHAR[],
    note          VARCHAR,

    ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    provider_id   UUID,
    service_time  TIME

);

CREATE TABLE IF NOT EXISTS patients (
    patient_id    VARCHAR PRIMARY KEY,
    patient_name  VARCHAR,
    patient_dob   DATE,
    
    ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CASE_COLUMNS = (
    "case_id",
    "service_date",
    "patient_id",
    "case_position",
    "diagnosis",
    "cpt",
    "eye",
    "minutes",
    "status",
    "sub_status",
    "note",
    "ts",
    "provider_id",
    "service_time",
)

_PATIENT_COLUMNS = (
    "patient_id",
    "patient_name",
    "patient_dob",
    "ts",
)

_CASE_UPDATE_COLUMNS = tuple(c for c in _CASE_COLUMNS if c != "case_id")
_CASE_COLS_CSV = ", ".join(_CASE_COLUMNS)
_CASE_ROW_PLACEHOLDERS = "(" + ", ".join("?" * len(_CASE_COLUMNS)) + ")"
_CASE_UPDATE_SET = ", ".join(
    f"{c} = COALESCE(v.{c}, cases.{c})" for c in _CASE_UPDATE_COLUMNS
)

_PATIENT_UPDATE_COLUMNS = tuple(c for c in _PATIENT_COLUMNS if c != "patient_id")
_PATIENT_COLS_CSV = ", ".join(_PATIENT_COLUMNS)
_PATIENT_ROW_PLACEHOLDERS = "(" + ", ".join("?" * len(_PATIENT_COLUMNS)) + ")"
_PATIENT_UPDATE_SET = ", ".join(
    f"{c} = COALESCE(v.{c}, patients.{c})" for c in _PATIENT_UPDATE_COLUMNS
)


class CasesDB:
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path or ":memory:")
        self._cursor().execute(_DB_SCHEMA_SQL)

    def _cursor(self) -> duckdb.DuckDBPyConnection:
        return self.conn.cursor()

    @classmethod
    def _ensure_case_id(cls, cases: list[CaseInfo]) -> list[CaseInfo]:
        for case in cases:
            if not case.case_id:
                case.case_id = create_case_id(case)
        return cases

    @classmethod
    def _stamp_ts(cls, items: list[CaseInfo] | list[PatientInfo]) -> list:
        now = datetime.now()
        for item in items:
            item.ts = now
        return items

    @classmethod
    def _case_row_tuple(cls, case: CaseInfo) -> tuple:
        """Fixed-width row; unset/None fields become SQL NULL (not applied on update)."""
        data = case.model_dump(exclude_none=True)
        return tuple(data.get(col) for col in _CASE_COLUMNS)

    @classmethod
    def _patient_row_tuple(cls, patient: PatientInfo) -> tuple:
        """Fixed-width row; unset/None fields become SQL NULL (not applied on update)."""
        data = patient.model_dump(exclude_none=True)
        return tuple(data.get(col) for col in _PATIENT_COLUMNS)

    @classmethod
    def _case_values_clause(cls, n: int) -> str:
        return ", ".join(_CASE_ROW_PLACEHOLDERS for _ in range(n))

    @classmethod
    def _patient_values_clause(cls, n: int) -> str:
        return ", ".join(_PATIENT_ROW_PLACEHOLDERS for _ in range(n))

    def insert_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        if not cases:
            return []

        cases = self._ensure_case_id(cases)
        cases = self._stamp_ts(cases)
        params: list = []
        for case in cases:
            params.extend(self._case_row_tuple(case))
        rows = self._cursor().execute(
            f"""
            INSERT INTO cases ({_CASE_COLS_CSV})
            VALUES {self._case_values_clause(len(cases))}
            ON CONFLICT (case_id) DO NOTHING
            RETURNING case_id
            """,
            params,
        ).fetchall()
        return [row[0] for row in rows]

    def update_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        if not cases:
            return []

        cases = self._ensure_case_id(cases)
        cases = self._stamp_ts(cases)
        params: list = []
        for case in cases:
            params.extend(self._case_row_tuple(case))
        rows = self._cursor().execute(
            f"""
            UPDATE cases
            SET {_CASE_UPDATE_SET}
            FROM (VALUES {self._case_values_clause(len(cases))}) AS v({_CASE_COLS_CSV})
            WHERE cases.case_id = v.case_id
            RETURNING cases.case_id
            """,
            params,
        ).fetchall()
        return [row[0] for row in rows]

    def insert_patients(self, patients: list[PatientInfo]) -> list[str]:
        patients = [p for p in patients if p.patient_id]
        if not patients:
            return []
        patients = self._stamp_ts(patients)
        params: list = []
        for patient in patients:
            params.extend(self._patient_row_tuple(patient))
        rows = self._cursor().execute(
            f"""
            INSERT INTO patients ({_PATIENT_COLS_CSV})
            VALUES {self._patient_values_clause(len(patients))}
            ON CONFLICT (patient_id) DO NOTHING
            RETURNING patient_id
            """,
            params,
        ).fetchall()
        return [row[0] for row in rows]

    def update_patients(self, patients: list[PatientInfo]) -> list[str]:
        patients = [p for p in patients if p.patient_id]
        if not patients:
            return []
        patients = self._stamp_ts(patients)
        params: list = []
        for patient in patients:
            params.extend(self._patient_row_tuple(patient))
        rows = self._cursor().execute(
            f"""
            UPDATE patients
            SET {_PATIENT_UPDATE_SET}
            FROM (VALUES {self._patient_values_clause(len(patients))}) AS v({_PATIENT_COLS_CSV})
            WHERE patients.patient_id = v.patient_id
            RETURNING patients.patient_id
            """,
            params,
        ).fetchall()
        return [row[0] for row in rows]

    def query_cases(
        self,
        patient_id: Optional[str] = None,
        service_date: Optional[date] = None,
        status: Optional[list[CaseStatus]] = None,
        provider_id: Optional[UUID] = None,
    ) -> list[CaseView]:
        clauses, params = [], []
        if patient_id:
            clauses.append("cases.patient_id = ?")
            params.append(patient_id)
        if service_date:
            clauses.append("cases.service_date = ?")
            params.append(service_date)
        if status:
            clauses.append(f"cases.status IN ({', '.join('?' * len(status))})")
            params.extend(status)
        if provider_id:
            clauses.append("cases.provider_id = ?")
            params.append(provider_id)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        result = self._cursor().execute(
            f"""
            SELECT cases.* EXCLUDE (ts), patients.patient_name, patients.patient_dob
            FROM cases
            LEFT JOIN patients ON cases.patient_id = patients.patient_id
            {where}
            """,
            params,
        )
        columns = [desc[0] for desc in result.description]
        return [
            CaseView.model_validate(dict(zip(columns, row)))
            for row in result.fetchall()
        ]

    def close(self):
        self.conn.close()
