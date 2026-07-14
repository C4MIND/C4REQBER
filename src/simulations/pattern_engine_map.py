"""Pattern-Engine Mapper for C4REQBER v8.0.

Maps 162 existing simulation patterns to optimal physics engines.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EngineType(Enum):
    """Available physics engines including all P1 adapters."""
    # Legacy / internal
    NEWTON = "newton"
    JAXSIM = "jaxsim"
    TORCHSIM = "torchsim"
    SCHR = "schr"
    LEGACY = "legacy"
    # Physics / CFD
    FENICSX = "fenicsx"
    OPENFOAM = "openfoam"
    # Chemistry / MD
    GROMACS = "gromacs"
    LAMMPS = "lammps"
    MDANALYSIS = "mdanalysis"
    PYSCF = "pyscf"
    PSI4 = "psi4"
    QUANTUM_ESPRESSO = "quantum_espresso"
    # Biology
    TELLURIUM = "tellurium"
    NEURON = "neuron"
    BRIAN2 = "brian2"
    JAXLEY = "jaxley"
    COPASI = "copasi"
    # Climate
    XARRAY = "xarray"
    WRF = "wrf"
    # Economics / ABM
    MESA = "mesa"
    SIMPY = "simpy"
    # Astronomy
    REBOUND = "rebound"
    AMUSE = "amuse"
    # Robotics
    MUJOCO = "mujoco"
    PYBULLET = "pybullet"
    # General / differentiable
    DIFFEQPY = "diffeqpy"
    TAICHI = "taichi"
    JAX_MD = "jax_md"
    JAX_LAB = "jax_lab"
    MODELINGTOOLKIT = "modelingtoolkit"
    # Already present
    OPENMM = "openmm"
    # Virtual Biology (Phase 3)
    VINA = "vina"
    BOOLNET = "boolnet"
    COBRA = "cobra"
    SLIM = "slim"


@dataclass
class PatternMetadata:
    """Metadata for a simulation pattern."""
    pattern_id: str
    category: str
    complexity: str  # low, medium, high
    typical_grid_size: tuple[int, ...] | None = None
    time_steps: int | None = None
    requires_gradients: bool = False
    custom_engine: str | None = None


class PatternEngineMap:
    """Map existing patterns to optimal physics engines."""

    PATTERN_ENGINE_MAP: dict[str, str] = {
        # CFD → Newton (GPU)
        "cfd": "newton",
        "climate_gcm": "newton",
        "cloud_microphysics": "newton",
        "ocean_circulation": "newton",
        "air_quality": "newton",
        "navier_stokes": "newton",
        "turbulence": "newton",
        "boundary_layer": "newton",
        "convection": "newton",
        "advection_diffusion": "newton",

        # Continuum → Newton (GPU) / JaxSim
        "continuum_mechanics": "newton",
        "elasticity_3d": "jaxsim",
        "phase_field": "newton",
        "thermal": "newton",
        "stress_strain": "newton",
        "fracture_mechanics": "newton",
        "viscoelasticity": "newton",
        "plasticity": "newton",
        "heat_transfer": "newton",
        "diffusion": "newton",

        # Atomistic → TorchSim
        "dft": "torchsim",
        "crystal_growth": "torchsim",
        "composite_mechanics": "torchsim",
        "molecular_dynamics": "torchsim",
        "lattice_dynamics": "torchsim",
        "dislocation_dynamics": "torchsim",
        "grain_growth": "torchsim",
        "atomistic_deposition": "torchsim",

        # Rigid Body → JaxSim
        "double_pendulum": "jaxsim",
        "agent_based": "jaxsim",
        "flocking": "jaxsim",
        "n_body": "newton",
        "robot_kinematics": "jaxsim",
        "articulated_body": "jaxsim",
        "multi_body_dynamics": "jaxsim",
        "soft_robotics": "jaxsim",

        # Particle Systems → Newton
        "particle_system": "newton",
        "granular_flow": "newton",
        "powder_dynamics": "newton",
        "sediment_transport": "newton",

        # Electromagnetics → Newton
        "em_wave": "newton",
        "antenna_simulation": "newton",
        "em_scattering": "newton",

        # Acoustics → Newton
        "acoustic_wave": "newton",
        "sonar": "newton",
        "ultrasound": "newton",

        # Astrophysics → Newton
        "stellar_evolution": "newton",
        "galaxy_dynamics": "newton",
        "black_hole_accretion": "newton",

        # Quantum → Schr (if any)
        "quantum_harmonic": "schr",
        "wave_function": "schr",
        "quantum_tunneling": "schr",

        # Virtual Biology (Phase 3)
        "protein_folding": "openmm",
        "ligand_binding": "openmm",
        "protein_docking": "vina",
        "drug_target_interaction": "vina",
        "gene_regulatory_network": "boolnet",
        "boolean_network_dynamics": "boolnet",
        "metabolic_pathway": "cobra",
        "flux_balance_analysis": "cobra",
        "population_dynamics": "slim",
        "evolutionary_simulation": "slim",
        "quantum_chemistry_bio": "psi4",
        "molecular_dynamics_openmm": "openmm",
    }

    CATEGORY_ENGINE_MAP: dict[str, str] = {
        "cfd": "newton",
        "continuum": "newton",
        "atomistic": "torchsim",
        "rigid_body": "jaxsim",
        "quantum": "schr",
        "particle": "newton",
        "em": "newton",
        "acoustic": "newton",
        "astro": "newton",
        "agent": "jaxsim",
        # P1 categories
        "fem": "fenicsx",
        "openfoam": "openfoam",
        "molecular_dynamics": "gromacs",
        "md": "lammps",
        "trajectory_analysis": "mdanalysis",
        "quantum_chemistry": "pyscf",
        "dft": "pyscf",
        "systems_biology": "tellurium",
        "biophysical_neuron": "neuron",
        "snn": "brian2",
        "differentiable_neuron": "jaxley",
        "biochemical_network": "copasi",
        "climate": "xarray",
        "weather": "wrf",
        "abm": "mesa",
        "discrete_event": "simpy",
        "planetary_dynamics": "rebound",
        "astrophysics": "amuse",
        "robotics": "mujoco",
        "robotics_simple": "pybullet",
        "ode_solver": "diffeqpy",
        "gpu_sim": "taichi",
        "differentiable_md": "jax_md",
        "lbm": "jax_lab",
        "symbolic_modeling": "modelingtoolkit",
        # Virtual Biology (Phase 3)
        "protein_docking": "vina",
        "gene_network": "boolnet",
        "metabolic_flux": "cobra",
        "population_genetics": "slim",
        "molecular_dynamics_openmm": "openmm",
    }

    ACCELERATION_FACTORS: dict[str, float] = {
        "cfd": 50.0,
        "climate_gcm": 80.0,
        "cloud_microphysics": 30.0,
        "ocean_circulation": 100.0,
        "air_quality": 40.0,
        "navier_stokes": 60.0,
        "turbulence": 70.0,
        "continuum_mechanics": 25.0,
        "elasticity_3d": 35.0,
        "phase_field": 45.0,
        "thermal": 20.0,
        "dft": 15.0,
        "crystal_growth": 12.0,
        "molecular_dynamics": 18.0,
        "double_pendulum": 5.0,
        "agent_based": 8.0,
        "flocking": 10.0,
        "n_body": 30.0,
        "particle_system": 25.0,
        "em_wave": 35.0,
        "acoustic_wave": 30.0,
        "quantum_harmonic": 20.0,
        # P1 additions
        "fenicsx": 25.0,
        "openfoam": 50.0,
        "gromacs": 18.0,
        "lammps": 18.0,
        "mdanalysis": 2.0,
        "pyscf": 15.0,
        "psi4": 15.0,
        "quantum_espresso": 20.0,
        "tellurium": 3.0,
        "neuron": 5.0,
        "brian2": 5.0,
        "jaxley": 10.0,
        "copasi": 3.0,
        "xarray": 8.0,
        "wrf": 80.0,
        "mesa": 5.0,
        "simpy": 2.0,
        "rebound": 30.0,
        "amuse": 20.0,
        "mujoco": 10.0,
        "pybullet": 5.0,
        "diffeqpy": 8.0,
        "taichi": 40.0,
        "jax_md": 25.0,
        "jax_lab": 35.0,
        "modelingtoolkit": 10.0,
        # Virtual Biology (Phase 3)
        "openmm": 18.0,
        "vina": 2.0,
        "boolnet": 2.0,
        "cobra": 3.0,
        "slim": 5.0,
    }

    GPU_PATTERNS: set[str] = {
        "cfd", "climate_gcm", "cloud_microphysics", "ocean_circulation",
        "air_quality", "navier_stokes", "turbulence", "boundary_layer",
        "convection", "advection_diffusion", "continuum_mechanics",
        "elasticity_3d", "phase_field", "thermal", "stress_strain",
        "fracture_mechanics", "viscoelasticity", "plasticity",
        "heat_transfer", "diffusion", "dft", "crystal_growth",
        "composite_mechanics", "molecular_dynamics", "lattice_dynamics",
        "dislocation_dynamics", "grain_growth", "atomistic_deposition",
        "double_pendulum", "agent_based", "flocking", "n_body",
        "robot_kinematics", "articulated_body", "multi_body_dynamics",
        "soft_robotics", "particle_system", "granular_flow",
        "powder_dynamics", "sediment_transport", "em_wave",
        "antenna_simulation", "em_scattering", "acoustic_wave",
        "sonar", "ultrasound", "stellar_evolution", "galaxy_dynamics",
        "black_hole_accretion", "quantum_harmonic", "wave_function",
        "quantum_tunneling",
        # P1 GPU-capable
        "jaxley", "mujoco", "taichi", "jax_md", "jax_lab",
        "brian2", "diffeqpy", "modelingtoolkit",
        # Virtual Biology GPU-capable
        "openmm",
    }

    def __init__(self) -> None:
        self._pattern_cache: dict[str, str] = {}
        self._custom_mappings: dict[str, str] = {}

    def get_engine(self, pattern_id: str, metadata: dict[str, Any] | None = None) -> str:
        """Get recommended engine for pattern.

        Args:
            pattern_id: Unique identifier for the simulation pattern.
            metadata: Optional metadata dict with keys:
                - category: Pattern category for fallback mapping
                - complexity: low/medium/high
                - prefer_gpu: bool to force GPU engine selection
                - custom_engine: Override engine selection

        Returns:
            Engine name string: "newton", "jaxsim", "torchsim", "schr", or "legacy"
        """
        if pattern_id in self._custom_mappings:
            return self._custom_mappings[pattern_id]

        if pattern_id in self.PATTERN_ENGINE_MAP:
            engine = self.PATTERN_ENGINE_MAP[pattern_id]
            if self._validate_engine(engine):
                return engine

        if metadata:
            if custom := metadata.get("custom_engine"):
                if self._validate_engine(custom):
                    return custom

            if category := metadata.get("category"):
                normalized = self._normalize_category(category)
                if normalized in self.CATEGORY_ENGINE_MAP:
                    return self.CATEGORY_ENGINE_MAP[normalized]

            if metadata.get("prefer_gpu"):
                return "newton"

        return "legacy"

    def _validate_engine(self, engine: str) -> bool:
        """Validate engine name is supported."""
        valid_engines = {e.value for e in EngineType}
        return engine in valid_engines

    def _normalize_category(self, category: str) -> str:
        """Normalize category name for lookup."""
        normalized = category.lower().replace("-", "_").replace(" ", "_")
        category_aliases = {
            "fluid": "cfd",
            "fluid_dynamics": "cfd",
            "computational_fluid_dynamics": "cfd",
            "solid_mechanics": "continuum",
            "structural": "continuum",
            "materials": "atomistic",
            "md": "atomistic",
            "rigid": "rigid_body",
            "robotics": "rigid_body",
            "electromagnetic": "em",
            "electromagnetics": "em",
            "acoustics": "acoustic",
            "astrophysics": "astro",
            # P1 aliases
            "finite_element": "fem",
            "fem": "fem",
            "pde": "fenicsx",
            "openfoam": "openfoam",
            "cfd_openfoam": "openfoam",
            "gromacs": "molecular_dynamics",
            "lammps": "md",
            "mdanalysis": "trajectory_analysis",
            "pyscf": "quantum_chemistry",
            "psi4": "quantum_chemistry",
            "quantum_espresso": "quantum_chemistry",
            "tellurium": "systems_biology",
            "neuron": "biophysical_neuron",
            "brian2": "snn",
            "jaxley": "differentiable_neuron",
            "copasi": "biochemical_network",
            "xarray": "climate",
            "wrf": "weather",
            "mesa": "abm",
            "simpy": "discrete_event",
            "rebound": "planetary_dynamics",
            "amuse": "astrophysics",
            "mujoco": "robotics",
            "pybullet": "robotics_simple",
            "diffeqpy": "ode_solver",
            "taichi": "gpu_sim",
            "jax_md": "differentiable_md",
            "jax_lab": "lbm",
            "modelingtoolkit": "symbolic_modeling",
        }
        return category_aliases.get(normalized, normalized)

    def get_gpu_accelerated_patterns(self) -> list[str]:
        """Return list of patterns that can use GPU acceleration."""
        return sorted(self.GPU_PATTERNS)

    def get_acceleration_factor(self, pattern_id: str) -> float:
        """Estimate speedup from GPU acceleration.

        Args:
            pattern_id: The simulation pattern identifier.

        Returns:
            Estimated speedup factor (1.0 = no acceleration).
        """
        if pattern_id in self.ACCELERATION_FACTORS:
            return self.ACCELERATION_FACTORS[pattern_id]

        base_category = pattern_id.split("_")[0] if "_" in pattern_id else pattern_id
        for cat_key, factor in [
            ("cfd", 50.0),
            ("continuum", 25.0),
            ("atomistic", 15.0),
            ("rigid", 5.0),
            ("quantum", 20.0),
            ("particle", 25.0),
            ("em", 35.0),
            ("acoustic", 30.0),
            ("astro", 40.0),
        ]:
            if base_category.startswith(cat_key):
                return factor

        return 1.0

    def register_custom_mapping(self, pattern_id: str, engine: str) -> None:
        """Register a custom pattern-to-engine mapping.

        Args:
            pattern_id: The pattern to map.
            engine: The engine to use (must be valid).
        """
        if self._validate_engine(engine):
            self._custom_mappings[pattern_id] = engine

    def get_patterns_by_engine(self, engine: str) -> list[str]:
        """Get all patterns mapped to a specific engine.

        Args:
            engine: Engine name to filter by.

        Returns:
            List of pattern IDs using the specified engine.
        """
        return [
            pattern
            for pattern, mapped_engine in self.PATTERN_ENGINE_MAP.items()
            if mapped_engine == engine
        ]

    def get_engine_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics about engine distribution.

        Returns:
            Dict with engine names as keys and stats as values.
        """
        stats: dict[str, dict[str, Any]] = {}
        for engine in EngineType:
            patterns = self.get_patterns_by_engine(engine.value)
            stats[engine.value] = {
                "pattern_count": len(patterns),
                "patterns": patterns[:10],
                "avg_acceleration": sum(
                    self.ACCELERATION_FACTORS.get(p, 1.0) for p in patterns
                ) / max(len(patterns), 1),
            }
        return stats

    def is_gpu_pattern(self, pattern_id: str) -> bool:
        """Check if a pattern supports GPU acceleration."""
        return pattern_id in self.GPU_PATTERNS

    def recommend_engine(
        self,
        pattern_id: str,
        grid_size: tuple[int, ...] | None = None,
        time_steps: int | None = None,
        requires_gradients: bool = False,
    ) -> str:
        """Recommend optimal engine based on problem characteristics.

        Args:
            pattern_id: Pattern identifier.
            grid_size: Spatial grid dimensions.
            time_steps: Number of time steps.
            requires_gradients: Whether gradient computation is needed.

        Returns:
            Recommended engine name.
        """
        base_engine = self.get_engine(pattern_id)

        if base_engine == "legacy":
            return "legacy"

        if requires_gradients and base_engine in ("newton", "jaxsim"):
            return "jaxsim"

        if grid_size:
            total_cells = 1
            for dim in grid_size:
                total_cells *= dim

            if total_cells > 1_000_000:
                if base_engine in ("newton", "jaxsim", "torchsim"):
                    return base_engine
            elif total_cells < 10_000:
                return "legacy"

        return base_engine


PATTERN_ENGINE_MAP = PatternEngineMap.PATTERN_ENGINE_MAP


def get_engine(pattern_id: str, metadata: dict[str, Any] | None = None) -> str:
    """Convenience function to get engine for a pattern."""
    mapper = PatternEngineMap()
    return mapper.get_engine(pattern_id, metadata)


def get_gpu_accelerated_patterns() -> list[str]:
    """Convenience function to get GPU-acceleratable patterns."""
    mapper = PatternEngineMap()
    return mapper.get_gpu_accelerated_patterns()
