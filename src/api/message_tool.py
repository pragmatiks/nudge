"""SDK MCP server that gives the agent explicit control over messaging."""

import logging

from claude_agent_sdk import McpSdkServerConfig, create_sdk_mcp_server, tool

from src.api.history import MessageHistory
from src.api.pool import ConnectionPool

logger = logging.getLogger(__name__)

SERVER_NAME = "nudge"
QUALIFIED_TOOL_NAME = "mcp__nudge__message"


def create_message_server(
    pool: ConnectionPool, history: MessageHistory
) -> McpSdkServerConfig:
    """Create an SDK MCP server with message() and get_history() tools.

    The server captures pool and history via closure so the agent
    can send messages and check conversation context.
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

    return create_sdk_mcp_server(
        name=SERVER_NAME,
        tools=[message_tool, get_history_tool],
    )
