from pathlib import Path

from src.models.event import Event
from src.store._base import JsonDictStore


class EventStore(JsonDictStore[Event]):
    """JSON-backed calendar event persistence."""

    label = "events"

    def __init__(self, path: Path) -> None:
        super().__init__(path, from_dict=Event.from_dict, to_dict=Event.to_dict)

    def _sort_key(self, event: Event):
        return event.start
