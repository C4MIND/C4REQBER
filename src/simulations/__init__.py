"""c4-cdi-turbo Simulations Module.

Provides physics simulation bridges and auto-engine capabilities.
"""

import logging

_logger = logging.getLogger(__name__)

try:
    from .base_adapter import BaseSimulationAdapter, SimulationResult, SimStatus
except ImportError as e:
    _logger.debug("base_adapter not available: %s", e)
    BaseSimulationAdapter = None  # type: ignore
    SimulationResult = None  # type: ignore
    SimStatus = None  # type: ignore

try:
    from .auto_engine import PhysicsAutoDetector, get_detector
except ImportError as e:
    _logger.debug("auto_engine not available: %s", e)
    PhysicsAutoDetector = None  # type: ignore
    get_detector = None  # type: ignore

try:
    from .jaxsim_bridge import (
        InverseDynamicsConfig,
        JaxSimBridge,
        RigidBodyConfig,
    )
except ImportError as e:
    _logger.debug("jaxsim_bridge not available: %s", e)
    InverseDynamicsConfig = None  # type: ignore
    JaxSimBridge = None  # type: ignore
    RigidBodyConfig = None  # type: ignore

try:
    from .newton_bridge import (
        NewtonBridge,
        NewtonConfig,
        NewtonMode,
        NewtonResult,
        get_bridge,
    )
except ImportError as e:
    _logger.debug("newton_bridge not available: %s", e)
    NewtonBridge = None  # type: ignore
    NewtonConfig = None  # type: ignore
    NewtonMode = None  # type: ignore
    NewtonResult = None  # type: ignore
    get_bridge = None  # type: ignore

try:
    from .pattern_engine_map import (
        EngineType,
        PatternEngineMap,
        PatternMetadata,
        get_engine,
        get_gpu_accelerated_patterns,
    )
except ImportError as e:
    _logger.debug("pattern_engine_map not available: %s", e)
    EngineType = None  # type: ignore
    PatternEngineMap = None  # type: ignore
    PatternMetadata = None  # type: ignore
    get_engine = None  # type: ignore
    get_gpu_accelerated_patterns = None  # type: ignore

try:
    from .runner_v2 import PatternRunnerV2, get_runner_v2
except ImportError as e:
    _logger.debug("runner_v2 not available: %s", e)
    PatternRunnerV2 = None  # type: ignore
    get_runner_v2 = None  # type: ignore

try:
    from .schr_bridge import QEDConfig, SchrBridge, SchrodingerConfig
except ImportError as e:
    _logger.debug("schr_bridge not available: %s", e)
    QEDConfig = None  # type: ignore
    SchrBridge = None  # type: ignore
    SchrodingerConfig = None  # type: ignore

try:
    from .torchsim_bridge import (
        MDIntegrator,
        RelaxationMethod,
        TorchSimBridge,
        TorchSimResult,
        get_torchsim_bridge,
    )
except ImportError as e:
    _logger.debug("torchsim_bridge not available: %s", e)
    MDIntegrator = None  # type: ignore
    RelaxationMethod = None  # type: ignore
    TorchSimBridge = None  # type: ignore
    TorchSimResult = None  # type: ignore
    get_torchsim_bridge = None  # type: ignore

try:
    from .vastai_delegate import VastAIDelegate, get_vastai_delegate
except ImportError as e:
    _logger.debug("vastai_delegate not available: %s", e)
    VastAIDelegate = None  # type: ignore
    get_vastai_delegate = None  # type: ignore

try:
    from .openmm_bridge import OpenMMBridge, get_openmm_bridge
except ImportError as e:
    _logger.debug("openmm_bridge not available: %s", e)
    OpenMMBridge = None  # type: ignore
    get_openmm_bridge = None  # type: ignore

# P1 bridges — lazy import with graceful fallback
_P1_BRIDGE_NAMES = [
    ("fenicsx_bridge", "FenicsxBridge"),
    ("openfoam_bridge", "OpenFOAMBridge"),
    ("gromacs_bridge", "GromacsBridge"),
    ("lammps_bridge", "LammpsBridge"),
    ("mdanalysis_bridge", "MDAnalysisBridge"),
    ("pyscf_bridge", "PySCFBridge"),
    ("psi4_bridge", "Psi4Bridge"),
    ("quantum_espresso_bridge", "QuantumEspressoBridge"),
    ("tellurium_bridge", "TelluriumBridge"),
    ("neuron_bridge", "NeuronBridge"),
    ("brian2_bridge", "Brian2Bridge"),
    ("jaxley_bridge", "JaxleyBridge"),
    ("copasi_bridge", "CopasiBridge"),
    ("xarray_bridge", "XarrayBridge"),
    ("wrf_bridge", "WrfBridge"),
    ("mesa_bridge", "MesaBridge"),
    ("simpy_bridge", "SimPyBridge"),
    ("rebound_bridge", "ReboundBridge"),
    ("amuse_bridge", "AmuseBridge"),
    ("mujoco_bridge", "MuJoCoBridge"),
    ("pybullet_bridge", "PyBulletBridge"),
    ("diffeqpy_bridge", "DiffEqPyBridge"),
    ("taichi_bridge", "TaichiBridge"),
    ("jaxmd_bridge", "JaxMDBridge"),
    ("jaxlab_bridge", "JaxLaBBridge"),
    ("modelingtoolkit_bridge", "ModelingToolkitBridge"),
]

for _mod_name, _cls_name in _P1_BRIDGE_NAMES:
    try:
        _mod = __import__(f"src.simulations.{_mod_name}", fromlist=[_cls_name])
        globals()[_cls_name] = getattr(_mod, _cls_name)
    except Exception as _exc:
        _logger.debug("%s not available: %s", _cls_name, _exc)
        globals()[_cls_name] = None  # type: ignore

__all__ = [
    "BaseSimulationAdapter",
    "SimulationResult",
    "SimStatus",
    "NewtonBridge",
    "NewtonConfig",
    "NewtonMode",
    "NewtonResult",
    "get_bridge",
    "JaxSimBridge",
    "RigidBodyConfig",
    "InverseDynamicsConfig",
    "TorchSimBridge",
    "TorchSimResult",
    "MDIntegrator",
    "RelaxationMethod",
    "get_torchsim_bridge",
    "SchrBridge",
    "SchrodingerConfig",
    "QEDConfig",
    "VastAIDelegate",
    "get_vastai_delegate",
    "PatternRunnerV2",
    "get_runner_v2",
    "PhysicsAutoDetector",
    "get_detector",
    "PatternEngineMap",
    "EngineType",
    "PatternMetadata",
    "get_engine",
    "get_gpu_accelerated_patterns",
    "OpenMMBridge",
    "get_openmm_bridge",
    # P1 bridges
    "FenicsxBridge",
    "OpenFOAMBridge",
    "GromacsBridge",
    "LammpsBridge",
    "MDAnalysisBridge",
    "PySCFBridge",
    "Psi4Bridge",
    "QuantumEspressoBridge",
    "TelluriumBridge",
    "NeuronBridge",
    "Brian2Bridge",
    "JaxleyBridge",
    "CopasiBridge",
    "XarrayBridge",
    "WrfBridge",
    "MesaBridge",
    "SimPyBridge",
    "ReboundBridge",
    "AmuseBridge",
    "MuJoCoBridge",
    "PyBulletBridge",
    "DiffEqPyBridge",
    "TaichiBridge",
    "JaxMDBridge",
    "JaxLaBBridge",
    "ModelingToolkitBridge",
]
