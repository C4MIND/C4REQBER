# Migrated to Newton Physics (2025) — github.com/newton-physics/newton — Apache 2.0 License
"""
Pattern 20: N-Body Gravity

Christopher Alexander Structure:
- Context: Simulating gravitational interactions between N point masses (planets, stars,
  galaxies). Direct O(N^2) computation becomes prohibitive for N > 10^4.
- Forces:
  * Accuracy vs computational cost trade-off
  * Need for long-term energy conservation in orbital dynamics
  * Hierarchical structure of astronomical systems
  * GPU acceleration for massive parallelism
- Solution: Barnes-Hut tree algorithm with O(N log N) complexity, combining direct
  summation for close particles and tree approximation for distant clusters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import BaseConfig, BasePattern, GPUMixin


@dataclass
class NBodyConfig(BaseConfig):
    """Configuration for N-Body Gravity simulation."""

    n_particles: int = 1000
    G: float = 6.67430e-11  # Gravitational constant
    softening: float = 1e-3  # Softening length to avoid singularities
    theta: float = 0.5  # Barnes-Hut opening angle criterion
    dt: float = 0.001  # Time step
    n_steps: int = 100  # Number of integration steps
    integrator: str = "leapfrog"  # "euler", "leapfrog", "rk4"
    use_gpu: bool = True
    domain_size: float = 1.0  # Size of simulation domain
    initial_distribution: str = "plummer"  # "plummer", "uniform", "disk"


class OctreeNode:
    """Node in the Barnes-Hut octree."""

    def __init__(self, center: np.ndarray, size: float) -> None:
        self.center = center  # Center of this node's region
        self.size = size  # Side length of the region
        self.mass = 0.0  # Total mass in this node
        self.com = np.zeros(3)  # Center of mass
        self.particle_idx = -1  # Index if leaf node (-1 if internal)
        self.leaf_pos = np.zeros(3)  # Position of leaf particle
        self.leaf_mass = 0.0  # Mass of leaf particle
        self.children: list[OctreeNode | None] = [None] * 8  # Octant children
        self.is_leaf = True

    def get_octant(self, pos: np.ndarray) -> int:
        """Determine which octant a position belongs to."""
        octant = 0
        for i in range(3):
            if pos[i] >= self.center[i]:
                octant |= 1 << i
        return octant

    def insert(
        self,
        pos: np.ndarray,
        mass: float,
        idx: int,
        max_depth: int = 20,
        depth: int = 0,
    ) -> None:
        """Insert a particle into the tree."""
        if depth >= max_depth:
            return

        # Update center of mass
        total_mass = self.mass + mass
        if total_mass > 0:
            self.com = (self.com * self.mass + pos * mass) / total_mass
        self.mass = total_mass

        if self.is_leaf:
            if self.particle_idx == -1:
                # Empty leaf, store particle here
                self.particle_idx = idx
                self.leaf_pos = pos.copy()
                self.leaf_mass = mass
                return
            else:
                # Occupied leaf, need to subdivide
                old_idx = self.particle_idx
                old_pos = self.leaf_pos.copy()
                old_mass = self.leaf_mass
                self.particle_idx = -1
                self.is_leaf = False

                # Create children
                half_size = self.size / 2
                for i in range(8):
                    offset = np.array(
                        [
                            (i & 1) * half_size - half_size / 2,
                            ((i >> 1) & 1) * half_size - half_size / 2,
                            ((i >> 2) & 1) * half_size - half_size / 2,
                        ]
                    )
                    self.children[i] = OctreeNode(self.center + offset, half_size)

                # Re-insert existing particle into appropriate child octant
                old_octant = self.get_octant(old_pos)
                self.children[old_octant].insert(old_pos, old_mass, old_idx, max_depth, depth + 1)  # type: ignore[union-attr]

        # Insert into appropriate child
        octant = self.get_octant(pos)
        self.children[octant].insert(pos, mass, idx, max_depth, depth + 1)  # type: ignore[union-attr]

    def compute_force(
        self, pos: np.ndarray, mass: float, theta: float, G: float, softening: float
    ) -> np.ndarray:
        """Compute gravitational force using Barnes-Hut approximation."""
        force = np.zeros(3)

        if self.mass == 0:
            return force

        # Distance to center of mass
        dx = self.com - pos
        r = np.sqrt(np.sum(dx**2) + softening**2)

        # Check if node is far enough for approximation
        if self.is_leaf or (self.size / r < theta):
            if r > softening:
                force = G * mass * self.mass * dx / r**3
        else:
            # Recurse into children
            for child in self.children:
                if child is not None:
                    force += child.compute_force(pos, mass, theta, G, softening)

        return force


class NBodyGravity(BasePattern, GPUMixin):
    """
    N-Body gravitational simulation with Barnes-Hut optimization.
    Complexity: O(N log N) with tree, O(N^2) direct method.
    """

    PATTERN_ID = "n_body_gravity"
    PATTERN_VERSION = "6.5.0"

    def _validate_config(self) -> None:
        """Validate NBody configuration parameters."""
        cfg = self.config
        if cfg.n_particles < 1:
            raise ValueError("n_particles must be at least 1")
        if cfg.theta <= 0:
            raise ValueError("theta must be positive")
        if cfg.softening <= 0:
            raise ValueError("softening must be positive")
        if cfg.dt <= 0:
            raise ValueError("dt must be positive")
        if cfg.G <= 0:
            raise ValueError("G must be positive")
        valid_integrators = {"euler", "leapfrog", "rk4"}
        if cfg.integrator not in valid_integrators:
            raise ValueError(f"integrator must be one of {valid_integrators}")
        valid_distributions = {"plummer", "uniform", "disk"}
        if cfg.initial_distribution not in valid_distributions:
            raise ValueError(f"initial_distribution must be one of {valid_distributions}")

    def __init__(self, config: NBodyConfig | None = None) -> None:
        BasePattern.__init__(self, config or NBodyConfig())
        GPUMixin.__init__(self)
        self.config: NBodyConfig = self.config
        self.positions: np.ndarray | None = None
        self.velocities: np.ndarray | None = None
        self.masses: np.ndarray | None = None
        self._initialize_particles()

    def _initialize_particles(self) -> None:
        """Initialize particle positions and velocities."""
        n = self.config.n_particles

        if self.config.initial_distribution == "plummer":
            # Plummer model for globular clusters
            self.positions, self.velocities = self._plummer_model(n)
        elif self.config.initial_distribution == "disk":
            # Disk galaxy model
            self.positions, self.velocities = self._disk_model(n)
        else:  # uniform
            self.positions = np.random.randn(n, 3) * self.config.domain_size
            self.velocities = np.random.randn(n, 3) * 0.1

        self.masses = np.ones(n) / n  # Equal masses normalized

    def _plummer_model(self, n: int) -> tuple[np.ndarray, np.ndarray]:
        """Generate Plummer model initial conditions."""
        # Plummer radius distribution
        radius = 1.0 / np.sqrt(np.random.uniform(0, 1, n) ** (-2 / 3) - 1)

        # Random directions
        theta = np.arccos(2 * np.random.uniform(0, 1, n) - 1)
        phi = 2 * np.pi * np.random.uniform(0, 1, n)

        positions = np.column_stack(
            [
                radius * np.sin(theta) * np.cos(phi),
                radius * np.sin(theta) * np.sin(phi),
                radius * np.cos(theta),
            ]
        )

        # Velocity dispersion (approximate)
        v_escape = np.sqrt(2) * (1 + radius**2) ** (-0.25)
        velocities = np.random.randn(n, 3) * 0.1

        return positions, velocities

    def _disk_model(self, n: int) -> tuple[np.ndarray, np.ndarray]:
        """Generate disk galaxy model."""
        r = np.random.exponential(1.0, n)
        phi = 2 * np.pi * np.random.uniform(0, 1, n)
        z = np.random.normal(0, 0.1, n)

        positions = np.column_stack([r * np.cos(phi), r * np.sin(phi), z])

        # Circular orbits with small random component
        v_circular = 1.0 / np.sqrt(r + 0.1)
        velocities = np.column_stack(
            [
                -v_circular * np.sin(phi),
                v_circular * np.cos(phi),
                np.random.normal(0, 0.01, n),
            ]
        )

        return positions, velocities

    def _build_tree(self) -> OctreeNode:
        """Build Barnes-Hut octree from current positions."""
        # Find bounding box
        min_coords = np.min(self.positions, axis=0)  # type: ignore[arg-type]
        max_coords = np.max(self.positions, axis=0)  # type: ignore[arg-type]
        center = (min_coords + max_coords) / 2
        size = np.max(max_coords - min_coords) * 1.01  # Slightly larger

        root = OctreeNode(center, size)

        for i in range(self.config.n_particles):
            root.insert(self.positions[i], self.masses[i], i)  # type: ignore[index]

        return root

    def _compute_forces_direct(self) -> np.ndarray:
        """Compute forces with O(N^2) direct summation."""
        n = self.config.n_particles
        forces = np.zeros((n, 3))

        for i in range(n):
            for j in range(i + 1, n):
                dx = self.positions[j] - self.positions[i]  # type: ignore[index]
                r = np.sqrt(np.sum(dx**2) + self.config.softening**2)

                if r > self.config.softening:
                    f = self.config.G * self.masses[i] * self.masses[j] / r**3  # type: ignore[index]
                    forces[i] += f * dx
                    forces[j] -= f * dx

        return forces

    def _compute_forces_tree(self) -> np.ndarray:
        """Compute forces with Barnes-Hut tree."""
        tree = self._build_tree()
        forces = np.zeros((self.config.n_particles, 3))

        for i in range(self.config.n_particles):
            forces[i] = tree.compute_force(
                self.positions[i],  # type: ignore[index]
                self.masses[i],  # type: ignore[index]
                self.config.theta,
                self.config.G,
                self.config.softening,
            )

        return forces

    def _integrate_euler(self, forces: np.ndarray) -> None:
        """Euler integration step."""
        dt = self.config.dt
        self.velocities += forces / self.masses[:, np.newaxis] * dt  # type: ignore[index]
        self.positions += self.velocities * dt  # type: ignore[operator]

    def _integrate_leapfrog(self, forces: np.ndarray) -> None:
        """Leapfrog (symplectic) integration."""
        dt = self.config.dt
        # Half step velocity
        self.velocities += forces / self.masses[:, np.newaxis] * dt / 2  # type: ignore[index]
        # Full step position
        self.positions += self.velocities * dt  # type: ignore[operator]
        # Recompute forces at new positions
        forces_new = self._compute_forces_tree()
        # Half step velocity
        self.velocities += forces_new / self.masses[:, np.newaxis] * dt / 2  # type: ignore[index]

    def _integrate_rk4(self, forces: np.ndarray) -> None:
        """Runge-Kutta 4th order integration."""
        dt = self.config.dt
        n = self.config.n_particles

        # Save initial state
        pos0 = self.positions.copy()  # type: ignore[union-attr]
        vel0 = self.velocities.copy()  # type: ignore[union-attr]

        # k1
        k1_v = forces / self.masses[:, np.newaxis]  # type: ignore[index]
        k1_r = vel0

        # k2
        self.positions = pos0 + k1_r * dt / 2
        forces2 = self._compute_forces_tree()
        k2_v = forces2 / self.masses[:, np.newaxis]  # type: ignore[index]
        k2_r = vel0 + k1_v * dt / 2

        # k3
        self.positions = pos0 + k2_r * dt / 2
        forces3 = self._compute_forces_tree()
        k3_v = forces3 / self.masses[:, np.newaxis]  # type: ignore[index]
        k3_r = vel0 + k2_v * dt / 2

        # k4
        self.positions = pos0 + k3_r * dt
        forces4 = self._compute_forces_tree()
        k4_v = forces4 / self.masses[:, np.newaxis]  # type: ignore[index]
        k4_r = vel0 + k3_v * dt

        # Combine
        self.velocities = vel0 + (k1_v + 2 * k2_v + 2 * k3_v + k4_v) * dt / 6
        self.positions = pos0 + (k1_r + 2 * k2_r + 2 * k3_r + k4_r) * dt / 6

    def _compute_energy(self) -> tuple[float, float, float]:
        """Compute kinetic, potential, and total energy."""
        # Kinetic energy
        ke = 0.5 * np.sum(self.masses * np.sum(self.velocities**2, axis=1))  # type: ignore[operator]

        # Potential energy
        pe = 0.0
        for i in range(self.config.n_particles):
            for j in range(i + 1, self.config.n_particles):
                r = np.sqrt(np.sum((self.positions[i] - self.positions[j]) ** 2))  # type: ignore[index]
                pe -= (
                    self.config.G
                    * self.masses[i]  # type: ignore[index]
                    * self.masses[j]  # type: ignore[index]
                    / max(r, self.config.softening)
                )

        return ke, pe, ke + pe

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute N-body simulation with Newton (or fallback).

        Returns:
            Dictionary with final state, energies, and trajectory data.
        """
        from src.simulations.newton_bridge import NewtonBridge
        bridge = NewtonBridge()

        if bridge.available:
            newton_config = {
                "type": "n_body",
                "n_particles": self.config.n_particles,
                "G": self.config.G,
                "softening": self.config.softening,
                "theta": self.config.theta,
                "dt": self.config.dt,
                "n_steps": self.config.n_steps,
                "integrator": self.config.integrator,
                "use_gpu": self.config.use_gpu,
                "domain_size": self.config.domain_size,
                "initial_distribution": self.config.initial_distribution,
            }
            if hypothesis:
                newton_config.update(hypothesis)
            result = bridge.run_simulation(newton_config)
            if result.get("status") == "success":
                result["pattern_id"] = self.PATTERN_ID
                return result

        # Fallback to legacy implementation
        trajectory = []
        energies = []

        # Record initial state
        ke, pe, total_e = self._compute_energy()
        energies.append({"step": 0, "kinetic": ke, "potential": pe, "total": total_e})

        for step in range(self.config.n_steps):
            # Compute forces
            forces = self._compute_forces_tree()

            # Integrate
            if self.config.integrator == "euler":
                self._integrate_euler(forces)
            elif self.config.integrator == "rk4":
                self._integrate_rk4(forces)
            else:  # leapfrog
                self._integrate_leapfrog(forces)

            # Record trajectory (every 10 steps)
            if step % 10 == 0:
                trajectory.append(self.positions.copy())  # type: ignore[union-attr]

            # Compute energy (every 10 steps)
            if step % 10 == 0:
                ke, pe, total_e = self._compute_energy()
                energies.append(
                    {"step": step + 1, "kinetic": ke, "potential": pe, "total": total_e}
                )

        final_ke, final_pe, final_total = self._compute_energy()
        energy_drift = abs(final_total - energies[0]["total"]) / abs(
            energies[0]["total"]
        )

        return {
            "pattern_id": self.PATTERN_ID,
            "final_positions": self.positions,
            "final_velocities": self.velocities,
            "masses": self.masses,
            "trajectory": np.array(trajectory),
            "energies": energies,
            "energy_drift": energy_drift,
            "virial_ratio": 2 * final_ke / abs(final_pe) if final_pe != 0 else 0,
            "com": np.average(self.positions, axis=0, weights=self.masses),  # type: ignore[arg-type]
            "mean_velocity": np.mean(self.velocities, axis=0),  # type: ignore[arg-type]
            "gpu_accelerated": self.gpu_available and self.config.use_gpu,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "pattern_id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "N-Body Gravity",
            "context": "When simulating gravitational interactions between N point masses "
            "where N > 1000, direct O(N²) methods become computationally prohibitive. "
            "Astronomical systems often exhibit hierarchical clustering (galaxies, clusters).",
            "forces": [
                "Accuracy vs computational cost: Direct summation is exact but O(N²)",
                "Long-term stability: Energy conservation critical for orbital dynamics",
                "Hierarchical structure: Distant clusters can be approximated as point masses",
                "GPU parallelism: Modern GPUs can accelerate both tree and direct methods",
            ],
            "solution": "Barnes-Hut tree algorithm partitions space into an octree. "
            "When computing force on a particle, if a tree node's angular size "
            "is smaller than threshold θ (opening angle), treat the entire subtree "
            "as a single point mass at its center of mass. This yields O(N log N) "
            "complexity. Symplectic integrators (leapfrog) preserve energy over long timescales.",
            "complexity": "O(N log N) with Barnes-Hut, O(N²) direct",
            "domain": "Astrophysics, celestial mechanics, cosmology",
            "parameters": [
                "G: Gravitational constant",
                "theta: Opening angle criterion (0 = exact, 1 = fast)",
                "softening: Plummer softening to avoid singularities",
                "integrator: Time integration scheme",
            ],
        }


# Alias for C4REQBER compatibility
NBodyPattern = NBodyGravity
