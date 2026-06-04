"""
C4REQBER: Saga Pattern

Orchestrates long-running business transactions across multiple services
with compensation support for rollback.
"""
from __future__ import annotations

import logging
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable

from src.compat import UTC


logger = logging.getLogger(__name__)


class SagaStatus(Enum):
    """Saga execution status."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    COMPENSATING = auto()
    COMPENSATED = auto()


@dataclass
class SagaLogEntry:
    """Log entry for saga step execution."""

    step_name: str
    action: str  # "execute" or "compensate"
    status: str  # "success" or "failure"
    timestamp: datetime
    error: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class SagaContext:
    """Mutable context passed between saga steps."""

    saga_id: str
    data: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    _log: list[SagaLogEntry] = field(default_factory=list)

    def log(self, step_name: str, action: str, status: str, error: str | None = None) -> None:
        self._log.append(
            SagaLogEntry(
                step_name=step_name,
                action=action,
                status=status,
                timestamp=datetime.now(UTC),
                error=error,
            )
        )

    @property
    def execution_log(self) -> list[SagaLogEntry]:
        return list(self._log)


class SagaStep(ABC):
    """Single step in a saga."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def execute(self, context: SagaContext) -> None:
        """Execute the step. Raise exception on failure."""
        raise NotImplementedError

    @abstractmethod
    def compensate(self, context: SagaContext) -> None:
        """Compensate (rollback) the step."""
        raise NotImplementedError


class FunctionSagaStep(SagaStep):
    """Saga step implemented with functions."""

    def __init__(
        self,
        name: str,
        execute_fn: Callable[[SagaContext], None],
        compensate_fn: Callable[[SagaContext], None] | None = None,
    ) -> None:
        super().__init__(name)
        self._execute_fn = execute_fn
        self._compensate_fn = compensate_fn

    def execute(self, context: SagaContext) -> None:
        self._execute_fn(context)

    def compensate(self, context: SagaContext) -> None:
        if self._compensate_fn:
            self._compensate_fn(context)


class Saga:
    """Saga orchestrator for long-running transactions."""

    def __init__(self, name: str, saga_id: str | None = None) -> None:
        self.name = name
        self.saga_id = saga_id or str(uuid.uuid4())
        self._steps: list[SagaStep] = []
        self._status = SagaStatus.PENDING
        self._current_step = 0
        self._lock = threading.RLock()

    def add_step(self, step: SagaStep) -> Saga:
        """Add step."""
        self._steps.append(step)
        return self

    @property
    def status(self) -> SagaStatus:
        with self._lock:
            return self._status

    def execute(self, initial_data: dict[str, Any] | None = None) -> SagaContext:
        """Execute saga steps sequentially."""
        context = SagaContext(saga_id=self.saga_id, data=initial_data or {})

        with self._lock:
            self._status = SagaStatus.RUNNING
            self._current_step = 0

        try:
            for i, step in enumerate(self._steps):
                with self._lock:
                    self._current_step = i

                logger.info("Saga %s: executing step %s", self.saga_id, step.name)
                step.execute(context)
                context.log(step.name, "execute", "success")
                logger.info("Saga %s: step %s completed", self.saga_id, step.name)

            with self._lock:
                self._status = SagaStatus.COMPLETED

        except Exception as e:
            logger.error("Saga %s failed at step %s: %s", self.saga_id, step.name, e)
            context.log(step.name, "execute", "failure", str(e))
            self._compensate(context, i)
            with self._lock:
                self._status = SagaStatus.FAILED

        return context

    def _compensate(self, context: SagaContext, failed_step_index: int) -> None:
        """Run compensation for completed steps in reverse order."""
        with self._lock:
            self._status = SagaStatus.COMPENSATING

        any_failed = False
        failed_steps: list[str] = []
        for i in range(failed_step_index - 1, -1, -1):
            step = self._steps[i]
            try:
                logger.info("Saga %s: compensating step %s", self.saga_id, step.name)
                step.compensate(context)
                context.log(step.name, "compensate", "success")
            except Exception as e:
                logger.error(
                    "Saga %s: compensation failed for step %s: %s",
                    self.saga_id,
                    step.name,
                    e,
                )
                context.log(step.name, "compensate", "failure", str(e))
                any_failed = True
                failed_steps.append(step.name)

        with self._lock:
            if any_failed:
                self._status = SagaStatus.FAILED
                context.data["compensation_errors"] = failed_steps
            else:
                self._status = SagaStatus.COMPENSATED


# ============================================================================
# C4REQBER Specific Sagas
# ============================================================================

class DiscoverySaga(Saga):
    """Saga for the complete discovery pipeline."""

    def __init__(self, saga_id: str | None = None) -> None:
        super().__init__("discovery_pipeline", saga_id)


class PatternApplicationSaga(Saga):
    """Saga for applying multiple patterns with rollback."""

    def __init__(self, saga_id: str | None = None) -> None:
        super().__init__("pattern_application", saga_id)


def create_discovery_saga(
    problem_statement: str,
    domain: str,
    llm_call_fn: Callable[[str], str],
    pattern_apply_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    validate_fn: Callable[[dict[str, Any]], bool],
) -> Saga:
    """Factory for creating a discovery pipeline saga."""
    saga = DiscoverySaga()

    # Step 1: Analyze problem
    def analyze_problem(ctx: SagaContext) -> None:
        ctx.results["analysis"] = llm_call_fn(f"Analyze: {problem_statement}")

    def compensate_analysis(ctx: SagaContext) -> None:
        ctx.results.pop("analysis", None)

    saga.add_step(FunctionSagaStep("analyze", analyze_problem, compensate_analysis))

    # Step 2: Apply patterns
    def apply_patterns(ctx: SagaContext) -> None:
        ctx.results["patterns"] = pattern_apply_fn(domain, {})

    def compensate_patterns(ctx: SagaContext) -> None:
        ctx.results.pop("patterns", None)

    saga.add_step(FunctionSagaStep("apply_patterns", apply_patterns, compensate_patterns))

    # Step 3: Validate
    def validate(ctx: SagaContext) -> None:
        if not validate_fn(ctx.results):
            raise ValueError("Validation failed")

    saga.add_step(FunctionSagaStep("validate", validate))

    return saga
