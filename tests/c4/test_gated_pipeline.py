from __future__ import annotations

import pytest

from c4.gated_pipeline import GatedPipeline, GateStatus, VerificationGate


class TestGateStatus:
    def test_enum_values(self):
        assert GateStatus.PASS.value == "pass"
        assert GateStatus.FAIL.value == "fail"
        assert GateStatus.REGRESS.value == "regress"
        assert GateStatus.SKIP.value == "skip"

    def test_enum_membership(self):
        assert GateStatus("pass") == GateStatus.PASS
        assert GateStatus("fail") == GateStatus.FAIL
        assert GateStatus("regress") == GateStatus.REGRESS

    def test_four_members(self):
        assert len(GateStatus) == 4


class TestVerificationGate:
    def test_creation_with_defaults(self):
        gate = VerificationGate(name="quality_check", checker=lambda a, b: True)
        assert gate.name == "quality_check"
        assert gate.on_fail == "regress"
        assert gate.max_retries == 2
        assert gate.retry_count == 0
        assert gate.last_error == ""

    def test_creation_with_custom_options(self):
        gate = VerificationGate(
            name="strict_check",
            checker=None,
            on_fail="abort",
            max_retries=1,
        )
        assert gate.name == "strict_check"
        assert gate.on_fail == "abort"
        assert gate.max_retries == 1

    def test_defaults_can_be_mutated(self):
        gate = VerificationGate(name="g", checker=lambda a, b: True)
        gate.retry_count = 1
        gate.last_error = "something went wrong"
        assert gate.retry_count == 1
        assert gate.last_error == "something went wrong"


class TestGatedPipeline:
    def test_init_with_stages(self):
        pipeline = GatedPipeline(stages=["search", "analyze", "verify"])
        assert pipeline.stages == ["search", "analyze", "verify"]
        assert pipeline.gates == {}
        assert pipeline.current_stage == 0

    def test_init_with_gates(self):
        gate = VerificationGate(name="quality", checker=lambda a, b: True)
        pipeline = GatedPipeline(
            stages=["search", "analyze"],
            gates={1: gate},
        )
        assert 1 in pipeline.gates
        assert pipeline.gates[1] is gate

    def test_init_defaults(self):
        pipeline = GatedPipeline(stages=[])
        assert pipeline.stages == []
        assert pipeline.gates == {}
        assert pipeline.current_stage == 0
        assert pipeline.stage_results == {}

    @pytest.mark.anyio
    async def test_run_stage_no_gate_advances(self):
        pipeline = GatedPipeline(stages=["a", "b"])
        next_stage, _ = await pipeline.run_stage(0, "data")
        assert next_stage == 1

    @pytest.mark.anyio
    async def test_run_stage_with_passing_gate_advances(self):
        gate = VerificationGate(name="g", checker=lambda prev, cur: True)
        pipeline = GatedPipeline(stages=["a", "b"], gates={0: gate})
        next_stage, _ = await pipeline.run_stage(0, "data")
        assert next_stage == 1

    @pytest.mark.anyio
    async def test_run_stage_with_failing_gate_regresses(self):
        gate = VerificationGate(name="g", checker=lambda prev, cur: False)
        pipeline = GatedPipeline(stages=["a", "b"], gates={0: gate})
        next_stage, _ = await pipeline.run_stage(0, "data")
        assert next_stage == -1  # regress to stage -1
        assert gate.retry_count == 1

    @pytest.mark.anyio
    async def test_run_stage_exhausted_retries_aborts(self):
        gate = VerificationGate(name="g", checker=lambda prev, cur: False)
        pipeline = GatedPipeline(stages=["a", "b", "c"], gates={0: gate})
        await pipeline.run_stage(0, "data")
        await pipeline.run_stage(0, "data")
        next_stage, _ = await pipeline.run_stage(0, "data")
        assert next_stage == -1
        assert gate.retry_count == 2
        assert "Max retries" in gate.last_error

    @pytest.mark.anyio
    async def test_run_stage_checker_raises_returns_regress(self):
        def failing_checker(prev, cur):
            raise RuntimeError("checker crashed")

        gate = VerificationGate(name="g", checker=failing_checker, on_fail="regress")
        pipeline = GatedPipeline(stages=["a", "b"], gates={0: gate})
        next_stage, _ = await pipeline.run_stage(0, "data")
        assert next_stage == -1
        assert gate.last_error == "checker crashed"

    @pytest.mark.anyio
    async def test_run_stage_checker_raises_abort_returns_fail(self):
        def failing_checker(prev, cur):
            raise RuntimeError("fatal")

        gate = VerificationGate(name="g", checker=failing_checker, on_fail="abort")
        pipeline = GatedPipeline(stages=["a", "b"], gates={0: gate})
        next_stage, _ = await pipeline.run_stage(0, "data")
        assert next_stage == -1
        assert gate.last_error == "fatal"
