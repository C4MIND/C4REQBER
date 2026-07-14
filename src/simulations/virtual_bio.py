# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Virtual Biology Simulation Orchestrator — in-silico experiments via GPU compute.

Uses BaseSimulationAdapter bridges for all simulation backends.
Each adapter provides is_available(), run(), and GPU-aware install hints.

Supported backends (via adapters):
- Molecular Dynamics: OpenMM, GROMACS (ligand binding, protein folding)
- Protein Docking: AutoDock Vina (drug-target interactions)
- Gene Regulatory Network: BoolNet (Boolean network dynamics)
- Metabolic Pathway: COBRApy (flux balance analysis)
- Population Genetics: SLiM (evolutionary dynamics)
- Quantum Chemistry: Psi4, PySCF (electronic structure)

Usage:
    from src.simulations.virtual_bio import VirtualBioOrchestrator
    orch = VirtualBioOrchestrator()
    result = orch.run(domain="molecular_dynamics", hypothesis=H)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .base_adapter import BaseSimulationAdapter
from .pattern_engine_map import EngineType


logger = logging.getLogger(__name__)


@dataclass
class BioSimConfig:
    """Configuration for a virtual biology simulation domain."""

    domain: str
    engine: str
    gpu_required: bool
    estimated_runtime_seconds: int
    vastai_cost_per_hour: float
    memory_required_gb: int
    adapter_class: str  # module.Class path


SIMULATION_CATALOG: dict[str, BioSimConfig] = {
    "molecular_dynamics": BioSimConfig(
        domain="molecular_dynamics",
        engine=EngineType.OPENMM.value,
        gpu_required=True,
        estimated_runtime_seconds=3600,
        vastai_cost_per_hour=0.35,
        memory_required_gb=8,
        adapter_class="src.simulations.openmm_bridge.OpenMMBridge",
    ),
    "protein_docking": BioSimConfig(
        domain="protein_docking",
        engine=EngineType.VINA.value,
        gpu_required=False,
        estimated_runtime_seconds=300,
        vastai_cost_per_hour=0.0,
        memory_required_gb=2,
        adapter_class="src.simulations.vina_bridge.VinaBridge",
    ),
    "gene_network": BioSimConfig(
        domain="gene_network",
        engine=EngineType.BOOLNET.value,
        gpu_required=False,
        estimated_runtime_seconds=60,
        vastai_cost_per_hour=0.0,
        memory_required_gb=1,
        adapter_class="src.simulations.boolnet_bridge.BoolNetBridge",
    ),
    "metabolic_flux": BioSimConfig(
        domain="metabolic_flux",
        engine=EngineType.COBRA.value,
        gpu_required=False,
        estimated_runtime_seconds=120,
        vastai_cost_per_hour=0.0,
        memory_required_gb=2,
        adapter_class="src.simulations.cobra_bridge.CobraBridge",
    ),
    "population_genetics": BioSimConfig(
        domain="population_genetics",
        engine=EngineType.SLIM.value,
        gpu_required=False,
        estimated_runtime_seconds=600,
        vastai_cost_per_hour=0.0,
        memory_required_gb=4,
        adapter_class="src.simulations.slim_bridge.SlimBridge",
    ),
    "quantum_chemistry": BioSimConfig(
        domain="quantum_chemistry",
        engine=EngineType.PSI4.value,
        gpu_required=True,
        estimated_runtime_seconds=1800,
        vastai_cost_per_hour=0.50,
        memory_required_gb=16,
        adapter_class="src.simulations.psi4_bridge.Psi4Bridge",
    ),
}


def _get_adapter(adapter_class: str) -> BaseSimulationAdapter | None:
    """Dynamically import and instantiate an adapter by module.Class path."""
    try:
        module_path, class_name = adapter_class.rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls()
    except Exception as exc:
        logger.debug("Failed to load adapter %s: %s", adapter_class, exc)
        return None


class VirtualBioOrchestrator:
    """Orchestrate in-silico experiments as partial hypothesis validation."""

    def _get_adapter(self, domain: str) -> BaseSimulationAdapter | None:
        cfg = SIMULATION_CATALOG.get(domain)
        if not cfg:
            return None
        return _get_adapter(cfg.adapter_class)

    def list_available(self) -> list[dict[str, Any]]:
        """List available simulation backends with availability status."""
        available = []
        for name, cfg in SIMULATION_CATALOG.items():
            adapter = self._get_adapter(name)
            ok = adapter.is_available() if adapter else False
            available.append({
                "domain": name,
                "engine": cfg.engine,
                "available": ok,
                "gpu_required": cfg.gpu_required,
                "estimated_runtime": f"{cfg.estimated_runtime_seconds}s",
                "cost": f"${cfg.vastai_cost_per_hour}/h on vast.ai" if cfg.gpu_required else "CPU (free)",
            })
        return available

    def estimate_cost(self, domain: str, runtime_hours: float = 1.0) -> dict[str, Any]:
        """Estimate cost for a given domain and runtime."""
        cfg = SIMULATION_CATALOG.get(domain)
        if not cfg:
            return {"error": f"Unknown domain: {domain}"}

        cost = cfg.vastai_cost_per_hour * runtime_hours if cfg.gpu_required else 0.0
        return {
            "domain": domain,
            "engine": cfg.engine,
            "gpu_required": cfg.gpu_required,
            "runtime_hours": runtime_hours,
            "estimated_cost_usd": round(cost, 2),
            "platform": "vast.ai RTX 4090" if cfg.gpu_required else "local CPU",
            "memory_gb": cfg.memory_required_gb,
        }

    def run(self, domain: str, hypothesis: str, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run virtual biology experiment. Returns structured result."""
        cfg = SIMULATION_CATALOG.get(domain)
        if not cfg:
            return {"status": "unavailable", "error": f"No config for domain: {domain}"}

        adapter = self._get_adapter(domain)
        if adapter is None:
            return {
                "status": "unavailable",
                "domain": domain,
                "engine": cfg.engine,
                "hypothesis": hypothesis[:200],
                "install_hint": f"Adapter class {cfg.adapter_class} could not be loaded",
                "estimated_cost": f"${cfg.vastai_cost_per_hour}/h on vast.ai",
            }

        if not adapter.is_available():
            result = adapter._make_unavailable()
            return {
                "status": result.status.value,
                "domain": domain,
                "engine": cfg.engine,
                "hypothesis": hypothesis[:200],
                "install_hint": result.install_hint,
                "estimated_cost": f"${cfg.vastai_cost_per_hour}/h on vast.ai",
            }

        adapter.configure(input_data or {})
        result = adapter.run(input_data)
        return {
            "status": result.status.value,
            "domain": domain,
            "engine": cfg.engine,
            "hypothesis": hypothesis[:200],
            "gpu_required": cfg.gpu_required,
            "estimated_runtime": f"{cfg.estimated_runtime_seconds}s",
            "memory_gb": cfg.memory_required_gb,
            "data": result.data,
            "elapsed_seconds": result.elapsed_seconds,
            "metadata": result.metadata,
            "error_message": result.error_message,
            "install_hint": result.install_hint,
        }
