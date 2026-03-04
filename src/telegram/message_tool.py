"""SDK MCP server that gives the agent explicit control over Telegram messaging."""

import logging

from claude_agent_sdk import McpSdkServerConfig, create_sdk_mcp_server, tool
from telegram import Bot

from src.telegram.history import MessageHistory

logger = logging.getLogger(__name__)

SERVER_NAME = "telegram"
QUALIFIED_TOOL_NAME = "mcp__telegram__message"


def create_message_server(
    bot: Bot, chat_id: int, history: MessageHistory
) -> McpSdkServerConfig:
    """Create an SDK MCP server with message() and get_history() tools.

    The server captures bot, chat_id, and history via closure so the agent
    can send messages and check conversation context.
    """

    @tool("message", "Send a message to the user on Telegram", {"text": str})
    async def message_tool(args: dict) -> dict:
        text = args["text"]
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception:
            # Markdown parse failed — retry without formatting
            logger.debug("Markdown send failed, retrying plain", exc_info=True)
            await bot.send_message(chat_id=chat_id, text=text)
        history.record("assistant", text)
        return {"content": [{"type": "text", "text": "Message sent."}]}

    @tool(
        "get_history",
        "Get recent Telegram message history (last 24 hours) to check what was recently discussed",
        {},
    )
    async def get_history_tool(args: dict) -> dict:
        recent = history.get_recent()
        return {"content": [{"type": "text", "text": recent}]}

    return create_sdk_mcp_server(
        name=SERVER_NAME,
        tools=[message_tool, get_history_tool],
    )
