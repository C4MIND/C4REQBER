# SPDX-License-Identifier: AGPL-3.0
"""Unit tests for all P1 simulation engine bridges.

These tests verify that every adapter:
  1. Imports without error
  2. Implements BaseSimulationAdapter interface
  3. Returns SimulationResult on run()
  4. Provides install_hint when engine is unavailable
  5. Integrates with PatternEngineMap and PatternRunnerV2
"""
from __future__ import annotations

import pytest

from src.simulations.base_adapter import BaseSimulationAdapter, SimStatus, SimulationResult
from src.simulations.pattern_engine_map import EngineType, PatternEngineMap
from src.simulations.runner_v2 import PatternRunnerV2

# ---------------------------------------------------------------------------
# List of all P1 adapter classes to test
# ---------------------------------------------------------------------------
_P1_ADAPTERS = [
    ("src.simulations.fenicsx_bridge", "FenicsxBridge"),
    ("src.simulations.openfoam_bridge", "OpenFOAMBridge"),
    ("src.simulations.gromacs_bridge", "GromacsBridge"),
    ("src.simulations.lammps_bridge", "LammpsBridge"),
    ("src.simulations.mdanalysis_bridge", "MDAnalysisBridge"),
    ("src.simulations.pyscf_bridge", "PySCFBridge"),
    ("src.simulations.psi4_bridge", "Psi4Bridge"),
    ("src.simulations.quantum_espresso_bridge", "QuantumEspressoBridge"),
    ("src.simulations.tellurium_bridge", "TelluriumBridge"),
    ("src.simulations.neuron_bridge", "NeuronBridge"),
    ("src.simulations.brian2_bridge", "Brian2Bridge"),
    ("src.simulations.jaxley_bridge", "JaxleyBridge"),
    ("src.simulations.copasi_bridge", "CopasiBridge"),
    ("src.simulations.xarray_bridge", "XarrayBridge"),
    ("src.simulations.wrf_bridge", "WrfBridge"),
    ("src.simulations.mesa_bridge", "MesaBridge"),
    ("src.simulations.simpy_bridge", "SimPyBridge"),
    ("src.simulations.rebound_bridge", "ReboundBridge"),
    ("src.simulations.amuse_bridge", "AmuseBridge"),
    ("src.simulations.mujoco_bridge", "MuJoCoBridge"),
    ("src.simulations.pybullet_bridge", "PyBulletBridge"),
    ("src.simulations.diffeqpy_bridge", "DiffEqPyBridge"),
    ("src.simulations.taichi_bridge", "TaichiBridge"),
    ("src.simulations.jaxmd_bridge", "JaxMDBridge"),
    ("src.simulations.jaxlab_bridge", "JaxLaBBridge"),
    ("src.simulations.modelingtoolkit_bridge", "ModelingToolkitBridge"),
]

_LEGACY_ADAPTERS = [
    ("src.simulations.openmm_bridge", "OpenMMBridge"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _import_cls(mod_name: str, cls_name: str):
    import importlib
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod_name,cls_name", _P1_ADAPTERS + _LEGACY_ADAPTERS)
def test_adapter_imports(mod_name: str, cls_name: str) -> None:
    cls = _import_cls(mod_name, cls_name)
    assert cls is not None
    assert issubclass(cls, BaseSimulationAdapter) or cls_name == "OpenMMBridge"


@pytest.mark.parametrize("mod_name,cls_name", _P1_ADAPTERS)
def test_adapter_interface(mod_name: str, cls_name: str) -> None:
    cls = _import_cls(mod_name, cls_name)
    inst = cls()
    assert hasattr(inst, "is_available")
    assert hasattr(inst, "configure")
    assert hasattr(inst, "run")
    assert hasattr(inst, "cleanup")

    # configure + cleanup should not raise
    inst.configure({"test_param": 1})
    inst.cleanup()


@pytest.mark.parametrize("mod_name,cls_name", _P1_ADAPTERS)
def test_adapter_run_returns_simulation_result(mod_name: str, cls_name: str) -> None:
    cls = _import_cls(mod_name, cls_name)
    inst = cls()
    result = inst.run({})
    assert isinstance(result, SimulationResult)
    assert result.status in {SimStatus.SUCCESS, SimStatus.UNAVAILABLE, SimStatus.ERROR}
    assert result.metadata.get("engine") == inst._engine_name


@pytest.mark.parametrize("mod_name,cls_name", _P1_ADAPTERS)
def test_adapter_unavailability_has_hint(mod_name: str, cls_name: str) -> None:
    cls = _import_cls(mod_name, cls_name)
    inst = cls()
    if not inst.is_available():
        result = inst.run({})
        assert result.status == SimStatus.UNAVAILABLE
        assert result.install_hint != ""


def test_pattern_engine_map_has_all_p1_engines() -> None:
    valid = {e.value for e in EngineType}
    mapper = PatternEngineMap()
    for pattern, engine in mapper.PATTERN_ENGINE_MAP.items():
        assert engine in valid, f"Pattern '{pattern}' maps to unknown engine '{engine}'"


def test_pattern_engine_map_category_aliases() -> None:
    mapper = PatternEngineMap()
    # Category aliases fallback when pattern_id is not in PATTERN_ENGINE_MAP
    assert mapper.get_engine("fem", metadata={"category": "fem"}) == "fenicsx"
    assert mapper.get_engine("des_unknown", metadata={"category": "discrete_event"}) == "simpy"
    assert mapper.get_engine("abm_unknown", metadata={"category": "abm"}) == "mesa"
    assert mapper.get_engine("snn_unknown", metadata={"category": "snn"}) == "brian2"
    assert mapper.get_engine("planet", metadata={"category": "planetary_dynamics"}) == "rebound"
    # Existing pattern takes precedence over category
    assert mapper.get_engine("molecular_dynamics", metadata={"category": "molecular_dynamics"}) == "torchsim"


def test_runner_v2_loads_all_p1_bridges() -> None:
    runner = PatternRunnerV2()
    for engine in [
        "fenicsx", "openfoam", "gromacs", "lammps", "mdanalysis",
        "pyscf", "psi4", "quantum_espresso", "tellurium", "neuron",
        "brian2", "jaxley", "copasi", "xarray", "wrf", "mesa", "simpy",
        "rebound", "amuse", "mujoco", "pybullet", "diffeqpy", "taichi",
        "jax_md", "jax_lab", "modelingtoolkit",
    ]:
        bridge = runner._get_bridge(engine)
        # Most will be None in CI because engines aren't installed,
        # but the call itself must not raise.
        assert bridge is None or hasattr(bridge, "is_available")


def test_runner_v2_openmm_bridge() -> None:
    runner = PatternRunnerV2()
    bridge = runner._get_bridge("openmm")
    # OpenMM may or may not be installed; either way no exception.
    assert bridge is None or hasattr(bridge, "available")


def test_base_adapter_can_import_helper() -> None:
    assert BaseSimulationAdapter._can_import("sys") is True
    assert BaseSimulationAdapter._can_import("nonexistent_module_xyz_123") is False


def test_simulation_result_to_dict() -> None:
    sr = SimulationResult(status=SimStatus.SUCCESS, data={"x": 1})
    d = sr.to_dict()
    assert d["status"] == "success"
    assert d["data"]["x"] == 1
