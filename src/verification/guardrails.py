# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
import re
import resource
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)

# ── Complexity thresholds per backend ──

@dataclass
class BackendGuard:
    """BackendGuard."""
    name: str
    max_lines: int = 500       # Reject proofs >N lines
    max_depth: int = 20        # Max nesting depth
    max_quantifiers: int = 50  # Max ∀/∃ quantifiers
    max_variables: int = 200   # Max distinct variables
    max_memory_mb: int = 512   # Hard memory cap (SIGXCPU if exceeded)
    stall_timeout: float = 10.0  # If no stdout for N seconds → kill
    known_hang_patterns: list[str] = field(default_factory=list)

BACKEND_GUARDS: dict[str, BackendGuard] = {
    "lean4": BackendGuard(
        name="lean4",
        max_lines=500, max_depth=15, max_quantifiers=30, max_variables=150,
        max_memory_mb=512, stall_timeout=15.0,
        known_hang_patterns=["simp", "omega", "dec_trivial", "native_decide"],
    ),
    "coq": BackendGuard(
        name="coq",
        max_lines=400, max_depth=15, max_quantifiers=40, max_variables=200,
        max_memory_mb=512, stall_timeout=20.0,
        known_hang_patterns=["auto", "ring", "omega", "firstorder", "intuition"],
    ),
    "dafny": BackendGuard(
        name="dafny",
        max_lines=300, max_depth=12, max_quantifiers=20, max_variables=100,
        max_memory_mb=512, stall_timeout=30.0,
        known_hang_patterns=["assert", "assume", "forall", "exists"],
    ),
    "agda": BackendGuard(
        name="agda",
        max_lines=200, max_depth=10, max_quantifiers=10, max_variables=80,
        max_memory_mb=1024, stall_timeout=60.0,  # Agda is VERY slow
        known_hang_patterns=["termination", "mutual", "induction"],
    ),
    "z3": BackendGuard(
        name="z3",
        max_lines=1000, max_depth=30, max_quantifiers=100, max_variables=500,
        max_memory_mb=256, stall_timeout=5.0,
        known_hang_patterns=[],
    ),
    "cvc5": BackendGuard(
        name="cvc5",
        max_lines=1000, max_depth=30, max_quantifiers=100, max_variables=500,
        max_memory_mb=256, stall_timeout=5.0,
        known_hang_patterns=[],
    ),
    "hoare": BackendGuard(
        name="hoare",
        max_lines=200, max_depth=8, max_quantifiers=5, max_variables=50,
        max_memory_mb=128, stall_timeout=5.0,
        known_hang_patterns=[],
    ),
    "haskell-typecheck": BackendGuard(
        name="haskell-typecheck",
        max_lines=1000, max_depth=30, max_quantifiers=0, max_variables=500,
        max_memory_mb=512, stall_timeout=10.0,
        known_hang_patterns=["type family", "injective", "ambiguous"],
    ),
    "haskell-quickcheck": BackendGuard(
        name="haskell-quickcheck",
        max_lines=500, max_depth=20, max_quantifiers=0, max_variables=200,
        max_memory_mb=256, stall_timeout=15.0,
        known_hang_patterns=[],
    ),
    "alloy": BackendGuard(
        name="alloy",
        max_lines=300, max_depth=10, max_quantifiers=20, max_variables=100,
        max_memory_mb=512, stall_timeout=30.0,
        known_hang_patterns=["reachable", "transitive", "closure"],
    ),
    "tla": BackendGuard(
        name="tla",
        max_lines=500, max_depth=15, max_quantifiers=30, max_variables=150,
        max_memory_mb=512, stall_timeout=45.0,
        known_hang_patterns=["liveness", "fairness", "[]<>", "<>[]"],
    ),
}


def set_memory_limit(mb: int) -> None:
    """Set per-process memory limit (macOS compatible)."""
    limit = mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    except (OSError, ValueError) as e:
        logger.debug("Memory limit not set: %s", e)


