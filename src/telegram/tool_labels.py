"""Map raw MCP tool names to friendly status labels."""

# Exact tool name → label (checked first)
_EXACT_MAP: dict[str, str] = {
    # Todoist
    "mcp__todoist__add-tasks": "Adding tasks...",
    "mcp__todoist__update-tasks": "Updating tasks...",
    "mcp__todoist__complete-tasks": "Completing tasks...",
    "mcp__todoist__find-tasks": "Searching tasks...",
    "mcp__todoist__find-tasks-by-date": "Searching tasks by date...",
    "mcp__todoist__find-completed-tasks": "Checking completed tasks...",
    "mcp__todoist__get-overview": "Getting Todoist overview...",
    "mcp__todoist__add-projects": "Creating project...",
    "mcp__todoist__update-projects": "Updating project...",
    "mcp__todoist__find-projects": "Searching projects...",
    "mcp__todoist__project-management": "Managing project...",
    "mcp__todoist__project-move": "Moving project...",
    "mcp__todoist__add-sections": "Adding section...",
    "mcp__todoist__update-sections": "Updating section...",
    "mcp__todoist__find-sections": "Searching sections...",
    "mcp__todoist__add-comments": "Adding comment...",
    "mcp__todoist__find-comments": "Reading comments...",
    "mcp__todoist__update-comments": "Updating comment...",
    "mcp__todoist__find-activity": "Checking activity log...",
    "mcp__todoist__delete-object": "Deleting from Todoist...",
    "mcp__todoist__fetch-object": "Fetching from Todoist...",
    "mcp__todoist__user-info": "Getting user info...",
    "mcp__todoist__find-project-collaborators": "Finding collaborators...",
    "mcp__todoist__manage-assignments": "Managing assignments...",
    "mcp__todoist__list-workspaces": "Listing workspaces...",
    "mcp__todoist__search": "Searching Todoist...",
    "mcp__todoist__fetch": "Fetching from Todoist...",
    # Memory
    "mcp__claude-mem__search": "Searching memory...",
    "mcp__claude-mem__timeline": "Browsing memory timeline...",
    "mcp__claude-mem__get_observations": "Retrieving memories...",
    "mcp__claude-mem__save_memory": "Saving to memory...",
    # Perplexity
    "mcp__perplexity__perplexity_ask": "Asking the web...",
    "mcp__perplexity__perplexity_search": "Searching the web...",
    "mcp__perplexity__perplexity_research": "Researching online...",
    "mcp__perplexity__perplexity_reason": "Reasoning about web results...",
    # Bash
    "Bash": "Running a command...",
}

_FALLBACK = "Working..."


def friendly_label(tool_name: str) -> str:
    """Return a human-friendly label for a tool name."""
    return _EXACT_MAP.get(tool_name, _FALLBACK)
