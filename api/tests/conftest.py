"""Pytest fixtures for Medicafe API tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from fixtures import (  # noqa: E402
    BILLABLE_SENDING,
    BILLABLE_SENDING_MINIMAL,
    EXPECTED_BILLABLE_SENDING_RESPONSE,
    EXPECTED_SCHEDULE_RECEIVING_RESPONSE,
    SCHEDULE_RECEIVING,
    SCHEDULE_RECEIVING_BUSY,
    SCHEDULE_RECEIVING_MINIMAL,
    SCHEDULE_RECEIVING_PENDING_ONLY,
    load_fixture,
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CASES_DB_PATH", str(tmp_path / "cases.duckdb"))
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("CASES_DB_API_KEY", raising=False)
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def schedule_receiving():
    return load_fixture(SCHEDULE_RECEIVING)


@pytest.fixture
def schedule_receiving_minimal():
    return load_fixture(SCHEDULE_RECEIVING_MINIMAL)


@pytest.fixture
def schedule_receiving_pending_only():
    return load_fixture(SCHEDULE_RECEIVING_PENDING_ONLY)


@pytest.fixture
def schedule_receiving_busy():
    return load_fixture(SCHEDULE_RECEIVING_BUSY)


@pytest.fixture
def billable_sending():
    return load_fixture(BILLABLE_SENDING)


@pytest.fixture
def billable_sending_minimal():
    return load_fixture(BILLABLE_SENDING_MINIMAL)


@pytest.fixture
def expected_schedule_receiving_response():
    return load_fixture(EXPECTED_SCHEDULE_RECEIVING_RESPONSE)


@pytest.fixture
def expected_billable_sending_response():
    return load_fixture(EXPECTED_BILLABLE_SENDING_RESPONSE)
