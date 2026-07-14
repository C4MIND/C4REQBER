"""Probe simulation engines and formal verifiers for TUI capabilities overlay."""
from __future__ import annotations

import importlib
import os
import platform
import shutil
import time
from dataclasses import dataclass, field
from typing import Any

from src.config.paths import load_verifiers_env
from src.simulations.auto_engine import PhysicsAutoDetector


# Engine registry: (id, display_name, bridge_module, bridge_class, domain, tier, mac_native)
_ENGINE_SPECS: list[tuple[str, str, str, str, str, str, bool]] = [
    ("newton", "Newton", "newton_bridge", "NewtonBridge", "physics", "fast", True),
    ("torchsim", "TorchSim", "torchsim_bridge", "TorchSimBridge", "physics", "fast", True),
    ("jaxsim", "JaxSim", "jaxsim_bridge", "JaxSimBridge", "physics", "fast", True),
    ("schr", "Schrödinger", "schr_bridge", "SchrBridge", "quantum", "slow", True),
    ("openmm", "OpenMM", "openmm_bridge", "OpenMMBridge", "biology", "slow", True),
    ("vina", "AutoDock Vina", "vina_bridge", "VinaBridge", "biology", "slow", True),
    ("boolnet", "BoolNet", "boolnet_bridge", "BoolNetBridge", "biology", "slow", True),
    ("cobra", "COBRApy", "cobra_bridge", "CobraBridge", "biology", "slow", True),
    ("slim", "SLiM", "slim_bridge", "SlimBridge", "biology", "linux_only", False),
    ("fenicsx", "FEniCSx", "fenicsx_bridge", "FenicsxBridge", "physics", "slow", True),
    ("openfoam", "OpenFOAM", "openfoam_bridge", "OpenFOAMBridge", "physics", "slow", True),
    ("gromacs", "GROMACS", "gromacs_bridge", "GromacsBridge", "chemistry", "slow", True),
    ("lammps", "LAMMPS", "lammps_bridge", "LammpsBridge", "materials", "slow", True),
    ("mdanalysis", "MDAnalysis", "mdanalysis_bridge", "MDAnalysisBridge", "chemistry", "slow", True),
    ("pyscf", "PySCF", "pyscf_bridge", "PySCFBridge", "quantum", "slow", True),
    ("psi4", "Psi4", "psi4_bridge", "Psi4Bridge", "quantum", "slow", True),
    ("quantum_espresso", "Quantum ESPRESSO", "quantum_espresso_bridge", "QuantumEspressoBridge", "quantum", "slow", True),
    ("tellurium", "Tellurium", "tellurium_bridge", "TelluriumBridge", "biology", "slow", True),
    ("neuron", "NEURON", "neuron_bridge", "NeuronBridge", "neuroscience", "slow", True),
    ("brian2", "Brian2", "brian2_bridge", "Brian2Bridge", "neuroscience", "slow", True),
    ("jaxley", "Jaxley", "jaxley_bridge", "JaxleyBridge", "neuroscience", "slow", True),
    ("copasi", "COPASI", "copasi_bridge", "CopasiBridge", "biology", "slow", True),
    ("xarray", "xarray", "xarray_bridge", "XarrayBridge", "climate", "slow", True),
    ("wrf", "WRF", "wrf_bridge", "WrfBridge", "climate", "slow", True),
    ("mesa", "Mesa", "mesa_bridge", "MesaBridge", "economics", "slow", True),
    ("simpy", "SimPy", "simpy_bridge", "SimPyBridge", "general", "slow", True),
    ("rebound", "Rebound", "rebound_bridge", "ReboundBridge", "astrophysics", "slow", True),
    ("amuse", "AMUSE", "amuse_bridge", "AmuseBridge", "astrophysics", "slow", True),
    ("mujoco", "MuJoCo", "mujoco_bridge", "MuJoCoBridge", "robotics", "fast", True),
    ("pybullet", "PyBullet", "pybullet_bridge", "PyBulletBridge", "robotics", "slow", True),
    ("diffeqpy", "DiffEqPy", "diffeqpy_bridge", "DiffEqPyBridge", "physics", "slow", True),
    ("taichi", "Taichi", "taichi_bridge", "TaichiBridge", "physics", "fast", True),
    ("jax_md", "JAX-MD", "jaxmd_bridge", "JaxMDBridge", "physics", "fast", True),
    ("jax_lab", "JAX-LaB", "jaxlab_bridge", "JaxLaBBridge", "biology", "slow", True),
    ("modelingtoolkit", "ModelingToolkit", "modelingtoolkit_bridge", "ModelingToolkitBridge", "physics", "slow", True),
    ("vastai", "Vast.ai", "vastai_delegate", "VastAIDelegate", "general", "cloud", True),
    ("nvidia", "NVIDIA Brev", "nvidia_bridge", "NvidiaBridge", "general", "cloud", True),
]

_VERIFIER_SPECS: list[tuple[str, str, str, str]] = [
    ("lean4", "Lean 4", "lean4_client", "Lean4Client", "brew install elan-init && elan default stable"),
    ("coq", "Coq/Rocq", "coq_client", "CoqClient", "brew install coq"),
    ("dafny", "Dafny", "dafny_client", "DafnyClient", "brew install dafny"),
    ("agda", "Agda", "agda_bridge", "AgdaBridge", "brew install agda"),
    ("z3", "Z3 SMT", "hoare_verifier", "HoareVerifier", "pip install z3-solver"),
    ("cvc5", "CVC5", "cvc5_client", "CVC5Client", "bash tools/install-verifiers.sh"),
    ("hoare", "Hoare/Z3", "hoare_verifier", "HoareVerifier", "pip install z3-solver"),
    ("tla", "TLA+", "tla_client", "TLAClient", "bash tools/install-verifiers.sh  # downloads tla2tools.jar"),
    ("alloy", "Alloy", "alloy_client", "AlloyClient", "brew install alloy-analyzer"),
    ("haskell", "Haskell", "haskell_bridge", "_find_ghc", "brew install ghc"),
]


