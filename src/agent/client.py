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
    """Wraps Claude Agent SDK with a persistent session.

    Uses ClaudeSDKClient for multi-turn conversation with context
    maintained across messages within the same session.
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
        self._client: ClaudeSDKClient | None = None
        self._session_id: str | None = None
        logger.info(
            "AgentClient initialized with MCP servers: %s",
            list(self._mcp_servers.keys()),
        )

    async def _ensure_client(self) -> ClaudeSDKClient:
        """Get or create the SDK client."""
        if self._client is None:
            self._client = ClaudeSDKClient(options=self._options)
            await self._client.__aenter__()
            logger.info("ClaudeSDKClient connected")
        return self._client

    async def send_message(self, text: str) -> str:
        """Send a user message to Claude and return the text response."""
        logger.info("Sending to Claude: %s", text[:100])

        client = await self._ensure_client()
        await client.query(text)

        response_parts: list[str] = []

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        logger.info("Tool call: %s", block.name)
            elif isinstance(message, ResultMessage):
                self._session_id = getattr(message, "session_id", None)
                logger.info(
                    "Result: session=%s, cost=$%s",
                    self._session_id,
                    getattr(message, "total_cost_usd", None),
                )

        response = "\n".join(response_parts) if response_parts else "..."
        logger.info("Response (%d chars)", len(response))
        return response

    async def close(self) -> None:
        """Shut down the client connection."""
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None
            logger.info("ClaudeSDKClient disconnected")
