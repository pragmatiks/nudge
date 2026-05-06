from pathlib import Path

from src.models.task import Task
from src.store._base import JsonDictStore, utcnow


class TaskStore(JsonDictStore[Task]):
    """JSON-backed task persistence."""

    label = "tasks"

    def __init__(self, path: Path) -> None:
        super().__init__(path, from_dict=Task.from_dict, to_dict=Task.to_dict)

    def _sort_key(self, task: Task):
        return (task.completed, task.priority, task.created_at)

    def complete(self, task_id: str, completed: bool = True) -> Task | None:
        return self.update(
            task_id,
            completed=completed,
            completed_at=utcnow() if completed else None,
        )
