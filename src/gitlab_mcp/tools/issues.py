"""Issue tools: list, read, create, update, and comment."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import encode_id, get_client
from ._util import ISSUE_FIELDS, slim_many


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_issues(
        project_id: str | None = None,
        state: str = "opened",
        labels: str | None = None,
        assignee_username: str | None = None,
        search: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List issues. Omit ``project_id`` to search issues across all projects.

        Args:
            state: "opened", "closed", or "all".
            labels: Comma-separated label names.
            assignee_username: Filter by assignee.
            search: Full-text search over title and description.
        """
        path = (
            f"projects/{encode_id(project_id)}/issues" if project_id else "issues"
        )
        items = await get_client().paginate(
            path,
            params={
                "state": state,
                "labels": labels,
                "assignee_username": assignee_username,
                "search": search,
            },
            max_items=limit,
        )
        return slim_many(items, ISSUE_FIELDS)

    @mcp.tool()
    async def get_issue(project_id: str, issue_iid: int) -> dict[str, Any]:
        """Get one issue by its project-scoped IID."""
        return await get_client().get(
            f"projects/{encode_id(project_id)}/issues/{issue_iid}"
        )

    @mcp.tool()
    async def create_issue(
        project_id: str,
        title: str,
        description: str | None = None,
        labels: str | None = None,
        assignee_ids: list[int] | None = None,
        milestone_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an issue in a project. ``labels`` is comma-separated."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/issues",
            json={
                "title": title,
                "description": description,
                "labels": labels,
                "assignee_ids": assignee_ids,
                "milestone_id": milestone_id,
            },
        )

    @mcp.tool()
    async def update_issue(
        project_id: str,
        issue_iid: int,
        title: str | None = None,
        description: str | None = None,
        state_event: str | None = None,
        labels: str | None = None,
        assignee_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Update an issue. Use ``state_event`` = "close" or "reopen" to change state."""
        return await get_client().put(
            f"projects/{encode_id(project_id)}/issues/{issue_iid}",
            json={
                "title": title,
                "description": description,
                "state_event": state_event,
                "labels": labels,
                "assignee_ids": assignee_ids,
            },
        )

    @mcp.tool()
    async def comment_issue(
        project_id: str, issue_iid: int, body: str
    ) -> dict[str, Any]:
        """Add a comment (note) to an issue."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/issues/{issue_iid}/notes",
            json={"body": body},
        )

    @mcp.tool()
    async def list_issue_notes(
        project_id: str, issue_iid: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List comments (notes) on an issue, oldest first."""
        return await get_client().paginate(
            f"projects/{encode_id(project_id)}/issues/{issue_iid}/notes",
            params={"sort": "asc", "order_by": "created_at"},
            max_items=limit,
        )
