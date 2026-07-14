# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
# type: ignore
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


logger = logging.getLogger(__name__)


@dataclass
class PipelineProgress:
    """Progress event emitted during pipeline execution."""

    stage: str
    step: int
    total_steps: int
    status: str  # "started" | "in_progress" | "completed" | "failed"
    message: str
    elapsed: float
    data: dict[str, Any] | None = None
    pipeline_id: str = ""
    mode: str = ""
    timestamp: float = field(default_factory=time.time)


class ProgressEmitter:
    """Fire-and-forget progress event emitter.

    Events are broadcast to all subscribers. If no subscriber is registered,
    events are silently discarded. Emit is non-blocking: it uses
    put_nowait so the pipeline is never blocked by a slow subscriber.
    """

    def __init__(self, max_queue: int = 256) -> None:
        self._subscribers: list[asyncio.Queue[PipelineProgress]] = []
        self._history: deque[PipelineProgress] = deque(maxlen=200)
        self._lock = asyncio.Lock()

    async def emit(self, progress: PipelineProgress) -> None:
        """Emit a progress event to all subscribers (fire-and-forget).

        If no subscriber is registered, the event is silently discarded.
        Uses put_nowait to never block the pipeline.
        """
        self._history.append(progress)
        async with self._lock:
            dead: list[asyncio.Queue[PipelineProgress]] = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(progress)
                except asyncio.QueueFull:
                    dead.append(queue)
            for d in dead:
                self._subscribers.remove(d)

    def emit_sync(self, progress: PipelineProgress) -> None:
        """Synchronous emit wrapper for non-async pipeline stages."""
        self._history.append(progress)
        # When called from sync context, try to schedule
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(progress))
        except RuntimeError:
            pass  # No event loop — silently discard

    def subscribe_queue(self) -> asyncio.Queue[PipelineProgress]:
        """Subscribe via raw asyncio.Queue for polling with get_nowait().

        Usage (CLI):
            queue = emitter.subscribe_queue()
            try:
                progress = queue.get_nowait()
            except asyncio.QueueEmpty:
                logger.debug("progress queue empty", exc_info=True)
                pass
        """
        queue: asyncio.Queue[PipelineProgress] = asyncio.Queue(maxsize=256)
        self._subscribers.append(queue)
        return queue

    def unsubscribe_queue(self, queue: asyncio.Queue[PipelineProgress]) -> None:
        """Remove a queue subscription."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def subscribe(self) -> AsyncIterator[PipelineProgress]:
        """Subscribe to progress events. Returns an async iterator.

        Usage:
            async for progress in emitter.subscribe():
                render_progress(progress)
        """
        queue: asyncio.Queue[PipelineProgress] = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.append(queue)
        try:
            while True:
                try:
                    progress = await asyncio.wait_for(queue.get(), timeout=300)
                    yield progress
                except TimeoutError:
                    break
        finally:
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)

    def get_history(self, count: int = 50) -> list[PipelineProgress]:
        """Get recent progress history."""
        return list(self._history)[-count:]

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


# Progress taxonomy for UniversalSolvePipeline (blast solve) — up to 12 stages in deep-work mode.
# HILDiscoveryPipeline (blast turbo / c4_solve) runs 7 phases A→G; see hil_pipeline.py.
PIPELINE_12_STAGES: list[dict[str, str]] = [
    {"step": 1, "stage": "C4 Navigation", "short": "C4"},
    {"step": 2, "stage": "TRIZ Contradiction", "short": "TRIZ"},
    {"step": 3, "stage": "UCOS Analysis", "short": "UCOS"},
    {"step": 4, "stage": "QZRF Operators", "short": "QZRF"},
    {"step": 5, "stage": "Gap Mining", "short": "GAP"},
    {"step": 6, "stage": "Hypothesis Generation", "short": "HYP"},
    {"step": 7, "stage": "Simulation", "short": "SIM"},
    {"step": 8, "stage": "Formal Verification", "short": "VERIFY"},
    {"step": 9, "stage": "Novelty Validation", "short": "NOVELTY"},
    {"step": 10, "stage": "Self-Critique", "short": "CRITIQUE"},
    {"step": 11, "stage": "Dissertation", "short": "DISSERT"},
    {"step": 12, "stage": "Quality Control", "short": "QUALITY"},
]
