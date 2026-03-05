import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from config.prompts import TASK_MONITOR_SYSTEM_PROMPT
from src.agent.client import AgentClient

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    should_check_in: bool
    prompt: str
    next_check_minutes: int


class TaskMonitor:
    """Periodically reviews Todoist tasks and decides whether to check in."""

    async def check(self) -> CheckResult:
        """One-shot Claude call to assess tasks and decide on check-in."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        prompt = (
            f"Current time: {now.strftime('%A, %B %d, %Y at %H:%M')} (Europe/Paris)"
        )

        try:
            agent = AgentClient(
                resume_session_id=None,
                system_prompt=TASK_MONITOR_SYSTEM_PROMPT,
                mcp_mode="monitor",
                max_turns=5,
            )
            raw_response, _ = await agent.send_message(prompt)
            return self._parse(raw_response)
        except Exception:
            logger.exception("Task monitor agent failed")
            return CheckResult(should_check_in=False, prompt="", next_check_minutes=30)

    def _parse(self, raw: str) -> CheckResult:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                logger.warning("Monitor output not valid JSON: %s", raw[:200])
                return CheckResult(
                    should_check_in=False, prompt="", next_check_minutes=30
                )
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning("Monitor output not valid JSON: %s", raw[:200])
                return CheckResult(
                    should_check_in=False, prompt="", next_check_minutes=30
                )

        next_minutes = max(5, min(120, data.get("next_check_minutes", 30)))

        if not data.get("check_in"):
            logger.info(
                "Monitor: no check-in (reason: %s, next: %dm)",
                data.get("reason", "?"),
                next_minutes,
            )
            return CheckResult(
                should_check_in=False, prompt="", next_check_minutes=next_minutes
            )

        prompt = data.get("message", "")
        logger.info(
            "Monitor: check-in requested (reason: %s, next: %dm)",
            data.get("reason", "?"),
            next_minutes,
        )
        return CheckResult(
            should_check_in=True, prompt=prompt, next_check_minutes=next_minutes
        )
