"""Pipeline-TUI Event Bridge — real-time streaming from pipelines to dashboard.

Usage:
    from src.pipeline.events import event_bus

    # In pipeline:
    await event_bus.emit("phase_start", {"phase": "A", "name": "USP Cognitive Framing"})

    # In TUI:
    async for event in event_bus.subscribe():
        update_dashboard(event)
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


logger = logging.getLogger(__name__)


@dataclass
class PipelineEvent:
    """Event emitted by pipeline during execution."""
    event_type: str  # phase_start, phase_end, gate_check, quality_report, error, complete
    timestamp: float
    data: dict[str, Any] = field(default_factory=dict)
    pipeline_id: str = ""
    mode: str = ""  # solve, turbo, flash, turbofactory


class EventBus:
    """Async event bus for pipeline → TUI communication."""

    def __init__(self, max_history: int = 1000) -> None:
        self._subscribers: list[asyncio.Queue[PipelineEvent]] = []
        self._history: deque[PipelineEvent] = deque(maxlen=max_history)
        self._callbacks: list[Callable[[PipelineEvent], None]] = []
        self._lock = asyncio.Lock()

    async def emit(self, event_type: str, data: dict[str, Any], pipeline_id: str = "", mode: str = "") -> None:
        """Emit event to all subscribers."""
        import time
        event = PipelineEvent(
            event_type=event_type,
            timestamp=time.time(),
            data=data,
            pipeline_id=pipeline_id,
            mode=mode,
        )
        self._history.append(event)

        # Async subscribers
        async with self._lock:
            dead = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(queue)
            for d in dead:
                self._subscribers.remove(d)

        # Sync callbacks
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.debug("Event callback error: %s", e)

    def subscribe(self) -> asyncio.Queue[PipelineEvent]:
        """Subscribe to events. Returns queue that receives all future events."""
        queue: asyncio.Queue[PipelineEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue

    def add_callback(self, callback: Callable[[PipelineEvent], None]) -> None:
        """Add sync callback for events."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PipelineEvent], None]) -> None:
        """Remove sync callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def unsubscribe(self, queue: asyncio.Queue[PipelineEvent]) -> None:
        """Unsubscribe a queue from events."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_history(self, event_type: str | None = None, count: int = 100) -> list[PipelineEvent]:
        """Get recent event history, optionally filtered by type."""
        events = list(self._history)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-count:]

    def clear(self) -> None:
        """Clear all subscribers and history."""
        self._subscribers.clear()
        self._callbacks.clear()
        self._history.clear()


# Global event bus instance
event_bus = EventBus()
