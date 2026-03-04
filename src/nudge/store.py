import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.models.nudge import Nudge, NudgeStatus

logger = logging.getLogger(__name__)


class NudgeStore:
    """JSON-backed nudge persistence at /data/nudges/pending.json."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._nudges: list[Nudge] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                self._nudges = [Nudge.from_dict(n) for n in raw]
                logger.info("Loaded %d nudges from %s", len(self._nudges), self._path)
            except (json.JSONDecodeError, OSError, KeyError):
                logger.warning("Failed to load nudges, starting fresh")
                self._nudges = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps([n.to_dict() for n in self._nudges], indent=2))

    def add(self, nudge: Nudge) -> None:
        self._nudges.append(nudge)
        self._save()
        logger.info("Added nudge %s: %s at %s", nudge.id, nudge.about, nudge.remind_at)

    def get_due(self) -> list[Nudge]:
        return [n for n in self._nudges if n.is_due()]

    def mark_sent(self, nudge_id: str) -> None:
        for n in self._nudges:
            if n.id == nudge_id:
                n.status = NudgeStatus.SENT
                self._save()
                logger.info("Marked nudge %s as sent", nudge_id)
                return

    def remove(self, nudge_id: str) -> None:
        self._nudges = [n for n in self._nudges if n.id != nudge_id]
        self._save()

    def count_sent_since(self, since: datetime) -> int:
        return sum(
            1
            for n in self._nudges
            if n.status == NudgeStatus.SENT and n.created_at >= since
        )

    def cleanup_old(self, days: int = 7) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        before = len(self._nudges)
        self._nudges = [
            n
            for n in self._nudges
            if n.status == NudgeStatus.PENDING or n.created_at >= cutoff
        ]
        removed = before - len(self._nudges)
        if removed:
            self._save()
            logger.info("Cleaned up %d old nudges", removed)
        return removed
