"""Async GitLab REST API client shared by all MCP tools."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import httpx


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
    """Thin async wrapper over the GitLab REST API v4."""

    def __init__(self, url: str | None = None, token: str | None = None) -> None:
        base = (url or os.environ.get("GITLAB_URL") or "https://gitlab.com").rstrip("/")
        self.token = (
            token
            or os.environ.get("GITLAB_TOKEN")
            or os.environ.get("GITLAB_PRIVATE_TOKEN")
        )
        if not self.token:
            raise RuntimeError(
                "A GitLab personal access token is required. "
                "Set GITLAB_TOKEN (and optionally GITLAB_URL for self-hosted instances)."
            )
        self.api_url = f"{base}/api/v4"
        self._client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"PRIVATE-TOKEN": self.token},
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


_client: GitLabClient | None = None


def get_client() -> GitLabClient:
    """Lazily construct the shared client (so the token is read at first use)."""
    global _client
    if _client is None:
        _client = GitLabClient()
    return _client
