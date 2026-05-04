from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # API auth
    api_token: str

    # Claude Agent SDK (uses OAuth token from Max subscription)
    claude_code_oauth_token: str

    # Todoist
    todoist_api_token: str

    # Perplexity (optional — web search for the agent)
    perplexity_api_key: str = ""

    # Linear (optional — issue tracking)
    linear_api_key: str = ""

    # Office 365 calendar (optional — ICS feed URL from Outlook Web)
    outlook_calendar_ics_url: str = ""

    # Nudge behavior
    daily_briefing_time: str = "09:30"
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8  # 8 AM
    max_nudges_per_hour: int = 3
    max_nudges_per_day: int = 15
    nudge_check_interval_seconds: int = 60

    # Session management
    session_idle_timeout_seconds: int = 900  # 15 minutes

    # Agent
    max_agent_turns: int = 10
