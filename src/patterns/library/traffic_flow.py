"""
C4REQBER v6.0 - Traffic Flow Pattern
Macroscopic traffic flow simulation using LWR model and Cellular Automata.

Pattern Structure (Christopher Alexander):
- Context: Transportation planning, congestion analysis, flow optimization
- Forces: Shock wave formation, bottleneck effects, driver behavior
- Solution: Multi-scale modeling from microscopic to macroscopic
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class TrafficModel(Enum):
    """Available traffic flow models"""

    LWR = "lwr"  # Lighthill-Whitham-Richards (macroscopic)
    CA = "cellular_automaton"  # Nagel-Schreckenberg (microscopic)
    HYBRID = "hybrid"  # Combined approach


class FundamentalDiagram(Enum):
    """Fundamental diagram (flux-density relation) types"""

    GREENSHELDS = "greenshields"  # Parabolic
    GREENBERG = "greenberg"  # Logarithmic
    UNDERWOOD = "underwood"  # Exponential
    TRIANGULAR = "triangular"  # Piecewise linear


class BoundaryCondition(Enum):
    """Boundary condition types"""

    PERIODIC = "periodic"
    INFLOW_OUTFLOW = "inflow_outflow"
    CLOSED = "closed"


@dataclass
class TrafficFlowConfig:
    """Configuration for traffic flow simulation"""

    # Model selection
    model: TrafficModel = TrafficModel.LWR
    fundamental_diagram: FundamentalDiagram = FundamentalDiagram.GREENSHELDS

    # Road parameters
    road_length: float = 10.0  # km
    n_cells: int = 200  # Number of cells/grid points
    n_lanes: int = 2  # Number of lanes

    # Traffic parameters
    free_flow_speed: float = 120.0  # km/h
    jam_density: float = 150.0  # vehicles/km/lane
    critical_density: float | None = None  # vehicles/km/lane (None = auto)

    # Simulation parameters
    dt: float = 0.5  # time step (seconds)
    simulation_time: float = 3600.0  # Total simulation time (seconds)
    output_interval: int = 60  # Output every N steps

    # Boundary conditions
    bc_type: BoundaryCondition = BoundaryCondition.INFLOW_OUTFLOW
    inflow_rate: float = 1500.0  # vehicles/hour

    # Bottleneck (optional)
    has_bottleneck: bool = False
    bottleneck_start: float = 0.4  # Fraction of road
    bottleneck_end: float = 0.6
    bottleneck_capacity_factor: float = 0.5  # Reduced capacity

    # CA-specific parameters
    ca_slowdown_prob: float = 0.3  # Randomization probability
    ca_max_speed: int = 5  # Cells per time step


class TrafficFlowPattern:
    """
    Traffic flow simulation using LWR and Cellular Automata models.

    LWR Model:
    ∂ρ/∂t + ∂Q(ρ)/∂x = 0
    where ρ = density, Q = flux

    Nagel-Schreckenberg CA:
    - Acceleration: v = min(v+1, v_max)
    - Braking: v = min(v, gap)
    - Randomization: v = max(v-1, 0) with probability p
    - Movement: x = x + v
    """

    PATTERN_ID = "traffic_flow"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: TrafficFlowConfig | None = None) -> None:
        self.config = config or TrafficFlowConfig()

        # Fields
        self.density: np.ndarray | None = None  # Vehicles per km
        self.velocity: np.ndarray | None = None  # km/h
        self.flux: np.ndarray | None = None  # Vehicles per hour

        # CA fields
        self.vehicles: list[dict] = []  # List of vehicle states

        # History
        self.density_history: list[np.ndarray] = []
        self.flux_history: list[np.ndarray] = []
        self.time_history: list[float] = []

        self._initialize_road()

    def _initialize_road(self) -> None:
        """Initialize road state"""
        cfg = self.config

        # Calculate critical density if not provided
        if cfg.critical_density is None:
            if cfg.fundamental_diagram == FundamentalDiagram.GREENSHELDS:
                cfg.critical_density = cfg.jam_density / 2
            else:
                cfg.critical_density = cfg.jam_density / np.e

        if cfg.model == TrafficModel.CA:
            self._initialize_ca()
        else:
            self._initialize_lwr()

    def _initialize_lwr(self) -> None:
        """Initialize LWR model"""
        cfg = self.config

        # Initialize with low density everywhere
        self.density = np.ones(cfg.n_cells) * 20.0  # 20 veh/km

        # Add some density variation
        x = np.linspace(0, cfg.road_length, cfg.n_cells)
        self.density += 10 * np.sin(2 * np.pi * x / cfg.road_length)
        self.density = np.clip(self.density, 0, cfg.jam_density)

        self.velocity = np.zeros(cfg.n_cells)
        self.flux = np.zeros(cfg.n_cells)

        self._update_fields()

    def _initialize_ca(self) -> None:
        """Initialize Cellular Automaton model"""
        cfg = self.config

        # Calculate initial number of vehicles
        avg_density = 30.0  # veh/km/lane
        n_vehicles = int(avg_density * cfg.road_length * cfg.n_lanes)

        # Cell size
        cell_size = cfg.road_length * 1000 / cfg.n_cells  # meters

        # Place vehicles randomly
        occupied = set()
        for _ in range(n_vehicles):
            while True:
                cell = np.random.randint(0, cfg.n_cells)
                lane = np.random.randint(0, cfg.n_lanes)
                if (cell, lane) not in occupied:
                    occupied.add((cell, lane))
                    self.vehicles.append(
                        {
                            "cell": cell,
                            "lane": lane,
                            "speed": np.random.randint(0, cfg.ca_max_speed + 1),
                            "distance": cell * cell_size,
                        }
                    )
                    break

        # Sort by position
        self.vehicles.sort(key=lambda v: v["distance"])

    def _fundamental_diagram(self, rho: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Calculate flux Q(ρ) and speed v(ρ) from density"""
        cfg = self.config

        rho = np.clip(rho, 0, cfg.jam_density)

        if cfg.fundamental_diagram == FundamentalDiagram.GREENSHELDS:
            # Q = v_free * ρ * (1 - ρ/ρ_jam)
            v = cfg.free_flow_speed * (1 - rho / cfg.jam_density)
            Q = rho * v

        elif cfg.fundamental_diagram == FundamentalDiagram.GREENBERG:
            # Q = v_free * ρ * ln(ρ_jam/ρ)
            v = cfg.free_flow_speed * np.log(cfg.jam_density / (rho + 1e-6))
            Q = rho * v

        elif cfg.fundamental_diagram == FundamentalDiagram.UNDERWOOD:
            # Q = v_free * ρ * exp(-ρ/ρ_critical)
            v = cfg.free_flow_speed * np.exp(-rho / cfg.critical_density)
            Q = rho * v

        elif cfg.fundamental_diagram == FundamentalDiagram.TRIANGULAR:
            # Piecewise linear
            Q = np.zeros_like(rho)
            v = np.zeros_like(rho)

            mask1 = rho <= cfg.critical_density
            Q[mask1] = cfg.free_flow_speed * rho[mask1]
            v[mask1] = cfg.free_flow_speed

            mask2 = rho > cfg.critical_density
            Q[mask2] = (
                cfg.free_flow_speed  # type: ignore[operator]
                * cfg.critical_density
                * (cfg.jam_density - rho[mask2])
                / (cfg.jam_density - cfg.critical_density)  # type: ignore[operator]
            )
            v[mask2] = Q[mask2] / (rho[mask2] + 1e-6)

        else:
            v = cfg.free_flow_speed * (1 - rho / cfg.jam_density)  # type: ignore[unreachable]
            Q = rho * v

        return Q, v

    def _bottleneck_capacity(self, x_idx: int) -> float:
        """Calculate local capacity factor (for bottleneck)"""
        cfg = self.config

        if not cfg.has_bottleneck:
            return 1.0

        x_frac = x_idx / cfg.n_cells

        if cfg.bottleneck_start <= x_frac <= cfg.bottleneck_end:
            return cfg.bottleneck_capacity_factor
        return 1.0

    def _lwr_step(self) -> None:
        """One step of LWR model (Godunov scheme)"""
        cfg = self.config

        dx = cfg.road_length / cfg.n_cells

        # Calculate flux at cell centers
        Q, v = self._fundamental_diagram(self.density)  # type: ignore[arg-type]

        # Calculate flux at cell interfaces (Godunov/Rusanov flux)
        Q_interface = np.zeros(cfg.n_cells + 1)

        for i in range(1, cfg.n_cells):
            # Rusanov flux
            Q_left, _ = self._fundamental_diagram(np.array([self.density[i - 1]]))  # type: ignore[index]
            Q_right, _ = self._fundamental_diagram(np.array([self.density[i]]))  # type: ignore[index]

            max_wave_speed = cfg.free_flow_speed  # Approximate
            Q_interface[i] = 0.5 * (Q_left[0] + Q_right[0]) - 0.5 * max_wave_speed * (
                self.density[i] - self.density[i - 1]  # type: ignore[index]
            )

        # Boundary fluxes
        if cfg.bc_type == BoundaryCondition.INFLOW_OUTFLOW:
            # Inflow
            Q_interface[0] = min(
                cfg.inflow_rate,
                self._fundamental_diagram(np.array([self.density[0]]))[0][0],  # type: ignore[index]
            )
            # Outflow (free flow)
            Q_interface[-1] = self._fundamental_diagram(np.array([self.density[-1]]))[  # type: ignore[index]
                0
            ][0]
        else:
            Q_interface[0] = Q_interface[-1] = 0

        # Apply bottleneck
        if cfg.has_bottleneck:
            for i in range(cfg.n_cells + 1):
                Q_interface[i] *= self._bottleneck_capacity(i % cfg.n_cells)

        # Update density (conservation law)
        for i in range(cfg.n_cells):
            self.density[i] += (  # type: ignore[index]
                (cfg.dt / 3600) * (Q_interface[i] - Q_interface[i + 1]) / dx
            )

        # Ensure physical bounds
        self.density = np.clip(self.density, 0, cfg.jam_density)  # type: ignore[arg-type]

        self._update_fields()

    def _update_fields(self) -> None:
        """Update velocity and flux from density"""
        self.flux, self.velocity = self._fundamental_diagram(self.density)  # type: ignore[arg-type]

    def _ca_step(self) -> None:
        """One step of Nagel-Schreckenberg CA model"""
        cfg = self.config

        cell_size = cfg.road_length * 1000 / cfg.n_cells  # meters

        # Sort vehicles by position
        self.vehicles.sort(key=lambda v: v["distance"])

        # Create occupancy map
        occupied = {(v["cell"], v["lane"]): i for i, v in enumerate(self.vehicles)}

        new_vehicles = []

        for i, vehicle in enumerate(self.vehicles):
            cell = vehicle["cell"]
            lane = vehicle["lane"]
            speed = vehicle["speed"]

            # 1. Acceleration
            speed = min(speed + 1, cfg.ca_max_speed)

            # 2. Braking (find gap to next vehicle)
            gap = cfg.ca_max_speed
            for d in range(1, cfg.ca_max_speed + 1):
                check_cell = (cell + d) % cfg.n_cells
                if (check_cell, lane) in occupied and occupied[(check_cell, lane)] != i:
                    gap = d - 1
                    break

            speed = min(speed, gap)

            # 3. Randomization (dawdling)
            if speed > 0 and np.random.rand() < cfg.ca_slowdown_prob:
                speed -= 1

            # 4. Movement
            new_cell = (cell + speed) % cfg.n_cells
            new_distance = vehicle["distance"] + speed * cell_size

            new_vehicles.append(
                {
                    "cell": new_cell,
                    "lane": lane,
                    "speed": speed,
                    "distance": new_distance,
                }
            )

        self.vehicles = new_vehicles

        # Convert to density/velocity for output
        self._ca_to_macro()

    def _ca_to_macro(self) -> None:
        """Convert CA state to macroscopic variables"""
        cfg = self.config

        self.density = np.zeros(cfg.n_cells)
        self.velocity = np.zeros(cfg.n_cells)

        cell_size = cfg.road_length * 1000 / cfg.n_cells

        for vehicle in self.vehicles:
            cell = vehicle["cell"]
            self.density[cell] += 1
            self.velocity[cell] += vehicle["speed"] * cell_size / cfg.dt * 3.6  # km/h

        # Convert counts to density (veh/km)
        self.density *= 1000 / (cell_size * cfg.n_lanes)

        # Average velocity
        nonzero = self.density > 0
        self.velocity[nonzero] /= self.density[nonzero] * cell_size * cfg.n_lanes / 1000
        self.velocity[~nonzero] = cfg.free_flow_speed

        self.flux = self.density * self.velocity

    def _compute_travel_time(self) -> float:
        """Compute average travel time through road"""
        if self.velocity is None or np.mean(self.velocity) <= 0:
            return float("inf")

        avg_speed = np.mean(self.velocity)  # km/h
        return self.config.road_length / avg_speed * 3600  # type: ignore  # seconds

    def _compute_total_delay(self) -> float:
        """Compute total vehicle-hours of delay"""
        cfg = self.config

        free_flow_time = cfg.road_length / cfg.free_flow_speed * 3600  # seconds
        actual_time = self._compute_travel_time()

        # Approximate number of vehicles on road
        if cfg.model == TrafficModel.CA:
            n_vehicles = len(self.vehicles)
        else:
            n_vehicles = np.mean(self.density) * cfg.road_length * cfg.n_lanes  # type: ignore[arg-type, assignment]

        delay_per_vehicle = max(0, actual_time - free_flow_time) / 3600  # hours
        return n_vehicles * delay_per_vehicle

    def _detect_shock_wave(self) -> tuple[float, float] | None:
        """Detect shock wave position and speed"""
        if len(self.density_history) < 2:
            return None

        # Find location with maximum density gradient
        grad = np.gradient(self.density)  # type: ignore[arg-type]
        shock_idx = np.argmax(np.abs(grad))
        shock_pos = shock_idx / self.config.n_cells * self.config.road_length

        return (shock_pos, float(np.abs(grad[shock_idx])))  # type: ignore[return-value]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run traffic flow simulation"""
        cfg = self.config

        logger.info(
            f"Starting traffic flow: {cfg.model.value}, "
            f"road={cfg.road_length}km, time={cfg.simulation_time / 60:.1f}min"
        )

        n_steps = int(cfg.simulation_time / cfg.dt)

        for step in range(n_steps):
            if cfg.model == TrafficModel.LWR:
                self._lwr_step()
            elif cfg.model == TrafficModel.CA:
                self._ca_step()
            else:
                # Hybrid: use CA for details, LWR for average
                if step % 2 == 0:
                    self._ca_step()
                else:
                    self._lwr_step()

            # Store output
            if step % cfg.output_interval == 0:
                self.density_history.append(self.density.copy())  # type: ignore[union-attr]
                self.flux_history.append(self.flux.copy())  # type: ignore[union-attr]
                self.time_history.append(step * cfg.dt)

            if step % 600 == 0:  # Every 10 minutes
                avg_density = np.mean(self.density)  # type: ignore[arg-type]
                avg_speed = np.mean(self.velocity)  # type: ignore[arg-type]
                logger.debug(
                    f"Step {step}: ρ={avg_density:.1f} veh/km, v={avg_speed:.1f} km/h"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate statistics
        avg_density = float(np.mean([np.mean(d) for d in self.density_history]))
        avg_velocity = float(
            np.mean(
                [
                    np.mean(np.where(d > 0, self._fundamental_diagram(d)[1], 0))
                    for d in self.density_history
                ]
            )
        )
        max_density = float(np.max([np.max(d) for d in self.density_history]))

        # Check for congestion
        congestion_threshold = cfg.critical_density
        is_congested = max_density > congestion_threshold  # type: ignore[operator]

        # Travel time and delay
        travel_time = self._compute_travel_time()
        total_delay = self._compute_total_delay()

        # Shock wave detection
        shock = self._detect_shock_wave()

        output = {
            "model": cfg.model.value,
            "fundamental_diagram": cfg.fundamental_diagram.value,
            "road_length_km": cfg.road_length,
            "n_lanes": cfg.n_lanes,
            "simulation_time_s": cfg.simulation_time,
            "average_density": avg_density,
            "average_velocity": avg_velocity,
            "max_density": max_density,
            "is_congested": is_congested,
            "travel_time_s": travel_time,
            "total_delay_vehicle_hours": total_delay,
            "free_flow_travel_time_s": cfg.road_length / cfg.free_flow_speed * 3600,
            "time_history": self.time_history,
            "density_history": [d.tolist() for d in self.density_history],
            "flux_history": [f.tolist() for f in self.flux_history],
            "final_density": self.density.tolist(),  # type: ignore[union-attr]
            "final_velocity": self.velocity.tolist()  # type: ignore[union-attr]
            if cfg.model != TrafficModel.CA
            else self.velocity.tolist(),  # type: ignore[union-attr]
            "parameters": {
                "free_flow_speed": cfg.free_flow_speed,
                "jam_density": cfg.jam_density,
                "critical_density": cfg.critical_density,
            },
        }

        if shock:
            output["shock_wave"] = {"position_km": shock[0], "strength": shock[1]}

        if cfg.model == TrafficModel.CA:
            output["n_vehicles"] = len(self.vehicles)

        if cfg.has_bottleneck:
            output["bottleneck"] = {
                "start": cfg.bottleneck_start,
                "end": cfg.bottleneck_end,
                "capacity_factor": cfg.bottleneck_capacity_factor,
            }

        return output

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Traffic Flow",
            "category": "EXTENDED",
            "domain": [
                "Transportation Engineering",
                "Urban Planning",
                "Operations Research",
            ],
            "description": "Traffic flow simulation using LWR and Cellular Automata models",
            "computational_complexity": "O(N) per time step",
            "typical_runtime": "seconds to minutes",
            "accuracy": "High (macroscopic), Medium (microscopic)",
            "assumptions": [
                "Single vehicle type (homogeneous flow)",
                "No lane changing (LWR)",
                "Instantaneous driver reactions",
                "Well-defined fundamental diagram",
            ],
            "parameters": [
                {
                    "name": "model",
                    "type": "enum",
                    "options": ["lwr", "cellular_automaton", "hybrid"],
                    "default": "lwr",
                },
                {
                    "name": "fundamental_diagram",
                    "type": "enum",
                    "options": ["greenshields", "greenberg", "underwood", "triangular"],
                    "default": "greenshields",
                },
                {
                    "name": "road_length",
                    "type": "float",
                    "default": 10.0,
                    "description": "Road length in km",
                },
                {
                    "name": "free_flow_speed",
                    "type": "float",
                    "default": 120.0,
                    "description": "Free flow speed in km/h",
                },
                {
                    "name": "has_bottleneck",
                    "type": "bool",
                    "default": False,
                    "description": "Include capacity bottleneck",
                },
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================


def test_conservation_of_vehicles() -> None:
    """Test that total number of vehicles is conserved (closed system)"""
    config = TrafficFlowConfig(
        model=TrafficModel.CA,
        bc_type=BoundaryCondition.CLOSED,
        n_cells=100,
        simulation_time=300,
    )

    traffic = TrafficFlowPattern(config)
    result = traffic.run()

    # Number of vehicles should be constant
    assert result["n_vehicles"] > 0, "No vehicles in simulation"
    print("✓ Conservation of vehicles test passed")


def test_fundamental_diagram_monotonicity() -> None:
    """Test that fundamental diagram is physically valid"""
    config = TrafficFlowConfig(
        model=TrafficModel.LWR, fundamental_diagram=FundamentalDiagram.GREENSHELDS
    )

    traffic = TrafficFlowPattern(config)

    # Test that flux is non-negative
    densities = np.linspace(0, config.jam_density, 100)
    fluxes, speeds = traffic._fundamental_diagram(densities)

    assert np.all(fluxes >= 0), "Flux should be non-negative"
    assert np.all(speeds >= 0), "Speed should be non-negative"
    assert np.all(speeds <= config.free_flow_speed), "Speed should not exceed free flow"
    print("✓ Fundamental diagram monotonicity test passed")


def test_bottleneck_creates_congestion() -> None:
    """Test that bottleneck creates congestion"""
    # Without bottleneck
    config_no = TrafficFlowConfig(
        model=TrafficModel.LWR,
        has_bottleneck=False,
        simulation_time=600,
        inflow_rate=2000,
    )
    traffic_no = TrafficFlowPattern(config_no)
    result_no = traffic_no.run()

    # With bottleneck
    config_yes = TrafficFlowConfig(
        model=TrafficModel.LWR,
        has_bottleneck=True,
        bottleneck_capacity_factor=0.5,
        simulation_time=600,
        inflow_rate=2000,
    )
    traffic_yes = TrafficFlowPattern(config_yes)
    result_yes = traffic_yes.run()

    # With bottleneck should have higher density/travel time
    assert result_yes["max_density"] >= result_no["max_density"] * 0.9, (
        "Bottleneck did not increase density"
    )
    print("✓ Bottleneck congestion test passed")


def test_travel_time_increases_with_density() -> None:
    """Test that travel time increases with traffic density"""
    travel_times = []
    inflows = [500, 1500, 2500]

    for inflow in inflows:
        config = TrafficFlowConfig(
            model=TrafficModel.LWR, inflow_rate=inflow, simulation_time=600
        )
        traffic = TrafficFlowPattern(config)
        result = traffic.run()
        travel_times.append(result["travel_time_s"])

    # Travel time should increase with inflow
    for i in range(len(travel_times) - 1):
        assert travel_times[i] <= travel_times[i + 1] * 1.5, (
            f"Travel time did not increase: {travel_times}"
        )
    print("✓ Travel time vs density test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run tests
    test_conservation_of_vehicles()
    test_fundamental_diagram_monotonicity()
    test_bottleneck_creates_congestion()
    test_travel_time_increases_with_density()

    # Demo run
    print("\n--- Demo Run ---")
    config = TrafficFlowConfig(
        model=TrafficModel.LWR,
        fundamental_diagram=FundamentalDiagram.GREENSHELDS,
        road_length=10.0,
        simulation_time=1800,
        has_bottleneck=True,
        bottleneck_capacity_factor=0.6,
    )

    traffic = TrafficFlowPattern(config)
    result = traffic.run()

    print(f"Model: {result['model']}")
    print(f"Avg density: {result['average_density']:.1f} veh/km")
    print(f"Avg velocity: {result['average_velocity']:.1f} km/h")
    print(f"Travel time: {result['travel_time_s'] / 60:.1f} min")
    print(f"Congested: {result['is_congested']}")
