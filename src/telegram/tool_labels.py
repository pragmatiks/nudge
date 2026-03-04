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
    # Bash
    "Bash": "Running a command...",
}

_FALLBACK = "Working..."


def friendly_label(tool_name: str) -> str:
    """Return a human-friendly label for a tool name."""
    return _EXACT_MAP.get(tool_name, _FALLBACK)
