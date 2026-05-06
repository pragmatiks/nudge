"""SDK MCP server that gives the agent explicit control over messaging and UI."""

import json
import logging
from uuid import uuid4

from claude_agent_sdk import McpSdkServerConfig, create_sdk_mcp_server, tool

from src.api.data_service import DataService
from src.api.history import MessageHistory
from src.api.pool import ConnectionPool

logger = logging.getLogger(__name__)

SERVER_NAME = "nudge"
QUALIFIED_TOOL_NAME = "mcp__nudge__message"


def create_message_server(
    pool: ConnectionPool, history: MessageHistory, data: DataService
) -> McpSdkServerConfig:
    """Create an SDK MCP server with messaging, rendering, data, and client-side tools.

    The server captures pool, history, and data via closure so the agent
    can send messages, render components, manage native tasks/events, and
    invoke client-side tools.
    """

    @tool("message", "Send a message to the user", {"text": str})
    async def message_tool(args: dict) -> dict:
        text = args["text"]
        await pool.push({"type": "message", "text": text})
        history.record("assistant", text)
        return {"content": [{"type": "text", "text": "Message sent."}]}

    @tool(
        "get_history",
        "Get recent message history (last 24 hours) to check what was recently discussed",
        {},
    )
    async def get_history_tool(args: dict) -> dict:
        recent = history.get_recent()
        return {"content": [{"type": "text", "text": recent}]}

    @tool(
        "render",
        "Render a rich UI component inline in the chat. Available components:\n"
        "- task_list: {title: str, tasks: [{name, priority?, due?, completed?}]}\n"
        "- info_card: {title: str, body: str, icon?: 'info'|'warning'|'success'|'calendar'}\n"
        "- confirm: {title: str, message: str, actions: [{label: str, value: str}]}",
        {"component": str, "props": dict},
    )
    async def render_tool(args: dict) -> dict:
        component = args["component"]
        props = args["props"]
        # Claude sometimes passes props as a JSON string instead of a dict
        if isinstance(props, str):
            props = json.loads(props)
        logger.info("Render: component=%s, props=%s", component, props)
        await pool.push({"type": "component", "component": component, "props": props})
        return {
            "content": [{"type": "text", "text": f"Component '{component}' rendered."}]
        }

    @tool(
        "notify",
        "Send a native OS notification to the user",
        {"title": str, "body": str},
    )
    async def notify_tool(args: dict) -> dict:
        request_id = uuid4().hex[:8]
        await pool.request_tool(request_id, "notify", args)
        return {"content": [{"type": "text", "text": "Notification sent."}]}

    @tool(
        "open_url",
        "Open a URL in the user's default browser",
        {"url": str},
    )
    async def open_url_tool(args: dict) -> dict:
        request_id = uuid4().hex[:8]
        await pool.request_tool(request_id, "open_url", args)
        return {"content": [{"type": "text", "text": "URL opened."}]}

    @tool(
        "clipboard_write",
        "Write text to the user's clipboard",
        {"text": str},
    )
    async def clipboard_write_tool(args: dict) -> dict:
        request_id = uuid4().hex[:8]
        await pool.request_tool(request_id, "clipboard_write", args)
        return {"content": [{"type": "text", "text": "Text copied to clipboard."}]}

    @tool(
        "clipboard_read",
        "Read text from the user's clipboard",
        {},
    )
    async def clipboard_read_tool(args: dict) -> dict:
        request_id = uuid4().hex[:8]
        result = await pool.request_tool(request_id, "clipboard_read", args)
        text = result.get("text", "")
        return {"content": [{"type": "text", "text": text}]}

    # --- Native tasks (the user's todo list)

    @tool(
        "task_list",
        "List all of the user's tasks. Returns JSON: "
        "[{id, title, notes, due, priority (1=urgent..4=normal), completed, completed_at}]",
        {},
    )
    async def task_list_tool(args: dict) -> dict:
        tasks = [t.to_dict() for t in data.list_tasks()]
        return {"content": [{"type": "text", "text": json.dumps(tasks)}]}

    @tool(
        "task_create",
        "Create a new task. priority is 1 (urgent) to 4 (normal/none). "
        "due is ISO 8601 (date 'YYYY-MM-DD' or datetime).",
        {"title": str, "notes": str, "due": str, "priority": int},
    )
    async def task_create_tool(args: dict) -> dict:
        task = await data.add_task(
            title=args["title"],
            notes=args.get("notes", "") or "",
            due=args.get("due") or None,
            priority=int(args.get("priority") or 4),
        )
        return {"content": [{"type": "text", "text": f"Task created: {task.id}"}]}

    @tool(
        "task_update",
        "Update fields on an existing task. Only include fields to change.",
        {"id": str, "title": str, "notes": str, "due": str, "priority": int},
    )
    async def task_update_tool(args: dict) -> dict:
        fields = {k: v for k, v in args.items() if k != "id" and v is not None}
        if "priority" in fields:
            fields["priority"] = int(fields["priority"])
        task = await data.update_task(args["id"], **fields)
        if not task:
            return {"content": [{"type": "text", "text": f"Task {args['id']} not found."}]}
        return {"content": [{"type": "text", "text": f"Task updated: {task.id}"}]}

    @tool(
        "task_complete",
        "Mark a task complete (or uncomplete by passing completed=false).",
        {"id": str, "completed": bool},
    )
    async def task_complete_tool(args: dict) -> dict:
        completed = bool(args.get("completed", True))
        task = await data.complete_task(args["id"], completed)
        if not task:
            return {"content": [{"type": "text", "text": f"Task {args['id']} not found."}]}
        verb = "completed" if completed else "reopened"
        return {"content": [{"type": "text", "text": f"Task {verb}: {task.id}"}]}

    @tool(
        "task_delete",
        "Delete a task permanently.",
        {"id": str},
    )
    async def task_delete_tool(args: dict) -> dict:
        ok = await data.delete_task(args["id"])
        msg = f"Task deleted: {args['id']}" if ok else f"Task {args['id']} not found."
        return {"content": [{"type": "text", "text": msg}]}

    # --- Native calendar events

    @tool(
        "event_list",
        "List all calendar events. Returns JSON: "
        "[{id, title, description, start, end, location, all_day}]",
        {},
    )
    async def event_list_tool(args: dict) -> dict:
        events = [e.to_dict() for e in data.list_events()]
        return {"content": [{"type": "text", "text": json.dumps(events)}]}

    @tool(
        "event_create",
        "Create a calendar event. start/end are ISO 8601. "
        "Set all_day=true for all-day events (use 'YYYY-MM-DD' for start/end).",
        {
            "title": str,
            "start": str,
            "end": str,
            "description": str,
            "location": str,
            "all_day": bool,
        },
    )
    async def event_create_tool(args: dict) -> dict:
        event = await data.add_event(
            title=args["title"],
            start=args["start"],
            end=args["end"],
            description=args.get("description", "") or "",
            location=args.get("location", "") or "",
            all_day=bool(args.get("all_day", False)),
        )
        return {"content": [{"type": "text", "text": f"Event created: {event.id}"}]}

    @tool(
        "event_update",
        "Update fields on an existing event. Only include fields to change.",
        {
            "id": str,
            "title": str,
            "start": str,
            "end": str,
            "description": str,
            "location": str,
            "all_day": bool,
        },
    )
    async def event_update_tool(args: dict) -> dict:
        fields = {k: v for k, v in args.items() if k != "id" and v is not None}
        event = await data.update_event(args["id"], **fields)
        if not event:
            return {"content": [{"type": "text", "text": f"Event {args['id']} not found."}]}
        return {"content": [{"type": "text", "text": f"Event updated: {event.id}"}]}

    @tool(
        "event_delete",
        "Delete a calendar event permanently.",
        {"id": str},
    )
    async def event_delete_tool(args: dict) -> dict:
        ok = await data.delete_event(args["id"])
        msg = f"Event deleted: {args['id']}" if ok else f"Event {args['id']} not found."
        return {"content": [{"type": "text", "text": msg}]}

    return create_sdk_mcp_server(
        name=SERVER_NAME,
        tools=[
            message_tool,
            get_history_tool,
            render_tool,
            notify_tool,
            open_url_tool,
            clipboard_write_tool,
            clipboard_read_tool,
            task_list_tool,
            task_create_tool,
            task_update_tool,
            task_complete_tool,
            task_delete_tool,
            event_list_tool,
            event_create_tool,
            event_update_tool,
            event_delete_tool,
        ],
    )
