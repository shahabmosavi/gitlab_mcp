"""Run the GitLab MCP server.

Transport is chosen via the MCP_TRANSPORT env var:
  - "stdio" (default): launched as a subprocess by a local MCP client.
  - "streamable-http" / "sse": run as a networked server (set MCP_HOST/MCP_PORT),
    suitable for deploying on a server and connecting to over the network.
"""

from __future__ import annotations

import os

from .server import mcp


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
