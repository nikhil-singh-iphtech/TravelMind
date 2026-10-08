from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, bookings, health, travel_plans
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import init_db
from app.embeddings.local_provider import SentenceTransformerProvider

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    init_db()
    # Load embedding model once at startup
    _ = SentenceTransformerProvider()
    yield
    logger.info("Shutting down %s...", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, tags=["auth"])
app.include_router(travel_plans.router, tags=["travel-plans"])
app.include_router(bookings.router, tags=["bookings"])
app.include_router(health.router, tags=["health"])


