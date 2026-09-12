# Team member: Vinayak Shivam Gupta (@vsh2504)

import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import get_settings
from app.middleware.request_context import request_id_context
from app.services.signature_service import verify_signature
from app.services.webhook_service import process_webhook

router = APIRouter(tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=204)
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str = Header(),
    x_github_delivery: str = Header(),
) -> Response:
    body = await request.body()
    if not verify_signature(body, x_hub_signature_256, get_settings().webhook_secret):
        raise HTTPException(401, detail={"code": "INVALID_SIGNATURE", "message": "Invalid signature"})
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, detail={"code": "INVALID_JSON", "message": "Invalid JSON"}) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            400,
            detail={"code": "INVALID_JSON", "message": "Webhook payload must be an object"},
        )
    stored = process_webhook(
        request.app.state.events, x_github_delivery, x_github_event, payload
    )
    event_data = {
        "request_id": request_id_context.get(),
        "delivery_id": x_github_delivery,
        "event": x_github_event,
        "action": payload.get("action", "ping" if x_github_event == "ping" else ""),
        "issue_number": payload.get("issue", {}).get("number"),
        "stored": stored,
    }
    logger.info("webhook_processed", extra={"event_data": event_data})
    return Response(status_code=204)
