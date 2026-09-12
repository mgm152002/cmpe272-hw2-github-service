# Team member: Vinayak Shivam Gupta (@vsh2504)

import logging

from fastapi.testclient import TestClient

from app.logging_config import JsonFormatter
from app.main import app
from app.middleware import request_context


def test_echoes_supplied_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Request-ID": "request-123"})

    assert response.headers["x-request-id"] == "request-123"


def test_generates_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.headers["x-request-id"]


def test_exposes_request_id_context_variable() -> None:
    assert hasattr(request_context, "request_id_context")


def test_application_logger_uses_json_formatter() -> None:
    assert any(
        isinstance(handler.formatter, JsonFormatter)
        for handler in logging.getLogger("app").handlers
    )


def test_request_log_contains_request_id(caplog) -> None:
    logger = logging.getLogger("app.middleware.request_context")
    logger.addHandler(caplog.handler)
    try:
        with TestClient(app) as client:
            client.get("/healthz", headers={"X-Request-ID": "request-log-1"})
    finally:
        logger.removeHandler(caplog.handler)

    records = [record for record in caplog.records if hasattr(record, "event_data")]
    assert records[-1].event_data["request_id"] == "request-log-1"
    assert records[-1].event_data["method"] == "GET"
    assert records[-1].event_data["path"] == "/healthz"
    assert records[-1].event_data["status_code"] == 200
