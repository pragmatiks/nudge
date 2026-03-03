import asyncio
import logging
import time

from src.agent.client import AgentClient
from src.agent.sessions import SessionStore
from src.nudge.observer import Observer

logger = logging.getLogger(__name__)

MAIN_THREAD = "main"


class Coordinator:
    """Orchestrates message processing with session persistence."""

    def __init__(
        self,
        session_store: SessionStore,
        observer: Observer | None = None,
    ) -> None:
        self._sessions = session_store
        self._observer = observer
        self._last_user_activity: float = time.monotonic()

    @property
    def idle_seconds(self) -> float:
        """Seconds since last user message."""
        return time.monotonic() - self._last_user_activity

    def clear_session(self) -> None:
        """Delete the main session so the next message starts fresh."""
        self._sessions.delete(MAIN_THREAD)
        logger.info("Main session cleared")

    async def process_message(self, user_text: str, on_text=None) -> str:
        """Process a user message and return the response.

        Resumes the main session if one exists. If resume fails (e.g. stale
        session after container rebuild), falls back to a fresh session.
        After responding, fires the observer in the background.
        If on_text is provided, streams each assistant message immediately.
        """
        self._last_user_activity = time.monotonic()
        response = await self._send_to_main_session(user_text, on_text=on_text)

        if self._observer:
            asyncio.create_task(self._observer.observe(user_text, response))

        return response

    async def process_internal(self, prompt: str, on_text=None) -> str:
        """Process an internal prompt (nudge/briefing) through the main session.

        Does NOT trigger the observer — prevents recursive nudge chains.
        """
        return await self._send_to_main_session(prompt, on_text=on_text)

    async def _send_to_main_session(self, text: str, on_text=None) -> str:
        """Send text through the main session with resume/fallback logic."""
        session_id = self._sessions.get(MAIN_THREAD)
        logger.info("Processing message (session=%s)", session_id)

        try:
            agent = AgentClient(resume_session_id=session_id)
            response, new_session_id = await agent.send_message(text, on_text=on_text)
        except Exception:
            if session_id is None:
                raise
            logger.warning("Resume failed for session=%s, retrying fresh", session_id)
            self._sessions.delete(MAIN_THREAD)
            agent = AgentClient(resume_session_id=None)
            response, new_session_id = await agent.send_message(text, on_text=on_text)

        if new_session_id:
            self._sessions.set(MAIN_THREAD, new_session_id)

        return response
