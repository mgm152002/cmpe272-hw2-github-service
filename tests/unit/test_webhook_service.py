# Team member: Vinayak Shivam Gupta (@vsh2504)

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.services.webhook_service import process_webhook


@pytest.mark.parametrize(
    ("event", "action"),
    [
        ("ping", None),
        ("issues", "assigned"),
        ("issues", "opened"),
        ("issues", "closed"),
        ("issues", "deleted"),
        ("issues", "demilestoned"),
        ("issues", "edited"),
        ("issues", "labeled"),
        ("issues", "locked"),
        ("issues", "milestoned"),
        ("issues", "pinned"),
        ("issues", "reopened"),
        ("issues", "transferred"),
        ("issues", "unassigned"),
        ("issues", "unlabeled"),
        ("issues", "unlocked"),
        ("issues", "unpinned"),
        ("issue_comment", "created"),
        ("issue_comment", "edited"),
        ("issue_comment", "deleted"),
    ],
)
def test_processes_supported_events(event: str, action: str | None) -> None:
    repository = Mock()
    repository.save.return_value = True
    payload = {} if action is None else {"action": action, "issue": {"number": 7}}

    stored = process_webhook(repository, "delivery-1", event, payload)

    assert stored is True


@pytest.mark.parametrize(
    ("event", "payload"),
    [
        ("push", {"action": "created"}),
        ("issues", {}),
        ("issues", {"action": "invented"}),
        ("issue_comment", {"action": "opened"}),
    ],
)
def test_rejects_unsupported_events_and_actions(event: str, payload: dict) -> None:
    with pytest.raises(HTTPException) as caught:
        process_webhook(Mock(), "delivery-1", event, payload)

    assert caught.value.status_code == 400
    assert caught.value.detail["code"] == "UNSUPPORTED_EVENT"
