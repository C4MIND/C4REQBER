"""LM Studio CLI bridge — model management + OpenAI-compatible API provider.

Integrates LM Studio CLI (lms) for:
- Model listing, loading, unloading
- Automatic model selection based on availability
- GPU/CPU device awareness
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Any


logger = logging.getLogger(__name__)

_LMS_PATH = os.path.expanduser("~/.lmstudio/bin/lms")


class LMStudioCLI:
    """LM Studio CLI bridge for model management."""

    def __init__(self) -> None:
        self.lms = _LMS_PATH if os.path.exists(_LMS_PATH) else "lms"

    @property
    def available(self) -> bool:
        return os.path.exists(self.lms) or shutil.which(self.lms) is not None

    def _run(self, *args: str, timeout: int = 30) -> tuple[int, str, str]:
        try:
            r = subprocess.run([self.lms, *args], capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return 1, "", str(e)

    def status(self) -> dict[str, Any]:
        """Get LM Studio server status."""
        code, out, err = self._run("status")
        lines = out.split("\n")
        result: dict[str, Any] = {"running": False, "port": 1234, "models_loaded": []}
        for line in lines:
            line = line.strip()
            if line.startswith("Server:"):
                result["running"] = "ON" in line
            elif ":" in line and "Models Loaded" not in line and "(" in line:
                result["models_loaded"].append(line)
        return result

    def list_models(self) -> list[dict[str, str]]:
        """List all available LM Studio models."""
        code, out, _ = self._run("ls")
        models = []
        for line in out.split("\n"):
            line = line.strip()
            if (
                not line
                or line.startswith("You have")
                or line.startswith("LLM")
                or line.startswith("───")
            ):
                continue
            parts = line.split()
            if len(parts) >= 3:
                models.append(
                    {
                        "name": parts[0],
                        "params": parts[1] if len(parts) > 1 else "",
                        "size": parts[-2] + " " + parts[-1] if len(parts) > 3 else "",
                    }
                )
        return models

    def load_model(self, model_id: str) -> dict[str, Any]:
        """Load a model via LM Studio CLI."""
        code, out, err = self._run("load", model_id, timeout=120)
        if "loaded successfully" in out.lower() or "loaded successfully" in err.lower():
            return {"success": True, "model": model_id, "output": out or err}
        return {"success": False, "model": model_id, "error": err or out}

    def unload_model(self, model_id: str = "all") -> dict[str, Any]:
        """Unload models."""
        code, out, err = self._run("unload", model_id)
        return {"success": code == 0, "model": model_id, "output": out or err}

    def get_current_model(self) -> str | None:
        """Get the currently loaded model ID."""
        s = self.status()
        if s["models_loaded"]:
            return s["models_loaded"][0]
        return None

    async def test_connection(self) -> dict[str, Any]:
        s = self.status()
        models = self.list_models() if s["running"] else []
        return {
            "healthy": s["running"],
            "port": s.get("port"),
            "models_available": len(models),
            "models_loaded": len(s.get("models_loaded", [])),
            "current_model": self.get_current_model(),
        }
