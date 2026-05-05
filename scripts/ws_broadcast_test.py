"""Verify that user messages from one client are echoed to peer clients.

Opens a 'peer' connection that listens, then a 'sender' connection that
posts a user message. Asserts the peer sees a `user_message` event with
the original text and that the sender does NOT (no echo loop).
"""

import asyncio
import json

import websockets

URL = "ws://localhost:8787/ws?token=dev-local-token"


async def collect_until_idle(ws, timeout: float = 8.0) -> list[dict]:
    events: list[dict] = []
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            return events
        events.append(json.loads(raw))


async def main() -> None:
    async with websockets.connect(URL) as peer:
        # Give the peer connection time to register
        await asyncio.sleep(0.3)

        async with websockets.connect(URL) as sender:
            await asyncio.sleep(0.3)
            await sender.send(
                json.dumps({"type": "message", "text": "hello peers"})
            )

            peer_events, sender_events = await asyncio.gather(
                collect_until_idle(peer, timeout=15.0),
                collect_until_idle(sender, timeout=15.0),
            )

    peer_user_msgs = [e for e in peer_events if e.get("type") == "user_message"]
    sender_user_msgs = [e for e in sender_events if e.get("type") == "user_message"]

    print(f"peer events:   {[e['type'] for e in peer_events]}")
    print(f"sender events: {[e['type'] for e in sender_events]}")
    print(f"peer user_message texts:   {[e['text'] for e in peer_user_msgs]}")
    print(f"sender user_message count: {len(sender_user_msgs)}")

    assert peer_user_msgs, "peer should have received a user_message echo"
    assert peer_user_msgs[0]["text"] == "hello peers"
    assert not sender_user_msgs, "sender should NOT receive its own echo"
    print("\nOK: user_message echoed to peer, not back to sender")


if __name__ == "__main__":
    asyncio.run(main())
