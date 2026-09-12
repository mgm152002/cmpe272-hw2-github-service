# Team member: Vinayak Shivam Gupta (@vsh2504)

from fastapi.testclient import TestClient

from app.main import app


def test_missing_issue_title_returns_standard_400() -> None:
    with TestClient(app) as client:
        response = client.post("/issues", json={})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert response.json()["error"]["details"][0]["loc"] == ["body", "title"]


def test_invalid_webhook_signature_uses_error_envelope() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/webhook",
            content=b"{}",
            headers={
                "X-Hub-Signature-256": "sha256=bad",
                "X-GitHub-Event": "ping",
                "X-GitHub-Delivery": "d-1",
            },
        )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "INVALID_SIGNATURE",
            "message": "Invalid signature",
            "details": {},
        }
    }
