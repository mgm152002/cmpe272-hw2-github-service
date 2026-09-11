# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

import sqlite3
from pathlib import Path


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS events (
        delivery_id TEXT NOT NULL,
        action TEXT NOT NULL,
        event TEXT NOT NULL,
        issue_number INTEGER,
        timestamp TEXT NOT NULL,
        PRIMARY KEY (delivery_id, action)
        )"""
    )
    connection.commit()
    return connection
