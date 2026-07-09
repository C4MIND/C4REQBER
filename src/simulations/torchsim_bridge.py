"""
TorchSim Bridge — Adapter for torch-sim-atomistic (github.com/torchsim/torch-sim)
License: MIT (permissive, commercial OK)
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    import torch

if sys.version_info >= (3, 11):  # noqa: UP036
    from enum import StrEnum
else:

    class StrEnum(str, Enum):  # noqa: UP042
        """Compatibility StrEnum for Python < 3.11."""

        def __str__(self) -> str:
            return str(self.value)


logger = logging.getLogger(__name__)


class MDIntegrator(StrEnum):
    """MDIntegrator."""
    NVE = "nve"
    NVT_LANGEVIN = "nvt_langevin"
    NPT_LANGEVIN = "npt_langevin"


class RelaxationMethod(StrEnum):
    """RelaxationMethod."""
    FIRE = "fire"
    GRADIENT_DESCENT = "gradient_descent"
    LBFGS = "lbfgs"
    BFGS = "bfgs"


@dataclass
class TorchSimResult:
    """TorchSimResult."""
    status: str
    engine: str
    final_energy: float
    n_atoms: int
    n_steps: int
    trajectory_path: str | None = None
    metrics: dict[str, Any] = None
    error_message: str | None = None
    execution_time: float = 0.0

    def __post_init__(self) -> None:
        if self.metrics is None:
            self.metrics = {}


@runtime_checkable
class BasePatternProtocol(Protocol):
    """Protocol for pattern-like objects that can be accelerated."""

    PATTERN_ID: str

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


class TorchSimBridge:
    """
    Bridge to TorchSim atomistic simulation engine (MIT license).

    TorchSim is a PyTorch-based atomistic simulation engine supporting:
    - Molecular dynamics: NVE, NVT Langevin, NPT Langevin
    - Relaxation: FIRE, gradient descent, LBFGS, BFGS
    - MLIP models: MACE, Fairchem, SevenNet, ORB, MatterSim, Nequix
    - Classical potentials: Lennard-Jones, Morse, soft-sphere
    """

    ENGINE_NAME = "torchsim"
    PACKAGE_NAME = "torch_sim"
    INSTALL_CMD = "pip install torch-sim-atomistic"

    def __init__(self, device: str = "auto"):
        self._device = device
        self._available: bool | None = None
        self._torch_sim = None
        self._torch = None
        self._initialized = False

    def _lazy_init(self) -> None:
        if self._initialized:
            return
        self._available = self._check_availability()
        if self._available:
            self._init_torch_sim()
        self._initialized = True

    def _check_availability(self) -> bool:
        try:
            import torch_sim

            self._torch_sim = torch_sim
            logger.info(f"TorchSim v{torch_sim.__version__} found")
            return True
        except ImportError:
            logger.debug("TorchSim not installed")
            return False

    def _init_torch_sim(self) -> None:
        try:
            import torch

            self._torch = torch
            if self._device == "auto":
                if torch.cuda.is_available():
                    self._device = "cuda:0"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self._device = "mps"
                else:
                    self._device = "cpu"
            logger.info(f"TorchSim initialized on device: {self._device}")
        except ImportError:
            self._torch = None
            self._device = "cpu"

    @property
    def device(self) -> str:
        """Device."""
        self._lazy_init()
        return self._device

    def is_available(self) -> bool:
        """Check if TorchSim is installed."""
        self._lazy_init()
        return bool(self._available)

    def list_supported_models(self) -> list[str]:
        """List supported MLIP and classical models."""
        return [
            "mace",
            "fairchem",
            "sevennet",
            "orb",
            "mattersim",
            "nequix",
            "metatomic",
            "lennard_jones",
            "morse",
            "soft_sphere",
        ]

    def list_supported_integrators(self) -> list[str]:
        """List supported MD integrators."""
        return [e.value for e in MDIntegrator]

    def list_supported_relaxation_methods(self) -> list[str]:
        """List supported relaxation methods."""
        return [e.value for e in RelaxationMethod]

    def create_state(
        self,
        positions: list[tuple[float, float, float]] | torch.Tensor,
        atomic_numbers: list[int],
        cell: list[list[float]] | None = None,
        pbc: bool = True,
    ) -> Any:
        """
        Create a SimState from atomic positions.

        Args:
            positions: Atomic positions (N, 3)
            atomic_numbers: Element atomic numbers
            cell: Unit cell vectors (3, 3)
            pbc: Periodic boundary conditions

        Returns:
            SimState object
        """
        if not self.is_available():
            raise RuntimeError(f"TorchSim not installed. Run: {self.INSTALL_CMD}")

        import torch

        ts = self._torch_sim

        if isinstance(positions, list):
            positions = torch.tensor(positions, dtype=torch.float32)
        if isinstance(atomic_numbers, list):
            atomic_numbers = torch.tensor(atomic_numbers, dtype=torch.long)

        cell_tensor = None
        if cell is not None:
            if isinstance(cell, list):
                cell_tensor = torch.tensor(cell, dtype=torch.float32)

        state = ts.SimState(
            positions=positions,
            masses=ts.units.AtomicMass.to(torch.tensor(atomic_numbers, dtype=torch.float32)),
            cell=cell_tensor if cell_tensor is not None else torch.eye(3),
            atomic_numbers=atomic_numbers,
            pbc=pbc,
        )
        return state.to(self._device)

    def run_molecular_dynamics(
        self,
        config: dict[str, Any],
    ) -> TorchSimResult:
        """
        Run MD simulation with TorchSim.

        Config keys:
            positions: Atomic positions (N, 3)
            atomic_numbers: Element atomic numbers
            cell: Unit cell vectors
            model: Model name or model object (default: "lennard_jones")
            integrator: MD integrator (default: "nvt_langevin")
            temperature: Temperature in Kelvin
            pressure: Pressure for NPT (optional)
            n_steps: Number of MD steps
            timestep: Time step in fs
            trajectory_path: Path to save trajectory
            seed: Random seed for reproducibility
        """
        start_time = datetime.now()

        if not self.is_available():
            return TorchSimResult(
                status="error",
                engine=self.ENGINE_NAME,
                final_energy=0.0,
                n_atoms=0,
                n_steps=0,
                error_message=f"TorchSim not installed. Run: {self.INSTALL_CMD}",
            )

        try:
            ts = self._torch_sim

            integrator_name = config.get("integrator", "nvt_langevin").lower()
            n_steps = config.get("n_steps", 1000)
            temperature = config.get("temperature", 300.0)
            model_name = config.get("model", "lennard_jones")
            trajectory_path = config.get("trajectory_path")

            state = self._create_state_from_config(config)

            model = self._create_model(model_name, config)

            integrator_kwargs = self._build_integrator_kwargs(integrator_name, config)

            final_state, results = ts.integrate(
                state=state,
                model=model,
                integrator=integrator_name,
                n_steps=n_steps,
                temperature=temperature,
                trajectory_path=trajectory_path,
                **integrator_kwargs,
            )

            final_energy = float(results.get("energy", 0.0))
            n_atoms = int(state.positions.shape[0])

            execution_time = (datetime.now() - start_time).total_seconds()

            return TorchSimResult(
                status="success",
                engine=self.ENGINE_NAME,
                final_energy=final_energy,
                n_atoms=n_atoms,
                n_steps=n_steps,
                trajectory_path=trajectory_path,
                metrics={
                    "temperature": temperature,
                    "integrator": integrator_name,
                    "model": model_name,
                    "device": self._device,
                },
                execution_time=execution_time,
            )

        except Exception as e:
            logger.exception("TorchSim MD simulation failed")
            return TorchSimResult(
                status="error",
                engine=self.ENGINE_NAME,
                final_energy=0.0,
                n_atoms=0,
                n_steps=config.get("n_steps", 0),
                error_message=str(e),
            )

    def run_relaxation(
        self,
        config: dict[str, Any],
    ) -> TorchSimResult:
        """
        Run atomic position relaxation.

        Config keys:
            positions: Atomic positions (N, 3)
            atomic_numbers: Element atomic numbers
            cell: Unit cell vectors
            model: Model name or model object
            method: Relaxation method (default: "fire")
            max_steps: Maximum optimization steps
            force_tol: Force convergence tolerance (eV/A)
            trajectory_path: Path to save trajectory
        """
        start_time = datetime.now()

        if not self.is_available():
            return TorchSimResult(
                status="error",
                engine=self.ENGINE_NAME,
                final_energy=0.0,
                n_atoms=0,
                n_steps=0,
                error_message=f"TorchSim not installed. Run: {self.INSTALL_CMD}",
            )

        try:
            ts = self._torch_sim

            method = config.get("method", "fire").lower()
            max_steps = config.get("max_steps", 500)
            force_tol = config.get("force_tol", 0.01)
            model_name = config.get("model", "lennard_jones")
            trajectory_path = config.get("trajectory_path")

            state = self._create_state_from_config(config)
            model = self._create_model(model_name, config)

            final_state, results = ts.optimize(
                state=state,
                model=model,
                optimizer=method,
                max_steps=max_steps,
                force_tol=force_tol,
                trajectory_path=trajectory_path,
            )

            final_energy = float(results.get("energy", 0.0))
            n_steps = int(results.get("n_steps", 0))
            n_atoms = int(state.positions.shape[0])

            execution_time = (datetime.now() - start_time).total_seconds()

            return TorchSimResult(
                status="success",
                engine=self.ENGINE_NAME,
                final_energy=final_energy,
                n_atoms=n_atoms,
                n_steps=n_steps,
                trajectory_path=trajectory_path,
                metrics={
                    "method": method,
                    "model": model_name,
                    "force_tol": force_tol,
                    "device": self._device,
                },
                execution_time=execution_time,
            )

        except Exception as e:
            logger.exception("TorchSim relaxation failed")
            return TorchSimResult(
                status="error",
                engine=self.ENGINE_NAME,
                final_energy=0.0,
                n_atoms=0,
                n_steps=config.get("max_steps", 0),
                error_message=str(e),
            )

    def accelerate_pattern(
        self,
        pattern: BasePatternProtocol,
        hypothesis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Accelerate existing pattern with TorchSim if applicable.

        Checks if pattern is atomistic/molecular and routes to TorchSim
        for GPU acceleration. Falls back to pattern.run() otherwise.
        """
        if not self.is_available():
            logger.info(f"TorchSim not available, using {pattern.PATTERN_ID} fallback")
            return pattern.run(hypothesis)

        is_atomistic = self._is_atomistic_pattern(pattern, hypothesis)

        if not is_atomistic:
            logger.info(f"Pattern {pattern.PATTERN_ID} is not atomistic, using native run")
            return pattern.run(hypothesis)

        logger.info(f"Accelerating {pattern.PATTERN_ID} with TorchSim GPU")

        config = self._extract_atomistic_config(pattern, hypothesis)

        simulation_type = hypothesis.get("simulation_type", "md")
        if simulation_type == "relaxation":
            result = self.run_relaxation(config)
        else:
            result = self.run_molecular_dynamics(config)

        return {
            "status": result.status,
            "engine": self.ENGINE_NAME,
            "pattern_id": pattern.PATTERN_ID,
            "accelerated": True,
            "final_energy": result.final_energy,
            "n_atoms": result.n_atoms,
            "n_steps": result.n_steps,
            "execution_time": result.execution_time,
            "metrics": result.metrics,
            "error": result.error_message,
        }

    def _create_state_from_config(self, config: dict[str, Any]) -> Any:
        """Create SimState from config dict."""
        positions = config.get("positions")
        atomic_numbers = config.get("atomic_numbers", [1] * len(positions))
        cell = config.get("cell")
        pbc = config.get("pbc", True)

        if positions is None:
            raise ValueError("positions required in config")

        return self.create_state(
            positions=positions,
            atomic_numbers=atomic_numbers,
            cell=cell,
            pbc=pbc,
        )

    def _create_model(self, model_name: str, config: dict[str, Any]) -> Any:
        """Create a model by name or return passed model object."""
        if "." in model_name:
            model_name = model_name.split(".")[-1].lower()

        if model_name in config:
            return config[model_name]

        if not self.is_available():
            raise RuntimeError("TorchSim not available")

        ts = self._torch_sim

        model_map = {
            "lennard_jones": lambda: ts.models.LennardJonesModel(
                epsilon=config.get("epsilon", 0.01),
                sigma=config.get("sigma", 2.5),
                cutoff=config.get("cutoff", 6.0),
            ),
            "morse": lambda: ts.models.MorseModel(
                D=config.get("D", 1.0),
                alpha=config.get("alpha", 1.0),
                r0=config.get("r0", 1.0),
            ),
            "soft_sphere": lambda: ts.models.SoftSphereModel(
                epsilon=config.get("epsilon", 1.0),
                alpha=config.get("alpha", 2.0),
            ),
        }

        if model_name in model_map:
            return model_map[model_name]()

        raise ValueError(
            f"Unknown model: {model_name}. Available: {list(model_map.keys())}"
        )

    def _build_integrator_kwargs(self, integrator: str, config: dict[str, Any]) -> dict[str, Any]:
        """Build kwargs for integrator."""
        kwargs = {}

        if integrator in ("nvt_langevin", "npt_langevin"):
            kwargs["gamma"] = config.get("gamma", 0.1)

        if integrator == "npt_langevin":
            kwargs["pressure"] = config.get("pressure", 1.0)

        if "timestep" in config:
            kwargs["timestep"] = config["timestep"]

        if "seed" in config:
            kwargs["seed"] = config["seed"]

        return kwargs

    def _is_atomistic_pattern(self, pattern: BasePatternProtocol, hypothesis: dict[str, Any]) -> bool:
        """Check if pattern is atomistic/molecular."""
        atomistic_keywords = {
            "atom", "atomic", "molecular", "molecule", "crystal",
            "md", "molecular dynamics", "dft", "ab initio",
            "relaxation", "geometry optimization", "minimization",
            "lattice", "unit cell", "simulation cell",
            "mlip", "machine learning potential", "interatomic",
        }

        pattern_id = pattern.PATTERN_ID.lower()
        for kw in atomistic_keywords:
            if kw in pattern_id:
                return True

        if hypothesis:
            title = hypothesis.get("title", "").lower()
            desc = hypothesis.get("description", "").lower()
            text = f"{title} {desc}"
            for kw in atomistic_keywords:
                if kw in text:
                    return True

            if "positions" in hypothesis or "atomic_numbers" in hypothesis:
                return True

        return False

    def _extract_atomistic_config(self, pattern: BasePatternProtocol, hypothesis: dict[str, Any]) -> dict[str, Any]:
        """Extract atomistic simulation config from pattern/hypothesis."""
        config: dict[str, Any] = {}

        if hypothesis:
            for key in ["positions", "atomic_numbers", "cell", "model",
                        "temperature", "pressure", "n_steps", "timestep",
                        "integrator", "method", "max_steps", "force_tol",
                        "trajectory_path", "pbc", "seed"]:
                if key in hypothesis:
                    config[key] = hypothesis[key]

        if hasattr(pattern, "get_default_config"):
            defaults = pattern.get_default_config()
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value

        return config


def get_torchsim_bridge(device: str = "auto") -> TorchSimBridge:
    """Get singleton TorchSimBridge instance (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if not container.has("torchsim_bridge"):
        container.register("torchsim_bridge", TorchSimBridge(device=device))
    return container.resolve("torchsim_bridge")
