# Team member: Prajval Sudhir (@prajvalsudhir)

from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture(scope="module")
def contract() -> dict[str, Any]:
    return yaml.safe_load(Path("openapi.yaml").read_text())


def test_contract_is_openapi_31(contract: dict[str, Any]) -> None:
    assert contract["openapi"].startswith("3.1.")


def test_contract_covers_all_operations(contract: dict[str, Any]) -> None:
    expected = {
        "/healthz": {"get"},
        "/issues": {"get", "post"},
        "/issues/{number}": {"get", "patch"},
        "/issues/{number}/comments": {"get", "post"},
        "/webhook": {"post"},
        "/events": {"get"},
    }

    for path, methods in expected.items():
        assert methods <= set(contract["paths"][path])


def test_contract_defines_reusable_components(contract: dict[str, Any]) -> None:
    components = contract["components"]

    assert {"Issue", "Comment", "Event", "Error"} <= set(components["schemas"])
    assert {"Location", "Link", "RetryAfter", "RequestId"} <= set(components["headers"])
    assert {
        "BadRequest",
        "Unauthorized",
        "Forbidden",
        "NotFound",
        "RateLimited",
        "ServiceUnavailable",
    } <= set(components["responses"])


def test_success_responses_include_examples(contract: dict[str, Any]) -> None:
    operations = [
        ("/healthz", "get", "200"),
        ("/issues", "post", "201"),
        ("/issues", "get", "200"),
        ("/issues/{number}", "get", "200"),
        ("/issues/{number}", "patch", "200"),
        ("/issues/{number}/comments", "post", "201"),
        ("/issues/{number}/comments", "get", "200"),
        ("/events", "get", "200"),
    ]

    for path, method, status in operations:
        media = contract["paths"][path][method]["responses"][status]["content"]["application/json"]
        assert "example" in media or "examples" in media


def test_error_responses_include_example_and_request_id(contract: dict[str, Any]) -> None:
    example = contract["components"]["schemas"]["Error"]["example"]
    assert example["error"]["code"]
    assert example["error"]["message"]

    for path_item in contract["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "patch"}:
                continue
            responses = operation["responses"]
            for response in responses.values():
                if "$ref" in response:
                    response = contract["components"]["responses"][
                        response["$ref"].rsplit("/", 1)[1]
                    ]
                assert response.get("headers", {}).get("X-Request-ID") == {
                    "$ref": "#/components/headers/RequestId"
                }
