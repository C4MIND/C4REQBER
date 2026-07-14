"""
lean4lean Client — External checker for Lean 4 kernel.
License: BSD-style (digama0/lean4lean)
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


class Lean4LeanClient:
    """Client for lean4lean kernel verification."""

    def __init__(self, lean4lean_path: str | None = None) -> None:
        self.lean4lean_path = lean4lean_path or os.getenv("LEAN4LEAN_PATH", "")
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if lean4lean is available."""
        try:
            if self.lean4lean_path:
                exe = Path(self.lean4lean_path)
                if exe.exists() and os.access(exe, os.X_OK):
                    return True
            result = subprocess.run(
                ["lean4lean", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "lean4lean" in result.stdout.lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def verify_kernel_operation(self, operation: str) -> dict[str, Any]:
        """Verify a kernel operation using lean4lean."""
        if not self.available:
            return {
                "valid": False,
                "error": "lean4lean not installed. See github.com/digama0/lean4lean"
            }
        try:
            exe = self.lean4lean_path or "lean4lean"
            result = subprocess.run(
                [exe, operation],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = (result.stdout or result.stderr).strip()
            return {
                "valid": result.returncode == 0,
                "output": output[:2000],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": "lean4lean timed out"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
