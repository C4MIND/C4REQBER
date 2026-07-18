"""
Schr Bridge — Adapter for Schr quantum mechanics engine (MIT license).
GitHub: github.com/qiboteam/schr

Schr is a JAX-based GPU-accelerated Quantum Mechanics and QED Simulator.
Supports time-dependent Schrödinger equation, QED light-matter interactions.
License: MIT (permissive, commercial OK)
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
class SchrodingerConfig:
    """Configuration for Schrödinger equation solver."""

    n_points: int = 128
    domain_size: float = 10.0
    dt: float = 0.001
    duration: float = 1.0
    potential_type: str = "harmonic"
    potential_strength: float = 1.0
    initial_state: str = "gaussian"
    boundary_conditions: str = "periodic"
    integrate: bool = True


@dataclass
class QEDConfig:
    """Configuration for QED simulation."""

    n_modes: int = 8
    n_photons_max: int = 4
    n_levels: int = 4
    coupling_strength: float = 1.0
    detuning: float = 0.0
    dt: float = 0.01
    duration: float = 10.0
    initial_state: str = "ground"


class SchrBridge:
    """
    Bridge to Schr quantum mechanics engine (MIT license).

    Schr provides JAX-accelerated quantum mechanics simulations:
    - Time-dependent Schrödinger equation (split-step Fourier)
    - QED simulations with Fock space representation
    - GPU acceleration via JAX

    Use cases:
    - Quantum dynamics simulation
    - Light-matter interaction (cavity QED)
    - Quantum computing simulation
    - Atomic physics modeling
    """

    PATTERN_TYPES_QUANTUM = {
        "schrodinger",
        "quantum_dynamics",
        "wave_function",
        "quantum_well",
        "tunneling",
        "harmonic_oscillator",
        "double_well",
        "quantum_scatter",
        "bose_hubbard",
    }

    PATTERN_TYPES_QED = {
        "qed",
        "cavity_qed",
        "jaynes_cummings",
        "dicke_model",
        "light_matter",
        "quantum_optics",
        "rabi_oscillations",
    }

    PATTERN_TYPES_QUANTUM_COMPUTING = {
        "quantum_circuit",
        "qubit_dynamics",
        "quantum_gate",
        "entanglement",
        "bell_state",
        "quantum_error",
    }

    def __init__(self, device: str = "auto") -> None:
        """
        Initialize Schr bridge.

        Args:
            device: JAX device - "auto", "cpu", "gpu", "tpu"
        """
        self._device_preference = device
        self._jax = None
        self._schr = None
        self._device = None
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Schr is installed and initialize JAX backend."""
        try:
            import jax

            self._jax = jax

            try:
                import schr

                self._schr = schr
            except ImportError:
                logger.info("schr not installed. Run: pip install schr")
                return False

            self._init_device()
            return True

        except ImportError:
            logger.info("JAX not installed. Run: pip install jax[cpu] or jax[cuda]")
            return False

    def _init_device(self) -> None:
        """Initialize JAX device (CPU/GPU/TPU)."""
        if self._jax is None:
            return

        devices = self._jax.devices()

        if self._device_preference == "auto":
            if any("gpu" in str(d).lower() for d in devices):
                self._device = "gpu"
            elif any("tpu" in str(d).lower() for d in devices):
                self._device = "tpu"
            else:
                self._device = "cpu"
        else:
            self._device = self._device_preference

        logger.info(f"Schr initialized on device: {self._device}")

    @property
    def available(self) -> bool:
        """Check if Schr is available."""
        return self._available

    def is_available(self) -> bool:
        """Check if Schr is installed and ready."""
        return self._available

    def get_device(self) -> str:
        """Get current JAX device (cpu/gpu/tpu)."""
        return self._device or "unavailable"

    def run_schrodinger(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Run time-dependent Schrödinger equation solver.

        Uses split-step Fourier method for efficient wave propagation.

        Args:
            config: Simulation configuration including:
                - n_points: Grid resolution (default: 128)
                - domain_size: Spatial domain size (default: 10.0)
                - dt: Time step (default: 0.001)
                - duration: Simulation duration (default: 1.0)
                - potential_type: "harmonic", "well", "barrier", "custom"
                - potential_strength: Potential amplitude
                - initial_state: "gaussian", "plane_wave", "coherent"
                - boundary_conditions: "periodic", "reflecting"
                - integrate: Run full trajectory or single step

        Returns:
            Dictionary with simulation results:
                - status: "success" or "error"
                - wave_function: Complex wave function array
                - probability_density: |psi|^2
                - energy: Expectation values
                - trajectory: Time evolution data
        """
        try:
            cfg = self._parse_schrodinger_config(config)

            if not self._available:
                return self._fallback_schrodinger(cfg)

            result = self._execute_schrodinger(cfg)
            return result
        except Exception as e:
            logger.exception("Schrödinger simulation failed")
            return {
                "status": "error",
                "message": str(e),
                "engine": "schr",
            }

    def _parse_schrodinger_config(self, config: dict[str, Any]) -> SchrodingerConfig:
        """Parse configuration dictionary."""
        return SchrodingerConfig(
            n_points=config.get("n_points", 128),
            domain_size=config.get("domain_size", 10.0),
            dt=config.get("dt", 0.001),
            duration=config.get("duration", 1.0),
            potential_type=config.get("potential_type", "harmonic"),
            potential_strength=config.get("potential_strength", 1.0),
            initial_state=config.get("initial_state", "gaussian"),
            boundary_conditions=config.get("boundary_conditions", "periodic"),
            integrate=config.get("integrate", True),
        )

    def _execute_schrodinger(self, cfg: SchrodingerConfig) -> dict[str, Any]:
        """Execute Schrödinger simulation using Schr."""
        if self._schr is None:
            return {"status": "error", "message": "Schr not available"}

        try:
            from schr import SchrodingerSolver

            solver = SchrodingerSolver(
                n_points=cfg.n_points,
                domain_size=cfg.domain_size,
                dt=cfg.dt,
                potential_type=cfg.potential_type,
                potential_strength=cfg.potential_strength,
            )

            psi0 = self._create_initial_state(cfg)

            if cfg.integrate:
                n_steps = int(cfg.duration / cfg.dt)
                trajectory = []
                energies = []
                positions = []
                momenta = []

                psi = psi0
                for _step in range(n_steps):
                    psi = solver.step(psi)
                    trajectory.append(np.array(psi))

                    energy = solver.energy(psi)
                    energies.append(float(energy))

                    pos = solver.position_expectation(psi)
                    positions.append(float(pos))

                    mom = solver.momentum_expectation(psi)
                    momenta.append(float(mom))

                times = np.linspace(0, cfg.duration, n_steps)

                return {
                    "status": "success",
                    "engine": "schr",
                    "engine_truth": "schr",
                    "executed": True,
                    "device": self._device,
                    "n_points": cfg.n_points,
                    "wave_function": np.array(psi),
                    "probability_density": np.abs(np.array(psi)) ** 2,
                    "trajectory": np.array(trajectory),
                    "energy": energies,
                    "position_expectation": positions,
                    "momentum_expectation": momenta,
                    "times": times,
                    "duration": cfg.duration,
                    "dt": cfg.dt,
                    "n_steps": n_steps,
                    "potential_type": cfg.potential_type,
                }
            else:
                psi = solver.step(psi0)
                energy = solver.energy(psi)

                return {
                    "status": "success",
                    "engine": "schr",
                    "engine_truth": "schr",
                    "executed": True,
                    "device": self._device,
                    "n_points": cfg.n_points,
                    "wave_function": np.array(psi),
                    "probability_density": np.abs(np.array(psi)) ** 2,
                    "energy": float(energy),
                    "potential_type": cfg.potential_type,
                }

        except Exception as e:
            logger.warning(f"Schr simulation failed, using fallback: {e}")
            return self._fallback_schrodinger(cfg)

    def _create_initial_state(self, cfg: SchrodingerConfig) -> Any:
        """Create initial wave function."""
        import jax.numpy as jnp

        x = jnp.linspace(-cfg.domain_size / 2, cfg.domain_size / 2, cfg.n_points)
        dx = cfg.domain_size / cfg.n_points

        if cfg.initial_state == "gaussian":
            sigma = cfg.domain_size / 10
            x0 = 0.0
            k0 = 2.0
            psi = jnp.exp(-((x - x0) ** 2) / (2 * sigma**2)) * jnp.exp(1j * k0 * x)
        elif cfg.initial_state == "plane_wave":
            k0 = 2.0
            psi = jnp.exp(1j * k0 * x)
        elif cfg.initial_state == "coherent":
            sigma = cfg.domain_size / 10
            x0 = cfg.domain_size / 4
            psi = jnp.exp(-((x - x0) ** 2) / (2 * sigma**2))
        else:
            psi = jnp.ones(cfg.n_points, dtype=complex)

        norm = jnp.sqrt(jnp.sum(jnp.abs(psi) ** 2) * dx)
        return psi / norm

    def _fallback_schrodinger(self, cfg: SchrodingerConfig) -> dict[str, Any]:
        """Fallback simulation using split-step Fourier method."""
        n_steps = int(cfg.duration / cfg.dt) if cfg.integrate else 1

        x = np.linspace(-cfg.domain_size / 2, cfg.domain_size / 2, cfg.n_points)
        dx = cfg.domain_size / cfg.n_points
        k = 2 * np.pi * np.fft.fftfreq(cfg.n_points, dx)

        psi = self._create_initial_state_numpy(cfg, x, dx)

        if cfg.potential_type == "harmonic":
            V = 0.5 * cfg.potential_strength * x**2
        elif cfg.potential_type == "well":
            V = np.where(np.abs(x) < cfg.domain_size / 4, 0, cfg.potential_strength * 10)
        elif cfg.potential_type == "barrier":
            V = np.where(np.abs(x) < cfg.domain_size / 20, cfg.potential_strength * 5, 0)
        else:
            V = np.zeros(cfg.n_points)

        kinetic_phase = np.exp(-1j * 0.5 * k**2 * cfg.dt)
        potential_phase = np.exp(-1j * V * cfg.dt)

        if cfg.integrate:
            trajectory = [psi.copy()]
            energies = []
            positions = []
            momenta = []

            for _ in range(n_steps - 1):
                psi = np.fft.ifft(kinetic_phase * np.fft.fft(psi))
                psi = potential_phase * psi
                psi = np.fft.ifft(kinetic_phase * np.fft.fft(psi))
                trajectory.append(psi.copy())

                prob = np.abs(psi) ** 2
                energy = (
                    np.sum(prob * V) * dx
                    + 0.5 * np.sum(k**2 * np.abs(np.fft.fft(psi)) ** 2) * dx / cfg.n_points
                )
                energies.append(float(np.real(energy)))

                pos = np.sum(x * prob) * dx
                positions.append(float(pos))

                momentum_space = np.fft.fft(psi)
                mom = np.sum(k * np.abs(momentum_space) ** 2) * dx / cfg.n_points
                momenta.append(float(np.real(mom)))

            times = np.linspace(0, cfg.duration, n_steps)

            return {
                "status": "partial",
                "engine": "schr_fallback",
                "backend": "numpy_split_operator",
                "engine_truth": "not_schr",
                "executed": True,
                "stub": False,
                "accelerated": False,
                "device": "cpu",
                "n_points": cfg.n_points,
                "wave_function": psi,
                "probability_density": np.abs(psi) ** 2,
                "trajectory": np.array(trajectory),
                "energy": energies,
                "position_expectation": positions,
                "momentum_expectation": momenta,
                "times": times,
                "duration": cfg.duration,
                "dt": cfg.dt,
                "n_steps": n_steps,
                "potential_type": cfg.potential_type,
                "note": "NumPy split-operator fallback — not Schr GPU engine",
            }

        psi = np.fft.ifft(kinetic_phase * np.fft.fft(psi))
        psi = potential_phase * psi
        psi = np.fft.ifft(kinetic_phase * np.fft.fft(psi))

        prob = np.abs(psi) ** 2
        energy = np.sum(prob * V) * dx

        return {
            "status": "partial",
            "engine": "schr_fallback",
            "backend": "numpy_split_operator",
            "engine_truth": "not_schr",
            "executed": True,
            "stub": False,
            "accelerated": False,
            "device": "cpu",
            "n_points": cfg.n_points,
            "wave_function": psi,
            "probability_density": prob,
            "energy": float(np.real(energy)),
            "potential_type": cfg.potential_type,
            "note": "NumPy fallback — not Schr GPU engine",
        }

    def _create_initial_state_numpy(
        self, cfg: SchrodingerConfig, x: np.ndarray, dx: float
    ) -> np.ndarray:
        """Create initial wave function (numpy fallback)."""
        if cfg.initial_state == "gaussian":
            sigma = cfg.domain_size / 10
            x0 = 0.0
            k0 = 2.0
            psi = np.exp(-((x - x0) ** 2) / (2 * sigma**2)) * np.exp(1j * k0 * x)
        elif cfg.initial_state == "plane_wave":
            k0 = 2.0
            psi = np.exp(1j * k0 * x)
        elif cfg.initial_state == "coherent":
            sigma = cfg.domain_size / 10
            x0 = cfg.domain_size / 4
            psi = np.exp(-((x - x0) ** 2) / (2 * sigma**2))
        else:
            psi = np.ones(cfg.n_points, dtype=complex)

        norm = np.sqrt(np.sum(np.abs(psi) ** 2) * dx)
        return psi / norm

    def run_qed(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Run QED simulation with light-matter interaction.

        Uses Fock space representation for quantum optics.

        Args:
            config: Simulation configuration including:
                - n_modes: Number of cavity modes (default: 8)
                - n_photons_max: Max photons per mode (default: 4)
                - n_levels: Atomic levels (default: 4)
                - coupling_strength: Light-matter coupling g (default: 1.0)
                - detuning: Atomic-cavity detuning (default: 0.0)
                - dt: Time step (default: 0.01)
                - duration: Simulation duration (default: 10.0)
                - initial_state: "ground", "excited", "coherent", "fock"

        Returns:
            Dictionary with QED simulation results:
                - status: "success" or "error"
                - state_evolution: Density matrix evolution
                - photon_number: Photon number expectation
                - atomic_population: Level populations
                - entanglement: Entanglement measures
        """
        try:
            cfg = self._parse_qed_config(config)

            if not self._available:
                return self._fallback_qed(cfg)

            result = self._execute_qed(cfg)
            return result
        except Exception as e:
            logger.exception("QED simulation failed")
            return {
                "status": "error",
                "message": str(e),
                "engine": "schr",
            }

    def _parse_qed_config(self, config: dict[str, Any]) -> QEDConfig:
        """Parse QED configuration."""
        return QEDConfig(
            n_modes=config.get("n_modes", 8),
            n_photons_max=config.get("n_photons_max", 4),
            n_levels=config.get("n_levels", 4),
            coupling_strength=config.get("coupling_strength", 1.0),
            detuning=config.get("detuning", 0.0),
            dt=config.get("dt", 0.01),
            duration=config.get("duration", 10.0),
            initial_state=config.get("initial_state", "ground"),
        )

    def _execute_qed(self, cfg: QEDConfig) -> dict[str, Any]:
        """Execute QED simulation using Schr."""
        if self._schr is None:
            return {"status": "error", "message": "Schr not available"}

        try:
            from schr import QEDSolver

            solver = QEDSolver(
                n_modes=cfg.n_modes,
                n_photons_max=cfg.n_photons_max,
                n_levels=cfg.n_levels,
                coupling_strength=cfg.coupling_strength,
                detuning=cfg.detuning,
            )

            rho0 = self._create_qed_initial_state(cfg)

            n_steps = int(cfg.duration / cfg.dt)
            times = np.linspace(0, cfg.duration, n_steps)

            photon_numbers = []
            atomic_populations = []
            entanglement = []
            purities = []

            rho = rho0
            for _t in times:
                rho = solver.step(rho, cfg.dt)

                n_ph = solver.photon_number(rho)
                photon_numbers.append(float(n_ph))

                pop = solver.atomic_population(rho)
                atomic_populations.append(np.array(pop))

                ent = solver.entanglement_entropy(rho)
                entanglement.append(float(ent))

                purity = solver.purity(rho)
                purities.append(float(purity))

            return {
                "status": "success",
                "engine": "schr",
                "engine_truth": "schr",
                "executed": True,
                "device": self._device,
                "n_modes": cfg.n_modes,
                "n_photons_max": cfg.n_photons_max,
                "n_levels": cfg.n_levels,
                "times": times,
                "photon_number": np.array(photon_numbers),
                "atomic_population": np.array(atomic_populations),
                "entanglement_entropy": np.array(entanglement),
                "purity": np.array(purities),
                "coupling_strength": cfg.coupling_strength,
                "detuning": cfg.detuning,
                "duration": cfg.duration,
            }

        except Exception as e:
            logger.warning(f"Schr QED simulation failed, using fallback: {e}")
            return self._fallback_qed(cfg)

    def _create_qed_initial_state(self, cfg: QEDConfig) -> Any:
        """Create initial state for QED simulation."""
        import jax.numpy as jnp

        dim = cfg.n_levels * (cfg.n_photons_max + 1) ** cfg.n_modes

        if cfg.initial_state == "ground":
            state = jnp.zeros(dim, dtype=complex)
            state = state.at[0].set(1.0)
        elif cfg.initial_state == "excited":
            state = jnp.zeros(dim, dtype=complex)
            state = state.at[1].set(1.0)
        elif cfg.initial_state == "coherent":
            state = jnp.ones(dim, dtype=complex) / np.sqrt(dim)
        else:
            state = jnp.zeros(dim, dtype=complex)
            state = state.at[0].set(1.0)

        return jnp.outer(state, jnp.conj(state))

    def _fallback_qed(self, cfg: QEDConfig) -> dict[str, Any]:
        """Fallback QED simulation using Jaynes-Cummings model."""
        n_steps = int(cfg.duration / cfg.dt)
        times = np.linspace(0, cfg.duration, n_steps)

        g = cfg.coupling_strength
        delta = cfg.detuning
        Omega = np.sqrt(g**2 + delta**2)

        photon_numbers = []
        atomic_populations = []
        entanglement = []

        if cfg.initial_state == "ground":
            ce0, cg0 = 0.0, 1.0
        elif cfg.initial_state == "excited":
            ce0, cg0 = 1.0, 0.0
        else:
            ce0, cg0 = 0.5, 0.5

        n0 = cfg.n_photons_max / 2

        for t in times:
            g_n = g * np.sqrt(max(n0, 1))

            if abs(delta) < 1e-10:
                Pe = ce0 * np.cos(g_n * t) ** 2 + cg0 * np.sin(g_n * t) ** 2
                Pg = ce0 * np.sin(g_n * t) ** 2 + cg0 * np.cos(g_n * t) ** 2
            else:
                Pe = ce0 * (np.cos(Omega * t) ** 2 + (delta / Omega) ** 2 * np.sin(Omega * t) ** 2)
                Pg = 1 - Pe

            atomic_populations.append([Pe, Pg])

            n_ph = n0 * Pg + (n0 + 1) * Pe * 0.5
            photon_numbers.append(float(n_ph))

            ent = (
                -Pe * np.log(max(Pe, 1e-10)) - Pg * np.log(max(Pg, 1e-10))
                if Pe > 0 and Pg > 0
                else 0
            )
            entanglement.append(float(ent))

        return {
            "status": "partial",
            "engine": "schr_fallback",
            "backend": "numpy_jaynes_cummings",
            "engine_truth": "not_schr",
            "executed": True,
            "stub": False,
            "accelerated": False,
            "device": "cpu",
            "n_modes": cfg.n_modes,
            "times": times,
            "photon_number": np.array(photon_numbers),
            "atomic_population": np.array(atomic_populations),
            "entanglement_entropy": np.array(entanglement),
            "coupling_strength": cfg.coupling_strength,
            "detuning": cfg.detuning,
            "duration": cfg.duration,
            "note": "NumPy Jaynes-Cummings fallback — not Schr GPU engine",
        }

    def accelerate_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Accelerate quantum patterns with Schr if applicable.

        Checks if pattern is suitable for Schr acceleration:
        - Quantum dynamics patterns → GPU-accelerated Schrödinger
        - QED patterns → Cavity QED simulation
        - Quantum computing → Qubit dynamics

        Falls back to pattern.run() if Schr not applicable.

        Args:
            pattern: Pattern instance to potentially accelerate
            hypothesis: Simulation hypothesis/configuration

        Returns:
            Simulation results (accelerated or fallback)
        """
        if not self._available:
            logger.info("Schr not available, using pattern default")
            return pattern.run(hypothesis)

        pattern_id = getattr(pattern, "PATTERN_ID", "").lower()
        pattern_type = self._classify_pattern(pattern_id)

        if pattern_type == "quantum":
            return self._accelerate_quantum_pattern(pattern, hypothesis)
        elif pattern_type == "qed":
            return self._accelerate_qed_pattern(pattern, hypothesis)
        elif pattern_type == "quantum_computing":
            return self._accelerate_qc_pattern(pattern, hypothesis)
        else:
            logger.info(f"Pattern {pattern_id} not suitable for Schr acceleration")
            return pattern.run(hypothesis)

    def _classify_pattern(self, pattern_id: str) -> str:
        """Classify pattern type for acceleration strategy."""
        pattern_id_lower = pattern_id.lower()

        for ptype in self.PATTERN_TYPES_QUANTUM:
            if ptype in pattern_id_lower:
                return "quantum"

        for ptype in self.PATTERN_TYPES_QED:
            if ptype in pattern_id_lower:
                return "qed"

        for ptype in self.PATTERN_TYPES_QUANTUM_COMPUTING:
            if ptype in pattern_id_lower:
                return "quantum_computing"

        return "unknown"

    def _accelerate_quantum_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """Accelerate quantum dynamics pattern with Schr."""
        config = hypothesis.copy()

        if hasattr(pattern, "config"):
            pattern_config = getattr(pattern, "config", None)
            if pattern_config:
                if hasattr(pattern_config, "n_points"):
                    config["n_points"] = pattern_config.n_points
                if hasattr(pattern_config, "dt"):
                    config["dt"] = pattern_config.dt
                if hasattr(pattern_config, "t_max"):
                    config["duration"] = pattern_config.t_max
                if hasattr(pattern_config, "potential"):
                    config["potential_type"] = pattern_config.potential

        result = self.run_schrodinger(config)
        result["pattern_id"] = getattr(pattern, "PATTERN_ID", "unknown")
        if (
            result.get("status") == "success"
            and result.get("engine") == "schr"
            and result.get("stub") is not True
        ):
            result["accelerated_by"] = "schr"
            result["accelerated"] = True
        else:
            result["accelerated_by"] = "none"
            result["accelerated"] = False
        return result

    def _accelerate_qed_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """Accelerate QED pattern with Schr."""
        config = hypothesis.copy()

        if hasattr(pattern, "config"):
            pattern_config = getattr(pattern, "config", None)
            if pattern_config:
                if hasattr(pattern_config, "coupling"):
                    config["coupling_strength"] = pattern_config.coupling
                if hasattr(pattern_config, "modes"):
                    config["n_modes"] = pattern_config.modes

        result = self.run_qed(config)
        result["pattern_id"] = getattr(pattern, "PATTERN_ID", "unknown")
        if (
            result.get("status") == "success"
            and result.get("engine") == "schr"
            and result.get("stub") is not True
        ):
            result["accelerated_by"] = "schr"
            result["accelerated"] = True
        else:
            result["accelerated_by"] = "none"
            result["accelerated"] = False
        return result

    def _accelerate_qc_pattern(
        self, pattern: BasePattern, hypothesis: dict[str, Any]
    ) -> dict[str, Any]:
        """Accelerate quantum computing pattern."""
        logger.info("Quantum computing patterns use specialized simulators")
        return pattern.run(hypothesis)

    def benchmark_legacy_vs_schr(self, pattern_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """
        Benchmark legacy CPU implementation vs Schr GPU acceleration.

        Returns speedup metrics for pattern.
        """
        # Refuse fake speedup theater (time.sleep as "legacy").
        return {
            "pattern": pattern_id,
            "schr_available": True,
            "device": self._device,
            "legacy_time": None,
            "schr_time": None,
            "speedup": None,
            "note": "benchmark_legacy_vs_schr refuses synthetic sleep-based legacy timing",
            "heuristic": False,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return bridge metadata."""
        return {
            "name": "Schr Bridge",
            "description": "JAX-based GPU-accelerated Quantum Mechanics and QED Simulator",
            "license": "MIT",
            "github": "https://github.com/qiboteam/schr",
            "supported_devices": ["cpu", "gpu", "tpu"],
            "capabilities": [
                "time_dependent_schrodinger",
                "split_step_fourier",
                "cavity_qed",
                "fock_space",
                "jaynes_cummings",
                "quantum_optics",
            ],
            "limitations": [
                "Limited to non-relativistic QM",
                "QED limited to cavity systems",
                "No full QFT support",
            ],
        }
