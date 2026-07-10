"""Unit tests for CasesDB storage (insert / update / query).

Inserts never supply case_id — storage derives it from patient_id + service_date.
Updates may supply case_id or omit it; update_cases calls _ensure_case_id either way.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from db.ids import create_case_id
from db.schemas import CaseInfo, PatientInfo
from db.storage import CasesDB


@pytest.fixture
def db(tmp_path):
    store = CasesDB(str(tmp_path / "cases.duckdb"))
    yield store
    store.close()


def _case(**overrides) -> CaseInfo:
    """Seed/insert helper — must not pass case_id."""
    assert "case_id" not in overrides, "insert/seed helpers must not pass case_id"
    base = dict(
        patient_id="P1",
        service_date=date(2026, 1, 20),
        case_position=1,
        diagnosis="H25.812",
        cpt="00142",
        eye="LEFT",
        minutes=15,
        status="scheduled",
    )
    base.update(overrides)
    return CaseInfo(**base)


def _update_case(*, case_id: UUID | None = None, **overrides) -> CaseInfo:
    """Update payload helper — case_id optional (explicit or derived by storage)."""
    base = dict(
        patient_id="P1",
        service_date=date(2026, 1, 20),
        case_position=1,
        diagnosis="H25.812",
        cpt="00142",
        eye="LEFT",
        minutes=15,
        status="scheduled",
    )
    base.update(overrides)
    if case_id is not None:
        base["case_id"] = case_id
    return CaseInfo(**base)


def _patient(**overrides) -> PatientInfo:
    base = dict(
        patient_id="P1",
        patient_name="DOE, JANE",
        patient_dob=date(1950, 1, 1),
    )
    base.update(overrides)
    return PatientInfo(**base)


def test_insert_cases_stores_new_only_does_not_change_existing(db):
    original = _case(patient_id="P1", service_date=date(2026, 1, 20), minutes=15, status="scheduled")
    expected_id = create_case_id(original)
    assert db.insert_cases([original]) == [expected_id]

    conflict = _case(
        patient_id="P1",
        service_date=date(2026, 1, 20),
        minutes=99,
        diagnosis="H26.9",
        status="billable",
        note="should not apply",
    )
    assert db.insert_cases([conflict]) == []

    rows = db.query_cases()
    assert len(rows) == 1
    assert rows[0].case_id == expected_id
    assert rows[0].minutes == 15
    assert rows[0].diagnosis == "H25.812"
    assert rows[0].status == "scheduled"
    assert rows[0].note is None


def test_insert_patients_stores_new_only_does_not_change_existing(db):
    original = _patient(patient_id="P1", patient_name="DOE, JANE", patient_dob=date(1950, 1, 1))
    assert db.insert_patients([original]) == ["P1"]

    conflict = _patient(patient_id="P1", patient_name="SMITH, JOHN", patient_dob=date(1990, 5, 5))
    assert db.insert_patients([conflict]) == []

    db.insert_cases([_case(patient_id="P1")])
    rows = db.query_cases(patient_id="P1")
    assert len(rows) == 1
    assert rows[0].patient_name == "DOE, JANE"
    assert rows[0].patient_dob == date(1950, 1, 1)


@pytest.mark.parametrize("explicit_case_id", [False, True], ids=["derived_id", "explicit_id"])
def test_update_cases_only_updates_existing_leaves_others_unchanged(db, explicit_case_id):
    keep = _case(patient_id="P1", service_date=date(2026, 1, 20), minutes=10, status="scheduled")
    target = _case(patient_id="P2", service_date=date(2026, 1, 20), minutes=20, status="scheduled")
    keep_id = create_case_id(keep)
    update_id = create_case_id(target)

    assert set(db.insert_cases([keep, target])) == {keep_id, update_id}

    patch_target = _update_case(
        case_id=update_id if explicit_case_id else None,
        patient_id="P2",
        service_date=date(2026, 1, 20),
        minutes=45,
        status="billable",
    )
    patch_missing = _update_case(
        case_id=uuid4() if explicit_case_id else None,
        patient_id="P9",
        service_date=date(2026, 1, 20),
        minutes=1,
        status="mission",
    )
    updated = db.update_cases([patch_target, patch_missing])
    assert updated == [update_id]
    assert patch_target.case_id == update_id

    by_id = {row.case_id: row for row in db.query_cases()}
    assert set(by_id) == {keep_id, update_id}
    assert by_id[keep_id].minutes == 10
    assert by_id[keep_id].status == "scheduled"
    assert by_id[update_id].minutes == 45
    assert by_id[update_id].status == "billable"


def test_update_patients_only_updates_existing_leaves_others_unchanged(db):
    db.insert_patients(
        [
            _patient(patient_id="P1", patient_name="ALPHA"),
            _patient(patient_id="P2", patient_name="BETA"),
        ]
    )
    db.insert_cases(
        [
            _case(patient_id="P1", service_date=date(2026, 1, 20)),
            _case(patient_id="P2", service_date=date(2026, 1, 20)),
        ]
    )

    updated = db.update_patients(
        [
            _patient(patient_id="P2", patient_name="BETA UPDATED"),
            _patient(patient_id="P9", patient_name="MISSING"),
        ]
    )
    assert updated == ["P2"]

    by_pid = {row.patient_id: row for row in db.query_cases()}
    assert by_pid["P1"].patient_name == "ALPHA"
    assert by_pid["P2"].patient_name == "BETA UPDATED"
    assert "P9" not in by_pid


@pytest.mark.parametrize("explicit_case_id", [False, True], ids=["derived_id", "explicit_id"])
def test_update_cases_skips_null_fields(db, explicit_case_id):
    seed = _case(
        patient_id="P1",
        service_date=date(2026, 1, 20),
        minutes=18,
        diagnosis="H25.812",
        cpt="00142",
        eye="LEFT",
        status="billable",
        note="keep me",
        sub_status=["identity_issue"],
    )
    expected_id = create_case_id(seed)
    assert db.insert_cases([seed]) == [expected_id]

    patch = CaseInfo(
        case_id=expected_id if explicit_case_id else None,
        patient_id="P1",
        service_date=date(2026, 1, 20),
        status="mission",
        # minutes, diagnosis, cpt, eye, note, sub_status intentionally null
    )
    updated = db.update_cases([patch])
    assert updated == [expected_id]
    assert patch.case_id == expected_id

    row = db.query_cases()[0]
    assert row.status == "mission"
    assert row.minutes == 18
    assert row.diagnosis == "H25.812"
    assert row.cpt == "00142"
    assert row.eye == "LEFT"
    assert row.note == "keep me"
    assert row.sub_status == ["identity_issue"]


def test_update_patients_skips_null_fields(db):
    db.insert_patients(
        [_patient(patient_id="P1", patient_name="DOE, JANE", patient_dob=date(1950, 1, 1))]
    )
    db.insert_cases([_case(patient_id="P1")])

    updated = db.update_patients(
        [PatientInfo(patient_id="P1", patient_name="DOE, JANE UPDATED")]
    )
    assert updated == ["P1"]

    row = db.query_cases(patient_id="P1")[0]
    assert row.patient_name == "DOE, JANE UPDATED"
    assert row.patient_dob == date(1950, 1, 1)


def test_query_cases_joins_patient_fields_allowing_missing_name_dob(db):
    with_demo = _case(patient_id="P1", service_date=date(2026, 1, 20), case_position=1)
    without_demo = _case(patient_id="P2", service_date=date(2026, 1, 20), case_position=2)
    orphan = _case(patient_id="P3", service_date=date(2026, 1, 20), case_position=3)
    with_demo_id = create_case_id(with_demo)
    without_demo_id = create_case_id(without_demo)
    orphan_id = create_case_id(orphan)

    db.insert_patients(
        [
            _patient(patient_id="P1", patient_name="DOE, JANE", patient_dob=date(1950, 1, 1)),
            PatientInfo(patient_id="P2"),  # id only — no name/dob
        ]
    )
    assert set(db.insert_cases([with_demo, without_demo, orphan])) == {
        with_demo_id,
        without_demo_id,
        orphan_id,
    }

    rows = {row.case_id: row for row in db.query_cases()}
    assert set(rows) == {with_demo_id, without_demo_id, orphan_id}

    assert rows[with_demo_id].patient_name == "DOE, JANE"
    assert rows[with_demo_id].patient_dob == date(1950, 1, 1)
    assert rows[with_demo_id].diagnosis == "H25.812"

    assert rows[without_demo_id].patient_id == "P2"
    assert rows[without_demo_id].patient_name is None
    assert rows[without_demo_id].patient_dob is None
    assert rows[without_demo_id].diagnosis == "H25.812"

    assert rows[orphan_id].patient_id == "P3"
    assert rows[orphan_id].patient_name is None
    assert rows[orphan_id].patient_dob is None
    assert rows[orphan_id].diagnosis == "H25.812"


def test_insert_cases_derives_case_id_from_patient_and_service_date(db):
    case = _case(patient_id="P10", service_date=date(2026, 2, 1), minutes=12)
    expected_id = create_case_id(case)

    inserted = db.insert_cases([case])
    assert inserted == [expected_id]
    assert case.case_id == expected_id

    rows = db.query_cases(patient_id="P10")
    assert len(rows) == 1
    assert rows[0].case_id == expected_id
    assert rows[0].minutes == 12


def test_insert_cases_conflict_same_derived_id_does_not_change_existing(db):
    first = _case(patient_id="P11", service_date=date(2026, 3, 1), minutes=10, status="scheduled")
    expected_id = create_case_id(first)
    assert db.insert_cases([first]) == [expected_id]

    second = _case(
        patient_id="P11",
        service_date=date(2026, 3, 1),
        minutes=99,
        status="billable",
        diagnosis="H26.9",
    )
    assert create_case_id(second) == expected_id
    assert db.insert_cases([second]) == []

    row = db.query_cases(patient_id="P11")[0]
    assert row.case_id == expected_id
    assert row.minutes == 10
    assert row.status == "scheduled"
    assert row.diagnosis == "H25.812"


def test_insert_cases_distinct_keys_get_distinct_ids(db):
    a = _case(patient_id="P12", service_date=date(2026, 4, 1), case_position=1)
    b = _case(patient_id="P13", service_date=date(2026, 4, 1), case_position=2)
    c = _case(patient_id="P12", service_date=date(2026, 4, 2), case_position=3)

    inserted = db.insert_cases([a, b, c])
    assert set(inserted) == {create_case_id(a), create_case_id(b), create_case_id(c)}
    assert len(set(inserted)) == 3
    assert len(db.query_cases()) == 3


@pytest.mark.parametrize("explicit_case_id", [False, True], ids=["derived_id", "explicit_id"])
def test_update_cases_updates_existing_with_or_without_case_id(db, explicit_case_id):
    seed = _case(patient_id="P14", service_date=date(2026, 5, 1), minutes=10, status="scheduled")
    expected_id = create_case_id(seed)
    assert db.insert_cases([seed]) == [expected_id]

    patch = _update_case(
        case_id=expected_id if explicit_case_id else None,
        patient_id="P14",
        service_date=date(2026, 5, 1),
        minutes=40,
        status="billable",
    )
    updated = db.update_cases([patch])
    assert updated == [expected_id]
    assert patch.case_id == expected_id

    row = db.query_cases(patient_id="P14")[0]
    assert row.case_id == expected_id
    assert row.minutes == 40
    assert row.status == "billable"


@pytest.mark.parametrize("explicit_case_id", [False, True], ids=["derived_id", "explicit_id"])
def test_update_cases_does_not_create_missing(db, explicit_case_id):
    if explicit_case_id:
        missing_id = uuid4()
        patch = _update_case(
            case_id=missing_id,
            patient_id="P16",
            service_date=date(2026, 7, 1),
            minutes=5,
            status="billable",
        )
        assert db.update_cases([patch]) == []
        assert patch.case_id == missing_id
    else:
        patch = _case(patient_id="P16", service_date=date(2026, 7, 1), minutes=5, status="billable")
        expected_id = create_case_id(patch)
        assert db.update_cases([patch]) == []
        assert patch.case_id == expected_id

    assert db.query_cases() == []


def test_ensure_case_id_requires_patient_and_service_date(db):
    with pytest.raises(ValueError, match="Not enough information"):
        db.insert_cases([CaseInfo(patient_id="P17", status="scheduled")])

    with pytest.raises(ValueError, match="Not enough information"):
        db.update_cases([CaseInfo(service_date=date(2026, 8, 1), status="billable")])
