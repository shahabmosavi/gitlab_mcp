# GitLab MCP

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes the
GitLab REST API to MCP clients (Claude Code, Claude Desktop, etc.). Authenticate once
with a personal access token and the assistant can drive projects, issues, merge
requests, repositories, and CI/CD pipelines.

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create a personal access token in GitLab (**Settings → Access Tokens**) with the
**`api`** scope, then set it in the environment:

```sh
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
# For self-hosted instances only:
# export GITLAB_URL=https://gitlab.example.com
```

## Run

```sh
gitlab-mcp          # console script (installed by pip)
# or
python -m gitlab_mcp
```

The server speaks MCP over stdio.

## Docker / deploy on a server

CI publishes an image to GitHub Container Registry on every push to `main` and on
version tags:

```sh
docker pull ghcr.io/shahabmosavi/gitlab_mcp:main
```

Run it as a **networked** MCP server (HTTP transport) on your server:

```sh
docker run -d --name gitlab-mcp -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e GITLAB_TOKEN=glpat-xxxxxxxx \
  -e GITLAB_URL=https://git.dctm.dev \
  ghcr.io/shahabmosavi/gitlab_mcp:main
```

Or run it as a local **stdio** server (the default) straight from the image:

```sh
docker run -i --rm -e GITLAB_TOKEN=glpat-xxxx -e GITLAB_URL=https://git.dctm.dev \
  ghcr.io/shahabmosavi/gitlab_mcp:main
```

| Env var | Default | Purpose |
| --- | --- | --- |
| `MCP_TRANSPORT` | `stdio` | `stdio`, `streamable-http`, or `sse` |
| `MCP_HOST` | `0.0.0.0` | Bind host for networked transports |
| `MCP_PORT` | `8000` | Bind port for networked transports |

## Use with Claude Code

```sh
claude mcp add gitlab --env GITLAB_TOKEN=glpat-xxxx -- gitlab-mcp
```

Or add it manually to your MCP client config:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "gitlab-mcp",
      "env": { "GITLAB_TOKEN": "glpat-xxxxxxxxxxxxxxxxxxxx" }
    }
  }
}
```

(Use the absolute path to the `gitlab-mcp` binary inside `.venv/bin/` if it isn't on
your PATH.)

## Tools

| Area | Tools |
| --- | --- |
| Projects/Groups | `list_projects`, `get_project`, `create_project`, `list_groups`, `list_group_projects` |
| Issues | `list_issues`, `get_issue`, `create_issue`, `update_issue`, `comment_issue`, `list_issue_notes` |
| Merge requests | `list_merge_requests`, `get_merge_request`, `get_merge_request_diffs`, `create_merge_request`, `update_merge_request`, `merge_merge_request`, `approve_merge_request`, `comment_merge_request`, `list_merge_request_notes` |
| Repository | `list_branches`, `create_branch`, `delete_branch`, `get_file`, `create_or_update_file`, `delete_file`, `list_repository_tree`, `list_commits`, `get_commit_diff`, `create_commit`, `list_tags`, `create_tag` |
| CI/CD | `list_pipelines`, `get_pipeline`, `create_pipeline`, `retry_pipeline`, `cancel_pipeline`, `list_pipeline_jobs`, `get_job_log` |
| Misc | `get_current_user`, `search_users`, `search` |
| Escape hatch | `gitlab_api` — call **any** GitLab REST endpoint directly |

Whatever isn't covered by a dedicated tool is reachable through `gitlab_api`, so the
server can do anything your token is allowed to do.

### Notes

- `project_id` accepts a numeric ID **or** a URL path like `group/subgroup/project`.
- Issues and merge requests are addressed by their project-scoped **IID** (the number
  in the web URL), not their global ID.
- List tools trim responses to the most useful fields to keep them compact; use
  `gitlab_api` when you need the full, raw payload.
