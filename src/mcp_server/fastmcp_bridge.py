"""FastMCP bridge — MCP client for connecting to external MCP servers.

Uses fastmcp (22K⭐) to act as an MCP client, discovering and calling tools
on external MCP servers. Complements the built-in MCP server (21 tools).
"""

from __future__ import annotations

import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


class FastMCPBridge:
    """MCP client bridge using fastmcp.

    Enables C4REQBER to connect to external MCP servers and use their tools.
    Supports stdio transport for local MCP servers and SSE for remote.
    """

    def __init__(self) -> None:
        self._client = None
        self._tools: dict[str, Any] = {}
        self._connected_servers: list[str] = []

    @property
    def available(self) -> bool:
        try:
            import fastmcp

            return True
        except ImportError:
            return False

    async def connect_stdio(self, command: str, args: list[str] | None = None) -> bool:
        """Connect to a local MCP server via stdio."""
        if not self.available:
            return False
        try:
            import fastmcp

            self._client = fastmcp.Client(
                transport="stdio",
                command=command,
                args=args or [],
            )
            await self._client.connect()
            tools = await self._client.list_tools()
            for tool in tools:
                self._tools[tool.name] = tool
            self._connected_servers.append(f"stdio:{command}")
            return True
        except Exception as e:
            logger.debug("FastMCP stdio connect failed: %s", e)
            return False

    async def connect_sse(self, url: str) -> bool:
        """Connect to a remote MCP server via SSE."""
        if not self.available:
            return False
        try:
            import fastmcp

            self._client = fastmcp.Client(transport="sse", url=url)
            await self._client.connect()
            tools = await self._client.list_tools()
            for tool in tools:
                self._tools[tool.name] = tool
            self._connected_servers.append(url)
            return True
        except Exception as e:
            logger.debug("FastMCP SSE connect failed: %s", e)
            return False

    async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """Call a tool on the connected MCP server."""
        if not self._client:
            return {"error": "Not connected"}
        try:
            return await self._client.call_tool(name, arguments or {})
        except Exception as e:
            return {"error": str(e)}

    async def discover_servers(self) -> list[dict]:
        """Scan for available MCP servers via smithery if available."""
        servers = []
        # Scan common MCP config locations
        config_paths = [
            os.path.expanduser("~/.mcp.json"),
            os.path.expanduser("~/.config/mcp/servers.json"),
            ".mcp.json",
        ]
        import json as _json

        for path in config_paths:
            if os.path.exists(path):
                try:
                    cfg = _json.loads(open(path).read())
                    if "mcpServers" in cfg:
                        for name, srv in cfg["mcpServers"].items():
                            servers.append({"name": name, "config": srv, "source": path})
                except Exception as _exc:
                    logger.debug("swallowed exception: %s", _exc, exc_info=True)
        return servers

    @property
    def external_tools(self) -> dict[str, Any]:
        return dict(self._tools)

    @property
    def connected(self) -> bool:
        return len(self._connected_servers) > 0

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.close()
            except Exception as _exc:
                logger.debug("swallowed exception: %s", _exc, exc_info=True)
            self._client = None
            self._tools = {}
            self._connected_servers = []

    async def test_connection(self) -> dict[str, Any]:
        if not self.available:
            return {"healthy": False, "error": "fastmcp not installed"}
        servers = await self.discover_servers()
        return {
            "healthy": True,
            "connected": self.connected,
            "connected_servers": self._connected_servers,
            "external_tools_count": len(self._tools),
            "discovered_servers": len(servers),
        }
