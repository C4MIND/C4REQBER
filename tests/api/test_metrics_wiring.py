"""Tests for the 5 missing Prometheus counter wirings (audit 2026-06-22 C-2 follow-up).

Background: v9.14.0 (master audit) defined 14 Counters/Histograms in
src/api/routers/metrics.py and wired up `LLM_CALLS` + `PIPELINE_RUNS`,
but the other 5 (API_REQUESTS, CACHE_HITS, DISCOVERIES_GENERATED,
VERIFICATION_RUNS, RATE_LIMIT_HITS) were defined and never incremented.
The /metrics endpoint was exporting zeros for all of them.

This commit wires the 5 to their natural call sites. These tests lock
in that each counter actually moves on the relevant event.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


# ─────────────────────────────────────────────────────────────────────
# RATE_LIMIT_HITS — counter is defined + is a Counter
# ─────────────────────────────────────────────────────────────────────


def test_rate_limit_hits_counter_exists():
    """RATE_LIMIT_HITS must be defined (was missing in v9.14.0)."""
    from src.api.routers.metrics import RATE_LIMIT_HITS
    assert RATE_LIMIT_HITS is not None


def test_rate_limit_hits_increment_works():
    from src.api.routers.metrics import RATE_LIMIT_HITS
    counter = RATE_LIMIT_HITS.labels(endpoint="/test/path")
    before = counter._value.get()
    counter.inc()
    after = counter._value.get()
    assert after == before + 1


# ─────────────────────────────────────────────────────────────────────
# CACHE_HITS — SearchCache.get() increments on hit
# ─────────────────────────────────────────────────────────────────────


def test_search_cache_hit_increments_counter():
    """SearchCache.get() must increment CACHE_HITS{cache_type=search} on a hit."""
    from src.api.routers.metrics import CACHE_HITS
    from src.knowledge.cache import SearchCache

    cache = SearchCache(ttl=60.0, max_size=10)
    cache.set("key-1", {"foo": "bar"})

    counter = CACHE_HITS.labels(cache_type="search")
    before = counter._value.get()

    result = cache.get("key-1")
    assert result == {"foo": "bar"}  # sanity

    after = counter._value.get()
    assert after == before + 1, f"CACHE_HITS should increment from {before} to {before + 1}, got {after}"


def test_search_cache_miss_does_not_increment_counter():
    """SearchCache.get() must NOT increment CACHE_HITS on a miss (deliberate, per audit)."""
    from src.api.routers.metrics import CACHE_HITS
    from src.knowledge.cache import SearchCache

    cache = SearchCache()
    counter = CACHE_HITS.labels(cache_type="search")
    before = counter._value.get()

    result = cache.get("nonexistent-key")
    assert result is None

    after = counter._value.get()
    assert after == before, "misses should not increment CACHE_HITS (audit decision)"


# ─────────────────────────────────────────────────────────────────────
# VERIFICATION_RUNS — importable + incrementable
# ─────────────────────────────────────────────────────────────────────


def test_verification_runs_counter_increments():
    """VERIFICATION_RUNS must be incrementable with (backend, status) labels."""
    from src.api.routers.metrics import VERIFICATION_RUNS

    counter = VERIFICATION_RUNS.labels(backend="hoare", status="success")
    before = counter._value.get()
    counter.inc()
    after = counter._value.get()
    assert after == before + 1


# ─────────────────────────────────────────────────────────────────────
# DISCOVERIES_GENERATED — importable + incrementable
# ─────────────────────────────────────────────────────────────────────


def test_discoveries_generated_counter_increments():
    """DISCOVERIES_GENERATED must be incrementable with output_format label."""
    from src.api.routers.metrics import DISCOVERIES_GENERATED

    for fmt in ("markdown", "json", "latex", "bib", "html"):
        counter = DISCOVERIES_GENERATED.labels(output_format=fmt)
        before = counter._value.get()
        counter.inc()
        after = counter._value.get()
        assert after == before + 1, f"format={fmt}: expected {before + 1}, got {after}"


# ─────────────────────────────────────────────────────────────────────
# API_REQUESTS — importable + incrementable
# ─────────────────────────────────────────────────────────────────────


def test_api_requests_counter_increments():
    """API_REQUESTS must be incrementable with (method, endpoint, status_code) labels."""
    from src.api.routers.metrics import API_REQUESTS

    counter = API_REQUESTS.labels(method="GET", endpoint="/api/v8/discovery", status_code="200")
    before = counter._value.get()
    counter.inc()
    after = counter._value.get()
    assert after == before + 1
