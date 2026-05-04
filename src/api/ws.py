"""WebSocket endpoint for client communication."""

import asyncio
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

    async def send_loop() -> None:
        """Drain the queue and send events to the WebSocket client."""
        try:
            while True:
                event = await queue.get()
                await ws.send_json(event)
        except Exception:
            pass

    send_task = asyncio.create_task(send_loop())

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") != "message":
                continue

            text = data.get("text", "").strip()
            if not text:
                continue

            logger.info("Message from client: %s", text[:80])
            history.record("user", text)

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

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        send_task.cancel()
        await pool.disconnect(queue)
