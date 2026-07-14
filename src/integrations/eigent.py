"""Eigent Desktop integration.

Eigent (github.com/eigent-ai/eigent) is an Electron+FastAPI+React desktop app
for multi-agent AI workforce. Built on CAMEL-AI framework.

Key details:
- Backend: FastAPI + Uvicorn (Python) on localhost
- Frontend: Electron + React + TypeScript
- Auth: OAuth 2.0 (Passlib)
- MCP tools: web browsing, code execution, Notion, Google, Slack, etc.
- Custom model support: vLLM, Ollama, LM Studio

This client discovers the locally running Eigent backend and connects to it.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class EigentDesktop:
    """Client for local Eigent Cowork desktop application.

    Auto-discovers the Eigent backend via common config paths
    and environment variables. Supports querying the Eigent
    FastAPI backend and managing the desktop app lifecycle.
    """

    def __init__(self) -> None:
        self.connected = False
        self.api_port = self._discover_port()
        self.api_url = f"http://127.0.0.1:{self.api_port}" if self.api_port else ""
        self.config_path = self._discover_config_dir()

    def _discover_port(self) -> int | None:
        """Discover Eigent backend API port."""
        # Environment variable
        env_port = os.getenv("EIGENT_API_PORT")
        if env_port:
            try:
                return int(env_port)
            except ValueError:
                pass

        # Check common config locations
        candidates = [
            Path.home() / ".eigent" / "backend" / ".env",
            Path.home() / ".eigent" / ".env",
            Path("backend") / ".env.development",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    content = candidate.read_text()
                    for line in content.split("\n"):
                        line = line.strip()
                        if line.startswith("EIGENT_API_PORT=") or line.startswith("PORT="):
                            port_str = line.split("=", 1)[1].strip().strip('"')
                            return int(port_str)
                except (ValueError, OSError):
                    pass

        # Default common port for Eigent backend
        return 3000

    def _discover_config_dir(self) -> Path:
        """Find the Eigent configuration directory."""
        candidates = [
            Path.home() / ".eigent",
            Path(os.getenv("EIGENT_HOME", "")),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return Path.home() / ".eigent"

    async def connect(self) -> bool:
        """Connect to local Eigent backend."""
        if not self.api_port:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.api_url}/api/health")
                if resp.status_code == 200:
                    self.connected = True
                    return True
        except Exception:
            pass
        return False

    async def query(self, prompt: str) -> dict[str, Any]:
        """Send a task to Eigent's workforce."""
        if not self.connected and not await self.connect():
            return {"error": "Eigent desktop not running or not reachable"}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.api_url}/api/tasks",
                    json={"prompt": prompt},
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def list_agents(self) -> list[dict[str, Any]]:
        """List active Eigent agents."""
        if not self.connected and not await self.connect():
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.api_url}/api/agents")
                if resp.status_code == 200:
                    return resp.json().get("agents", [])
                return []
        except Exception:
            return []

    async def list_mcp_tools(self) -> list[dict[str, Any]]:
        """List installed MCP tools."""
        if not self.connected and not await self.connect():
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.api_url}/api/mcp/tools")
                if resp.status_code == 200:
                    return resp.json().get("tools", [])
                return []
        except Exception:
            return []

    def start_desktop(self) -> bool:
        """Attempt to start Eigent desktop app."""
        # Try npm run dev from the eigent project directory
        candidates = [
            Path.home() / "eigent",
            Path(os.getenv("EIGENT_HOME", ".")),
        ]
        for project_dir in candidates:
            package_json = project_dir / "package.json"
            if not package_json.exists():
                continue
            try:
                subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(project_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            except (FileNotFoundError, OSError):
                continue
        return False

    async def test_connection(self) -> dict[str, Any]:
        """Test connectivity to Eigent backend."""
        connected = await self.connect()
        if connected:
            agents = await self.list_agents()
            return {"healthy": True, "agents_found": len(agents), "port": self.api_port}
        return {"healthy": False, "port": self.api_port, "error": "Backend not reachable"}
