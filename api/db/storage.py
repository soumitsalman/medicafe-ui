from datetime import date, datetime
from typing import Optional
from uuid import NAMESPACE_OID, UUID, uuid5

import duckdb

from .schemas import CaseInfo, CaseStatus, PatientInfo

_CASES_DDL = """
CREATE TABLE IF NOT EXISTS cases (
    case_id       UUID PRIMARY KEY,
    facility_id   UUID,
    provider_id   UUID,
    service_date  DATE,
    service_time  TIME,
    patient_id    VARCHAR, -- foreign key to patients table
    case_position INTEGER,
    diagnosis     VARCHAR,
    cpt           VARCHAR,
    eye           VARCHAR,
    minutes       INTEGER,
    status        VARCHAR,
    sub_status    VARCHAR[],
    note          VARCHAR,
    ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    patient_id    VARCHAR PRIMARY KEY,
    patient_name  VARCHAR,
    patient_dob   DATE,
    facility_id   UUID,
    ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CASE_COLUMNS = (
    "case_id",
    "facility_id",
    "provider_id",
    "service_date",
    "service_time",
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
)

_PATIENT_COLUMNS = (
    "patient_id",
    "patient_name",
    "patient_dob",
    "facility_id",
    "ts",
)

_CASE_UPDATE_COLUMNS = tuple(c for c in _CASE_COLUMNS if c != "case_id")
_CASE_COLS_CSV = ", ".join(_CASE_COLUMNS)
_CASE_ROW_PLACEHOLDERS = "(" + ", ".join("?" * len(_CASE_COLUMNS)) + ")"
_CASE_UPSERT_SET = ", ".join(
    f"{c} = COALESCE(EXCLUDED.{c}, cases.{c})" for c in _CASE_UPDATE_COLUMNS
)

_PATIENT_UPDATE_COLUMNS = tuple(c for c in _PATIENT_COLUMNS if c != "patient_id")
_PATIENT_COLS_CSV = ", ".join(_PATIENT_COLUMNS)
_PATIENT_ROW_PLACEHOLDERS = "(" + ", ".join("?" * len(_PATIENT_COLUMNS)) + ")"
_PATIENT_UPSERT_SET = ", ".join(
    f"{c} = COALESCE(EXCLUDED.{c}, patients.{c})" for c in _PATIENT_UPDATE_COLUMNS
)


class CasesDB:
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path or ":memory:")
        self.conn.execute(_CASES_DDL)

    @classmethod
    def _create_case_id(cls, case: CaseInfo) -> UUID:
        parts = []
        if case.facility_id:
            parts.append(case.facility_id.hex)
        if case.service_date:
            parts.append(case.service_date.strftime("%Y%m%d"))
        if case.service_time:
            parts.append(case.service_time.strftime("%H%M"))
        if case.patient_id:
            parts.append(case.patient_id)
        if not parts or len(parts) < 3:
            raise ValueError("Not enough information to create case ID")
        return uuid5(NAMESPACE_OID, "-".join(parts))

    @classmethod
    def _prepare_for_storage(cls, cases: list[CaseInfo]) -> list[CaseInfo]:
        now = datetime.now()
        for case in cases:
            if not case.case_id:
                case.case_id = cls._create_case_id(case)
            if not case.status:
                case.status = "scheduled"
            case.ts = now
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

    def store_cases(self, cases: list[CaseInfo]) -> list[UUID]:
        if not cases:
            return []
        cases = self._prepare_for_storage(cases)
        params: list = []
        for case in cases:
            params.extend(self._case_row_tuple(case))
        rows = self.conn.execute(
            f"""
            INSERT INTO cases ({_CASE_COLS_CSV})
            VALUES {self._case_values_clause(len(cases))}
            ON CONFLICT (case_id) DO UPDATE SET {_CASE_UPSERT_SET}
            RETURNING case_id
            """,
            params,
        ).fetchall()
        return [row[0] for row in rows]

    def store_patients(self, patients: list[PatientInfo]) -> list[str]:
        patients = [p for p in patients if p.patient_id]
        if not patients:
            return []
        patients = self._stamp_ts(patients)
        params: list = []
        for patient in patients:
            params.extend(self._patient_row_tuple(patient))
        rows = self.conn.execute(
            f"""
            INSERT INTO patients ({_PATIENT_COLS_CSV})
            VALUES {self._patient_values_clause(len(patients))}
            ON CONFLICT (patient_id) DO UPDATE SET {_PATIENT_UPSERT_SET}
            RETURNING patient_id
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
        result = self.conn.execute(
            f"SELECT {_CASE_COLS_CSV} FROM cases {where}",
            params,
        )
        columns = [desc[0] for desc in result.description]
        return [
            CaseInfo.model_validate(dict(zip(columns, row)))
            for row in result.fetchall()
        ]

    def close(self):
        self.conn.close()
