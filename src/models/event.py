from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Event:
    title: str
    start: str  # ISO 8601 datetime (or date if all_day)
    end: str
    description: str = ""
    location: str = ""
    all_day: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start": self.start,
            "end": self.end,
            "location": self.location,
            "all_day": self.all_day,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Event:
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            start=data["start"],
            end=data["end"],
            location=data.get("location", ""),
            all_day=bool(data.get("all_day", False)),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
