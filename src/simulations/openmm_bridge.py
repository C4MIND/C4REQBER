"""OpenMM Bridge — Molecular dynamics for protein folding simulations."""

from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class OpenMMBridge(BaseSimulationAdapter):
    """Bridge to OpenMM molecular dynamics engine.

    Used in Virtual Biology simulations for protein folding,
    ligand binding, and free energy calculations.

    GPU-aware: set platform="CUDA" or "OpenCL" for GPU acceleration.
    On macOS use "CPU" (OpenMM does not support Metal).
    """

    _engine_name = "openmm"
    _package_checks = ["openmm", "openmm.app", "openmm.unit"]
    _install_hint = (
        "conda install -c conda-forge openmm  (or)  "
        "pip install openmm.  "
        "For GPU: CUDA on Linux, OpenCL on macOS/AMD.  "
        "Note: Metal is not supported by OpenMM."
    )

    def __init__(self, platform: str = "CPU") -> None:
        super().__init__()
        self.platform_name = platform

    # Backward-compat property used by runner_v2
    @property
    def available(self) -> bool:
        return self.is_available()

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        self.platform_name = params.get("platform", self.platform_name)

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            result = self.simulate_protein(**data)
            if "error" in result:
                raise RuntimeError(result["error"])
            return result

        return self._run_wrapped(_run, input_data)

    def simulate_protein(
        self,
        pdb_data: str | None = None,
        pdb_id: str = "1CRN",
        steps: int = 10000,
        temperature_k: float = 300.0,
        pressure_atm: float = 1.0,
    ) -> dict[str, Any]:
        """Run a protein folding simulation.

        Args:
            pdb_data: PDB file content (or None to fetch from RCSB)
            pdb_id: PDB ID to fetch if no pdb_data provided
            steps: Number of simulation steps
            temperature_k: Temperature in Kelvin
            pressure_atm: Pressure in atmospheres

        Returns:
            dict with potential_energy, temperature, volume, final_coordinates
        """
        if not self.is_available():
            return {"error": "OpenMM not installed"}
        try:
            import openmm.app as app
            import openmm.unit as unit
            from openmm import (
                LangevinMiddleIntegrator,
                MonteCarloBarostat,
                Platform,
                System,
            )

            if pdb_data:
                from io import StringIO
                pdb = app.PDBFile(StringIO(pdb_data))
            else:
                pdb = app.PDBFile(f"https://files.rcsb.org/download/{pdb_id}.pdb")

            forcefield = app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")
            modeller = app.Modeller(pdb.topology, pdb.positions)
            modeller.addHydrogens(forcefield)
            modeller.addSolvent(forcefield, padding=1.0 * unit.nanometers)

            system: System = forcefield.createSystem(
                modeller.topology,
                nonbondedMethod=app.PME,
                nonbondedCutoff=1.0 * unit.nanometers,
                constraints=app.HBonds,
            )

            integrator = LangevinMiddleIntegrator(
                temperature_k * unit.kelvin,
                1.0 / unit.picoseconds,
                0.002 * unit.picoseconds,
            )

            system.addForce(MonteCarloBarostat(pressure_atm * unit.atmospheres, temperature_k * unit.kelvin))

            simulation = app.Simulation(
                modeller.topology, system, integrator,
                Platform.getPlatformByName(self.platform_name),
            )
            simulation.context.setPositions(modeller.positions)

            simulation.minimizeEnergy()
            simulation.reporters.append(
                app.StateDataReporter(
                    "openmm_output.csv", 100, step=True,
                    potentialEnergy=True, temperature=True, volume=True,
                )
            )
            simulation.step(steps)

            state = simulation.context.getState(getEnergy=True, getPositions=True)
            energy = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
            coords = state.getPositions(asNumpy=True)

            return {
                "potential_energy_kj_mol": round(float(energy), 2),
                "steps": steps,
                "temperature_k": temperature_k,
                "atom_count": len(coords),
                "final_coordinates_sample": coords[:5].tolist() if len(coords) > 0 else [],
            }
        except Exception as e:
            logger.error("OpenMM simulation failed: %s", e)
            return {"error": str(e)}

    async def test_connection(self) -> dict[str, Any]:
        if not self.is_available():
            return {"healthy": False, "error": "OpenMM not installed"}
        return {"healthy": True, "platform": self.platform_name}


def get_openmm_bridge() -> OpenMMBridge:
    return OpenMMBridge()
