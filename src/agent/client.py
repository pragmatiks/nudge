import logging
import os

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from config import get_settings
from config.mcp_servers import get_allowed_tools, get_mcp_servers
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

        # Observer only gets claude-mem (not Todoist) to keep cost low
        if mcp_mode == "observer":
            servers = {k: v for k, v in servers.items() if k == "claude-mem"}

        self._mcp_servers = servers
        self._allowed_tools = get_allowed_tools(self._mcp_servers)
        self._options = ClaudeAgentOptions(
            system_prompt=system_prompt or MAIN_AGENT_SYSTEM_PROMPT,
            mcp_servers=self._mcp_servers,
            allowed_tools=self._allowed_tools,
            max_turns=max_turns or s.max_agent_turns,
            permission_mode="bypassPermissions",
            resume=resume_session_id,
        )
        os.environ.setdefault(
            "CLAUDE_CODE_OAUTH_TOKEN", s.claude_code_oauth_token
        )
        logger.info(
            "AgentClient created (resume=%s, servers=%s)",
            resume_session_id,
            list(self._mcp_servers.keys()),
        )

    async def send_message(self, text: str) -> tuple[str, str | None]:
        """Send a message and return (response_text, session_id).

        Creates a client, processes the message, and closes — all in one call.
        """
        logger.info("Sending to Claude: %s", text[:100])

        session_id: str | None = None
        response_parts: list[str] = []

        async with ClaudeSDKClient(options=self._options) as client:
            await client.query(text)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_parts.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            logger.info("Tool call: %s", block.name)
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
