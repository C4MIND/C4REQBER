from __future__ import annotations

import ast
import logging
from typing import Any


logger = logging.getLogger(__name__)


def verify_z3_mcp(code: str, language: str = "z3") -> dict[str, Any]:
    """Run Z3 check for MCP c4_verify; sat ≠ verified (HONESTY_CONTRACT)."""
    try:
        import z3
    except ImportError as e:
        return {"valid": False, "error": f"Z3 not installed: {e}", "language": language}

    s = z3.Solver()
    s.set("timeout", 5000)  # prevent DoS from exponential SMT-LIB2 blowup
    try:
        s.from_string(code)
    except z3.Z3Exception as e:
        logger.warning("Z3 parse error: language=%s error=%s", language, e)
        return {
            "error": f"Z3 parse error: {e}",
            "status": "error",
            "language": language,
        }
    except (ValueError, RuntimeError):
        return _reject_z3_python(code, language)

    result = s.check()
    if result == z3.sat:
        return {
            "valid": False,
            "verified": False,
            "satisfiable": True,
            "proof": code,
            "language": language,
            "status": "partial",
            "note": "z3.sat means satisfiable, not formally verified",
            "details": {"status": str(result), "model": str(s.model())},
        }
    if result == z3.unsat:
        return {
            "valid": False,
            "verified": False,
            "satisfiable": False,
            "proof": code,
            "language": language,
            "status": "partial",
            "note": "unsat without explicit proof-goal semantics",
            "details": {"status": str(result)},
        }
    return {
        "valid": False,
        "verified": False,
        "satisfiable": None,
        "proof": code,
        "language": language,
        "status": "error",
        "details": {"status": str(result)},
    }


def _reject_z3_python(code: str, language: str) -> dict[str, Any]:
    tree = ast.parse(code, mode="exec")
    allowed = (
        ast.Module,
        ast.Expr,
        ast.Call,
        ast.Name,
        ast.Constant,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.BoolOp,
        ast.Attribute,
        ast.Subscript,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            return {
                "valid": False,
                "error": f"Invalid AST node: {type(node).__name__}",
                "language": language,
            }
        if isinstance(node, ast.Name) and node.id in (
            "__import__",
            "eval",
            "exec",
            "compile",
            "open",
            "os",
            "sys",
        ):
            return {
                "valid": False,
                "error": f"Dangerous name: {node.id}",
                "language": language,
            }

    z3_names = {
        "Int",
        "Real",
        "Bool",
        "And",
        "Or",
        "Not",
        "Implies",
        "ForAll",
        "Exists",
        "If",
        "Distinct",
        "Sum",
        "Product",
        "BitVec",
        "BitVecVal",
        "IntVal",
        "RealVal",
        "BoolVal",
        "true",
        "false",
        "solve",
        "prove",
    }
    z3_attrs = {
        "add",
        "check",
        "model",
        "assert_and_track",
        "push",
        "pop",
        "reset",
        "to_smt2",
        "sexpr",
        "set",
        "from_string",
        "Solver",
        "SimpleSolver",
        "Tactic",
        "Then",
        "Repeat",
        "OrElse",
        "With",
        "ParOr",
        "ParThen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "s":
                    return {
                        "valid": False,
                        "error": "Cannot reassign 's' — use s.add()",
                        "language": language,
                    }
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "s"
                and func.attr in z3_attrs
            ):
                return {
                    "valid": False,
                    "error": (
                        f"Cannot call s.{func.attr}() without exec — use SMT-LIB2 format instead"
                    ),
                    "language": language,
                }
    return {
        "valid": False,
        "error": (
            "Z3 Python code requires exec() which is disabled. "
            "Use SMT-LIB2 format (e.g. (declare-const x Int) "
            "(assert (> x 0)) (check-sat))"
        ),
        "language": language,
    }
