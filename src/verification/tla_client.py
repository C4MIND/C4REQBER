"""TLA+ model checker client (TLC via tla2tools.jar)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path
from src.verification.jar_resolver import resolve_java, tla_tools_jar
from src.verification.timer import BACKEND_TIMEOUTS


CFG_SEPARATOR = "---CFG---"

UNBOUNDED_HINT = (
    "Unbounded TLA+ state space (e.g. Naturals counter without x < MAX). "
    "Bound Next with x < N, or add ---CFG--- with CONSTANT MAX = N and use x < MAX in Next. "
    "TLC -modelcheck -depth is not a substitute for a finite state space."
)


class TLAClient:
    """TLA+ specification verifier using TLC model checker."""

    DEFAULT_DEPTH = 10
    DEFAULT_AUTO_MAX = 12

    def __init__(
        self,
        tlc_path: str | None = None,
        jar_path: str | None = None,
        *,
        depth: int | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.tlc_path = tlc_path or shutil.which("tlc")
        self.jar_path = jar_path or tla_tools_jar()
        self.java_path = resolve_java()
        self.depth = depth if depth is not None else self.DEFAULT_DEPTH
        _soft, hard = BACKEND_TIMEOUTS.get("tla", (30.0, 180.0))
        self.timeout_s = timeout_s if timeout_s is not None else min(hard, 120.0)
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self.test_connection()
        return self._available

    def is_available(self) -> bool:
        return self.available

    def test_connection(self) -> bool:
        if self.tlc_path:
            try:
                result = safe_subprocess_run(
                    [self.tlc_path, "-help"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0 or "TLC" in (result.stdout + result.stderr):
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        if not self.java_path or not self.jar_path:
            return False
        try:
            result = safe_subprocess_run(
                [self.java_path, "-cp", self.jar_path, "tlc2.TLC", "-help"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            out = result.stdout + result.stderr
            return "TLC" in out or "Model Checker" in out
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def verify(self, code: str) -> dict[str, Any]:
        """Model-check a TLA+ specification (optional ---CFG--- block)."""
        if not self.available:
            return {
                "valid": False,
                "error": "TLA+ TLC not installed (set TLA_TOOLS_JAR or install TLA+ Toolbox)",
                "language": "tla",
            }

        tla_code, cfg_code = self._split_input(code)
        module_name = self._extract_module_name(tla_code)
        if not module_name:
            return {"valid": False, "error": "Missing TLA+ MODULE declaration", "language": "tla"}

        unbounded = self._detect_unbounded(tla_code, cfg_code)
        if unbounded:
            return {
                "valid": False,
                "error": unbounded,
                "language": "tla",
                "hint": UNBOUNDED_HINT,
            }

        if not cfg_code:
            cfg_code = self._auto_cfg(tla_code)

        workdir = tempfile.mkdtemp(prefix="c4reqber_tla_")
        tla_path = Path(workdir) / f"{module_name}.tla"
        cfg_path = Path(workdir) / f"{module_name}.cfg"

        try:
            tla_path.write_text(tla_code, encoding="utf-8")
            cfg_path.write_text(cfg_code, encoding="utf-8")
            validate_temp_path(str(tla_path))

            cmd = self._build_command(str(tla_path))
            result = safe_subprocess_run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            valid = self._parse_result(stdout, stderr, result.returncode)
            return {
                "valid": valid,
                "output": (stdout + stderr)[:500],
                "language": "tla",
                "module": module_name,
                "error": None if valid else self._first_error(stdout, stderr),
            }
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "error": f"TLC timed out after {int(self.timeout_s)}s — use a bounded model (CONSTANT MAX)",
                "language": "tla",
                "hint": UNBOUNDED_HINT,
            }
        except subprocess.SubprocessError as e:
            return {"valid": False, "error": str(e), "language": "tla"}
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

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

    def _build_command(self, spec_path: str) -> list[str]:
        """Always use -modelcheck; -depth alone does not bound infinite state spaces."""
        flags = [
            "-modelcheck",
            "-workers",
            "1",
            "-depth",
            str(self.depth),
            spec_path,
        ]
        if self.tlc_path:
            return [self.tlc_path, *flags]
        assert self.java_path and self.jar_path
        return [
            self.java_path,
            "-cp",
            self.jar_path,
            "tlc2.TLC",
            *flags,
        ]

    @staticmethod
    def _split_input(code: str) -> tuple[str, str]:
        if CFG_SEPARATOR in code:
            tla, cfg = code.split(CFG_SEPARATOR, 1)
            return tla.strip(), cfg.strip()
        return code.strip(), ""

    @staticmethod
    def _extract_module_name(tla_code: str) -> str | None:
        match = re.search(r"----\s*MODULE\s+(\w+)", tla_code)
        return match.group(1) if match else None

    @classmethod
    def _detect_unbounded(cls, tla_code: str, cfg_code: str) -> str | None:
        """Reject specs that will run forever (unbounded Naturals/Integers counters)."""
        if not re.search(r"EXTENDS\s+(Naturals|Integers)\b", tla_code, re.I):
            return None
        if not re.search(r"\bx'\s*=\s*x\s*\+\s*1\b", tla_code):
            return None
        if cls._has_explicit_bound(tla_code, cfg_code):
            return None
        return UNBOUNDED_HINT

    @staticmethod
    def _has_explicit_bound(tla_code: str, cfg_code: str) -> bool:
        combined = tla_code + "\n" + cfg_code
        if re.search(r"\bx\s*<\s*\d+\b", combined):
            return True
        if re.search(r"\bCONSTANT\s+MAX\b", combined, re.I):
            return True
        if re.search(r"\bx\s*<\s*MAX\b", combined):
            return True
        if re.search(r"\bDOMAIN\b", combined) and re.search(r"\{[^}]*\.\.[^}]*\}", combined):
            return True
        return False

    @staticmethod
    def _auto_cfg(tla_code: str) -> str:
        if re.search(r"\bSpec\s*==", tla_code):
            return "SPECIFICATION Spec\n"
        init = "Init" if re.search(r"\bInit\s*==", tla_code) else None
        nxt = "Next" if re.search(r"\bNext\s*==", tla_code) else None
        if init and nxt:
            return f"INIT {init}\nNEXT {nxt}\n"
        if init:
            return f"INIT {init}\n"
        return "INIT Init\nNEXT Next\n"

    @staticmethod
    def _parse_result(stdout: str, stderr: str, returncode: int) -> bool:
        combined = stdout + "\n" + stderr
        low = combined.lower()
        if "65536 or more states" in combined:
            return False
        if "tlc threw an unexpected exception" in low:
            return False
        if "unexpected exception" in low and "runtimeexception" in low:
            return False
        if any(
            tok in low for tok in ("violation", "counterexample", "assertion failed", "invariant")
        ):
            if "no error" not in low:
                return False
        if "finished in" in low and "states generated" in low:
            if "65536" in combined or "unexpected exception" in low:
                return False
            # Require absence of soft failures, not just returncode
            if returncode != 0 or "error:" in low:
                return False
            return True
        if "model checking completed" in low:
            return returncode == 0 and "error:" not in low
        # Refuse returncode==0 alone without positive TLC success tokens.
        return False

    @staticmethod
    def _first_error(stdout: str, stderr: str) -> str:
        for line in (stdout + "\n" + stderr).splitlines():
            low = line.lower()
            if "65536 or more states" in line:
                return UNBOUNDED_HINT
            if (
                "error" in low
                or "violation" in low
                or "counterexample" in low
                or "exception" in low
            ):
                return line.strip()
        return "TLC model checking failed"
