import logging
from datetime import datetime, timedelta, timezone

from src.nudge.store import NudgeStore

logger = logging.getLogger(__name__)


class NudgeEvaluator:
    """Decides whether a nudge should be delivered right now."""

    def __init__(
        self,
        store: NudgeStore,
        quiet_start: int = 22,
        quiet_end: int = 8,
        max_per_hour: int = 3,
        max_per_day: int = 15,
    ) -> None:
        self._store = store
        self._quiet_start = quiet_start
        self._quiet_end = quiet_end
        self._max_per_hour = max_per_hour
        self._max_per_day = max_per_day

    def should_deliver(self) -> tuple[bool, str]:
        now = datetime.now()
        hour = now.hour

        # Quiet hours (handles midnight wrap, e.g. 22-08)
        if self._quiet_start > self._quiet_end:
            in_quiet = hour >= self._quiet_start or hour < self._quiet_end
        else:
            in_quiet = self._quiet_start <= hour < self._quiet_end

        if in_quiet:
            return False, f"quiet hours ({self._quiet_start}:00-{self._quiet_end}:00)"

        now_utc = datetime.now(timezone.utc)
        hourly = self._store.count_sent_since(now_utc - timedelta(hours=1))
        if hourly >= self._max_per_hour:
            return False, f"hourly limit reached ({hourly}/{self._max_per_hour})"

        daily = self._store.count_sent_since(now_utc - timedelta(hours=24))
        if daily >= self._max_per_day:
            return False, f"daily limit reached ({daily}/{self._max_per_day})"

        return True, "ok"
