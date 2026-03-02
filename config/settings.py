from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Telegram
    telegram_bot_token: str
    telegram_owner_id: int

    # Claude Agent SDK (uses OAuth token from Max subscription)
    claude_code_oauth_token: str

    # Todoist
    todoist_api_token: str

    # Perplexity (optional — web search for the agent)
    perplexity_api_key: str = ""

    # Nudge behavior
    daily_briefing_time: str = "09:30"
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8  # 8 AM
    max_nudges_per_hour: int = 3
    max_nudges_per_day: int = 15
    nudge_check_interval_seconds: int = 60

    # Agent
    max_agent_turns: int = 10
