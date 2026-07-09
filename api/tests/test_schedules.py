"""Schedule endpoint tests."""


def test_post_schedules_returns_expected_ids(
    client, schedule_receiving, expected_schedule_receiving_response
):
    response = client.post("/cases/schedules", json=schedule_receiving)
    assert response.status_code == 200
    assert set(response.json()["scheduled"]) == set(
        expected_schedule_receiving_response["scheduled"]
    )


def test_post_schedules_minimal(client, schedule_receiving_minimal):
    response = client.post("/cases/schedules", json=schedule_receiving_minimal)
    assert response.status_code == 200
    body = response.json()
    assert "scheduled" in body
    assert len(body["scheduled"]) == 1
    assert body["scheduled"][0] == "a334ad13-d199-5585-bbe4-0accd3da64b9"


def test_post_schedules_pending_only(client, schedule_receiving_pending_only):
    response = client.post("/cases/schedules", json=schedule_receiving_pending_only)
    assert response.status_code == 200
    body = response.json()
    assert len(body["scheduled"]) == len(schedule_receiving_pending_only["cases"])


def test_post_schedules_busy(client, schedule_receiving_busy):
    response = client.post("/cases/schedules", json=schedule_receiving_busy)
    assert response.status_code == 200
    body = response.json()
    assert len(body["scheduled"]) == len(schedule_receiving_busy["cases"])


def test_post_schedules_idempotent(client, schedule_receiving):
    first = client.post("/cases/schedules", json=schedule_receiving)
    second = client.post("/cases/schedules", json=schedule_receiving)
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(first.json()["scheduled"]) == 8
    assert second.json()["scheduled"] == []


def test_get_schedules_after_post(client, schedule_receiving):
    post = client.post("/cases/schedules", json=schedule_receiving)
    assert post.status_code == 200

    response = client.get("/cases/schedules")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 8
    assert all(case["status"] == "scheduled" for case in cases)
    assert {case["case_id"] for case in cases} == set(post.json()["scheduled"])


def test_get_schedules_empty(client):
    response = client.get("/cases/schedules")
    assert response.status_code == 200
    assert response.json() == []
