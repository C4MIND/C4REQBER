"""
C4REQBER v8.4 - Pattern Resource Estimator
Estimates and checks computational resources before running patterns.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class ResourceEstimate:
    """Estimated resource requirements for a pattern."""

    cpu_time: float
    memory_mb: float
    io_ops: float

    def __post_init__(self) -> None:
        if self.cpu_time < 0:
            self.cpu_time = 0.0
        if self.memory_mb < 0:
            self.memory_mb = 0.0
        if self.io_ops < 0:
            self.io_ops = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "cpu_time": self.cpu_time,
            "memory_mb": self.memory_mb,
            "io_ops": self.io_ops,
        }


class ResourceCheckError(Exception):
    """Raised when resource check fails."""

    def __init__(self, message: str, recommendations: list[str] | None = None) -> None:
        super().__init__(message)
        self.recommendations = recommendations or []


class PatternResourceEstimator:
    """
    Estimates computational resources for simulation patterns
    and checks availability against current system state.
    """

    # Base constants for heuristics (empirically tuned)
    BASE_CPU_PER_AGENT_STEP = 0.001
    BASE_MEMORY_PER_AGENT = 1.0
    BASE_IO_PER_AGENT_STEP = 0.01

    BASE_CPU_PER_SAMPLE = 0.0001
    BASE_MEMORY_PER_SAMPLE = 0.1
    BASE_IO_PER_SAMPLE = 0.001

    BASE_CPU_PER_STOCK_TIMESTEP = 0.0005
    BASE_MEMORY_PER_STOCK = 0.5
    BASE_IO_PER_STOCK_TIMESTEP = 0.005

    BASE_CPU_PER_VAR_CONSTRAINT = 0.0001
    BASE_MEMORY_PER_VAR = 0.2
    BASE_IO_PER_VAR_CONSTRAINT = 0.001

    # Safety margin multiplier
    SAFETY_MARGIN = 1.2

    def __init__(self) -> None:
        self._has_psutil = False
        try:
            import psutil

            self._has_psutil = True
        except ImportError:
            logger.warning("psutil not available; resource checks will use conservative estimates")

    def estimate(self, pattern_id: str, params: dict[str, Any] | None = None) -> ResourceEstimate:
        """
        Estimate resources for a pattern based on its ID and parameters.

        Args:
            pattern_id: Pattern identifier (e.g., 'agent_based', 'monte_carlo')
            params: Pattern-specific parameters dict

        Returns:
            ResourceEstimate with cpu_time (sec), memory_mb, io_ops
        """
        params = params or {}
        estimator = self._get_estimator(pattern_id)
        return estimator(params)  # type: ignore[no-any-return]

    def _get_estimator(self, pattern_id: str) -> Any:
        """Return the appropriate estimator function for a pattern."""
        estimators = {
            "agent_based": self._estimate_agent_based,
            "monte_carlo": self._estimate_monte_carlo,
            "system_dynamics": self._estimate_system_dynamics,
            "optimization_lp": self._estimate_optimization,
        }
        return estimators.get(pattern_id, self._estimate_generic)

    def _estimate_agent_based(self, params: dict[str, Any]) -> ResourceEstimate:
        """O(agents x steps) heuristic."""
        agents = params.get("n_agents", 100)
        steps = params.get("n_steps", 1000)

        cpu_time = agents * steps * self.BASE_CPU_PER_AGENT_STEP
        memory_mb = agents * self.BASE_MEMORY_PER_AGENT + 50
        io_ops = agents * steps * self.BASE_IO_PER_AGENT_STEP

        return ResourceEstimate(cpu_time=cpu_time, memory_mb=memory_mb, io_ops=io_ops)

    def _estimate_monte_carlo(self, params: dict[str, Any]) -> ResourceEstimate:
        """O(samples x dimensions) heuristic."""
        samples = params.get("n_samples", 10000)
        dimensions = params.get("dimensions", 10)

        cpu_time = samples * dimensions * self.BASE_CPU_PER_SAMPLE
        memory_mb = samples * self.BASE_MEMORY_PER_SAMPLE + 100
        io_ops = samples * dimensions * self.BASE_IO_PER_SAMPLE

        return ResourceEstimate(cpu_time=cpu_time, memory_mb=memory_mb, io_ops=io_ops)

    def _estimate_system_dynamics(self, params: dict[str, Any]) -> ResourceEstimate:
        """O(stocks x timesteps) heuristic."""
        stocks = params.get("stocks", ["population", "resources"])
        n_stocks = len(stocks) if isinstance(stocks, list) else stocks
        t_end = params.get("t_end", 100.0)
        dt = params.get("dt", 0.1)
        timesteps = int(t_end / dt)
        n_runs = params.get("n_sensitivity_runs", 50) if params.get("sensitivity_analysis", True) else 1

        cpu_time = n_stocks * timesteps * n_runs * self.BASE_CPU_PER_STOCK_TIMESTEP
        memory_mb = n_stocks * self.BASE_MEMORY_PER_STOCK + 100
        io_ops = n_stocks * timesteps * n_runs * self.BASE_IO_PER_STOCK_TIMESTEP

        return ResourceEstimate(cpu_time=cpu_time, memory_mb=memory_mb, io_ops=io_ops)

    def _estimate_optimization(self, params: dict[str, Any]) -> ResourceEstimate:
        """O(variables x constraints) heuristic."""
        variables = params.get("num_variables", 3)
        constraints = params.get("num_constraints", 5)

        product = variables * constraints
        cpu_time = product * self.BASE_CPU_PER_VAR_CONSTRAINT
        memory_mb = variables * self.BASE_MEMORY_PER_VAR + 50
        io_ops = product * self.BASE_IO_PER_VAR_CONSTRAINT

        return ResourceEstimate(cpu_time=cpu_time, memory_mb=memory_mb, io_ops=io_ops)

    def _estimate_generic(self, params: dict[str, Any]) -> ResourceEstimate:
        """Fallback generic estimator."""
        return ResourceEstimate(cpu_time=60.0, memory_mb=256.0, io_ops=1000.0)

    def get_system_resources(self) -> dict[str, Any]:
        """
        Get current available system resources.

        Returns dict with:
            - available_memory_mb: free RAM
            - available_cpu_percent: idle CPU %
            - available_disk_mb: free disk space
            - has_psutil: whether psutil is available
        """
        if not self._has_psutil:
            return self._fallback_system_resources()

        import psutil

        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage(os.getcwd())

        return {
            "available_memory_mb": mem.available / (1024 * 1024),
            "available_cpu_percent": 100.0 - cpu_percent,
            "available_disk_mb": disk.free / (1024 * 1024),
            "has_psutil": True,
        }

    def _fallback_system_resources(self) -> dict[str, Any]:
        """Conservative fallback when psutil is unavailable."""
        return {
            "available_memory_mb": 512.0,
            "available_cpu_percent": 50.0,
            "available_disk_mb": 1024.0,
            "has_psutil": False,
        }

    def check_available(self, estimate: ResourceEstimate) -> bool:
        """
        Check if estimated resources fit within available system resources.

        Returns True if resources are sufficient, False otherwise.
        """
        system = self.get_system_resources()

        available_mem = system.get("available_memory_mb", 512.0)
        available_cpu = system.get("available_cpu_percent", 50.0)

        # Memory check with safety margin
        if estimate.memory_mb * self.SAFETY_MARGIN > available_mem:
            return False

        # CPU check: assume cpu_time seconds needs at least some CPU headroom
        # Very long CPU estimates should fail if CPU is heavily loaded
        if estimate.cpu_time > 300 and available_cpu < 20:
            return False

        return True

    def check_or_raise(self, pattern_id: str, params: dict[str, Any] | None = None) -> ResourceEstimate:
        """
        Estimate resources and raise ResourceCheckError if insufficient.

        Returns the estimate on success.
        """
        estimate = self.estimate(pattern_id, params)

        if not self.check_available(estimate):
            system = self.get_system_resources()
            recommendations = self._build_recommendations(estimate, system)
            raise ResourceCheckError(
                f"Insufficient resources for pattern '{pattern_id}': "
                f"needs {estimate.memory_mb:.1f}MB memory, "
                f"{estimate.cpu_time:.1f}s CPU time; "
                f"available {system.get('available_memory_mb', 'unknown'):.1f}MB memory, "
                f"{system.get('available_cpu_percent', 'unknown'):.1f}% CPU free",
                recommendations=recommendations,
            )

        return estimate

    def _build_recommendations(self, estimate: ResourceEstimate, system: dict[str, Any]) -> list[str]:
        """Build actionable recommendations when resources are insufficient."""
        recommendations = []

        available_mem = system.get("available_memory_mb", 512.0)
        if estimate.memory_mb * self.SAFETY_MARGIN > available_mem:
            recommendations.append(
                f"Reduce memory usage: current estimate {estimate.memory_mb:.1f}MB, "
                f"available {available_mem:.1f}MB. "
                f"Try reducing problem size (agents, samples, variables)."
            )

        available_cpu = system.get("available_cpu_percent", 50.0)
        if estimate.cpu_time > 300 and available_cpu < 20:
            recommendations.append(
                f"CPU heavily loaded ({100 - available_cpu:.1f}% used). "
                f"Consider running when system is less busy or reducing computational complexity."
            )

        if not system.get("has_psutil", False):
            recommendations.append(
                "Install psutil for accurate resource monitoring: pip install psutil"
            )

        return recommendations


def get_estimator() -> PatternResourceEstimator:
    """Get singleton resource estimator (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("resource_estimator", PatternResourceEstimator)
