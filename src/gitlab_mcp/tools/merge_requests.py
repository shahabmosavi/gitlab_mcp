"""Merge request tools: list, read, diff, create, update, review, and merge."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import encode_id, get_client
from ._util import MR_FIELDS, slim_many


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_merge_requests(
        project_id: str | None = None,
        state: str = "opened",
        source_branch: str | None = None,
        target_branch: str | None = None,
        author_username: str | None = None,
        reviewer_username: str | None = None,
        labels: str | None = None,
        search: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List merge requests. Omit ``project_id`` to search across all projects.

        Args:
            state: "opened", "closed", "merged", or "all".
        """
        path = (
            f"projects/{encode_id(project_id)}/merge_requests"
            if project_id
            else "merge_requests"
        )
        items = await get_client().paginate(
            path,
            params={
                "state": state,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "author_username": author_username,
                "reviewer_username": reviewer_username,
                "labels": labels,
                "search": search,
            },
            max_items=limit,
        )
        return slim_many(items, MR_FIELDS)

    @mcp.tool()
    async def get_merge_request(project_id: str, mr_iid: int) -> dict[str, Any]:
        """Get full details for one merge request by its project-scoped IID."""
        return await get_client().get(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}"
        )

    @mcp.tool()
    async def get_merge_request_diffs(
        project_id: str, mr_iid: int
    ) -> list[dict[str, Any]]:
        """Get the per-file diffs (changes) of a merge request."""
        data = await get_client().get(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}/changes"
        )
        return data.get("changes", []) if isinstance(data, dict) else data

    @mcp.tool()
    async def create_merge_request(
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str | None = None,
        draft: bool = False,
        remove_source_branch: bool = True,
        reviewer_ids: list[int] | None = None,
        assignee_ids: list[int] | None = None,
        labels: str | None = None,
    ) -> dict[str, Any]:
        """Open a merge request from ``source_branch`` into ``target_branch``."""
        if draft and not title.lower().startswith("draft:"):
            title = f"Draft: {title}"
        return await get_client().post(
            f"projects/{encode_id(project_id)}/merge_requests",
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "remove_source_branch": remove_source_branch,
                "reviewer_ids": reviewer_ids,
                "assignee_ids": assignee_ids,
                "labels": labels,
            },
        )

    @mcp.tool()
    async def update_merge_request(
        project_id: str,
        mr_iid: int,
        title: str | None = None,
        description: str | None = None,
        target_branch: str | None = None,
        state_event: str | None = None,
        labels: str | None = None,
    ) -> dict[str, Any]:
        """Update a merge request. ``state_event`` = "close" or "reopen"."""
        return await get_client().put(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}",
            json={
                "title": title,
                "description": description,
                "target_branch": target_branch,
                "state_event": state_event,
                "labels": labels,
            },
        )

    @mcp.tool()
    async def merge_merge_request(
        project_id: str,
        mr_iid: int,
        merge_commit_message: str | None = None,
        squash: bool = False,
        should_remove_source_branch: bool | None = None,
        merge_when_pipeline_succeeds: bool = False,
    ) -> dict[str, Any]:
        """Accept (merge) a merge request."""
        return await get_client().put(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}/merge",
            json={
                "merge_commit_message": merge_commit_message,
                "squash": squash,
                "should_remove_source_branch": should_remove_source_branch,
                "merge_when_pipeline_succeeds": merge_when_pipeline_succeeds or None,
            },
        )

    @mcp.tool()
    async def approve_merge_request(project_id: str, mr_iid: int) -> dict[str, Any]:
        """Approve a merge request (requires the GitLab approvals feature)."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}/approve"
        )

    @mcp.tool()
    async def comment_merge_request(
        project_id: str, mr_iid: int, body: str
    ) -> dict[str, Any]:
        """Add a comment (note) to a merge request."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}/notes",
            json={"body": body},
        )

    @mcp.tool()
    async def list_merge_request_notes(
        project_id: str, mr_iid: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List comments (notes) on a merge request, oldest first."""
        return await get_client().paginate(
            f"projects/{encode_id(project_id)}/merge_requests/{mr_iid}/notes",
            params={"sort": "asc", "order_by": "created_at"},
            max_items=limit,
        )
