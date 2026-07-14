# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """GateStatus."""
    PASS = "pass"
    FAIL = "fail"
    REGRESS = "regress"  # go back to previous stage
    SKIP = "skip"


@dataclass
class VerificationGate:
    """VerificationGate."""
    name: str
    checker: Any  # callable or verification engine
    on_fail: str = "regress"  # "regress" | "abort" | "warn"
    max_retries: int = 2
    retry_count: int = 0
    last_error: str = ""


class GatedPipeline:
    """Pipeline with verification gates between stages that can regress on failure."""

    def __init__(self, stages: list[str], gates: dict[int, VerificationGate] | None = None) -> None:
        self.stages = stages
        self.gates = gates or {}
        self.current_stage = 0
        self.stage_results: dict[int, Any] = {}

    async def run_stage(self, stage_idx: int, input_data: Any) -> tuple[int, Any]:
        """Run a stage and check its verification gate. May regress."""
        if stage_idx in self.gates:
            gate = self.gates[stage_idx]
            status = await self._check_gate(gate, self.stage_results.get(stage_idx - 1), input_data)
            if status == GateStatus.REGRESS:
                if gate.retry_count < gate.max_retries:
                    gate.retry_count += 1
                    logger.warning("Gate %s failed — regressing to stage %d (retry %d/%d)", gate.name, stage_idx - 1, gate.retry_count, gate.max_retries)
                    return stage_idx - 1, None
                else:
                    logger.error("Gate %s failed after %d retries — aborting", gate.name, gate.max_retries)
                    gate.last_error = f"Max retries ({gate.max_retries}) exceeded"
                    return -1, None
            elif status == GateStatus.FAIL:
                logger.error("Gate %s failed", gate.name)
                return -1, None
        return stage_idx + 1, input_data

    async def _check_gate(self, gate: VerificationGate, prev_result: Any, current_input: Any) -> GateStatus:
        try:
            if callable(gate.checker):
                result = gate.checker(prev_result, current_input)
                return GateStatus.PASS if result else GateStatus.REGRESS
        except Exception as e:
            gate.last_error = str(e)
            return GateStatus.FAIL if gate.on_fail == "abort" else GateStatus.REGRESS
        return GateStatus.PASS
