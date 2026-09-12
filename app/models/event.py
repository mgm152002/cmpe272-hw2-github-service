# Team member: Vinayak Shivam Gupta (@vsh2504)

from datetime import datetime

from pydantic import BaseModel


class StoredEvent(BaseModel):
    id: str
    event: str
    action: str
    issue_number: int | None = None
    timestamp: datetime
