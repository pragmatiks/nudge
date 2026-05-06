"""WebSocket endpoint for client communication."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.message_tool import QUALIFIED_TOOL_NAME, create_message_server
from src.api.tool_labels import friendly_label

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    """Handle WebSocket connections with auth, message processing, and status updates."""
    from config import settings

    # Auth: check token from query params
    token = ws.query_params.get("token")
    if token != settings.api_token:
        await ws.close(code=4001, reason="Unauthorized")
        return

    await ws.accept()

    pool = ws.app.state.pool
    coordinator = ws.app.state.coordinator
    history = ws.app.state.history
    data = ws.app.state.data

    # Send initial snapshots BEFORE joining the pool so any concurrent
    # task_added/event_added broadcast lands in the queue *after* the
    # snapshot, not before — otherwise the client's setTasks(snapshot)
    # would clobber the just-added item.
    await ws.send_json(data.tasks_snapshot())
    await ws.send_json(data.events_snapshot())
    await ws.send_json(history.snapshot())

    queue = await pool.connect()
    incoming: asyncio.Queue[dict] = asyncio.Queue()

    async def send_loop() -> None:
        """Drain the pool queue and send events to the WebSocket client."""
        while True:
            event = await queue.get()
            await ws.send_json(event)

    async def receive_loop() -> None:
        """Read from WebSocket, dispatching tool_responses immediately and queuing the rest."""
        while True:
            msg = await ws.receive_json()
            msg_type = msg.get("type")

            # Tool responses must be handled immediately (not queued)
            # to avoid deadlock when coordinator is awaiting a client tool result.
            if msg_type == "tool_response":
                pool.resolve_tool(msg["id"], msg.get("result"), msg.get("error"))
            else:
                await incoming.put(msg)

    async def process_loop() -> None:
        """Process queued messages and actions."""
        while True:
            msg = await incoming.get()
            msg_type = msg.get("type")
            try:
                if msg_type == "action":
                    await _handle_action(msg, pool, coordinator, history, data, ws, queue)
                elif msg_type == "message":
                    await _handle_message(msg, pool, coordinator, history, data, ws, queue)
                elif msg_type and msg_type.startswith(("task_", "event_")):
                    await _handle_data_op(msg, data)
            except WebSocketDisconnect:
                raise
            except Exception:
                logger.exception("Error processing %s", msg_type)

    send_task = asyncio.create_task(send_loop())
    receive_task = asyncio.create_task(receive_loop())
    process_task = asyncio.create_task(process_loop())

    try:
        # Wait until any task finishes (disconnect, error, etc.)
        done, _ = await asyncio.wait(
            [send_task, receive_task, process_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        # Check for WebSocketDisconnect
        for task in done:
            exc = task.exception()
            if isinstance(exc, WebSocketDisconnect):
                raise exc
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        send_task.cancel()
        receive_task.cancel()
        process_task.cancel()
        await pool.disconnect(queue)


async def _handle_message(
    msg: dict,
    pool,
    coordinator,
    history,
    data,
    ws: WebSocket,
    sender_queue: asyncio.Queue,
) -> None:
    text = msg.get("text", "").strip()
    if not text:
        return

    logger.info("Message from client: %s", text[:80])
    history.record("user", text)

    # Echo to peer clients so they stay in sync; sender already added locally.
    await pool.push({"type": "user_message", "text": text}, exclude=sender_queue)

    message_server = create_message_server(pool, history, data)

    async def on_tool(tool_name: str) -> None:
        if tool_name == QUALIFIED_TOOL_NAME:
            return
        label = friendly_label(tool_name)
        await pool.push_status(label)

    try:
        await coordinator.process_message(
            text,
            on_tool_use=on_tool,
            extra_mcp_servers={"nudge": message_server},
        )
    except Exception:
        logger.exception("Error processing message")
        await ws.send_json({"type": "error", "text": "Something went wrong."})


async def _handle_action(
    msg: dict,
    pool,
    coordinator,
    history,
    data,
    ws: WebSocket,
    sender_queue: asyncio.Queue,
) -> None:
    action = msg.get("action", "unknown")
    payload = msg.get("payload", {})
    text = f'[User clicked "{action}": {json.dumps(payload)}]'
    logger.info("Action from client: %s", text[:80])
    history.record("user", text)

    await pool.push({"type": "user_message", "text": text}, exclude=sender_queue)

    message_server = create_message_server(pool, history, data)

    async def on_tool(tool_name: str) -> None:
        if tool_name == QUALIFIED_TOOL_NAME:
            return
        label = friendly_label(tool_name)
        await pool.push_status(label)

    try:
        await coordinator.process_message(
            text,
            on_tool_use=on_tool,
            extra_mcp_servers={"nudge": message_server},
        )
    except Exception:
        logger.exception("Error processing action")
        await ws.send_json({"type": "error", "text": "Something went wrong."})


async def _op_create(data, payload, *, kind: str) -> None:
    if kind == "task":
        await data.add_task(**payload)
    else:
        await data.add_event(**payload)


async def _op_update(data, payload, *, kind: str) -> None:
    item_id = payload.pop("id", None)
    if not item_id:
        return
    if kind == "task":
        await data.update_task(item_id, **payload)
    else:
        await data.update_event(item_id, **payload)


async def _op_delete(data, payload, *, kind: str) -> None:
    item_id = payload.get("id")
    if not item_id:
        return
    if kind == "task":
        await data.delete_task(item_id)
    else:
        await data.delete_event(item_id)


async def _op_complete(data, payload, *, kind: str) -> None:
    item_id = payload.get("id")
    if not item_id:
        return
    await data.complete_task(item_id, bool(payload.get("completed", True)))


_DATA_OPS = {
    "task_create": (_op_create, "task"),
    "task_update": (_op_update, "task"),
    "task_complete": (_op_complete, "task"),
    "task_delete": (_op_delete, "task"),
    "event_create": (_op_create, "event"),
    "event_update": (_op_update, "event"),
    "event_delete": (_op_delete, "event"),
}


async def _handle_data_op(msg: dict, data) -> None:
    """Dispatch client-driven CRUD on tasks/events through DataService.

    Mutations broadcast to all clients via DataService, so other connected
    clients stay in sync without needing an explicit echo.
    """
    op = msg.get("type")
    handler = _DATA_OPS.get(op or "")
    if not handler:
        logger.warning("Unknown data op: %s", op)
        return
    fn, kind = handler
    try:
        await fn(data, dict(msg.get("payload", {})), kind=kind)
    except Exception:
        logger.exception("Failed to handle data op %s", op)
