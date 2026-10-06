import logging

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes import health

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.include_router(health.router, tags=["health"])


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Starting %s in %s mode",
        settings.app_name,
        settings.environment,
    )
