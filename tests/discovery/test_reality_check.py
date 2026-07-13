"""Tests for RealityCheckStep expanded patterns and falsifier integration."""

from __future__ import annotations

import pytest

from src.agents.pipeline.steps.step_02d_reality_check import RealityCheckStep


pytestmark = pytest.mark.anyio


class TestExtraordinaryPatterns:
    """Original extraordinary claim patterns."""

    async def test_fusion_q_gte_1(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "Our compact reactor achieves Q >= 1."})
        assert result.output_data["is_extraordinary"] is True
        assert any("fusion" in w["domain"] for w in result.output_data["warnings"])

    async def test_perpetual_motion(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "We built a perpetual motion machine."})
        assert result.output_data["is_extraordinary"] is True
        assert any("physics" in w["domain"] for w in result.output_data["warnings"])

    async def test_hundred_percent_cure(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "Our drug provides 100% cure for cancer."})
        assert result.output_data["is_extraordinary"] is True
        assert any("medicine" in w["domain"] for w in result.output_data["warnings"])

    async def test_no_false_positive(self) -> None:
        step = RealityCheckStep()
        result = await step.execute(
            {"problem": "We study protein folding using molecular dynamics."}
        )
        assert result.output_data["is_extraordinary"] is False
        assert result.output_data["warning_count"] == 0


class TestNumericalPatterns:
    """New numerical outlier detection."""

    async def test_three_hundred_percent_improvement(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "The catalyst shows 300% improvement in yield."})
        assert result.output_data["is_extraordinary"] is True
        assert any("metrics" in w["domain"] for w in result.output_data["warnings"])

    async def test_ten_fold_increase(self) -> None:
        step = RealityCheckStep()
        result = await step.execute(
            {"problem": "The new method provides a 15-fold increase in efficiency."}
        )
        assert result.output_data["is_extraordinary"] is True
        assert any("metrics" in w["domain"] for w in result.output_data["warnings"])

    async def test_orders_of_magnitude(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "Our approach is orders of magnitude better."})
        assert result.output_data["is_extraordinary"] is True

    async def test_normal_percentage_ok(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "The yield improved by 15%."})
        assert result.output_data["is_extraordinary"] is False


class TestDomainPatterns:
    """New domain-specific red flags."""

    async def test_room_temperature_superconductor(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "We discovered a room-temperature superconductor."})
        assert result.output_data["is_extraordinary"] is True
        assert any("materials" in w["domain"] for w in result.output_data["warnings"])

    async def test_water_powered_car(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "Our water-powered car engine runs on HHO gas."})
        assert result.output_data["is_extraordinary"] is True
        assert any("energy" in w["domain"] for w in result.output_data["warnings"])

    async def test_vaccine_autism(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "Vaccines cause autism according to our study."})
        assert result.output_data["is_extraordinary"] is True
        assert any("medicine" in w["domain"] for w in result.output_data["warnings"])

    async def test_flat_earth(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "The earth is flat and NASA lies."})
        assert result.output_data["is_extraordinary"] is True
        assert any("astronomy" in w["domain"] for w in result.output_data["warnings"])

    async def test_5g_conspiracy(self) -> None:
        step = RealityCheckStep()
        result = await step.execute({"problem": "5G radiation causes COVID-19."})
        assert result.output_data["is_extraordinary"] is True
        assert any("health" in w["domain"] for w in result.output_data["warnings"])

    async def test_creation_science(self) -> None:
        step = RealityCheckStep()
        result = await step.execute(
            {"problem": "Intelligent design is supported by scientific evidence."}
        )
        assert result.output_data["is_extraordinary"] is True


class TestSolutionCheck:
    """Reality check on solution/hypothesis text."""

    async def test_hypothesis_text_checked(self) -> None:
        step = RealityCheckStep()
        result = await step.execute(
            {
                "problem": "We study materials science.",
                "hypothesis": {
                    "text": "Our material achieves 500% improvement in tensile strength."
                },
            }
        )
        assert result.output_data["is_extraordinary"] is True
        assert result.output_data["warning_count"] >= 1

    async def test_solution_text_checked(self) -> None:
        step = RealityCheckStep()
        result = await step.execute(
            {
                "problem": "We study biology.",
                "solution": "The treatment provides a 100% cure rate with zero side effects.",
            }
        )
        assert result.output_data["is_extraordinary"] is True
        assert result.output_data["extraordinary_count"] >= 1


class TestStructuredOutput:
    """Output format includes separated counts."""

    async def test_has_extraordinary_and_falsifier_counts(self) -> None:
        step = RealityCheckStep()
        result = await step.execute(
            {"problem": "Our perpetual motion machine generates free energy."}
        )
        assert "extraordinary_count" in result.output_data
        assert "falsifier_count" in result.output_data
        assert isinstance(result.output_data["extraordinary_count"], int)
        assert isinstance(result.output_data["falsifier_count"], int)
