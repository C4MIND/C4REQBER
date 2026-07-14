"""Coq proof assistant client for C44TCDI v8.0."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any


class CoqClient:
    """Coq proof assistant client."""

    def __init__(self, coq_path: str = "coqc"):
        self.coq_path = shutil.which(coq_path) or coq_path
        self._available: bool | None = None
        self._version: str | None = None

    @property
    def available(self) -> bool:
        return self.is_available()

    def is_available(self) -> bool:
        """Check if available."""
        if self._available is not None:
            return self._available
        self._available = shutil.which(self.coq_path) is not None
        return self._available

    def test_connection(self) -> bool:
        """Check if coqc is available and responding.

        Returns:
            True if coqc is installed and responds to --version.
        """
        try:
            result = subprocess.run(
                [self.coq_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and "version" in result.stdout.lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_version(self) -> str | None:
        """Get Coq version string."""
        if self._version is not None:
            return self._version
        try:
            result = subprocess.run(
                [self.coq_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                self._version = lines[0] if lines else None
                return self._version
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def check_proof(self, code: str) -> dict[str, Any]:
        """Check Coq proof.

        Args:
            code: Coq code to check.

        Returns:
            Dict with keys: valid, success, output, language, errors, goals, error.
        """
        if not self.is_available():
            return {
                "valid": False,
                "success": False,
                "error": "Coq not installed",
                "errors": [{"line": 0, "column": 0, "message": "Coq not installed"}],
                "goals": [],
                "output": "",
                "language": "coq",
            }

        with tempfile.NamedTemporaryFile(suffix=".v", mode="w", delete=False) as f:
            f.write(code)
            path = f.name

        from src.utils.safe_subprocess import validate_temp_path
        validate_temp_path(path)

        try:
            result = subprocess.run(
                [self.coq_path, path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            errors = self._parse_errors(result.stdout, result.stderr)
            goals = self._parse_goals(result.stdout)
            has_errors = bool(errors)
            is_valid = result.returncode == 0 and not has_errors

            return {
                "valid": is_valid,
                "success": is_valid,
                "output": result.stdout[:500],
                "language": "coq",
                "errors": errors,
                "goals": goals,
                "error": errors[0]["message"] if errors else None,
            }
        except subprocess.SubprocessError as e:
            return {
                "valid": False,
                "success": False,
                "error": str(e),
                "errors": [{"line": 0, "column": 0, "message": str(e)}],
                "goals": [],
                "output": "",
                "language": "coq",
            }
        finally:
            os.unlink(path)

    def _parse_errors(self, stdout: str, stderr: str) -> list[dict[str, Any]]:
        """Parse Coq error messages.

        Coq prints errors to stderr (or stdout) prefixed with "Error:".

        Args:
            stdout: Standard output from coqc.
            stderr: Standard error from coqc.

        Returns:
            List of error dicts with keys: line, column, message.
        """
        errors = []
        combined = (stderr or "") + "\n" + (stdout or "")

        for line in combined.split("\n"):
            if "Error:" in line:
                # Try to extract location info from preceding "File ... line ..."
                message = line.split("Error:", 1)[1].strip()
                line_num = 0
                column = 0
                errors.append({
                    "line": line_num,
                    "column": column,
                    "message": message,
                })

        # Also look for multi-line error blocks that start with "File ..."
        in_error = False
        current_message = ""
        current_line = 0
        current_col = 0

        for line in combined.split("\n"):
            if line.startswith("File ") and "line" in line:
                parts = line.split(",")
                for part in parts:
                    if "line" in part.lower():
                        try:
                            current_line = int("".join(c for c in part if c.isdigit()))
                        except ValueError:
                            pass
                    if "characters" in part.lower():
                        import re
                        m = re.search(r"characters\s+(\d+)-(\d+)", part, re.IGNORECASE)
                        if m:
                            try:
                                current_col = int(m.group(1))
                            except ValueError:
                                pass
                in_error = True
                current_message = ""
            elif in_error and line.strip() and not line.startswith("File "):
                if "Error:" in line:
                    current_message = line.split("Error:", 1)[1].strip()
                    errors.append({
                        "line": current_line,
                        "column": current_col,
                        "message": current_message,
                    })
                    in_error = False
                    current_message = ""
                else:
                    current_message += line + " "

        # Deduplicate
        seen = set()
        unique_errors = []
        for err in errors:
            key = (err["line"], err["column"], err["message"])
            if key not in seen:
                seen.add(key)
                unique_errors.append(err)

        return unique_errors

    def _parse_goals(self, stdout: str) -> list[dict[str, Any]]:
        """Extract proof goals from Coq output.

        Coq prints goals with a separator line of equals signs.

        Args:
            stdout: Standard output from coqc.

        Returns:
            List of goal dicts with keys: hypothesis, target.
        """
        goals: list[dict[str, Any]] = []
        if not stdout:
            return goals

        lines = stdout.split("\n")
        i = 0
        while i < len(lines):
            if "============================" in lines[i] or "=" * 20 in lines[i]:
                # Gather hypothesis lines above separator
                hypothesis_lines: list[str] = []
                j = i - 1
                while j >= 0 and lines[j].strip() != "" and "subgoal" not in lines[j].lower():
                    hypothesis_lines.insert(0, lines[j])
                    j -= 1

                # Target is the line below separator
                target = ""
                if i + 1 < len(lines):
                    target = lines[i + 1].strip()

                hypothesis = "\n".join(hypothesis_lines).strip()
                goals.append({
                    "hypothesis": hypothesis,
                    "target": target,
                })
                i += 1
            i += 1

        return goals

    def run_tactic(self, tactic_code: str, theorem_context: str = "") -> dict[str, Any]:
        """Run a single tactic in a temporary Coq file.

        Args:
            tactic_code: Tactic to apply.
            theorem_context: Surrounding theorem statement and proof context.

        Returns:
            Dict with keys: success, new_state, goals, error.
        """
        if not self.is_available():
            return {
                "success": False,
                "new_state": theorem_context,
                "goals": [],
                "error": "Coq not installed",
            }

        code = theorem_context
        if tactic_code.strip():
            if code.strip():
                # Append tactic before closing Qed if present (only the LAST occurrence)
                if "Qed." in code:
                    before, sep, after = code.rpartition("Qed.")
                    code = before + tactic_code.strip() + "\nQed." + after
                elif "Defined." in code:
                    before, sep, after = code.rpartition("Defined.")
                    code = before + tactic_code.strip() + "\nDefined." + after
                else:
                    code = code.rstrip() + "\n" + tactic_code.strip() + "\nQed.\n"
            else:
                code = f"Theorem test : True.\nProof.\n  {tactic_code.strip()}\nQed.\n"

        result = self.check_proof(code)

        return {
            "success": result["success"],
            "new_state": code,
            "goals": result.get("goals", []),
            "error": result.get("error"),
        }

    def verify_theorem(self, theorem_statement: str, proof_tactics: str = "") -> dict[str, Any]:
        """Verify a complete theorem with proof.

        Args:
            theorem_statement: Theorem statement (e.g. "forall n : nat, n = n").
            proof_tactics: Proof tactics (default: empty = admit with Abort).

        Returns:
            Dict with keys: valid, error.
        """
        pt_lower = proof_tactics.strip().lower()
        if not pt_lower or "admitted" in pt_lower or "abort" in pt_lower:
            return {"valid": False, "error": "Empty or vacuous proof rejected: provide real Coq proof tactics, not 'Admitted' or 'Abort'."}

        code = f"""Theorem discovery_1 : {theorem_statement}.
Proof.
  {proof_tactics}
Qed.
"""
        result = self.check_proof(code)
        return {
            "valid": result["success"],
            "error": result.get("error"),
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

        # Semantic alignment check if enabled and at least one proof succeeded
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

            # Recalculate consensus after alignment filter
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
        """Verify multiple Coq snippets.

        Args:
            codes: List of Coq code strings.

        Returns:
            List of verification results.
        """
        results = []
        for i, code in enumerate(codes):
            result = self.check_proof(code)
            results.append({
                "index": i,
                "valid": result["success"],
                "error": result.get("error"),
                "goals": result.get("goals", []),
            })
        return results

    def get_environment(self) -> dict[str, Any]:
        """Get Coq environment info.

        Returns:
            Dict with keys: available, version, path.
        """
        return {
            "available": self.available,
            "version": self._get_version(),
            "path": self.coq_path,
        }
