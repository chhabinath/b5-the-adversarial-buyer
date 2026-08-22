"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.core.database import initialize_database
from app.api.health import router as health_router
from app.api.personas import router as personas_router
from app.api.scan import router as scan_router
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize application-wide services during startup."""

    settings = get_settings()
    configure_logging(settings.log_level)
    initialize_database()
    logging.getLogger(__name__).info("application_started", extra={"environment": settings.app_env})
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router)
app.include_router(personas_router)
app.include_router(scan_router)