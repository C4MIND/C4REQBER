"""
TURBO-CDI v6.0 - Climate GCM Pattern
Atmospheric and oceanic circulation modeling using simplified GCM approach.

Pattern Structure (Christopher Alexander):
- Context: Climate modeling, weather prediction, climate change analysis
- Forces: Complexity of Navier-Stokes, computational cost, grid resolution
- Solution: Simplified GCM with parameterizations
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GCMConfig:
    """Configuration for GCM simulation"""

    # Grid settings
    n_lat: int = 32  # Latitude grid points
    n_lon: int = 64  # Longitude grid points
    n_levels: int = 8  # Vertical levels

    # Physics
    dt: float = 600.0  # Time step (seconds)
    day_duration: float = 86400.0  # Seconds per simulated day
    days: int = 30  # Simulation days

    # Planet parameters
    radius: float = 6.371e6  # Earth radius (m)
    omega: float = 7.292e-5  # Angular velocity (rad/s)
    g: float = 9.81  # Gravity (m/s²)

    # Atmospheric parameters
    p_surface: float = 101325.0  # Surface pressure (Pa)
    t_surface: float = 288.0  # Surface temperature (K)

    # Simplified physics flags
    enable_radiation: bool = True
    enable_convection: bool = True
    enable_precipitation: bool = True

    # Output
    output_interval: int = 4  # Output every N timesteps


class ClimateGCMPattern:
    """
    Simplified Global Climate Model (GCM).

    Solves primitive equations on latitude-longitude grid with
    sigma vertical coordinate. Includes simplified radiation,
    convection, and precipitation parameterizations.
    """

    PATTERN_ID = "climate_gcm"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[GCMConfig] = None):
        self.config = config or GCMConfig()
        self._initialize_grid()
        self._initialize_fields()

    def _initialize_grid(self):
        """Initialize computational grid"""
        cfg = self.config

        # Latitude grid (Gaussian)
        self.lats = np.linspace(-90, 90, cfg.n_lat)
        self.lons = np.linspace(0, 360, cfg.n_lon, endpoint=False)

        # Convert to radians
        self.lat_rad = np.radians(self.lats)
        self.lon_rad = np.radians(self.lons)

        # Sigma levels (normalized pressure)
        self.sigma = np.linspace(0.1, 1.0, cfg.n_levels)

        # Grid spacing
        self.dlat = np.radians(180.0 / (cfg.n_lat - 1))
        self.dlon = np.radians(360.0 / cfg.n_lon)

        # Coriolis parameter
        self.f = 2 * cfg.omega * np.sin(self.lat_rad)

        # Cosine of latitude (for spherical geometry)
        self.cos_lat = np.cos(self.lat_rad)
        self.cos_lat_2d = self.cos_lat[:, np.newaxis]

    def _initialize_fields(self):
        """Initialize prognostic variables"""
        cfg = self.config
        shape_3d = (cfg.n_lat, cfg.n_lon, cfg.n_levels)
        shape_2d = (cfg.n_lat, cfg.n_lon)

        # Winds
        self.u = np.zeros(shape_3d)  # Zonal wind
        self.v = np.zeros(shape_3d)  # Meridional wind
        self.omega = np.zeros(shape_3d)  # Vertical velocity (Pa/s)

        # Thermodynamic variables
        self.T = np.ones(shape_3d) * cfg.t_surface  # Temperature
        self.q = np.zeros(shape_3d)  # Specific humidity
        self.p_surf = np.ones(shape_2d) * cfg.p_surface  # Surface pressure

        # Initialize temperature profile (decreases with height)
        for k in range(cfg.n_levels):
            lapse_rate = 6.5e-3  # K/m
            height = (1 - self.sigma[k]) * 1e4  # Approximate height
            self.T[:, :, k] = cfg.t_surface - lapse_rate * height

        # Initialize humidity (decreases with height)
        q_surf = 0.01  # kg/kg
        for k in range(cfg.n_levels):
            self.q[:, :, k] = q_surf * self.sigma[k] ** 3

        # Geopotential
        self.phi = np.zeros(shape_3d)
        self._update_geopotential()

        # Output storage
        self.history = {"T": [], "u": [], "v": [], "precip": [], "time": []}

    def _update_geopotential(self):
        """Calculate geopotential from temperature"""
        cfg = self.config
        R = 287.0  # Gas constant for dry air

        # Hydrostatic integration
        for k in range(cfg.n_levels):
            if k == 0:
                self.phi[:, :, k] = cfg.g * 100  # Surface geopotential
            else:
                # Integrate hydrostatic equation
                dlnp = np.log(self.sigma[k]) - np.log(self.sigma[k - 1])
                self.phi[:, :, k] = self.phi[:, :, k - 1] + R * self.T[:, :, k] * dlnp

    def _calculate_pressure(self) -> np.ndarray:
        """Calculate 3D pressure field"""
        cfg = self.config
        p = np.zeros((cfg.n_lat, cfg.n_lon, cfg.n_levels))
        for k in range(cfg.n_levels):
            p[:, :, k] = self.p_surf * self.sigma[k]
        return p

    def _calculate_density(self) -> np.ndarray:
        """Calculate air density"""
        p = self._calculate_pressure()
        R = 287.0
        return p / (R * self.T)

    def _radiation_scheme(self) -> np.ndarray:
        """
        Simplified radiation scheme.
        Includes solar heating and longwave cooling.
        """
        cfg = self.config
        heating = np.zeros_like(self.T)

        # Solar heating (simplified)
        cos_sza = np.cos(self.lat_rad)[:, np.newaxis]  # Cosine solar zenith
        solar_max = 300.0  # W/m²

        for k in range(cfg.n_levels):
            # Absorption decreases with height
            absorption = np.exp(-(1 - self.sigma[k]) * 3)
            heating[:, :, k] = solar_max * cos_sza * absorption / (1004.0 * 100.0)

        # Longwave cooling (simplified)
        cooling_rate = 1.5  # K/day
        heating -= cooling_rate / cfg.day_duration * cfg.dt

        return heating

    def _convection_scheme(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simplified convection scheme.
        Returns heating and moistening tendencies.
        """
        cfg = self.config

        heating = np.zeros_like(self.T)
        moistening = np.zeros_like(self.q)

        # Simple adjustment scheme
        for j in range(cfg.n_lat):
            for i in range(cfg.n_lon):
                # Check for convective instability
                for k in range(cfg.n_levels - 1):
                    # If lower level is cooler than upper (unstable)
                    if self.T[j, i, k] < self.T[j, i, k + 1]:
                        # Mix to remove instability
                        avg_T = (self.T[j, i, k] + self.T[j, i, k + 1]) / 2
                        heating[j, i, k] = (avg_T - self.T[j, i, k]) / cfg.dt * 0.1
                        heating[j, i, k + 1] = (
                            (avg_T - self.T[j, i, k + 1]) / cfg.dt * 0.1
                        )

        return heating, moistening

    def _precipitation_scheme(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simplified precipitation scheme.
        Returns precipitation rate and humidity tendency.
        """
        cfg = self.config

        # Saturation humidity
        es = 611.2 * np.exp(17.67 * (self.T - 273.15) / (self.T - 29.65))
        p = self._calculate_pressure()
        qs = 0.622 * es / p

        # Relative humidity
        RH = self.q / qs

        # Precipitation where RH > 100%
        precip = np.zeros((cfg.n_lat, cfg.n_lon))
        dq = np.zeros_like(self.q)

        for k in range(cfg.n_levels):
            excess = np.maximum(0, self.q[:, :, k] - qs[:, :, k])
            precip += excess * p[:, :, k] / cfg.g / cfg.dt
            dq[:, :, k] = -excess / cfg.dt

        return precip, dq

    def _momentum_tendency(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate momentum tendencies"""
        cfg = self.config

        # Pressure gradient forces (simplified)
        dphi_dx = np.zeros_like(self.u)
        dphi_dy = np.zeros_like(self.v)

        # Geopotential gradients
        for k in range(cfg.n_levels):
            dphi_dx[:, :, k] = np.gradient(self.phi[:, :, k], axis=1) / self.dlon
            dphi_dy[:, :, k] = np.gradient(self.phi[:, :, k], axis=0) / self.dlat

        # Coriolis acceleration
        f_3d = self.f[:, np.newaxis, np.newaxis] * np.ones_like(self.u)

        du_dt = f_3d * self.v - dphi_dx / cfg.radius
        dv_dt = -f_3d * self.u - dphi_dy / cfg.radius

        # Add diffusion
        diffusion_coef = 1e5  # m²/s
        for k in range(cfg.n_levels):
            du_dt[:, :, k] += diffusion_coef * self._laplacian(self.u[:, :, k])
            dv_dt[:, :, k] += diffusion_coef * self._laplacian(self.v[:, :, k])

        return du_dt, dv_dt

    def _laplacian(self, field: np.ndarray) -> np.ndarray:
        """Spherical Laplacian on latitude-longitude grid"""
        lapl = np.zeros_like(field)

        # Simple 5-point stencil
        lapl[1:-1, 1:-1] = (
            field[:-2, 1:-1]
            + field[2:, 1:-1]
            + field[1:-1, :-2]
            + field[1:-1, 2:]
            - 4 * field[1:-1, 1:-1]
        )

        # Periodic in longitude
        lapl[:, 0] = lapl[:, -2]
        lapl[:, -1] = lapl[:, 1]

        # Poles (simplified)
        lapl[0, :] = lapl[1, :]
        lapl[-1, :] = lapl[-2, :]

        return lapl

    def _step(self):
        """Advance model by one time step"""
        cfg = self.config

        # Calculate tendencies
        du_dt, dv_dt = self._momentum_tendency()

        dT_dt = np.zeros_like(self.T)
        dq_dt = np.zeros_like(self.q)

        # Physics tendencies
        if cfg.enable_radiation:
            dT_dt += self._radiation_scheme()

        if cfg.enable_convection:
            conv_T, conv_q = self._convection_scheme()
            dT_dt += conv_T
            dq_dt += conv_q

        if cfg.enable_precipitation:
            precip, precip_q = self._precipitation_scheme()
            dq_dt += precip_q
            self.precip = precip

        # Update fields (forward Euler)
        self.u += du_dt * cfg.dt
        self.v += dv_dt * cfg.dt
        self.T += dT_dt * cfg.dt
        self.q += dq_dt * cfg.dt

        # Ensure physical bounds
        self.q = np.clip(self.q, 0, 0.05)
        self.T = np.clip(self.T, 150, 350)

        # Update geopotential
        self._update_geopotential()

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the GCM simulation"""
        cfg = self.config
        n_steps = int(cfg.days * cfg.day_duration / cfg.dt)

        logger.info(f"Starting GCM simulation: {cfg.days} days, {n_steps} steps")

        for step in range(n_steps):
            self._step()

            # Output
            if step % cfg.output_interval == 0:
                day = step * cfg.dt / cfg.day_duration
                self.history["T"].append(self.T.copy())
                self.history["u"].append(self.u.copy())
                self.history["v"].append(self.v.copy())
                self.history["precip"].append(
                    getattr(self, "precip", np.zeros((cfg.n_lat, cfg.n_lon)))
                )
                self.history["time"].append(day)

            if step % 100 == 0:
                logger.debug(f"Step {step}/{n_steps}, Day {day:.1f}")

        # Convert history to arrays
        for key in ["T", "u", "v", "precip", "time"]:
            self.history[key] = np.array(self.history[key])

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate statistics
        T_mean = np.mean(self.history["T"], axis=(1, 2, 3))
        u_mean = np.mean(self.history["u"], axis=(1, 2, 3))
        v_mean = np.mean(self.history["v"], axis=(1, 2, 3))
        precip_total = np.sum(self.history["precip"], axis=(1, 2))

        return {
            "mean_temperature_timeseries": T_mean.tolist(),
            "mean_zonal_wind": u_mean.tolist(),
            "mean_meridional_wind": v_mean.tolist(),
            "total_precipitation": precip_total.tolist(),
            "time_days": self.history["time"].tolist(),
            "final_state": {
                "T": self.T.tolist(),
                "u": self.u.tolist(),
                "v": self.v.tolist(),
                "q": self.q.tolist(),
                "p_surf": self.p_surf.tolist(),
            },
            "grid": {
                "lats": self.lats.tolist(),
                "lons": self.lons.tolist(),
                "sigma": self.sigma.tolist(),
            },
            "config": {
                "n_lat": cfg.n_lat,
                "n_lon": cfg.n_lon,
                "n_levels": cfg.n_levels,
                "days": cfg.days,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Climate GCM",
            "category": "ON_DEMAND",
            "domain": ["Climate Science", "Atmospheric Physics"],
            "description": "Simplified Global Climate Model for atmospheric circulation",
            "computational_complexity": "O(N³)",
            "typical_runtime": "minutes to hours",
            "accuracy": "Moderate (educational/research grade)",
            "assumptions": [
                "Hydrostatic balance",
                "Simplified radiation",
                "Parameterised convection",
                "Spherical geometry",
            ],
            "parameters": [
                {
                    "name": "n_lat",
                    "type": "int",
                    "default": 32,
                    "description": "Latitude grid points",
                },
                {
                    "name": "n_lon",
                    "type": "int",
                    "default": 64,
                    "description": "Longitude grid points",
                },
                {
                    "name": "n_levels",
                    "type": "int",
                    "default": 8,
                    "description": "Vertical levels",
                },
                {
                    "name": "days",
                    "type": "int",
                    "default": 30,
                    "description": "Simulation days",
                },
            ],
        }


if __name__ == "__main__":
    # Test GCM pattern
    logging.basicConfig(level=logging.INFO)

    config = GCMConfig(days=5, n_lat=16, n_lon=32, n_levels=4)
    gcm = ClimateGCMPattern(config)

    result = gcm.run()
    print(
        f"Simulation complete. Final mean T: {result['mean_temperature_timeseries'][-1]:.2f} K"
    )
    print(
        f"Precipitation range: {min(result['total_precipitation']):.2e} to {max(result['total_precipitation']):.2e} mm/day"
    )
