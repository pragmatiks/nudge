"""SDK MCP server that gives the agent explicit control over messaging and UI."""

import logging
from uuid import uuid4

from claude_agent_sdk import McpSdkServerConfig, create_sdk_mcp_server, tool

from src.api.history import MessageHistory
from src.api.pool import ConnectionPool

logger = logging.getLogger(__name__)

SERVER_NAME = "nudge"
QUALIFIED_TOOL_NAME = "mcp__nudge__message"


def create_message_server(
    pool: ConnectionPool, history: MessageHistory
) -> McpSdkServerConfig:
    """Create an SDK MCP server with messaging, rendering, and client-side tools.

    The server captures pool and history via closure so the agent
    can send messages, render components, and invoke client-side tools.
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
            import json

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
        ],
    )
