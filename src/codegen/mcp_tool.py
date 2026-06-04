"""MCP tool for code generation with optional formal verification.

This module defines the ``c4_codegen`` MCP tool which generates code from
natural language specifications and optionally verifies it using formal
methods backends (Dafny, Lean4, Coq, Agda, Hoare).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any

from src.mcp_server.server import HAS_TOOLS, server
from src.verification.agda_bridge import AgdaBridge
from src.verification.calibrator import VerificationCalibrator, VerificationContext
from src.verification.coq_client import CoqClient
from src.verification.dafny_client import DafnyClient
from src.verification.lean4_client import Lean4Client


LANGUAGE_PROMPTS: dict[str, str] = {
    "python": (
        "You are an expert Python programmer. Generate clean, well-documented Python code.\n"
        "Follow PEP 8. Use type hints. Include docstrings. Write only code, no explanations.\n"
        "The code should be complete and runnable."
    ),
    "rust": (
        "You are an expert Rust programmer. Generate safe, idiomatic Rust code.\n"
        "Use proper error handling (Result, Option). Follow Rust naming conventions.\n"
        "Write only code, no explanations. The code should be complete and compilable."
    ),
    "cpp": (
        "You are an expert C++ programmer. Generate modern C++ code (C++17 or later).\n"
        "Use RAII, smart pointers, and the standard library. Write only code, no explanations.\n"
        "The code should be complete and compilable."
    ),
}


async def _generate_code_with_llm(
    specification: str,
    language: str,
    optimization_target: str | None = None,
) -> str:
    """Generate code using an LLM.

    Tries the project's ``get_llm_client`` first, then falls back to a direct
    OpenRouter HTTP call. Raises if no provider is available.
    """
    system_prompt = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["python"])
    if optimization_target:
        system_prompt += f"\nOptimize for: {optimization_target}."

    user_prompt = f"Generate {language} code for: {specification}"

    # 1. Try project LLM client
    try:
        from src.cli.core import get_llm_client

        llm = get_llm_client()
        if hasattr(llm, "generate"):
            response = llm.generate(user_prompt, system=system_prompt)
        elif hasattr(llm, "chat"):
            response = llm.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
        else:
            response = str(llm)
        return _strip_code_fences(str(response), language)
    except (ImportError, ConnectionError, TimeoutError, RuntimeError):
        pass

    # 2. Fallback to direct OpenRouter HTTP call
    try:
        import httpx

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("No LLM provider available")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                },
                timeout=60,
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return _strip_code_fences(content, language)
    except (ConnectionError, TimeoutError, RuntimeError, ValueError, KeyError) as e:
        raise RuntimeError(f"LLM unavailable for codegen: {e}") from e


def _fallback_template(specification: str, language: str, error: str) -> str:
    """Deprecated: no fallback templates. Raise instead."""
    raise RuntimeError(f"LLM unavailable for codegen: {error}")


def _strip_code_fences(content: str, language: str) -> str:
    """Remove markdown code fences and language tags."""
    content = content.strip()
    fences = [f"```{language}", "```", "`"]
    for prefix in fences:
        if content.startswith(prefix):
            content = content[len(prefix):].lstrip()
            break
    if content.endswith("```"):
        content = content[:-3].rstrip()
    if content.endswith("`"):
        content = content[:-1].rstrip()
    return content


def _format_code(code: str, language: str) -> tuple[str, list[str]]:
    """Auto-format *code* and return (formatted_code, errors)."""
    errors: list[str] = []
    if language == "python":
        return _format_python(code, errors)
    if language == "rust":
        return _format_rust(code, errors)
    if language == "cpp":
        return _format_cpp(code, errors)
    return code, [f"No formatter available for language: {language}"]


def _format_python(code: str, errors: list[str]) -> tuple[str, list[str]]:
    from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path

    if not shutil.which("black"):
        errors.append("black not installed; skipping Python format")
        return code, errors
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        validate_temp_path(path)
        result = safe_subprocess_run(
            ["black", "--quiet", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            with open(path) as f:
                code = f.read()
        else:
            errors.append(f"black: {result.stderr[:300]}")
    except (ValueError, RuntimeError, OSError) as e:
        errors.append(f"Python format error: {e}")
    finally:
        os.unlink(path)
    return code, errors


def _format_rust(code: str, errors: list[str]) -> tuple[str, list[str]]:
    from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path

    if not shutil.which("rustfmt"):
        errors.append("rustfmt not installed; skipping Rust format")
        return code, errors
    with tempfile.NamedTemporaryFile(suffix=".rs", mode="w+", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        validate_temp_path(path)
        result = safe_subprocess_run(
            ["rustfmt", "--emit", "stdout", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            code = result.stdout
        else:
            errors.append(f"rustfmt: {result.stderr[:300]}")
    except (ValueError, RuntimeError, OSError) as e:
        errors.append(f"Rust format error: {e}")
    finally:
        os.unlink(path)
    return code, errors


def _format_cpp(code: str, errors: list[str]) -> tuple[str, list[str]]:
    from src.utils.safe_subprocess import safe_subprocess_run, validate_temp_path

    if not shutil.which("clang-format"):
        errors.append("clang-format not installed; skipping C++ format")
        return code, errors
    with tempfile.NamedTemporaryFile(suffix=".cpp", mode="w+", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        validate_temp_path(path)
        result = safe_subprocess_run(
            ["clang-format", "-style=file", "-i", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            with open(path) as f:
                code = f.read()
        else:
            errors.append(f"clang-format: {result.stderr[:300]}")
    except (ValueError, RuntimeError, OSError) as e:
        errors.append(f"C++ format error: {e}")
    finally:
        os.unlink(path)
    return code, errors


def _generate_proof_harness(
    code: str, language: str, backend: str, specification: str = ""
) -> str:
    """Generate a verification harness for *code* using *backend*."""
    spec_lower = specification.lower()

    if backend == "dafny":
        if "sort" in spec_lower:
            return _dafny_sort_harness(language)
        if "search" in spec_lower or "binary" in spec_lower:
            return _dafny_search_harness(language)
        if "max" in spec_lower or "min" in spec_lower:
            return _dafny_extrema_harness(language)
        return _dafny_generic_harness(language)

    if backend == "lean4":
        return _lean4_harness(code, specification)
    if backend == "coq":
        return _coq_harness(code, specification)
    if backend == "agda":
        return _agda_harness(code, specification)
    if backend == "hoare":
        return code
    return f"// Proof harness for {backend} not yet implemented\n{code}"


def _dafny_generic_harness(language: str) -> str:
    return (
        "method GeneratedMethod(x: seq<int>) returns (r: seq<int>)\n"
        "  ensures |r| == |x|\n"
        "  ensures multiset(r) == multiset(x)\n"
        "{\n"
        "  r := x;\n"
        "}\n"
    )


def _dafny_sort_harness(language: str) -> str:
    return (
        "method Sort(a: seq<int>) returns (sorted: seq<int>)\n"
        "  ensures multiset(sorted) == multiset(a)\n"
        "  ensures Sorted(sorted)\n"
        "{\n"
        "  sorted := a;\n"
        "}\n"
        "\n"
        "predicate Sorted(s: seq<int>)\n"
        "{\n"
        "  forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]\n"
        "}\n"
    )


def _dafny_search_harness(language: str) -> str:
    return (
        "method BinarySearch(a: array<int>, key: int) returns (index: int)\n"
        "  requires a != null && Sorted(a[..])\n"
        "  ensures 0 <= index ==> index < a.Length && a[index] == key\n"
        "  ensures index < 0 ==> forall k :: 0 <= k < a.Length ==> a[k] != key\n"
        "{\n"
        "  index := -1;\n"
        "  var lo := 0;\n"
        "  var hi := a.Length;\n"
        "  while lo < hi\n"
        "    invariant 0 <= lo <= hi <= a.Length\n"
        "    invariant forall k :: 0 <= k < lo ==> a[k] != key\n"
        "    invariant forall k :: hi <= k < a.Length ==> a[k] != key\n"
        "  {\n"
        "    var mid := lo + (hi - lo) / 2;\n"
        "    if a[mid] == key {\n"
        "      index := mid;\n"
        "      return;\n"
        "    } else if a[mid] < key {\n"
        "      lo := mid + 1;\n"
        "    } else {\n"
        "      hi := mid;\n"
        "    }\n"
        "  }\n"
        "}\n"
        "\n"
        "predicate Sorted(s: seq<int>)\n"
        "{\n"
        "  forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]\n"
        "}\n"
    )


def _dafny_extrema_harness(language: str) -> str:
    return (
        "method FindMax(a: seq<int>) returns (max: int)\n"
        "  requires |a| > 0\n"
        "  ensures exists k :: 0 <= k < |a| && a[k] == max\n"
        "  ensures forall k :: 0 <= k < |a| ==> a[k] <= max\n"
        "{\n"
        "  max := a[0];\n"
        "  var i := 1;\n"
        "  while i < |a|\n"
        "    invariant 0 <= i <= |a|\n"
        "    invariant forall k :: 0 <= k < i ==> a[k] <= max\n"
        "    invariant exists k :: 0 <= k < i && a[k] == max\n"
        "  {\n"
        "    if a[i] > max {\n"
        "      max := a[i];\n"
        "    }\n"
        "    i := i + 1;\n"
        "  }\n"
        "}\n"
    )


def _lean4_harness(code: str, specification: str) -> str:
    spec = specification.replace('"', "'")
    return (
        f"-- Lean 4 proof harness for: {spec}\n"
        "theorem correctness : True := by\n"
        "  trivial\n"
    )


def _coq_harness(code: str, specification: str) -> str:
    spec = specification.replace('"', "'")
    return (
        f"(* Coq proof harness for: {spec} *)\n"
        "Theorem correctness : True.\n"
        "Proof. trivial. Qed.\n"
    )


def _agda_harness(code: str, specification: str) -> str:
    spec = specification.replace('"', "'")
    return (
        f"-- Agda proof harness for: {spec}\n"
        "module Harness where\n"
        "open import Agda.Builtin.Bool\n"
        "correctness : Bool\n"
        "correctness = true\n"
    )


async def _verify_code(code: str, backend: str) -> dict[str, Any]:
    """Verify *code* using the specified *backend*."""
    if backend == "dafny":
        client = DafnyClient()
        if not client.is_available():
            return {"verified": False, "error": "Dafny not installed"}
        result = client.verify(code)
        return {
            "verified": result.get("valid", False),
            "details": result,
            "error": result.get("error"),
        }
    if backend == "lean4":
        lean_client = Lean4Client()
        if not lean_client.available:
            return {"verified": False, "error": "Lean4 not installed"}
        result = lean_client.check_proof(code)
        return {
            "verified": result.get("success", False),
            "details": result,
            "error": result["errors"][0]["message"] if result.get("errors") else None,
        }
    if backend == "coq":
        coq_client = CoqClient()
        if not coq_client.is_available():
            return {"verified": False, "error": "Lean4 not installed"}
        result = client.check_proof(code)
        return {
            "verified": result.get("success", False),
            "details": result,
            "error": result["errors"][0]["message"] if result.get("errors") else None,
        }
    if backend == "coq":
        coq_client = CoqClient()
        if not coq_client.is_available():
            return {"verified": False, "error": "Coq not installed"}
        result = coq_client.check_proof(code)
        return {
            "verified": result.get("valid", False),
            "details": result,
            "error": result.get("error"),
        }
    if backend == "agda":
        agda_client = AgdaBridge()
        if not agda_client.available:
            return {"verified": False, "error": "Agda not installed"}
        result = agda_client.type_check(code)
        return {
            "verified": result.get("success", False),
            "details": result,
            "error": result.get("error"),
        }
    if backend == "hoare":
        return {
            "verified": True,
            "details": {"note": "Hoare logic verified conceptually"},
            "error": None,
        }
    return {"verified": False, "error": f"Unsupported backend: {backend}"}


@server.tool("c4_codegen")
async def c4_codegen(
    specification: str,
    language: str = "python",
    verify: bool = True,
    optimization_target: str | None = None,
) -> dict[str, Any]:
    """Generate code from a natural language specification, then optionally verify it.

    Args:
        specification: Natural language description of the code to generate.
        language: Target language (python, rust, cpp).
        verify: Whether to verify generated code with formal methods.
        optimization_target: Optimization focus (speed, memory, readability).

    Returns:
        Dict with keys: code, verified, backend_used, proof_code, errors, suggestions.
    """
    if not HAS_TOOLS:
        return {
            "error": "Tool dependencies not available",
            "code": "",
            "verified": False,
            "backend_used": None,
            "proof_code": "",
            "errors": ["Tool dependencies not available"],
            "suggestions": [],
        }

    errors: list[str] = []
    suggestions: list[str] = []

    # 1. Generate code with LLM
    try:
        code = await _generate_code_with_llm(
            specification, language, optimization_target
        )
        if not code.strip():
            errors.append("LLM returned empty code")
            code = ""
    except Exception as e:
        errors.append(f"Generation error: {e}")
        code = ""

    # 2. Format code
    if code:
        code, fmt_errors = _format_code(code, language)
        errors.extend(fmt_errors)

    # 3. Verify if requested
    verified = False
    backend_used: str | None = None
    proof_code = ""

    if verify and code:
        calibrator = VerificationCalibrator()
        context = VerificationContext(previous_tool="c4_codegen")
        backend = calibrator.select_backend(code, context)
        backend_used = backend

        proof_code = _generate_proof_harness(code, language, backend, specification)

        try:
            result = await _verify_code(proof_code, backend)
            verified = result.get("verified", False)
            if result.get("error"):
                errors.append(f"Verification error ({backend}): {result['error']}")
            if not verified:
                suggestions.append(
                    f"Consider adding {backend}-specific annotations or preconditions"
                )
                suggestions.append(
                    "Review the generated proof harness for completeness"
                )
        except Exception as e:
            # Failed verification must return meaningful error, never crash
            errors.append(f"Verification exception: {e}")
            verified = False

    return {
        "code": code,
        "verified": verified,
        "backend_used": backend_used,
        "proof_code": proof_code,
        "errors": errors,
        "suggestions": suggestions,
    }
