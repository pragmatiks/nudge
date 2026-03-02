FROM python:3.12-slim

# Node.js (for MCP server scripts) + Bun (for claude-mem worker) + curl (for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip jq && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    curl -fsSL https://bun.sh/install | bash && \
    mv /root/.bun /usr/local/bun && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/local/bun/bin:$PATH"

# uv (provides uvx, needed by claude-mem for ChromaDB MCP server)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Proton Pass CLI (credential retrieval for browser automation)
RUN curl -fsSL https://proton.me/download/pass-cli/install.sh | bash && \
    mv /root/.local/bin/pass-cli /usr/local/bin/pass-cli

# Playwright CLI (browser automation via shell commands, token-efficient)
RUN npm install -g @anthropic-ai/claude-code @playwright/cli && \
    npx playwright install --with-deps chromium && \
    playwright-cli install --skills

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY vendor/ vendor/
COPY config/ config/
COPY src/ src/
COPY scripts/ scripts/

# Non-root user (Claude CLI refuses bypassPermissions as root)
RUN useradd -m -s /bin/bash nudge && \
    mkdir -p /data/claude-mem /data/sessions /data/nudges /data/proton-pass /data/browser-profile && \
    chown -R nudge:nudge /data /app

USER nudge

VOLUME /data

ENV TZ=Europe/Berlin
ENV PROTON_PASS_KEY_PROVIDER=fs
ENV PROTON_PASS_SESSION_DIR=/data/proton-pass

CMD ["/app/scripts/entrypoint.sh"]
