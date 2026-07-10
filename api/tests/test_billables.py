"""Billable endpoint tests."""


def test_post_billables_returns_ids(
    client, schedule_receiving, billable_sending, expected_billable_sending_response
):
    seeded = client.post("/cases/schedules", json=schedule_receiving)
    assert seeded.status_code == 200

    response = client.post("/cases/billables", json=billable_sending)
    assert response.status_code == 200
    assert set(response.json()) == set(expected_billable_sending_response)


def test_post_billables_minimal(client, schedule_receiving_minimal, billable_sending_minimal):
    seeded = client.post("/cases/schedules", json=schedule_receiving_minimal)
    assert seeded.status_code == 200

    response = client.post("/cases/billables", json=billable_sending_minimal)
    assert response.status_code == 200
    assert response.json() == ["0d9153e1-3a55-599a-84cb-d91dd9227a71"]


def test_get_billables_after_post(client, schedule_receiving, billable_sending):
    assert client.post("/cases/schedules", json=schedule_receiving).status_code == 200
    assert client.post("/cases/billables", json=billable_sending).status_code == 200

    response = client.get("/cases/billables")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(billable_sending)
    statuses = {case["status"] for case in body}
    assert statuses == {"billable", "mission", "cancelled", "issue"}


def test_billables_null_notes_do_not_corrupt_storage(
    client, schedule_receiving, billable_sending
):
    """Mixed null/string notes must not write NaN or break GET /billables."""
    payload = []
    for case in billable_sending:
        row = {**case}
        if case["status"] != "issue":
            row["note"] = None
        payload.append(row)

    assert client.post("/cases/schedules", json=schedule_receiving).status_code == 200
    assert client.post("/cases/billables", json=payload).status_code == 200

    response = client.get("/cases/billables")
    assert response.status_code == 200
    by_id = {c["case_id"]: c for c in response.json()}
    for case in payload:
        stored = by_id[case["case_id"]]
        if case["status"] == "issue":
            assert stored["note"] == case["note"]
        else:
            assert stored.get("note") in (None, "")


def test_get_schedules_excludes_terminal_after_billables(
    client, schedule_receiving, billable_sending
):
    assert client.post("/cases/schedules", json=schedule_receiving).status_code == 200
    assert client.post("/cases/billables", json=billable_sending).status_code == 200

    scheduled = client.get("/cases/schedules").json()
    billed_ids = {case["case_id"] for case in billable_sending}
    remaining_ids = {case["case_id"] for case in scheduled}
    assert remaining_ids.isdisjoint(billed_ids)
    assert len(scheduled) == 2


def test_end_to_end_schedule_then_bill(
    client,
    schedule_receiving,
    billable_sending,
    expected_schedule_receiving_response,
    expected_billable_sending_response,
):
    schedule_resp = client.post("/cases/schedules", json=schedule_receiving)
    assert schedule_resp.status_code == 200
    assert set(schedule_resp.json()) == set(expected_schedule_receiving_response)

    before = client.get("/cases/schedules").json()
    assert len(before) == 8

    bill_resp = client.post("/cases/billables", json=billable_sending)
    assert bill_resp.status_code == 200
    assert set(bill_resp.json()) == set(expected_billable_sending_response)

    after = client.get("/cases/schedules").json()
    assert len(after) == 2

    billables = client.get("/cases/billables").json()
    assert len(billables) == 6
