"""
Backward-compatibility shim.

The event bus is cross-cutting infrastructure (pub/sub), not pipeline-specific —
it now lives in src/infrastructure/events.py so lower-level packages (e.g.
verification) can publish events without depending on the high-level `pipeline`
package. Re-exported here so existing `src.pipeline.events` imports keep working.
"""
from __future__ import annotations

from src.infrastructure.events import EventBus, PipelineEvent, event_bus


__all__ = ["EventBus", "PipelineEvent", "event_bus"]
