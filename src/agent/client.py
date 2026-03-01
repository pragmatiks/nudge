import logging
import os

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from config import get_settings
from config.mcp_servers import get_allowed_tools, get_mcp_servers
from config.prompts import MAIN_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentClient:
    """Wraps Claude Agent SDK for handling user messages.

    Phase 1: stateless query() per message.
    Phase 3 will upgrade to ClaudeSDKClient with session persistence.
    """

    def __init__(self) -> None:
        s = get_settings()
        self._mcp_servers = get_mcp_servers(s)
        self._allowed_tools = get_allowed_tools(self._mcp_servers)
        self._options = ClaudeAgentOptions(
            system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
            mcp_servers=self._mcp_servers,
            allowed_tools=self._allowed_tools,
            max_turns=s.max_agent_turns,
            permission_mode="bypassPermissions",
        )
        # Ensure the OAuth token is available to the SDK
        os.environ.setdefault(
            "CLAUDE_CODE_OAUTH_TOKEN", s.claude_code_oauth_token
        )
        logger.info(
            "AgentClient initialized with MCP servers: %s",
            list(self._mcp_servers.keys()),
        )

    async def send_message(self, text: str) -> str:
        """Send a user message to Claude and return the text response."""
        logger.debug("Sending message to Claude: %s", text[:100])

        response_parts: list[str] = []

        async for message in query(prompt=text, options=self._options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)

        response = "\n".join(response_parts) if response_parts else "..."
        logger.debug("Got response (%d chars)", len(response))
        return response
