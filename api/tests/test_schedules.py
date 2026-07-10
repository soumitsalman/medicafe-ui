"""Schedule endpoint tests."""

from fixtures import schedule_patient_count


def test_post_schedules_returns_expected_ids(
    client, schedule_receiving, expected_schedule_receiving_response
):
    response = client.post("/cases/schedules", json=schedule_receiving)
    assert response.status_code == 200
    assert set(response.json()) == set(expected_schedule_receiving_response)


def test_post_schedules_minimal(client, schedule_receiving_minimal):
    response = client.post("/cases/schedules", json=schedule_receiving_minimal)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0] == "31388fc7-1bde-57ce-8428-01f6a446b990"


def test_post_schedules_pending_only(client, schedule_receiving_pending_only):
    response = client.post("/cases/schedules", json=schedule_receiving_pending_only)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == schedule_patient_count(schedule_receiving_pending_only)


def test_post_schedules_busy(client, schedule_receiving_busy):
    response = client.post("/cases/schedules", json=schedule_receiving_busy)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == schedule_patient_count(schedule_receiving_busy)


def test_post_schedules_idempotent(client, schedule_receiving):
    first = client.post("/cases/schedules", json=schedule_receiving)
    second = client.post("/cases/schedules", json=schedule_receiving)
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(first.json()) == 8
    assert set(second.json()) == set(first.json())


def test_get_schedules_after_post(client, schedule_receiving):
    post = client.post("/cases/schedules", json=schedule_receiving)
    assert post.status_code == 200

    response = client.get("/cases/schedules")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 8
    assert all(case["status"] == "scheduled" for case in cases)
    assert {case["case_id"] for case in cases} == set(post.json())


def test_get_schedules_empty(client):
    response = client.get("/cases/schedules")
    assert response.status_code == 200
    assert response.json() == []


def test_patch_schedules_updates_cpt(client, schedule_receiving, schedule_updating):
    assert client.post("/cases/schedules", json=schedule_receiving).status_code == 200

    response = client.patch("/cases/schedules", json=schedule_updating)
    assert response.status_code == 200
    assert len(response.json()) == len(schedule_updating["rows"])

    cases = {c["patient_id"]: c for c in client.get("/cases/schedules").json()}
    assert cases["12345"]["cpt"] == "00142"
    assert cases["12345"]["case_position"] == 1
    assert cases["55667"]["cpt"] == "00140"


def test_patch_schedules_minimal(
    client, schedule_receiving_minimal, schedule_updating_minimal
):
    assert client.post("/cases/schedules", json=schedule_receiving_minimal).status_code == 200

    response = client.patch("/cases/schedules", json=schedule_updating_minimal)
    assert response.status_code == 200
    assert response.json() == ["31388fc7-1bde-57ce-8428-01f6a446b990"]

    case = client.get("/cases/schedules").json()[0]
    assert case["cpt"] == "00142"
    assert case["diagnosis"] == "H25.812"
