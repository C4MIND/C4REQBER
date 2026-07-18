"""Hoare logic verifier client for C44TCDI.

Provides verification of Hoare triples {P} C {Q} using z3-solver when available,
with a fallback to basic parsing and symbolic execution for simple cases.
"""

from __future__ import annotations

import ast
import re
from typing import Any


class HoareClient:
    """Hoare logic verification client."""

    def __init__(self) -> None:
        self._z3: Any | None = None
        self._z3_available: bool | None = None
        self._try_import_z3()

    def _try_import_z3(self) -> None:
        try:
            import z3

            self._z3 = z3
            self._z3_available = True
        except ImportError:
            self._z3_available = False

    @property
    def available(self) -> bool:
        """Whether z3-solver is installed."""
        return bool(self._z3_available)

    def test_connection(self) -> dict[str, Any]:
        """Check if the z3 backend is available.

        Returns:
            Dict with keys: available, error.
        """
        if self.available:
            return {"available": True, "error": None}
        return {
            "available": False,
            "error": "z3-solver not installed; running in fallback mode",
        }

    def verify(self, triple: str) -> dict[str, Any]:
        """Verify a Hoare triple {P} C {Q}.

        Args:
            triple: Hoare triple string in ``{P} C {Q}`` format.

        Returns:
            Dict with keys: valid, counterexample, error.
        """
        parsed = self._parse_triple(triple)
        if parsed.get("error"):
            return {
                "valid": False,
                "counterexample": None,
                "error": parsed["error"],
            }

        precondition = parsed["precondition"]
        command = parsed["command"]
        postcondition = parsed["postcondition"]

        if self.available and self._z3 is not None:
            return self._verify_with_z3(precondition, command, postcondition)

        return self._verify_fallback(precondition, command, postcondition)

    def check_precondition(self, program: str, precondition: str) -> dict[str, Any]:
        """Check if a precondition holds for a program.

        Args:
            program: Program/command string.
            precondition: Precondition predicate.

        Returns:
            Dict with keys: valid, counterexample, error.
        """
        return self.verify(f"{{{precondition}}} {program} {{True}}")

    def check_postcondition(self, program: str, postcondition: str) -> dict[str, Any]:
        """Check if a postcondition holds for a program.

        Args:
            program: Program/command string.
            postcondition: Postcondition predicate.

        Returns:
            Dict with keys: valid, counterexample, error.
        """
        return self.verify(f"{{True}} {program} {{{postcondition}}}")

    def verify_batch(self, triples: list[str]) -> list[dict[str, Any]]:
        """Verify multiple Hoare triples.

        Args:
            triples: List of Hoare triple strings.

        Returns:
            List of result dicts.
        """
        return [self.verify(t) for t in triples]

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_triple(triple: str) -> dict[str, Any]:
        pattern = re.compile(r"\{([^}]*)\}\s*(.*?)\s*\{([^}]*)\}")
        match = pattern.search(triple.strip())
        if not match:
            return {"error": f"Invalid Hoare triple format: {triple!r}"}
        return {
            "precondition": match.group(1).strip(),
            "command": match.group(2).strip(),
            "postcondition": match.group(3).strip(),
            "error": None,
        }

    # ------------------------------------------------------------------
    # Z3 backend
    # ------------------------------------------------------------------

    def _verify_with_z3(
        self, precondition: str, command: str, postcondition: str
    ) -> dict[str, Any]:
        z3 = self._z3
        assert z3 is not None
        solver = z3.Solver()

        # Extract variable names
        vars_pre = self._extract_variables(precondition)
        vars_post = self._extract_variables(postcondition)
        vars_cmd = self._extract_variables(command)
        all_vars = vars_pre | vars_post | vars_cmd

        # Create z3 variables (Int sort for simplicity)
        z3_vars: dict[str, Any] = {}
        for v in all_vars:
            z3_vars[v] = z3.Int(v)

        # Parse precondition and add as assumption
        try:
            pre_expr = self._expr_to_z3(precondition, z3_vars)
            if pre_expr is not None:
                solver.add(pre_expr)
        except (ValueError, TypeError, KeyError) as e:
            return {
                "valid": False,
                "counterexample": None,
                "error": f"Failed to parse precondition: {e}",
            }

        # Compute weakest precondition / postcondition via simple symbolic exec
        try:
            wp = self._symbolic_execute(command, postcondition, z3_vars)
        except (ValueError, TypeError, KeyError) as e:
            return {
                "valid": False,
                "counterexample": None,
                "error": f"Symbolic execution failed: {e}",
            }

        if wp is None:
            return {
                "valid": False,
                "counterexample": None,
                "error": "Unsupported command for symbolic execution",
            }

        # We want to check: precondition => wp
        # So we assert precondition AND NOT(wp) and check unsat
        try:
            wp_expr = self._expr_to_z3(wp, z3_vars)
            if wp_expr is None:
                return {
                    "valid": False,
                    "counterexample": None,
                    "error": f"Failed to parse weakest precondition: {wp}",
                }

            if pre_expr is not None:
                solver.add(z3.Not(z3.Implies(pre_expr, wp_expr)))
            else:
                solver.add(z3.Not(wp_expr))
        except (ValueError, TypeError, KeyError) as e:
            return {
                "valid": False,
                "counterexample": None,
                "error": f"Z3 encoding error: {e}",
            }

        result = solver.check()
        if result == z3.unsat:
            return {"valid": True, "counterexample": None, "error": None}
        elif result == z3.sat:
            model = solver.model()
            counterexample = {}
            for v in all_vars:
                val = model.evaluate(z3_vars[v], model_completion=True)
                counterexample[v] = str(val)
            return {
                "valid": False,
                "counterexample": counterexample,
                "error": None,
            }
        else:
            return {
                "valid": False,
                "counterexample": None,
                "error": "Z3 returned unknown",
            }

    # ------------------------------------------------------------------
    # Fallback backend (no z3)
    # ------------------------------------------------------------------

    def _verify_fallback(
        self, precondition: str, command: str, postcondition: str
    ) -> dict[str, Any]:
        vars_pre = self._extract_variables(precondition)
        vars_post = self._extract_variables(postcondition)
        vars_cmd = self._extract_variables(command)

        # Trivial case: True postcondition is always valid (heuristic fallback)
        if postcondition.strip() in ("True", "true", "1"):
            return {
                "valid": True,
                "counterexample": None,
                "error": None,
                "mode": "fallback",
                "heuristic": True,
            }

        # Simple sanity check: variables mentioned in post should be assigned in command
        # or exist in precondition
        assigned = self._extract_assigned_variables(command)
        for v in vars_post:
            if v not in assigned and v not in vars_pre and v not in vars_cmd:
                return {
                    "valid": False,
                    "counterexample": None,
                    "error": f"Variable '{v}' in postcondition not defined",
                    "mode": "fallback",
                    "heuristic": True,
                }

        # Try simple symbolic execution for basic assignments
        try:
            wp = self._symbolic_execute(command, postcondition, {})
        except (ValueError, TypeError, KeyError):
            wp = None

        if wp is not None:
            # Simple syntactic check: if wp looks "similar" to precondition
            if self._syntactically_implies(precondition, wp):
                return {
                    "valid": True,
                    "counterexample": None,
                    "error": None,
                    "mode": "fallback",
                    "heuristic": True,
                }

        # Basic pattern matching for common cases
        if self._check_simple_patterns(precondition, command, postcondition):
            return {
                "valid": True,
                "counterexample": None,
                "error": None,
                "mode": "fallback",
                "heuristic": True,
            }

        return {
            "valid": False,
            "counterexample": None,
            "error": "Fallback mode: unable to verify (z3 not installed)",
            "mode": "fallback",
            "heuristic": True,
        }

    # ------------------------------------------------------------------
    # Symbolic execution
    # ------------------------------------------------------------------

    @staticmethod
    def _symbolic_execute(command: str, postcondition: str, _z3_vars: dict[str, Any]) -> str | None:
        """Compute weakest precondition for simple imperative commands."""
        command = command.strip()

        # Assignment: x := expr  or  x = expr
        assign_match = re.match(r"^(\w+)\s*:=\s*(.+)$", command)
        if not assign_match:
            assign_match = re.match(r"^(\w+)\s*=\s*(.+)$", command)
        if assign_match:
            var = assign_match.group(1)
            expr = assign_match.group(2).strip()
            # Substitute var with expr in postcondition
            return HoareClient._substitute(postcondition, var, expr)

        # Sequence: C1 ; C2
        if ";" in command:
            parts = [p.strip() for p in command.split(";") if p.strip()]
            wp: str | None = postcondition
            for part in reversed(parts):
                if wp is None:
                    return None
                wp = HoareClient._symbolic_execute(part, wp, _z3_vars)
            return wp

        # Skip / empty
        if command.lower() in ("skip", "", "noop"):
            return postcondition

        return None

    @staticmethod
    def _substitute(expr: str, var: str, replacement: str) -> str:
        """Substitute variable with replacement in expression."""
        # Use regex to match whole words only
        pattern = re.compile(r"\b" + re.escape(var) + r"\b")
        return pattern.sub(replacement, expr)

    # ------------------------------------------------------------------
    # Variable extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_variables(expr: str) -> set[str]:
        """Extract variable names from an arithmetic/boolean expression."""
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError:
            # Fallback: regex extraction for simple identifiers
            return set(re.findall(r"\b[a-zA-Z_]\w*\b", expr)) - set(
                ["True", "False", "and", "or", "not", "in", "is", "if", "else"]
            )

        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                variables.add(node.id)
        return variables

    @staticmethod
    def _extract_assigned_variables(command: str) -> set[str]:
        """Extract variables that are assigned in a command."""
        assigned = set()
        for line in command.split(";"):
            line = line.strip()
            match = re.match(r"^(\w+)\s*[:=]\s*", line)
            if match:
                assigned.add(match.group(1))
        return assigned

    # ------------------------------------------------------------------
    # Z3 expression builder
    # ------------------------------------------------------------------

    def _expr_to_z3(self, expr: str, z3_vars: dict[str, Any]) -> Any | None:
        """Convert a Python-like expression to a Z3 expression."""
        assert self._z3 is not None
        if not expr or expr == "True":
            return self._z3.BoolVal(True)
        if expr == "False":
            return self._z3.BoolVal(False)

        try:
            tree = ast.parse(expr, mode="eval")
            return self._ast_to_z3(tree.body, z3_vars)
        except SyntaxError as exc:
            raise ValueError(f"Cannot parse expression: {expr}") from exc

    def _ast_to_z3(self, node: ast.AST, z3_vars: dict[str, Any]) -> Any:
        z3 = self._z3
        assert z3 is not None
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return z3.BoolVal(node.value)
            return z3.IntVal(node.value)
        if isinstance(node, ast.Name):
            if node.id in z3_vars:
                return z3_vars[node.id]
            if node.id == "True":
                return z3.BoolVal(True)
            if node.id == "False":
                return z3.BoolVal(False)
            raise ValueError(f"Unknown variable: {node.id}")
        if isinstance(node, ast.BinOp):
            left = self._ast_to_z3(node.left, z3_vars)
            right = self._ast_to_z3(node.right, z3_vars)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Mod):
                return left % right
            if isinstance(node.op, ast.Pow):
                return left**right
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        if isinstance(node, ast.UnaryOp):
            operand = self._ast_to_z3(node.operand, z3_vars)
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Not):
                return z3.Not(operand)
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        if isinstance(node, ast.Compare):
            left = self._ast_to_z3(node.left, z3_vars)
            result = None
            for op, comparator in zip(node.ops, node.comparators, strict=False):
                right = self._ast_to_z3(comparator, z3_vars)
                cmp = None
                if isinstance(op, ast.Eq):
                    cmp = left == right
                elif isinstance(op, ast.NotEq):
                    cmp = left != right
                elif isinstance(op, ast.Lt):
                    cmp = left < right
                elif isinstance(op, ast.LtE):
                    cmp = left <= right
                elif isinstance(op, ast.Gt):
                    cmp = left > right
                elif isinstance(op, ast.GtE):
                    cmp = left >= right
                else:
                    raise ValueError(f"Unsupported comparison: {type(op).__name__}")
                result = cmp if result is None else z3.And(result, cmp)
                left = right
            return result
        if isinstance(node, ast.BoolOp):
            values = [self._ast_to_z3(v, z3_vars) for v in node.values]
            if isinstance(node.op, ast.And):
                return z3.And(*values)
            if isinstance(node.op, ast.Or):
                return z3.Or(*values)
            raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "abs" and len(node.args) == 1:
                arg = self._ast_to_z3(node.args[0], z3_vars)
                return z3.If(arg >= 0, arg, -arg)
            raise ValueError(f"Unsupported function call: {ast.dump(node)}")
        raise ValueError(f"Unsupported AST node: {ast.dump(node)}")

    # ------------------------------------------------------------------
    # Simple pattern checks (fallback)
    # ------------------------------------------------------------------

    @staticmethod
    def _check_simple_patterns(precondition: str, command: str, postcondition: str) -> bool:
        """Check common Hoare triple patterns without z3."""
        # Pattern: {x > n} x := x + 1 {x > n + 1}
        inc_match = re.match(r"^(\w+)\s*:=\s*\1\s*\+\s*(\d+)$", command.strip())
        if inc_match:
            var = inc_match.group(1)
            k = int(inc_match.group(2))
            pre_match = re.match(rf"^{var}\s*>\s*(\d+)$", precondition.strip())
            post_match = re.match(rf"^{var}\s*>\s*(\d+)$", postcondition.strip())
            if pre_match and post_match:
                pre_n = int(pre_match.group(1))
                post_n = int(post_match.group(1))
                return pre_n + k >= post_n

        # Pattern: {x > n} x := x - 1 {x > n - 1}
        dec_match = re.match(r"^(\w+)\s*:=\s*\1\s*-\s*(\d+)$", command.strip())
        if dec_match:
            var = dec_match.group(1)
            k = int(dec_match.group(2))
            pre_match = re.match(rf"^{var}\s*>\s*(\d+)$", precondition.strip())
            post_match = re.match(rf"^{var}\s*>\s*(\d+)$", postcondition.strip())
            if pre_match and post_match:
                pre_n = int(pre_match.group(1))
                post_n = int(post_match.group(1))
                return pre_n - k >= post_n

        # Pattern: {True} x := c {x == c}
        const_match = re.match(r"^(\w+)\s*:=\s*(.+)$", command.strip())
        if const_match and precondition.strip() in ("True", "true", "1", ""):
            var = const_match.group(1)
            const_val = const_match.group(2).strip()
            post_pattern = re.match(rf"^{var}\s*==\s*(.+)$", postcondition.strip())
            if post_pattern:
                return post_pattern.group(1).strip() == const_val

        return False

    @staticmethod
    def _syntactically_implies(precondition: str, wp: str) -> bool:
        """Very simple syntactic implication check."""
        pre = precondition.replace(" ", "")
        wp_clean = wp.replace(" ", "")
        if pre == wp_clean:
            return True
        # e.g. x>0 implies x+1>1
        match_pre = re.match(r"^(\w+)>(\d+)$", pre)
        match_wp = re.match(r"^(\w+)\+1>(\d+)$", wp_clean)
        if match_pre and match_wp:
            if match_pre.group(1) == match_wp.group(1):
                return int(match_pre.group(2)) + 1 >= int(match_wp.group(2))
        return False
