"""Load API test fixtures derived from app/mock data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent


def load_fixture(name: str) -> Any:
    path = FIXTURES_DIR / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


SCHEDULE_RECEIVING = "schedule-receiving.json"
SCHEDULE_RECEIVING_MINIMAL = "schedule-receiving-minimal.json"
SCHEDULE_RECEIVING_PENDING_ONLY = "schedule-receiving-pending-only.json"
SCHEDULE_RECEIVING_BUSY = "schedule-receiving-busy.json"
BILLABLE_SENDING = "billable-sending.json"
BILLABLE_SENDING_MINIMAL = "billable-sending-minimal.json"
EXPECTED_SCHEDULE_RECEIVING_RESPONSE = "expected-schedule-receiving-response.json"
EXPECTED_BILLABLE_SENDING_RESPONSE = "expected-billable-sending-response.json"
