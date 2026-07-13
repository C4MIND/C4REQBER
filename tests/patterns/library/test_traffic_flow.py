"""
Tests for traffic_flow pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.traffic_flow import (
    BoundaryCondition,
    FundamentalDiagram,
    TrafficFlowConfig,
    TrafficFlowPattern,
    TrafficModel,
)


class TestEnums:
    def test_traffic_model_values(self):
        assert TrafficModel.LWR.value == "lwr"
        assert TrafficModel.CA.value == "cellular_automaton"
        assert TrafficModel.HYBRID.value == "hybrid"

    def test_fundamental_diagram_values(self):
        assert FundamentalDiagram.GREENSHELDS.value == "greenshields"
        assert FundamentalDiagram.GREENBERG.value == "greenberg"
        assert FundamentalDiagram.UNDERWOOD.value == "underwood"
        assert FundamentalDiagram.TRIANGULAR.value == "triangular"

    def test_boundary_condition_values(self):
        assert BoundaryCondition.PERIODIC.value == "periodic"
        assert BoundaryCondition.INFLOW_OUTFLOW.value == "inflow_outflow"
        assert BoundaryCondition.CLOSED.value == "closed"


class TestConfig:
    def test_default_config(self):
        cfg = TrafficFlowConfig()
        assert cfg.model == TrafficModel.LWR
        assert cfg.road_length == 10.0
        assert cfg.n_cells == 200
        assert cfg.free_flow_speed == 120.0

    def test_custom_config(self):
        cfg = TrafficFlowConfig(n_cells=50, simulation_time=300)
        assert cfg.n_cells == 50
        assert cfg.simulation_time == 300


class TestInit:
    def test_pattern_init_default(self):
        pattern = TrafficFlowPattern()
        assert pattern.config is not None
        assert pattern.density is not None

    def test_pattern_init_ca(self):
        cfg = TrafficFlowConfig(model=TrafficModel.CA, n_cells=20, n_lanes=1, road_length=0.1)
        pattern = TrafficFlowPattern(cfg)
        assert len(pattern.vehicles) > 0


class TestFundamentalDiagram:
    def test_greenshields_flux_nonnegative(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.LWR, fundamental_diagram=FundamentalDiagram.GREENSHELDS
        )
        pattern = TrafficFlowPattern(cfg)
        densities = np.linspace(0, cfg.jam_density, 50)
        Q, v = pattern._fundamental_diagram(densities)
        assert np.all(Q >= 0)
        assert np.all(v >= 0)

    def test_speed_not_exceed_free_flow(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.LWR, fundamental_diagram=FundamentalDiagram.GREENSHELDS
        )
        pattern = TrafficFlowPattern(cfg)
        densities = np.linspace(0, cfg.jam_density, 50)
        Q, v = pattern._fundamental_diagram(densities)
        assert np.all(v <= cfg.free_flow_speed)

    def test_triangular_piecewise(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.LWR, fundamental_diagram=FundamentalDiagram.TRIANGULAR
        )
        pattern = TrafficFlowPattern(cfg)
        densities = np.array([0, cfg.critical_density / 2, cfg.critical_density, cfg.jam_density])
        Q, v = pattern._fundamental_diagram(densities)
        assert np.all(np.isfinite(Q))


class TestBottleneck:
    def test_bottleneck_capacity(self):
        cfg = TrafficFlowConfig(has_bottleneck=True, bottleneck_capacity_factor=0.5)
        pattern = TrafficFlowPattern(cfg)
        cap = pattern._bottleneck_capacity(100)
        assert 0 <= cap <= 1.0

    def test_no_bottleneck(self):
        cfg = TrafficFlowConfig(has_bottleneck=False)
        pattern = TrafficFlowPattern(cfg)
        cap = pattern._bottleneck_capacity(100)
        assert cap == 1.0


class TestLWRStep:
    def test_lwr_step(self):
        cfg = TrafficFlowConfig(model=TrafficModel.LWR, n_cells=50)
        pattern = TrafficFlowPattern(cfg)
        density_before = pattern.density.copy()
        pattern._lwr_step()
        assert np.all(pattern.density >= 0)
        assert np.all(pattern.density <= cfg.jam_density)


class TestCAStep:
    def test_ca_step(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.CA, n_cells=20, simulation_time=30, n_lanes=1, road_length=0.1
        )
        pattern = TrafficFlowPattern(cfg)
        n_vehicles_before = len(pattern.vehicles)
        pattern._ca_step()
        assert len(pattern.vehicles) == n_vehicles_before


class TestTravelTime:
    def test_travel_time(self):
        cfg = TrafficFlowConfig(model=TrafficModel.LWR, n_cells=50)
        pattern = TrafficFlowPattern(cfg)
        tt = pattern._compute_travel_time()
        assert isinstance(tt, float)
        assert tt > 0


class TestRun:
    def test_run_lwr(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.LWR, n_cells=50, simulation_time=60, output_interval=10
        )
        pattern = TrafficFlowPattern(cfg)
        result = pattern.run()
        assert result["model"] == "lwr"
        assert "average_density" in result

    def test_run_ca(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.CA,
            n_cells=20,
            simulation_time=30,
            output_interval=10,
            n_lanes=1,
            road_length=0.1,
        )
        pattern = TrafficFlowPattern(cfg)
        result = pattern.run()
        assert result["model"] == "cellular_automaton"
        assert "n_vehicles" in result

    def test_run_hybrid(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.HYBRID,
            n_cells=20,
            simulation_time=30,
            output_interval=10,
            n_lanes=1,
            road_length=0.1,
        )
        pattern = TrafficFlowPattern(cfg)
        result = pattern.run()
        assert result["model"] == "hybrid"

    def test_run_with_bottleneck(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.LWR,
            n_cells=20,
            simulation_time=30,
            has_bottleneck=True,
            bottleneck_capacity_factor=0.5,
        )
        pattern = TrafficFlowPattern(cfg)
        result = pattern.run()
        assert "bottleneck" in result

    def test_metadata(self):
        meta = TrafficFlowPattern.get_metadata()
        assert meta["id"] == "traffic_flow"
        assert "parameters" in meta


class TestEdgeCases:
    def test_zero_density(self):
        cfg = TrafficFlowConfig(model=TrafficModel.LWR, n_cells=20)
        pattern = TrafficFlowPattern(cfg)
        pattern.density[:] = 0
        Q, v = pattern._fundamental_diagram(pattern.density)
        assert np.all(Q == 0)

    def test_jam_density(self):
        cfg = TrafficFlowConfig(model=TrafficModel.LWR, n_cells=20)
        pattern = TrafficFlowPattern(cfg)
        pattern.density[:] = cfg.jam_density
        Q, v = pattern._fundamental_diagram(pattern.density)
        assert np.all(v == 0)

    def test_closed_boundary(self):
        cfg = TrafficFlowConfig(
            model=TrafficModel.CA,
            bc_type=BoundaryCondition.CLOSED,
            n_cells=20,
            simulation_time=30,
            n_lanes=1,
            road_length=0.1,
        )
        pattern = TrafficFlowPattern(cfg)
        result = pattern.run()
        assert result["n_vehicles"] > 0
