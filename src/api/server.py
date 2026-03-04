"""FastAPI application factory with lifespan management."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from config import settings
from src.agent.sessions import SessionStore
from src.api.history import MessageHistory
from src.api.pool import ConnectionPool
from src.api.ws import router as ws_router
from src.coordinator import Coordinator
from src.nudge.engine import NudgeEngine
from src.nudge.evaluator import NudgeEvaluator
from src.nudge.monitor import TaskMonitor
from src.nudge.observer import Observer
from src.nudge.store import NudgeStore

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("NUDGE_DATA_DIR", "/data"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize singletons and scheduler on startup, clean up on shutdown."""
    pool = ConnectionPool()
    session_store = SessionStore(DATA_DIR / "sessions" / "sessions.json")
    nudge_store = NudgeStore(DATA_DIR / "nudges" / "pending.json")
    history = MessageHistory(DATA_DIR / "history" / "messages.json")

    observer = Observer(nudge_store)
    evaluator = NudgeEvaluator(
        store=nudge_store,
        quiet_start=settings.quiet_hours_start,
        quiet_end=settings.quiet_hours_end,
        max_per_hour=settings.max_nudges_per_hour,
        max_per_day=settings.max_nudges_per_day,
    )

    coordinator = Coordinator(session_store, observer=observer)
    monitor = TaskMonitor()
    engine = NudgeEngine(coordinator, nudge_store, evaluator, monitor, pool, history)

    app.state.pool = pool
    app.state.coordinator = coordinator
    app.state.history = history

    scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
    engine.register_jobs(scheduler)
    scheduler.start()

    logger.info("Nudge server started")
    yield
    scheduler.shutdown()
    logger.info("Nudge server stopped")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(lifespan=lifespan)
    app.include_router(ws_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
