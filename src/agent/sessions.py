import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionStore:
    """Maps thread_id → Claude session_id with JSON persistence."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
                logger.info("Loaded %d sessions from %s", len(self._data), self._path)
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to load sessions, starting fresh")
                self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data))

    def get(self, thread_id: str) -> str | None:
        return self._data.get(thread_id)

    def set(self, thread_id: str, session_id: str) -> None:
        self._data[thread_id] = session_id
        self._save()

    def delete(self, thread_id: str) -> None:
        self._data.pop(thread_id, None)
        self._save()
