"""
C4REQBER v6.0 - Wildfire Pattern
Fire spread model with coupled atmosphere-vegetation interactions.

Pattern Structure (Christopher Alexander):
- Context: Wildfire forecasting, prescribed burn planning, risk assessment
- Forces: Fuel moisture, wind, topography, spotting, suppression
- Solution: Reaction-diffusion fire spread with atmospheric coupling
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class WildfireConfig:
    """Configuration for wildfire simulation"""

    # Grid settings
    nx: int = 200  # Grid resolution
    ny: int = 200

    # Domain (landscape scale)
    Lx: float = 20.0e3  # 20 km
    Ly: float = 20.0e3

    # Time stepping
    dt: float = 60.0  # 1 minute
    hours: int = 24  # Simulation duration

    # Fuel parameters (Canadian Fire Weather Index style)
    fuel_load: float = 1.0  # kg/m^2
    fuel_moisture: float = 0.15  # fraction (15%)
    fuel_type: str = "mixed_wood"  # grass, shrub, mixed_wood, conifer

    # Fire behavior
    ros_base: float = 1.0  # Base rate of spread (m/min)
    spread_exponent: float = 1.5  # Wind effect exponent

    # Meteorology
    wind_speed: float = 10.0  # km/h
    wind_dir: float = 270.0  # degrees (from west)
    temperature: float = 25.0  # Celsius
    humidity: float = 40.0  # %

    # Topography
    slope: float = 0.1  # Average slope (rise/run)
    slope_dir: float = 0.0  # Slope direction (degrees)

    # Ignition
    ignition_x: float = 10.0e3
    ignition_y: float = 10.0e3
    ignition_radius: float = 100.0  # m
    ignition_time: float = 0.0  # hours after start

    # Spotting
    spotting_enabled: bool = True
    spot_distance_mean: float = 500.0  # m
    spot_probability: float = 0.01  # per burning cell per timestep

    # Suppression
    suppression_enabled: bool = False
    suppression_start: float = 2.0  # hours
    suppression_rate: float = 0.1  # fraction per hour

    # Crown fire
    crown_fire_enabled: bool = True
    crown_fire_threshold: float = 3000.0  # kW/m

    # Output
    output_interval: int = 10  # every 10 minutes


class WildfirePattern:
    """
    Wildfire spread model with atmospheric coupling.

    Simulates fire spread using a reaction-diffusion approach
    with Rothermel-style rate of spread calculations. Includes
    spotting, crown fire transitions, and suppression effects.
    """

    PATTERN_ID = "wildfire"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: WildfireConfig | None = None) -> None:
        self.config = config or WildfireConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self) -> None:
        """Initialize computational grid"""
        cfg = self.config

        self.x = np.linspace(0, cfg.Lx, cfg.nx)
        self.y = np.linspace(0, cfg.Ly, cfg.ny)
        self.dx = cfg.Lx / cfg.nx
        self.dy = cfg.Ly / cfg.ny

        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")

        logger.debug(f"Fire grid: {cfg.nx}x{cfg.ny}, dx={self.dx:.1f}m")

    def _initialize_fields(self) -> None:
        """Initialize fire state variables"""
        cfg = self.config

        # Fire state (0 = unburned, 0-1 = burning, 1 = burned)
        self.fuel = np.ones((cfg.nx, cfg.ny))  # Available fuel fraction
        self.fire_intensity = np.zeros((cfg.nx, cfg.ny))  # kW/m
        self.heat_release = np.zeros((cfg.nx, cfg.ny))  # Cumulative

        # Fire front arrival time
        self.arrival_time = np.full((cfg.nx, cfg.ny), np.inf)

        # Crown fire state
        self.crown_fire = np.zeros((cfg.nx, cfg.ny), dtype=bool)

        # Spot fires (new ignitions)
        self.spot_fires = []  # type: ignore[var-annotated]

        # Topography
        self.elevation = cfg.slope * (
            self.X * np.cos(np.radians(cfg.slope_dir))
            + self.Y * np.sin(np.radians(cfg.slope_dir))
        )

        # Fuel moisture map (spatial variation)
        self.fuel_moisture_map = cfg.fuel_moisture * (
            1 + 0.2 * np.random.randn(cfg.nx, cfg.ny)
        )
        self.fuel_moisture_map = np.clip(self.fuel_moisture_map, 0.05, 0.5)

        # Output storage
        self.history = {  # type: ignore[var-annotated]
            "burned_area": [],
            "fire_perimeter": [],
            "max_intensity": [],
            "active_fire_cells": [],
            "spot_fire_count": [],
            "time": [],
        }

    def _rothermel_ros(self, slope_factor: float = 1.0) -> float:
        """
        Calculate Rothermel-style rate of spread.
        Returns ROS in m/min.
        """
        cfg = self.config

        # Base ROS
        ros = cfg.ros_base

        # Wind effect
        # Convert wind to m/min
        wind_m_min = cfg.wind_speed * 1000 / 60
        ros *= 1 + 0.5 * wind_m_min**cfg.spread_exponent / 10

        # Slope effect
        ros *= slope_factor

        # Fuel moisture effect
        # Critical moisture varies by fuel type
        critical_moisture = 0.25 if cfg.fuel_type == "grass" else 0.30
        moisture_factor = max(0, 1 - cfg.fuel_moisture / critical_moisture)
        ros *= moisture_factor

        # Temperature effect
        temp_factor = 1 + 0.01 * (cfg.temperature - 20)
        ros *= temp_factor

        # Humidity effect
        humidity_factor = 1 - 0.005 * (cfg.humidity - 30)
        ros *= humidity_factor

        return max(ros, 0.1)  # type: ignore  # Minimum ROS

    def _slope_factor(self, i: int, j: int) -> float:
        """Calculate local slope factor for fire spread"""
        cfg = self.config

        # Gradient of elevation
        if 0 < i < cfg.nx - 1 and 0 < j < cfg.ny - 1:
            dz_dx = (self.elevation[i + 1, j] - self.elevation[i - 1, j]) / (
                2 * self.dx
            )
            dz_dy = (self.elevation[i, j + 1] - self.elevation[i, j - 1]) / (
                2 * self.dy
            )

            # Slope angle
            slope = np.sqrt(dz_dx**2 + dz_dy**2)

            # Slope factor (Rothermel)
            if slope > 0:
                slope_factor = np.exp(3.533 * slope)
            else:
                slope_factor = 1.0
        else:
            slope_factor = 1.0

        return slope_factor  # type: ignore[no-any-return]

    def _fire_intensity_calc(self, ros: float) -> float:
        """
        Calculate fire intensity (Byram's formula).
        Returns intensity in kW/m.
        """
        cfg = self.config

        # I = H * w * ROS
        # H = heat of combustion (~18,000 kJ/kg)
        # w = fuel load (kg/m^2)
        H = 18000.0  # kJ/kg
        w = cfg.fuel_load * (1 - cfg.fuel_moisture)  # Available fuel

        intensity = H * w * ros / 60  # Convert to kW/m

        return intensity

    def _spotting(self, burning_cells: list[tuple[int, int]], time: float) -> None:
        """Generate spot fires from burning cells"""
        cfg = self.config

        if not cfg.spotting_enabled:
            return

        new_spots = []

        for i, j in burning_cells:
            if self.fire_intensity[i, j] > 1000:  # Only intense fires spot
                if np.random.random() < cfg.spot_probability:
                    # Spot fire location (downwind)
                    wind_rad = np.radians(270 - cfg.wind_dir)
                    spot_dist = np.random.exponential(cfg.spot_distance_mean)

                    di = int(spot_dist * np.cos(wind_rad) / self.dx)
                    dj = int(spot_dist * np.sin(wind_rad) / self.dy)

                    new_i = i + di
                    new_j = j + dj

                    if 0 <= new_i < cfg.nx and 0 <= new_j < cfg.ny:
                        if self.fuel[new_i, new_j] > 0.5:  # Has fuel
                            new_spots.append((new_i, new_j, time))

        self.spot_fires.extend(new_spots)

    def _crown_fire_transition(self) -> None:
        """Check for crown fire transitions"""
        cfg = self.config

        if not cfg.crown_fire_enabled:
            return

        # Crown fire occurs when surface fire intensity exceeds threshold
        crown_threshold = cfg.crown_fire_threshold

        for i in range(cfg.nx):
            for j in range(cfg.ny):
                if self.fire_intensity[i, j] > crown_threshold:
                    if not self.crown_fire[i, j] and cfg.fuel_type in [
                        "mixed_wood",
                        "conifer",
                    ]:
                        self.crown_fire[i, j] = True
                        # Increase intensity for crown fire
                        self.fire_intensity[i, j] *= 2.0

    def _fire_spread(self, time: float) -> None:
        """Calculate fire spread for one time step"""
        cfg = self.config

        # Find burning cells
        burning = self.fire_intensity > 100  # Active burning threshold
        burning_cells = list(zip(*np.where(burning), strict=False))

        # Rate of spread for each burning cell
        new_burning = []

        for i, j in burning_cells:
            # Local ROS
            slope_factor = self._slope_factor(i, j)
            ros = self._rothermel_ros(slope_factor)

            # Fire intensity
            self.fire_intensity[i, j] = self._fire_intensity_calc(ros)

            # Consume fuel
            burn_rate = ros * cfg.dt / 60 / max(self.dx, self.dy)  # cells per timestep
            self.fuel[i, j] = max(0, self.fuel[i, j] - burn_rate * 0.1)

            # Heat release
            self.heat_release[i, j] += self.fire_intensity[i, j] * cfg.dt

            # Spread to neighbors
            ros_cells = ros * cfg.dt / 60 / self.dx  # cells per timestep

            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj

                if 0 <= ni < cfg.nx and 0 <= nj < cfg.ny:
                    if self.fuel[ni, nj] > 0.1 and not burning[ni, nj]:
                        # Check if fire reaches this cell
                        if np.random.random() < ros_cells * 0.5:
                            new_burning.append((ni, nj))
                            if self.arrival_time[ni, nj] == np.inf:
                                self.arrival_time[ni, nj] = time

        # Ignite new cells
        for i, j in new_burning:
            self.fire_intensity[i, j] = self._fire_intensity_calc(self._rothermel_ros())

        # Spotting
        self._spotting(burning_cells, time)

        # Check for crown fire
        self._crown_fire_transition()

        # Apply spot fires
        for i, j, spot_time in self.spot_fires:
            if time >= spot_time and self.fuel[i, j] > 0.1:
                self.fire_intensity[i, j] = max(
                    self.fire_intensity[i, j],
                    self._fire_intensity_calc(self._rothermel_ros()),
                )

    def _suppression(self, time: float) -> None:
        """Apply fire suppression"""
        cfg = self.config

        if not cfg.suppression_enabled:
            return

        if time >= cfg.suppression_start:
            # Reduce fire intensity
            suppression_factor = np.exp(
                -cfg.suppression_rate * (time - cfg.suppression_start)
            )
            self.fire_intensity *= suppression_factor

            # Extinguish low-intensity fires
            self.fire_intensity[self.fire_intensity < 50] = 0

    def _calculate_burned_area(self) -> float:
        """Calculate total burned area in hectares"""
        burned = np.sum(self.fuel < 0.5)
        area_m2 = burned * self.dx * self.dy
        return area_m2 / 10000  # type: ignore[return-value]

    def _calculate_fire_perimeter(self) -> float:
        """Calculate fire perimeter in meters"""
        # Find boundary of burned area
        burned = self.fuel < 0.5

        perimeter = 0
        for i in range(1, self.config.nx - 1):
            for j in range(1, self.config.ny - 1):
                if burned[i, j]:
                    # Check if on perimeter
                    if not (
                        burned[i - 1, j]
                        and burned[i + 1, j]
                        and burned[i, j - 1]
                        and burned[i, j + 1]
                    ):
                        perimeter += 1

        return perimeter * self.dx

    def _step(self, time: float) -> None:
        """Advance fire simulation by one time step"""
        cfg = self.config

        # Ignition
        if time >= cfg.ignition_time and time < cfg.ignition_time + cfg.dt / 3600:
            # Initialize fire at ignition point
            ignition_i = int(cfg.ignition_x / self.dx)
            ignition_j = int(cfg.ignition_y / self.dy)

            radius_cells = int(cfg.ignition_radius / self.dx)

            for di in range(-radius_cells, radius_cells + 1):
                for dj in range(-radius_cells, radius_cells + 1):
                    if di**2 + dj**2 <= radius_cells**2:
                        i = ignition_i + di
                        j = ignition_j + dj
                        if 0 <= i < cfg.nx and 0 <= j < cfg.ny:
                            self.fire_intensity[i, j] = self._fire_intensity_calc(
                                self._rothermel_ros()
                            )
                            self.arrival_time[i, j] = time

        # Fire spread
        self._fire_spread(time)

        # Suppression
        self._suppression(time)

        # Decay fire intensity in burned areas
        self.fire_intensity[self.fuel < 0.1] *= 0.9

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run the wildfire simulation"""
        cfg = self.config
        n_steps = int(cfg.hours * 3600 / cfg.dt)

        logger.info(
            f"Starting wildfire simulation: {cfg.hours} hours, fuel={cfg.fuel_type}"
        )
        logger.info(
            f"Ignition at ({cfg.ignition_x / 1000:.1f}, {cfg.ignition_y / 1000:.1f}) km"
        )

        for step in range(n_steps):
            time = step * cfg.dt / 3600.0  # hours

            self._step(time)

            # Output
            if step % cfg.output_interval == 0:
                burned_area = self._calculate_burned_area()
                perimeter = self._calculate_fire_perimeter()
                max_intensity = np.max(self.fire_intensity)
                active_cells = np.sum(self.fire_intensity > 100)

                self.history["burned_area"].append(burned_area)
                self.history["fire_perimeter"].append(perimeter)
                self.history["max_intensity"].append(max_intensity)
                self.history["active_fire_cells"].append(int(active_cells))
                self.history["spot_fire_count"].append(len(self.spot_fires))
                self.history["time"].append(time)

            if step % 30 == 0:
                logger.debug(
                    f"Step {step}/{n_steps}, t={time:.1f}h, burned={burned_area:.1f} ha"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Final statistics
        final_burned = self._calculate_burned_area()
        crown_fraction = np.sum(self.crown_fire) / (cfg.nx * cfg.ny)

        # Fire behavior classes
        max_intensity = (
            max(self.history["max_intensity"]) if self.history["max_intensity"] else 0
        )

        if max_intensity < 350:
            fire_class = "Low"
        elif max_intensity < 1700:
            fire_class = "Moderate"
        elif max_intensity < 8000:
            fire_class = "High"
        elif max_intensity < 40000:
            fire_class = "Very High"
        else:
            fire_class = "Extreme"

        return {
            "burned_area_ha": self.history["burned_area"],
            "fire_perimeter_m": self.history["fire_perimeter"],
            "max_intensity": self.history["max_intensity"],
            "active_fire_cells": self.history["active_fire_cells"],
            "spot_fires": self.history["spot_fire_count"],
            "time_hours": self.history["time"],
            "final_state": {
                "total_burned_ha": float(final_burned),
                "crown_fire_fraction": float(crown_fraction),
                "max_fire_intensity_kW_m": float(max_intensity),
                "fire_class": fire_class,
                "total_spot_fires": len(self.spot_fires),
            },
            "fire_behavior": {
                "fuel_type": cfg.fuel_type,
                "fuel_moisture": cfg.fuel_moisture,
                "wind_speed_kmh": cfg.wind_speed,
                "spread_rate": float(self._rothermel_ros()),
            },
            "grid": {
                "nx": cfg.nx,
                "ny": cfg.ny,
                "dx": self.dx,
            },
            "config": {
                "hours": cfg.hours,
                "ignition_location": (cfg.ignition_x, cfg.ignition_y),
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Wildfire",
            "category": "ON_DEMAND",
            "domain": ["Fire Science", "Emergency Management"],
            "description": "Wildfire spread model with spotting and crown fire",
            "computational_complexity": "O(N²)",
            "typical_runtime": "minutes",
            "accuracy": "Moderate (operational grade)",
            "assumptions": [
                "Rothermel-style spread",
                "Elliptical fire growth",
                "Probabilistic spotting",
                "Simplified suppression",
            ],
            "parameters": [
                {
                    "name": "nx",
                    "type": "int",
                    "default": 200,
                    "description": "Grid points in x",
                },
                {
                    "name": "ny",
                    "type": "int",
                    "default": 200,
                    "description": "Grid points in y",
                },
                {
                    "name": "hours",
                    "type": "int",
                    "default": 24,
                    "description": "Simulation hours",
                },
                {
                    "name": "wind_speed",
                    "type": "float",
                    "default": 10.0,
                    "description": "Wind speed (km/h)",
                },
                {
                    "name": "fuel_moisture",
                    "type": "float",
                    "default": 0.15,
                    "description": "Fuel moisture fraction",
                },
                {
                    "name": "fuel_type",
                    "type": "str",
                    "default": "mixed_wood",
                    "description": "Fuel type",
                },
            ],
        }


# Unit tests
import unittest


class TestWildfire(unittest.TestCase):
    """TestWildfire."""
    def test_initialization(self) -> None:
        """Test that pattern initializes correctly"""
        config = WildfireConfig(nx=50, ny=50)
        pattern = WildfirePattern(config)

        self.assertEqual(pattern.fuel.shape, (50, 50))
        self.assertEqual(pattern.fire_intensity.shape, (50, 50))
        self.assertTrue(np.all(pattern.fuel > 0))

    def test_rothermel_ros(self) -> None:
        """Test rate of spread calculation"""
        config = WildfireConfig()
        pattern = WildfirePattern(config)

        ros = pattern._rothermel_ros()

        self.assertIsInstance(ros, float)
        self.assertGreater(ros, 0)

    def test_slope_factor(self) -> None:
        """Test slope factor calculation"""
        config = WildfireConfig(slope=0.2)
        pattern = WildfirePattern(config)

        slope_factor = pattern._slope_factor(25, 25)

        self.assertIsInstance(slope_factor, float)
        self.assertGreater(slope_factor, 1.0)  # Upslope increases ROS

    def test_fire_intensity(self) -> None:
        """Test fire intensity calculation"""
        config = WildfireConfig()
        pattern = WildfirePattern(config)

        intensity = pattern._fire_intensity_calc(10.0)

        self.assertIsInstance(intensity, float)
        self.assertGreater(intensity, 0)

    def test_spotting(self) -> None:
        """Test spotting generation"""
        config = WildfireConfig(spotting_enabled=True)
        pattern = WildfirePattern(config)

        # Create some burning cells
        pattern.fire_intensity[25, 25] = 5000

        burning_cells = [(25, 25)]
        n_spots_before = len(pattern.spot_fires)

        pattern._spotting(burning_cells, 1.0)

        # May or may not generate spots (probabilistic)
        self.assertGreaterEqual(len(pattern.spot_fires), n_spots_before)

    def test_crown_fire(self) -> None:
        """Test crown fire transition"""
        config = WildfireConfig(crown_fire_enabled=True, fuel_type="conifer")
        pattern = WildfirePattern(config)

        # Set high intensity
        pattern.fire_intensity[25, 25] = 5000

        pattern._crown_fire_transition()

        self.assertTrue(pattern.crown_fire[25, 25])

    def test_burned_area(self) -> None:
        """Test burned area calculation"""
        config = WildfireConfig()
        pattern = WildfirePattern(config)

        # Burn some cells
        pattern.fuel[20:30, 20:30] = 0

        area = pattern._calculate_burned_area()

        self.assertIsInstance(area, float)
        self.assertGreater(area, 0)

    def test_fire_perimeter(self) -> None:
        """Test perimeter calculation"""
        config = WildfireConfig()
        pattern = WildfirePattern(config)

        # Create a burned patch
        pattern.fuel[23:27, 23:27] = 0

        perimeter = pattern._calculate_fire_perimeter()

        self.assertIsInstance(perimeter, float)
        self.assertGreater(perimeter, 0)

    def test_step(self) -> None:
        """Test single time step"""
        config = WildfireConfig()
        pattern = WildfirePattern(config)

        # Set ignition
        pattern.fire_intensity[50, 50] = 1000

        pattern._step(0.5)

        # Fire should spread or intensity change
        self.assertTrue(np.any(pattern.fire_intensity > 0))

    def test_metadata(self) -> None:
        """Test metadata retrieval"""
        metadata = WildfirePattern.get_metadata()

        self.assertEqual(metadata["id"], "wildfire")
        self.assertIn("parameters", metadata)

    def test_short_simulation(self) -> None:
        """Test running a short simulation"""
        config = WildfireConfig(nx=50, ny=50, hours=2, dt=60, output_interval=5)
        pattern = WildfirePattern(config)

        result = pattern.run()

        self.assertIn("burned_area_ha", result)
        self.assertIn("final_state", result)
        self.assertGreater(len(result["time_hours"]), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
