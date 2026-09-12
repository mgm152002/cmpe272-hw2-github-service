# Team member: Vinayak Shivam Gupta (@vsh2504)

from app.database import connect
from app.repositories.event_repository import EventRepository


def test_duplicate_delivery_and_action_is_stored_once() -> None:
    connection = connect(":memory:")
    repository = EventRepository(connection)
    try:
        first = repository.save("delivery-1", "issues", "opened", 1)
        duplicate = repository.save("delivery-1", "issues", "opened", 1)
        events = repository.list_recent()
    finally:
        connection.close()

    assert first is True
    assert duplicate is False
    assert len(events) == 1
    assert events[0].id == "delivery-1"


def test_lists_newest_events_first_and_honors_limit() -> None:
    connection = connect(":memory:")
    repository = EventRepository(connection)
    try:
        repository.save("delivery-1", "issues", "opened", 1)
        repository.save("delivery-2", "issue_comment", "created", 1)
        events = repository.list_recent(limit=1)
    finally:
        connection.close()

    assert [event.id for event in events] == ["delivery-2"]
