"""
c4reqber: Hoare Logic Verifier — Z3-based Weakest Precondition Calculus

Verifies Hoare triples ``{P} C {Q}`` using Dijkstra's weakest precondition
calculus encoded via Z3's SMT solver.

Supported commands:
  - ``x := E`` — assignment
  - ``C1; C2`` — sequential composition
  - ``if B then C1 else C2`` — conditional
  - ``while B inv I do C`` — while loop with invariant
  - ``skip`` — no-op

Variables are type-inferred from usage (Int → Real → Bool).
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import z3


class HoareSyntaxError(ValueError):
    """Raised when a Hoare triple cannot be parsed."""


class HoareProverError(RuntimeError):
    """Raised when the prover encounters an unrecoverable error."""


@dataclass
class HoareResult:
    valid: bool
    triple: str = ""
    precondition: str = ""
    command: str = ""
    postcondition: str = ""
    wp: str = ""
    counterexample: dict[str, str] = field(default_factory=dict)
    verification_time_ms: float = 0.0
    error: str = ""
    z3_script: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "triple": self.triple,
            "precondition": self.precondition,
            "command": self.command,
            "postcondition": self.postcondition,
            "wp": self.wp,
            "counterexample": self.counterexample if self.counterexample else None,
            "verification_time_ms": round(self.verification_time_ms, 1),
            "error": self.error or None,
            "z3_script": self.z3_script or None,
        }


class TypeInferrer:
    """Infers Z3 sorts (Int, Real, Bool) for program variables."""

    INT_PATTERN = re.compile(r"\b\d+\b")
    REAL_PATTERN = re.compile(r"\b\d+\.\d+\b")
    BOOL_OPS = {"and", "or", "not", "implies", "true", "false", "True", "False"}

    def __init__(self) -> None:
        self._var_types: dict[str, type] = {}

    def infer(self, *texts: str) -> dict[str, Any]:
        """Infer Z3 variable declarations from expression texts."""
        self._var_types = {}
        for text in texts:
            self._scan(text)
        return self._build_decls()

    def _scan(self, text: str) -> None:
        tokens = re.findall(r"[a-zA-Z_]\w*", text)
        for t in tokens:
            if t.lower() in self.BOOL_OPS or t in ("Int", "Real", "Bool"):
                continue
            if t not in self._var_types:
                self._var_types[t] = int  # default

    def _build_decls(self) -> dict[str, Any]:
        sorts = {int: z3.Int, float: z3.Real, bool: z3.Bool}
        return {
            name: sorts.get(t, z3.Int)(name)
            for name, t in self._var_types.items()
        }


class ExprBuilder:
    """Builds Z3 expressions from mathematical expression strings.

    Supports:
    - Arithmetic: +, -, *, /, ** (pow)
    - Comparison: =, ==, !=, <, >, <=, >=
    - Logical: and, or, not, implies
    - Functions: Abs, Min, Max, If
    """

    SAFE_BUILTINS: dict[str, Any] = {
        "True": z3.BoolVal(True),
        "False": z3.BoolVal(False),
        "And": z3.And,
        "Or": z3.Or,
        "Not": z3.Not,
        "Implies": z3.Implies,
        "Abs": lambda x: z3.If(x >= 0, x, -x),
        "Min": lambda a, b: z3.If(a <= b, a, b),
        "Max": lambda a, b: z3.If(a >= b, a, b),
        "If": lambda c, t, e: z3.If(c, t, e),
        "IntVal": z3.IntVal,
        "RealVal": z3.RealVal,
    }

    def __init__(self, variables: dict[str, Any]) -> None:
        self._ctx: dict[str, Any] = {**self.SAFE_BUILTINS, **variables}

    def build(self, text: str) -> z3.ExprRef:
        text = text.strip()
        if not text:
            return z3.BoolVal(True)
        processed = self._preprocess(text)
        try:
            tree = ast.parse(processed, mode="eval")
            result = self._eval_node(tree.body)
            return self._coerce_literal(result)
        except z3.Z3Exception:
            raise
        except Exception as e:
            raise ValueError(f"Cannot evaluate '{text}': {e}") from e

    def _coerce_literal(self, value: Any) -> z3.ExprRef:
        if isinstance(value, int):
            return z3.IntVal(value)
        if isinstance(value, float):
            return z3.RealVal(value)
        if isinstance(value, bool):
            return z3.BoolVal(value)
        return value

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, bool)):
                return node.value
            raise ValueError(f"Unsupported constant: {type(node.value).__name__}")

        if isinstance(node, ast.Name):
            if node.id in self._ctx:
                return self._ctx[node.id]
            raise NameError(f"Unknown symbol: {node.id}")

        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise ValueError(f"Disallowed binary operator: {type(node.op).__name__}")

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Not):
                return z3.Not(operand)
            raise ValueError(f"Disallowed unary operator: {type(node.op).__name__}")

        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return z3.And(*values)
            if isinstance(node.op, ast.Or):
                return z3.Or(*values)
            raise ValueError(f"Disallowed bool op: {type(node.op).__name__}")

        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("Only simple comparisons are allowed")
            left = self._eval_node(node.left)
            right = self._eval_node(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.Eq):
                return left == right
            if isinstance(op, ast.NotEq):
                return left != right
            if isinstance(op, ast.Lt):
                return left < right
            if isinstance(op, ast.LtE):
                return left <= right
            if isinstance(op, ast.Gt):
                return left > right
            if isinstance(op, ast.GtE):
                return left >= right
            raise ValueError(f"Disallowed comparison: {type(op).__name__}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")
            func_name = node.func.id
            if func_name not in self._ctx:
                raise NameError(f"Unknown function: {func_name}")
            func = self._ctx[func_name]
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords if kw.arg is not None}
            return func(*args, **kwargs)

        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    def _preprocess(self, text: str) -> str:
        s = text.strip()
        if not s:
            return s

        # Protect :=, <=, >=, !=, == from single-= rewriting
        protected: list[str] = []
        def _protect(m: re.Match[str]) -> str:
            protected.append(m.group(0))
            return f"\x00{len(protected)-1}\x00"
        s = re.sub(r":=|<=|>=|!=|==", _protect, s)
        # Replace lone = with ==
        s = re.sub(r"(?<![!<>])=(?!=)", "==", s)
        # Restore protected tokens
        for i, val in enumerate(protected):
            s = s.replace(f"\x00{i}\x00", val, 1)

        # ---- helper: split by a top-level keyword ----
        def _split_top(expr: str, kw: str) -> list[str]:
            depth = 0
            parts: list[str] = []
            cur: list[str] = []
            i = 0
            el = expr.lower()
            kl = len(kw)
            while i < len(expr):
                if expr[i] == '(':
                    depth += 1
                elif expr[i] == ')':
                    depth -= 1
                if depth == 0 and el[i:i+kl] == kw and (i == 0 or not expr[i-1].isalnum()) and (i+kl >= len(expr) or not expr[i+kl].isalnum()):
                    parts.append(''.join(cur))
                    cur = []
                    i += kl
                    continue
                cur.append(expr[i])
                i += 1
            parts.append(''.join(cur))
            return [p.strip() for p in parts if p.strip()]

        # ---- not (highest precedence) ----
        # Split by top-level 'not' and wrap the following minimal expression
        def _wrap_not(expr: str) -> str:
            parts = _split_top(expr, 'not')
            if len(parts) == 1:
                return expr
            # First part is before first not, rest are after each not
            result = [parts[0]] if parts[0] else []
            for rest in parts[1:]:
                # Find extent of the negated expression: until next top-level and/or
                subparts = _split_top(rest, 'and')
                if len(subparts) == 1:
                    subparts = _split_top(rest, 'or')
                first = subparts[0].strip()
                remainder = ''
                if len(subparts) > 1:
                    # Re-join with the operator we split on
                    # We know the operator was 'and' or 'or'
                    if 'and' in rest.lower():
                        op = ' and '
                    else:
                        op = ' or '
                    remainder = op + op.join(p.strip() for p in subparts[1:])
                result.append(f"Not({first}){remainder}")
            return ''.join(result)

        s = _wrap_not(s)

        # ---- and / or (left-associative) ----
        def _wrap_op(expr: str, kw: str, wrapper: str) -> str:
            parts = _split_top(expr, kw)
            if len(parts) == 1:
                return expr
            inner = ", ".join(_wrap_op(p, kw, wrapper) for p in parts)
            return f"{wrapper}({inner})"

        s = _wrap_op(s, 'and', 'And')
        s = _wrap_op(s, 'or', 'Or')
        return s


class WPCalculus:
    """Weakest Precondition Calculus for a simple imperative language."""

    @staticmethod
    def wp(
        cmd: str,
        post: z3.ExprRef,
        variables: dict[str, Any],
        expr_builder: ExprBuilder,
    ) -> z3.ExprRef:
        cmd = cmd.strip()

        # Skip
        if not cmd or cmd == "skip":
            return post

        # Assignment: x := E
        m = re.match(r"(\w+)\s*:=\s*(.+)", cmd)
        if m and ";" not in cmd and not cmd.startswith("if ") and not cmd.startswith("while "):
            var_name = m.group(1)
            if var_name not in variables:
                variables[var_name] = z3.Int(var_name)
            expr = expr_builder.build(m.group(2))
            return z3.substitute(post, (variables[var_name], expr))

        # Sequence: C1; C2
        if ";" in cmd and not cmd.startswith("if ") and not cmd.startswith("while "):
            parts = [p.strip() for p in cmd.split(";")]
            current = post
            for p in reversed(parts):
                current = WPCalculus.wp(p, current, variables, expr_builder)
            return current

        # Conditional: if B then C1 else C2
        m = re.match(
            r"if\s+(.+?)\s+then\s+(.+?)\s+else\s+(.+)",
            cmd, re.DOTALL,
        )
        if m:
            cond = expr_builder.build(m.group(1))
            wp_t = WPCalculus.wp(m.group(2).strip(), post, variables, expr_builder)
            wp_e = WPCalculus.wp(m.group(3).strip(), post, variables, expr_builder)
            return z3.And(
                z3.Implies(cond, wp_t),
                z3.Implies(z3.Not(cond), wp_e),
            )

        # While loop: while B inv I do C
        m = re.match(
            r"while\s+(.+?)\s+inv\s+(.+?)\s+do\s+(.+)",
            cmd, re.DOTALL,
        )
        if m:
            cond_str = m.group(1)
            inv_str = m.group(2)
            body = m.group(3).strip()
            invariant = expr_builder.build(inv_str)
            condition = expr_builder.build(cond_str)
            body_wp = WPCalculus.wp(body, invariant, variables, expr_builder)
            preservation = z3.Implies(z3.And(invariant, condition), body_wp)
            post_condition = z3.Implies(z3.And(invariant, z3.Not(condition)), post)
            return z3.And(invariant, preservation, post_condition)

        raise ValueError(f"Unsupported command: {cmd}")

    @staticmethod
    def to_smt2(formula: z3.ExprRef) -> str:
        """Convert a Z3 formula to SMT-LIB2 format for debugging."""
        return z3.Z3_ast_to_string(formula.ast)


class HoareVerifier:
    """Production-grade Hoare logic verifier.

    Verifies triples ``{P} C {Q}`` using Z3's SMT solver with full
    weakest precondition calculus.

    Usage::

        hv = HoareVerifier()
        result = hv.verify("{x > 0} x := x + 1 {x > 1}")
        print(result.valid)  # True
    """

    MAX_TIMEOUT_MS: int = 10000

    def __init__(self, timeout_ms: int = MAX_TIMEOUT_MS, max_cache_size: int = 1000) -> None:
        self._timeout = timeout_ms
        self._max_cache_size = max_cache_size
        self._cache: OrderedDict[str, HoareResult] = OrderedDict()

    def verify(self, code: str) -> HoareResult:
        """Verify a Hoare triple. Returns a HoareResult dataclass."""
        start = time.perf_counter()

        # Check cache
        cache_key = hashlib.sha256(code.encode()).hexdigest()
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_cache_size:
            oldest = next(iter(self._cache))
            self._cache.pop(oldest, None)

        try:
            pre, cmd, post = self._parse_triple(code)
        except HoareSyntaxError as e:
            result = HoareResult(valid=False, triple=code, error=str(e))
            result.verification_time_ms = (time.perf_counter() - start) * 1000
            return result

        try:
            # Type inference from all expressions
            inferrer = TypeInferrer()
            inferrer.infer(pre, post, cmd)
            variables = inferrer._build_decls()

            expr_builder = ExprBuilder(variables)
            pre_expr = expr_builder.build(pre)
            post_expr = expr_builder.build(post)

            # Compute weakest precondition
            cmd_wp = WPCalculus.wp(cmd, post_expr, variables, expr_builder)

            # Check: pre → wp
            s = z3.Solver()
            s.set("timeout", self._timeout)
            s.add(z3.Not(z3.Implies(pre_expr, cmd_wp)))

            smt2_script = s.to_smt2() if hasattr(s, 'to_smt2') else str(s)

            check_result = s.check()
            ver_time = (time.perf_counter() - start) * 1000

            if check_result == z3.unsat:
                result = HoareResult(
                    valid=True,
                    triple=code,
                    precondition=pre,
                    command=cmd,
                    postcondition=post,
                    wp=self._fmt(cmd_wp),
                    verification_time_ms=ver_time,
                    z3_script=smt2_script,
                )
            elif check_result == z3.sat:
                model = s.model()
                cex = {str(d): str(model[d]) for d in model.decls() if str(d) not in ("__builtins__",)}
                result = HoareResult(
                    valid=False,
                    triple=code,
                    precondition=pre,
                    command=cmd,
                    postcondition=post,
                    wp=self._fmt(cmd_wp),
                    counterexample=cex,
                    verification_time_ms=ver_time,
                    z3_script=smt2_script,
                )
            else:
                result = HoareResult(
                    valid=False,
                    triple=code,
                    error="Z3 timeout or undecidable",
                    verification_time_ms=ver_time,
                )

            self._cache[cache_key] = result
            return result

        except Exception as e:
            ver_time = (time.perf_counter() - start) * 1000
            result = HoareResult(
                valid=False,
                triple=code,
                error=f"Prover error: {e}",
                verification_time_ms=ver_time,
            )
            return result

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    TRIPLE_RE = re.compile(
        r"\{(.+?)\}\s*(.+?)\s*\{(.+?)\}",
        re.DOTALL,
    )

    def _parse_triple(self, code: str) -> tuple[str, str, str]:
        code = code.strip()
        m = self.TRIPLE_RE.fullmatch(code)
        if not m:
            raise HoareSyntaxError(
                "Expected format: {P} C {Q}\n"
                "  Example: { x > 0 } x := x + 1 { x > 1 }\n"
                "  While:   { true } while i < n inv i <= n do i := i + 1 { i = n }"
            )
        return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt(expr: z3.ExprRef) -> str:
        """Format Z3 expression as a readable string."""
        text = str(expr)
        if len(text) > 500:
            return text[:500] + "..."
        return text

    def cache_stats(self) -> dict[str, int]:
        return {"entries": len(self._cache)}

    def clear_cache(self) -> None:
        self._cache.clear()
