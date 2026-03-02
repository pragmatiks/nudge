from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


class NudgeStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


@dataclass
class Nudge:
    remind_at: datetime
    about: str
    context: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: NudgeStatus = NudgeStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_due(self) -> bool:
        return (
            self.status == NudgeStatus.PENDING
            and datetime.now(timezone.utc) >= self.remind_at
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "remind_at": self.remind_at.isoformat(),
            "about": self.about,
            "context": self.context,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Nudge:
        return cls(
            id=data["id"],
            remind_at=datetime.fromisoformat(data["remind_at"]),
            about=data["about"],
            context=data["context"],
            status=NudgeStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
        )
