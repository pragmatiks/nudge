"""Map raw MCP tool names to friendly status labels."""

# Exact tool name → label (checked first)
_EXACT_MAP: dict[str, str] = {
    # Native tasks (Nudge)
    "mcp__nudge__task_list": "Reading tasks...",
    "mcp__nudge__task_create": "Creating task...",
    "mcp__nudge__task_update": "Updating task...",
    "mcp__nudge__task_complete": "Completing task...",
    "mcp__nudge__task_delete": "Deleting task...",
    # Native calendar (Nudge)
    "mcp__nudge__event_list": "Reading calendar...",
    "mcp__nudge__event_create": "Creating event...",
    "mcp__nudge__event_update": "Updating event...",
    "mcp__nudge__event_delete": "Deleting event...",
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
    # Linear
    "mcp__linear__list_issues": "Listing Linear issues...",
    "mcp__linear__get_issue": "Reading Linear issue...",
    "mcp__linear__save_issue": "Updating Linear issue...",
    "mcp__linear__list_issue_statuses": "Checking issue statuses...",
    "mcp__linear__list_issue_labels": "Listing issue labels...",
    "mcp__linear__create_issue_label": "Creating issue label...",
    "mcp__linear__list_projects": "Listing Linear projects...",
    "mcp__linear__get_project": "Reading Linear project...",
    "mcp__linear__save_project": "Updating Linear project...",
    "mcp__linear__list_cycles": "Listing Linear cycles...",
    "mcp__linear__list_teams": "Listing Linear teams...",
    "mcp__linear__get_team": "Reading Linear team...",
    "mcp__linear__list_users": "Listing Linear users...",
    "mcp__linear__get_user": "Reading Linear user...",
    "mcp__linear__list_comments": "Reading Linear comments...",
    "mcp__linear__create_comment": "Commenting on Linear...",
    "mcp__linear__get_document": "Reading Linear doc...",
    "mcp__linear__list_documents": "Listing Linear docs...",
    "mcp__linear__create_document": "Creating Linear doc...",
    "mcp__linear__update_document": "Updating Linear doc...",
    "mcp__linear__search_documentation": "Searching Linear docs...",
    "mcp__linear__list_milestones": "Listing milestones...",
    "mcp__linear__get_milestone": "Reading milestone...",
    "mcp__linear__save_milestone": "Updating milestone...",
    "mcp__linear__get_issue_status": "Checking issue status...",
    "mcp__linear__get_attachment": "Getting Linear attachment...",
    "mcp__linear__create_attachment": "Creating Linear attachment...",
    "mcp__linear__delete_attachment": "Deleting Linear attachment...",
    "mcp__linear__list_project_labels": "Listing project labels...",
    "mcp__linear__extract_images": "Extracting images...",
    # Nudge message tool
    "mcp__nudge__message": "Sending message...",
    "mcp__nudge__get_history": "Checking message history...",
    "mcp__nudge__render": "Rendering component...",
    "mcp__nudge__notify": "Sending notification...",
    "mcp__nudge__open_url": "Opening URL...",
    "mcp__nudge__clipboard_write": "Copying to clipboard...",
    "mcp__nudge__clipboard_read": "Reading clipboard...",
    # Bash
    "Bash": "Running a command...",
}

_FALLBACK = "Working..."


def friendly_label(tool_name: str) -> str:
    """Return a human-friendly label for a tool name."""
    return _EXACT_MAP.get(tool_name, _FALLBACK)
