import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.api.history import MessageHistory
from src.api.message_tool import create_message_server
from src.api.pool import ConnectionPool
from src.coordinator import Coordinator
from src.nudge.evaluator import NudgeEvaluator
from src.nudge.monitor import TaskMonitor
from src.nudge.store import NudgeStore

logger = logging.getLogger(__name__)

NUDGE_DELIVERY_PROMPT = """\
[INTERNAL — NUDGE DELIVERY]
You have a pending reminder for the owner. Compose a brief, natural follow-up message.

Nudge: {about}
Context: {context}

Be conversational, not robotic. Don't say "reminder" or "nudge" — just bring it up naturally, \
like a thoughtful assistant checking in. Keep it to 1-2 sentences."""

DAILY_BRIEFING_PROMPT = """\
[INTERNAL — DAILY BRIEFING]
Good morning! Compose a brief daily briefing for the owner.

Check their Todoist tasks for today and any overdue items. Also search your memory for any \
relevant context about ongoing projects or commitments.

Format: Start with a friendly greeting, then list today's priorities. Keep it concise — \
bullet points are fine. If there's nothing urgent, say so briefly."""

SESSION_SAVE_PROMPT = """\
[INTERNAL — SESSION CYCLING]
Your session is about to be cleared due to inactivity. If there is any important context \
from recent conversations that hasn't been saved to memory yet, save it now using claude-mem. \
Focus on: decisions made, action items discussed, key information shared. \
Do NOT respond with any text — just save if needed."""


class NudgeEngine:
    """Manages all scheduled jobs for the nudge system."""

    def __init__(
        self,
        coordinator: Coordinator,
        nudge_store: NudgeStore,
        evaluator: NudgeEvaluator,
        monitor: TaskMonitor,
        pool: ConnectionPool,
        history: MessageHistory,
    ) -> None:
        self._coordinator = coordinator
        self._nudge_store = nudge_store
        self._evaluator = evaluator
        self._monitor = monitor
        self._pool = pool
        self._history = history
        self._scheduler: AsyncIOScheduler | None = None

    def _make_message_server(self):
        """Create a message server for engine jobs."""
        return create_message_server(self._pool, self._history)

    def register_jobs(self, scheduler: AsyncIOScheduler) -> None:
        """Register all scheduled jobs with the APScheduler instance."""
        from config import settings

        self._scheduler = scheduler

        scheduler.add_job(
            self.check_nudges,
            "interval",
            seconds=settings.nudge_check_interval_seconds,
            id="check_nudges",
        )

        hour, minute = (int(x) for x in settings.daily_briefing_time.split(":"))
        scheduler.add_job(
            self.daily_briefing,
            "cron",
            hour=hour,
            minute=minute,
            id="daily_briefing",
        )

        # Session cycle every 5 minutes
        scheduler.add_job(
            self.session_cycle,
            "interval",
            seconds=300,
            id="session_cycle",
        )

        # Task monitor: first check 2 min after startup, then self-schedules
        scheduler.add_job(
            self.task_checkin,
            "date",
            run_date=datetime.now(timezone.utc) + timedelta(minutes=2),
            id="task_checkin_initial",
        )

        logger.info(
            "Scheduled jobs: check_nudges every %ds, daily_briefing at %s, task_checkin (self-scheduling), session_cycle every 300s",
            settings.nudge_check_interval_seconds,
            settings.daily_briefing_time,
        )

    async def check_nudges(self) -> None:
        """Repeating job: check for due nudges and deliver them."""
        due = self._nudge_store.get_due()
        if not due:
            return

        message_server = self._make_message_server()

        for nudge in due:
            allowed, reason = self._evaluator.should_deliver()
            if not allowed:
                logger.info("Nudge %s suppressed: %s", nudge.id, reason)
                continue

            try:
                prompt = NUDGE_DELIVERY_PROMPT.format(
                    about=nudge.about, context=nudge.context
                )
                await self._coordinator.process_internal(
                    prompt, extra_mcp_servers={"nudge": message_server}
                )
                self._nudge_store.mark_sent(nudge.id)
                logger.info("Delivered nudge %s", nudge.id)
            except Exception:
                logger.exception("Failed to deliver nudge %s", nudge.id)

    async def daily_briefing(self) -> None:
        """Daily job: send morning briefing and clean up old nudges."""
        self._nudge_store.cleanup_old()

        message_server = self._make_message_server()

        try:
            await self._coordinator.process_internal(
                DAILY_BRIEFING_PROMPT, extra_mcp_servers={"nudge": message_server}
            )
            logger.info("Daily briefing sent")
        except Exception:
            logger.exception("Failed to send daily briefing")

    async def session_cycle(self) -> None:
        """Repeating job: clear idle sessions after saving context to memory.

        Deliberately has NO message server — structurally enforces silence.
        """
        from config import settings

        timeout = settings.session_idle_timeout_seconds

        if self._coordinator.idle_seconds < timeout:
            return

        if self._coordinator._sessions.get("main") is None:
            return

        try:
            await self._coordinator.process_internal(SESSION_SAVE_PROMPT)
            self._coordinator.clear_session()
            logger.info(
                "Session cleared after %.0f seconds idle (threshold: %ds)",
                self._coordinator.idle_seconds,
                timeout,
            )
        except Exception:
            logger.exception("Failed to cycle idle session")

    async def task_checkin(self) -> None:
        """Self-scheduling job: ask the task monitor to assess tasks, deliver if needed."""
        next_minutes = 30  # default fallback

        try:
            result = await self._monitor.check()
            next_minutes = result.next_check_minutes

            if result.should_check_in:
                allowed, reason = self._evaluator.should_deliver()
                if allowed:
                    prompt = f"[INTERNAL — TASK CHECK-IN]\n{result.prompt}"
                    message_server = self._make_message_server()
                    await self._coordinator.process_internal(
                        prompt, extra_mcp_servers={"nudge": message_server}
                    )
                    logger.info("Task check-in delivered")
                else:
                    logger.info("Task check-in suppressed: %s", reason)
        except Exception:
            logger.exception("Task check-in failed")
        finally:
            if self._scheduler:
                run_at = datetime.now(timezone.utc) + timedelta(minutes=next_minutes)
                self._scheduler.add_job(
                    self.task_checkin,
                    "date",
                    run_date=run_at,
                    id=f"task_checkin_{int(run_at.timestamp())}",
                )
                logger.info("Next task check-in in %d minutes", next_minutes)
