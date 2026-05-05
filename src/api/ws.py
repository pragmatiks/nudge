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

    queue = await pool.connect()
    incoming: asyncio.Queue[dict] = asyncio.Queue()

    async def send_loop() -> None:
        """Drain the pool queue and send events to the WebSocket client."""
        try:
            while True:
                event = await queue.get()
                await ws.send_json(event)
        except Exception:
            pass

    async def receive_loop() -> None:
        """Read from WebSocket, dispatching tool_responses immediately and queuing the rest."""
        try:
            while True:
                data = await ws.receive_json()
                msg_type = data.get("type")

                # Tool responses must be handled immediately (not queued)
                # to avoid deadlock when coordinator is awaiting a client tool result.
                if msg_type == "tool_response":
                    pool.resolve_tool(data["id"], data.get("result"), data.get("error"))
                else:
                    await incoming.put(data)
        except Exception:
            pass

    async def process_loop() -> None:
        """Process queued messages and actions."""
        try:
            while True:
                data = await incoming.get()
                msg_type = data.get("type")

                if msg_type == "action":
                    await _handle_action(data, pool, coordinator, history, ws, queue)
                elif msg_type == "message":
                    await _handle_message(data, pool, coordinator, history, ws, queue)
        except Exception:
            pass

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
    data: dict,
    pool,
    coordinator,
    history,
    ws: WebSocket,
    sender_queue: asyncio.Queue,
) -> None:
    text = data.get("text", "").strip()
    if not text:
        return

    logger.info("Message from client: %s", text[:80])
    history.record("user", text)

    # Echo to peer clients so they stay in sync; sender already added locally.
    await pool.push({"type": "user_message", "text": text}, exclude=sender_queue)

    message_server = create_message_server(pool, history)

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
    data: dict,
    pool,
    coordinator,
    history,
    ws: WebSocket,
    sender_queue: asyncio.Queue,
) -> None:
    action = data.get("action", "unknown")
    payload = data.get("payload", {})
    text = f'[User clicked "{action}": {json.dumps(payload)}]'
    logger.info("Action from client: %s", text[:80])
    history.record("user", text)

    await pool.push({"type": "user_message", "text": text}, exclude=sender_queue)

    message_server = create_message_server(pool, history)

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
