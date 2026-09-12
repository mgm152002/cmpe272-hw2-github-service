# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

import pytest
from pydantic import ValidationError

from app.models.issue import CreateIssueRequest, UpdateIssueRequest


def test_create_issue_requires_nonempty_title() -> None:
    with pytest.raises(ValidationError):
        CreateIssueRequest(title="")


def test_update_issue_rejects_invalid_state() -> None:
    with pytest.raises(ValidationError):
        UpdateIssueRequest(state="deleted")
