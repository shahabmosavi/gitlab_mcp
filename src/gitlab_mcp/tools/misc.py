"""User identity and global search tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import encode_id, get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_current_user() -> dict[str, Any]:
        """Return the user that owns the configured personal access token."""
        return await get_client().get("user")

    @mcp.tool()
    async def search_users(
        search: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search users by name, username, or email."""
        return await get_client().paginate(
            "users", params={"search": search}, max_items=limit
        )

    @mcp.tool()
    async def search(
        scope: str,
        search: str,
        project_id: str | None = None,
        limit: int = 20,
    ) -> list[Any]:
        """Global or project-scoped search.

        Args:
            scope: What to search — "projects", "issues", "merge_requests",
                   "milestones", "blobs", "commits", "users", "wiki_blobs", "notes".
            search: The query string.
            project_id: If set, search is scoped to this project.
        """
        path = (
            f"projects/{encode_id(project_id)}/search"
            if project_id
            else "search"
        )
        return await get_client().paginate(
            path, params={"scope": scope, "search": search}, max_items=limit
        )
