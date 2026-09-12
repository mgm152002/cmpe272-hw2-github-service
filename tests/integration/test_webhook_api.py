# Team member: Vinayak Shivam Gupta (@vsh2504)

import hashlib
import hmac
import logging
import sqlite3
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.event_repository import EventRepository


def signature(body: bytes, secret: str = "test-secret") -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def headers(body: bytes, *, event: str = "issues", delivery: str = "delivery-1") -> dict[str, str]:
    return {
        "X-Hub-Signature-256": signature(body),
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": delivery,
        "X-Request-ID": "request-1",
    }


@pytest.fixture
def webhook_client() -> Iterator[TestClient]:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE events (
        delivery_id TEXT NOT NULL,
        action TEXT NOT NULL,
        event TEXT NOT NULL,
        issue_number INTEGER,
        timestamp TEXT NOT NULL,
        PRIMARY KEY (delivery_id, action)
        )"""
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        app.state.events = EventRepository(connection)
        yield client
    connection.close()


def test_valid_and_duplicate_webhook_is_stored_once(
    webhook_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    body = b'{"action":"opened","issue":{"number":7}}'
    logger = logging.getLogger("app.api.webhooks")
    logger.addHandler(caplog.handler)

    try:
        first = webhook_client.post("/webhook", content=body, headers=headers(body))
        duplicate = webhook_client.post("/webhook", content=body, headers=headers(body))
    finally:
        logger.removeHandler(caplog.handler)
    events = webhook_client.get("/events?limit=20")

    assert first.status_code == 204
    assert duplicate.status_code == 204
    assert events.status_code == 200
    assert len(events.json()) == 1
    records = [record for record in caplog.records if hasattr(record, "event_data")]
    assert [record.event_data["stored"] for record in records] == [True, False]
    assert records[0].event_data["request_id"] == "request-1"
    assert records[0].event_data["delivery_id"] == "delivery-1"
    assert "test-secret" not in caplog.text
    assert headers(body)["X-Hub-Signature-256"] not in caplog.text


@pytest.mark.parametrize(
    ("body", "header_overrides", "expected_status", "expected_code"),
    [
        (b"{}", {"X-Hub-Signature-256": "sha256=bad"}, 401, "INVALID_SIGNATURE"),
        (b"not-json", {}, 400, "INVALID_JSON"),
        (b"[]", {}, 400, "INVALID_JSON"),
        (b'{"action":"invented"}', {}, 400, "UNSUPPORTED_EVENT"),
    ],
)
def test_rejects_invalid_webhooks(
    webhook_client: TestClient,
    body: bytes,
    header_overrides: dict[str, str],
    expected_status: int,
    expected_code: str,
) -> None:
    request_headers = headers(body)
    request_headers.update(header_overrides)

    response = webhook_client.post("/webhook", content=body, headers=request_headers)

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code


def test_accepts_signed_ping(webhook_client: TestClient) -> None:
    body = b"{}"

    response = webhook_client.post("/webhook", content=body, headers=headers(body, event="ping"))

    assert response.status_code == 204


def test_rejects_missing_signature(webhook_client: TestClient) -> None:
    body = b"{}"
    request_headers = headers(body)
    request_headers.pop("X-Hub-Signature-256")

    response = webhook_client.post("/webhook", content=body, headers=request_headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_SIGNATURE"
