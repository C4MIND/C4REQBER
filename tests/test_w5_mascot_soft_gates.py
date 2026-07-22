"""W5 regression: mascot must not celebrate on soft gate / partial failure."""

from __future__ import annotations

from src.cli.cube_mascot import inject_mascot_status
from src.utils.honesty_status import mascot_state_from_outer_status, outer_status_from_hil_like


def test_mascot_state_from_outer_status_never_done_on_partial() -> None:
    assert mascot_state_from_outer_status("success") == "done"
    assert mascot_state_from_outer_status("partial") == "partial"
    assert mascot_state_from_outer_status("error") == "error"
    assert mascot_state_from_outer_status("unavailable") == "partial"


def test_outer_status_partial_when_gates_fail() -> None:
    assert (
        outer_status_from_hil_like(
            quality_passed_all=False,
            quality_score=72,
            sim_status="success",
            gate_any_failed=True,
        )
        == "partial"
    )


def test_inject_mascot_partial_not_done_cube() -> None:
    rendered = inject_mascot_status(mode="turbo", state="partial", sources=3)
    assert "◈▣◈ ✓" not in rendered  # done cube glyph
    assert "partial" in rendered.lower() or "◈▣▫" in rendered or "▫" in rendered


def test_quality_score_alone_not_success_when_gates_failed() -> None:
    outer = outer_status_from_hil_like(
        quality_passed_all=False,
        quality_score=88,
        sim_status="success",
        gate_any_failed=True,
        sources_requested=True,
        verified_count=5,
    )
    assert outer == "partial"
    assert mascot_state_from_outer_status(outer) == "partial"
