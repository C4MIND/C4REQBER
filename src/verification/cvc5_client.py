"""CVC5 SMT solver client for C44TCDI.

Verifies SMT-LIB2 specifications via the cvc5 binary.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from typing import Any

from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path


class CVC5Client:
    """CVC5 SMT-LIB2 verification client."""

    def __init__(self, cvc5_path: str | None = None) -> None:
        path = cvc5_path or os.environ.get("CVC5_PATH", "cvc5")
        self.cvc5_path = shutil.which(path) or path
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self.test_connection()
        return self._available

    def is_available(self) -> bool:
        return self.available

    def test_connection(self) -> bool:
        try:
            result = safe_subprocess_run(
                [self.cvc5_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "cvc5" in (result.stdout + result.stderr).lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def verify(self, code: str) -> dict[str, Any]:
        """Verify SMT-LIB2 code with CVC5."""
        if not self.available:
            return {"valid": False, "error": "CVC5 not installed", "language": "cvc5"}

        smt_code = self._normalize_smtlib(code)
        with tempfile.NamedTemporaryFile(suffix=".smt2", mode="w", delete=False) as f:
            f.write(smt_code)
            path = f.name

        try:
            validate_temp_path(path)
            result = safe_subprocess_run(
                [self.cvc5_path, "--lang", "smt2", "-q", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            valid = self._parse_result(stdout, stderr, result.returncode)
            status = self._extract_sat_status(stdout, stderr)
            return {
                "valid": valid,
                "output": (stdout + stderr)[:500],
                "language": "cvc5",
                "status": status,
                "error": None if valid else self._first_error(stdout, stderr, status),
            }
        except subprocess.SubprocessError as e:
            return {"valid": False, "error": str(e), "language": "cvc5"}
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def check_proof(self, code: str) -> dict[str, Any]:
        """Mirror Lean4Client check_proof API."""
        result = self.verify(code)
        return {
            "success": result.get("valid", False),
            "errors": (
                [{"line": 0, "column": 0, "message": result["error"]}]
                if result.get("error")
                else []
            ),
            "goals": [],
            "status": result.get("status"),
        }

    @staticmethod
    def _normalize_smtlib(code: str) -> str:
        stripped = code.strip()
        if not stripped:
            return "(set-logic ALL)\n(check-sat)\n"
        if "(check-sat)" not in stripped.lower():
            stripped += "\n(check-sat)\n"
        if "(set-logic" not in stripped.lower():
            stripped = "(set-logic ALL)\n" + stripped
        return stripped

    @staticmethod
    def _extract_sat_status(stdout: str, stderr: str) -> str:
        for line in reversed((stdout + "\n" + stderr).splitlines()):
            token = line.strip().lower()
            if token in ("sat", "unsat", "unknown"):
                return token
        return "error"

    @staticmethod
    def _parse_result(stdout: str, stderr: str, returncode: int) -> bool:
        status = CVC5Client._extract_sat_status(stdout, stderr)
        if status in ("sat", "unsat"):
            return returncode == 0
        combined = (stdout + stderr).lower()
        if "error" in combined or "parse error" in combined:
            return False
        return returncode == 0 and status != "unknown"

    @staticmethod
    def _first_error(stdout: str, stderr: str, status: str) -> str:
        combined = stdout + "\n" + stderr
        for line in combined.splitlines():
            low = line.lower()
            if "error" in low or "parse error" in low:
                return line.strip()
        if status == "unknown":
            return "CVC5 returned unknown (timeout or incomplete)"
        return "CVC5 verification failed"

    @staticmethod
    def estimate_complexity(code: str) -> float:
        """Heuristic complexity score for guardrails integration."""
        lines = len(code.splitlines())
        quantifiers = len(re.findall(r"forall|exists|∀|∃", code, flags=re.IGNORECASE))
        return min(1.0, (lines / 1000) * 0.5 + (quantifiers / 100) * 0.5)
