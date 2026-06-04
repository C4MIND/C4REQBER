from __future__ import annotations


"""Hybrid Verifier — 6-backend formal verification with smart model routing.

Backends: Z3 (numerical) + Lean4 + Coq + Dafny + Agda + Hoare
Model: MultiProviderReasonerClient (deepseek-reasoner → OR/gemini → OR/llama → local)
Strategy: Auto-select backend → generate proof → compile → error-driven retry → Z3 fallback
"""

import asyncio
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any

from src.llm.reasoner_client import MultiProviderReasonerClient
from src.verification.auto_theorem import AutoTheoremFormulator
from src.verification.timer import BACKEND_TIMEOUTS


logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """VerificationResult."""
    backend: str
    status: str  # verified | partial | failed | z3_fallback | timeout
    claim: str
    proof_code: str = ""
    proof_text: str = ""  # Human-readable summary
    error_message: str = ""  # Last compiler error
    iterations: int = 0
    execution_time_ms: float = 0.0
    timing_info: dict[str, Any] | None = None  # From VerificationTimer
    was_timeout: bool = False
    fallback_reason: str = ""


class HybridVerifier:
    """Smart verification with auto-backend selection and error-driven retry."""

    # Configurable executable paths (override for non-standard installs)
    LEAN4_PATH = "lean"
    COQ_PATH = "coqc"
    DAFNY_PATH = "dafny"
    AGDA_PATH = "agda"

    # Backend selection keywords
    BACKEND_RULES = {
        "z3": {
            "patterns": [r"\d+(?:\.\d+)?\s*(?:%|mpa|mm|days|cells|k|ev|j|w|nm|μm|kg|hz)", r"[\d.]+%", r"Q\s*[≥>=]", r"probability\s*[≥>=]"],
            "keywords": ["%", "mpa", "mm", "days", "cells", "concentration", "temperature", "pressure"],
        },
        "dafny": {
            "patterns": [r"O\(n\^?\d*\)", r"algorithm", r"sort", r"complexity", r"method\s+\w+"],
            "keywords": ["algorithm", "sort", "search", "complexity", "method", "loop", "invariant"],
        },
        "coq": {
            "patterns": [r"protocol", r"deadlock", r"race", r"concurrent", r"message passing"],
            "keywords": ["protocol", "deadlock", "race condition", "concurrent", "distributed", "consensus"],
        },
        "agda": {
            "patterns": [r"type\s+\w+", r"total\s+function", r"dependent", r"constructive"],
            "keywords": ["type theory", "total function", "dependent type", "constructive", "intuitionistic"],
        },
        "hoare": {
            "patterns": [r"precondition", r"postcondition", r"invariant", r"while\s+\("],
            "keywords": ["precondition", "postcondition", "invariant", "hoare", "imperative"],
        },
        "lean4": {
            "patterns": [r"theorem\b", r"lemma\b", r"forall", r"exists", r"proof\b"],
            "keywords": ["theorem", "lemma", "proof", "mathematics", "number theory", "algebra"],
        },
    }

    def __init__(self) -> None:
        self.z3 = AutoTheoremFormulator()
        self.reasoner = MultiProviderReasonerClient()
        self._cache: dict[str, VerificationResult] = {}  # hypothesis_hash -> result

    @staticmethod
    def _check_executable(path: str) -> bool:
        import shutil
        return shutil.which(path) is not None

    async def verify(self, hypothesis: dict[str, Any], context: dict[str, Any] | None = None) -> VerificationResult:
        """Main entry: auto-select backend, generate proof, retry on error WITH timeout management."""
        import time

        from src.verification.timer import VerificationTimeoutManager, VerificationTimer

        t0 = time.perf_counter()

        claim = f"{hypothesis.get('title', '')}. {hypothesis.get('description', '')}"
        domain = self._detect_domain(claim)

        # Check cache
        cache_key = self._hash_claim(claim)
        if cache_key in self._cache:
            logger.info("Cache hit for claim")
            return self._cache[cache_key]

        # Step 0: Statistical validation fast path
        ctx = context or {}
        if ctx.get("test_type") in ("ttest", "chi2", "ks", "correlation"):
            from src.verification.stats_validator import StatisticalValidator
            validator = StatisticalValidator()
            stat_result = await validator.verify(claim, context=ctx)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            vr = VerificationResult(
                backend="statistical",
                status=stat_result.get("status", "unknown"),
                claim=claim[:200],
                proof_code="",
                proof_text=stat_result.get("proof_output", ""),
                iterations=1,
                execution_time_ms=elapsed_ms,
                timing_info={"backend": "statistical", "elapsed_ms": int(elapsed_ms)},
            )
            self._cache[cache_key] = vr
            return vr

        # Step 1: Auto-select backend
        backend = self._select_backend(claim)
        logger.info("Selected backend: %s for claim: %s...", backend, claim[:60])

        # Emit verification start event
        try:
            from src.pipeline.events import event_bus
            await event_bus.emit("verification_start", {
                "backend": backend,
                "claim": claim[:100],
                "estimated_timeout": BACKEND_TIMEOUTS.get(backend, (30, 120))[1],
            }, mode="turbo")
        except (ImportError, RuntimeError, ValueError):
            pass

        # Step 2: Fast path — Z3 for numerical claims (no LLM, instant)
        if backend == "z3":
            result = self.z3.formulate(hypothesis, backend="z3")
            elapsed_ms = (time.perf_counter() - t0) * 1000
            vr = VerificationResult(
                backend="z3",
                status=result.get("status", "unknown"),
                claim=claim[:200],
                proof_code=result.get("theorem_statement", ""),
                proof_text=result.get("proof_strategy", ""),
                iterations=1,
                execution_time_ms=elapsed_ms,
                timing_info={"backend": "z3", "elapsed_ms": int(elapsed_ms), "was_killed": False},
            )
            self._cache[cache_key] = vr
            return vr

        # Step 3: Generate formal proof with reasoner model (with timeout)
        timer = VerificationTimer(backend)

        # Progress callback → EventBus
        def on_progress(progress: Any) -> None:
            try:
                from src.pipeline.events import event_bus
                asyncio.create_task(event_bus.emit("verification_progress", {
                    "backend": progress.backend,
                    "status": progress.status,
                    "elapsed_seconds": round(progress.elapsed_seconds, 1),
                    "percent_complete": round(progress.percent_complete, 1),
                    "message": progress.message,
                }, mode="turbo"))
            except (ImportError, RuntimeError):
                pass

        timer.add_progress_callback(on_progress)

        # Generate proof with hard timeout
        async def _generate() -> str:
            return await self.reasoner.generate_proof(claim, backend, domain)

        proof_code, timing = await timer.run_with_timeout(_generate())

        if proof_code is None or proof_code.startswith("[Error"):
            # Timeout or reasoner failed — fallback to Z3
            reason = timing.fallback_reason if proof_code is None else "Reasoner failed"
            logger.warning("Proof generation failed/timed out (%s), falling back to Z3", reason)
            vr = self._z3_fallback(hypothesis, claim, reason, t0)
            vr.was_timeout = timing.was_killed
            vr.timing_info = timing.to_dict()
            vr.fallback_reason = reason
            return vr

        # Step 4: Compile with error-driven retry (max 3) — each with timer
        for attempt in range(1, 4):
            compile_timer = VerificationTimer(backend)

            async def _compile_once(_code: str = proof_code) -> dict[str, Any]:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, self._compile, _code, backend)

            compile_result, compile_timing = await compile_timer.run_with_timeout(_compile_once())

            if compile_result is None:
                # Compile timed out — fallback
                reason = f"Compilation timed out after {VerificationTimeoutManager.format_elapsed(compile_timing.elapsed_ms / 1000)}"
                logger.warning("Compile timeout on attempt %d", attempt)
                vr = self._z3_fallback(hypothesis, claim, reason, t0)
                vr.was_timeout = True
                vr.timing_info = compile_timing.to_dict()
                vr.fallback_reason = reason
                return vr

            if compile_result["status"] == "success":
                total_ms = (time.perf_counter() - t0) * 1000
                vr = VerificationResult(
                    backend=backend,
                    status="verified",
                    claim=claim[:200],
                    proof_code=proof_code,
                    proof_text=f"Proof verified by {backend} compiler in {VerificationTimeoutManager.format_elapsed(total_ms/1000)}.",
                    iterations=attempt,
                    execution_time_ms=total_ms,
                    timing_info={"backend": backend, "elapsed_ms": int(total_ms), "attempts": attempt, "was_killed": False},
                )
                self._cache[cache_key] = vr
                return vr

            if compile_result["status"] == "incomplete":
                logger.warning("Incomplete proof (attempt %d), requesting fix...", attempt)
                fixed = await self.reasoner.fix_error(
                    proof_code, f"Proof contains placeholders: {compile_result['error']}", backend
                )
                if fixed and not fixed.startswith("[Error"):
                    proof_code = fixed
                    continue

            # Parse error and retry
            error_category = self._categorize_error(compile_result["error"], backend)
            logger.warning("Compile error (attempt %d): %s — %s", attempt, error_category, compile_result["error"][:100])

            fixed = await self.reasoner.fix_error(proof_code, compile_result["error"], backend)
            if fixed and not fixed.startswith("[Error"):
                proof_code = fixed
            else:
                break  # Reasoner can't fix — stop retrying

        # Step 5: All retries failed — fallback to Z3
        total_ms = (time.perf_counter() - t0) * 1000
        vr = self._z3_fallback(hypothesis, claim, f"{backend} failed after 3 attempts", t0)
        vr.execution_time_ms = total_ms
        return vr

    def _select_backend(self, claim: str) -> str:
        """Auto-select best backend based on claim content."""
        claim_lower = claim.lower()

        # Priority 1: Numerical bounds → Z3 (fastest, no LLM)
        z3_score = sum(1 for kw in self.BACKEND_RULES["z3"]["keywords"] if kw in claim_lower)
        z3_score += sum(1 for p in self.BACKEND_RULES["z3"]["patterns"] if re.search(p, claim_lower))
        if z3_score >= 1:
            return "z3"

        # Score other backends
        scores = {}
        for backend, rules in self.BACKEND_RULES.items():
            if backend == "z3":
                continue
            score = sum(1 for kw in rules["keywords"] if kw in claim_lower)
            score += sum(2 for p in rules["patterns"] if re.search(p, claim_lower))
            scores[backend] = score

        if scores:
            best = max(scores, key=lambda k: scores[k])
            if scores[best] >= 1:
                return best

        # Default: Lean4 for pure math
        return "lean4"

    def _detect_domain(self, claim: str) -> str:
        """Detect scientific domain for better prompt engineering."""
        domains = {
            "physics": ["quantum", "thermodynamic", "particle", "field", "relativity"],
            "biology": ["cell", "gene", "protein", "organism", "bacterial", "neural"],
            "chemistry": ["molecule", "reaction", "catalyst", "polymer", "synthesis"],
            "computer_science": ["algorithm", "complexity", "graph", "neural network", "optimization"],
            "mathematics": ["theorem", "proof", "topology", "algebra", "number theory"],
            "engineering": ["mechanical", "electrical", "civil", "aerospace", "material"],
        }
        claim_lower = claim.lower()
        scores = {d: sum(1 for kw in kws if kw in claim_lower) for d, kws in domains.items()}
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else "general"

    def _compile(self, code: str, backend: str) -> dict[str, Any]:
        """Compile proof code and return status + error."""
        try:
            if backend == "lean4":
                return self._compile_lean4(code)
            elif backend == "coq":
                return self._compile_coq(code)
            elif backend == "dafny":
                return self._compile_dafny(code)
            elif backend == "agda":
                return self._compile_agda(code)
            elif backend == "hoare":
                return self._compile_hoare(code)
            else:
                return {"status": "unknown_backend", "error": f"Unknown backend: {backend}"}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            return {"status": "exception", "error": str(e)}

    def _compile_lean4(self, code: str) -> dict[str, Any]:
        """Compile Lean 4 code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False) as f:
            f.write(code)
            path = f.name

        try:
            # Check for sorry/admit first
            if "sorry" in code.lower() or "admit" in code.lower():
                return {"status": "incomplete", "error": "Contains sorry or admit"}

            result = subprocess.run(
                [self.LEAN4_PATH, path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return {"status": "success", "error": ""}
            return {"status": "error", "error": result.stderr[:500]}
        except FileNotFoundError:
            return {"status": "not_installed", "error": "lean not found"}
        finally:
            os.unlink(path)

    def _compile_coq(self, code: str) -> dict[str, Any]:
        """Compile Coq code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".v", delete=False) as f:
            f.write(code)
            path = f.name

        try:
            if "Admitted" in code or "admit" in code.lower():
                return {"status": "incomplete", "error": "Contains Admitted"}

            result = subprocess.run(
                [self.COQ_PATH, path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return {"status": "success", "error": ""}
            return {"status": "error", "error": result.stderr[:500]}
        except FileNotFoundError:
            return {"status": "not_installed", "error": "coqc not found"}
        finally:
            os.unlink(path)

    def _compile_dafny(self, code: str) -> dict[str, Any]:
        """Verify Dafny code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dfy", delete=False) as f:
            f.write(code)
            path = f.name

        try:
            result = subprocess.run(
                [self.DAFNY_PATH, "verify", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return {"status": "success", "error": ""}
            return {"status": "error", "error": result.stdout[:500]}
        except FileNotFoundError:
            return {"status": "not_installed", "error": "dafny not found"}
        finally:
            os.unlink(path)

    def _compile_agda(self, code: str) -> dict[str, Any]:
        """Compile Agda code."""
        # Extract module name from first line: "module Name where"
        import re
        match = re.match(r'module\s+([\w.]+)', code.strip())
        module_name = match.group(1) if match else "Main"

        # Agda requires filename path to match module name dots
        temp_dir = tempfile.mkdtemp()
        parts = module_name.split(".")
        if len(parts) > 1:
            subdir = os.path.join(temp_dir, *parts[:-1])
            os.makedirs(subdir, exist_ok=True)
            path = os.path.join(subdir, f"{parts[-1]}.agda")
        else:
            path = os.path.join(temp_dir, f"{module_name}.agda")
        with open(path, "w") as f:
            f.write(code)

        try:
            if "{!" in code or "?" in code:
                return {"status": "incomplete", "error": "Contains holes"}

            result = subprocess.run(
                [self.AGDA_PATH, path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_dir,
            )
            if result.returncode == 0:
                return {"status": "success", "error": ""}
            err = result.stderr[:500] or result.stdout[:500] or f"returncode={result.returncode}"
            return {"status": "error", "error": err}
        except FileNotFoundError:
            return {"status": "not_installed", "error": "agda not found"}
        finally:
            os.unlink(path)
            os.rmdir(temp_dir)

    def _compile_hoare(self, code: str) -> dict[str, Any]:
        """Verify Hoare triple via Z3-based weakest-precondition calculus."""
        from src.verification.hoare_verifier import HoareVerifier
        hv = HoareVerifier()
        result = hv.verify(code)
        return {
            "status": "verified" if result.valid else "failed",
            "success": result.valid,
            "valid": result.valid,
            "details": result.counterexample if result.counterexample else str(result.wp)[:200],
        }

    def _categorize_error(self, error: str, backend: str) -> str:
        """Categorize compiler error for targeted fixing."""
        error_lower = error.lower()

        categories = {
            "syntax_error": ["syntax error", "unexpected", "expected", "parse error"],
            "type_mismatch": ["type mismatch", "has type", "expected type"],
            "unknown_identifier": ["unknown identifier", "unknown constant", "not found"],
            "missing_import": ["unknown namespace", "could not resolve", "no such file"],
            "incomplete_proof": ["sorry", "admit", "unsolved goals", "proof incomplete"],
            "timeout": ["timeout", "maximum recursion", "stack overflow"],
        }

        for cat, patterns in categories.items():
            if any(p in error_lower for p in patterns):
                return cat

        return "unknown_error"

    def _z3_fallback(self, hypothesis: dict, claim: str, reason: str, t0: float) -> VerificationResult:
        """Fall back to Z3 for numerical constraint checking."""
        import time
        result = self.z3.formulate(hypothesis, backend="z3")
        return VerificationResult(
            backend="z3",
            status=result.get("status", "unknown"),
            claim=claim[:200],
            proof_code=result.get("theorem_statement", ""),
            proof_text=f"Z3 fallback: {reason}. {result.get('proof_strategy', '')}",
            iterations=3,
            execution_time_ms=(time.perf_counter() - t0) * 1000,
        )

    def _hash_claim(self, claim: str) -> str:
        """Hash claim for caching."""
        import hashlib
        return hashlib.sha256(claim.encode()).hexdigest()[:16]
