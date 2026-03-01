FROM python:3.12-slim

# Node.js for MCP servers (e.g. Todoist via npx)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install claude-code CLI (required by Agent SDK)
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY config/ config/
COPY src/ src/

RUN mkdir -p /data/sessions

VOLUME /data

ENV TZ=Europe/Berlin

CMD ["python", "-m", "src.main"]
