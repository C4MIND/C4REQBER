"""
Protein Folding Pattern
Coarse-grained molecular dynamics for protein structure prediction

Based on:
- Go model (Taketomi et al., 1975)
- C-alpha/C-beta coarse-graining
- Implicit solvent models
- Replica exchange methods
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from ..core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)


logger = logging.getLogger(__name__)


class FoldingModel(Enum):
    """FoldingModel."""
    GO_MODEL = "go_model"
    CA_ONLY = "ca_only"
    HARMONIC = "harmonic"
    LATTICE = "lattice"


@dataclass
class ProteinFoldingConfig:
    """Protein folding simulation configuration"""
    # Model selection
    model: FoldingModel = FoldingModel.GO_MODEL

    # Protein structure
    num_residues: int = 50
    sequence: str | None = None  # Amino acid sequence

    # Force field parameters
    epsilon: float = 1.0  # Energy scale (kcal/mol)
    sigma: float = 3.8  # Distance scale (Angstroms, C-alpha distance)
    k_bond: float = 100.0  # Bond spring constant
    k_angle: float = 20.0  # Angle spring constant

    # Simulation
    t_max: float = 1000.0  # ps
    dt: float = 0.001  # ps (1 fs)
    temperature: float = 300.0  # K
    friction: float = 1.0  # Langevin friction (1/ps)

    # Sampling
    num_replicas: int = 1  # For replica exchange
    replica_temperatures: list[float] | None = None

    # Analysis
    record_interval: int = 100  # Record every N steps
    calculate_rmsd: bool = True
    calculate_rg: bool = True  # Radius of gyration
    calculate_contacts: bool = True

    # Native structure (for Go model)
    native_coords: np.ndarray | None = None
    contact_cutoff: float = 8.0  # Angstroms for native contacts

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "num_residues": self.num_residues,
            "sequence": self.sequence,
            "epsilon": self.epsilon,
            "sigma": self.sigma,
            "k_bond": self.k_bond,
            "k_angle": self.k_angle,
            "t_max": self.t_max,
            "dt": self.dt,
            "temperature": self.temperature,
            "friction": self.friction,
            "num_replicas": self.num_replicas,
            "replica_temperatures": self.replica_temperatures,
            "record_interval": self.record_interval,
            "calculate_rmsd": self.calculate_rmsd,
            "calculate_rg": self.calculate_rg,
            "calculate_contacts": self.calculate_contacts,
            "contact_cutoff": self.contact_cutoff,
        }


@simulation_pattern(
    id="protein_folding",
    name="Protein Folding",
    category="biology",
    description="Coarse-grained molecular dynamics for protein folding simulation",
)
class ProteinFoldingPattern(SimulationPattern):
    """
    Protein folding simulation using coarse-grained models

    Simulates the folding process of proteins from extended
    conformations to native structures using simplified models:

    1. Go Model: Native-centric potential
    2. C-alpha only: Minimal representation
    3. Harmonic: Simple elastic network
    4. Lattice: Discrete space model

    Applications:
    - Folding pathway analysis
    - Structure prediction validation
    - Thermodynamic characterization
    - Drug binding studies
    """

    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="go_model",
            options=["go_model", "ca_only", "harmonic", "lattice"],
            description="Folding model type",
        ),
        SimulationParameter(
            name="num_residues",
            type="int",
            default=50,
            min=5,
            max=500,
            description="Number of amino acid residues",
        ),
        SimulationParameter(
            name="epsilon",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Energy scale (kcal/mol)",
        ),
        SimulationParameter(
            name="temperature",
            type="float",
            default=300.0,
            min=100.0,
            max=1000.0,
            description="Temperature (K)",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=1000.0,
            min=100.0,
            max=10000.0,
            description="Simulation duration (ps)",
        ),
        SimulationParameter(
            name="friction",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Langevin friction (1/ps)",
        ),
        SimulationParameter(
            name="k_bond",
            type="float",
            default=100.0,
            min=10.0,
            max=500.0,
            description="Bond force constant",
        ),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config: ProteinFoldingConfig = ProteinFoldingConfig()
        self.rng = np.random.default_rng(seed=42)
        self.native_structure: np.ndarray | None = None
        self.native_contacts: list[tuple[int, int]] | None = None

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if protein folding can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "protein", "folding", "structure", "conformation", "native",
            "denaturation", "renaturation", "unfolding", "fold",
            "secondary structure", "tertiary structure", "molecular dynamics",
            "force field", "go model", "coarse-grained", "residue",
            "amino acid", "peptide", "ensemble", "thermodynamics",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute protein folding simulation"""
        start_time = datetime.now()
        simulation_id = f"pf_{start_time.timestamp()}"

        logger.info(f"Starting protein folding simulation {simulation_id}")

        try:
            # Parse configuration
            self.config = self._parse_config(config)

            # Generate or load native structure
            self._prepare_native_structure()

            # Run simulation based on model type
            if self.config.model == FoldingModel.GO_MODEL:
                results = await self._go_model_simulation()
            elif self.config.model == FoldingModel.CA_ONLY:
                results = await self._ca_only_simulation()
            elif self.config.model == FoldingModel.HARMONIC:
                results = await self._harmonic_simulation()
            else:
                results = await self._lattice_simulation()

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Protein folding simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: dict[str, Any]) -> ProteinFoldingConfig:
        """Parse configuration dictionary"""
        cfg = ProteinFoldingConfig()

        if "model" in config:
            cfg.model = FoldingModel(config["model"])
        if "num_residues" in config:
            cfg.num_residues = int(config["num_residues"])
        if "sequence" in config:
            cfg.sequence = config["sequence"]
        if "epsilon" in config:
            cfg.epsilon = float(config["epsilon"])
        if "sigma" in config:
            cfg.sigma = float(config["sigma"])
        if "k_bond" in config:
            cfg.k_bond = float(config["k_bond"])
        if "k_angle" in config:
            cfg.k_angle = float(config["k_angle"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "temperature" in config:
            cfg.temperature = float(config["temperature"])
        if "friction" in config:
            cfg.friction = float(config["friction"])
        if "contact_cutoff" in config:
            cfg.contact_cutoff = float(config["contact_cutoff"])
        if "record_interval" in config:
            cfg.record_interval = int(config["record_interval"])

        return cfg

    def _prepare_native_structure(self) -> None:
        """Generate or load native structure"""
        cfg = self.config
        n = cfg.num_residues

        # Generate simple helix as native structure
        # Alpha helix: 3.6 residues per turn, 1.5A rise per residue
        t = np.linspace(0, 2 * np.pi * n / 3.6, n)
        radius = 2.3  # Alpha helix radius

        x = radius * np.cos(t)
        y = radius * np.sin(t)
        z = np.linspace(0, n * 1.5, n)

        self.native_structure = np.column_stack([x, y, z])

        # Define native contacts (pairs within cutoff in native)
        self.native_contacts = []
        for i in range(n):
            for j in range(i + 4, n):  # Skip neighbors
                dist = np.linalg.norm(self.native_structure[i] - self.native_structure[j])
                if dist < cfg.contact_cutoff:
                    self.native_contacts.append((i, j))

    async def _go_model_simulation(self) -> dict[str, Any]:
        """Go model simulation (native-centric)"""

        cfg = self.config
        n = cfg.num_residues

        # Initialize extended conformation
        coords = self._initialize_extended()

        # Storage
        trajectory = [coords.copy()]
        energies = []
        q_values = []  # Native contact fraction
        rgs = []  # Radius of gyration

        # Langevin dynamics parameters
        dt = cfg.dt
        gamma = cfg.friction
        kT = 0.001987 * cfg.temperature  # kcal/mol

        # Initial velocities
        velocities = self.rng.normal(0, np.sqrt(kT), (n, 3))

        n_steps = int(cfg.t_max / dt)
        record_every = cfg.record_interval

        for step in range(n_steps):
            # Calculate forces
            forces = self._calculate_go_forces(coords)

            # Langevin update
            # v(t+dt) = v(t) * (1 - gamma*dt) + F/m * dt + random_force
            # r(t+dt) = r(t) + v(t+dt) * dt

            random_force = self.rng.normal(0, np.sqrt(2 * gamma * kT / dt), (n, 3))

            velocities = velocities * (1 - gamma * dt) + forces * dt + random_force * dt
            coords = coords + velocities * dt

            # Record
            if step % record_every == 0:
                trajectory.append(coords.copy())

                # Calculate energy
                energy = self._calculate_go_energy(coords)
                energies.append(energy)

                # Calculate Q (fraction of native contacts)
                q = self._calculate_q(coords)
                q_values.append(q)

                # Calculate Rg
                rg = self._calculate_radius_of_gyration(coords)
                rgs.append(rg)

            if step % 10000 == 0:
                await asyncio.sleep(0)

        # Calculate final RMSD
        rmsd = self._calculate_rmsd(coords, self.native_structure)  # type: ignore[arg-type]

        metrics = {
            "num_residues": n,
            "num_native_contacts": len(self.native_contacts) if self.native_contacts else 0,
            "final_rmsd": float(rmsd),
            "final_q": float(q_values[-1]) if q_values else 0,
            "mean_q": float(np.mean(q_values)) if q_values else 0,
            "final_rg": float(rgs[-1]) if rgs else 0,
            "mean_rg": float(np.mean(rgs)) if rgs else 0,
            "final_energy": float(energies[-1]) if energies else 0,
            "mean_energy": float(np.mean(energies)) if energies else 0,
            "folded": float(q_values[-1]) > 0.8 if q_values else False,
            "model": "go_model",
        }

        logs = [
            "Go model simulation completed",
            f"Residues: {n}, Native contacts: {metrics['num_native_contacts']}",
            f"Final RMSD: {rmsd:.2f} Å",
            f"Final Q (native contacts): {metrics['final_q']:.3f}",
            f"Final Rg: {metrics['final_rg']:.2f} Å",
            f"Folded: {metrics['folded']}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "trajectory_coords": [t.tolist() for t in trajectory[::10]],  # Decimate for storage
            "q_values": q_values,
            "rg_values": rgs,
            "energies": energies,
        }

    def _initialize_extended(self) -> np.ndarray:
        """Initialize extended conformation"""
        n = self.config.num_residues
        # Linear chain along x-axis
        coords = np.zeros((n, 3))
        coords[:, 0] = np.arange(n) * self.config.sigma
        # Add small random perturbation
        coords += self.rng.normal(0, 0.1, (n, 3))
        return coords

    def _calculate_go_forces(self, coords: np.ndarray) -> np.ndarray:
        """Calculate Go model forces"""
        cfg = self.config
        n = cfg.num_residues
        forces = np.zeros((n, 3))

        # Bond forces (harmonic)
        for i in range(n - 1):
            r = coords[i+1] - coords[i]
            dist = np.linalg.norm(r)
            if dist > 0:
                f = -cfg.k_bond * (dist - cfg.sigma) * r / dist
                forces[i] -= f
                forces[i+1] += f

        # Angle forces (simplified)
        # Would need more complex calculation for proper angle potential

        # Native contact attractions
        if self.native_contacts:
            for i, j in self.native_contacts:
                r = coords[j] - coords[i]
                dist = np.linalg.norm(r)
                r_native = np.linalg.norm(
                    self.native_structure[j] - self.native_structure[i]  # type: ignore[index]
                )

                # 10-12 Lennard-Jones-like for native contacts
                if dist > 0:
                    ratio = r_native / dist
                    f_mag = 12 * cfg.epsilon * (ratio**12 - ratio**10) / dist
                    f = f_mag * r / dist
                    forces[i] -= f
                    forces[j] += f

        # Non-native repulsion (excluded volume)
        for i in range(n):
            for j in range(i + 2, n):
                if not self.native_contacts or (i, j) not in self.native_contacts:
                    r = coords[j] - coords[i]
                    dist = np.linalg.norm(r)
                    if dist < cfg.sigma and dist > 0:
                        # Repulsive
                        f = cfg.epsilon * (cfg.sigma / dist)**12 * r / dist
                        forces[i] -= f
                        forces[j] += f

        return forces

    def _calculate_go_energy(self, coords: np.ndarray) -> float:
        """Calculate Go model potential energy"""
        cfg = self.config
        n = cfg.num_residues
        energy = 0.0

        # Bond energy
        for i in range(n - 1):
            dist = np.linalg.norm(coords[i+1] - coords[i])
            energy += 0.5 * cfg.k_bond * (dist - cfg.sigma)**2  # type: ignore[assignment]

        # Native contact energy
        if self.native_contacts:
            for i, j in self.native_contacts:
                dist = np.linalg.norm(coords[j] - coords[i])
                r_native = np.linalg.norm(
                    self.native_structure[j] - self.native_structure[i]  # type: ignore[index]
                )
                ratio = r_native / dist if dist > 0 else 1
                energy += cfg.epsilon * (ratio**12 - 2 * ratio**10)  # type: ignore[assignment]

        return energy

    def _calculate_q(self, coords: np.ndarray) -> float:
        """Calculate fraction of native contacts formed"""
        if not self.native_contacts:
            return 0.0

        formed = 0
        for i, j in self.native_contacts:
            dist = np.linalg.norm(coords[j] - coords[i])
            r_native = np.linalg.norm(
                self.native_structure[j] - self.native_structure[i]  # type: ignore[index]
            )
            # Contact formed if within factor of 1.2 of native
            if dist < r_native * 1.2:
                formed += 1

        return formed / len(self.native_contacts)

    def _calculate_radius_of_gyration(self, coords: np.ndarray) -> float:
        """Calculate radius of gyration"""
        center = np.mean(coords, axis=0)
        rg = np.sqrt(np.mean(np.sum((coords - center)**2, axis=1)))
        return float(rg)

    def _calculate_rmsd(self, coords1: np.ndarray, coords2: np.ndarray) -> float:
        """Calculate RMSD between two structures"""
        diff = coords1 - coords2
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    async def _ca_only_simulation(self) -> dict[str, Any]:
        """C-alpha only simplified MD"""
        # Similar to Go model but without native contacts
        cfg = self.config
        n = cfg.num_residues

        coords = self._initialize_extended()
        trajectory = [coords.copy()]
        rgs = []

        dt = cfg.dt
        kT = 0.001987 * cfg.temperature
        gamma = cfg.friction

        velocities = self.rng.normal(0, np.sqrt(kT), (n, 3))

        n_steps = int(cfg.t_max / dt)

        for step in range(n_steps):
            # Simplified forces: only bonds and excluded volume
            forces = np.zeros((n, 3))

            # Bonds
            for i in range(n - 1):
                r = coords[i+1] - coords[i]
                dist = np.linalg.norm(r)
                if dist > 0:
                    f = -cfg.k_bond * (dist - cfg.sigma) * r / dist
                    forces[i] -= f
                    forces[i+1] += f

            # Excluded volume
            for i in range(n):
                for j in range(i + 2, n):
                    r = coords[j] - coords[i]
                    dist = np.linalg.norm(r)
                    if dist < cfg.sigma and dist > 0:
                        f = cfg.epsilon * (cfg.sigma / dist)**12 * r / dist
                        forces[i] -= f
                        forces[j] += f

            # Langevin update
            random_force = self.rng.normal(0, np.sqrt(2 * gamma * kT / dt), (n, 3))
            velocities = velocities * (1 - gamma * dt) + forces * dt + random_force * dt
            coords = coords + velocities * dt

            if step % cfg.record_interval == 0:
                trajectory.append(coords.copy())
                rgs.append(self._calculate_radius_of_gyration(coords))

            if step % 10000 == 0:
                await asyncio.sleep(0)

        metrics = {
            "num_residues": n,
            "final_rg": float(rgs[-1]) if rgs else 0,
            "mean_rg": float(np.mean(rgs)) if rgs else 0,
            "model": "ca_only",
        }

        return {
            "metrics": metrics,
            "logs": ["C-alpha only simulation completed"],
            "rg_values": rgs,
        }

    async def _harmonic_simulation(self) -> dict[str, Any]:
        """Harmonic/elastic network model"""
        # Simplified elastic network
        cfg = self.config
        n = cfg.num_residues

        coords = self.native_structure.copy()  # type: ignore  # Start near native
        # Add thermal fluctuations
        coords += self.rng.normal(0, 0.5, (n, 3))

        rmsds = []
        n_frames = 1000

        for _ in range(n_frames):
            # Random thermal fluctuations around native
            kT = 0.001987 * cfg.temperature
            displacement = self.rng.normal(0, np.sqrt(kT / cfg.k_bond), (n, 3))
            coords = self.native_structure + displacement  # type: ignore[operator]

            rmsd = self._calculate_rmsd(coords, self.native_structure)  # type: ignore[arg-type]
            rmsds.append(rmsd)

            await asyncio.sleep(0)

        metrics = {
            "num_residues": n,
            "mean_rmsd": float(np.mean(rmsds)),
            "rmsd_fluctuation": float(np.std(rmsds)),
            "model": "harmonic",
        }

        return {
            "metrics": metrics,
            "logs": ["Harmonic network simulation completed"],
            "rmsd_values": rmsds,
        }

    async def _lattice_simulation(self) -> dict[str, Any]:
        """Simple 2D lattice protein model (HP model style)"""
        cfg = self.config
        n = cfg.num_residues

        # Simplified lattice simulation
        # Track number of HH contacts
        hh_contacts = []

        # Generate random HP sequence
        sequence = self.rng.choice(['H', 'P'], n)

        # Simulate random walk on lattice
        for _ in range(1000):
            # Random walk
            coords = np.zeros((n, 2), dtype=int)
            for i in range(1, n):
                # Random step
                step = self.rng.choice([[0,1], [0,-1], [1,0], [-1,0]])
                coords[i] = coords[i-1] + step

            # Count HH contacts
            hh = 0
            for i in range(n):
                for j in range(i + 1, n):
                    if sequence[i] == 'H' and sequence[j] == 'H':
                        dist = np.abs(coords[i] - coords[j]).sum()
                        if dist == 1:  # Adjacent on lattice
                            hh += 1

            hh_contacts.append(hh)
            await asyncio.sleep(0)

        metrics = {
            "num_residues": n,
            "hp_sequence": ''.join(sequence),
            "max_hh_contacts": int(np.max(hh_contacts)),
            "mean_hh_contacts": float(np.mean(hh_contacts)),
            "model": "lattice",
        }

        return {
            "metrics": metrics,
            "logs": [
                "Lattice model simulation completed",
                f"Sequence: {metrics['hp_sequence']}",
                f"Max HH contacts: {metrics['max_hh_contacts']}",
            ],
            "hh_contacts": hh_contacts,
        }

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Valid protein size
        if 5 <= metrics.get("num_residues", 0) <= 500:
            factors.append(0.3)

        # Model-specific checks
        if self.config.model == FoldingModel.GO_MODEL:
            q = metrics.get("final_q", 0)
            if 0 <= q <= 1:
                factors.append(0.3)

            rg = metrics.get("final_rg", 0)
            if rg > 0:  # Valid Rg
                factors.append(0.2)

        elif self.config.model == FoldingModel.HARMONIC:
            rmsd = metrics.get("mean_rmsd", 0)
            if rmsd > 0:
                factors.append(0.4)

        elif self.config.model == FoldingModel.LATTICE:
            if metrics.get("max_hh_contacts", 0) >= 0:
                factors.append(0.4)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        n = params.get("num_residues", 50)
        t_max = params.get("t_max", 1000.0)
        dt = params.get("dt", 0.001)

        n_steps = int(t_max / dt)

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + n * n_steps * 1e-7,
            "gpu_required": False,
            "estimated_time_seconds": n_steps * n / 1e7,
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,  # type: ignore[attr-defined]
            "category": cls.category,  # type: ignore[attr-defined]
            "description": cls.description,  # type: ignore[attr-defined]
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default": p.default,
                    "min": p.min,
                    "max": p.max,
                    "options": p.options,
                    "description": p.description,
                }
                for p in cls.parameters
            ],
            "references": [
                "Taketomi, H. et al. (1975). Studies on protein folding",
                "Go, N. (1983). Theoretical studies of protein folding",
                "Clementi, C. et al. (2000). Topological and energetic factors",
            ],
        }