@dataclass
class CapabilitiesReport:
    platform: dict[str, str]
    hardware: dict[str, Any]
    engines: list[dict[str, Any]] = field(default_factory=list)
    verifiers: list[dict[str, Any]] = field(default_factory=list)
    domains: list[dict[str, Any]] = field(default_factory=list)
    probe_timestamp: str = ""
    probe_latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "hardware": self.hardware,
            "engines": self.engines,
            "verifiers": self.verifiers,
            "domains": self.domains,
            "probe_timestamp": self.probe_timestamp,
            "probe_latency_ms": self.probe_latency_ms,
        }


def _probe_bridge(module_name: str, class_name: str) -> tuple[bool, str, str]:
    """Return (available, install_hint, missing_reason)."""
    try:
        mod = importlib.import_module(f"src.simulations.{module_name}")
        cls = getattr(mod, class_name, None)
        if cls is None:
            return False, "", "module not loaded"
        inst = cls()
        if hasattr(inst, "available"):
            ok = bool(inst.available)
        elif hasattr(inst, "is_available"):
            ok = bool(inst.is_available())
        elif hasattr(inst, "_check_available"):
            ok = bool(inst._check_available())
        else:
            ok = True
        hint = getattr(cls, "_install_hint", "") or getattr(inst, "_install_hint", "")
        if ok:
            return True, hint, ""
        return False, hint, "not installed"
    except Exception as exc:
        return False, "", str(exc)[:120]


def _probe_verifier(module_name: str, class_name: str) -> tuple[bool, str, str]:
    try:
        mod = importlib.import_module(f"src.verification.{module_name}")
        if class_name.startswith("_"):
            fn = getattr(mod, class_name)
            path = fn() if callable(fn) else ""
            return bool(path), str(path or ""), ""
        cls = getattr(mod, class_name)
        inst = cls()
        if hasattr(inst, "test_connection"):
            ok = bool(inst.test_connection())
        elif hasattr(inst, "available"):
            ok = bool(inst.available)
        elif hasattr(inst, "is_available"):
            ok = bool(inst.is_available())
        else:
            ok = True
        path = ""
        for attr in ("cvc5_path", "alloy_path", "tlc_path", "jar_path", "lean_path"):
            if hasattr(inst, attr) and getattr(inst, attr):
                path = str(getattr(inst, attr))
                break
        if not path and class_name == "Lean4Client":
            path = shutil.which("lean") or ""
        if not path and class_name == "CoqClient":
            path = shutil.which("coqc") or ""
        return ok, path, ""
    except Exception as exc:
        return False, "", str(exc)[:120]


def probe_capabilities() -> CapabilitiesReport:
    """Build full capabilities report for TUI overlay."""
    load_verifiers_env()
    t0 = time.perf_counter()
    detector = PhysicsAutoDetector()
    detector._lazy_init()

    import datetime

    hw: dict[str, Any] = {
        "metal": detector.has_apple_silicon,
        "cuda": detector.has_nvidia_gpu,
        "apple_silicon": detector.has_apple_silicon,
        "gpu_name": detector._gpu_name or "CPU",
        "gpu_memory_gb": detector._gpu_memory_gb or 0.0,
        "cpu_count": os.cpu_count() or 0,
        "ram_gb": 0.0,
    }
    try:
        import psutil

        hw["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        pass

    engines: list[dict[str, Any]] = []
    domain_buckets: dict[str, list[str]] = {}

    for eid, name, mod, cls, domain, tier, mac_native in _ENGINE_SPECS:
        avail, hint, reason = _probe_bridge(mod, cls)
        if tier == "linux_only" and platform.system() == "Darwin":
            status = "unavailable"
            reason = reason or "linux only"
        elif avail:
            status = "available" if tier in ("fast", "cloud") else "slow"
        else:
            status = "unavailable"
        engines.append({
            "id": eid,
            "name": name,
            "domain": domain,
            "status": status,
            "mac_native": mac_native,
            "tier": tier,
            "install_hint": hint,
            "missing_reason": reason,
        })
        domain_buckets.setdefault(domain, []).append(eid)

    verifiers: list[dict[str, Any]] = []
    seen: set[str] = set()
    for vid, vname, mod, cls, hint in _VERIFIER_SPECS:
        if vid in seen:
            continue
        seen.add(vid)
        if vid == "z3":
            try:
                import z3  # noqa: F401
                avail, path = True, "python:z3"
            except ImportError:
                avail, path = False, ""
        else:
            avail, path, _ = _probe_verifier(mod, cls)
        verifiers.append({
            "id": vid,
            "name": vname,
            "available": avail,
            "version": "",
            "path": path,
            "install_hint": hint if not avail else "",
        })

    domains = [{"domain": d, "engines": ids} for d, ids in sorted(domain_buckets.items())]
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return CapabilitiesReport(
        platform={"system": platform.system(), "arch": platform.machine()},
        hardware=hw,
        engines=engines,
        verifiers=verifiers,
        domains=domains,
        probe_timestamp=datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        probe_latency_ms=elapsed_ms,
    )
