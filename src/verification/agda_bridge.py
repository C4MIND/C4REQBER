"""
Agda proof assistant bridge for C4REQBER v8.0.
License: Apache 2.0
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AgdaError:
    """AgdaError."""
    file: str
    line: int
    column: int
    message: str


class AgdaBridge:
    """Agda proof assistant bridge."""

    def __init__(self, agda_path: str = "agda"):
        self.agda_path = agda_path
        self.available = self._check_availability()
        self._version = self._get_version() if self.available else None

    def _check_availability(self) -> bool:
        try:
            result = subprocess.run(
                [self.agda_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_version(self) -> str | None:
        try:
            result = subprocess.run(
                [self.agda_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                return lines[0] if lines else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    @staticmethod
    def _validate_module_name(name: str) -> str:
        import re
        if not re.fullmatch(r"[A-Z][a-zA-Z0-9_]*", name):
            raise ValueError(f"Invalid Agda module name: {name}")
        return name

    def type_check(self, code: str, module_name: str = "TURBOCDI") -> dict[str, Any]:
        """Type-check Agda code.

        Args:
            code: Agda code to type-check
            module_name: Module name for the code

        Returns:
            Dict with keys: success, errors, warnings
        """
        module_name = self._validate_module_name(module_name)
        if not self.available:
            return {
                "success": False,
                "errors": [{"file": "", "line": 0, "column": 0, "message": "Agda not installed"}],
                "warnings": [],
            }

        agda_code = f"module {module_name} where\n\n{code}"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".agda", delete=False
        ) as f:
            f.write(agda_code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [self.agda_path, temp_path],
                capture_output=True,
                text=True,
                timeout=120,
            )

            errors, warnings = self._parse_output(result.stderr or result.stdout)

            return {
                "success": result.returncode == 0 and not errors,
                "errors": errors,
                "warnings": warnings,
                "module": module_name,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": [{"file": "", "line": 0, "column": 0, "message": "Type-checking timed out"}],
                "warnings": [],
            }
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            compiled_file = temp_path.replace(".agda", ".agdai")
            if os.path.exists(compiled_file):
                os.unlink(compiled_file)

    def compile(self, code: str, target: str = "haskell", module_name: str = "TURBOCDI") -> dict[str, Any]:
        """Compile Agda to Haskell or JS.

        Args:
            code: Agda code to compile
            target: Target language ("haskell" or "js")
            module_name: Module name for the code

        Returns:
            Dict with keys: success, output_path, errors
        """
        if not self.available:
            return {
                "success": False,
                "output_path": None,
                "errors": [{"file": "", "line": 0, "column": 0, "message": "Agda not installed"}],
            }

        if target not in ("haskell", "js"):
            return {
                "success": False,
                "output_path": None,
                "errors": [{"file": "", "line": 0, "column": 0, "message": f"Unknown target: {target}"}],
            }

        agda_code = f"module {module_name} where\n\n{code}"

        with tempfile.TemporaryDirectory() as tmpdir:
            agda_file = Path(tmpdir) / f"{module_name}.agda"
            agda_file.write_text(agda_code)

            compile_flag = "-c" if target == "haskell" else "--js"
            try:
                result = subprocess.run(
                    [self.agda_path, compile_flag, str(agda_file)],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    cwd=tmpdir,
                )

                errors, _ = self._parse_output(result.stderr or result.stdout)

                output_files = list(Path(tmpdir).glob(f"{module_name}.*"))
                output_path = str(output_files[0]) if output_files else None

                return {
                    "success": result.returncode == 0 and not errors,
                    "output_path": output_path,
                    "errors": errors,
                    "target": target,
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "output_path": None,
                    "errors": [{"file": "", "line": 0, "column": 0, "message": "Compilation timed out"}],
                }

    def get_environment(self) -> dict[str, Any]:
        """Get Agda environment info.

        Returns:
            Dict with keys: available, version, path, libraries
        """
        return {
            "available": self.available,
            "version": self._version,
            "path": self.agda_path,
            "libraries": self._get_libraries(),
        }

    def _get_libraries(self) -> list[str]:
        libraries = []
        agda_dir = Path.home() / ".agda"
        libraries_file = agda_dir / "libraries"

        if libraries_file.exists():
            try:
                libraries = [
                    line.strip()
                    for line in libraries_file.read_text().split("\n")
                    if line.strip() and not line.startswith("--")
                ]
            except OSError:
                pass

        return libraries

    def _parse_output(self, output: str) -> tuple[list[dict], list[dict]]:
        errors = []
        warnings = []

        for line in output.split("\n"):
            line_lower = line.lower()
            is_error = "error" in line_lower
            is_warning = "warning" in line_lower

            if is_error or is_warning:
                parts = line.split(":")
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1].strip())
                        col_num = int(parts[2].strip())
                        message = ":".join(parts[3:]).strip()

                        entry = {
                            "file": parts[0],
                            "line": line_num,
                            "column": col_num,
                            "message": message,
                        }

                        if is_error:
                            errors.append(entry)
                        else:
                            warnings.append(entry)
                    except (ValueError, IndexError):
                        entry = {
                            "file": "",
                            "line": 0,
                            "column": 0,
                            "message": line,
                        }
                        if is_error:
                            errors.append(entry)
                        else:
                            warnings.append(entry)

        return errors, warnings

    def prove_theorem(self, theorem: str, proof: str | None = None) -> dict[str, Any]:
        """Prove a theorem in Agda.

        Args:
            theorem: Theorem statement
            proof: Optional proof term

        Returns:
            Dict with verification result
        """
        code = f"""
{theorem} : ?
{theorem} = {"?" if proof is None else proof}
"""
        return self.type_check(code, module_name="Theorem")

    def generate_theorem_template(self, name: str, type_signature: str) -> str:
        """Generate a theorem template for Agda.

        Args:
            name: Theorem name
            type_signature: Type signature

        Returns:
            Agda code template
        """
        return f"""
{name} : {type_signature}
{name} = ?
"""

    def check_termination(self, code: str, module_name: str = "Termination") -> dict[str, Any]:
        """Check termination of recursive definitions.

        Args:
            code: Agda code with recursive definitions
            module_name: Module name

        Returns:
            Dict with termination analysis result
        """
        result = self.type_check(code, module_name)
        termination_errors = [
            e for e in result["errors"]
            if "termination" in e.get("message", "").lower()
        ]

        return {
            "terminates": not termination_errors,
            "errors": termination_errors,
            "raw_result": result,
        }

    def check_coverage(self, code: str, module_name: str = "Coverage") -> dict[str, Any]:
        """Check pattern matching coverage.

        Args:
            code: Agda code with pattern definitions
            module_name: Module name

        Returns:
            Dict with coverage analysis result
        """
        result = self.type_check(code, module_name)
        coverage_errors = [
            e for e in result["errors"]
            if "coverage" in e.get("message", "").lower() or "incomplete" in e.get("message", "").lower()
        ]

        return {
            "complete": not coverage_errors,
            "errors": coverage_errors,
            "raw_result": result,
        }
