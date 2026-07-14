"""Router → DB wiring tests for /cases/schedules and /cases/billables."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from db.ids import create_case_id
from db.schemas import CaseInfo
from fixtures import load_fixture

SLI_REMOTE_INITIAL_INSERT = "sli-remote-initial-insert.json"
SLI_REMOTE_UPSERT_MINUTES_NOTE = "sli-remote-upsert-minutes-note.json"
SLI_REMOTE_UPSERT_DX_CPT = "sli-remote-upsert-dx-cpt.json"
SLI_REMOTE_UPSERT_CLEAR_AND_COMPLETE = "sli-remote-upsert-clear-and-complete.json"

_MDY = "%m-%d-%Y"


def _parse_mdy(dos: str) -> date:
    return datetime.strptime(dos, _MDY).date()


def expected_case_ids(payload: dict) -> set[str]:
    return {
        str(
            create_case_id(
                CaseInfo(
                    patient_id=row["key"]["patient_id"],
                    service_date=_parse_mdy(row["key"]["dos"]),
                )
            )
        )
        for row in payload["rows"]
    }


def schedules_seed_from_billables(billables: list[dict]) -> dict:
    """Build CaseSchedules body so billable case_ids remain create_case_id-stable."""
    rows = []
    for case in billables:
        service_date = date.fromisoformat(case["service_date"])
        rows.append(
            {
                "key": {
                    "patient_id": case["patient_id"],
                    "dos": service_date.strftime(_MDY),
                },
                "patch": {
                    "diagnosis": case.get("diagnosis"),
                    "eye": case.get("eye"),
                    "docx_position": case.get("case_position"),
                },
            }
        )
    return {"rows": rows}


@pytest.fixture
def sli_remote_initial_insert():
    return load_fixture(SLI_REMOTE_INITIAL_INSERT)


@pytest.fixture
def sli_remote_upsert_minutes_note():
    return load_fixture(SLI_REMOTE_UPSERT_MINUTES_NOTE)


@pytest.fixture
def sli_remote_upsert_dx_cpt():
    return load_fixture(SLI_REMOTE_UPSERT_DX_CPT)


@pytest.fixture
def sli_remote_upsert_clear_and_complete():
    return load_fixture(SLI_REMOTE_UPSERT_CLEAR_AND_COMPLETE)


# --- POST /cases/schedules ---


def test_post_schedules_initial_insert_returns_unique_create_case_ids(
    client, sli_remote_initial_insert
):
    response = client.post("/cases/schedules", json=sli_remote_initial_insert)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"inserted"}
    inserted = body["inserted"]
    assert len(inserted) == len(sli_remote_initial_insert["rows"])
    assert len(inserted) == len(set(inserted))
    assert set(inserted) == expected_case_ids(sli_remote_initial_insert)


def test_post_schedules_initial_insert_idempotent(client, sli_remote_initial_insert):
    first = client.post("/cases/schedules", json=sli_remote_initial_insert)
    second = client.post("/cases/schedules", json=sli_remote_initial_insert)
    assert first.status_code == 200
    assert second.status_code == 200
    assert set(first.json()["inserted"]) == expected_case_ids(sli_remote_initial_insert)
    assert second.json() == {"inserted": []}
    assert {c["case_id"] for c in client.get("/cases/schedules").json()} == set(
        first.json()["inserted"]
    )


def test_post_schedules_upsert_fixture_inserts_only(client, sli_remote_upsert_dx_cpt):
    response = client.post("/cases/schedules", json=sli_remote_upsert_dx_cpt)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"inserted"}
    assert "updated" not in body
    assert len(body["inserted"]) == len(sli_remote_upsert_dx_cpt["rows"])
    assert set(body["inserted"]) == expected_case_ids(sli_remote_upsert_dx_cpt)


@pytest.mark.parametrize(
    "fixture_name",
    (SLI_REMOTE_UPSERT_MINUTES_NOTE, SLI_REMOTE_UPSERT_CLEAR_AND_COMPLETE),
)
def test_post_schedules_without_diagnosis_returns_422_without_partial_insert(
    client, fixture_name
):
    """POST rejects rows without diagnosis before writing patients or cases."""
    payload = load_fixture(fixture_name)
    response = client.post("/cases/schedules", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "Invalid schedule input"
    assert response.json()["detail"]["rows"]
    assert client.get("/cases/schedules").json() == []
    patients = client.app.state.db._cursor().execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]
    assert patients == 0


@pytest.mark.parametrize("fixture_name", (SLI_REMOTE_UPSERT_DX_CPT,))
def test_post_schedules_upsert_fixture_does_not_update_existing(
    client, sli_remote_initial_insert, fixture_name
):
    assert client.post("/cases/schedules", json=sli_remote_initial_insert).status_code == 200
    before = {c["case_id"]: c for c in client.get("/cases/schedules").json()}

    payload = load_fixture(fixture_name)
    response = client.post("/cases/schedules", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"inserted"}
    assert body["inserted"] == []

    after = {c["case_id"]: c for c in client.get("/cases/schedules").json()}
    for case_id in expected_case_ids(payload):
        assert after[case_id] == before[case_id]


# --- GET /cases/schedules ---


def test_get_schedules_after_post(client, sli_remote_initial_insert):
    post = client.post("/cases/schedules", json=sli_remote_initial_insert)
    assert post.status_code == 200

    response = client.get("/cases/schedules")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == len(sli_remote_initial_insert["rows"])
    assert all(case["status"] == "scheduled" for case in cases)
    assert {case["case_id"] for case in cases} == set(post.json()["inserted"])
    by_patient = {c["patient_id"]: c for c in cases}
    assert by_patient["90001"]["patient_name"] == "Avery Sample"
    assert by_patient["90001"]["diagnosis"] == "H25.11"
    assert by_patient["90001"]["eye"] == "R"
    assert by_patient["90001"]["case_position"] == 1


def test_get_schedules_empty(client):
    response = client.get("/cases/schedules")
    assert response.status_code == 200
    assert response.json() == []


def test_get_schedules_matches_db_query(client, sli_remote_initial_insert):
    """Router GET must return the same rows CasesDB.query_cases would."""
    assert client.post("/cases/schedules", json=sli_remote_initial_insert).status_code == 200

    via_router = client.get("/cases/schedules").json()
    via_db = [
        row.model_dump(mode="json")
        for row in client.app.state.db.query_cases(status=["scheduled"])
    ]
    via_db.sort(key=lambda x: x.get("case_position") or 0)

    assert via_router == via_db


# --- PATCH /cases/schedules ---


def test_patch_schedules_upsert_minutes_note(
    client, sli_remote_initial_insert, sli_remote_upsert_minutes_note
):
    assert client.post("/cases/schedules", json=sli_remote_initial_insert).status_code == 200

    response = client.patch("/cases/schedules", json=sli_remote_upsert_minutes_note)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"updated", "inserted"}
    assert set(body["updated"]) == expected_case_ids(sli_remote_upsert_minutes_note)
    assert body["inserted"] == []

    case = next(c for c in client.get("/cases/schedules").json() if c["patient_id"] == "90001")
    assert case["minutes"] == 22
    assert case["note"] == "Awaiting final diagnosis confirmation."


def test_patch_schedules_upsert_dx_cpt(
    client, sli_remote_initial_insert, sli_remote_upsert_dx_cpt
):
    assert client.post("/cases/schedules", json=sli_remote_initial_insert).status_code == 200

    response = client.patch("/cases/schedules", json=sli_remote_upsert_dx_cpt)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"updated", "inserted"}
    assert set(body["updated"]) == expected_case_ids(sli_remote_upsert_dx_cpt)
    assert body["inserted"] == []

    case = next(c for c in client.get("/cases/schedules").json() if c["patient_id"] == "90002")
    assert case["diagnosis"] == "H25.12"
    assert case["cpt"] == "00142"


def test_patch_schedules_upsert_clear_and_complete(
    client, sli_remote_initial_insert, sli_remote_upsert_clear_and_complete
):
    assert client.post("/cases/schedules", json=sli_remote_initial_insert).status_code == 200

    response = client.patch("/cases/schedules", json=sli_remote_upsert_clear_and_complete)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"updated", "inserted"}
    assert set(body["updated"]) == expected_case_ids(sli_remote_upsert_clear_and_complete)
    assert body["inserted"] == []

    case = next(c for c in client.get("/cases/schedules").json() if c["patient_id"] == "90003")
    assert case["minutes"] == 31
    assert case["status"] == "scheduled"


# --- POST /cases/billables ---


def test_post_billables_returns_ids(
    client, billable_sending, expected_billable_sending_response
):
    seeded = client.post(
        "/cases/schedules", json=schedules_seed_from_billables(billable_sending)
    )
    assert seeded.status_code == 200

    response = client.post("/cases/billables", json=billable_sending)
    assert response.status_code == 200
    assert set(response.json()["updated"]) == set(expected_billable_sending_response)


def test_post_billables_minimal(client, billable_sending_minimal):
    seeded = client.post(
        "/cases/schedules", json=schedules_seed_from_billables(billable_sending_minimal)
    )
    assert seeded.status_code == 200

    response = client.post("/cases/billables", json=billable_sending_minimal)
    assert response.status_code == 200
    assert response.json()["updated"] == ["45bf8828-3100-5e56-8c5c-175dad7635bb"]


def test_billables_null_notes_do_not_corrupt_storage(client, billable_sending):
    """Mixed null/string notes must not write NaN or break GET /billables."""
    payload = []
    for case in billable_sending:
        row = {**case}
        if case["status"] != "skipped":
            row["note"] = None
        payload.append(row)

    assert (
        client.post(
            "/cases/schedules", json=schedules_seed_from_billables(billable_sending)
        ).status_code
        == 200
    )
    assert client.post("/cases/billables", json=payload).status_code == 200

    response = client.get("/cases/billables")
    assert response.status_code == 200
    by_id = {c["case_id"]: c for c in response.json()}
    for case in payload:
        stored = by_id[case["case_id"]]
        if case["status"] == "skipped":
            assert stored["note"] == case["note"]
        else:
            assert stored.get("note") in (None, "")


# --- GET /cases/billables ---


def test_get_billables_after_post(client, billable_sending):
    assert (
        client.post(
            "/cases/schedules", json=schedules_seed_from_billables(billable_sending)
        ).status_code
        == 200
    )
    assert client.post("/cases/billables", json=billable_sending).status_code == 200

    response = client.get("/cases/billables")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(billable_sending)
    statuses = {case["status"] for case in body}
    assert statuses == {"billable", "mission", "cancelled", "skipped"}


def test_get_billables_matches_db_query(client, billable_sending):
    """Router GET must return the same rows CasesDB.query_cases would."""
    assert (
        client.post(
            "/cases/schedules", json=schedules_seed_from_billables(billable_sending)
        ).status_code
        == 200
    )
    assert client.post("/cases/billables", json=billable_sending).status_code == 200

    via_router = client.get("/cases/billables").json()
    via_db = [
        row.model_dump(mode="json")
        for row in client.app.state.db.query_cases(
            status=["billable", "mission", "cancelled", "skipped"]
        )
    ]

    assert via_router == via_db


def test_get_schedules_excludes_terminal_after_billables(client, billable_sending):
    assert (
        client.post(
            "/cases/schedules", json=schedules_seed_from_billables(billable_sending)
        ).status_code
        == 200
    )
    assert client.post("/cases/billables", json=billable_sending).status_code == 200

    scheduled = client.get("/cases/schedules").json()
    billed_ids = {case["case_id"] for case in billable_sending}
    remaining_ids = {case["case_id"] for case in scheduled}
    assert remaining_ids.isdisjoint(billed_ids)
    assert len(scheduled) == 0


# --- End-to-end ---


def test_end_to_end_schedule_then_bill(
    client, billable_sending, expected_billable_sending_response
):
    seed = schedules_seed_from_billables(billable_sending)
    schedule_resp = client.post("/cases/schedules", json=seed)
    assert schedule_resp.status_code == 200
    assert set(schedule_resp.json()["inserted"]) == expected_case_ids(seed)

    before = client.get("/cases/schedules").json()
    assert len(before) == len(billable_sending)

    bill_resp = client.post("/cases/billables", json=billable_sending)
    assert bill_resp.status_code == 200
    assert set(bill_resp.json()["updated"]) == set(expected_billable_sending_response)

    after = client.get("/cases/schedules").json()
    assert len(after) == 0

    billables = client.get("/cases/billables").json()
    assert len(billables) == len(billable_sending)
