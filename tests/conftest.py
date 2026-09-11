# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("GITHUB_OWNER", "test-owner")
os.environ.setdefault("GITHUB_REPO", "test-repo")
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("PORT", "8000")

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def issue_json() -> dict[str, Any]:
    timestamp = datetime(2026, 9, 13, tzinfo=UTC).isoformat()
    return {
        "number": 1,
        "html_url": "https://github.com/test-owner/test-repo/issues/1",
        "state": "open",
        "title": "Created",
        "body": "Initial body",
        "labels": [{"name": "test"}],
        "created_at": timestamp,
        "updated_at": timestamp,
    }


@pytest.fixture
def comment_json() -> dict[str, Any]:
    return {
        "id": 100,
        "body": "hello",
        "user": {"login": "test-user"},
        "created_at": datetime(2026, 9, 13, tzinfo=UTC).isoformat(),
        "html_url": "https://github.com/test-owner/test-repo/issues/1#issuecomment-100",
    }
