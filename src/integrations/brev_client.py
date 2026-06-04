"""NVIDIA Brev CLI Integration — GPU cloud instances via subprocess.

Requires: `brew install brevdev/homebrew-brev/brev` and `brev login`

Auto-selects cheapest GPU by default:
  - T4  (~$0.50/hr) — dev / small inference
  - L4  (~$0.75/hr) — inference / video
  - V100 (~$1.00/hr) — training

Usage in TUI: press [G] to auto-deploy cheapest GPU.
"""
from __future__ import annotations

import subprocess
from typing import Any


# GPU type → approximate hourly cost (USD) for auto-selection
GPU_COSTS = {
    "nvidia-tesla-t4": 0.50,
    "nvidia-l4": 0.75,
    "nvidia-tesla-v100": 1.00,
    "nvidia-a10g": 1.20,
    "nvidia-rtx-4000-ada": 1.50,
    "nvidia-l40s": 2.50,
    "nvidia-a100": 3.00,
    "nvidia-a100-80gb": 4.00,
    "nvidia-h100": 8.00,
}

CHEAPEST_GPUS = ["nvidia-tesla-t4", "nvidia-l4", "nvidia-tesla-v100"]


class BrevClient:
    """NVIDIA Brev CLI wrapper for GPU instance management."""

    def __init__(self) -> None:
        self._check_cli()
        self.instance_name = "reqber-gpu"

    def _check_cli(self) -> None:
        result = subprocess.run(["brev", "--version"], capture_output=True, text=True, timeout=10)
        self.cli_available = result.returncode == 0
        self.logged_in = self._check_login()

    def _check_login(self) -> bool:
        """Check if user is logged in to Brev."""
        if not self.cli_available:
            return False
        result = subprocess.run(
            ["brev", "list"],
            capture_output=True, text=True,
            input="n\n",  # answer 'n' to login prompt
            timeout=15,
        )
        # If logged in, list works. If not, it prompts for login.
        return "would you like to log in" not in result.stderr.lower()

    def status(self) -> dict[str, Any]:
        """Return status for dashboard."""
        if not self.cli_available:
            return {
                "name": "NVIDIA Brev",
                "enabled": False,
                "provider": "brev",
                "icon": "🟢",
                "note": "install: brew install brevdev/homebrew-brev/brev",
            }
        if not self.logged_in:
            return {
                "name": "NVIDIA Brev",
                "enabled": True,
                "provider": "brev",
                "icon": "🟡",
                "note": "run: brev login",
            }
        return {
            "name": "NVIDIA Brev",
            "enabled": True,
            "provider": "brev",
            "icon": "🟢",
            "note": "ready — press [G] to deploy",
        }

    def list_instances(self) -> list[dict[str, Any]]:
        """List existing Brev instances."""
        if not self.logged_in:
            return []
        result = subprocess.run(
            ["brev", "list", "--json"],
            capture_output=True, text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return []
        try:
            import json
            return json.loads(result.stdout)
        except (ValueError, TypeError, json.JSONDecodeError):
            return []

    def start_cheapest(self, gpu_type: str | None = None) -> dict[str, Any]:
        """Start cheapest available GPU instance.

        If gpu_type is None, tries CHEAPEST_GPUS in order.
        Returns {"ok": bool, "name": str, "gpu": str, "message": str}
        """
        if not self.logged_in:
            return {"ok": False, "message": "Not logged in. Run: brev login"}

        gpus_to_try = [gpu_type] if gpu_type else CHEAPEST_GPUS

        for gpu in gpus_to_try:
            machine = "n1-standard-4"
            if "a100" in gpu or "h100" in gpu:
                machine = "n1-highmem-8"

            gpu_spec = f"{machine}:{gpu}:1"
            result = subprocess.run(
                ["brev", "start", "--name", self.instance_name,
                 "--gpu", gpu_spec, "--empty", "--detached"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                cost = GPU_COSTS.get(gpu, "unknown")
                return {
                    "ok": True,
                    "name": self.instance_name,
                    "gpu": gpu,
                    "cost_hr": cost,
                    "message": f"Deployed {gpu} @ ~${cost}/hr",
                }
            elif "cloudCredId" in result.stderr or "workspaceGroupId" in result.stderr:
                return {
                    "ok": False,
                    "message": "Cloud credentials not configured. Visit https://console.brev.dev → Cloud → Add GCP/AWS account",
                }

        return {"ok": False, "message": "No capacity for cheap GPUs. Try manually at https://console.brev.dev"}

    def stop(self, name: str | None = None) -> dict[str, Any]:
        """Stop instance to save money."""
        target = name or self.instance_name
        result = subprocess.run(
            ["brev", "stop", target],
            capture_output=True, text=True, timeout=30,
        )
        return {
            "ok": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr,
        }

    def shell(self, name: str | None = None) -> None:
        """Open shell in instance (blocks)."""
        target = name or self.instance_name
        subprocess.run(["brev", "shell", target])

    def ssh_command(self, name: str | None = None) -> str:
        """Return SSH command for instance."""
        target = name or self.instance_name
        return f"brev shell {target}"
