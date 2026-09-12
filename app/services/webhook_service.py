# Team member: Vinayak Shivam Gupta (@vsh2504)

from fastapi import HTTPException

from app.repositories.event_repository import EventRepository

ALLOWED_ACTIONS = {
    "ping": {"ping"},
    "issues": {
        "assigned",
        "closed",
        "deleted",
        "demilestoned",
        "edited",
        "labeled",
        "locked",
        "milestoned",
        "opened",
        "pinned",
        "reopened",
        "transferred",
        "unassigned",
        "unlabeled",
        "unlocked",
        "unpinned",
    },
    "issue_comment": {"created", "deleted", "edited"},
}


def process_webhook(
    repository: EventRepository, delivery_id: str, event: str, payload: dict
) -> bool:
    action = payload.get("action", "ping" if event == "ping" else "")
    if action not in ALLOWED_ACTIONS.get(event, set()):
        raise HTTPException(400, detail={"code": "UNSUPPORTED_EVENT", "message": "Unknown event or action"})
    issue_number = payload.get("issue", {}).get("number")
    return repository.save(delivery_id, event, action, issue_number)
