# SPDX-License-Identifier: AGPL-3.0
"""Base simulation adapter for all P1 engine bridges.

Provides the AbstractEngineAdapter pattern from simulation_engines_report.md:
  configure(params) -> None
  run(input_data) -> SimulationResult
  get_status() -> Status
  get_results() -> dict
  cleanup() -> None

All P1 adapters must inherit from BaseSimulationAdapter and implement
is_available() + run().  If the underlying engine is not installed,
the adapter returns status="unavailable" with an install_hint.
"""
from __future__ import annotations

import abc
import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class SimStatus(str, Enum):
    """Simulation execution status."""

    READY = "ready"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class SimulationResult:
    """Structured result returned by every adapter run()."""

    status: SimStatus = SimStatus.UNAVAILABLE
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    install_hint: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "metadata": self.metadata,
            "logs": self.logs,
            "elapsed_seconds": self.elapsed_seconds,
            "install_hint": self.install_hint,
            "error_message": self.error_message,
        }


class BaseSimulationAdapter(abc.ABC):
    """Abstract base for every simulation engine adapter.

    Subclasses must set:
      _engine_name: str   — human-readable engine name
      _package_checks: list[str] — Python import names to test (e.g. ["openmm"])
    """

    _engine_name: str = ""
    _package_checks: list[str] = []
    _install_hint: str = ""

    def __init__(self) -> None:
        self._params: dict[str, Any] = {}
        self._last_result: SimulationResult | None = None
        self._start_time: float = 0.0

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        """Check whether the underlying engine can be imported."""
        for pkg in self._package_checks:
            if not self._can_import(pkg):
                return False
        return True

    @staticmethod
    def _can_import(module_name: str) -> bool:
        try:
            __import__(module_name)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def configure(self, params: dict[str, Any]) -> None:
        """Store simulation parameters; subclasses may validate here."""
        self._params = dict(params)

    @abc.abstractmethod
    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        """Execute the simulation.

        Must return a SimulationResult.  If the engine is unavailable,
        return status=UNAVAILABLE with install_hint set.
        """
        ...

    def get_status(self) -> SimStatus:
        """Return status of the most recent run."""
        if self._last_result is None:
            return SimStatus.UNAVAILABLE
        return self._last_result.status

    def get_results(self) -> dict[str, Any]:
        """Return raw data dict from the most recent run."""
        if self._last_result is None:
            return {}
        return self._last_result.data

    def cleanup(self) -> None:
        """Release resources.  Override if the engine holds file handles/GPU memory."""
        self._params.clear()
        self._last_result = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_unavailable(self, extra_hint: str = "") -> SimulationResult:
        hint = self._install_hint or extra_hint
        return SimulationResult(
            status=SimStatus.UNAVAILABLE,
            install_hint=hint,
            metadata={"engine": self._engine_name},
        )

    def _run_wrapped(
        self, fn: callable, input_data: dict[str, Any] | None
    ) -> SimulationResult:
        """Wrap a concrete run with timing, logging and exception handling."""
        if not self.is_available():
            return self._make_unavailable()

        self._start_time = time.perf_counter()
        try:
            data = fn(input_data or {})
            elapsed = time.perf_counter() - self._start_time
            result = SimulationResult(
                status=SimStatus.SUCCESS,
                data=data,
                elapsed_seconds=elapsed,
                metadata={"engine": self._engine_name},
            )
        except Exception as exc:
            elapsed = time.perf_counter() - self._start_time
            logger.error("%s run failed: %s", self._engine_name, exc, exc_info=True)
            result = SimulationResult(
                status=SimStatus.ERROR,
                elapsed_seconds=elapsed,
                error_message=str(exc),
                logs=traceback.format_exc().splitlines(),
                metadata={"engine": self._engine_name},
            )
        self._last_result = result
        return result
