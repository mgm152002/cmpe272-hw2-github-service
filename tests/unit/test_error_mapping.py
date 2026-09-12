# Team member: Prajval Sudhir (@prajvalsudhir)

import httpx
import pytest
from fastapi import HTTPException

from app.utils.error_mapping import raise_for_github_error


@pytest.mark.parametrize(
    ("github_status", "expected_status", "expected_code"),
    [
        (400, 400, "GITHUB_BAD_REQUEST"),
        (401, 401, "GITHUB_UNAUTHORIZED"),
        (403, 403, "GITHUB_FORBIDDEN"),
        (404, 404, "ISSUE_NOT_FOUND"),
        (422, 400, "GITHUB_VALIDATION_FAILED"),
        (500, 503, "GITHUB_UNAVAILABLE"),
    ],
)
def test_maps_github_statuses(
    github_status: int, expected_status: int, expected_code: str
) -> None:
    response = httpx.Response(github_status, json={"message": "upstream message"})

    with pytest.raises(HTTPException) as caught:
        raise_for_github_error(response)

    assert caught.value.status_code == expected_status
    assert caught.value.detail == {
        "code": expected_code,
        "message": "upstream message",
        "details": {},
    }


def test_rate_limit_adds_retry_after_header() -> None:
    response = httpx.Response(
        403,
        json={"message": "rate limited"},
        headers={"x-ratelimit-remaining": "0", "retry-after": "30"},
    )

    with pytest.raises(HTTPException) as caught:
        raise_for_github_error(response)

    assert caught.value.status_code == 429
    assert caught.value.detail["code"] == "RATE_LIMITED"
    assert caught.value.headers == {"Retry-After": "30"}


@pytest.mark.parametrize(
    ("status", "headers"),
    [
        (403, {"retry-after": "15"}),
        (429, {"retry-after": "20"}),
    ],
)
def test_secondary_and_explicit_rate_limits_return_429(
    status: int, headers: dict[str, str]
) -> None:
    response = httpx.Response(status, json={"message": "slow down"}, headers=headers)

    with pytest.raises(HTTPException) as caught:
        raise_for_github_error(response)

    assert caught.value.status_code == 429
    assert caught.value.detail["code"] == "RATE_LIMITED"
    assert caught.value.headers == {"Retry-After": headers["retry-after"]}


def test_malformed_upstream_error_body_is_safe() -> None:
    response = httpx.Response(502, content=b"not-json")

    with pytest.raises(HTTPException) as caught:
        raise_for_github_error(response)

    assert caught.value.status_code == 503
    assert caught.value.detail["message"] == "GitHub request failed"
