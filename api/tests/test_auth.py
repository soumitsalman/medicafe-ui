"""API key middleware tests."""


def test_health_skips_api_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-key")

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_api_key_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-key")

    response = client.get("/cases/schedules")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_wrong_api_key_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-key")

    response = client.get(
        "/cases/schedules",
        headers={"X-API-KEY": "wrong-key"},
    )
    assert response.status_code == 401


def test_valid_api_key_allows_request(client, monkeypatch, schedule_receiving):
    monkeypatch.setenv("API_KEY", "secret-key")
    headers = {"X-API-KEY": "secret-key"}

    post = client.post("/cases/schedules", json=schedule_receiving, headers=headers)
    assert post.status_code == 200

    get = client.get("/cases/schedules", headers=headers)
    assert get.status_code == 200
    assert len(get.json()) == 8
