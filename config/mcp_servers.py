from pathlib import Path

from config.settings import Settings

_VENDORED_MCP_SERVER = Path(__file__).parent.parent / "vendor" / "claude-mem" / "scripts" / "mcp-server.cjs"


def get_mcp_servers(s: Settings) -> dict:
    """Build MCP server configuration for the Claude Agent."""
    servers: dict = {}

    if s.todoist_api_token:
        servers["todoist"] = {
            "type": "http",
            "url": "https://ai.todoist.net/mcp",
            "headers": {"Authorization": f"Bearer {s.todoist_api_token}"},
        }

    if _VENDORED_MCP_SERVER.exists():
        servers["claude-mem"] = {
            "command": "node",
            "args": [str(_VENDORED_MCP_SERVER)],
        }

    if s.perplexity_api_key:
        servers["perplexity"] = {
            "command": "npx",
            "args": ["-y", "@perplexity-ai/mcp-server"],
            "env": {"PERPLEXITY_API_KEY": s.perplexity_api_key},
        }

    if s.linear_api_key:
        servers["linear"] = {
            "type": "http",
            "url": "https://mcp.linear.app/mcp",
            "headers": {"Authorization": f"Bearer {s.linear_api_key}"},
        }

    if s.outlook_calendar_ics_url:
        servers["calendar"] = {
            "command": "npx",
            "args": ["-y", "@voxxit/mcp-ical"],
            "env": {
                "CALENDAR_URL": s.outlook_calendar_ics_url,
                "CALENDAR_NAME": "Ducker Carlisle",
                "TZ": "Europe/Berlin",
            },
        }

    return servers


# Servers excluded from non-full modes (observer gets claude-mem only)
_OBSERVER_SERVERS = {"claude-mem"}
_MONITOR_SERVERS = {"todoist", "claude-mem", "linear", "calendar"}


def get_allowed_tools(servers: dict, mcp_mode: str = "full") -> list[str]:
    """Return tool permissions based on mode and configured MCP servers.

    Only the main agent (mcp_mode="full") gets Bash access for pass-cli.
    Observer and task monitor don't need Bash or browser automation.
    """
    tools = [f"mcp__{name}__*" for name in servers]
    if mcp_mode == "full":
        tools.append("Bash")
    return tools
