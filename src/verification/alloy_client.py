"""Alloy analyzer client for relational model checking."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from typing import Any

from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path
from src.verification.jar_resolver import alloy_binary, alloy_jar, resolve_java


class AlloyClient:
    """Alloy specification verifier."""

    def __init__(self, alloy_path: str | None = None, jar_path: str | None = None) -> None:
        self.alloy_path = alloy_path or alloy_binary()
        self.jar_path = jar_path or alloy_jar()
        self.java_path = resolve_java()
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self.test_connection()
        return self._available

    def is_available(self) -> bool:
        return self.available

    def test_connection(self) -> bool:
        if self.alloy_path:
            try:
                result = safe_subprocess_run(
                    [self.alloy_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        if not self.java_path or not self.jar_path:
            return False
        try:
            result = safe_subprocess_run(
                [self.java_path, "-jar", self.jar_path, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            out = (result.stdout + result.stderr).lower()
            return result.returncode == 0 or "alloy" in out
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def verify(self, code: str) -> dict[str, Any]:
        """Execute an Alloy model and check assertions."""
        if not self.available:
            return {
                "valid": False,
                "error": "Alloy not installed (brew install alloy-analyzer or set ALLOY_JAR)",
                "language": "alloy",
            }

        alloy_code = self._normalize_code(code)
        with tempfile.NamedTemporaryFile(suffix=".als", mode="w", delete=False) as f:
            f.write(alloy_code)
            path = f.name

        try:
            validate_temp_path(path)
            cmd = self._build_command(path)
            result = safe_subprocess_run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            valid = self._parse_result(stdout, stderr, result.returncode)
            return {
                "valid": valid,
                "output": (stdout + stderr)[:500],
                "language": "alloy",
                "error": None if valid else self._first_error(stdout, stderr),
            }
        except subprocess.SubprocessError as e:
            return {"valid": False, "error": str(e), "language": "alloy"}
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def check_proof(self, code: str) -> dict[str, Any]:
        result = self.verify(code)
        return {
            "success": result.get("valid", False),
            "errors": (
                [{"line": 0, "column": 0, "message": result["error"]}]
                if result.get("error")
                else []
            ),
            "goals": [],
        }

    def _build_command(self, path: str) -> list[str]:
        if self.alloy_path:
            return [self.alloy_path, "exec", path]
        assert self.java_path and self.jar_path
        return [self.java_path, "-jar", self.jar_path, "exec", path]

    @staticmethod
    def _normalize_code(code: str) -> str:
        stripped = code.strip()
        if not stripped:
            return "run {} for 3\n"
        if not re.search(r"\b(run|check)\b", stripped):
            stripped += "\nrun {} for 3\n"
        return stripped

    @staticmethod
    def _parse_result(stdout: str, stderr: str, returncode: int) -> bool:
        combined = (stdout + "\n" + stderr).lower()
        if any(
            tok in combined
            for tok in (
                "syntax error",
                "type error",
                "resolution error",
                "cannot be found",
                "no solution",
            )
        ):
            return False
        if "counterexample" in combined and "no counterexample" not in combined:
            return False
        # Require positive success tokens — returncode==0 alone is not enough.
        positive = any(
            tok in combined
            for tok in ("no counterexample", "instance found", " sat", "\tsat", "1/1")
        )
        if positive and returncode == 0 and "error" not in combined:
            return True
        if "unsat" in combined:
            return False
        return False

    @staticmethod
    def _first_error(stdout: str, stderr: str) -> str:
        for line in (stdout + "\n" + stderr).splitlines():
            low = line.lower()
            if any(tok in low for tok in ("error", "counterexample", "syntax")):
                return line.strip()
        return "Alloy verification failed"
