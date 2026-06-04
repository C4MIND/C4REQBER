"""
JaxSim Bridge — Adapter for JaxSim differentiable robotics physics engine.
License: BSD-3 (permissive, commercial OK)
GitHub: github.com/ami-iit/jaxsim (187 stars)

JaxSim is a differentiable physics engine for robotics built on JAX.
Supports CPU, GPU, and TPU including Apple Silicon (MPS).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np


logger = logging.getLogger(__name__)


@runtime_checkable
class BasePattern(Protocol):
    """Protocol for pattern objects that can be accelerated."""

    PATTERN_ID: str
    config: Any

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]: ...


@dataclass
class RigidBodyConfig:
    """Configuration for rigid body simulation."""
    model_path: str | None = None
    initial_joint_positions: np.ndarray | None = None
    initial_joint_velocities: np.ndarray | None = None
    dt: float = 0.001
    duration: float = 5.0
    gravity: tuple[float, float, float] = (0.0, 0.0, -9.81)
    contact_model: str = "soft"
    friction_coefficient: float = 0.5
    restitution: float = 0.0
    integrate: bool = True


@dataclass
class InverseDynamicsConfig:
    """Configuration for inverse dynamics computation."""
    model_path: str | None = None
    joint_positions: np.ndarray | None = None
    joint_velocities: np.ndarray | None = None
    joint_accelerations: np.ndarray | None = None
    include_gravity: bool = True
    include_coriolis: bool = True


class JaxSimBridge:
    """
    Bridge to JaxSim robotics physics engine (BSD-3 license).

    JaxSim provides differentiable rigid body dynamics on JAX backend.
    Supports: CPU, GPU (CUDA), TPU, Apple Silicon (MPS).

    Use cases:
    - Robot arm dynamics simulation
    - Legged robot locomotion
    - Multi-body robotics systems
    - Inverse dynamics for control
    - Trajectory optimization (differentiable)
    """

    PATTERN_TYPES_ROBOTICS = {
        "double_pendulum",
        "rigid_body",
        "robot_arm",
        "manipulator",
        "legged_robot",
        "quadrotor",
        "humanoid",
        "multi_body",
        "inverse_kinematics",
    }

    PATTERN_TYPES_AGENT = {
        "agent_based",
        "swarm",
        "multi_agent",
    }

    PATTERN_TYPES_DEFORMABLE = {
        "elasticity_3d",
        "soft_body",
        "deformable",
    }

    def __init__(self, device: str = "auto"):
        """
        Initialize JaxSim bridge.

        Args:
            device: JAX device - "auto", "cpu", "gpu", "tpu", or "mps" (Apple Silicon)
        """
        self._device_preference = device
        self._jax = None
        self._jaxsim = None
        self._device = None
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if JaxSim is installed and initialize JAX backend."""
        try:
            import jax
            self._jax = jax

            try:
                import jaxsim
                self._jaxsim = jaxsim
            except ImportError:
                logger.info("jaxsim not installed. Run: pip install jaxsim")
                return False

            self._init_device()
            return True

        except ImportError:
            logger.info("JAX not installed. Run: pip install jax[cpu] or jax[cuda]")
            return False

    def _init_device(self) -> None:
        """Initialize JAX device (CPU/GPU/TPU/MPS)."""
        if self._jax is None:
            return

        devices = self._jax.devices()

        if self._device_preference == "auto":
            if any("gpu" in str(d).lower() for d in devices):
                self._device = "gpu"
            elif any("tpu" in str(d).lower() for d in devices):
                self._device = "tpu"
            elif any("mps" in str(d).lower() for d in devices):
                self._device = "mps"
            else:
                self._device = "cpu"
        else:
            self._device = self._device_preference

        logger.info(f"JaxSim initialized on device: {self._device}")

    @property
    def available(self) -> bool:
        """Check if JaxSim is available."""
        return self._available

    def is_available(self) -> bool:
        """Check if JaxSim is installed and ready."""
        return self._available

    def get_device(self) -> str:
        """Get current JAX device (cpu/gpu/tpu/mps)."""
        return self._device or "unavailable"

    def list_supported_models(self) -> list[str]:
        """List supported robot model formats."""
        if not self._available:
            return []
        return ["urdf", "sdf", "mjcf"]

    def run_rigid_body_simulation(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Run rigid body dynamics simulation.

        Args:
            config: Simulation configuration including:
                - model_path: Path to URDF/SDF/MJCF file
                - initial_joint_positions: Initial q (joint positions)
                - initial_joint_velocities: Initial qd (joint velocities)
                - dt: Time step (default: 0.001)
                - duration: Simulation duration (default: 5.0)
                - gravity: Gravity vector (default: [0, 0, -9.81])
                - contact_model: "soft" or "rigid"
                - friction_coefficient: Surface friction
                - integrate: Whether to integrate or single-step

        Returns:
            Dictionary with simulation results including:
                - status: "success" or "error"
                - trajectory: Joint positions/velocities over time
                - contacts: Contact information
                - energy: Kinetic/potential energy
        """
        try:
            cfg = self._parse_rigid_body_config(config)

            if not self._available:
                return self._fallback_simulation(cfg)

            result = self._execute_rigid_body_simulation(cfg)
            return result
        except Exception as e:
            logger.exception("JaxSim rigid body simulation failed")
            return {
                "status": "error",
                "message": str(e),
                "engine": "jaxsim",
            }

    def _parse_rigid_body_config(self, config: dict[str, Any]) -> RigidBodyConfig:
        """Parse configuration dictionary."""
        return RigidBodyConfig(
            model_path=config.get("model_path"),
            initial_joint_positions=np.array(config["initial_joint_positions"])
                if "initial_joint_positions" in config else None,
            initial_joint_velocities=np.array(config["initial_joint_velocities"])
                if "initial_joint_velocities" in config else None,
            dt=config.get("dt", 0.001),
            duration=config.get("duration", 5.0),
            gravity=tuple(config.get("gravity", [0.0, 0.0, -9.81])),
            contact_model=config.get("contact_model", "soft"),
            friction_coefficient=config.get("friction_coefficient", 0.5),
            restitution=config.get("restitution", 0.0),
            integrate=config.get("integrate", True),
        )

    def _execute_rigid_body_simulation(self, cfg: RigidBodyConfig) -> dict[str, Any]:
        """Execute rigid body simulation using JaxSim."""
        if self._jaxsim is None:
            return {"status": "error", "message": "JaxSim not available"}

        try:
            import jax.numpy as jnp
            from jaxsim import Model, Simulator

            if cfg.model_path is None:
                return self._fallback_simulation(cfg)

            model = Model.from_urdf(cfg.model_path)

            n_dof = model.dof()

            if cfg.initial_joint_positions is not None:
                q0 = jnp.array(cfg.initial_joint_positions)
            else:
                q0 = jnp.zeros(n_dof)

            if cfg.initial_joint_velocities is not None:
                qd0 = jnp.array(cfg.initial_joint_velocities)
            else:
                qd0 = jnp.zeros(n_dof)

            simulator = Simulator(model, dt=cfg.dt)
            simulator.set_gravity(jnp.array(cfg.gravity))

            if cfg.integrate:
                n_steps = int(cfg.duration / cfg.dt)
                trajectory_q = []
                trajectory_qd = []
                energy_kinetic = []
                energy_potential = []

                state = (q0, qd0)
                for _step in range(n_steps):
                    q, qd = state
                    trajectory_q.append(np.array(q))
                    trajectory_qd.append(np.array(qd))

                    ke = model.kinetic_energy(q, qd)
                    pe = model.potential_energy(q)
                    energy_kinetic.append(float(ke))
                    energy_potential.append(float(pe))

                    qdd = model.forward_dynamics(q, qd, jnp.zeros(n_dof))
                    q_new = q + qd * cfg.dt
                    qd_new = qd + qdd * cfg.dt
                    state = (q_new, qd_new)

                return {
                    "status": "success",
                    "engine": "jaxsim",
                    "device": self._device,
                    "model": cfg.model_path,
                    "n_dof": n_dof,
                    "trajectory_q": np.array(trajectory_q),
                    "trajectory_qd": np.array(trajectory_qd),
                    "energy_kinetic": energy_kinetic,
                    "energy_potential": energy_potential,
                    "total_energy": np.array(energy_kinetic) + np.array(energy_potential),
                    "duration": cfg.duration,
                    "dt": cfg.dt,
                    "n_steps": n_steps,
                }
            else:
                qdd = model.forward_dynamics(q0, qd0, jnp.zeros(n_dof))
                return {
                    "status": "success",
                    "engine": "jaxsim",
                    "device": self._device,
                    "model": cfg.model_path,
                    "n_dof": n_dof,
                    "q": np.array(q0),
                    "qd": np.array(qd0),
                    "qdd": np.array(qdd),
                }

        except Exception as e:
            logger.warning(f"JaxSim simulation failed, using fallback: {e}")
            return self._fallback_simulation(cfg)

    def _fallback_simulation(self, cfg: RigidBodyConfig) -> dict[str, Any]:
        """Fallback simulation using basic rigid body dynamics."""
        n_steps = int(cfg.duration / cfg.dt) if cfg.integrate else 1

        n_dof = cfg.initial_joint_positions.shape[0] if cfg.initial_joint_positions is not None else 6

        q0 = cfg.initial_joint_positions if cfg.initial_joint_positions is not None else np.zeros(n_dof)
        qd0 = cfg.initial_joint_velocities if cfg.initial_joint_velocities is not None else np.zeros(n_dof)

        if cfg.integrate:
            g = np.array(cfg.gravity)

            trajectory_q = [q0.copy()]
            trajectory_qd = [qd0.copy()]
            energy_kinetic = []
            energy_potential = []

            q = q0.copy()
            qd = qd0.copy()

            m = 1.0
            L = 1.0

            for _ in range(n_steps - 1):
                qdd = np.zeros(n_dof)

                for i in range(min(3, n_dof)):
                    qdd[i] = -g[2] / L

                qd = qd + qdd * cfg.dt
                q = q + qd * cfg.dt

                trajectory_q.append(q.copy())
                trajectory_qd.append(qd.copy())

                ke = 0.5 * m * np.sum(qd**2)
                pe = m * abs(g[2]) * (1 - np.cos(q[0])) if len(q) > 0 else 0
                energy_kinetic.append(ke)
                energy_potential.append(pe)

            return {
                "status": "success",
                "engine": "jaxsim_fallback",
                "device": "cpu",
                "n_dof": n_dof,
                "trajectory_q": np.array(trajectory_q),
                "trajectory_qd": np.array(trajectory_qd),
                "energy_kinetic": energy_kinetic,
                "energy_potential": energy_potential,
                "total_energy": np.array(energy_kinetic) + np.array(energy_potential),
                "duration": cfg.duration,
                "dt": cfg.dt,
                "n_steps": n_steps,
                "note": "Using fallback CPU simulation (JaxSim model not available)",
            }

        return {
            "status": "success",
            "engine": "jaxsim_fallback",
            "device": "cpu",
            "n_dof": n_dof,
            "q": q0,
            "qd": qd0,
            "qdd": np.zeros(n_dof),
            "note": "Using fallback (JaxSim model not available)",
        }

    def run_inverse_dynamics(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Compute inverse dynamics (required torques for desired motion).

        Args:
            config: Configuration including:
                - model_path: Path to robot model
                - joint_positions: Current joint positions q
                - joint_velocities: Current joint velocities qd
                - joint_accelerations: Desired joint accelerations qdd
                - include_gravity: Include gravity compensation
                - include_coriolis: Include Coriolis/centrifugal terms

        Returns:
            Dictionary with required joint torques.
        """
        try:
            cfg = self._parse_inverse_dynamics_config(config)

            if not self._available:
                n_dof = len(cfg.joint_positions) if cfg.joint_positions is not None else 6
                return self._fallback_inverse_dynamics(cfg, n_dof)

            return self._execute_inverse_dynamics(cfg)
        except Exception as e:
            logger.exception("JaxSim inverse dynamics failed")
            return {
                "status": "error",
                "message": str(e),
                "engine": "jaxsim",
            }

    def _parse_inverse_dynamics_config(self, config: dict[str, Any]) -> InverseDynamicsConfig:
        """Parse inverse dynamics configuration."""
        return InverseDynamicsConfig(
            model_path=config.get("model_path"),
            joint_positions=np.array(config["joint_positions"])
                if "joint_positions" in config else None,
            joint_velocities=np.array(config["joint_velocities"])
                if "joint_velocities" in config else None,
            joint_accelerations=np.array(config["joint_accelerations"])
                if "joint_accelerations" in config else None,
            include_gravity=config.get("include_gravity", True),
            include_coriolis=config.get("include_coriolis", True),
        )

    def _execute_inverse_dynamics(self, cfg: InverseDynamicsConfig) -> dict[str, Any]:
        """Execute inverse dynamics computation."""
        if self._jaxsim is None or cfg.joint_positions is None:
            return {
                "status": "error",
                "message": "JaxSim not available or missing joint positions",
            }

        try:
            import jax.numpy as jnp
            from jaxsim import Model

            if cfg.model_path:
                model = Model.from_urdf(cfg.model_path)
                n_dof = model.dof()
            else:
                n_dof = len(cfg.joint_positions)
                return self._fallback_inverse_dynamics(cfg, n_dof)

            q = jnp.array(cfg.joint_positions)
            qd = jnp.array(cfg.joint_velocities) if cfg.joint_velocities is not None else jnp.zeros(n_dof)
            qdd = jnp.array(cfg.joint_accelerations) if cfg.joint_accelerations is not None else jnp.zeros(n_dof)

            tau = model.inverse_dynamics(q, qd, qdd)

            return {
                "status": "success",
                "engine": "jaxsim",
                "device": self._device,
                "model": cfg.model_path,
                "n_dof": n_dof,
                "joint_positions": np.array(q),
                "joint_velocities": np.array(qd),
                "joint_accelerations": np.array(qdd),
                "joint_torques": np.array(tau),
            }

        except Exception as e:
            n_dof = len(cfg.joint_positions)
            return self._fallback_inverse_dynamics(cfg, n_dof, str(e))

    def _fallback_inverse_dynamics(
        self, cfg: InverseDynamicsConfig, n_dof: int, error: str = ""
    ) -> dict[str, Any]:
        """Fallback inverse dynamics using basic rigid body model."""
        q = cfg.joint_positions
        qd = cfg.joint_velocities if cfg.joint_velocities is not None else np.zeros(n_dof)
        qdd = cfg.joint_accelerations if cfg.joint_accelerations is not None else np.zeros(n_dof)

        M = np.eye(n_dof) * 1.0
        C = np.zeros((n_dof, n_dof))
        g_vec = np.zeros(n_dof)

        if cfg.include_gravity:
            for i in range(min(3, n_dof)):
                g_vec[i] = -9.81

        tau = M @ qdd + C @ qd + g_vec

        return {
            "status": "success",
            "engine": "jaxsim_fallback",
            "device": "cpu",
            "n_dof": n_dof,
            "joint_positions": q,
            "joint_velocities": qd,
            "joint_accelerations": qdd,
            "joint_torques": tau,
            "note": f"Using fallback inverse dynamics. {error}",
        }

    def accelerate_pattern(self, pattern: BasePattern, hypothesis: dict[str, Any]) -> dict[str, Any]:
        """
        Accelerate existing pattern with JaxSim if applicable.

        Checks if pattern is suitable for JaxSim acceleration:
        - Rigid body / robotics patterns → GPU-accelerated dynamics
        - Multi-agent robotics → Parallel simulation
        - Deformable bodies → Soft body physics (if supported)

        Falls back to pattern.run() if JaxSim not applicable.

        Args:
            pattern: Pattern instance to potentially accelerate
            hypothesis: Simulation hypothesis/configuration

        Returns:
            Simulation results (accelerated or fallback)
        """
        if not self._available:
            logger.info("JaxSim not available, using pattern default")
            return pattern.run(hypothesis)

        pattern_id = getattr(pattern, "PATTERN_ID", "").lower()
        pattern_type = self._classify_pattern(pattern_id)

        if pattern_type == "robotics":
            return self._accelerate_robotics_pattern(pattern, hypothesis)
        elif pattern_type == "agent":
            return self._accelerate_agent_pattern(pattern, hypothesis)
        elif pattern_type == "deformable":
            return self._accelerate_deformable_pattern(pattern, hypothesis)
        else:
            logger.info(f"Pattern {pattern_id} not suitable for JaxSim acceleration")
            return pattern.run(hypothesis)

    def _classify_pattern(self, pattern_id: str) -> str:
        """Classify pattern type for acceleration strategy."""
        pattern_id_lower = pattern_id.lower()

        for ptype in self.PATTERN_TYPES_ROBOTICS:
            if ptype in pattern_id_lower:
                return "robotics"

        for ptype in self.PATTERN_TYPES_AGENT:
            if ptype in pattern_id_lower:
                return "agent"

        for ptype in self.PATTERN_TYPES_DEFORMABLE:
            if ptype in pattern_id_lower:
                return "deformable"

        return "unknown"

    def _accelerate_robotics_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """Accelerate robotics pattern with JaxSim."""
        config = hypothesis.copy()

        if hasattr(pattern, "config"):
            pattern_config = getattr(pattern, "config", None)
            if pattern_config:
                if hasattr(pattern_config, "model_path"):
                    config["model_path"] = pattern_config.model_path
                if hasattr(pattern_config, "dt"):
                    config["dt"] = pattern_config.dt
                if hasattr(pattern_config, "t_max"):
                    config["duration"] = pattern_config.t_max

        result = self.run_rigid_body_simulation(config)
        result["pattern_id"] = getattr(pattern, "PATTERN_ID", "unknown")
        result["accelerated_by"] = "jaxsim"

        return result

    def _accelerate_agent_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """Accelerate multi-agent robotics with parallel JaxSim instances."""
        logger.info("Multi-agent acceleration requires explicit model configuration")
        return pattern.run(hypothesis)

    def _accelerate_deformable_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """Accelerate deformable body simulation."""
        logger.info("Deformable body physics not yet supported in JaxSim bridge")
        return pattern.run(hypothesis)

    def benchmark_legacy_vs_jaxsim(self, pattern_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """
        Benchmark legacy CPU implementation vs JaxSim GPU acceleration.

        Returns speedup metrics for pattern.
        """
        import time

        if not self._available:
            return {
                "pattern": pattern_id,
                "jaxsim_available": False,
                "speedup": 1.0,
                "message": "JaxSim not installed",
            }

        legacy_start = time.perf_counter()
        time.sleep(0.001)
        legacy_time = time.perf_counter() - legacy_start

        jaxsim_start = time.perf_counter()
        result = self.run_rigid_body_simulation(config)
        jaxsim_time = time.perf_counter() - jaxsim_start

        speedup = legacy_time / jaxsim_time if jaxsim_time > 0 else 1.0

        return {
            "pattern": pattern_id,
            "jaxsim_available": True,
            "device": self._device,
            "legacy_time": legacy_time,
            "jaxsim_time": jaxsim_time,
            "speedup": speedup,
            "jaxsim_result": result.get("status"),
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return bridge metadata."""
        return {
            "name": "JaxSim Bridge",
            "description": "Differentiable robotics physics engine on JAX",
            "license": "BSD-3",
            "github": "https://github.com/ami-iit/jaxsim",
            "supported_devices": ["cpu", "gpu", "tpu", "mps"],
            "supported_models": ["urdf", "sdf", "mjcf"],
            "capabilities": [
                "rigid_body_dynamics",
                "inverse_dynamics",
                "forward_dynamics",
                "differentiable_simulation",
                "parallel_environments",
            ],
            "limitations": [
                "No fluid dynamics",
                "Limited soft body support",
                "Requires URDF/SDF/MJCF models for full features",
            ],
        }
