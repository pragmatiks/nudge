"""Headless WS client for end-to-end testing the Nudge backend protocol.

Drives one or more conversation turns and prints every event received.
Auto-replies to client tool requests with successful mock results so the
agent can complete its turn.
"""

import asyncio
import json
import sys

import websockets

URL = "ws://localhost:8787/ws?token=dev-local-token"


MOCK_TOOL_RESULTS = {
    "notify": {"sent": True},
    "open_url": {"opened": True},
    "clipboard_write": {"written": True},
    "clipboard_read": {"text": "<clipboard contents>"},
}


async def run_turn(
    prompt: str,
    follow_up_action: tuple[str, dict] | None = None,
    idle_timeout: float = 60.0,
) -> None:
    """Send `prompt`, then drain events until idle. Auto-replies to tool requests.

    If `follow_up_action` is given, sends it after the agent goes quiet.
    """
    print(f"\n{'=' * 70}\n>>> USER: {prompt}\n{'=' * 70}")
    async with websockets.connect(URL) as ws:
        await ws.send(json.dumps({"type": "message", "text": prompt}))

        followup_sent = follow_up_action is None

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=idle_timeout)
            except asyncio.TimeoutError:
                print(f"<<< [idle for {idle_timeout}s, ending turn]")
                return

            event = json.loads(raw)
            t = event.get("type")

            if t == "message":
                print(f"<<< MESSAGE: {event['text']}")
                if not followup_sent:
                    action, payload = follow_up_action
                    print(f">>> ACTION: {action} {payload}")
                    await ws.send(
                        json.dumps(
                            {"type": "action", "action": action, "payload": payload}
                        )
                    )
                    followup_sent = True
            elif t == "component":
                print(f"<<< COMPONENT: {event['component']}")
                print(f"    props: {json.dumps(event['props'], indent=4)}")
                if not followup_sent:
                    action, payload = follow_up_action
                    print(f">>> ACTION: {action} {payload}")
                    await ws.send(
                        json.dumps(
                            {"type": "action", "action": action, "payload": payload}
                        )
                    )
                    followup_sent = True
            elif t == "tool_request":
                name = event["name"]
                args = event["args"]
                rid = event["id"]
                result = MOCK_TOOL_RESULTS.get(name, {})
                print(f"<<< TOOL_REQUEST: {name}({json.dumps(args)}) -> mock {result}")
                await ws.send(
                    json.dumps({"type": "tool_response", "id": rid, "result": result})
                )
            elif t == "status":
                print(f"    [status] {event['text']}")
            elif t == "error":
                print(f"<<< ERROR: {event['text']}")
            else:
                print(f"<<< UNKNOWN ({t}): {event}")


async def main() -> None:
    test = sys.argv[1] if len(sys.argv) > 1 else "render_list"

    if test == "render_list":
        await run_turn(
            "Please render a small task_list component with these tasks: "
            "'Ship Phase 6' (p1), 'Write docs' (p2), 'Test client tools' (p3). "
            "Title: 'Today'. Render the component, no extra explanation."
        )
    elif test == "confirm":
        await run_turn(
            "Render a confirm component asking 'Mark Phase 6 done?' with Yes/No buttons. "
            "Don't send any other message.",
            follow_up_action=("confirm", {"value": "yes"}),
        )
    elif test == "notify":
        await run_turn(
            "Send a desktop notification with title 'Test' and body 'Phase 6 works'. "
            "Then briefly confirm it was sent."
        )
    elif test == "clipboard":
        await run_turn(
            "Copy the text 'phase 6 works' to my clipboard, then briefly confirm."
        )
    elif test == "open_url":
        await run_turn(
            "Open https://anthropic.com in my browser, then briefly confirm."
        )
    elif test == "info_card":
        await run_turn(
            "Render an info_card component with title='Phase 6', body='Rich UI rendering and "
            "client-side tools are wired end-to-end.', icon='success'. No extra text."
        )
    else:
        print(f"Unknown test: {test}")


if __name__ == "__main__":
    asyncio.run(main())
