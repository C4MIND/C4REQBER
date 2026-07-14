# Migrated to Newton Physics (2025) — github.com/newton-physics/newton — Apache 2.0 License
"""
Pattern 21: Rigid Body Dynamics

Christopher Alexander Structure:
- Context: Simulating solid objects that maintain their shape under motion and collision.
  Required for robotics, vehicle dynamics, and game physics.
- Forces:
  * Rotation representation: Euler angles have singularities, matrices drift
  * Numerical stability of rotational dynamics
  * Handling contacts and constraints
  * Conservation of angular momentum
- Solution: Quaternion representation for rotation, implicit integration for stability,
  constraint solvers for contacts. Uses Lie group structure of SO(3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


try:
    from .base import (
        BaseConfig,
        BasePattern,
        GPUMixin,
        quaternion_conjugate,
        quaternion_multiply,
        quaternion_rotate_vector,
        rotation_matrix_from_quaternion,
    )
except ImportError:
    from .base import (
        BaseConfig,
        BasePattern,
        GPUMixin,
        quaternion_multiply,
        rotation_matrix_from_quaternion,
    )


@dataclass
class RigidBodyConfig(BaseConfig):
    """Configuration for Rigid Body simulation."""

    n_bodies: int = 10
    dt: float = 0.01
    n_steps: int = 1000
    gravity: np.ndarray = None  # type: ignore[assignment]
    damping: float = 0.001
    use_quaternion: bool = True  # Use quaternions vs rotation matrices
    constraint_solver: str = "sequential"  # "sequential", "pgs", "direct"
    friction_coefficient: float = 0.3
    restitution: float = 0.5

    def __post_init__(self) -> None:
        if self.gravity is None:
            self.gravity = np.array([0.0, -9.81, 0.0])  # type: ignore[unreachable]


@dataclass
class BodyState:
    """State of a single rigid body."""

    mass: float
    inertia: np.ndarray  # 3x3 inertia tensor in body frame
    position: np.ndarray  # World position
    quaternion: np.ndarray  # Orientation [w, x, y, z]
    velocity: np.ndarray  # Linear velocity
    angular_velocity: np.ndarray  # Angular velocity in body frame

    def __post_init__(self) -> None:
        if isinstance(self.inertia, list):  # type: ignore[unreachable]
            self.inertia = np.array(self.inertia, dtype=float)  # type: ignore[unreachable]
        if isinstance(self.position, list):  # type: ignore[unreachable]
            self.position = np.array(self.position, dtype=float)  # type: ignore[unreachable]
        if isinstance(self.quaternion, list):  # type: ignore[unreachable]
            self.quaternion = np.array(self.quaternion, dtype=float)  # type: ignore[unreachable]
        if isinstance(self.velocity, list):  # type: ignore[unreachable]
            self.velocity = np.array(self.velocity, dtype=np.float64)  # type: ignore[unreachable]
        if isinstance(self.angular_velocity, list):  # type: ignore[unreachable]
            self.angular_velocity = np.array(self.angular_velocity, dtype=np.float64)  # type: ignore[unreachable]
        # Ensure all arrays are float64
        self.inertia = np.asarray(self.inertia, dtype=np.float64)
        self.position = np.asarray(self.position, dtype=np.float64)
        self.quaternion = np.asarray(self.quaternion, dtype=np.float64)
        self.velocity = np.asarray(self.velocity, dtype=np.float64)
        self.angular_velocity = np.asarray(self.angular_velocity, dtype=np.float64)


class RigidBody(BasePattern, GPUMixin):
    """
    Rigid body dynamics with quaternion rotation representation.
    Complexity: O(N) per step for unconstrained, O(N²) with contacts.
    """

    PATTERN_ID = "rigid_body_dynamics"
    PATTERN_VERSION = "6.5.0"

    def _validate_config(self) -> None:
        pass

    def __init__(self, config: RigidBodyConfig | None = None) -> None:
        BasePattern.__init__(self, config or RigidBodyConfig())
        GPUMixin.__init__(self)
        self.config: RigidBodyConfig = self.config
        self.bodies: list[BodyState] = []
        self.constraints: list[dict[str, Any]] = []
        self._initialize_bodies()

    def _initialize_bodies(self) -> None:
        """Initialize rigid bodies with random positions and orientations."""
        np.random.seed(42)

        for _i in range(self.config.n_bodies):
            mass = 1.0 + np.random.random()

            # Random inertia tensor (diagonal for simplicity)
            Ixx = mass * (0.1 + 0.1 * np.random.random())
            Iyy = mass * (0.1 + 0.1 * np.random.random())
            Izz = mass * (0.1 + 0.1 * np.random.random())
            inertia = np.diag([Ixx, Iyy, Izz])

            # Random position
            position = np.random.randn(3) * 2.0
            position[1] = abs(position[1]) + 1.0  # Start above ground

            # Random orientation (unit quaternion)
            theta = np.random.uniform(0, 2 * np.pi)
            axis = np.random.randn(3)
            axis = axis / np.linalg.norm(axis)
            quaternion = np.array(
                [
                    np.cos(theta / 2),
                    axis[0] * np.sin(theta / 2),
                    axis[1] * np.sin(theta / 2),
                    axis[2] * np.sin(theta / 2),
                ]
            )

            # Initial velocities
            velocity = np.random.randn(3) * 0.1
            angular_velocity = np.random.randn(3) * 0.5

            body = BodyState(
                mass=mass,
                inertia=inertia,
                position=position,
                quaternion=quaternion,
                velocity=velocity,
                angular_velocity=angular_velocity,
            )
            self.bodies.append(body)

        # Add ground plane constraint
        self.constraints.append(
            {"type": "plane", "normal": np.array([0, 1, 0]), "offset": 0.0}
        )

    def _quaternion_derivative(self, q: np.ndarray, omega: np.ndarray) -> np.ndarray:
        """
        Compute quaternion derivative from angular velocity.
        dq/dt = 0.5 * q * [0, omega]
        """
        omega_quat = np.array([0, omega[0], omega[1], omega[2]])
        return 0.5 * quaternion_multiply(q, omega_quat)

    def _integrate_quaternion(self, body: BodyState, dt: float) -> None:
        """Integrate quaternion using exponential map."""
        omega = body.angular_velocity
        omega_mag = np.linalg.norm(omega)

        if omega_mag > 1e-10:
            # Rotation quaternion for this timestep
            half_angle = omega_mag * dt / 2
            rotation_quat = np.array(
                [
                    np.cos(half_angle),
                    omega[0] / omega_mag * np.sin(half_angle),
                    omega[1] / omega_mag * np.sin(half_angle),
                    omega[2] / omega_mag * np.sin(half_angle),
                ]
            )
            body.quaternion = quaternion_multiply(rotation_quat, body.quaternion)

        # Normalize to prevent drift
        body.quaternion = body.quaternion / np.linalg.norm(body.quaternion)

    def _get_rotation_matrix(self, body: BodyState) -> np.ndarray:
        """Get rotation matrix from quaternion."""
        return rotation_matrix_from_quaternion(body.quaternion)

    def _get_world_inertia(self, body: BodyState) -> np.ndarray:
        """Get inertia tensor in world coordinates."""
        R = self._get_rotation_matrix(body)
        return R @ body.inertia @ R.T  # type: ignore[no-any-return]

    def _compute_forces(self, body: BodyState) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute external forces and torques on body.
        Returns (force, torque) in world coordinates.
        """
        # Gravity
        force = body.mass * self.config.gravity

        # Damping
        force -= self.config.damping * body.velocity

        # Torque from angular velocity damping
        torque_body = -self.config.damping * body.angular_velocity
        R = self._get_rotation_matrix(body)
        torque_world = R @ torque_body

        return force, torque_world

    def _check_collision(self, body: BodyState) -> dict[str, Any] | None:
        """Check collision with ground plane."""
        # Simple sphere-ground collision
        radius = 0.5  # Approximate radius
        penetration = radius - body.position[1]

        if penetration > 0:
            contact_point = body.position.copy()
            contact_point[1] -= radius

            return {
                "body_idx": self.bodies.index(body),
                "penetration": penetration,
                "normal": np.array([0, 1, 0]),
                "point": contact_point,
                "constraint": self.constraints[0],
            }
        return None

    def _solve_contact(self, collision: dict[str, Any]) -> None:
        """Solve contact constraint using impulse-based response."""
        body = self.bodies[collision["body_idx"]]
        n = collision["normal"]

        # Relative velocity at contact point
        r = collision["point"] - body.position
        v_contact = body.velocity + np.cross(body.angular_velocity, r)
        v_rel = np.dot(v_contact, n)

        if v_rel > 0:  # Separating
            return

        # Effective mass
        I_inv = np.linalg.inv(self._get_world_inertia(body))
        r_cross_n = np.cross(r, n)
        effective_mass = 1.0 / (1.0 / body.mass + np.dot(r_cross_n, I_inv @ r_cross_n))

        # Restitution
        restitution = self.config.restitution
        j_normal = -(1 + restitution) * v_rel * effective_mass

        # Apply impulse
        impulse = j_normal * n
        body.velocity += impulse / body.mass
        body.angular_velocity += I_inv @ np.cross(r, impulse)

        # Position correction
        body.position += collision["penetration"] * n * 0.5

    def _step(self, dt: float) -> None:
        """Single integration step."""
        # Semi-implicit Euler integration
        for body in self.bodies:
            # Compute forces
            force, torque = self._compute_forces(body)

            # Linear dynamics
            acceleration = force / body.mass
            body.velocity += acceleration * dt
            body.position += body.velocity * dt

            # Angular dynamics (world frame)
            I_world = self._get_world_inertia(body)
            omega = body.angular_velocity

            # Euler's equation: I * alpha + omega x (I * omega) = tau
            # alpha = I^(-1) * (tau - omega x (I * omega))
            I_inv = np.linalg.inv(I_world)
            gyroscopic = np.cross(omega, I_world @ omega)
            alpha = I_inv @ (torque - gyroscopic)

            body.angular_velocity += alpha * dt

            # Integrate orientation
            self._integrate_quaternion(body, dt)

        # Collision detection and response
        collisions = []
        for body in self.bodies:
            collision = self._check_collision(body)
            if collision:
                collisions.append(collision)

        # Solve contacts
        for _ in range(10):  # Iterations for constraint satisfaction
            for collision in collisions:
                self._solve_contact(collision)

    def _compute_energy(self) -> tuple[float, float, float]:
        """Compute total mechanical energy."""
        kinetic = 0.0
        potential = 0.0

        for body in self.bodies:
            # Linear KE
            kinetic += 0.5 * body.mass * np.dot(body.velocity, body.velocity)

            # Angular KE
            I_world = self._get_world_inertia(body)
            kinetic += 0.5 * np.dot(
                body.angular_velocity, I_world @ body.angular_velocity
            )

            # Gravitational PE
            potential -= body.mass * np.dot(self.config.gravity, body.position)

        return kinetic, potential, kinetic + potential

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute rigid body simulation with Newton (or fallback).

        Returns:
            Dictionary with final states, energy history, and constraint violations.
        """
        from src.simulations.newton_bridge import NewtonBridge
        bridge = NewtonBridge()

        if bridge.available:
            newton_config = {
                "type": "rigid_body",
                "n_bodies": self.config.n_bodies,
                "dt": self.config.dt,
                "n_steps": self.config.n_steps,
                "gravity": self.config.gravity.tolist() if self.config.gravity is not None else [0.0, -9.81, 0.0],
                "damping": self.config.damping,
                "use_quaternion": self.config.use_quaternion,
                "constraint_solver": self.config.constraint_solver,
                "friction_coefficient": self.config.friction_coefficient,
                "restitution": self.config.restitution,
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
        constraint_violations = []

        # Record initial state
        ke, pe, total = self._compute_energy()
        energies.append({"step": 0, "kinetic": ke, "potential": pe, "total": total})

        for step in range(self.config.n_steps):
            self._step(self.config.dt)

            # Record trajectory (every 10 steps)
            if step % 10 == 0:
                state = {
                    "positions": np.array([b.position for b in self.bodies]),
                    "quaternions": np.array([b.quaternion for b in self.bodies]),
                    "velocities": np.array([b.velocity for b in self.bodies]),
                }
                trajectory.append(state)

            # Record energy
            if step % 10 == 0:
                ke, pe, total = self._compute_energy()
                energies.append(
                    {"step": step + 1, "kinetic": ke, "potential": pe, "total": total}
                )

            # Track constraint violations
            violations = 0
            for body in self.bodies:
                if body.position[1] < 0.5:  # Below ground
                    violations += 1
            constraint_violations.append(violations)

        # Compile results
        final_positions = np.array([b.position for b in self.bodies])
        final_velocities = np.array([b.velocity for b in self.bodies])
        final_quaternions = np.array([b.quaternion for b in self.bodies])

        return {
            "pattern_id": self.PATTERN_ID,
            "final_positions": final_positions,
            "final_velocities": final_velocities,
            "final_quaternions": final_quaternions,
            "final_angular_velocities": np.array(
                [b.angular_velocity for b in self.bodies]
            ),
            "trajectory": trajectory,
            "energies": energies,
            "constraint_violations": constraint_violations,
            "energy_drift": abs(energies[-1]["total"] - energies[0]["total"])
            / abs(energies[0]["total"]),
            "total_collisions": sum(constraint_violations),
            "mean_position": np.mean(final_positions, axis=0),
            "mean_velocity": np.mean(final_velocities, axis=0),
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "pattern_id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Rigid Body Dynamics",
            "context": "When simulating solid objects that maintain their shape under motion, "
            "such as robots, vehicles, or game objects. Requires handling rotation "
            "in 3D space without singularities or numerical drift.",
            "forces": [
                "Rotation representation: Euler angles have gimbal lock singularities",
                "Numerical stability: Rotation matrices drift from orthogonality over time",
                "Contact handling: Collisions require impulse-based constraint solving",
                "Angular momentum conservation: Critical for long-term stability",
                "Gyroscopic effects: Cross terms in Euler's equations",
            ],
            "solution": "Quaternions represent rotations compactly without singularities. "
            "The Lie algebra so(3) allows correct integration of angular velocity. "
            "Semi-implicit Euler integration provides stability for stiff contacts. "
            "Iterative constraint solvers (PGS/SOR) handle multiple simultaneous contacts. "
            "Exponential map integration preserves quaternion unit norm.",
            "complexity": "O(N) unconstrained, O(N²) with contacts, O(N³) with direct solver",
            "domain": "Robotics, game physics, vehicle dynamics, mechanical engineering",
            "parameters": [
                "dt: Time step size",
                "damping: Velocity decay for stability",
                "friction_coefficient: Coulomb friction",
                "restitution: Bounciness factor",
            ],
        }
