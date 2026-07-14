"""Dafny verification client for C44TCDI.

Provides structured error parsing, goal extraction, and batch verification
for the Dafny programming language and program verifier.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any

from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path


class DafnyClient:
    """Dafny verification client."""

    def __init__(self, dafny_path: str = "dafny"):
        """Initialize the Dafny client.

        Args:
            dafny_path: Path to the Dafny executable.
        """
        self.dafny_path = shutil.which(dafny_path) or dafny_path
        self._available: bool | None = None
        self._version: str | None = None

    @property
    def available(self) -> bool:
        """Whether Dafny is available on the system."""
        if self._available is None:
            self._available = self.test_connection()
        return self._available

    def is_available(self) -> bool:
        """Backward-compatible availability check.

        Returns:
            True if Dafny is installed and accessible.
        """
        return self.available

    def test_connection(self) -> bool:
        """Check if the Dafny executable is available.

        Returns:
            True if Dafny responds to ``--version``.
        """
        try:
            result = safe_subprocess_run(
                [self.dafny_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "Dafny" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_version(self) -> str | None:
        """Get the installed Dafny version string.

        Returns:
            Version string or None if unavailable.
        """
        if self._version is not None:
            return self._version
        try:
            result = safe_subprocess_run(
                [self.dafny_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                self._version = lines[0] if lines else None
                return self._version
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def verify(self, code: str) -> dict[str, Any]:
        """Verify Dafny code.

        Args:
            code: Dafny source code to verify.

        Returns:
            Dict with keys: valid, output, language, and optionally error.
        """
        if not self.available:
            return {"valid": False, "error": "Dafny not installed", "language": "dafny"}

        with tempfile.NamedTemporaryFile(suffix=".dfy", mode="w", delete=False) as f:
            f.write(code)
            path = f.name

        try:
            validate_temp_path(path)
            result = safe_subprocess_run(
                [self.dafny_path, "verify", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout or ""
            errors = self._parse_errors(output, result.stderr or "")
            return {
                "valid": result.returncode == 0 and not errors,
                "output": output[:500],
                "language": "dafny",
                "error": errors[0]["message"] if errors else None,
            }
        except subprocess.SubprocessError as e:
            return {"valid": False, "error": str(e), "language": "dafny"}
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def check_proof(self, code: str) -> dict[str, Any]:
        """Check Dafny proof/code and return structured results.

        Mirrors the Lean4Client ``check_proof`` API.

        Args:
            code: Dafny source code to check.

        Returns:
            Dict with keys: success, errors, goals.
        """
        if not self.available:
            return {
                "success": False,
                "errors": [{"line": 0, "column": 0, "message": "Dafny not installed"}],
                "goals": [],
            }

        with tempfile.NamedTemporaryFile(suffix=".dfy", mode="w", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            validate_temp_path(temp_path)
            result = safe_subprocess_run(
                [self.dafny_path, "verify", temp_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            errors = self._parse_errors(result.stdout or "", result.stderr or "")
            goals = self._parse_goals(result.stdout or "")
            return {
                "success": result.returncode == 0 and not errors,
                "errors": errors,
                "goals": goals,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": [{"line": 0, "column": 0, "message": "Verification timed out"}],
                "goals": [],
            }
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _parse_errors(self, stdout: str, stderr: str) -> list[dict[str, Any]]:
        """Parse Dafny error messages.

        Expected format::

            file.dfy(5,10): Error: assertion might not hold

        Args:
            stdout: Standard output from Dafny.
            stderr: Standard error from Dafny.

        Returns:
            List of error dicts with line, column, and message keys.
        """
        errors: list[dict[str, Any]] = []
        combined = stdout + "\n" + stderr

        for line in combined.splitlines():
            stripped = line.strip()
            if "Error:" not in stripped:
                continue
            # Try to extract file.dfy(line,col): Error: message
            if ":" in stripped:
                parts = stripped.split(":", 2)
                if len(parts) >= 3:
                    location_part = parts[0].strip()
                    message = parts[2].strip()
                    line_num = 0
                    column_num = 0
                    # Look for (line,col) pattern
                    if "(" in location_part and ")" in location_part:
                        loc_inner = location_part.split("(", 1)[1].rsplit(")", 1)[0]
                        if "," in loc_inner:
                            try:
                                line_num = int(loc_inner.split(",", 1)[0].strip())
                                column_num = int(loc_inner.split(",", 1)[1].strip())
                            except ValueError:
                                pass
                    errors.append({
                        "line": line_num,
                        "column": column_num,
                        "message": message,
                    })
                else:
                    errors.append({
                        "line": 0,
                        "column": 0,
                        "message": stripped,
                    })
            else:
                errors.append({
                    "line": 0,
                    "column": 0,
                    "message": stripped,
                })

        return errors

    def _parse_goals(self, stdout: str) -> list[dict[str, Any]]:
        """Extract verification conditions (goals) from Dafny output.

        Looks for assertion violation context and related verification conditions.

        Args:
            stdout: Standard output from Dafny.

        Returns:
            List of goal dicts with hypothesis and target keys.
        """
        goals: list[dict[str, Any]] = []
        current_goal: dict[str, Any] | None = None

        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Start a new goal on assertion-related lines
            if "assertion" in line.lower() or "postcondition" in line.lower() or "invariant" in line.lower():
                if current_goal is not None:
                    goals.append(current_goal)
                current_goal = {"hypothesis": "", "target": line}
                continue

            # Accumulate context lines for the current goal
            if current_goal is not None:
                if line.startswith("|") or line.startswith("-") or line.startswith("Related"):
                    current_goal["hypothesis"] += line + "\n"
                else:
                    # End of current goal block
                    goals.append(current_goal)
                    current_goal = None

        if current_goal is not None:
            goals.append(current_goal)

        return goals

    def verify_method(self, method_code: str, module_context: str = "") -> dict[str, Any]:
        """Verify a single Dafny method or function.

        Args:
            method_code: The method/function to verify.
            module_context: Optional surrounding module or import context.

        Returns:
            Dict with keys: valid, error.
        """
        import re
        code_lower = method_code.lower()
        if re.search(r"\bassume\b", code_lower) or "{:verify false}" in code_lower or "{:axiom}" in code_lower:
            return {"valid": False, "error": "Vacuous proof rejected: 'assume', '{:verify false}', or '{:axiom}' detected."}
        code = module_context + "\n" + method_code if module_context else method_code
        result = self.check_proof(code)
        return {
            "valid": result["success"],
            "error": result["errors"][0]["message"] if result["errors"] else None,
        }

    def verify_theorem(self, lemma_statement: str, proof_body: str = "") -> dict[str, Any]:
        """Verify a Dafny lemma with an optional proof body.

        Args:
            lemma_statement: The lemma/theorem statement.
            proof_body: Body of the lemma (e.g., ``{ assert ...; }``).

        Returns:
            Dict with keys: valid, error.
        """
        code = f"lemma {lemma_statement}\n{proof_body}"
        result = self.check_proof(code)
        return {
            "valid": result["success"],
            "error": result["errors"][0]["message"] if result["errors"] else None,
        }

    async def verify_discovery(self, hypothesis: str, evidence: list[str] | None = None) -> dict[str, Any]:
        """Auto-generate and verify a discovery from a natural-language hypothesis.

        Uses FormalizationEngine → ConsensusEngine pipeline.

        Args:
            hypothesis: Natural-language hypothesis text.
            evidence: Optional list of evidence titles.

        Returns:
            Dict with keys: success, output.
        """
        from src.verification.config import get_auto_formalization_config
        from src.verification.consensus_engine import ConsensusEngine
        from src.verification.formalization_engine import FormalizationEngine
        from src.verification.semantic_alignment import SemanticAlignmentChecker

        config = get_auto_formalization_config()
        if not config.enabled:
            return {
                "success": False,
                "output": "Auto-formalization disabled by config.",
            }

        engine = FormalizationEngine()
        formal = await engine.formalize({"text": hypothesis}, evidence)
        if formal.formalizability_score < config.min_score:
            return {
                "success": False,
                "output": f"Not formalizable: {formal.not_formalizable_reason}",
            }

        consensus = await ConsensusEngine().verify_with_consensus(
            formal.theorem_statement,
            languages=config.languages,
            min_agreement=config.min_agreement,
        )

        if config.semantic_alignment_check and consensus.status in ("verified", "partial"):
            for lang, details in consensus.languages.items():
                if details.get("valid"):
                    checker = SemanticAlignmentChecker()
                    alignment = await checker.check_alignment(
                        consensus.theorem_statement,
                        details.get("proof", ""),
                        lang,
                    )
                    if not alignment.aligned:
                        details["valid"] = False
                        details["alignment_error"] = alignment.explanation

            valid_count = sum(1 for d in consensus.languages.values() if d.get("valid", False))
            total = len(consensus.languages)
            if valid_count >= config.min_agreement:
                consensus.status = "verified"
                consensus.confidence = valid_count / total
                consensus.human_review_recommended = False
            elif valid_count >= 1:
                consensus.status = "partial"
                consensus.confidence = valid_count / total
                consensus.human_review_recommended = True
            else:
                consensus.status = "failed"
                consensus.confidence = 0.0
                consensus.human_review_recommended = True

        return {
            "success": consensus.status == "verified",
            "output": consensus.to_dict(),
        }

    def batch_verify(self, codes: list[str]) -> list[dict[str, Any]]:
        """Verify multiple Dafny snippets.

        Args:
            codes: List of Dafny code strings to verify.

        Returns:
            List of result dicts with valid, output, and error keys.
        """
        results: list[dict[str, Any]] = []
        for code in codes:
            result = self.verify(code)
            results.append({
                "valid": result.get("valid", False),
                "output": result.get("output"),
                "error": result.get("error"),
            })
        return results
