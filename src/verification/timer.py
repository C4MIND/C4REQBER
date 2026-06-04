"""Verification Timer — smart timeout management for formal verification backends.

Handles the reality that different provers have wildly different performance:
- Z3: ~9ms (instant)
- Lean4: ~5-30s
- Dafny: ~10-60s
- Coq: ~30s-5min (sometimes 30+ min on trivial proofs!)
- Agda: ~1-30min (21 min observed on trivial theorem)
- Hoare: instant (conceptual)

Strategy: soft timeout → user warning → hard timeout → auto-kill + fallback
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable


logger = logging.getLogger(__name__)


# Timeout configuration per backend (seconds)
# Format: (soft_timeout, hard_timeout)
BACKEND_TIMEOUTS = {
    "z3":        (0.5,   5.0),      # 500ms soft, 5s hard (should be instant)
    "lean4":     (30.0,  120.0),    # 30s soft, 2min hard
    "dafny":     (60.0,  180.0),    # 1min soft, 3min hard
    "coq":       (60.0,  180.0),    # 1min soft, 3min hard (Coq can hang forever!)
    "agda":      (60.0,  1200.0),   # 1min soft, 20min hard (Agda is VERY SLOW)
    "hoare":     (1.0,   5.0),      # Instant
}


@dataclass
class TimingInfo:
    """Complete timing information for a verification attempt."""
    backend: str
    started_at: float
    ended_at: float = 0.0
    elapsed_ms: int = 0
    soft_timeout_ms: int = 0
    hard_timeout_ms: int = 0
    was_killed: bool = False
    was_fallback: bool = False
    fallback_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "elapsed_ms": self.elapsed_ms,
            "soft_timeout_ms": self.soft_timeout_ms,
            "hard_timeout_ms": self.hard_timeout_ms,
            "was_killed": self.was_killed,
            "was_fallback": self.was_fallback,
            "fallback_reason": self.fallback_reason,
        }


@dataclass
class VerificationProgress:
    """Real-time progress of a verification attempt."""
    backend: str
    status: str  # "running", "soft_timeout_exceeded", "killed", "completed", "fallback"
    elapsed_seconds: float
    soft_timeout_seconds: float
    hard_timeout_seconds: float
    percent_complete: float  # estimated 0-100
    message: str = ""


class VerificationTimer:
    """Timer that tracks verification progress and enforces timeouts."""

    def __init__(self, backend: str) -> None:
        self.backend = backend
        self.soft_timeout, self.hard_timeout = BACKEND_TIMEOUTS.get(backend, (30.0, 120.0))
        self.start_time = 0.0
        self._killed = False
        self._timing_info: TimingInfo | None = None
        self._progress_callbacks: list[Callable[[VerificationProgress], None]] = []

    def add_progress_callback(self, cb: Callable[[VerificationProgress], None]) -> None:
        self._progress_callbacks.append(cb)

    def start(self) -> None:
        """Start."""
        self.start_time = time.perf_counter()
        self._killed = False
        self._timing_info = TimingInfo(
            backend=self.backend,
            started_at=self.start_time,
            soft_timeout_ms=int(self.soft_timeout * 1000),
            hard_timeout_ms=int(self.hard_timeout * 1000),
        )

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def check_soft_timeout(self) -> bool:
        return self.elapsed() > self.soft_timeout

    def check_hard_timeout(self) -> bool:
        return self.elapsed() > self.hard_timeout

    def kill(self) -> None:
        self._killed = True

    def is_killed(self) -> bool:
        return self._killed

    def get_progress(self) -> VerificationProgress:
        """Get progress."""
        elapsed = self.elapsed()
        # Estimate percent: assume linear up to soft timeout = 80%, then uncertainty
        if elapsed < self.soft_timeout:
            pct = min(80.0, (elapsed / self.soft_timeout) * 80.0)
        else:
            pct = min(95.0, 80.0 + (elapsed - self.soft_timeout) / (self.hard_timeout - self.soft_timeout) * 15.0)

        status = "running"
        message = f"Verifying with {self.backend}..."
        if self._killed:
            status = "killed"
            message = f"Killed after {elapsed:.1f}s (hard timeout)"
        elif elapsed > self.hard_timeout:
            status = "killed"
            message = f"Hard timeout ({self.hard_timeout:.0f}s) exceeded"
        elif elapsed > self.soft_timeout:
            status = "soft_timeout_exceeded"
            message = f"Slow verification ({elapsed:.1f}s > {self.soft_timeout:.0f}s soft timeout)"

        return VerificationProgress(
            backend=self.backend,
            status=status,
            elapsed_seconds=elapsed,
            soft_timeout_seconds=self.soft_timeout,
            hard_timeout_seconds=self.hard_timeout,
            percent_complete=pct,
            message=message,
        )

    def _emit_progress(self) -> None:
        progress = self.get_progress()
        for cb in self._progress_callbacks:
            try:
                cb(progress)
            except (ValueError, RuntimeError):
                pass

    async def run_with_timeout(
        self,
        coro: Any,
        on_soft_timeout: Callable[[], None] | None = None,
    ) -> tuple[Any, TimingInfo]:
        """Run coroutine with soft + hard timeout enforcement.

        Returns (result, timing_info). Result may be None if killed.
        """
        self.start()
        assert self._timing_info is not None

        # Start progress reporting task
        progress_task = asyncio.create_task(self._progress_loop())

        try:
            # Wait with hard timeout
            result = await asyncio.wait_for(coro, timeout=self.hard_timeout)
            self._timing_info.ended_at = time.perf_counter()
            self._timing_info.elapsed_ms = int(self.elapsed() * 1000)
            progress_task.cancel()
            return result, self._timing_info

        except TimeoutError:
            self._timing_info.was_killed = True
            self._timing_info.ended_at = time.perf_counter()
            self._timing_info.elapsed_ms = int(self.elapsed() * 1000)
            self._timing_info.fallback_reason = f"Hard timeout ({self.hard_timeout:.0f}s) exceeded"
            progress_task.cancel()
            logger.warning("%s verification killed after %.1fs (hard timeout)", self.backend, self.elapsed())
            return None, self._timing_info

    async def _progress_loop(self) -> None:
        """Emit progress updates every second."""
        try:
            while True:
                await asyncio.sleep(1.0)
                if self.is_killed():
                    break
                self._emit_progress()
                if self.check_soft_timeout():
                    logger.warning("%s soft timeout exceeded (%.1fs > %.0fs)",
                                 self.backend, self.elapsed(), self.soft_timeout)
        except asyncio.CancelledError:
            pass


class VerificationTimeoutManager:
    """Manages timeouts across all backends with smart fallback strategy."""

    @staticmethod
    def get_timeout(backend: str) -> tuple[float, float]:
        return BACKEND_TIMEOUTS.get(backend, (30.0, 120.0))

    @staticmethod
    def format_elapsed(seconds: float) -> str:
        """Format elapsed time for human display."""
        if seconds < 1.0:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60.0:
            return f"{seconds:.1f}s"
        else:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"

    @staticmethod
    def get_recommended_timeout_for_hypothesis(hypothesis: dict[str, Any]) -> dict[str, float]:
        """Suggest timeouts based on hypothesis complexity."""
        claim = f"{hypothesis.get('title', '')} {hypothesis.get('description', '')}"
        claim_lower = claim.lower()

        # Detect complexity indicators
        complexity = 1.0
        if any(kw in claim_lower for kw in ["theorem", "lemma", "proof", "forall", "exists"]):
            complexity *= 1.5  # Pure math is harder
        if any(kw in claim_lower for kw in ["protocol", "concurrent", "distributed"]):
            complexity *= 2.0  # Distributed systems are complex
        if len(claim) > 200:
            complexity *= 1.3  # Long claims take longer

        return {
            "coq_soft": 60.0 * complexity,
            "coq_hard": min(180.0 * complexity, 600.0),  # Max 10 min
            "agda_soft": 60.0 * complexity,
            "agda_hard": min(180.0 * complexity, 600.0),
            "lean4_soft": 30.0 * complexity,
            "lean4_hard": min(120.0 * complexity, 300.0),
        }
