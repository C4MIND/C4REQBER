"""
PatternRunnerV2 - Enhanced PatternRunner with multi-engine GPU acceleration.

Inherits from PatternRunner and adds transparent GPU acceleration via
Newton, TorchSim, JaxSim, and Schr bridges.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from src.patterns.runner import PatternRunner

from .auto_engine import PhysicsAutoDetector
from .pattern_engine_map import PatternEngineMap


logger = logging.getLogger(__name__)


class PatternRunnerV2(PatternRunner):
    """
    Enhanced PatternRunner with multi-engine GPU acceleration.

    Extends the base PatternRunner with:
    - Automatic engine selection based on pattern type
    - GPU acceleration via Newton, TorchSim, JaxSim, Schr
    - Batch execution with parallelization support
    - Benchmarking legacy vs accelerated execution
    """

    def __init__(self) -> None:
        super().__init__()
        self.auto_detector = PhysicsAutoDetector()
        self.engine_map = PatternEngineMap()
        self._bridges: dict[str, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _get_bridge(self, engine: str) -> Any | None:
        """Get or create engine bridge (lazy loading).

        Supports all P1 simulation engines plus legacy internals.
        """
        if engine in self._bridges:
            return self._bridges[engine]

        bridge = None

        # Legacy internal bridges (may use .available property instead of .is_available())
        if engine == "newton":
            try:
                from .newton_bridge import NewtonBridge

                bridge = NewtonBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("Newton bridge failed: %s", exc)

        elif engine == "torchsim":
            try:
                from .torchsim_bridge import TorchSimBridge

                bridge = TorchSimBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("TorchSim bridge failed: %s", exc)

        elif engine == "jaxsim":
            try:
                from .jaxsim_bridge import JaxSimBridge

                bridge = JaxSimBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("JaxSim bridge failed: %s", exc)

        elif engine == "schr":
            try:
                from .schr_bridge import SchrBridge

                bridge = SchrBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("Schr bridge failed: %s", exc)

        elif engine == "openmm":
            try:
                from .openmm_bridge import OpenMMBridge

                bridge = OpenMMBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("OpenMM bridge failed: %s", exc)

        elif engine == "vina":
            try:
                from .vina_bridge import VinaBridge

                bridge = VinaBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("Vina bridge failed: %s", exc)

        elif engine == "boolnet":
            try:
                from .boolnet_bridge import BoolNetBridge

                bridge = BoolNetBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("BoolNet bridge failed: %s", exc)

        elif engine == "cobra":
            try:
                from .cobra_bridge import CobraBridge

                bridge = CobraBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("COBRApy bridge failed: %s", exc)

        elif engine == "slim":
            try:
                from .slim_bridge import SlimBridge

                bridge = SlimBridge()
                if not bridge.is_available():
                    bridge = None
            except Exception as exc:
                logger.debug("SLiM bridge failed: %s", exc)

        else:
            # P1 external bridges — all inherit BaseSimulationAdapter
            _p1_table = {
                "fenicsx": ("src.simulations.fenicsx_bridge", "FenicsxBridge"),
                "openfoam": ("src.simulations.openfoam_bridge", "OpenFOAMBridge"),
                "gromacs": ("src.simulations.gromacs_bridge", "GromacsBridge"),
                "lammps": ("src.simulations.lammps_bridge", "LammpsBridge"),
                "mdanalysis": ("src.simulations.mdanalysis_bridge", "MDAnalysisBridge"),
                "pyscf": ("src.simulations.pyscf_bridge", "PySCFBridge"),
                "psi4": ("src.simulations.psi4_bridge", "Psi4Bridge"),
                "quantum_espresso": (
                    "src.simulations.quantum_espresso_bridge",
                    "QuantumEspressoBridge",
                ),
                "tellurium": ("src.simulations.tellurium_bridge", "TelluriumBridge"),
                "neuron": ("src.simulations.neuron_bridge", "NeuronBridge"),
                "brian2": ("src.simulations.brian2_bridge", "Brian2Bridge"),
                "jaxley": ("src.simulations.jaxley_bridge", "JaxleyBridge"),
                "copasi": ("src.simulations.copasi_bridge", "CopasiBridge"),
                "xarray": ("src.simulations.xarray_bridge", "XarrayBridge"),
                "wrf": ("src.simulations.wrf_bridge", "WrfBridge"),
                "mesa": ("src.simulations.mesa_bridge", "MesaBridge"),
                "simpy": ("src.simulations.simpy_bridge", "SimPyBridge"),
                "rebound": ("src.simulations.rebound_bridge", "ReboundBridge"),
                "amuse": ("src.simulations.amuse_bridge", "AmuseBridge"),
                "mujoco": ("src.simulations.mujoco_bridge", "MuJoCoBridge"),
                "pybullet": ("src.simulations.pybullet_bridge", "PyBulletBridge"),
                "diffeqpy": ("src.simulations.diffeqpy_bridge", "DiffEqPyBridge"),
                "taichi": ("src.simulations.taichi_bridge", "TaichiBridge"),
                "jax_md": ("src.simulations.jaxmd_bridge", "JaxMDBridge"),
                "jax_lab": ("src.simulations.jaxlab_bridge", "JaxLaBBridge"),
                "modelingtoolkit": (
                    "src.simulations.modelingtoolkit_bridge",
                    "ModelingToolkitBridge",
                ),
            }
            if engine in _p1_table:
                mod_name, cls_name = _p1_table[engine]
                try:
                    import importlib

                    mod = importlib.import_module(mod_name)
                    cls = getattr(mod, cls_name)
                    bridge = cls()
                    if not bridge.is_available():
                        logger.debug("%s bridge not available (engine not installed)", engine)
                        bridge = None
                except Exception as exc:
                    logger.debug("%s bridge import failed: %s", engine, exc)

        self._bridges[engine] = bridge
        return bridge

    def _determine_engine(
        self, pattern_id: str, engine: str | None = None, force_cpu: bool = False
    ) -> str:
        """
        Determine the best engine for a pattern.

        Args:
            pattern_id: Pattern identifier
            engine: Force specific engine (None = auto)
            force_cpu: Force CPU mode

        Returns:
            Engine name to use
        """
        if engine:
            return engine.lower()

        if force_cpu:
            return "legacy"

        recommended = self.engine_map.get_engine(pattern_id)

        if recommended == "legacy":
            return "legacy"

        if not self.auto_detector.has_gpu:
            logger.debug("No GPU available, using legacy CPU")
            return "legacy"

        return recommended

    def run(
        self,
        pattern_id: str,
        hypothesis: dict | None = None,
        engine: str | None = None,
        force_cpu: bool = False,
    ) -> dict:
        """
        Run pattern with optimal engine.

        Args:
            pattern_id: Pattern identifier
            hypothesis: Simulation parameters
            engine: Force specific engine (None = auto)
            force_cpu: Force CPU mode (disable GPU)

        Returns:
            Simulation result with engine info
        """
        instance = self._patterns.get(pattern_id)
        if instance is None:
            return {
                "pattern_id": pattern_id,
                "status": "failed",
                "error": f"Pattern '{pattern_id}' not found",
                "engine": "none",
                "timestamp": datetime.now().isoformat(),
            }

        selected_engine = self._determine_engine(pattern_id, engine, force_cpu)

        start_time = time.perf_counter()

        if selected_engine == "legacy":
            result = self._run_legacy(pattern_id, instance, hypothesis)
        else:
            result = self._run_with_bridge(pattern_id, instance, hypothesis, selected_engine)

        execution_time = time.perf_counter() - start_time

        result["engine"] = selected_engine
        result["execution_time_seconds"] = execution_time
        result["timestamp"] = datetime.now().isoformat()

        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["gpu_available"] = self.auto_detector.has_gpu
        result["metadata"]["gpu_name"] = self.auto_detector.gpu_name
        result["metadata"]["forced_engine"] = engine is not None
        result["metadata"]["forced_cpu"] = force_cpu

        return result

    def _run_legacy(self, pattern_id: str, instance: Any, hypothesis: dict | None) -> dict:
        """Run pattern with legacy CPU implementation."""
        try:
            if hasattr(instance, "run"):
                run_method = instance.run

                if inspect.iscoroutinefunction(run_method):
                    loop = asyncio.new_event_loop()
                    try:
                        result = loop.run_until_complete(
                            self._run_async_pattern(run_method, hypothesis)
                        )
                    finally:
                        loop.close()
                else:
                    result = run_method(hypothesis)

                if hasattr(result, "__dict__") and not isinstance(result, dict):
                    result = result.__dict__
                elif not isinstance(result, dict):
                    result = {"output": str(result)}

                return self._finalize_result(
                    {
                        "pattern_id": pattern_id,
                        "result": result,
                        "accelerated": False,
                        "executed": True,
                    },
                    default_ok_status="completed",
                )
            else:
                return {
                    "pattern_id": pattern_id,
                    "status": "failed",
                    "error": "Pattern has no run() method",
                    "accelerated": False,
                    "executed": False,
                }
        except Exception as e:
            logger.exception(f"Legacy run failed for {pattern_id}")
            return {
                "pattern_id": pattern_id,
                "status": "failed",
                "error": str(e),
                "accelerated": False,
                "executed": False,
            }

    async def _run_async_pattern(self, run_method: Any, hypothesis: dict | None) -> Any:
        """Run async pattern method."""
        return await run_method(hypothesis)

    @staticmethod
    def _finalize_result(result: dict, *, default_ok_status: str = "completed") -> dict:
        """Normalize status — never invent SUCCESS/completed over stub/unavailable."""
        if not isinstance(result, dict):
            return {"status": "failed", "error": "non-dict result", "executed": False}

        incomplete_statuses = {
            "unavailable",
            "failed",
            "error",
            "skipped",
            "simulated",
            "not_implemented",
            "partial",
        }

        nested = result.get("result")
        if isinstance(nested, dict):
            if nested.get("stub") is True or nested.get("executed") is False:
                result["status"] = "unavailable"
                result["stub"] = True
                result["executed"] = False
                result["accelerated"] = False
                result.setdefault("note", nested.get("note") or "nested stub/unavailable")
                return result
            nested_status = str(nested.get("status", "")).lower()
            if nested_status in incomplete_statuses:
                result["status"] = nested_status
                result["stub"] = bool(nested.get("stub", nested_status != "partial"))
                result["executed"] = bool(nested.get("executed", False))
                result["accelerated"] = False
                return result

        if result.get("stub") is True or result.get("executed") is False:
            result["status"] = str(result.get("status") or "unavailable")
            if result["status"] not in incomplete_statuses:
                result["status"] = "unavailable"
            result["accelerated"] = False
            return result

        status = str(result.get("status", "")).lower()
        if status in incomplete_statuses:
            result["accelerated"] = False
            return result

        # Missing status: only promote if explicitly executed and not stub
        if "status" not in result or not status:
            if result.get("executed") is True and result.get("stub") is not True:
                result["status"] = default_ok_status
            else:
                result["status"] = "unavailable"
                result["stub"] = True
                result["executed"] = False
                result["accelerated"] = False
                result.setdefault(
                    "note",
                    "Missing status/executed — refusing invented completed",
                )
        return result

    def _run_with_bridge(
        self, pattern_id: str, instance: Any, hypothesis: dict | None, engine: str
    ) -> dict:
        """Run pattern with GPU-accelerated bridge."""
        bridge = self._get_bridge(engine)

        if bridge is None:
            logger.info(f"Bridge '{engine}' unavailable, falling back to legacy")
            legacy = self._run_legacy(pattern_id, instance, hypothesis)
            legacy["fallback_reason"] = f"bridge '{engine}' unavailable"
            legacy["accelerated"] = False
            legacy["engine_truth"] = "legacy_fallback"
            return legacy

        try:
            if hasattr(bridge, "accelerate_pattern"):
                result = bridge.accelerate_pattern(instance, hypothesis or {})
            elif hasattr(bridge, "run"):
                # Prefer adapter.run when accelerate_pattern is absent
                sim = bridge.run(hypothesis or {})
                if hasattr(sim, "to_dict"):
                    result = sim.to_dict()
                elif isinstance(sim, dict):
                    result = sim
                else:
                    result = {"output": str(sim)}
                result["accelerated"] = False
            else:
                result = self._run_legacy(pattern_id, instance, hypothesis)
                result["accelerated"] = False
                result["fallback_reason"] = f"bridge '{engine}' has no run/accelerate"

            if isinstance(result, dict):
                # Never invent accelerated=True
                if "accelerated" not in result:
                    result["accelerated"] = False
                result["pattern_id"] = pattern_id
                return self._finalize_result(result, default_ok_status="completed")
            return self._finalize_result(
                {
                    "pattern_id": pattern_id,
                    "result": result.__dict__
                    if hasattr(result, "__dict__")
                    else {"output": str(result)},
                    "accelerated": False,
                    "executed": False,
                    "stub": True,
                    "note": "Non-dict bridge result — not claiming completed",
                },
                default_ok_status="unavailable",
            )

        except Exception as e:
            logger.warning(f"Bridge acceleration failed for {pattern_id}: {e}, using legacy")
            legacy_result = self._run_legacy(pattern_id, instance, hypothesis)
            legacy_result["fallback_reason"] = str(e)
            legacy_result["accelerated"] = False
            return legacy_result

    def run_batch(
        self, patterns: list[str], hypotheses: list[dict], parallel: bool = True
    ) -> list[dict]:
        """
        Run multiple patterns in parallel if possible.

        Args:
            patterns: List of pattern IDs
            hypotheses: List of hypotheses (one per pattern)
            parallel: Enable parallel execution

        Returns:
            List of results (same order as input)
        """
        if len(patterns) != len(hypotheses):
            raise ValueError("patterns and hypotheses must have same length")

        if not parallel:
            return [self.run(pid, hyp) for pid, hyp in zip(patterns, hypotheses, strict=False)]

        futures = []
        for pid, hyp in zip(patterns, hypotheses, strict=False):
            future = self._executor.submit(self.run, pid, hyp)
            futures.append(future)

        results = []
        for future in futures:
            try:
                results.append(future.result(timeout=300))
            except Exception as e:
                results.append(
                    {
                        "status": "failed",
                        "error": str(e),
                        "engine": "batch_error",
                    }
                )

        return results

    async def run_batch_async(self, patterns: list[str], hypotheses: list[dict]) -> list[dict]:
        """
        Run multiple patterns asynchronously.

        Args:
            patterns: List of pattern IDs
            hypotheses: List of hypotheses (one per pattern)

        Returns:
            List of results
        """
        if len(patterns) != len(hypotheses):
            raise ValueError("patterns and hypotheses must have same length")

        tasks = [
            asyncio.create_task(self._run_async(pid, hyp))
            for pid, hyp in zip(patterns, hypotheses, strict=False)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append(
                    {
                        "pattern_id": patterns[i],
                        "status": "failed",
                        "error": str(result),
                        "engine": "async_error",
                    }
                )
            else:
                processed.append(result)

        return processed

    async def _run_async(self, pattern_id: str, hypothesis: dict | None) -> dict:
        """Async wrapper for run method."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.run, pattern_id, hypothesis)

    def benchmark(self, pattern_id: str, hypothesis: dict | None = None, num_runs: int = 3) -> dict:
        """
        Compare legacy vs GPU-accelerated execution.

        Args:
            pattern_id: Pattern identifier
            hypothesis: Simulation parameters
            num_runs: Number of runs for averaging

        Returns:
            Benchmark results with speedup metrics
        """
        instance = self._patterns.get(pattern_id)
        if instance is None:
            return {
                "pattern_id": pattern_id,
                "error": "Pattern not found",
                "speedup": 0.0,
            }

        recommended_engine = self.engine_map.get_engine(pattern_id)

        if recommended_engine == "legacy":
            return {
                "pattern_id": pattern_id,
                "recommended_engine": "legacy",
                "speedup": 1.0,
                "note": "Pattern does not support GPU acceleration",
            }

        legacy_times = []
        for _ in range(num_runs):
            start = time.perf_counter()
            self._run_legacy(pattern_id, instance, hypothesis)
            legacy_times.append(time.perf_counter() - start)

        gpu_times = []
        gpu_result = None
        for _ in range(num_runs):
            start = time.perf_counter()
            gpu_result = self._run_with_bridge(pattern_id, instance, hypothesis, recommended_engine)
            gpu_times.append(time.perf_counter() - start)

        avg_legacy = sum(legacy_times) / len(legacy_times)
        avg_gpu = sum(gpu_times) / len(gpu_times) if gpu_times else 0

        speedup = avg_legacy / avg_gpu if avg_gpu > 0 else 1.0

        return {
            "pattern_id": pattern_id,
            "recommended_engine": recommended_engine,
            "num_runs": num_runs,
            "legacy": {
                "times": legacy_times,
                "average_seconds": round(avg_legacy, 6),
            },
            "gpu_accelerated": {
                "times": gpu_times,
                "average_seconds": round(avg_gpu, 6),
                "engine": recommended_engine,
            },
            "speedup": round(speedup, 2),
            "gpu_available": self.auto_detector.has_gpu,
            "gpu_name": self.auto_detector.gpu_name,
            "last_result": gpu_result,
        }

    def get_engine_status(self) -> dict[str, Any]:
        """Get status of all available engines."""
        status = {
            "hardware": self.auto_detector.get_detection_report(),
            "engines": {},
        }

        for engine_name in ["newton", "torchsim", "jaxsim", "schr"]:
            bridge = self._get_bridge(engine_name)
            if bridge is not None:
                status["engines"][engine_name] = {
                    "available": True,
                    "type": engine_name,
                }
                if hasattr(bridge, "is_gpu_mode"):
                    status["engines"][engine_name]["gpu_mode"] = bridge.is_gpu_mode()
                if hasattr(bridge, "get_device"):
                    status["engines"][engine_name]["device"] = bridge.get_device()
            else:
                status["engines"][engine_name] = {
                    "available": False,
                }

        status["engines"]["legacy"] = {
            "available": True,
            "type": "cpu",
        }

        return status

    def __del__(self) -> None:
        """Cleanup executor on deletion."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)


def get_runner_v2() -> PatternRunnerV2:
    """Get singleton PatternRunnerV2 instance (backed by DI container)."""
    from src.di.container import get_container

    return get_container().get_or_register("runner_v2", PatternRunnerV2)
