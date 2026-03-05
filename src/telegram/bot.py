import logging
import os
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import settings
from src.agent.sessions import SessionStore
from src.coordinator import Coordinator
from src.nudge.engine import check_nudges, daily_briefing, session_cycle, task_checkin
from src.nudge.evaluator import NudgeEvaluator
from src.nudge.monitor import TaskMonitor
from src.nudge.observer import Observer
from src.nudge.store import NudgeStore
from src.telegram.access import owner_filter
from src.telegram.handlers import (
    handle_message,
    handle_start,
    set_coordinator,
    shutdown_agent,
)
from src.telegram.history import MessageHistory

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("NUDGE_DATA_DIR", "/opt/nudge/data"))


def create_app() -> Application:
    """Build and configure the Telegram bot application."""
    session_store = SessionStore(DATA_DIR / "sessions" / "sessions.json")
    nudge_store = NudgeStore(DATA_DIR / "nudges" / "pending.json")

    observer = Observer(nudge_store)
    evaluator = NudgeEvaluator(
        store=nudge_store,
        quiet_start=settings.quiet_hours_start,
        quiet_end=settings.quiet_hours_end,
        max_per_hour=settings.max_nudges_per_hour,
        max_per_day=settings.max_nudges_per_day,
    )

    coordinator = Coordinator(session_store, observer=observer)
    set_coordinator(coordinator)

    app = Application.builder().token(settings.telegram_bot_token).build()

    monitor = TaskMonitor()
    message_history = MessageHistory(DATA_DIR / "history" / "messages.json")

    app.bot_data["coordinator"] = coordinator
    app.bot_data["nudge_store"] = nudge_store
    app.bot_data["evaluator"] = evaluator
    app.bot_data["monitor"] = monitor
    app.bot_data["owner_chat_id"] = settings.telegram_owner_id
    app.bot_data["message_history"] = message_history

    app.add_handler(CommandHandler("start", handle_start, filters=owner_filter))
    app.add_handler(
        MessageHandler(owner_filter & filters.TEXT & ~filters.COMMAND, handle_message)
    )
    app.post_shutdown = shutdown_agent

    _schedule_jobs(app)

    logger.info("Telegram bot configured (owner_id=%s)", settings.telegram_owner_id)
    return app


def _schedule_jobs(app: Application) -> None:
    """Register recurring nudge check and daily briefing jobs."""
    job_queue = app.job_queue

    job_queue.run_repeating(
        check_nudges,
        interval=settings.nudge_check_interval_seconds,
        first=settings.nudge_check_interval_seconds,
        name="check_nudges",
    )

    hour, minute = (int(x) for x in settings.daily_briefing_time.split(":"))
    job_queue.run_daily(
        daily_briefing,
        time=time(hour=hour, minute=minute, tzinfo=ZoneInfo("Europe/Paris")),
        name="daily_briefing",
    )

    # Task monitor: first check 2 min after startup, then self-schedules
    job_queue.run_once(task_checkin, when=120, name="task_checkin")

    job_queue.run_repeating(
        session_cycle,
        interval=300,
        first=300,
        name="session_cycle",
    )

    logger.info(
        "Scheduled jobs: check_nudges every %ds, daily_briefing at %s, task_checkin (self-scheduling), session_cycle every 300s",
        settings.nudge_check_interval_seconds,
        settings.daily_briefing_time,
    )
