"""Prometheus /metrics endpoint for monitoring."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from prometheus_client import REGISTRY, Counter, Histogram, generate_latest

from src.api.dependencies import get_current_user


router = APIRouter(tags=["monitoring"])

# ── Pipeline metrics ──────────────────────────────────────────────────────────

PIPELINE_RUNS = Counter(
    "c4_pipeline_runs_total",
    "Total pipeline runs",
    labelnames=["pipeline_type", "status"],
)

PIPELINE_DURATION = Histogram(
    "c4_pipeline_duration_seconds",
    "Pipeline execution duration",
    labelnames=["pipeline_type"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

# ── LLM metrics ───────────────────────────────────────────────────────────────

LLM_CALLS = Counter(
    "c4_llm_calls_total",
    "Total LLM API calls",
    labelnames=["provider", "model", "status"],
)

LLM_TOKENS_INPUT = Counter(
    "c4_llm_tokens_input_total",
    "Input tokens consumed",
    labelnames=["provider", "model"],
)

LLM_TOKENS_OUTPUT = Counter(
    "c4_llm_tokens_output_total",
    "Output tokens generated",
    labelnames=["provider", "model"],
)

LLM_COST = Counter(
    "c4_llm_cost_dollars_total",
    "Total LLM cost in USD",
    labelnames=["provider"],
)

LLM_LATENCY = Histogram(
    "c4_llm_request_duration_seconds",
    "LLM request latency",
    labelnames=["provider", "model"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
)

# ── API metrics ───────────────────────────────────────────────────────────────

API_REQUESTS = Counter(
    "c4_api_requests_total",
    "Total API requests",
    labelnames=["method", "endpoint", "status_code"],
)

API_DURATION = Histogram(
    "c4_api_request_duration_seconds",
    "API request duration",
    labelnames=["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5),
)

# ── Cache metrics ─────────────────────────────────────────────────────────────

CACHE_HITS = Counter(
    "c4_cache_hits_total",
    "Total cache hits",
    labelnames=["cache_type"],
)

CACHE_MISSES = Counter(
    "c4_cache_misses_total",
    "Total cache misses",
    labelnames=["cache_type"],
)

# ── Verification metrics ──────────────────────────────────────────────────────

VERIFICATION_RUNS = Counter(
    "c4_verification_runs_total",
    "Total verification runs",
    labelnames=["backend", "status"],
)

# ── Discovery output metrics ──────────────────────────────────────────────────

DISCOVERIES_GENERATED = Counter(
    "c4_discoveries_total",
    "Total discoveries generated",
    labelnames=["output_format"],
)


@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint(_: object = Depends(get_current_user)) -> bytes:
    """Prometheus /metrics endpoint — exposes all registered metrics."""
    return generate_latest(REGISTRY)
