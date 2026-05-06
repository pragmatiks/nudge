# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Nudge is a personal AI assistant with a Tauri desktop app frontend and FastAPI + WebSocket backend, powered by Claude Agent SDK. It manages a native task list and calendar, detects commitments from conversations, delivers proactive nudges, runs daily briefings, and can automate browser tasks with Playwright and Proton Pass for credentials. The Tauri app has three tabs (Chat / Tasks / Calendar) all reflecting the same server state in real time over WebSocket.

## Commands

```bash
# Install dependencies
uv sync
(cd app && npm install)

# Local development (Taskfile.yml)
task backend            # FastAPI backend with uvicorn hot-reload on :8787
task frontend           # Tauri dev app (in app/)
task dev                # both at once
task dev:stop           # kill both

# Production deployment (bare-metal, mise + systemd)
mise run deploy         # git pull + uv sync + systemctl restart on remote
mise run logs           # journalctl -u nudge -f
mise run status         # systemctl status nudge + claude-mem health check
mise run restart        # systemctl restart nudge

# Tests
uv run pytest

# Lint and format
ruff check .
ruff format .

# One-time Proton Pass login (run on the server)
ssh root@$NUDGE_SERVER 'sudo -u nudge pass-cli login --interactive your@proton.me'
```

## Architecture

### Message Flow

All user messages and proactive prompts flow through a single persistent Claude session (`MAIN_THREAD = "main"`) for conversation continuity:

```
Tauri App → WebSocket → ws.py → Coordinator.process_message()
                                      ├── AgentClient (mcp_mode="full") → Claude SDK → response
                                      └── background: Observer (mcp_mode="observer") → detect commitments → NudgeStore
```

Internal prompts (nudges, briefings, check-ins) use `Coordinator.process_internal()` — same session, but no observer (prevents recursive chains).

### Proactive Systems (APScheduler jobs)

- **check_nudges** (every 60s): delivers due nudges from NudgeStore, gated by NudgeEvaluator (quiet hours 22–08, rate limits)
- **daily_briefing** (09:30 Europe/Paris): sends briefing prompt through main session
- **task_checkin** (self-scheduling, 5–120 min): TaskMonitor asks Claude to review native tasks/events, Claude decides when to check next

### MCP Modes

Agent tool access is controlled by mode, defined in `config/mcp_servers.py`. Tasks and calendar events are managed natively via SDK MCP tools in `src/api/message_tool.py` (not external servers):

| Mode | Servers | Bash | Used by |
|------|---------|------|---------|
| `full` | claude-mem, perplexity, linear | yes | Main agent |
| `observer` | claude-mem only | no | Commitment detection |
| `monitor` | claude-mem, linear | no | TaskMonitor |

### Key Modules

- `config/` — Settings (pydantic-settings from `.env`), MCP server configs, all system prompts
- `src/coordinator.py` — Central router: all messages and internal prompts go through here
- `src/agent/client.py` — Per-message `AgentClient` wrapping Claude SDK; session continuity via `SessionStore`
- `src/agent/sessions.py` — JSON-backed session_id persistence at `/data/sessions/`
- `src/api/server.py` — FastAPI app factory with lifespan management
- `src/api/ws.py` — WebSocket endpoint with auth and message processing
- `src/api/pool.py` — ConnectionPool (active WS clients + offline message queue)
- `src/api/message_tool.py` — SDK MCP server: message, get_history, render, client tools (notify/open_url/clipboard), and native task_*/event_* CRUD
- `src/api/data_service.py` — DataService: store mutations + WebSocket broadcast in one place
- `src/store/tasks.py` + `src/store/events.py` — JSON-backed CRUD for native tasks/events
- `src/models/task.py` + `src/models/event.py` — dataclass models
- `src/nudge/engine.py` — NudgeEngine class: all scheduled jobs (APScheduler)
- `src/nudge/observer.py` — Background commitment detector (JSON-only output, max 3 turns)
- `src/nudge/monitor.py` — Self-scheduling TaskMonitor (JSON-only output, decides next_check_minutes)
- `src/nudge/evaluator.py` — Rate limiting and quiet hours gate
- `config/prompts.py` — All three system prompts (main, observer, task monitor)
- `vendor/claude-mem/` — Vendored MCP server (.cjs bundles), worker runs on Bun at :37777
- `app/` — Tauri v2 + Vite + React desktop app

### Runtime Data

All persistent state lives under `$NUDGE_DATA_DIR` (defaults to `/data`; in production: `/opt/nudge/data`; in local dev: `./data`):
- `sessions/sessions.json` — Claude session ID map
- `nudges/pending.json` — Pending nudge queue
- `tasks/tasks.json` — Native task list
- `calendar/events.json` — Native calendar events
- `claude-mem/` — Memory storage (SQLite + vectors)
- `browser-profile/` — Playwright persistent sessions
- `proton-pass/` — Proton Pass CLI session

## Conventions

- **Boy Scout Rule**: Always leave the code cleaner than you found it. Fix lint warnings, unused imports, and small issues in files you touch
- **Single-owner app**: WebSocket auth via `API_TOKEN` shared secret restricts access to the owner
- **JSON-only agents**: Observer and TaskMonitor output only JSON. Parsing strips markdown fences and falls back to regex extraction
- **AgentClient is throwaway**: Created per-message, not long-lived. Session continuity comes from `SessionStore`, not client state
- **Session fallback**: If resuming a stale session fails, automatically creates a fresh one
- **Settings proxy**: Import `from config import settings` — it's a lazy proxy backed by `@lru_cache get_settings()`
- **Service runs as non-root `nudge` user** under systemd (claude CLI requires this for `bypassPermissions`)
- **`scripts/entrypoint.sh`** (invoked by `mise run start`) starts the claude-mem worker on Bun, waits for health at `:37777`, then execs `uvicorn src.api.server:create_app --factory` on `:8787`
