"""ConnectionPool manages active WebSocket clients and offline message buffering."""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Manages WebSocket connections and buffers messages when no client is connected.

    Messages are broadcast to all connected clients. When no clients are connected,
    messages are buffered in an offline queue and drained on reconnection.
    Status events are ephemeral and never buffered.
    """

    def __init__(self) -> None:
        self._queues: list[asyncio.Queue] = []
        self._offline_queue: list[dict] = []

    @property
    def has_clients(self) -> bool:
        return len(self._queues) > 0

    async def connect(self) -> asyncio.Queue:
        """Register a new client. Drains offline queue to it."""
        queue: asyncio.Queue = asyncio.Queue()
        self._queues.append(queue)
        logger.info("Client connected (total: %d)", len(self._queues))

        # Drain offline messages to the new client
        for msg in self._offline_queue:
            await queue.put(msg)
        if self._offline_queue:
            logger.info("Drained %d offline messages", len(self._offline_queue))
            self._offline_queue.clear()

        return queue

    async def disconnect(self, queue: asyncio.Queue) -> None:
        """Remove a client."""
        if queue in self._queues:
            self._queues.remove(queue)
        logger.info("Client disconnected (total: %d)", len(self._queues))

    async def push(self, event: dict) -> None:
        """Send an event to all connected clients, or buffer if none connected."""
        if not self._queues:
            event["queued_at"] = datetime.now(timezone.utc).isoformat()
            self._offline_queue.append(event)
            logger.debug(
                "Buffered message (offline queue: %d)", len(self._offline_queue)
            )
            return

        for queue in self._queues:
            await queue.put(event)

    async def push_status(self, text: str) -> None:
        """Send an ephemeral status event. Never buffered."""
        if not self._queues:
            return
        event = {"type": "status", "text": text}
        for queue in self._queues:
            await queue.put(event)
