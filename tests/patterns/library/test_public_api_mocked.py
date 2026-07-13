"""
Mocked public-API unit tests for pattern library modules.

These tests focus on:
- Fast execution via mocked numerical backends
- Public API surface: can_simulate, run, get_metadata, config parsing
- Error handling paths
- Result formatting

They do NOT test numerical accuracy.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from patterns.core import Hypothesis, SimulationResult, SimulationStatus


# =============================================================================
# Bootstrap
# =============================================================================


class TestBootstrapPublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.bootstrap import BootstrapPattern

        return BootstrapPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(title="Bootstrap", description="confidence interval")

    def test_can_simulate_match(self, pattern):
        h = Hypothesis(title="Bootstrap resampling", description="standard error")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self, pattern):
        h = Hypothesis(title="Quantum physics", description="entanglement")
        assert pattern.can_simulate(h) is False

    def test_get_metadata(self, pattern):
        meta = pattern.get_metadata()
        assert meta["id"] == "bootstrap"
        assert "parameters" in meta

    def test_parse_config_empty(self, pattern):
        cfg = pattern._parse_config({})
        assert cfg.n_bootstrap == 1000
        assert cfg.statistic == "mean"

    def test_parse_config_custom(self, pattern):
        cfg = pattern._parse_config({"n_bootstrap": 500, "statistic": "median", "seed": 42})
        assert cfg.n_bootstrap == 500
        assert cfg.statistic == "median"
        assert cfg.seed == 42

    @pytest.mark.asyncio
    async def test_run_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_simulate_bootstrap",
            return_value={
                "metrics": {
                    "coverage": 1.0,
                    "bias": 0.01,
                    "standard_error": 0.2,
                    "n_bootstrap": 1000,
                },
                "logs": ["ok"],
            },
        ):
            result = await pattern.run(hypothesis, {"n_bootstrap": 100})
            assert result.status == SimulationStatus.COMPLETED
            assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_run_failure(self, pattern, hypothesis):
        with patch.object(pattern, "_simulate_bootstrap", side_effect=TypeError("bad config")):
            result = await pattern.run(hypothesis, {"n_bootstrap": 100})
            assert result.status == SimulationStatus.FAILED
            assert "bad config" in result.error_message

    def test_estimate_resources(self, pattern, hypothesis):
        res = pattern.estimate_resources(hypothesis)
        assert "memory_gb" in res
        assert "estimated_time_seconds" in res


# =============================================================================
# Cellular Automata
# =============================================================================


class TestCellularAutomataPublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.cellular_automata import CellularAutomataPattern

        return CellularAutomataPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(title="Game of Life", description="cellular automata")

    def test_can_simulate_match(self, pattern):
        h = Hypothesis(title="Conway's Game of Life", description="emergence")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self, pattern):
        h = Hypothesis(title="Stock prices", description="trading")
        assert pattern.can_simulate(h) is False

    def test_get_metadata(self, pattern):
        meta = pattern.get_metadata()
        assert meta["id"] == "cellular_automata"

    def test_parse_config_empty(self, pattern):
        cfg = pattern._parse_config({})
        assert cfg.model == "game_of_life"
        assert cfg.width == 100

    def test_parse_config_custom(self, pattern):
        cfg = pattern._parse_config({"model": "rule_110", "width": 20, "n_steps": 5})
        assert cfg.model == "rule_110"
        assert cfg.width == 20
        assert cfg.n_steps == 5

    @pytest.mark.asyncio
    async def test_run_gol_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_simulate_gol",
            return_value={
                "metrics": {
                    "final_density": 0.2,
                    "n_steps": 10,
                    "alive_cells": 10,
                    "model": "game_of_life",
                },
                "logs": ["ok"],
            },
        ):
            result = await pattern.run(
                hypothesis, {"model": "game_of_life", "width": 10, "height": 10, "n_steps": 10}
            )
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_rule110_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_simulate_rule110",
            return_value={
                "metrics": {"density": 0.3, "n_steps": 10, "ones_count": 5, "model": "rule_110"},
                "logs": ["ok"],
            },
        ):
            result = await pattern.run(
                hypothesis, {"model": "rule_110", "width": 10, "n_steps": 10}
            )
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_failure(self, pattern, hypothesis):
        with patch.object(pattern, "_simulate_gol", side_effect=KeyError("missing")):
            result = await pattern.run(
                hypothesis, {"model": "game_of_life", "width": 10, "height": 10, "n_steps": 10}
            )
            assert result.status == SimulationStatus.FAILED

    def test_calculate_confidence(self, pattern):
        score = pattern._calculate_confidence(
            {
                "metrics": {
                    "final_density": 0.2,
                    "n_steps": 100,
                    "alive_cells": 10,
                    "model": "game_of_life",
                }
            }
        )
        assert 0 <= score <= 0.9

    def test_estimate_resources(self, pattern, hypothesis):
        res = pattern.estimate_resources(hypothesis)
        assert "memory_gb" in res


# =============================================================================
# Agent Based
# =============================================================================


class TestAgentBasedPublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.agent_based import AgentBasedPattern

        return AgentBasedPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(title="Market agents", description="multi-agent simulation")

    def test_can_simulate_match(self, pattern):
        h = Hypothesis(title="Swarm behavior", description="emergence")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self, pattern):
        h = Hypothesis(title="Quantum mechanics", description="wave function")
        assert pattern.can_simulate(h) is False

    def test_get_metadata(self, pattern):
        meta = pattern.get_metadata()
        assert meta["id"] == "agent_based"

    def test_parse_config_empty(self, pattern):
        cfg = pattern._parse_config({})
        assert cfg.n_agents == 100
        assert cfg.agent_behavior == "adaptive"

    def test_parse_config_custom(self, pattern):
        cfg = pattern._parse_config(
            {"n_agents": 50, "network_type": "small_world", "random_seed": 7}
        )
        assert cfg.n_agents == 50
        assert cfg.network_type == "small_world"
        assert cfg.random_seed == 7

    @pytest.mark.asyncio
    async def test_run_success(self, pattern, hypothesis):
        with (
            patch.object(pattern, "_initialize_simulation") as mock_init,
            patch.object(pattern, "_run_simulation") as mock_run,
            patch.object(
                pattern,
                "_analyze_results",
                return_value={"metrics": {"final_mean_wealth": 10}, "logs": ["ok"]},
            ),
        ):
            result = await pattern.run(hypothesis, {"n_agents": 10, "n_steps": 10})
            assert result.status == SimulationStatus.COMPLETED
            mock_init.assert_called_once()
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_failure(self, pattern, hypothesis):
        with patch.object(pattern, "_initialize_simulation", side_effect=ValueError("bad init")):
            result = await pattern.run(hypothesis, {"n_agents": 10, "n_steps": 10})
            assert result.status == SimulationStatus.FAILED
            assert "bad init" in result.error_message

    def test_create_network_grid(self, pattern):
        from patterns.library.agent_based import AgentBasedConfig

        cfg = AgentBasedConfig(n_agents=9, network_type="grid")
        net = pattern._create_network(cfg)
        assert len(net) > 0

    def test_create_network_small_world(self, pattern):
        from patterns.library.agent_based import AgentBasedConfig

        cfg = AgentBasedConfig(n_agents=10, network_type="small_world")
        net = pattern._create_network(cfg)
        assert len(net) > 0

    def test_create_network_random(self, pattern):
        from patterns.library.agent_based import AgentBasedConfig

        cfg = AgentBasedConfig(n_agents=10, network_type="random")
        net = pattern._create_network(cfg)
        assert len(net) > 0

    def test_create_network_scale_free(self, pattern):
        from patterns.library.agent_based import AgentBasedConfig

        cfg = AgentBasedConfig(n_agents=10, network_type="scale_free")
        net = pattern._create_network(cfg)
        assert len(net) > 0

    def test_compute_metrics_empty(self, pattern):
        pattern.agents = {}
        metrics = pattern._compute_metrics()
        assert metrics == {}

    def test_calculate_confidence(self, pattern):
        score = pattern._calculate_confidence(
            {
                "metrics": {
                    "equilibrium_reached": 1,
                    "final_gini": 0.2,
                    "wealth_trend": 0.1,
                    "n_steps": 600,
                    "phase_transitions": 1,
                }
            }
        )
        assert 0 <= score <= 0.9

    def test_estimate_resources(self, pattern, hypothesis):
        res = pattern.estimate_resources(hypothesis)
        assert "memory_gb" in res


# =============================================================================
# CFD
# =============================================================================


class TestCFDPublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.cfd import CFDPattern

        return CFDPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(title="Fluid flow", description="navier-stokes")

    def test_can_simulate_match(self, pattern):
        h = Hypothesis(title="Aerodynamic drag", description="wind tunnel")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self, pattern):
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_get_metadata(self, pattern):
        meta = pattern.get_metadata()
        assert meta["id"] == "cfd"

    @pytest.mark.asyncio
    async def test_run_potential_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_potential_flow",
            return_value={"metrics": {"max_velocity": 1.0}, "logs": ["ok"]},
        ):
            result = await pattern.run(hypothesis, {"flow_type": "potential"})
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_stokes_success(self, pattern, hypothesis):
        with patch.object(
            pattern, "_stokes_flow", return_value={"metrics": {"drag_force": 0.1}, "logs": ["ok"]}
        ):
            result = await pattern.run(hypothesis, {"flow_type": "stokes"})
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_laminar_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_laminar_flow",
            return_value={"metrics": {"reynolds_number": 100}, "logs": ["ok"]},
        ):
            result = await pattern.run(hypothesis, {"flow_type": "laminar"})
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_turbulent_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_turbulent_flow",
            return_value={"metrics": {"reynolds_number": 10000}, "logs": ["ok"]},
        ):
            result = await pattern.run(hypothesis, {"flow_type": "turbulent"})
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_failure(self, pattern, hypothesis):
        with patch.object(pattern, "_potential_flow", side_effect=TypeError("bad grid")):
            result = await pattern.run(hypothesis, {"flow_type": "potential"})
            assert result.status == SimulationStatus.FAILED

    def test_calculate_confidence(self, pattern):
        score = pattern._calculate_confidence(
            {
                "metrics": {
                    "reynolds_number": 100,
                    "mass_conservation": 0.5,
                    "max_velocity": 1.0,
                    "pressure_drop": 10,
                }
            }
        )
        assert 0 <= score <= 0.85

    def test_estimate_resources(self, pattern, hypothesis):
        res = pattern.estimate_resources(hypothesis)
        assert "memory_gb" in res


# =============================================================================
# Thermal
# =============================================================================


class TestThermalPublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.thermal import ThermalPattern

        return ThermalPattern()

    @pytest.fixture
    def hypothesis(self):
        return Hypothesis(title="Heat transfer", description="conduction")

    def test_can_simulate_match(self, pattern):
        h = Hypothesis(title="Cooling system", description="heat sink")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_no_match(self, pattern):
        h = Hypothesis(title="Graph theory", description="shortest path")
        assert pattern.can_simulate(h) is False

    def test_get_metadata(self, pattern):
        meta = pattern.get_metadata()
        assert meta["id"] == "thermal"

    @pytest.mark.asyncio
    async def test_run_steady_state_1d_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_steady_state_1d",
            return_value={"metrics": {"max_temperature": 50}, "logs": ["ok"]},
        ):
            result = await pattern.run(
                hypothesis, {"analysis_type": "steady_state", "dimension": "1d"}
            )
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_steady_state_2d_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_steady_state_2d",
            return_value={"metrics": {"max_temperature": 50}, "logs": ["ok"]},
        ):
            result = await pattern.run(
                hypothesis, {"analysis_type": "steady_state", "dimension": "2d"}
            )
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_transient_1d_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_transient_1d",
            return_value={"metrics": {"max_temperature": 50}, "logs": ["ok"]},
        ):
            result = await pattern.run(
                hypothesis, {"analysis_type": "transient", "dimension": "1d"}
            )
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_transient_2d_success(self, pattern, hypothesis):
        with patch.object(
            pattern,
            "_transient_2d",
            return_value={"metrics": {"max_temperature": 50}, "logs": ["ok"]},
        ):
            result = await pattern.run(
                hypothesis, {"analysis_type": "transient", "dimension": "2d"}
            )
            assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_failure(self, pattern, hypothesis):
        with patch.object(pattern, "_steady_state_1d", side_effect=KeyError("missing key")):
            result = await pattern.run(
                hypothesis, {"analysis_type": "steady_state", "dimension": "1d"}
            )
            assert result.status == SimulationStatus.FAILED

    def test_calculate_confidence(self, pattern):
        score = pattern._calculate_confidence(
            {
                "metrics": {
                    "max_temperature": 100,
                    "min_temperature": 20,
                    "iterations": 100,
                    "thermal_conductivity": 200,
                }
            }
        )
        assert 0 <= score <= 0.9

    def test_estimate_resources(self, pattern, hypothesis):
        res = pattern.estimate_resources(hypothesis)
        assert "memory_gb" in res


# =============================================================================
# State Space
# =============================================================================

scipy = pytest.importorskip("scipy", reason="scipy not installed")


class TestStateSpacePublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.state_space import (
            ControlMethod,
            StateSpaceConfig,
            StateSpacePattern,
            SystemType,
        )

        cfg = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.LQR,
            simulation_steps=10,
        )
        return StateSpacePattern(cfg)

    def test_get_metadata(self):
        from patterns.library.state_space import StateSpacePattern

        meta = StateSpacePattern.get_metadata()
        assert meta["id"] == "state_space"
        assert "parameters" in meta

    def test_config_post_init(self):
        from patterns.library.state_space import ControlMethod, StateSpaceConfig, SystemType

        cfg = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR, control_method=ControlMethod.LQR
        )
        assert cfg.A is not None
        assert cfg.B is not None
        assert cfg.Q is not None
        assert cfg.R is not None

    def test_initialize_controller_lqr(self, pattern):
        pattern._initialize_controller()
        assert pattern.controller is not None
        assert pattern.controller.K is not None

    def test_initialize_controller_pole_placement(self):
        from patterns.library.state_space import (
            ControlMethod,
            StateSpaceConfig,
            StateSpacePattern,
            SystemType,
        )

        cfg = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.POLE_PLACEMENT,
            desired_poles=[0.5, 0.6],
            simulation_steps=10,
        )
        pat = StateSpacePattern(cfg)
        pat._initialize_controller()
        assert pat.controller.K is not None

    def test_initialize_controller_deadbeat(self):
        from patterns.library.state_space import (
            ControlMethod,
            StateSpaceConfig,
            StateSpacePattern,
            SystemType,
        )

        cfg = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.DEADBEAT,
            simulation_steps=10,
        )
        pat = StateSpacePattern(cfg)
        pat._initialize_controller()
        assert pat.controller.K is not None

    def test_initialize_controller_lqg(self):
        from patterns.library.state_space import (
            ControlMethod,
            StateSpaceConfig,
            StateSpacePattern,
            SystemType,
        )

        cfg = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.LQG,
            simulation_steps=10,
        )
        pat = StateSpacePattern(cfg)
        pat._initialize_controller()
        assert pat.controller.K is not None
        assert pat.controller.L is not None

    def test_get_reference_constant(self, pattern):
        ref = pattern._get_reference(0.0)
        np.testing.assert_array_equal(ref, pattern.config.reference_value)

    def test_get_reference_sinusoid(self):
        from patterns.library.state_space import (
            ControlMethod,
            StateSpaceConfig,
            StateSpacePattern,
            SystemType,
        )

        cfg = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.LQR,
            reference_type="sinusoid",
            simulation_steps=10,
        )
        pat = StateSpacePattern(cfg)
        ref = pat._get_reference(0.25)
        assert isinstance(ref, np.ndarray)

    def test_run(self, pattern):
        result = pattern.run()
        assert "control_method" in result
        assert "performance_metrics" in result
        assert "stability" in result

    def test_run_with_hypothesis(self, pattern):
        result = pattern.run({"dummy": True})
        assert "control_method" in result

    def test_compute_control_raises_when_uninitialized(self, pattern):
        from patterns.library.state_space import StateSpaceController

        ctrl = StateSpaceController(
            np.array([[0, 1], [0, 0]]), np.array([[0], [1]]), np.array([[1, 0]]), np.array([[0]])
        )
        with pytest.raises(RuntimeError, match="Controller gain not computed"):
            ctrl.compute_control(np.array([1.0, 0.0]))

    def test_discretize(self, pattern):
        pattern._initialize_controller()
        A_d, B_d = pattern.controller.discretize()
        assert A_d.shape == pattern.config.A.shape
        assert B_d.shape == pattern.config.B.shape

    def test_place_poles_uncontrollable(self):
        from patterns.library.state_space import StateSpaceController

        # Make B zero so system is uncontrollable
        ctrl = StateSpaceController(
            np.array([[0, 1], [0, 0]]), np.array([[0], [0]]), np.array([[1, 0]]), np.array([[0]])
        )
        K = ctrl.place_poles([0.5, 0.6])
        assert K is not None


# =============================================================================
# Continuum Mechanics
# =============================================================================


class TestContinuumMechanicsPublicAPI:
    @pytest.fixture
    def pattern(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(n_elements_x=2, n_elements_y=2, n_elements_z=1, n_steps=1)
        return ContinuumMechanics(cfg)

    def test_validate_config_good(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig()
        cm = ContinuumMechanics(cfg)
        assert cm.config == cfg

    def test_validate_config_bad_elements(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(n_elements_x=0)
        with pytest.raises(ValueError, match="n_elements"):
            ContinuumMechanics(cfg)

    def test_validate_config_bad_youngs(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(youngs_modulus=-1)
        with pytest.raises(ValueError, match="youngs_modulus"):
            ContinuumMechanics(cfg)

    def test_validate_config_bad_poisson(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(poisson_ratio=0.6)
        with pytest.raises(ValueError, match="poisson_ratio"):
            ContinuumMechanics(cfg)

    def test_validate_config_bad_model(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(material_model="unknown")
        with pytest.raises(ValueError, match="material_model"):
            ContinuumMechanics(cfg)

    def test_validate_config_bad_formulation(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(formulation="bad")
        with pytest.raises(ValueError, match="formulation"):
            ContinuumMechanics(cfg)

    def test_get_metadata(self):
        from patterns.library.continuum_mechanics import ContinuumMechanics

        meta = ContinuumMechanics.get_metadata()
        assert meta["pattern_id"] == "continuum_mechanics"

    def test_initialize_mesh(self, pattern):
        assert pattern.nodes is not None
        assert len(pattern.elements) > 0
        assert pattern.displacements is not None

    def test_apply_boundary_conditions(self, pattern):
        pattern._apply_boundary_conditions()
        assert len(pattern.fixed_dofs) > 0

    def test_compute_external_forces_gravity(self, pattern):
        f = pattern._compute_external_forces()
        assert len(f) > 0

    def test_compute_external_forces_compression(self):
        from patterns.library.continuum_mechanics import (
            ContinuumMechanics,
            ContinuumMechanicsConfig,
        )

        cfg = ContinuumMechanicsConfig(
            n_elements_x=2, n_elements_y=2, n_elements_z=1, n_steps=1, load_type="compression"
        )
        cm = ContinuumMechanics(cfg)
        f = cm._compute_external_forces()
        assert len(f) > 0

    def test_run(self, pattern):
        result = pattern.run()
        assert result["pattern_id"] == "continuum_mechanics"
        assert "displacements" in result
        assert "energy_history" in result

    def test_finite_element_volume(self):
        from patterns.library.continuum_mechanics import FiniteElement

        nodes = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )
        elem = FiniteElement(nodes, np.arange(8))
        assert elem.volume_ref > 0

    def test_finite_element_shape_functions(self):
        from patterns.library.continuum_mechanics import FiniteElement

        nodes = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )
        elem = FiniteElement(nodes, np.arange(8))
        N = elem.shape_functions(np.array([0.0, 0.0, 0.0]))
        assert len(N) == 8
        assert abs(np.sum(N) - 1.0) < 1e-10

    def test_finite_element_deformation_gradient(self):
        from patterns.library.continuum_mechanics import FiniteElement

        nodes = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )
        elem = FiniteElement(nodes, np.arange(8))
        disp = np.zeros((8, 3))
        F = elem.compute_deformation_gradient(disp, np.array([0.0, 0.0, 0.0]))
        np.testing.assert_array_almost_equal(F, np.eye(3))

    def test_finite_element_stress_linear(self):
        from patterns.library.continuum_mechanics import FiniteElement

        nodes = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )
        elem = FiniteElement(nodes, np.arange(8))
        disp = np.zeros((8, 3))
        F = elem.compute_deformation_gradient(disp, np.array([0.0, 0.0, 0.0]))
        S = elem.compute_stress_linear(F, 1e7, 0.3)
        assert S.shape == (3, 3)

    def test_finite_element_stress_neo_hookean(self):
        from patterns.library.continuum_mechanics import FiniteElement

        nodes = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=float,
        )
        elem = FiniteElement(nodes, np.arange(8))
        disp = np.zeros((8, 3))
        F = elem.compute_deformation_gradient(disp, np.array([0.0, 0.0, 0.0]))
        S = elem.compute_stress_neo_hookean(F, 1e7, 0.3)
        assert S.shape == (3, 3)


# =============================================================================
# Base
# =============================================================================


class TestBasePublicAPI:
    def test_base_config_defaults(self):
        from patterns.library.base import BaseConfig

        cfg = BaseConfig()
        assert cfg.name == "default"
        assert cfg.precision == "float64"

    def test_base_pattern_abstract(self):
        from patterns.library.base import BasePattern

        with pytest.raises(TypeError):
            BasePattern()

    def test_gpu_mixin_no_gpu(self):
        from patterns.library.base import GPUMixin

        mixin = GPUMixin()
        assert mixin.gpu_available is False
        arr = np.array([1, 2, 3])
        np.testing.assert_array_equal(mixin.to_gpu(arr), arr)
        np.testing.assert_array_equal(mixin.to_cpu(arr), arr)

    def test_gpu_mixin_parallel_raises(self):
        from patterns.library.base import GPUMixin

        mixin = GPUMixin()
        with pytest.raises(RuntimeError, match="GPU not available"):
            mixin.gpu_parallel(None, (1,), (1,))

    def test_vectorized_dot(self):
        from patterns.library.base import vectorized_dot

        a = np.array([[1, 0, 0]])
        b = np.array([[0, 1, 0]])
        assert vectorized_dot(a, b)[0] == 0

    def test_quaternion_multiply_identity(self):
        from patterns.library.base import quaternion_multiply

        q = np.array([1, 0, 0, 0])
        result = quaternion_multiply(q, q)
        np.testing.assert_array_almost_equal(result, [1, 0, 0, 0])

    def test_quaternion_rotate_vector_no_rotation(self):
        from patterns.library.base import quaternion_rotate_vector

        q = np.array([1, 0, 0, 0])
        v = np.array([1, 2, 3])
        result = quaternion_rotate_vector(q, v)
        np.testing.assert_array_almost_equal(result, [1, 2, 3])

    def test_rotation_matrix_from_quaternion_identity(self):
        from patterns.library.base import rotation_matrix_from_quaternion

        q = np.array([1, 0, 0, 0])
        R = rotation_matrix_from_quaternion(q)
        np.testing.assert_array_almost_equal(R, np.eye(3))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
