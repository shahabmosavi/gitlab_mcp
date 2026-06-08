"""GitLab MCP server entry point."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .tools import register_all

mcp = FastMCP(
    "gitlab",
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", "8000")),
    instructions=(
        "Tools for the GitLab REST API, authenticated with a personal access token. "
        "Most tools accept a `project_id` that may be a numeric ID or a URL path like "
        "'group/subgroup/project'. Issues and merge requests are addressed by their "
        "project-scoped IID, not their global ID. For anything without a dedicated "
        "tool, use `gitlab_api` to call the endpoint directly."
    ),
)

register_all(mcp)
