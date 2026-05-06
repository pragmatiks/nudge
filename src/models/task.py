from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Task:
    title: str
    notes: str = ""
    due: str | None = None  # ISO 8601 date or datetime
    priority: int = 4  # 1=urgent, 2=high, 3=medium, 4=normal
    completed: bool = False
    completed_at: datetime | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "notes": self.notes,
            "due": self.due,
            "priority": self.priority,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        completed_at = data.get("completed_at")
        return cls(
            id=data["id"],
            title=data["title"],
            notes=data.get("notes", ""),
            due=data.get("due"),
            priority=int(data.get("priority", 4)),
            completed=bool(data.get("completed", False)),
            completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
