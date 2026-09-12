# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

import json
from typing import Any

import httpx
import respx
from fastapi.testclient import TestClient

GITHUB_BASE = "https://api.github.com/repos/test-owner/test-repo"


def test_create_then_get_issue(
    client: TestClient, respx_mock: respx.MockRouter, issue_json: dict[str, Any]
) -> None:
    create = respx_mock.post(f"{GITHUB_BASE}/issues").mock(
        return_value=httpx.Response(201, json=issue_json)
    )
    get = respx_mock.get(f"{GITHUB_BASE}/issues/1").mock(
        return_value=httpx.Response(200, json=issue_json)
    )

    created = client.post(
        "/issues", json={"title": "Created", "body": "Initial body", "labels": ["test"]}
    )
    fetched = client.get("/issues/1")

    assert created.status_code == 201
    assert created.headers["location"] == "/issues/1"
    assert created.json()["title"] == "Created"
    assert fetched.status_code == 200
    assert fetched.json()["number"] == 1
    assert json.loads(create.calls[0].request.content) == {
        "title": "Created",
        "body": "Initial body",
        "labels": ["test"],
    }
    assert create.called and get.called


def test_update_close_and_reopen_issue(
    client: TestClient, respx_mock: respx.MockRouter, issue_json: dict[str, Any]
) -> None:
    updated = {**issue_json, "title": "Updated", "body": "Updated body"}
    closed = {**updated, "state": "closed"}
    reopened = {**updated, "state": "open"}
    route = respx_mock.patch(f"{GITHUB_BASE}/issues/1").mock(
        side_effect=[
            httpx.Response(200, json=updated),
            httpx.Response(200, json=closed),
            httpx.Response(200, json=reopened),
        ]
    )

    responses = [
        client.patch("/issues/1", json={"title": "Updated", "body": "Updated body"}),
        client.patch("/issues/1", json={"state": "closed"}),
        client.patch("/issues/1", json={"state": "open"}),
    ]

    assert [response.status_code for response in responses] == [200, 200, 200]
    assert [response.json()["state"] for response in responses] == ["open", "closed", "open"]
    assert [json.loads(call.request.content) for call in route.calls] == [
        {"title": "Updated", "body": "Updated body"},
        {"state": "closed"},
        {"state": "open"},
    ]


def test_list_issues_forwards_query_and_link(
    client: TestClient, respx_mock: respx.MockRouter, issue_json: dict[str, Any]
) -> None:
    pull_request = {**issue_json, "number": 2, "pull_request": {"url": "https://example.test"}}
    link = '<https://api.github.com/issues?page=2>; rel="next"'
    route = respx_mock.get(f"{GITHUB_BASE}/issues").mock(
        return_value=httpx.Response(200, json=[issue_json, pull_request], headers={"Link": link})
    )

    response = client.get("/issues?state=all&labels=test&page=2&per_page=50")

    assert response.status_code == 200
    assert [item["number"] for item in response.json()] == [1]
    assert response.headers["link"] == link
    assert dict(route.calls[0].request.url.params) == {
        "state": "all",
        "labels": "test",
        "page": "2",
        "per_page": "50",
    }


def test_create_then_list_comments(
    client: TestClient, respx_mock: respx.MockRouter, comment_json: dict[str, Any]
) -> None:
    create = respx_mock.post(f"{GITHUB_BASE}/issues/1/comments").mock(
        return_value=httpx.Response(201, json=comment_json)
    )
    link = '<https://api.github.com/comments?page=2>; rel="next"'
    list_route = respx_mock.get(f"{GITHUB_BASE}/issues/1/comments").mock(
        return_value=httpx.Response(200, json=[comment_json], headers={"Link": link})
    )

    created = client.post("/issues/1/comments", json={"body": "hello"})
    listed = client.get("/issues/1/comments?page=1&per_page=30")

    assert created.status_code == 201
    assert created.json()["id"] == 100
    assert json.loads(create.calls[0].request.content) == {"body": "hello"}
    assert listed.status_code == 200
    assert listed.json()[0]["body"] == "hello"
    assert listed.headers["link"] == link
    assert dict(list_route.calls[0].request.url.params) == {"page": "1", "per_page": "30"}


def test_issue_number_must_be_positive(client: TestClient, respx_mock: respx.MockRouter) -> None:
    response = client.get("/issues/0")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert not respx_mock.calls.called


def test_pagination_bounds_return_400(client: TestClient, respx_mock: respx.MockRouter) -> None:
    response = client.get("/issues?per_page=101")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert not respx_mock.calls.called


def test_invalid_update_state_returns_400(
    client: TestClient, respx_mock: respx.MockRouter
) -> None:
    response = client.patch("/issues/1", json={"state": "deleted"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert not respx_mock.calls.called


def test_rejects_undocumented_request_fields(
    client: TestClient, respx_mock: respx.MockRouter
) -> None:
    response = client.post("/issues", json={"title": "test", "unexpected": True})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert not respx_mock.calls.called
