"""Suite 05 — HIL discover resets cost tracker (no cumulative inflation)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_hil_discover_resets_cost_tracker() -> None:
    from src.pipeline.hil_pipeline import HILDiscoveryPipeline

    class StopPipeline(Exception):
        pass

    calls = {"reset": 0}

    class FakeTracker:
        def reset(self) -> None:
            calls["reset"] += 1

    real = HILDiscoveryPipeline.__new__(HILDiscoveryPipeline)
    real.config = MagicMock()
    real.user_profile = None

    # Abort immediately after reset by failing DiscoveryRecord construction on 2nd use —
    # reset runs right after first DiscoveryRecord; raise from CQRS import path next.
    with (
        patch("src.llm.cost_tracker.get_cost_tracker", return_value=FakeTracker()),
        patch(
            "src.architecture.cqrs.CqrsBus",
            side_effect=StopPipeline("after-reset"),
        ),
    ):
        # CQRS is in try/except — need a hard stop after reset that is not swallowed.
        # Raise from event_bus / next phase by patching PhaseA to raise.
        with patch(
            "src.pipeline.hil_pipeline.PhaseA_USPCognitiveFraming",
            side_effect=StopPipeline("phase-a"),
        ):
            with pytest.raises(StopPipeline):
                await HILDiscoveryPipeline.discover(real, "topic-x")

    assert calls["reset"] == 1
