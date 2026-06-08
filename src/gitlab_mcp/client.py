"""Async GitLab REST API client shared by all MCP tools.

The server is multi-tenant: it carries no credentials of its own. Each caller
supplies their own GitLab token and instance URL per request, via HTTP headers:

    X-GitLab-Token: glpat-xxxx          (or  Authorization: Bearer glpat-xxxx)
    X-GitLab-Url:   https://gitlab.example.com

For local stdio use (where there are no HTTP headers), the GITLAB_TOKEN and
GITLAB_URL environment variables are used as a fallback.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import httpx

DEFAULT_URL = "https://gitlab.com"


class GitLabError(RuntimeError):
    """Raised when the GitLab API returns an error response."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"GitLab API error {status_code}: {body}")


def encode_id(value: str | int) -> str:
    """URL-encode a project/group identifier that may be a path like ``group/sub/project``."""
    return quote(str(value), safe="")


class GitLabClient:
    """Thin async wrapper over the GitLab REST API v4 for one (url, token) pair."""

    def __init__(self, base_url: str, token: str) -> None:
        self.api_url = f"{base_url}/api/v4"
        self._client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"PRIVATE-TOKEN": token},
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        raw: bool = False,
    ) -> Any:
        """Perform a single request. Returns parsed JSON, or raw text when ``raw`` is set."""
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        resp = await self._client.request(
            method, f"/{path.lstrip('/')}", params=params, json=json
        )
        if resp.status_code >= 400:
            try:
                body: Any = resp.json()
            except Exception:
                body = resp.text
            raise GitLabError(resp.status_code, body)
        if raw:
            return resp.text
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok", "status_code": resp.status_code}
        try:
            return resp.json()
        except Exception:
            return resp.text

    async def get(self, path: str, **kw: Any) -> Any:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> Any:
        return await self.request("POST", path, **kw)

    async def put(self, path: str, **kw: Any) -> Any:
        return await self.request("PUT", path, **kw)

    async def delete(self, path: str, **kw: Any) -> Any:
        return await self.request("DELETE", path, **kw)

    async def paginate(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        max_items: int = 100,
    ) -> list[Any]:
        """Follow keyset/offset pages until ``max_items`` results are collected."""
        params = {k: v for k, v in (params or {}).items() if v is not None}
        per_page = min(max_items, 100)
        params.setdefault("per_page", per_page)
        page = 1
        items: list[Any] = []
        while len(items) < max_items:
            resp = await self._client.get(
                f"/{path.lstrip('/')}", params={**params, "page": page}
            )
            if resp.status_code >= 400:
                try:
                    body: Any = resp.json()
                except Exception:
                    body = resp.text
                raise GitLabError(resp.status_code, body)
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            items.extend(batch)
            next_page = resp.headers.get("x-next-page")
            if not next_page:
                break
            page = int(next_page)
        return items[:max_items]

    async def aclose(self) -> None:
        await self._client.aclose()


def _normalize_url(raw: str) -> str:
    """Accept 'git.example.com', 'https://git.example.com', or a full '/api/v4' URL."""
    raw = raw.strip().rstrip("/")
    if raw.endswith("/api/v4"):
        raw = raw[: -len("/api/v4")]
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw.rstrip("/")


def _request_headers() -> Any:
    """Return the current request's headers (HTTP transports), or None for stdio."""
    try:
        from mcp.server.lowlevel.server import request_ctx

        request = request_ctx.get().request
    except (LookupError, AttributeError):
        return None
    return getattr(request, "headers", None)


def _resolve_credentials() -> tuple[str, str]:
    """Resolve (base_url, token) from request headers, falling back to env vars."""
    token: str | None = None
    url: str | None = None

    headers = _request_headers()
    if headers is not None:
        token = headers.get("x-gitlab-token")
        if not token:
            auth = headers.get("authorization") or ""
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()
        url = headers.get("x-gitlab-url") or headers.get("x-gitlab-domain")

    token = token or os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN")
    url = url or os.environ.get("GITLAB_URL") or DEFAULT_URL

    if not token:
        raise GitLabError(
            401,
            "No GitLab token provided. Send your personal access token in the "
            "'X-GitLab-Token' header (or 'Authorization: Bearer <token>'), and your "
            "instance in the 'X-GitLab-Url' header (e.g. https://gitlab.example.com).",
        )
    return _normalize_url(url), token


# One httpx client per (url, token) so connection pools are reused across calls.
_clients: dict[tuple[str, str], GitLabClient] = {}


def get_client() -> GitLabClient:
    """Return the client for the caller's credentials (resolved per request)."""
    base_url, token = _resolve_credentials()
    key = (base_url, token)
    client = _clients.get(key)
    if client is None:
        client = GitLabClient(base_url, token)
        _clients[key] = client
    return client
