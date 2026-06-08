"""Repository tools: branches, files, commits, and tags."""

from __future__ import annotations

import base64
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import encode_id, get_client


def register(mcp: FastMCP) -> None:
    # --- branches -----------------------------------------------------------
    @mcp.tool()
    async def list_branches(
        project_id: str, search: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List repository branches."""
        return await get_client().paginate(
            f"projects/{encode_id(project_id)}/repository/branches",
            params={"search": search},
            max_items=limit,
        )

    @mcp.tool()
    async def create_branch(
        project_id: str, branch: str, ref: str
    ) -> dict[str, Any]:
        """Create ``branch`` from ``ref`` (an existing branch name, tag, or commit SHA)."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/repository/branches",
            params={"branch": branch, "ref": ref},
        )

    @mcp.tool()
    async def delete_branch(project_id: str, branch: str) -> dict[str, Any]:
        """Delete a branch."""
        return await get_client().delete(
            f"projects/{encode_id(project_id)}/repository/branches/{encode_id(branch)}"
        )

    # --- files --------------------------------------------------------------
    @mcp.tool()
    async def get_file(
        project_id: str, file_path: str, ref: str = "HEAD"
    ) -> dict[str, Any]:
        """Read a file's decoded text content at ``ref`` (branch, tag, or SHA)."""
        data = await get_client().get(
            f"projects/{encode_id(project_id)}/repository/files/{encode_id(file_path)}",
            params={"ref": ref},
        )
        content = data.get("content")
        if content and data.get("encoding") == "base64":
            try:
                data["content"] = base64.b64decode(content).decode("utf-8")
                data["encoding"] = "text"
            except UnicodeDecodeError:
                data["content"] = "<binary file: content omitted>"
        return data

    @mcp.tool()
    async def create_or_update_file(
        project_id: str,
        file_path: str,
        branch: str,
        content: str,
        commit_message: str,
        update: bool = False,
        start_branch: str | None = None,
    ) -> dict[str, Any]:
        """Create (or, with ``update=True``, overwrite) a single file in one commit."""
        method = "PUT" if update else "POST"
        return await get_client().request(
            method,
            f"projects/{encode_id(project_id)}/repository/files/{encode_id(file_path)}",
            json={
                "branch": branch,
                "content": content,
                "commit_message": commit_message,
                "start_branch": start_branch,
            },
        )

    @mcp.tool()
    async def delete_file(
        project_id: str, file_path: str, branch: str, commit_message: str
    ) -> dict[str, Any]:
        """Delete a file in a single commit."""
        return await get_client().delete(
            f"projects/{encode_id(project_id)}/repository/files/{encode_id(file_path)}",
            json={"branch": branch, "commit_message": commit_message},
        )

    @mcp.tool()
    async def list_repository_tree(
        project_id: str,
        path: str | None = None,
        ref: str = "HEAD",
        recursive: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List files and directories in the repository tree."""
        return await get_client().paginate(
            f"projects/{encode_id(project_id)}/repository/tree",
            params={"path": path, "ref": ref, "recursive": recursive or None},
            max_items=limit,
        )

    # --- commits ------------------------------------------------------------
    @mcp.tool()
    async def list_commits(
        project_id: str,
        ref_name: str | None = None,
        path: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List commits. ``since``/``until`` are ISO 8601 timestamps."""
        return await get_client().paginate(
            f"projects/{encode_id(project_id)}/repository/commits",
            params={"ref_name": ref_name, "path": path, "since": since, "until": until},
            max_items=limit,
        )

    @mcp.tool()
    async def get_commit_diff(project_id: str, sha: str) -> list[dict[str, Any]]:
        """Get the per-file diff of a single commit."""
        return await get_client().get(
            f"projects/{encode_id(project_id)}/repository/commits/{encode_id(sha)}/diff"
        )

    @mcp.tool()
    async def create_commit(
        project_id: str,
        branch: str,
        commit_message: str,
        actions: list[dict[str, Any]],
        start_branch: str | None = None,
    ) -> dict[str, Any]:
        """Commit multiple file changes atomically.

        Each action is a dict like:
            {"action": "create"|"update"|"delete"|"move", "file_path": "...",
             "content": "...", "previous_path": "..." (for move)}
        """
        return await get_client().post(
            f"projects/{encode_id(project_id)}/repository/commits",
            json={
                "branch": branch,
                "commit_message": commit_message,
                "actions": actions,
                "start_branch": start_branch,
            },
        )

    # --- tags ---------------------------------------------------------------
    @mcp.tool()
    async def list_tags(
        project_id: str, search: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List repository tags."""
        return await get_client().paginate(
            f"projects/{encode_id(project_id)}/repository/tags",
            params={"search": search},
            max_items=limit,
        )

    @mcp.tool()
    async def create_tag(
        project_id: str, tag_name: str, ref: str, message: str | None = None
    ) -> dict[str, Any]:
        """Create a tag at ``ref``."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/repository/tags",
            params={"tag_name": tag_name, "ref": ref, "message": message},
        )
