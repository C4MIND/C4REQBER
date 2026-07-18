"""
Lean 4 proof assistant client for C4REQBER v8.0.
License: Apache 2.0
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any


@dataclass
class LeanGoal:
    """LeanGoal."""

    hypothesis: str
    target: str


@dataclass
class LeanError:
    """LeanError."""

    line: int
    column: int
    message: str


class Lean4Client:
    """Lean 4 proof assistant client."""

    def __init__(self, lean_path: str = "lean", lake_path: str = "lake") -> None:
        self.lean_path = lean_path
        self.lake_path = lake_path
        self.available = self._check_availability()
        self._version = self._get_version() if self.available else None

    def _check_availability(self) -> bool:
        try:
            result = subprocess.run(
                [self.lean_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "Lean" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_version(self) -> str | None:
        try:
            result = subprocess.run(
                [self.lean_path, "--version"],
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

    def check_proof(self, code: str) -> dict[str, Any]:
        """Check Lean 4 proof.

        Args:
            code: Lean 4 code to check

        Returns:
            Dict with keys: success, errors, goals
        """
        if not self.available:
            return {
                "success": False,
                "errors": [{"line": 0, "column": 0, "message": "Lean 4 not installed"}],
                "goals": [],
            }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [self.lean_path, temp_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            errors = self._parse_errors(result.stderr or result.stdout)
            goals = self._parse_goals(result.stdout)

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

    def run_tactic(self, state: str, tactic: str) -> dict[str, Any]:
        """Run single tactic.

        Args:
            state: Current proof state
            tactic: Tactic to apply

        Returns:
            Dict with keys: success, new_state, goals, error
        """
        if not self.available:
            return {
                "success": False,
                "new_state": state,
                "goals": [],
                "error": "Lean 4 not installed",
            }

        # Refuse True-wrapper theater — tactic success on `example : True`
        # does not advance a real goal. Require caller-supplied goal state.
        if "theorem" not in state and "example" not in state and "lemma" not in state:
            return {
                "success": False,
                "new_state": state,
                "goals": [],
                "error": "apply_tactic requires a real theorem/lemma/example goal in state "
                "(refusing example : True wrapper)",
                "heuristic": False,
            }

        code = f"""
{state}

  {tactic}
"""
        result = self.check_proof(code)

        return {
            "success": result["success"],
            "new_state": state,
            "goals": result["goals"],
            "error": result["errors"][0]["message"] if result["errors"] else None,
        }

    def get_environment(self) -> dict[str, Any]:
        """Get Lean environment info.

        Returns:
            Dict with keys: available, version, path, mathlib_available
        """
        env_info = {
            "available": self.available,
            "version": self._version,
            "path": self.lean_path,
            "mathlib_available": self._check_mathlib(),
        }

        if self.available:
            try:
                result = subprocess.run(
                    [self.lake_path, "env"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                env_info["lake_env"] = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                env_info["lake_env"] = False

        return env_info

    def _check_mathlib(self) -> bool:
        try:
            test_code = "import Mathlib\n#check Nat"
            result = self.check_proof(test_code)
            if result.get("success"):
                return True
            return not any(
                "unknown module 'Mathlib'" in e.get("message", "") for e in result.get("errors", [])
            )
        except (ValueError, TypeError, KeyError):
            return False

    def _parse_errors(self, output: str) -> list[dict[str, Any]]:
        errors = []
        import re

        # Match Lean4-style errors: file:line:col: error: message
        pattern = re.compile(r"^(.*?):(\d+):(\d+):\s*error:\s*(.*)$", re.IGNORECASE)
        for line in output.split("\n"):
            m = pattern.match(line)
            if m:
                errors.append(
                    {
                        "line": int(m.group(2)),
                        "column": int(m.group(3)),
                        "message": m.group(4).strip(),
                    }
                )
            elif "error:" in line.lower():
                errors.append(
                    {
                        "line": 0,
                        "column": 0,
                        "message": line.strip(),
                    }
                )
        return errors

    def _parse_goals(self, output: str) -> list[dict[str, Any]]:
        goals = []
        current_goal = {"hypothesis": "", "target": ""}

        for line in output.split("\n"):
            if "⊢" in line:
                current_goal["target"] = line.split("⊢", 1)[1].strip()
                goals.append(current_goal)
                current_goal = {"hypothesis": "", "target": ""}
            elif ":" in line and not line.startswith("-"):
                current_goal["hypothesis"] += line + "\n"

        return goals

    def verify_theorem(self, statement: str, proof: str | None = None) -> dict[str, Any]:
        """
        Verify a theorem using Lean 4.

        Args:
            statement: The theorem statement to verify
            proof: Proof tactics (required — rejects empty/default proofs)

        Returns:
            Dict with keys: valid, error
        """
        if proof is None:
            proof = ""
        proof_lower = proof.strip().lower()
        if not proof or proof_lower == "sorry" or "sorry" in proof_lower:
            return {
                "valid": False,
                "error": "Empty proof rejected: provide real Lean4 proof tactics, not 'sorry'.",
            }
        code = f"""
theorem discovery_1 : {statement} :=
  {proof}
"""
        result = self.check_proof(code)
        return {
            "valid": result["success"],
            "error": result["errors"][0]["message"] if result["errors"] else None,
        }

    async def verify_discovery(
        self, hypothesis: str, evidence: list[str] | None = None
    ) -> dict[str, Any]:
        """Auto-generate and verify a discovery.

        Uses FormalizationEngine → ConsensusEngine pipeline.
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

    def interactive_proof(self, theorem: str) -> dict[str, Any]:
        """Start interactive proof session.

        Args:
            theorem: Theorem to prove

        Returns:
            Dict with session_id and initial goals
        """
        code = f"""
theorem interactive : {theorem} := by
  -- Place tactics here
  sorry
"""
        result = self.check_proof(code)
        return {
            "session_id": id(theorem),
            "goals": result["goals"],
            "initial_code": code,
        }

    def batch_verify(self, theorems: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Batch verify multiple theorems.

        Args:
            theorems: List of dicts with 'name' and 'statement' keys

        Returns:
            List of verification results
        """
        results = []
        for thm in theorems:
            proof = thm.get("proof") or None
            result = self.verify_theorem(thm["statement"], proof)
            results.append(
                {
                    "name": thm.get("name", "unnamed"),
                    "valid": result["valid"],
                    "error": result.get("error"),
                }
            )
        return results
