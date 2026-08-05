"""Contract: NewtonResult is a dataclass; patterns convert via helper, never .get on it."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.simulations.newton_bridge import (
    NewtonMode,
    NewtonResult,
    newton_result_as_dict,
    newton_result_usable_for_pattern,
)


def test_newton_result_has_no_dict_get() -> None:
    nr = NewtonResult(status="success", data={"u": 1.0})
    assert not hasattr(nr, "get")


def test_newton_result_as_dict_maps_status_and_payload() -> None:
    nr = NewtonResult(
        status="success",
        mode=NewtonMode.GPU,
        execution_time=0.12,
        data={"velocity": [1.0]},
        metrics={"reynolds": 100.0},
        error_message="",
    )
    d = newton_result_as_dict(nr)
    assert d["status"] == "success"
    assert d["result"] == {"velocity": [1.0]}
    assert d["metrics"]["reynolds"] == 100.0
    assert d["error"] == ""
    # Mutable dict for pattern_id stamping
    d["pattern_id"] = "cfd"
    assert d["pattern_id"] == "cfd"


def test_newton_result_as_dict_falls_back_to_metrics_when_data_empty() -> None:
    nr = NewtonResult(status="success", data={}, metrics={"ke": 2.0})
    d = newton_result_as_dict(nr)
    assert d["result"] == {"ke": 2.0}


def test_xpbd_fall_not_usable_for_cfd() -> None:
    fake = {
        "status": "success",
        "result": {
            "fell": True,
            "z0": 2.0,
            "z_final": -1.0,
            "body_count": 1,
            "backend": "newton_physics",
        },
        "stub": False,
    }
    assert newton_result_usable_for_pattern(fake, pattern_id="cfd") is False
    assert newton_result_usable_for_pattern(fake, pattern_id="rigid_body") is True


@pytest.mark.asyncio
async def test_cfd_accepts_newton_result_via_helper_not_raw_get() -> None:
    """Behavioral: CFD Newton path survives NewtonResult (not dict) from bridge."""
    from patterns.core import Hypothesis, SimulationStatus
    from patterns.library.cfd import CFDPattern

    nr = NewtonResult(
        status="success",
        data={"flow": "ok"},
        metrics={"reynolds": 10.0},
    )
    mock_bridge = MagicMock()
    mock_bridge.available = True
    mock_bridge.run_simulation.return_value = nr

    pattern = CFDPattern()
    with patch("src.simulations.newton_bridge.NewtonBridge", return_value=mock_bridge):
        result = await pattern.run(
            Hypothesis(title="laminar flow", description="CFD channel"),
            {"flow_type": "laminar", "grid_size": 8},
        )
    assert result.status == SimulationStatus.COMPLETED
    assert result.logs and "Newton" in result.logs[0]
    mock_bridge.run_simulation.assert_called_once()