def estimate_complexity(code: str, backend: str) -> float:
    """Estimate problem complexity (0.0-1.0) based on code structure."""
    guard = BACKEND_GUARDS.get(backend)
    if not guard:
        return 0.5

    lines = len(code.splitlines())
    nesting = max((line.count("  ") // 2 for line in code.splitlines()), default=0)
    quantifiers = len(re.findall(r"∀|∃|forall|exists", code))
    variables = len(set(re.findall(r"[a-zA-Z_]\w*", code)))
    hang_risk = sum(1 for pat in guard.known_hang_patterns if pat in code.lower())

    scores = {
        "lines": min(1.0, lines / guard.max_lines),
        "nesting": min(1.0, nesting / guard.max_depth),
        "quantifiers": min(1.0, quantifiers / guard.max_quantifiers),
        "variables": min(1.0, variables / guard.max_variables),
        "hang_risk": min(1.0, hang_risk / max(len(guard.known_hang_patterns), 1)),
    }

    return round(sum(scores.values()) / len(scores), 2)


def preflight_check(code: str, backend: str) -> dict[str, Any]:
    """Pre-flight: estimate complexity, decide whether to attempt verification."""
    complexity = estimate_complexity(code, backend)
    guard = BACKEND_GUARDS.get(backend)

    risks = []

    if complexity > 0.8:
        risks.append(f"HIGH complexity ({complexity:.2f}) — likely to timeout/hang")
    if complexity > 0.6 and backend == "agda":
        risks.append("Agda is SLOW on medium+ complexity — consider Coq or Lean4")
    if complexity > 0.5 and backend == "dafny":
        risks.append("Dafny's Z3 backend may timeout on quantifier-heavy proofs")

    for pat in (guard.known_hang_patterns if guard else []):
        if pat in code.lower():
            risks.append(f"Contains '{pat}' — known hang pattern in {backend}")

    skip = complexity > 0.9
    use_z3_fallback = complexity > 0.7 and backend not in ("z3", "cvc5")

    return {
        "backend": backend,
        "complexity": complexity,
        "risks": risks,
        "skip": skip,
        "fallback_to_z3": use_z3_fallback,
        "recommendation": "skip" if skip else ("z3_fallback" if use_z3_fallback else "proceed"),
    }


def run_with_guardrails(cmd: list[str], backend: str, timeout_s: float = 60.0) -> dict[str, Any]:
    """Run verification subprocess with memory limit + hang detection."""
    guard = BACKEND_GUARDS.get(backend)
    memory_mb = guard.max_memory_mb if guard else 512
    stall_timeout = guard.stall_timeout if guard else 15.0

    t0 = time.perf_counter()
    last_output_time = t0

    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=lambda: set_memory_limit(memory_mb),
        )

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        stdout_failures = 0
        _STDOUT_FAILURE_LIMIT = 10

        while proc.poll() is None:
            elapsed = time.perf_counter() - t0
            if elapsed > timeout_s:
                proc.kill()
                proc.wait()
                return {
                    "status": "timeout",
                    "backend": backend,
                    "elapsed": round(elapsed, 1),
                    "error": f"Hard timeout ({timeout_s}s) exceeded",
                    "stdout": "".join(stdout_lines)[-500:],
                    "stderr": "".join(stderr_lines)[-500:],
                }

            # Hang detection: no output for stall_timeout
            if time.perf_counter() - last_output_time > stall_timeout:
                proc.kill()
                proc.wait()
                return {
                    "status": "stalled",
                    "backend": backend,
                    "elapsed": round(elapsed, 1),
                    "error": f"Process stalled — no output for {stall_timeout}s (backend: {backend})",
                    "stdout": "".join(stdout_lines)[-300:],
                    "stderr": "".join(stderr_lines)[-300:],
                }

            if proc.stdout is None:
                break
            try:
                line = proc.stdout.readline()
                if line:
                    stdout_lines.append(line)
                    last_output_time = time.perf_counter()
                    stdout_failures = 0
                else:
                    time.sleep(0.1)
            except Exception:
                stdout_failures += 1
                logger.warning(
                    "Verification stdout read failed for %s (%d consecutive failures)",
                    backend,
                    stdout_failures,
                )
                if stdout_failures >= _STDOUT_FAILURE_LIMIT:
                    logger.error(
                        "Verification stdout read failed %d times for %s — breaking loop",
                        stdout_failures,
                        backend,
                    )
                    break
                time.sleep(0.1)

            if proc.stderr is None:
                continue
            try:
                err_line = proc.stderr.readline()
                if err_line:
                    stderr_lines.append(err_line)
            except Exception as e:
                logger.debug("Verification stderr read failed: %s", e)
                pass

        stdout = "".join(stdout_lines)
        stderr = "".join(stderr_lines)

        return {
            "status": "passed" if proc.returncode == 0 else "failed",
            "backend": backend,
            "returncode": proc.returncode,
            "elapsed": round(time.perf_counter() - t0, 1),
            "stdout": stdout[-500:],
            "stderr": stderr[-500:],
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "backend": backend,
            "elapsed": round(time.perf_counter() - t0, 1),
            "error": "Subprocess timed out",
        }
    except Exception as e:
        return {
            "status": "crash",
            "backend": backend,
            "error": str(e),
            "elapsed": round(time.perf_counter() - t0, 1),
        }
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait()


def smart_select_backend(code: str, preferred: str = "lean4") -> str:
    """Auto-select the best verification backend based on code complexity."""
    assessment = preflight_check(code, preferred)
    if assessment["recommendation"] == "skip":
        logger.warning("Skipping %s (complexity %.2f > threshold)", preferred, assessment["complexity"])
    elif assessment["recommendation"] == "z3_fallback":
        logger.info("Falling back to Z3 for %s (complexity %.2f)", preferred, assessment["complexity"])
        return "z3"
    elif assessment["risks"]:
        for risk in assessment["risks"]:
            logger.warning("Risk for %s: %s", preferred, risk)
    return preferred if assessment["recommendation"] != "skip" else "skip"
