# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

from fastapi import APIRouter

router = APIRouter(tags=["Operations"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
