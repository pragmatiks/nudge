import logging
import os
from collections.abc import Awaitable, Callable

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from config import get_settings
from config.mcp_servers import (
    _MONITOR_SERVERS,
    _OBSERVER_SERVERS,
    get_allowed_tools,
    get_mcp_servers,
)
from config.prompts import MAIN_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentClient:
    """Wraps Claude Agent SDK with per-message lifecycle.

    Each send_message() creates a fresh ClaudeSDKClient, optionally
    resuming a previous session. This avoids persistent connection
    issues and naturally supports session switching.
    """

    def __init__(
        self,
        resume_session_id: str | None = None,
        system_prompt: str | None = None,
        mcp_mode: str = "full",
        max_turns: int | None = None,
    ) -> None:
        s = get_settings()
        servers = get_mcp_servers(s)

        # Filter servers by mode
        if mcp_mode == "observer":
            servers = {k: v for k, v in servers.items() if k in _OBSERVER_SERVERS}
        elif mcp_mode == "monitor":
            servers = {k: v for k, v in servers.items() if k in _MONITOR_SERVERS}

        self._mcp_servers = servers
        self._allowed_tools = get_allowed_tools(self._mcp_servers, mcp_mode)
        self._options = ClaudeAgentOptions(
            system_prompt=system_prompt or MAIN_AGENT_SYSTEM_PROMPT,
            mcp_servers=self._mcp_servers,
            allowed_tools=self._allowed_tools,
            max_turns=max_turns or s.max_agent_turns,
            permission_mode="bypassPermissions",
            resume=resume_session_id,
        )
        os.environ.setdefault("CLAUDE_CODE_OAUTH_TOKEN", s.claude_code_oauth_token)
        logger.info(
            "AgentClient created (resume=%s, servers=%s)",
            resume_session_id,
            list(self._mcp_servers.keys()),
        )

    async def send_message(
        self,
        text: str,
        on_text: "Callable[[str], Awaitable[None]] | None" = None,
        on_tool_use: "Callable[[str], Awaitable[None]] | None" = None,
    ) -> tuple[str, str | None]:
        """Send a message and return (response_text, session_id).

        Creates a client, processes the message, and closes — all in one call.
        If on_text is provided, each assistant message is streamed immediately.
        If on_tool_use is provided, called with tool name on each tool invocation.
        """
        logger.info("Sending to Claude: %s", text[:100])

        session_id: str | None = None
        response_parts: list[str] = []

        async with ClaudeSDKClient(options=self._options) as client:
            await client.query(text)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    parts = []
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            parts.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            logger.info("Tool call: %s", block.name)
                            if on_tool_use:
                                try:
                                    await on_tool_use(block.name)
                                except Exception:
                                    logger.warning(
                                        "on_tool_use callback failed",
                                        exc_info=True,
                                    )
                    chunk = "\n".join(parts)
                    if chunk:
                        response_parts.append(chunk)
                        if on_text:
                            try:
                                await on_text(chunk)
                            except Exception:
                                logger.warning("on_text callback failed", exc_info=True)
                elif isinstance(message, ResultMessage):
                    session_id = getattr(message, "session_id", None)
                    logger.info(
                        "Result: session=%s, cost=$%s",
                        session_id,
                        getattr(message, "total_cost_usd", None),
                    )

        response = "\n".join(response_parts) if response_parts else "..."
        logger.info("Response (%d chars, session=%s)", len(response), session_id)
        return response, session_id
