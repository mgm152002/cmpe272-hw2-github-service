# Team member: Vinayak Shivam Gupta (@vsh2504)

from fastapi import APIRouter, Query, Request

from app.models.event import StoredEvent

router = APIRouter(tags=["Webhooks"])


@router.get("/events", response_model=list[StoredEvent])
async def list_events(request: Request, limit: int = Query(20, ge=1, le=100)) -> list[StoredEvent]:
    return request.app.state.events.list_recent(limit)
