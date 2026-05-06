"""Service layer that mutates task/event stores and broadcasts changes to clients."""

import logging

from src.api.pool import ConnectionPool
from src.models.event import Event
from src.models.task import Task
from src.store.events import EventStore
from src.store.tasks import TaskStore

logger = logging.getLogger(__name__)


class DataService:
    """Wraps Task/Event stores with WebSocket broadcasting on mutation."""

    def __init__(
        self, tasks: TaskStore, events: EventStore, pool: ConnectionPool
    ) -> None:
        self._tasks = tasks
        self._events = events
        self._pool = pool

    # --- snapshots (used on client connect)

    def tasks_snapshot(self) -> dict:
        return {"type": "tasks_snapshot", "tasks": [t.to_dict() for t in self._tasks.list()]}

    def events_snapshot(self) -> dict:
        return {"type": "events_snapshot", "events": [e.to_dict() for e in self._events.list()]}

    # --- task mutations

    async def add_task(self, **fields) -> Task:
        task = self._tasks.add(Task(**fields))
        await self._pool.push({"type": "task_added", "task": task.to_dict()})
        return task

    async def update_task(self, task_id: str, **fields) -> Task | None:
        task = self._tasks.update(task_id, **fields)
        if task:
            await self._pool.push({"type": "task_updated", "task": task.to_dict()})
        return task

    async def complete_task(self, task_id: str, completed: bool = True) -> Task | None:
        task = self._tasks.complete(task_id, completed)
        if task:
            await self._pool.push({"type": "task_updated", "task": task.to_dict()})
        return task

    async def delete_task(self, task_id: str) -> bool:
        ok = self._tasks.delete(task_id)
        if ok:
            await self._pool.push({"type": "task_deleted", "id": task_id})
        return ok

    # --- event mutations

    async def add_event(self, **fields) -> Event:
        event = self._events.add(Event(**fields))
        await self._pool.push({"type": "event_added", "event": event.to_dict()})
        return event

    async def update_event(self, event_id: str, **fields) -> Event | None:
        event = self._events.update(event_id, **fields)
        if event:
            await self._pool.push({"type": "event_updated", "event": event.to_dict()})
        return event

    async def delete_event(self, event_id: str) -> bool:
        ok = self._events.delete(event_id)
        if ok:
            await self._pool.push({"type": "event_deleted", "id": event_id})
        return ok

    # --- read-only

    def list_tasks(self) -> list[Task]:
        return self._tasks.list()

    def list_events(self) -> list[Event]:
        return self._events.list()
