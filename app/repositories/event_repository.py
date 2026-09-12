# Team member: Vinayak Shivam Gupta (@vsh2504)

import sqlite3
from datetime import UTC, datetime

from app.models.event import StoredEvent


class EventRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def save(self, delivery_id: str, event: str, action: str, issue_number: int | None) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?, ?)",
            (delivery_id, action, event, issue_number, datetime.now(UTC).isoformat()),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def list_recent(self, limit: int = 20) -> list[StoredEvent]:
        rows = self.connection.execute(
            "SELECT delivery_id, event, action, issue_number, timestamp FROM events ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            StoredEvent(
                id=row["delivery_id"], event=row["event"], action=row["action"],
                issue_number=row["issue_number"], timestamp=row["timestamp"]
            )
            for row in rows
        ]
