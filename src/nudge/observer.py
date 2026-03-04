import json
import logging
import re

from config.prompts import OBSERVER_SYSTEM_PROMPT
from src.agent.client import AgentClient
from src.models.nudge import Nudge
from src.nudge.store import NudgeStore

logger = logging.getLogger(__name__)


class Observer:
    """Analyzes conversation turns for commitments and schedules nudges."""

    def __init__(self, store: NudgeStore) -> None:
        self._store = store

    async def observe(self, user_text: str, bot_response: str) -> None:
        """Run observer in background after each conversation turn."""
        try:
            await self._run(user_text, bot_response)
        except Exception:
            logger.exception("Observer failed (non-fatal)")

    async def _run(self, user_text: str, bot_response: str) -> None:
        prompt = f"User said: {user_text}\n\nAssistant replied: {bot_response}"

        agent = AgentClient(
            resume_session_id=None,
            system_prompt=OBSERVER_SYSTEM_PROMPT,
            mcp_mode="observer",
            max_turns=3,
        )
        raw_response, _ = await agent.send_message(prompt)
        nudges = self._parse_nudges(raw_response)

        for nudge in nudges:
            self._store.add(nudge)

        if nudges:
            logger.info("Observer detected %d nudge(s)", len(nudges))

    def _parse_nudges(self, raw: str) -> list[Nudge]:
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                return []
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning("Observer output not valid JSON: %s", raw[:200])
                return []

        nudge_list = data.get("nudges", [])
        result = []
        for item in nudge_list:
            try:
                from datetime import datetime, timezone

                remind_at = datetime.fromisoformat(item["remind_at"])
                if remind_at.tzinfo is None:
                    remind_at = remind_at.replace(tzinfo=timezone.utc)
                result.append(
                    Nudge(
                        remind_at=remind_at,
                        about=item["about"],
                        context=item.get("context", ""),
                    )
                )
            except (KeyError, ValueError) as e:
                logger.warning("Skipping malformed nudge: %s (%s)", item, e)

        return result
