from __future__ import annotations

import logging
from typing import Any

from src.mcp_server.tool_dependencies import (
    HAS_TOOLS,
    AgdaBridge,
    CoqClient,
    DafnyClient,
    Lean4Client,
    VerificationCalibrator,
    VerificationContext,
)


logger = logging.getLogger(__name__)


async def c4_verify(code: str, language: str | None = None) -> dict[str, Any]:
    """Verify formal proof in lean4, coq, dafny, agda, z3, hoare, cvc5, tla, or alloy."""
    try:
        if not HAS_TOOLS:
            return {"error": "Verification module not available"}

        if not language:
            calibrator = VerificationCalibrator()
            language = calibrator.select_backend(code, VerificationContext())

        if language == "lean4":
            client = Lean4Client()
            if not client.available:
                return {"valid": False, "error": "Lean4 not installed"}
            result = client.check_proof(code)
            return {
                "valid": result.get("success", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "coq":
            client = CoqClient()
            if not client.is_available():
                return {"valid": False, "error": "Coq not installed"}
            result = client.check_proof(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "dafny":
            client = DafnyClient()
            if not client.is_available():
                return {"valid": False, "error": "Dafny not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "agda":
            client = AgdaBridge()
            if not client.available:
                return {"valid": False, "error": "Agda not installed"}
            result = client.type_check(code)
            return {
                "valid": result.get("success", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "z3":
            try:
                import ast

                import z3

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
                    tree = ast.parse(code, mode="exec")
                    for node in ast.walk(tree):
                        if not isinstance(
                            node,
                            (
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
                            ),
                        ):
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
                        if (
                            isinstance(node, ast.Name)
                            and node.id not in z3_names
                            and node.id not in z3_attrs
                            and not node.id.startswith("_")
                        ):
                            pass  # Allow unknown names (could be Z3 variables)
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
                                    "error": f"Cannot call s.{func.attr}() without exec — use SMT-LIB2 format instead",
                                    "language": language,
                                }
                    return {
                        "valid": False,
                        "error": "Z3 Python code requires exec() which is disabled. Use SMT-LIB2 format (e.g. (declare-const x Int) (assert (> x 0)) (check-sat))",
                        "language": language,
                    }
                result = s.check()
                # sat = satisfiable, NOT theorem verified (HONESTY_CONTRACT).
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
            except (z3.Z3Exception, ValueError, RuntimeError) as e:
                logger.warning("Z3 verification error: language=%s error=%s", language, e)
                return {"valid": False, "error": f"Z3 error: {e}", "language": language}
        elif language == "hoare":
            from src.verification.hoare_verifier import HoareVerifier

            hv = HoareVerifier()
            result = hv.verify(code)
            return {
                "valid": result.valid,
                "proof": code,
                "language": language,
                "details": result.to_dict(),
                "error": result.error or None,
            }
        elif language == "cvc5":
            from src.verification.cvc5_client import CVC5Client

            client = CVC5Client()
            if not client.is_available():
                return {"valid": False, "error": "CVC5 not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language in ("tla", "tla+"):
            from src.verification.tla_client import TLAClient

            client = TLAClient()
            if not client.is_available():
                return {"valid": False, "error": "TLA+ TLC not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": "tla",
                "details": result,
            }
        elif language == "alloy":
            from src.verification.alloy_client import AlloyClient

            client = AlloyClient()
            if not client.is_available():
                return {"valid": False, "error": "Alloy not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language in ("haskell", "haskell-typecheck"):
            from src.verification.haskell_bridge import verify_haskell_typecheck

            result = verify_haskell_typecheck(code)
            valid = result.get("status") == "passed"
            return {
                "valid": valid,
                "proof": code,
                "language": "haskell-typecheck",
                "details": result,
                "error": None if valid else str(result.get("error", result.get("message", ""))),
            }
        elif language == "haskell-quickcheck":
            from src.verification.haskell_bridge import verify_haskell_quickcheck

            result = verify_haskell_quickcheck(code)
            valid = result.get("status") == "passed"
            return {
                "valid": valid,
                "proof": code,
                "language": "haskell-quickcheck",
                "details": result,
                "error": None if valid else str(result.get("error", result.get("message", ""))),
            }
        else:
            return {"valid": False, "error": f"Unsupported language: {language}"}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}
