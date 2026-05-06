"""Shared base for JSON-file-backed dict stores."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JsonDictStore(Generic[T]):
    """Dict-of-T persisted as a JSON array file, keyed by `id` attribute.

    Subclasses provide a model class with `from_dict`/`to_dict` and (optionally)
    override `_sort_key` to control list ordering.
    """

    label: str = "items"

    def __init__(
        self,
        path: Path,
        from_dict: Callable[[dict], T],
        to_dict: Callable[[T], dict],
    ) -> None:
        self._path = path
        self._from_dict = from_dict
        self._to_dict = to_dict
        self._items: dict[str, T] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text())
            self._items = {item["id"]: self._from_dict(item) for item in raw}
            logger.info("Loaded %d %s from %s", len(self._items), self.label, self._path)
        except (json.JSONDecodeError, OSError, KeyError):
            logger.warning("Failed to load %s, starting fresh", self.label)
            self._items = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([self._to_dict(item) for item in self._items.values()], indent=2)
        )

    def _sort_key(self, item: T):  # noqa: ANN001 — subclass-specific
        return getattr(item, "id", "")

    def list(self) -> list[T]:
        return sorted(self._items.values(), key=self._sort_key)

    def get(self, item_id: str) -> T | None:
        return self._items.get(item_id)

    def add(self, item: T) -> T:
        self._items[getattr(item, "id")] = item
        self._save()
        return item

    def update(self, item_id: str, **fields) -> T | None:
        """Apply `fields` via setattr, bump `updated_at`, save."""
        item = self._items.get(item_id)
        if not item:
            return None
        for key, value in fields.items():
            if hasattr(item, key):
                setattr(item, key, value)
        if hasattr(item, "updated_at"):
            item.updated_at = utcnow()
        self._save()
        return item

    def delete(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            self._save()
            return True
        return False
