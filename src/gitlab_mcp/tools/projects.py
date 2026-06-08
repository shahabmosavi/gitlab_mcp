"""Project and group discovery tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import encode_id, get_client
from ._util import PROJECT_FIELDS, slim_many


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_projects(
        search: str | None = None,
        membership: bool = True,
        owned: bool = False,
        visibility: str | None = None,
        order_by: str = "last_activity_at",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List projects visible to the authenticated user.

        Args:
            search: Filter by name/path substring.
            membership: Only projects the user is a member of (default true).
            owned: Only projects the user owns.
            visibility: "private", "internal", or "public".
            order_by: "id", "name", "created_at", "updated_at", "last_activity_at".
            limit: Max projects to return.
        """
        items = await get_client().paginate(
            "projects",
            params={
                "search": search,
                "membership": membership or None,
                "owned": owned or None,
                "visibility": visibility,
                "order_by": order_by,
            },
            max_items=limit,
        )
        return slim_many(items, PROJECT_FIELDS)

    @mcp.tool()
    async def get_project(project_id: str) -> dict[str, Any]:
        """Get full details for one project by numeric ID or "namespace/path"."""
        return await get_client().get(f"projects/{encode_id(project_id)}")

    @mcp.tool()
    async def create_project(
        name: str,
        namespace_id: int | None = None,
        visibility: str = "private",
        description: str | None = None,
        initialize_with_readme: bool = False,
    ) -> dict[str, Any]:
        """Create a new project. ``namespace_id`` targets a group; omit for the user's namespace."""
        return await get_client().post(
            "projects",
            json={
                "name": name,
                "namespace_id": namespace_id,
                "visibility": visibility,
                "description": description,
                "initialize_with_readme": initialize_with_readme,
            },
        )

    @mcp.tool()
    async def list_groups(
        search: str | None = None, owned: bool = False, limit: int = 20
    ) -> list[dict[str, Any]]:
        """List groups visible to the authenticated user."""
        return await get_client().paginate(
            "groups",
            params={"search": search, "owned": owned or None},
            max_items=limit,
        )

    @mcp.tool()
    async def list_group_projects(
        group_id: str, search: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """List projects belonging to a group (by numeric ID or full path)."""
        items = await get_client().paginate(
            f"groups/{encode_id(group_id)}/projects",
            params={"search": search, "include_subgroups": True},
            max_items=limit,
        )
        return slim_many(items, PROJECT_FIELDS)
