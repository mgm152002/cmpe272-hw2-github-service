# Team member: Prajval Sudhir (@prajvalsudhir)

import httpx
import pytest
from fastapi import HTTPException

from app.clients.github_client import GitHubClient
from app.config import Settings


def settings() -> Settings:
    return Settings(
        GITHUB_TOKEN="test-token",
        GITHUB_OWNER="test-owner",
        GITHUB_REPO="test-repo",
        WEBHOOK_SECRET="test-secret",
    )


@pytest.mark.asyncio
async def test_get_retries_transient_server_failures() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, json={"message": "try again"})
        return httpx.Response(200, json={"ok": True})

    client = GitHubClient(settings(), transport=httpx.MockTransport(handler))
    try:
        response = await client.request("GET", "/issues")
    finally:
        await client.close()

    assert attempts == 3
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_get_timeout_becomes_503_after_three_attempts() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timed out", request=request)

    client = GitHubClient(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(HTTPException) as caught:
            await client.request("GET", "/issues")
    finally:
        await client.close()

    assert attempts == 3
    assert caught.value.status_code == 503
    assert caught.value.detail["code"] == "GITHUB_UNAVAILABLE"


@pytest.mark.asyncio
async def test_post_is_not_retried() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"message": "unavailable"})

    client = GitHubClient(settings(), transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(HTTPException) as caught:
            await client.request("POST", "/issues", json={"title": "test"})
    finally:
        await client.close()

    assert attempts == 1
    assert caught.value.status_code == 503
