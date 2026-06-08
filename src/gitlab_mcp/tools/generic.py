"""A raw passthrough to any GitLab REST endpoint — the escape hatch that makes
this server able to do *everything* the API supports, even without a dedicated tool."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def gitlab_api(
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Call any GitLab REST API v4 endpoint directly.

        Use this for anything the dedicated tools don't cover (webhooks, members,
        variables, environments, deploy keys, etc.).

        Args:
            method: HTTP method, e.g. "GET", "POST", "PUT", "DELETE".
            path: API path relative to /api/v4, e.g. "projects/42/variables".
                  Remember to URL-encode project paths: "projects/group%2Fproject".
            params: Query-string parameters.
            body: JSON request body for POST/PUT.
        """
        return await get_client().request(
            method.upper(), path, params=params, json=body
        )
