"""Rolling 24-hour message history for conversations."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_RETENTION = timedelta(hours=24)


class MessageHistory:
    """In-memory + file-backed buffer of recent messages.

    Stores user and assistant messages with timestamps, auto-pruning
    entries older than 24 hours on each write.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._messages: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._messages = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load message history, starting fresh")
                self._messages = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._messages, ensure_ascii=False))

    def _prune(self) -> None:
        cutoff = (datetime.now(timezone.utc) - _RETENTION).isoformat()
        self._messages = [m for m in self._messages if m["ts"] >= cutoff]

    def record(self, direction: str, text: str) -> None:
        """Log a message. direction is 'user' or 'assistant'."""
        self._messages.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "direction": direction,
                "text": text,
            }
        )
        self._prune()
        self._save()

    def get_recent(self) -> str:
        """Return formatted string of recent messages (last 24h)."""
        self._prune()
        if not self._messages:
            return "No recent messages."

        lines = []
        for m in self._messages:
            ts = datetime.fromisoformat(m["ts"])
            local = ts.strftime("%H:%M")
            who = "User" if m["direction"] == "user" else "You"
            lines.append(f"[{local}] {who}: {m['text']}")
        return "\n".join(lines)
