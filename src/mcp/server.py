# src/mcp/server.py — DEPRECATED, use src.mcp_server.server
import warnings


warnings.warn("src.mcp.server is deprecated, use src.mcp_server.server", DeprecationWarning, stacklevel=2)
from src.mcp_server.server import *  # type: ignore[no-redef]  # noqa: F403
