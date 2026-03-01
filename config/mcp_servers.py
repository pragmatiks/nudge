from config.settings import Settings


def get_mcp_servers(s: Settings) -> dict:
    """Build MCP server configuration for the Claude Agent."""
    servers: dict = {}

    if s.todoist_api_token:
        servers["todoist"] = {
            "type": "http",
            "url": "https://ai.todoist.net/mcp",
            "headers": {"Authorization": f"Bearer {s.todoist_api_token}"},
        }

    return servers


def get_allowed_tools(servers: dict) -> list[str]:
    """Return wildcard permissions for all configured MCP servers."""
    return [f"mcp__{name}__*" for name in servers]
