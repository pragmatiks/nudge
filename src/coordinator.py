import asyncio
import logging

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

    async def process_message(self, user_text: str) -> str:
        """Process a user message and return the response.

        Resumes the main session if one exists. If resume fails (e.g. stale
        session after container rebuild), falls back to a fresh session.
        After responding, fires the observer in the background.
        """
        response = await self._send_to_main_session(user_text)

        if self._observer:
            asyncio.create_task(self._observer.observe(user_text, response))

        return response

    async def process_internal(self, prompt: str) -> str:
        """Process an internal prompt (nudge/briefing) through the main session.

        Does NOT trigger the observer — prevents recursive nudge chains.
        """
        return await self._send_to_main_session(prompt)

    async def _send_to_main_session(self, text: str) -> str:
        """Send text through the main session with resume/fallback logic."""
        session_id = self._sessions.get(MAIN_THREAD)
        logger.info("Processing message (session=%s)", session_id)

        try:
            agent = AgentClient(resume_session_id=session_id)
            response, new_session_id = await agent.send_message(text)
        except Exception:
            if session_id is None:
                raise
            logger.warning("Resume failed for session=%s, retrying fresh", session_id)
            self._sessions.delete(MAIN_THREAD)
            agent = AgentClient(resume_session_id=None)
            response, new_session_id = await agent.send_message(text)

        if new_session_id:
            self._sessions.set(MAIN_THREAD, new_session_id)

        return response
