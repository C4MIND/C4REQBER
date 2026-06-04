# Migrated to Newton Physics (2025) — github.com/newton-physics/newton — Apache 2.0 License
"""
C4REQBER v6.0 - Molecular Dynamics Pattern
Classical molecular dynamics simulation with various force fields.

Pattern Structure (Christopher Alexander):
- Context: Materials science, drug design, protein folding
- Forces: Long-range interactions, timescale separation, temperature control
- Solution: Velocity Verlet integration with thermostat
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class ForceField(Enum):
    """Available force fields"""

    LJ = "lennard_jones"  # Lennard-Jones
    EAM = "eam"  # Embedded Atom Method
    MORSE = "morse"  # Morse potential
    BUCKINGHAM = "buckingham"  # Buckingham potential


@dataclass
class MDConfig:
    """Configuration for molecular dynamics"""

    # System
    n_atoms: int = 256
    box_size: float = 10.0  # Angstroms
    temperature: float = 300.0  # Kelvin

    # Integration
    dt: float = 1.0  # Femtoseconds
    steps: int = 10000

    # Force field
    force_field: ForceField = ForceField.LJ
    cutoff: float = 10.0  # Angstroms

    # Thermostat
    thermostat: str = "nose_hoover"  # nose_hoover, berendsen, none
    tau_t: float = 100.0  # Thermostat coupling time (fs)

    # Output
    output_interval: int = 100

    # Physical constants
    kB: float = 0.0019872041  # Boltzmann constant (kcal/mol/K)

    # LJ parameters
    epsilon: float = 0.238  # kcal/mol
    sigma: float = 3.4  # Angstroms (Argon-like)


class MolecularDynamicsPattern:
    """
    Classical molecular dynamics simulation.

    Implements velocity Verlet integration with various force fields
    and thermostats for constant temperature simulations.
    """

    PATTERN_ID = "molecular_dynamics"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: MDConfig | None = None) -> None:
        self.config = config or MDConfig()
        self.positions: np.ndarray | None = None
        self.velocities: np.ndarray | None = None
        self.forces: np.ndarray | None = None

        # Thermostat variables
        self.eta = 0.0  # Nose-Hoover variable

        # Trajectory storage
        self.trajectory = []  # type: ignore[var-annotated]
        self.energies = []  # type: ignore[var-annotated]
        self.temperatures = []  # type: ignore[var-annotated]

        self._initialize_system()

    def _initialize_system(self) -> None:
        """Initialize atomic positions and velocities"""
        cfg = self.config

        # Initialize on simple cubic lattice
        n = int(np.ceil(cfg.n_atoms ** (1 / 3)))
        positions = []
        spacing = cfg.box_size / n

        atom_id = 0
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if atom_id < cfg.n_atoms:
                        x = (i + 0.5) * spacing
                        y = (j + 0.5) * spacing
                        z = (k + 0.5) * spacing
                        positions.append([x, y, z])
                        atom_id += 1

        self.positions = np.array(positions)

        # Initialize velocities from Maxwell-Boltzmann distribution
        mass = 39.948  # Argon mass (amu)
        sigma_v = np.sqrt(cfg.kB * cfg.temperature / mass)

        self.velocities = np.random.normal(0, sigma_v, (cfg.n_atoms, 3))

        # Remove center of mass velocity
        self.velocities -= np.mean(self.velocities, axis=0)

        # Scale to exact temperature
        current_temp = self._calculate_temperature()
        self.velocities *= np.sqrt(cfg.temperature / current_temp)

        # Calculate initial forces
        self.forces = self._calculate_forces()

    def _calculate_temperature(self) -> float:
        """Calculate instantaneous temperature"""
        cfg = self.config
        mass = 39.948

        ke = 0.5 * mass * np.sum(self.velocities**2)  # type: ignore[operator]
        # T = 2*KE / (3*N*kB)
        return 2 * ke / (3 * cfg.n_atoms * cfg.kB)  # type: ignore[no-any-return]

    def _calculate_forces(self) -> np.ndarray:
        """Calculate forces on all atoms"""
        cfg = self.config

        if cfg.force_field == ForceField.LJ:
            return self._calculate_lj_forces()
        elif cfg.force_field == ForceField.MORSE:
            return self._calculate_morse_forces()
        else:
            return self._calculate_lj_forces()

    def _calculate_lj_forces(self) -> np.ndarray:
        """Calculate Lennard-Jones forces"""
        cfg = self.config
        forces = np.zeros_like(self.positions)

        epsilon = cfg.epsilon
        sigma = cfg.sigma
        cutoff = cfg.cutoff
        cutoff2 = cutoff**2

        for i in range(cfg.n_atoms):
            for j in range(i + 1, cfg.n_atoms):
                # Distance vector with periodic boundary conditions
                rij = self.positions[j] - self.positions[i]  # type: ignore[index]
                rij -= cfg.box_size * np.round(rij / cfg.box_size)

                r2 = np.sum(rij**2)

                if r2 < cutoff2 and r2 > 0:
                    r = np.sqrt(r2)

                    # LJ force: F = 24*ε*(2*(σ/r)^12 - (σ/r)^6) * r_vec/r^2
                    sr6 = (sigma / r) ** 6
                    sr12 = sr6**2

                    f_mag = 24 * epsilon * (2 * sr12 - sr6) / r
                    f_vec = f_mag * rij / r

                    forces[i] -= f_vec
                    forces[j] += f_vec

        return forces

    def _calculate_morse_forces(self) -> np.ndarray:
        """Calculate Morse potential forces"""
        cfg = self.config
        forces = np.zeros_like(self.positions)

        D = cfg.epsilon
        alpha = 1.5 / cfg.sigma
        r0 = cfg.sigma * 2 ** (1 / 6)

        for i in range(cfg.n_atoms):
            for j in range(i + 1, cfg.n_atoms):
                rij = self.positions[j] - self.positions[i]  # type: ignore[index]
                rij -= cfg.box_size * np.round(rij / cfg.box_size)

                r = np.sqrt(np.sum(rij**2))

                if r < cfg.cutoff and r > 0:
                    # Morse force
                    exp_term = np.exp(-alpha * (r - r0))
                    f_mag = 2 * D * alpha * exp_term * (1 - exp_term)
                    f_vec = f_mag * rij / r

                    forces[i] -= f_vec
                    forces[j] += f_vec

        return forces

    def _calculate_potential_energy(self) -> float:
        """Calculate total potential energy"""
        cfg = self.config
        energy = 0.0

        epsilon = cfg.epsilon
        sigma = cfg.sigma
        cutoff2 = cfg.cutoff**2

        for i in range(cfg.n_atoms):
            for j in range(i + 1, cfg.n_atoms):
                rij = self.positions[j] - self.positions[i]  # type: ignore[index]
                rij -= cfg.box_size * np.round(rij / cfg.box_size)

                r2 = np.sum(rij**2)

                if r2 < cutoff2 and r2 > 0:
                    r6 = (sigma**2 / r2) ** 3
                    r12 = r6**2
                    energy += 4 * epsilon * (r12 - r6)

        return energy

    def _calculate_kinetic_energy(self) -> float:
        """Calculate total kinetic energy"""
        mass = 39.948
        return 0.5 * mass * np.sum(self.velocities**2)  # type: ignore[no-any-return, operator]

    def _apply_thermostat(self) -> None:
        """Apply thermostat to maintain temperature"""
        cfg = self.config

        if cfg.thermostat == "nose_hoover":
            self._apply_nose_hoover()
        elif cfg.thermostat == "berendsen":
            self._apply_berendsen()
        # else: no thermostat

    def _apply_nose_hoover(self) -> None:
        """Nose-Hoover thermostat"""
        cfg = self.config
        mass = 39.948

        # Calculate current temperature
        temp = self._calculate_temperature()

        # Nose-Hoover chain (simplified)
        Q = 3 * cfg.n_atoms * cfg.kB * cfg.temperature * cfg.tau_t**2

        # Update thermostat variable
        self.eta += cfg.dt * (temp - cfg.temperature) / Q * 3 * cfg.n_atoms * cfg.kB

        # Scale velocities
        scale = np.exp(-cfg.dt * self.eta / (2 * cfg.tau_t))
        self.velocities *= scale

    def _apply_berendsen(self) -> None:
        """Berendsen weak coupling thermostat"""
        cfg = self.config

        temp = self._calculate_temperature()
        lambda_factor = np.sqrt(1 + cfg.dt / cfg.tau_t * (cfg.temperature / temp - 1))

        self.velocities *= lambda_factor

    def _velocity_verlet_step(self) -> None:
        """One step of velocity Verlet integration"""
        cfg = self.config
        mass = 39.948

        # v(t + dt/2) = v(t) + F(t)*dt/(2m)
        self.velocities += self.forces * cfg.dt / (2 * mass)  # type: ignore[assignment, operator]

        # r(t + dt) = r(t) + v(t + dt/2)*dt
        self.positions += self.velocities * cfg.dt  # type: ignore[assignment, operator]

        # Apply periodic boundary conditions
        self.positions -= cfg.box_size * np.floor(self.positions / cfg.box_size)  # type: ignore[operator]

        # F(t + dt)
        self.forces = self._calculate_forces()

        # v(t + dt) = v(t + dt/2) + F(t + dt)*dt/(2m)
        self.velocities += self.forces * cfg.dt / (2 * mass)  # type: ignore[operator]

        # Apply thermostat
        self._apply_thermostat()

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run molecular dynamics simulation with Newton (or fallback)"""
        from src.simulations.newton_bridge import NewtonBridge
        bridge = NewtonBridge()

        if bridge.available:
            newton_config = {
                "type": "molecular_dynamics",
                "n_atoms": self.config.n_atoms,
                "box_size": self.config.box_size,
                "temperature": self.config.temperature,
                "dt": self.config.dt,
                "steps": self.config.steps,
                "force_field": self.config.force_field.value,
                "cutoff": self.config.cutoff,
                "thermostat": self.config.thermostat,
                "tau_t": self.config.tau_t,
                "output_interval": self.config.output_interval,
                "kB": self.config.kB,
                "epsilon": self.config.epsilon,
                "sigma": self.config.sigma,
            }
            if hypothesis:
                newton_config.update(hypothesis)
            result = bridge.run_simulation(newton_config)
            if result.get("status") == "success":
                return result

        # Fallback to legacy implementation
        cfg = self.config

        logger.info(
            f"Starting MD simulation: {cfg.n_atoms} atoms, "
            f"{cfg.steps} steps, T={cfg.temperature}K"
        )

        for step in range(cfg.steps):
            self._velocity_verlet_step()

            # Output
            if step % cfg.output_interval == 0:
                pe = self._calculate_potential_energy()
                ke = self._calculate_kinetic_energy()
                temp = self._calculate_temperature()

                self.energies.append(
                    {
                        "step": step,
                        "potential": pe,
                        "kinetic": ke,
                        "total": pe + ke,
                        "temperature": temp,
                    }
                )

                self.temperatures.append(temp)

                # Store trajectory (every 10th output)
                if step % (cfg.output_interval * 10) == 0:
                    self.trajectory.append(self.positions.copy())  # type: ignore[union-attr]

            if step % 1000 == 0:
                logger.debug(
                    f"Step {step}/{cfg.steps}, T={temp:.1f}K, "
                    f"E={(pe + ke) / cfg.n_atoms:.3f} kcal/mol/atom"
                )

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate statistics
        temps = np.array(self.temperatures)
        energies = np.array([e["total"] for e in self.energies])

        return {
            "n_atoms": cfg.n_atoms,
            "box_size": cfg.box_size,
            "target_temperature": cfg.temperature,
            "mean_temperature": float(np.mean(temps)),
            "temperature_std": float(np.std(temps)),
            "mean_total_energy": float(np.mean(energies)),
            "energy_drift": float(energies[-1] - energies[0]),
            "energies": self.energies,
            "temperature_timeseries": temps.tolist(),
            "trajectory": [t.tolist() for t in self.trajectory],
            "final_positions": self.positions.tolist(),  # type: ignore[union-attr]
            "final_velocities": self.velocities.tolist(),  # type: ignore[union-attr]
            "force_field": cfg.force_field.value,
            "thermostat": cfg.thermostat,
            "config": {"dt_fs": cfg.dt, "steps": cfg.steps, "cutoff_A": cfg.cutoff},
        }

    def calculate_rdf(self, bins: int = 100) -> dict[str, np.ndarray]:
        """
        Calculate radial distribution function g(r).
        Useful for analyzing liquid structure.
        """
        cfg = self.config

        max_r = cfg.box_size / 2
        dr = max_r / bins

        g_r = np.zeros(bins)
        counts = np.zeros(bins)

        for i in range(cfg.n_atoms):
            for j in range(i + 1, cfg.n_atoms):
                rij = self.positions[j] - self.positions[i]  # type: ignore[index]
                rij -= cfg.box_size * np.round(rij / cfg.box_size)
                r = np.sqrt(np.sum(rij**2))

                if r < max_r:
                    bin_idx = int(r / dr)
                    if bin_idx < bins:
                        g_r[bin_idx] += 2  # Count both i-j and j-i

        # Normalize
        rho = cfg.n_atoms / (cfg.box_size**3)
        for i in range(bins):
            r_inner = i * dr
            r_outer = (i + 1) * dr
            shell_volume = 4 / 3 * np.pi * (r_outer**3 - r_inner**3)
            expected = rho * shell_volume * cfg.n_atoms
            if expected > 0:
                g_r[i] /= expected

        r_bins = np.arange(bins) * dr + dr / 2

        return {"r": r_bins, "g_r": g_r}

    def calculate_msd(self) -> float:
        """
        Calculate mean squared displacement.
        Useful for estimating diffusion coefficient.
        """
        if len(self.trajectory) < 2:
            return 0.0

        initial = self.trajectory[0]
        final = self.trajectory[-1]

        # Account for periodic boundary conditions
        dr = final - initial
        dr -= self.config.box_size * np.round(dr / self.config.box_size)

        return np.mean(np.sum(dr**2, axis=1))  # type: ignore[no-any-return]

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Molecular Dynamics",
            "category": "ON_DEMAND",
            "domain": ["Materials Science", "Chemistry", "Biophysics"],
            "description": "Classical molecular dynamics with velocity Verlet integration",
            "computational_complexity": "O(N²) per timestep",
            "typical_runtime": "minutes to hours",
            "accuracy": "High (classical limit)",
            "assumptions": [
                "Classical mechanics (no quantum effects)",
                "Pairwise additive forces",
                "Periodic boundary conditions",
                "Fixed simulation box",
            ],
            "parameters": [
                {"name": "n_atoms", "type": "int", "default": 256},
                {"name": "temperature", "type": "float", "default": 300.0},
                {"name": "steps", "type": "int", "default": 10000},
                {
                    "name": "force_field",
                    "type": "enum",
                    "options": ["lennard_jones", "morse"],
                    "default": "lennard_jones",
                },
                {
                    "name": "thermostat",
                    "type": "enum",
                    "options": ["nose_hoover", "berendsen", "none"],
                    "default": "nose_hoover",
                },
            ],
        }


if __name__ == "__main__":
    # Test MD pattern
    logging.basicConfig(level=logging.INFO)

    config = MDConfig(n_atoms=64, steps=1000, temperature=100.0)
    md = MolecularDynamicsPattern(config)

    result = md.run()
    print(f"MD complete. Mean T: {result['mean_temperature']:.1f}K")
    print(f"Energy drift: {result['energy_drift']:.3f} kcal/mol")

    # Calculate RDF
    rdf = md.calculate_rdf()
    print(f"RDF calculated, max g(r): {max(rdf['g_r']):.2f}")

    # Calculate MSD
    msd = md.calculate_msd()
    print(f"MSD: {msd:.3f} Å²")
