"""Tool registration. Each submodule exposes ``register(mcp)``."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import generic, issues, merge_requests, misc, pipelines, projects, repository


def register_all(mcp: FastMCP) -> None:
    for module in (
        generic,
        projects,
        issues,
        merge_requests,
        repository,
        pipelines,
        misc,
    ):
        module.register(mcp)
