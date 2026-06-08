"""CI/CD tools: pipelines and jobs."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import encode_id, get_client
from ._util import JOB_FIELDS, PIPELINE_FIELDS, slim_many


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_pipelines(
        project_id: str,
        ref: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List pipelines. ``status`` e.g. "running", "success", "failed", "canceled"."""
        items = await get_client().paginate(
            f"projects/{encode_id(project_id)}/pipelines",
            params={"ref": ref, "status": status},
            max_items=limit,
        )
        return slim_many(items, PIPELINE_FIELDS)

    @mcp.tool()
    async def get_pipeline(project_id: str, pipeline_id: int) -> dict[str, Any]:
        """Get details for one pipeline."""
        return await get_client().get(
            f"projects/{encode_id(project_id)}/pipelines/{pipeline_id}"
        )

    @mcp.tool()
    async def create_pipeline(
        project_id: str, ref: str, variables: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Trigger a new pipeline on ``ref``. ``variables`` is a name->value map."""
        payload: dict[str, Any] = {"ref": ref}
        if variables:
            payload["variables"] = [
                {"key": k, "value": v} for k, v in variables.items()
            ]
        return await get_client().post(
            f"projects/{encode_id(project_id)}/pipeline", json=payload
        )

    @mcp.tool()
    async def retry_pipeline(project_id: str, pipeline_id: int) -> dict[str, Any]:
        """Retry the failed/canceled jobs of a pipeline."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/pipelines/{pipeline_id}/retry"
        )

    @mcp.tool()
    async def cancel_pipeline(project_id: str, pipeline_id: int) -> dict[str, Any]:
        """Cancel a running pipeline."""
        return await get_client().post(
            f"projects/{encode_id(project_id)}/pipelines/{pipeline_id}/cancel"
        )

    @mcp.tool()
    async def list_pipeline_jobs(
        project_id: str, pipeline_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List the jobs of a pipeline."""
        items = await get_client().paginate(
            f"projects/{encode_id(project_id)}/pipelines/{pipeline_id}/jobs",
            max_items=limit,
        )
        return slim_many(items, JOB_FIELDS)

    @mcp.tool()
    async def get_job_log(project_id: str, job_id: int) -> str:
        """Get the trace (console log) of a job."""
        return await get_client().get(
            f"projects/{encode_id(project_id)}/jobs/{job_id}/trace", raw=True
        )
