FROM python:3.12-slim

WORKDIR /app

# Install the package first (deps + entry point) using only the metadata it needs.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Default to stdio (run with `docker run -i`). For a networked deployment set
# MCP_TRANSPORT=streamable-http and publish the port (-p 8000:8000).
ENV MCP_TRANSPORT=stdio \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

EXPOSE 8000

ENTRYPOINT ["gitlab-mcp"]
