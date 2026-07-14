"""
C4REQBER: TOTE Metamodel
Test-Operate-Test-Exit micro-loop for agent self-correction.

TOTE = Test → Operate → Test → Exit

A fundamental cybernetic control loop used for:
- Agent self-correction
- Micro-level validation
- Feedback-driven iteration
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToteStatus(Enum):
    """ToteStatus."""
    INITIAL = "initial"
    TESTING_1 = "testing_1"
    OPERATING = "operating"
    TESTING_2 = "testing_2"
    EXIT = "exit"
    ERROR = "error"


@dataclass
class ToteIteration:
    """Single iteration of the TOTE loop."""

    iteration: int
    test_1_result: bool = False
    operation: str = ""
    operation_output: Any = None
    test_2_result: bool = False
    mismatch_delta: float = 0.0
    duration_ms: float = 0.0


@dataclass
class ToteResult:
    """Result of a TOTE loop execution."""

    target_state: str
    initial_state: str
    iterations: list[ToteIteration] = field(default_factory=list)
    final_state: str | None = None
    success: bool = False
    total_iterations: int = 0
    total_duration_ms: float = 0.0
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_state": self.target_state,
            "initial_state": self.initial_state,
            "success": self.success,
            "total_iterations": self.total_iterations,
            "total_duration_ms": self.total_duration_ms,
            "final_state": self.final_state,
            "iterations": [
                {
                    "iteration": it.iteration,
                    "test_1_passed": it.test_1_result,
                    "operation": it.operation,
                    "test_2_passed": it.test_2_result,
                    "mismatch_delta": it.mismatch_delta,
                    "duration_ms": it.duration_ms,
                }
                for it in self.iterations
            ],
        }


class ToteEngine:
    """
    TOTE Engine: Test-Operate-Test-Exit control loop.

    Usage:
        def test_fn(state) -> bool:
            return state == "correct"

        def operate_fn(state) -> str:
            return state + "_fixed"

        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=test_fn,
            operate_fn=operate_fn,
            max_iterations=10,
        )
    """

    def run(
        self,
        target_state: str,
        initial_state: str,
        test_fn: Callable[[str], bool],
        operate_fn: Callable[[str], str],
        max_iterations: int = 10,
        mismatch_fn: Callable[[str, str], float] | None = None,
    ) -> ToteResult:
        """
        Execute TOTE loop.

        Args:
            target_state: Description of desired state
            initial_state: Starting state
            test_fn: Function that returns True if state matches target
            operate_fn: Function that transforms state toward target
            max_iterations: Safety limit
            mismatch_fn: Optional function measuring how far state is from target
        """
        start_time = time.time()
        result = ToteResult(
            target_state=target_state,
            initial_state=initial_state,
        )
        current_state = initial_state

        for i in range(max_iterations):
            iter_start = time.time()
            iteration = ToteIteration(iteration=i + 1)

            # Test 1: Is current state acceptable?
            try:
                iteration.test_1_result = test_fn(current_state)
            except Exception as e:
                result.error_message = f"Test 1 error: {str(e)}"
                result.status = ToteStatus.ERROR  # type: ignore[attr-defined]
                return result

            if iteration.test_1_result:
                # Exit: state is already acceptable
                result.final_state = current_state
                result.success = True
                result.total_iterations = i
                result.total_duration_ms = (time.time() - start_time) * 1000
                iteration.duration_ms = (time.time() - iter_start) * 1000
                result.iterations.append(iteration)
                return result

            # Operate: transform state
            try:
                operation_start = current_state
                current_state = operate_fn(current_state)
                iteration.operation = f"{operation_start} → {current_state}"
                iteration.operation_output = current_state
            except Exception as e:
                result.error_message = f"Operate error: {str(e)}"
                result.status = ToteStatus.ERROR  # type: ignore[attr-defined]
                return result

            # Test 2: Is new state closer to target?
            try:
                iteration.test_2_result = test_fn(current_state)
                if mismatch_fn:
                    iteration.mismatch_delta = mismatch_fn(current_state, target_state)
            except Exception as e:
                result.error_message = f"Test 2 error: {str(e)}"
                result.status = ToteStatus.ERROR  # type: ignore[attr-defined]
                return result

            iteration.duration_ms = (time.time() - iter_start) * 1000
            result.iterations.append(iteration)

            if iteration.test_2_result:
                # Exit: operation succeeded
                result.final_state = current_state
                result.success = True
                result.total_iterations = i + 1
                result.total_duration_ms = (time.time() - start_time) * 1000
                return result

        # Max iterations reached
        result.final_state = current_state
        result.total_iterations = max_iterations
        result.total_duration_ms = (time.time() - start_time) * 1000
        return result

    def run_numeric(
        self,
        target_value: float,
        initial_value: float,
        operate_fn: Callable[[float], float],
        tolerance: float = 0.01,
        max_iterations: int = 100,
    ) -> ToteResult:
        """
        Simplified TOTE for numeric values with automatic test.
        """

        def test_fn(v: float) -> bool:
            return abs(v - target_value) <= tolerance

        def mismatch_fn(v: float, t: float) -> float:
            return abs(v - t)

        return self.run(
            target_state=str(target_value),
            initial_state=str(initial_value),
            test_fn=lambda s: test_fn(float(s)),
            operate_fn=lambda s: str(operate_fn(float(s))),
            max_iterations=max_iterations,
            mismatch_fn=lambda s, t: mismatch_fn(float(s), float(t)),
        )
