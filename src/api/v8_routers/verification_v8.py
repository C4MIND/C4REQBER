"""v8 verification router — formal, statistical, and SMT verification."""
from __future__ import annotations

import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.errors import C4APIError, ValidationError


logger = logging.getLogger(__name__)
from src.verification.unified_score import (
    BackendResult,
    compute_unified_score,
)


router = APIRouter(prefix="/verification", tags=["v8-verification"])

_VERIFY_CACHE_TTL = 3600
_VERIFY_CACHE_MAX = 500
_verify_cache: dict[str, dict[str, Any]] = {}


def _prune_verify_cache() -> None:
    """Drop expired entries and enforce max size (LRU by updated_at)."""
    now = time.time()
    expired = [
        key
        for key, entry in _verify_cache.items()
        if now - entry.get("updated_at", 0) > _VERIFY_CACHE_TTL
    ]
    for key in expired:
        _verify_cache.pop(key, None)
    while len(_verify_cache) >= _VERIFY_CACHE_MAX:
        oldest = min(_verify_cache, key=lambda k: _verify_cache[k].get("updated_at", 0))
        _verify_cache.pop(oldest, None)


def _set_verify_cache(verify_id: str, data: dict[str, Any]) -> None:
    _prune_verify_cache()
    data["updated_at"] = time.time()
    _verify_cache[verify_id] = data


def _get_verify_cache(verify_id: str) -> dict[str, Any] | None:
    data = _verify_cache.get(verify_id)
    if not data:
        return None
    if time.time() - data.get("updated_at", 0) > _VERIFY_CACHE_TTL:
        _verify_cache.pop(verify_id, None)
        return None
    return data


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class HypothesisVerifyRequest(BaseModel):
    """Verify a scientific hypothesis using multiple backends."""

    hypothesis: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        json_schema_extra={"example": "Increasing temperature increases reaction rate"},
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={"example": {"test_type": "correlation", "x": [1, 2, 3], "y": [2, 4, 6]}},
    )
    methods: list[str] = Field(
        default_factory=list,
        json_schema_extra={"example": ["statistical", "smt"]},
    )
    timeout_per_method: float = Field(default=60.0, ge=1.0, le=300.0)


# ---------------------------------------------------------------------------
# Unified hypothesis verification endpoint
# ---------------------------------------------------------------------------

@router.post("/hypothesis")
async def verify_hypothesis(req: HypothesisVerifyRequest) -> dict[str, Any]:
    """Verify a hypothesis using available backends and return unified score (0–100).

    Example context for statistical test:
    ```json
    {"test_type": "ttest", "group_a": [1,2,3], "group_b": [4,5,6], "alpha": 0.05}
    ```
    """
    if not req.hypothesis.strip():
        raise ValidationError("Hypothesis cannot be empty")

    verify_id = f"verify_{uuid4().hex[:12]}"
    backend_results: list[BackendResult] = []

    # 1. Statistical validation (if applicable)
    if req.context.get("test_type") in ("ttest", "chi2", "ks", "correlation"):
        from src.verification.stats_validator import StatisticalValidator
        validator = StatisticalValidator()
        try:
            stat_result = await validator.verify(
                req.hypothesis,
                context=req.context,
                timeout=req.timeout_per_method,
            )
            backend_results.append(BackendResult(
                backend="statistical",
                status=stat_result.get("status", "unknown"),
                confidence=stat_result.get("confidence", 0.0),
                proof_text=stat_result.get("proof_output", ""),
                error_message=stat_result.get("error_message", ""),
                execution_time_ms=stat_result.get("execution_time_ms", 0.0),
                metadata=stat_result.get("metadata", {}),
            ))
        except Exception as exc:
            logger.warning("statistical verifier failed: %s", exc)
            backend_results.append(BackendResult(
                backend="statistical",
                status="failed",
                confidence=0.0,
                error_message=str(exc),
            ))

    # 2. Formal verification via hybrid verifier
    try:
        from src.verification.hybrid_verifier import HybridVerifier
        from src.verification.math_detector import detect_math_structure

        hv = HybridVerifier()
        assessment = detect_math_structure(req.hypothesis)

        # Only run formal if hypothesis is Category A or B
        if assessment.get("category") in ("A", "B"):
            hypothesis_dict = {
                "title": req.hypothesis[:200],
                "description": req.hypothesis,
            }
            ctx = dict(req.context or {})
            if "preferred_backends" not in ctx:
                from src.pipeline.output_profiles import detect_format, get_profile
                mode = str(ctx.get("mode", "solve"))
                output_fmt = detect_format(req.hypothesis, mode=mode)
                profile = get_profile(output_fmt)
                ctx["preferred_backends"] = list(profile.verification_backends)
            hv_result = await hv.verify(hypothesis_dict, context=ctx)
            backend_results.append(BackendResult(
                backend=hv_result.backend,
                status=hv_result.status,
                confidence=0.9 if hv_result.status == "verified" else 0.3,
                proof_code=hv_result.proof_code,
                proof_text=hv_result.proof_text,
                error_message=hv_result.error_message,
                execution_time_ms=hv_result.execution_time_ms,
                metadata={"iterations": hv_result.iterations, "was_timeout": hv_result.was_timeout},
            ))
        else:
            backend_results.append(BackendResult(
                backend="math_detector",
                status="uncertain",
                confidence=0.0,
                proof_text=assessment.get("category_label", ""),
            ))
    except Exception as exc:
        logger.warning("hybrid verifier failed: %s", exc)
        backend_results.append(BackendResult(
            backend="hybrid_verifier",
            status="failed",
            confidence=0.0,
            error_message=str(exc),
        ))

    # 3. Compute unified score
    unified = compute_unified_score(req.hypothesis, backend_results)

    # Audit 2026-06-22: increment VERIFICATION_RUNS per backend result so
    # /metrics reflects per-backend run volume (the 5th Prometheus counter
    # left at zero after the v9.14.0 master audit C-2 fix). Best-effort —
    # observability must never crash callers.
    try:
        from src.api.routers.metrics import VERIFICATION_RUNS

        for r in backend_results:
            # Normalize: hybrid_verifier's per-backend label (e.g. "lean4",
            # "z3") flows through; "statistical"/"math_detector" map to
            # themselves. Status is whatever BackendResult reports.
            backend_label = r.backend or "unknown"
            status_label = r.status or "unknown"
            VERIFICATION_RUNS.labels(backend=backend_label, status=status_label).inc()
    except Exception:
        pass

    payload = {
        "verify_id": verify_id,
        "status": "completed",
        "overall_status": unified.overall_status,
        "overall_score": unified.overall_score,
        "overall_confidence": unified.overall_confidence,
        "backend_results": [r.to_dict() for r in backend_results],
        "recommendations": unified.recommendations,
    }
    _set_verify_cache(verify_id, payload)
    return payload


