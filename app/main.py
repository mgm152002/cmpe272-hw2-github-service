# Team member: Vinayak Shivam Gupta (@vsh2504)

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import events, health, issues, webhooks
from app.api.error_handlers import register_error_handlers
from app.config import get_settings
from app.database import connect
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.repositories.event_repository import EventRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = connect(get_settings().database_path)
    app.state.events = EventRepository(connection)
    yield
    connection.close()


configure_logging()
app = FastAPI(
    title="CMPE 272 - HW #2 - GitHub Service",
    version="0.1.0",
    lifespan=lifespan,
)
register_error_handlers(app)
app.add_middleware(RequestContextMiddleware)
app.include_router(health.router)
app.include_router(issues.router)
app.include_router(webhooks.router)
app.include_router(events.router)
