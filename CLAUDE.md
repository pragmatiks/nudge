# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Nudge is a personal AI assistant running as a Telegram bot, powered by Claude Agent SDK. It manages tasks via Todoist, detects commitments from conversations, delivers proactive nudges, runs daily briefings, and can automate browser tasks with Playwright and Proton Pass for credentials.

## Commands

```bash
# Run locally
uv sync
python -m src.main

# Run in Docker (primary deployment method)
docker compose up -d --build

# Logs
docker compose logs -f

# Tests
uv run pytest

# Lint and format
ruff check .
ruff format .

# One-time Proton Pass login (after first deploy)
docker exec -it nudge-bot pass-cli login --interactive your@proton.me
```

## Architecture

### Message Flow

All user messages and proactive prompts flow through a single persistent Claude session (`MAIN_THREAD = "main"`) for conversation continuity:

```
Telegram → handlers.py → Coordinator.process_message()
                              ├── AgentClient (mcp_mode="full") → Claude SDK → response
                              └── background: Observer (mcp_mode="observer") → detect commitments → NudgeStore
```

Internal prompts (nudges, briefings, check-ins) use `Coordinator.process_internal()` — same session, but no observer (prevents recursive chains).

### Proactive Systems (APScheduler jobs)

- **check_nudges** (every 60s): delivers due nudges from NudgeStore, gated by NudgeEvaluator (quiet hours 22–08, rate limits)
- **daily_briefing** (09:30 Europe/Paris): sends briefing prompt through main session
- **task_checkin** (self-scheduling, 5–120 min): TaskMonitor asks Claude to review Todoist, Claude decides when to check next

### MCP Modes

Agent tool access is controlled by mode, defined in `config/mcp_servers.py`:

| Mode | Servers | Bash | Used by |
|------|---------|------|---------|
| `full` | todoist, claude-mem, perplexity, linear, calendar | yes | Main agent |
| `observer` | claude-mem only | no | Commitment detection |
| `monitor` | todoist, claude-mem, linear, calendar | no | TaskMonitor |

### Key Modules

- `config/` — Settings (pydantic-settings from `.env`), MCP server configs, all system prompts
- `src/coordinator.py` — Central router: all messages and internal prompts go through here
- `src/agent/client.py` — Per-message `AgentClient` wrapping Claude SDK; session continuity via `SessionStore`
- `src/agent/sessions.py` — JSON-backed session_id persistence at `/data/sessions/`
- `src/nudge/observer.py` — Background commitment detector (JSON-only output, max 3 turns)
- `src/nudge/monitor.py` — Self-scheduling TaskMonitor (JSON-only output, decides next_check_minutes)
- `src/nudge/engine.py` — APScheduler job functions
- `src/nudge/evaluator.py` — Rate limiting and quiet hours gate
- `src/telegram/bot.py` — `create_app()` wires handlers, schedules jobs
- `config/prompts.py` — All three system prompts (main, observer, task monitor)
- `vendor/claude-mem/` — Vendored MCP server (.cjs bundles), worker runs on Bun at :37777

### Runtime Data

All persistent state lives under `/data/` (Docker volume `nudge_data`):
- `sessions/sessions.json` — Claude session ID map
- `nudges/pending.json` — Pending nudge queue
- `claude-mem/` — Memory storage (SQLite + vectors)
- `browser-profile/` — Playwright persistent sessions
- `proton-pass/` — Proton Pass CLI session

## Conventions

- **Boy Scout Rule**: Always leave the code cleaner than you found it. Fix lint warnings, unused imports, and small issues in files you touch
- **Single-owner bot**: `OwnerFilter` in `src/telegram/access.py` restricts all handlers to `TELEGRAM_OWNER_ID`
- **JSON-only agents**: Observer and TaskMonitor output only JSON. Parsing strips markdown fences and falls back to regex extraction
- **AgentClient is throwaway**: Created per-message, not long-lived. Session continuity comes from `SessionStore`, not client state
- **Session fallback**: If resuming a stale session fails, automatically creates a fresh one
- **Settings proxy**: Import `from config import settings` — it's a lazy proxy backed by `@lru_cache get_settings()`
- **Container runs as non-root `nudge` user** (claude CLI requires this for `bypassPermissions`)
- **entrypoint.sh** starts claude-mem worker first, waits for health check at `:37777`, then launches the bot
