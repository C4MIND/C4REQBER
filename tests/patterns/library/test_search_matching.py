"""
Tests for src/patterns/library/search_matching.py (Search and Matching/DMP pattern)

Covers:
- SearchMatchingConfig dataclass
- SearchMatchingModel initialization
- matching_function() properties
- job_finding_rate() and job_filling_rate()
- solve_steady_state()
- simulate_dynamics()
- analyze_policy()
- _calculate_welfare()
- run() integration
- get_metadata()
- Edge cases: extreme parameters, policy comparisons
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.search_matching import (

    SearchMatchingModel,
    SearchMatchingConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestSearchMatchingConfig:
    def test_default_init(self):
        cfg = SearchMatchingConfig()
        assert cfg.alpha == 0.5
        assert cfg.gamma == 0.5
        assert cfg.r == 0.05
        assert cfg.delta == 0.03
        assert cfg.c == 0.3
        assert cfg.z == 0.4
        assert cfg.p == 1.0
        assert cfg.eta == 0.5

    def test_custom_init(self):
        cfg = SearchMatchingConfig(
            alpha=0.6,
            gamma=0.4,
            r=0.04,
            delta=0.02
        )
        assert cfg.alpha == 0.6
        assert cfg.gamma == 0.4
        assert cfg.r == 0.04
        assert cfg.delta == 0.02


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestSearchMatchingModelInit:
    def test_default_init(self):
        model = SearchMatchingModel()
        assert model.config is not None

    def test_custom_config(self):
        cfg = SearchMatchingConfig(alpha=0.7)
        model = SearchMatchingModel(cfg)
        assert model.config.alpha == 0.7


# ═══════════════════════════════════════════════════════════════════
# Matching Function Tests
# ═══════════════════════════════════════════════════════════════════


class TestMatchingFunction:
    def test_zero_unemployment(self):
        model = SearchMatchingModel()
        m = model.matching_function(0, 0.1)
        assert m == 0

    def test_zero_vacancies(self):
        model = SearchMatchingModel()
        m = model.matching_function(0.1, 0)
        assert m == 0

    def test_positive_matches(self):
        model = SearchMatchingModel()
        m = model.matching_function(0.1, 0.1)
        assert m > 0

    def test_increasing_in_u(self):
        """Matches increase with unemployment"""
        model = SearchMatchingModel()
        m1 = model.matching_function(0.05, 0.1)
        m2 = model.matching_function(0.1, 0.1)
        assert m2 > m1

    def test_increasing_in_v(self):
        """Matches increase with vacancies"""
        model = SearchMatchingModel()
        m1 = model.matching_function(0.1, 0.05)
        m2 = model.matching_function(0.1, 0.1)
        assert m2 > m1

    def test_cobb_douglas_elasticity(self):
        """Matching function has constant returns to scale"""
        model = SearchMatchingModel(SearchMatchingConfig(alpha=0.5))
        m1 = model.matching_function(0.1, 0.1)
        m2 = model.matching_function(0.2, 0.2)
        # Doubling both should double matches (CRS)
        assert m2 == pytest.approx(2 * m1, rel=0.01)


# ═══════════════════════════════════════════════════════════════════
# Rate Function Tests
# ═══════════════════════════════════════════════════════════════════


class TestJobFindingRate:
    def test_increases_with_tightness(self):
        model = SearchMatchingModel()
        f1 = model.job_finding_rate(0.5)
        f2 = model.job_finding_rate(1.0)
        f3 = model.job_finding_rate(2.0)
        assert f3 > f2 > f1

    def test_positive(self):
        model = SearchMatchingModel()
        f = model.job_finding_rate(1.0)
        assert f > 0


class TestJobFillingRate:
    def test_decreases_with_tightness(self):
        model = SearchMatchingModel()
        q1 = model.job_filling_rate(0.5)
        q2 = model.job_filling_rate(1.0)
        q3 = model.job_filling_rate(2.0)
        assert q1 > q2 > q3

    def test_positive(self):
        model = SearchMatchingModel()
        q = model.job_filling_rate(1.0)
        assert q > 0


# ═══════════════════════════════════════════════════════════════════
# Steady State Tests
# ═══════════════════════════════════════════════════════════════════


class TestSolveSteadyState:
    def test_returns_dict(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        assert isinstance(ss, dict)

    def test_contains_required_keys(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        required = ["theta", "unemployment_rate", "vacancy_rate",
                   "job_finding_rate", "job_filling_rate", "match_rate", "wage"]
        for key in required:
            assert key in ss

    def test_unemployment_in_range(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        assert 0 < ss["unemployment_rate"] < 1

    def test_vacancy_positive(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        assert ss["vacancy_rate"] > 0

    def test_wage_between_bounds(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        # Wage should be between z (home production) and p (productivity)
        assert ss["wage"] >= model.config.z
        assert ss["wage"] <= model.config.p

    def test_tightness_positive(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        assert ss["tightness"] > 0


# ═══════════════════════════════════════════════════════════════════
# Dynamics Tests
# ═══════════════════════════════════════════════════════════════════


class TestSimulateDynamics:
    def test_returns_time_series(self):
        model = SearchMatchingModel()
        dyn = model.simulate_dynamics(T=50)
        assert isinstance(dyn, dict)
        assert len(dyn["unemployment"]) == 50
        assert len(dyn["vacancies"]) == 50
        assert len(dyn["wages"]) == 50

    def test_shock_effect(self):
        """Productivity shock should increase unemployment"""
        model = SearchMatchingModel()
        dyn = model.simulate_dynamics(T=100, shock_period=20)

        # Unemployment should increase after shock
        pre_shock = np.mean(dyn["unemployment"][15:20])
        post_shock = np.mean(dyn["unemployment"][30:40])
        assert post_shock > pre_shock

    def test_wages_change(self):
        model = SearchMatchingModel()
        dyn = model.simulate_dynamics(T=50)
        assert len(set(dyn["wages"])) > 1  # Wages should vary


# ═══════════════════════════════════════════════════════════════════
# Policy Analysis Tests
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzePolicy:
    def test_ui_policy_increases_unemployment(self):
        model = SearchMatchingModel()
        result = model.analyze_policy("unemployment_insurance")

        baseline_u = result["baseline"]["unemployment_rate"]
        higher_ui_u = result["higher_ui"]["unemployment_rate"]

        assert higher_ui_u > baseline_u

    def test_hiring_subsidy_increases_vacancies(self):
        model = SearchMatchingModel()
        result = model.analyze_policy("hiring_subsidy")

        baseline_v = result["baseline"]["vacancy_rate"]
        subsidy_v = result["hiring_subsidy"]["vacancy_rate"]

        assert subsidy_v > baseline_v

    def test_worker_power_increases_wage(self):
        model = SearchMatchingModel()
        result = model.analyze_policy("worker_power")

        baseline_w = result["baseline"]["wage"]
        higher_power_w = result["higher_worker_power"]["wage"]

        assert higher_power_w > baseline_w

    def test_elasticities_present(self):
        model = SearchMatchingModel()
        result = model.analyze_policy("unemployment_insurance")
        assert "elasticities" in result


# ═══════════════════════════════════════════════════════════════════
# Welfare Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateWelfare:
    def test_welfare_components(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        welfare = model._calculate_welfare(ss)

        assert "gross_output" in welfare
        assert "vacancy_costs" in welfare
        assert "net_output" in welfare
        assert "average_wage" in welfare

    def test_net_output_less_than_gross(self):
        model = SearchMatchingModel()
        ss = model.solve_steady_state()
        welfare = model._calculate_welfare(ss)

        assert welfare["net_output"] <= welfare["gross_output"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_returns_dict(self):
        model = SearchMatchingModel()
        result = model.run()
        assert isinstance(result, dict)

    def test_steady_state_present(self):
        model = SearchMatchingModel()
        result = model.run()
        assert "steady_state" in result

    def test_dynamics_present(self):
        model = SearchMatchingModel()
        result = model.run()
        assert "transition_dynamics" in result

    def test_policy_analysis_present(self):
        model = SearchMatchingModel()
        result = model.run()
        assert "policy_analysis" in result

    def test_efficiency_check(self):
        model = SearchMatchingModel()
        result = model.run()
        assert "efficiency" in result
        assert "hosios_satisfied" in result["efficiency"]

    def test_hosios_condition(self):
        """Hosios condition: alpha = gamma for efficiency"""
        # Efficient case
        cfg = SearchMatchingConfig(alpha=0.5, gamma=0.5)
        model = SearchMatchingModel(cfg)
        result = model.run()
        assert result["efficiency"]["hosios_satisfied"] is True

        # Inefficient case
        cfg = SearchMatchingConfig(alpha=0.5, gamma=0.3)
        model = SearchMatchingModel(cfg)
        result = model.run()
        assert result["efficiency"]["hosios_satisfied"] is False

    def test_welfare_present(self):
        model = SearchMatchingModel()
        result = model.run()
        assert "welfare" in result

    def test_model_type(self):
        model = SearchMatchingModel()
        result = model.run()
        assert result["model_type"] == "dmp_search_matching"


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = SearchMatchingModel.get_metadata()
        assert meta["pattern_id"] == 53
        assert meta["name"] == "Search and Matching"
        assert "category" in meta
        assert "description" in meta
        assert "parameters" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_high_destruction_rate(self):
        """High job destruction should increase unemployment"""
        cfg = SearchMatchingConfig(delta=0.1)
        model = SearchMatchingModel(cfg)
        ss = model.solve_steady_state()
        assert ss["unemployment_rate"] > 0.05

    def test_high_productivity(self):
        """High productivity should increase wages"""
        cfg = SearchMatchingConfig(p=2.0, z=0.5)
        model = SearchMatchingModel(cfg)
        ss = model.solve_steady_state()
        assert ss["wage"] > 0.5

    def test_low_matching_efficiency(self):
        """Low matching efficiency should increase unemployment"""
        cfg = SearchMatchingConfig(eta=0.1)
        model = SearchMatchingModel(cfg)
        ss = model.solve_steady_state()
        assert ss["unemployment_rate"] > 0.05

    def test_very_short_dynamics(self):
        model = SearchMatchingModel()
        dyn = model.simulate_dynamics(T=5)
        assert len(dyn["unemployment"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
