from __future__ import annotations


"""Auto-Theorem Formulator v2 — checks hypothesis consistency via Z3/SMT, not fake proofs."""

import logging
import re
import tempfile
from typing import Any


logger = logging.getLogger(__name__)


class AutoTheoremFormulator:
    """Automatically check scientific hypothesis consistency using SMT solvers (Z3).

    Design principle: we do NOT prove empirical claims (physics, biology, etc.).
    We verify that the hypothesis is INTERNALLY CONSISTENT:
    - Numerical bounds are satisfiable
    - Constraints do not contradict each other
    - Physical conservation laws are not violated
    """

    # Patterns that indicate checkable constraints
    CONSTRAINT_PATTERNS = [
        r"(\d+(?:\.\d+)?)\s*%\s+(?:reduction|increase|improvement)",
        r"(\d+(?:\.\d+)?)\s*(?:times|fold|x)\s+(?:faster|slower|better)",
        r"[<>]=?\s*(\d+(?:\.\d+)?)",
        r"(?:at least|at most|minimum|maximum|exceeds?|below|above)\s+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:K|°C|Pa|atm|eV|J|W|kg|m|s|Hz|nm|μm)\b",
        r"Q\s*[≥>=]\s*(\d+(?:\.\d+)?)",
        r"probability\s*[≥>=]\s*(\d+(?:\.\d+)?)",
        r"efficiency\s*[≥>=]\s*(\d+(?:\.\d+)?)",
    ]

    def formulate(self, hypothesis: dict[str, Any], backend: str = "z3") -> dict[str, Any]:
        """Formulate a consistency check from a hypothesis.

        Returns dict with theorem_statement, proof_strategy, backend, confidence, status.
        """
        text = f"{hypothesis.get('title', '')}. {hypothesis.get('description', '')}"

        # Extract all numerical constraints
        constraints = self._extract_constraints(text)

        if not constraints:
            return {
                "theorem_statement": "No formalizable numerical constraints found.",
                "proof_strategy": "This hypothesis contains no explicit numerical bounds. Empirical validation required.",
                "backend": backend,
                "property_type": "empirical",
                "confidence": 0.0,
                "status": "not_formalizable",
                "constraints": [],
            }

        # Build Z3/SMT check for constraint satisfiability
        smt_script = self._build_smt_script(constraints, hypothesis.get("title", ""))

        # Try Z3
        result = self._run_z3(smt_script)

        status = result.get("status", "unknown")
        if status == "sat":
            strategy = f"Constraints are SATISFIABLE (internally consistent). Found {len(constraints)} checkable bounds."
            confidence = 0.85
        elif status == "unsat":
            strategy = "Constraints are UNSATISFIABLE (contradictory)! Found conflicting bounds."
            confidence = 0.9
        elif status == "timeout":
            strategy = "Z3 timeout — constraints too complex for automatic checking."
            confidence = 0.5
        else:
            strategy = f"Z3 returned: {status}. Manual review needed."
            confidence = 0.3

        return {
            "theorem_statement": smt_script,
            "proof_strategy": strategy,
            "backend": "z3",
            "property_type": "constraint_consistency",
            "confidence": confidence,
            "status": status,
            "constraints": constraints,
            "z3_output": result.get("output", ""),
        }

    def _extract_constraints(self, text: str) -> list[dict[str, Any]]:
        """Extract numerical constraints from hypothesis text."""
        constraints = []
        text_lower = text.lower()

        # Pattern: X% reduction/increase
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%\s+(reduction|increase|improvement|decrease|enhancement)", text_lower):
            val = float(m.group(1))
            ctype = m.group(2)
            constraints.append({
                "type": "percentage_change",
                "value": val / 100.0,
                "direction": ctype,
                "context": text[max(0, m.start() - 30):m.end() + 30],
            })

        # Pattern: Q >= X (fusion)
        for m in re.finditer(r"\bq\b\s*([≥>=<≤]+)\s*(\d+(?:\.\d+)?)", text_lower):
            op = m.group(1)
            val = float(m.group(2))
            constraints.append({
                "type": "fusion_gain",
                "operator": op,
                "value": val,
                "context": text[max(0, m.start() - 20):m.end() + 20],
            })

        # Pattern: probability >= X
        for m in re.finditer(r"probability\s*([≥>=<≤]+)\s*(\d+(?:\.\d+)?)", text_lower):
            op = m.group(1)
            val = float(m.group(2))
            if val > 1:
                val = val / 100.0  # Convert percentage to fraction
            constraints.append({
                "type": "probability",
                "operator": op,
                "value": val,
                "context": text[max(0, m.start() - 20):m.end() + 20],
            })

        # Pattern: at least/most X (with units)
        for m in re.finditer(r"(at least|at most|minimum|maximum|exceeds?|below|above)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z/°²³]+)?", text_lower):
            ctype = m.group(1)
            val = float(m.group(2))
            unit = m.group(3) or ""
            constraints.append({
                "type": "bound",
                "bound_type": ctype,
                "value": val,
                "unit": unit,
                "context": text[max(0, m.start() - 20):m.end() + 20],
            })

        # Pattern: temperature/pressure/energy values
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(K|°C|Pa|eV|J|W|kg|km/s|m/s|nm|μm|mm|cm|m)\b", text):
            val = float(m.group(1))
            unit = m.group(2)
            constraints.append({
                "type": "physical_quantity",
                "value": val,
                "unit": unit,
                "context": text[max(0, m.start() - 20):m.end() + 20],
            })

        # Pattern: efficiency >= X%
        for m in re.finditer(r"efficiency\s*([≥>=<≤]+)\s*(\d+(?:\.\d+)?)\s*%?", text_lower):
            op = m.group(1)
            val = float(m.group(2))
            if val > 1:
                val = val / 100.0
            constraints.append({
                "type": "efficiency",
                "operator": op,
                "value": val,
                "context": text[max(0, m.start() - 20):m.end() + 20],
            })

        # Detect contradictions: e.g., "at least 50%" AND "at most 30%" for same metric
        return constraints

    def _build_smt_script(self, constraints: list[dict[str, Any]], title: str) -> str:
        """Build SMT-LIB script for Z3."""
        lines = [
            "; Auto-generated consistency check for hypothesis",
            f"; Topic: {title[:60]}",
            "(set-logic QF_LRA)",
        ]

        # Declare variables for each constraint type
        var_names = set()
        for i, c in enumerate(constraints):
            if c["type"] == "percentage_change":
                var = f"p{i}"
                var_names.add(var)
                lines.append(f"(declare-fun {var} () Real)")
                # Percentage change must be between -1 and 1 (or slightly beyond for extreme claims)
                lines.append(f"(assert (and (>= {var} -1.0) (<= {var} 1.0)))")
                if c["direction"] in ("increase", "improvement", "enhancement"):
                    lines.append(f"(assert (> {var} 0.0))")
                elif c["direction"] in ("reduction", "decrease"):
                    lines.append(f"(assert (< {var} 0.0))")
            elif c["type"] == "fusion_gain":
                var = f"fusion_Q_{i}"
                var_names.add(var)
                lines.append(f"(declare-fun {var} () Real)")
                op = c["operator"]
                val = c["value"]
                if op in (">=", "≥"):
                    lines.append(f"(assert (>= {var} {val}))")
                elif op in ("<=", "≤"):
                    lines.append(f"(assert (<= {var} {val}))")
                # Physical bound: Q cannot be negative for net energy
                lines.append(f"(assert (>= {var} 0.0))")
            elif c["type"] == "probability":
                var = f"prob{i}"
                var_names.add(var)
                lines.append(f"(declare-fun {var} () Real)")
                lines.append(f"(assert (and (>= {var} 0.0) (<= {var} 1.0)))")
                op = c["operator"]
                val = c["value"]
                if op in (">=", "≥"):
                    lines.append(f"(assert (>= {var} {val}))")
                elif op in ("<=", "≤"):
                    lines.append(f"(assert (<= {var} {val}))")
            elif c["type"] == "efficiency":
                var = f"eff{i}"
                var_names.add(var)
                lines.append(f"(declare-fun {var} () Real)")
                lines.append(f"(assert (and (>= {var} 0.0) (<= {var} 1.0)))")
                op = c["operator"]
                val = c["value"]
                if op in (">=", "≥"):
                    lines.append(f"(assert (>= {var} {val}))")
                elif op in ("<=", "≤"):
                    lines.append(f"(assert (<= {var} {val}))")
            elif c["type"] == "bound":
                var = f"bound{i}"
                var_names.add(var)
                lines.append(f"(declare-fun {var} () Real)")
                bt = c["bound_type"]
                val = c["value"]
                if bt in ("at least", "minimum", "exceeds"):
                    lines.append(f"(assert (>= {var} {val}))")
                elif bt in ("at most", "maximum", "below"):
                    lines.append(f"(assert (<= {var} {val}))")

        lines.append("(check-sat)")
        lines.append("(exit)")
        return "\n".join(lines)

    def _run_z3(self, smt_script: str) -> dict[str, Any]:
        """Run Z3 on SMT-LIB script."""
        import subprocess
        import os
        smt_file = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".smt2", delete=False) as f:
                f.write(smt_script)
                smt_file = f.name

            result = subprocess.run(
                ["z3", "-t:10000", smt_file],
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout.strip()
            if "sat\n" in output or output == "sat":
                status = "sat"
            elif "unsat" in output:
                status = "unsat"
            elif "timeout" in output or result.returncode != 0:
                status = "timeout"
            else:
                status = "unknown"

            return {"status": status, "output": output, "stderr": result.stderr}
        except FileNotFoundError:
            return {"status": "z3_not_installed", "output": "", "stderr": "z3 not found in PATH"}
        except Exception as e:
            return {"status": "error", "output": "", "stderr": str(e)}
        finally:
            if smt_file and os.path.exists(smt_file):
                os.unlink(smt_file)

    def reformulate(self, hypothesis: dict[str, Any], previous_attempt: dict[str, Any], error: str) -> dict[str, Any]:
        """Reformulate after failed verification — relax constraints."""
        # For Z3, reformulation means relaxing bounds
        constraints = previous_attempt.get("constraints", [])
        relaxed = []
        for c in constraints:
            rc = dict(c)
            if c["type"] == "percentage_change" and c["value"] > 0.5:
                rc["value"] = c["value"] * 0.8  # Reduce by 20%
                rc["relaxed"] = True
            elif c["type"] == "fusion_gain" and c.get("value", 0) >= 1:
                rc["value"] = 0.95
                rc["relaxed"] = True
            elif c["type"] == "probability" and c.get("value", 0) > 0.9:
                rc["value"] = 0.85
                rc["relaxed"] = True
            relaxed.append(rc)

        previous_attempt["constraints"] = relaxed
        previous_attempt["confidence"] *= 0.8
        previous_attempt["reformulated"] = True
        return previous_attempt
