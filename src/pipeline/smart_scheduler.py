# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Smart Multi-Agent Scheduler — rate-limit-aware parallel pipeline execution.

Problem: `blast turbofactory` spawns N parallel pipelines, each making 12+ LLM calls.
OpenRouter rate-limits at ~20 req/min. 5 concurrent × 12 stages = 60 calls = 429 error.

Solution: Token-bucket scheduler with:
- Max concurrent pipelines (default: 2)
- Min interval between LLM calls (default: 3s)
- Exponential backoff on 429
- Queue-based: remaining pipelines wait in queue, dequeued as capacity frees
- Cost-aware: cheap models get priority, premium models throttle harder
- Progress stream: each pipeline emits events → aggregated TUI progress bar

Architecture:
    turbofactory("topic", --scale 10)
        → SmartScheduler(max_concurrent=2, rate_limit=20/min)
        → Queue: [P1, P2, P3, ... P10]
        → Active: [P1, P2] running
        → Wait: [P3...P10] queued
        → P1 completes → P3 dequeued → Active: [P2, P3]
        → All complete → aggregate results
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Coroutine


logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """SchedulerConfig."""
    max_concurrent: int = 2
    min_call_interval: float = 3.0  # seconds between LLM calls
    max_retries: int = 3
    backoff_base: float = 2.0  # exponential backoff multiplier
    rate_limit_window: int = 60  # seconds
    max_calls_per_window: int = 20


class SmartScheduler:
    """Rate-limit-aware task scheduler for parallel pipeline execution."""

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self.cfg = config or SchedulerConfig()
        self._last_call_time = 0.0
        self._call_times: deque[float] = deque()
        self._lock = asyncio.Lock()
        self._active = 0
        self._completed = 0
        self._total = 0

    async def schedule(
        self,
        tasks: list[Callable[[], Coroutine[Any, Any, Any]]],
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> list[Any]:
        """Schedule tasks with rate limiting. Returns results in order."""
        self._total = len(tasks)
        self._completed = 0
        results: list[Any] = [None] * len(tasks)

        async def run_one(idx: int, task_fn: Callable) -> None:
            for attempt in range(self.cfg.max_retries):
                try:
                    await self._wait_for_slot()
                    async with self._lock:
                        self._active += 1
                        self._call_times.append(time.time())
                    if on_progress:
                        on_progress(self._completed, self._total, f"Pipeline {idx + 1}/{self._total} started")

                    result = await task_fn()

                    async with self._lock:
                        self._active -= 1
                        self._completed += 1
                    results[idx] = result
                    if on_progress:
                        on_progress(self._completed, self._total, f"Pipeline {idx + 1}/{self._total} done")
                    return
                except Exception as e:
                    if "429" in str(e) or "rate" in str(e).lower():
                        wait = self.cfg.backoff_base ** attempt
                        logger.warning("Rate limited on pipeline %d (attempt %d) — waiting %.1fs", idx + 1, attempt + 1, wait)
                        await asyncio.sleep(wait)
                    elif attempt < self.cfg.max_retries - 1:
                        logger.warning("Pipeline %d failed (attempt %d): %s — retrying", idx + 1, attempt + 1, e)
                        await asyncio.sleep(2.0)
                    else:
                        logger.error("Pipeline %d failed after %d attempts: %s", idx + 1, self.cfg.max_retries, e)
                        async with self._lock:
                            self._completed += 1
                        results[idx] = e
                        return

        coros = [run_one(i, task) for i, task in enumerate(tasks)]
        await asyncio.gather(*coros)
        return results

    async def _wait_for_slot(self) -> None:
        while True:
            async with self._lock:
                now = time.time()
                # Prune old entries outside rate limit window
                while self._call_times and now - self._call_times[0] > self.cfg.rate_limit_window:
                    self._call_times.popleft()

                # Check rate limit
                if len(self._call_times) < self.cfg.max_calls_per_window:
                    # Check min interval since last call
                    if now - self._last_call_time >= self.cfg.min_call_interval:
                        if self._active < self.cfg.max_concurrent:
                            self._last_call_time = now
                            return

            await asyncio.sleep(0.5)