@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available verification backends and their status."""
    from src.verification.hybrid_verifier import HybridVerifier
    from src.verification.stats_validator import StatisticalValidator

    hv = HybridVerifier()
    stats = StatisticalValidator()

    from src.verification.alloy_client import AlloyClient
    from src.verification.cvc5_client import CVC5Client
    from src.verification.tla_client import TLAClient

    backends = {
        "statistical": stats.available,
        "lean4": hv._check_executable(hv.LEAN4_PATH),
        "coq": hv._check_executable(hv.COQ_PATH),
        "dafny": hv._check_executable(hv.DAFNY_PATH),
        "agda": hv._check_executable(hv.AGDA_PATH),
        "z3": True,
        "cvc5": CVC5Client().test_connection(),
        "tla": TLAClient().test_connection(),
        "alloy": AlloyClient().test_connection(),
        "hoare": True,
    }
    return {
        "available": [k for k, v in backends.items() if v],
        "all": list(backends.keys()),
        "status": backends,
    }


# ---------------------------------------------------------------------------
# LEGACY: Original verification endpoints (backward compatibility)
# ---------------------------------------------------------------------------

class VerifyRequest(BaseModel):
    """VerifyRequest."""
    code: str
    specification: dict[str, str] | None = None
    formal_method: str = "hoare"
    proof: str = "sorry"


class AutoProofRequest(BaseModel):
    """AutoProofRequest."""
    discovery: dict[str, Any]
    evidence: list[str] = []


class LeanVerifyRequest(BaseModel):
    """LeanVerifyRequest."""
    theorem: str
    proof: str = "sorry"


@router.post("/verify")
async def verify_code(req: VerifyRequest) -> dict[str, Any]:
    """Verify code using specified formal method (legacy endpoint)."""
    verify_id = f"verify_{uuid4().hex[:12]}"
    _set_verify_cache(verify_id, {"status": "pending", "verified": False, "method": req.formal_method})

    try:
        if req.formal_method == "lean4":
            from src.verification.lean4_client import Lean4Client
            client = Lean4Client()
            if not client.available:
                raise C4APIError("Lean 4 not installed", status_code=501, error_code="lean4_not_installed")
            result = client.verify_theorem(req.code, req.proof)
            err = result.get("error", "")
            payload = {
                "verified": result.get("valid", False),
                "errors": [err] if err else [],
                "method": "lean4",
            }
        elif req.formal_method == "coq":
            from src.verification.coq_client import CoqClient
            client = CoqClient()
            if not client.is_available():
                raise C4APIError("Coq not installed", status_code=501, error_code="coq_not_installed")
            result = client.check_proof(req.code)
            err = str(result.get("error", result.get("output", "")))
            payload = {
                "verified": result.get("valid", False),
                "errors": [err] if not result.get("valid") else [],
                "method": "coq",
            }
        elif req.formal_method == "agda":
            from src.verification.agda_bridge import AgdaBridge
            client = AgdaBridge()
            if not client.available:
                raise C4APIError("Agda not installed", status_code=501, error_code="agda_not_installed")
            result = client.type_check(req.code)
            err = str(result.get("error", ""))
            payload = {
                "verified": result.get("success", False),
                "errors": [err] if not result.get("success") else [],
                "method": "agda",
            }
        elif req.formal_method == "z3":
            try:
                import z3
                solver = z3.Solver()
                solver.set("timeout", 5000)
                solver.from_string(req.code)
                check = solver.check()
                valid = check == z3.sat
                payload = {
                    "verified": valid,
                    "errors": [] if valid else [str(check)],
                    "method": "z3",
                }
            except Exception as exc:
                payload = {"verified": False, "errors": [str(exc)], "method": "z3"}
        elif req.formal_method == "hoare":
            from src.verification.hoare_verifier import HoareVerifier
            hv = HoareVerifier()
            hoare_result = hv.verify(req.code)
            payload = {"verified": hoare_result.valid, "errors": [hoare_result.error] if hoare_result.error else []}
        elif req.formal_method == "dafny":
            from src.verification.dafny_client import DafnyClient
            dc = DafnyClient()
            if not dc.is_available():
                raise C4APIError("Dafny not installed", status_code=501, error_code="dafny_not_installed")
            result = dc.verify(req.code)
            payload = {"verified": result.get("valid", False), "errors": [str(result.get("output", ""))] if not result.get("valid") else []}
        elif req.formal_method == "cvc5":
            from src.verification.cvc5_client import CVC5Client
            client = CVC5Client()
            if not client.is_available():
                raise C4APIError("CVC5 not installed", status_code=501, error_code="cvc5_not_installed")
            result = client.verify(req.code)
            payload = {"verified": result.get("valid", False), "errors": [result.get("error", "")] if not result.get("valid") else [], "method": "cvc5"}
        elif req.formal_method in ("tla", "tla+"):
            from src.verification.tla_client import TLAClient
            client = TLAClient()
            if not client.is_available():
                raise C4APIError("TLA+ TLC not installed", status_code=501, error_code="tla_not_installed")
            result = client.verify(req.code)
            payload = {"verified": result.get("valid", False), "errors": [result.get("error", "")] if not result.get("valid") else [], "method": "tla"}
        elif req.formal_method == "alloy":
            from src.verification.alloy_client import AlloyClient
            client = AlloyClient()
            if not client.is_available():
                raise C4APIError("Alloy not installed", status_code=501, error_code="alloy_not_installed")
            result = client.verify(req.code)
            payload = {"verified": result.get("valid", False), "errors": [result.get("error", "")] if not result.get("valid") else [], "method": "alloy"}
        else:
            raise ValidationError(f"Unsupported formal method: {req.formal_method}")
    except C4APIError:
        raise
    except Exception as exc:
        logger.exception("Verification failed")
        raise C4APIError(f"Verification failed: {exc}", status_code=500, error_code="verification_failed") from exc

    _set_verify_cache(verify_id, {"status": "completed", **payload})
    return {"verify_id": verify_id, **payload}


@router.post("/lean4/verify")
async def verify_lean4(req: VerifyRequest) -> dict[str, Any]:
    """Verify theorem using Lean 4 (legacy endpoint)."""
    from src.verification.lean4_client import Lean4Client
    client = Lean4Client()
    if not client.available:
        raise C4APIError("Lean 4 not installed", status_code=501, error_code="lean4_not_installed")
    result = client.verify_theorem(req.code, req.proof)
    return result


@router.post("/lean")
async def verify_lean(req: LeanVerifyRequest) -> dict[str, Any]:
    """Verify Lean 4 theorem (legacy endpoint)."""
    from src.verification.lean4_client import Lean4Client
    client = Lean4Client()
    if not client.available:
        raise C4APIError("Lean 4 not installed", status_code=501, error_code="lean4_not_installed")
    result = client.verify_theorem(req.theorem, req.proof)
    err = result.get("error", "")
    return {"verified": result.get("valid", False), "errors": [err] if err else []}


@router.post("/auto-proof")
async def auto_generate_proof(req: AutoProofRequest) -> dict[str, Any]:
    """Auto-generate proof from discovery using LLM (legacy endpoint)."""
    from src.verification.llm_prover import LLMProver
    prover = LLMProver()
    hypothesis = req.discovery.get("hypothesis", {}).get("text", str(req.discovery)[:500])
    result = await prover.prove(hypothesis, "lean4")
    return result.to_dict()


@router.get("/tools")
async def list_tools() -> list[str]:
    """List available verification tools (legacy endpoint)."""
    return ["hoare", "lean4", "dafny", "coq", "agda", "z3", "cvc5", "tla", "alloy"]


@router.get("/status/{verify_id}")
async def get_verify_status(verify_id: str) -> dict[str, Any]:
    """Get verification status by ID."""
    cached = _get_verify_cache(verify_id)
    if not cached:
        raise C4APIError(f"Verification {verify_id} not found", status_code=404, error_code="verification_not_found")
    return cached


@router.get("/lean4lean/status")
async def check_lean4lean() -> dict[str, Any]:
    """Check lean4lean kernel checker availability."""
    from src.verification.lean4lean_client import Lean4LeanClient
    client = Lean4LeanClient()
    return {"available": client.available, "license": "BSD-style"}
