# Team member: Prajval Sudhir (@prajvalsudhir)

import asyncio
from typing import Any

import httpx
from fastapi import HTTPException

from app.config import Settings
from app.utils.error_mapping import raise_for_github_error


class GitHubClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            transport=transport,
            timeout=10,
        )

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        normalized_method = method.upper()
        for attempt in range(3):
            try:
                response = await self.client.request(
                    normalized_method, self.base_url + path, **kwargs
                )
            except httpx.TransportError as exc:
                if normalized_method == "GET" and attempt < 2:
                    await asyncio.sleep(0.05 * (2**attempt))
                    continue
                raise HTTPException(
                    503,
                    detail={
                        "code": "GITHUB_UNAVAILABLE",
                        "message": "GitHub request failed",
                        "details": {},
                    },
                ) from exc
            if normalized_method == "GET" and response.status_code >= 500 and attempt < 2:
                await asyncio.sleep(0.05 * (2**attempt))
                continue
            raise_for_github_error(response)
            return response
        raise RuntimeError("unreachable")

    async def close(self) -> None:
        await self.client.aclose()
