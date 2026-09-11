# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

from collections.abc import AsyncIterator

from app.clients.github_client import GitHubClient
from app.config import get_settings


async def get_github_client() -> AsyncIterator[GitHubClient]:
    client = GitHubClient(get_settings())
    try:
        yield client
    finally:
        await client.close()
