# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Model Context Protocol (MCP) server exposing the GitLab REST API v4, authenticated with a personal access token. It speaks MCP over stdio and is meant to be launched by an MCP client (Claude Code/Desktop).

## Commands

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                      # install in editable mode

gitlab-mcp                            # run the server (stdio); needs GITLAB_TOKEN set
python -m gitlab_mcp                  # equivalent

# Inspect registered tools without a live token:
GITLAB_TOKEN=dummy python -c "import asyncio; from gitlab_mcp.server import mcp; \
print(asyncio.run(mcp.list_tools()))"
```

There is no test suite or linter configured yet. The package imports and lists tools without any credentials — they're only needed when a tool actually calls the API.

### Authentication (multi-tenant)

The server holds **no credentials**. `client.py::_resolve_credentials()` resolves a `(url, token)` pair **per request**: first from HTTP headers (`X-GitLab-Token` / `Authorization: Bearer`, and `X-GitLab-Url`), then falling back to the `GITLAB_TOKEN` / `GITLAB_URL` env vars (for local stdio use). Headers are read off the `request_ctx` contextvar from `mcp.server.lowlevel.server` (set by the streamable-http transport). `get_client()` caches one `httpx.AsyncClient` per `(url, token)`. This is why a deployed server can serve many users — each acts as themselves. Don't reintroduce a single global token.

## Architecture

The server is built on `FastMCP` (`mcp.server.fastmcp`). The flow is:

- `server.py` creates the single `FastMCP("gitlab")` instance and calls `tools.register_all(mcp)`.
- `tools/__init__.py` imports each tool submodule and calls its `register(mcp)`. **To add tools, add a module under `tools/` with a `register(mcp)` function and append it to the tuple in `register_all`.**
- Every tool is an `async` function decorated with `@mcp.tool()`. Its docstring and type hints become the tool's MCP schema, so keep them accurate — that's the only thing the model sees.
- All tools share one `GitLabClient` (`client.py`) obtained via `get_client()`, a lazy singleton holding a single `httpx.AsyncClient`. Do not construct clients elsewhere.

`GitLabClient` is deliberately thin: `request/get/post/put/delete` for single calls and `paginate()` which follows the `X-Next-Page` header up to `max_items`. `request(..., raw=True)` returns text (used for job logs). Errors >=400 raise `GitLabError`.

### Conventions that matter

- **`project_id` / group ids can be a path** (`group/sub/project`), so always run them through `encode_id()` (URL-encodes with `safe=""`) when interpolating into a path segment.
- **Issues and merge requests are addressed by project-scoped IID**, not global ID. Tool params are named `issue_iid` / `mr_iid` accordingly.
- **List endpoints trim their output** via `pick`/`slim_many` and the `*_FIELDS` tuples in `tools/_util.py`, to keep responses small. When adding a list tool, add a field tuple rather than returning raw objects. Detail/get tools return the full object.
- **`tools/generic.py` (`gitlab_api`) is the escape hatch** — a raw passthrough to any endpoint. Prefer adding a typed tool for common operations, but anything is reachable through it, so don't feel obliged to wrap every endpoint.
- `None`-valued query params and JSON fields are dropped by the client, so tools can pass optional args straight through without conditionals.
