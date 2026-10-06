import logging

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, travel_plans

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name) 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(travel_plans.router, tags=["travel-plans"])

app.include_router(health.router, tags=["health"])


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Starting %s in %s mode",
        settings.app_name,
        settings.environment,
    )
