# Team member: Prajval Sudhir (@prajvalsudhir)

import math
import time

from fastapi import HTTPException
from httpx import Response

STATUS_MAP = {
    400: (400, "GITHUB_BAD_REQUEST"),
    401: (401, "GITHUB_UNAUTHORIZED"),
    403: (403, "GITHUB_FORBIDDEN"),
    404: (404, "ISSUE_NOT_FOUND"),
    422: (400, "GITHUB_VALIDATION_FAILED"),
}


def _error_body(response: Response) -> tuple[str, object]:
    try:
        body = response.json()
    except ValueError:
        return "GitHub request failed", {}
    if not isinstance(body, dict):
        return "GitHub request failed", {}
    return str(body.get("message", "GitHub request failed")), body.get("errors", {})


def _retry_after(response: Response) -> str:
    if value := response.headers.get("retry-after"):
        return value
    if reset := response.headers.get("x-ratelimit-reset"):
        try:
            return str(max(1, math.ceil(float(reset) - time.time())))
        except ValueError:
            pass
    return "60"


def raise_for_github_error(response: Response) -> None:
    if response.is_success:
        return
    message, details = _error_body(response)
    status = response.status_code
    is_rate_limited = status == 429 or (
        status == 403
        and (
            response.headers.get("x-ratelimit-remaining") == "0"
            or "retry-after" in response.headers
        )
    )
    if is_rate_limited:
        raise HTTPException(
            429,
            detail={"code": "RATE_LIMITED", "message": message, "details": details},
            headers={"Retry-After": _retry_after(response)},
        )
    mapped_status, code = STATUS_MAP.get(status, (503, "GITHUB_UNAVAILABLE"))
    raise HTTPException(
        mapped_status,
        detail={"code": code, "message": message, "details": details},
    )
