FROM python:3.12-slim

# Node.js (for MCP server scripts) + Bun (for claude-mem worker) + curl (for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip && \
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

# Install claude-code CLI (required by Agent SDK)
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY vendor/ vendor/
COPY config/ config/
COPY src/ src/
COPY scripts/ scripts/

# Non-root user (Claude CLI refuses bypassPermissions as root)
RUN useradd -m -s /bin/bash nudge && \
    mkdir -p /data/claude-mem /data/sessions /data/nudges && \
    chown -R nudge:nudge /data /app

USER nudge

VOLUME /data

ENV TZ=Europe/Berlin

CMD ["/app/scripts/entrypoint.sh"]
