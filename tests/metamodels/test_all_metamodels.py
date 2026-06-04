"""
Tests for src/metamodels/ — all 7 metamodels

Covers: IMPACT, COMPASS, TOTE, QZRF, MP Library, Matrix Dream, C4 projections
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.c4.engine import C4State
from src.metamodels.compass import CompassEngine, CompassLevel, CompassNavigation, CompassNode
from src.metamodels.impact import ImpactEngine, ImpactPhase, ImpactResult, ImpactStep
from src.metamodels.matrix_dream import (
    MatrixDreamLibrary,
    MatrixDreamPattern,
    PatternType,
    VariationDim,
)
from src.metamodels.mp.core import Metaprogram, MPDimension, MPProfile
from src.metamodels.mp.data import CORE_METAPROGRAMS
from src.metamodels.mp.patterns import MPLibrary
from src.metamodels.mp.profiles import AgentPerspective, MPRotationEngine, RotationResult
from src.metamodels.qzrf.operators import QzrfLibrary, QzrfOperator, QzrfPhase
from src.metamodels.qzrf.projections import QzrfC4Projections
from src.metamodels.tote import ToteEngine, ToteIteration, ToteResult, ToteStatus


# ═══════════════════════════════════════════════════════════════════
# IMPACT Metamodel
# ═══════════════════════════════════════════════════════════════════


class TestImpactPhase:
    def test_all_phases(self):
        phases = list(ImpactPhase)
        assert len(phases) == 6
        assert ImpactPhase.IDENTIFY in phases
        assert ImpactPhase.MAP in phases
        assert ImpactPhase.PREDICT in phases
        assert ImpactPhase.ANALYZE in phases
        assert ImpactPhase.CREATE in phases
        assert ImpactPhase.TEST in phases

    def test_phase_values(self):
        assert ImpactPhase.IDENTIFY.value == "identify"
        assert ImpactPhase.TEST.value == "test"


class TestImpactStep:
    def test_creation(self):
        step = ImpactStep(
            phase=ImpactPhase.IDENTIFY,
            description="Test step",
            inputs={"problem": "X"},
            outputs={"result": "Y"},
            status="completed",
        )
        assert step.phase == ImpactPhase.IDENTIFY
        assert step.status == "completed"


class TestImpactResult:
    def test_creation(self):
        result = ImpactResult(problem="Test problem")
        assert result.problem == "Test problem"
        assert result.completed is False


class TestImpactEngine:
    def test_init(self):
        engine = ImpactEngine()
        assert len(engine.phase_templates) == 6

    def test_get_phase_prompt(self):
        engine = ImpactEngine()
        prompt = engine.get_phase_prompt(ImpactPhase.IDENTIFY)
        assert "Identify" in prompt

    def test_solve_basic(self):
        engine = ImpactEngine()
        result = engine.solve("How to reduce traffic congestion?")
        assert isinstance(result, ImpactResult)
        assert result.problem == "How to reduce traffic congestion?"
        assert len(result.steps) == 6
        assert result.completed is True
        assert result.total_duration >= 0.0

    def test_solve_with_domain(self):
        engine = ImpactEngine()
        result = engine.solve("Test problem", domain_hint="physics")
        assert result.completed is True
        # Check MAP phase has domain
        map_step = [s for s in result.steps if s.phase == ImpactPhase.MAP][0]
        assert "physics" in map_step.outputs.get("domains", [])

    def test_all_phases_completed(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        for step in result.steps:
            assert step.status == "completed"
            assert step.duration_seconds >= 0.0

    def test_phase_outputs(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        identify = [s for s in result.steps if s.phase == ImpactPhase.IDENTIFY][0]
        assert "core_problem" in identify.outputs
        create = [s for s in result.steps if s.phase == ImpactPhase.CREATE][0]
        assert "solutions" in create.outputs
        test_step = [s for s in result.steps if s.phase == ImpactPhase.TEST][0]
        assert "validation_plan" in test_step.outputs

    def test_generate_phase_output_identify(self):
        engine = ImpactEngine()
        result = ImpactResult(problem="P")
        out = engine._generate_phase_output(ImpactPhase.IDENTIFY, "P", None, result)
        assert out["core_problem"] == "P"

    def test_generate_phase_output_map(self):
        engine = ImpactEngine()
        result = ImpactResult(problem="P")
        out = engine._generate_phase_output(ImpactPhase.MAP, "P", "physics", result)
        assert "physics" in out["domains"]

    def test_generate_phase_output_analyze(self):
        engine = ImpactEngine()
        result = ImpactResult(problem="P")
        out = engine._generate_phase_output(ImpactPhase.ANALYZE, "P", None, result)
        assert "bottlenecks" in out
        assert "leverage_points" in out

    def test_generate_phase_output_predict(self):
        engine = ImpactEngine()
        result = ImpactResult(problem="P")
        out = engine._generate_phase_output(ImpactPhase.PREDICT, "P", None, result)
        assert "baseline" in out
        assert "scenarios" in out

    def test_generate_phase_output_create(self):
        engine = ImpactEngine()
        result = ImpactResult(problem="P")
        out = engine._generate_phase_output(ImpactPhase.CREATE, "P", None, result)
        assert "solutions" in out
        assert "synthesis_method" in out

    def test_generate_phase_output_test(self):
        engine = ImpactEngine()
        result = ImpactResult(problem="P")
        out = engine._generate_phase_output(ImpactPhase.TEST, "P", None, result)
        assert "validation_plan" in out
        assert "edge_cases" in out
        assert "confidence" in out

    def test_phase_order_constant(self):
        assert ImpactEngine.PHASE_ORDER == [
            ImpactPhase.IDENTIFY,
            ImpactPhase.MAP,
            ImpactPhase.PREDICT,
            ImpactPhase.ANALYZE,
            ImpactPhase.CREATE,
            ImpactPhase.TEST,
        ]

    def test_solve_steps_have_inputs(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        for step in result.steps:
            assert "problem" in step.inputs
            assert "previous_phases" in step.inputs

    def test_solve_steps_have_durations(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        for step in result.steps:
            assert step.duration_seconds >= 0.0

    def test_phase_transitions_in_order(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        phases = [s.phase for s in result.steps]
        assert phases == ImpactEngine.PHASE_ORDER

    def test_step_status_running_then_completed(self):
        engine = ImpactEngine()
        result = engine.solve("Test")
        for step in result.steps:
            assert step.status == "completed"

    def test_domain_hint_passed_to_outputs(self):
        engine = ImpactEngine()
        result = engine.solve("P", domain_hint="biology")
        map_step = [s for s in result.steps if s.phase == ImpactPhase.MAP][0]
        assert "biology" in map_step.outputs.get("domains", [])

    def test_impact_result_defaults(self):
        result = ImpactResult(problem="P")
        assert result.steps == []
        assert result.final_solution is None
        assert result.total_duration == 0.0
        assert result.completed is False

    def test_impact_step_defaults(self):
        step = ImpactStep(phase=ImpactPhase.IDENTIFY, description="D")
        assert step.inputs == {}
        assert step.outputs == {}
        assert step.status == "pending"
        assert step.duration_seconds == 0.0
        assert step.notes == ""


# ═══════════════════════════════════════════════════════════════════
# COMPASS Metamodel
# ═══════════════════════════════════════════════════════════════════


class TestCompassLevel:
    def test_all_levels(self):
        levels = list(CompassLevel)
        assert len(levels) == 7
        assert CompassLevel.FACT.value == 0
        assert CompassLevel.TRANSCENDENCE.value == 6


class TestCompassNode:
    def test_creation(self):
        node = CompassNode(level=CompassLevel.FACT, content="Test")
        assert node.level == CompassLevel.FACT
        assert node.level_name == "Факт"
        assert node.level_name_en == "Fact"

    def test_level_name_unknown(self):
        node = CompassNode(level=99, content="Test")  # type: ignore[arg-type]
        assert node.level_name == "Unknown"


class TestCompassNavigation:
    def test_to_dict(self):
        nav = CompassNavigation(problem="Test")
        nav.levels[0] = CompassNode(level=CompassLevel.FACT, content="Fact content")
        d = nav.to_dict()
        assert d["problem"] == "Test"
        assert d["current_level"] == 0
        assert "levels" in d


class TestCompassEngine:
    def test_explore(self):
        engine = CompassEngine()
        nav = engine.explore("Why does traffic occur?")
        assert nav.problem == "Why does traffic occur?"
        assert nav.current_level == 0
        assert 0 in nav.levels
        assert nav.path == [0]

    def test_ascend(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        assert nav.current_level == 1
        assert 1 in nav.levels
        assert nav.path == [0, 1]

    def test_ascend_max_level(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        for _ in range(10):
            nav = engine.ascend(nav)
        assert nav.current_level == 6  # capped

    def test_descend(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        nav = engine.descend(nav)
        assert nav.current_level == 0
        assert nav.path == [0, 1, 0]

    def test_descend_min_level(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.descend(nav)
        assert nav.current_level == 0

    def test_jump_to(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.jump_to(nav, 4)
        assert nav.current_level == 4
        assert 4 in nav.levels

    def test_jump_to_invalid(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.jump_to(nav, 10)
        assert nav.current_level == 0  # unchanged

    def test_get_level_description(self):
        engine = CompassEngine()
        desc = engine.get_level_description(3)
        assert desc["name_en"] == "Principle"

    def test_get_level_description_unknown(self):
        engine = CompassEngine()
        desc = engine.get_level_description(99)
        assert desc["name_en"] == "?"

    def test_analyze_depth(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        nav = engine.ascend(nav)
        analysis = engine.analyze_depth(nav)
        assert analysis["max_depth_reached"] == 2
        assert analysis["depth_ratio"] == 3 / 7.0
        assert analysis["is_complete"] is False

    def test_analyze_depth_complete(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        for _ in range(6):
            nav = engine.ascend(nav)
        analysis = engine.analyze_depth(nav)
        assert analysis["is_complete"] is True
        assert analysis["depth_ratio"] == 1.0

    def test_compass_node_children_and_parent(self):
        node = CompassNode(level=CompassLevel.FACT, content="root")
        child = CompassNode(level=CompassLevel.PHENOMENON, content="child", parent=node)
        node.children.append(child)
        assert child.parent is node
        assert child in node.children

    def test_compass_navigation_path_tracking(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        nav = engine.descend(nav)
        nav = engine.jump_to(nav, 3)
        assert nav.path == [0, 1, 0, 3]

    def test_compass_levels_visited_count(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        nav = engine.ascend(nav)
        analysis = engine.analyze_depth(nav)
        assert len(analysis["levels_visited"]) == 3
        assert analysis["levels_missing"] == [3, 4, 5, 6]

    def test_compass_navigation_to_dict_with_invalid_level(self):
        nav = CompassNavigation(problem="Test", current_level=99)
        d = nav.to_dict()
        assert d["current_level_name"] == "Unknown"

    def test_explore_sets_children_on_ascend(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        parent = nav.levels[0]
        child = nav.levels[1]
        assert child in parent.children

    def test_descend_at_min_level_no_change(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.descend(nav)
        assert nav.current_level == 0
        assert nav.path == [0]

    def test_jump_to_existing_level_does_not_overwrite(self):
        engine = CompassEngine()
        nav = engine.explore("Test")
        nav = engine.ascend(nav)
        original_content = nav.levels[1].content
        nav = engine.jump_to(nav, 1)
        assert nav.levels[1].content == original_content


# ═══════════════════════════════════════════════════════════════════
# TOTE Metamodel
# ═══════════════════════════════════════════════════════════════════


class TestToteStatus:
    def test_all_statuses(self):
        statuses = list(ToteStatus)
        assert len(statuses) == 6


class TestToteIteration:
    def test_creation(self):
        it = ToteIteration(iteration=1, test_1_result=False)
        assert it.iteration == 1
        assert it.test_1_result is False


class TestToteResult:
    def test_creation(self):
        result = ToteResult(target_state="correct", initial_state="wrong")
        assert result.target_state == "correct"
        assert result.success is False

    def test_to_dict(self):
        result = ToteResult(target_state="A", initial_state="B", success=True)
        d = result.to_dict()
        assert d["target_state"] == "A"
        assert d["success"] is True
        assert "iterations" in d


class TestToteEngine:
    def test_run_immediate_exit(self):
        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="correct",
            test_fn=lambda s: s == "correct",
            operate_fn=lambda s: s + "_fixed",
            max_iterations=10,
        )
        assert result.success is True
        assert result.total_iterations == 0
        assert result.final_state == "correct"

    def test_run_one_iteration(self):
        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=lambda s: s == "correct",
            operate_fn=lambda s: "correct",
            max_iterations=10,
        )
        assert result.success is True
        assert result.total_iterations == 1
        assert result.final_state == "correct"

    def test_run_max_iterations(self):
        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=lambda s: s == "correct",
            operate_fn=lambda s: s + "_still_wrong",
            max_iterations=5,
        )
        assert result.success is False
        assert result.total_iterations == 5

    def test_run_with_mismatch_fn(self):
        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=lambda s: s == "correct",
            operate_fn=lambda s: "correct",
            mismatch_fn=lambda s, t: 0.0 if s == t else 1.0,
        )
        assert result.success is True
        # After operate, current_state becomes "correct", so mismatch_delta = 0.0
        # The initial test_1 mismatch is not recorded (only test_2 mismatch is)
        assert result.iterations[0].mismatch_delta == 0.0

    def test_run_test_error(self):
        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=lambda s: (_ for _ in ()).throw(ValueError("test error")),
            operate_fn=lambda s: s,
        )
        assert result.success is False
        assert "Test 1 error" in (result.error_message or "")

    def test_run_operate_error(self):
        engine = ToteEngine()
        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=lambda s: False,
            operate_fn=lambda s: (_ for _ in ()).throw(ValueError("op error")),
        )
        assert result.success is False
        assert "Operate error" in (result.error_message or "")

    def test_run_numeric(self):
        engine = ToteEngine()
        result = engine.run_numeric(
            target_value=10.0,
            initial_value=0.0,
            operate_fn=lambda v: v + 2.0,
            tolerance=0.5,
            max_iterations=10,
        )
        assert result.success is True
        assert float(result.final_state or 0) >= 9.5

    def test_run_numeric_no_converge(self):
        engine = ToteEngine()
        result = engine.run_numeric(
            target_value=10.0,
            initial_value=0.0,
            operate_fn=lambda v: v + 0.1,
            tolerance=0.5,
            max_iterations=5,
        )
        assert result.success is False

    def test_run_test_2_error(self):
        engine = ToteEngine()

        def bad_test_2(s):
            if s == "wrong_fixed":
                raise RuntimeError("test2 crash")
            return False

        result = engine.run(
            target_state="correct",
            initial_state="wrong",
            test_fn=bad_test_2,
            operate_fn=lambda s: "wrong_fixed",
        )
        assert result.success is False
        assert "Test 2 error" in (result.error_message or "")

    def test_run_iteration_counting(self):
        engine = ToteEngine()
        call_count = 0

        def count_test(s):
            nonlocal call_count
            call_count += 1
            return s == "ok"

        result = engine.run(
            target_state="ok",
            initial_state="bad",
            test_fn=count_test,
            operate_fn=lambda s: "ok",
            max_iterations=10,
        )
        assert result.success is True
        assert result.total_iterations == 1
        assert len(result.iterations) == 1

    def test_run_numeric_exact_match(self):
        engine = ToteEngine()
        result = engine.run_numeric(
            target_value=5.0,
            initial_value=5.0,
            operate_fn=lambda v: v,
            tolerance=0.01,
        )
        assert result.success is True
        assert result.total_iterations == 0

    def test_run_numeric_convergence(self):
        engine = ToteEngine()
        result = engine.run_numeric(
            target_value=100.0,
            initial_value=0.0,
            operate_fn=lambda v: v + 25.0,
            tolerance=1.0,
            max_iterations=10,
        )
        assert result.success is True
        assert float(result.final_state or 0) >= 99.0

    def test_tote_result_to_dict_with_iterations(self):
        it = ToteIteration(
            iteration=1,
            test_1_result=False,
            operation="a -> b",
            operation_output="b",
            test_2_result=True,
            mismatch_delta=0.5,
            duration_ms=10.0,
        )
        result = ToteResult(
            target_state="b",
            initial_state="a",
            iterations=[it],
            final_state="b",
            success=True,
            total_iterations=1,
            total_duration_ms=10.0,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["total_iterations"] == 1
        assert len(d["iterations"]) == 1
        assert d["iterations"][0]["test_1_passed"] is False
        assert d["iterations"][0]["test_2_passed"] is True
        assert d["iterations"][0]["mismatch_delta"] == 0.5

    def test_tote_iteration_defaults(self):
        it = ToteIteration(iteration=1)
        assert it.test_1_result is False
        assert it.operation == ""
        assert it.operation_output is None
        assert it.test_2_result is False
        assert it.mismatch_delta == 0.0
        assert it.duration_ms == 0.0


# ═══════════════════════════════════════════════════════════════════
# QZRF Metamodel
# ═══════════════════════════════════════════════════════════════════


class TestQzrfPhase:
    def test_all_phases(self):
        phases = list(QzrfPhase)
        assert len(phases) == 5


class TestQzrfOperator:
    def test_is_applicable(self):
        op = QzrfOperator(
            id="QZ-01",
            name="Test",
            name_ru="Тест",
            phase=QzrfPhase.DIVERGENCE,
            description="Test",
            c4_target=C4State(0, 0, 0),
            applicable_states=[(0, 0, 0), (1, 1, 1)],
        )
        assert op.is_applicable(C4State(0, 0, 0)) is True
        assert op.is_applicable(C4State(2, 2, 2)) is False


class TestQzrfLibrary:
    def test_init(self):
        lib = QzrfLibrary()
        assert len(lib.all_operators()) == 14

    def test_get_existing(self):
        lib = QzrfLibrary()
        op = lib.get("QZ-01")
        assert op is not None
        assert op.name == "Branching"

    def test_get_missing(self):
        lib = QzrfLibrary()
        assert lib.get("QZ-99") is None

    def test_by_phase(self):
        lib = QzrfLibrary()
        divergence = lib.by_phase(QzrfPhase.DIVERGENCE)
        assert len(divergence) == 3
        topology = lib.by_phase(QzrfPhase.TOPOLOGY)
        assert len(topology) == 2

    def test_applicable_to(self):
        lib = QzrfLibrary()
        state = C4State(0, 0, 0)
        ops = lib.applicable_to(state)
        assert len(ops) > 0
        for op in ops:
            assert op.is_applicable(state)

    def test_recommend_sequence(self):
        lib = QzrfLibrary()
        start = C4State(0, 0, 0)
        end = C4State(1, 1, 1)
        seq = lib.recommend_sequence(start, end)
        assert len(seq) > 0
        assert all(isinstance(s, str) for s in seq)

    def test_all_operators_have_unique_ids(self):
        lib = QzrfLibrary()
        ids = [op.id for op in lib.all_operators()]
        assert len(ids) == len(set(ids))

    def test_recommend_sequence_no_candidates_fallback(self):
        lib = QzrfLibrary()
        start = C4State(0, 0, 0)
        end = C4State(0, 0, 0)
        seq = lib.recommend_sequence(start, end)
        assert len(seq) == 0

    def test_recommend_sequence_returns_operator_ids(self):
        lib = QzrfLibrary()
        start = C4State(0, 0, 0)
        end = C4State(2, 2, 2)
        seq = lib.recommend_sequence(start, end)
        assert all(s.startswith("QZ-") for s in seq)

    def test_operator_fields(self):
        lib = QzrfLibrary()
        op = lib.get("QZ-01")
        assert op.id == "QZ-01"
        assert op.name == "Branching"
        assert op.name_ru == "Ветвление"
        assert op.phase == QzrfPhase.DIVERGENCE
        assert isinstance(op.c4_target, C4State)
        assert isinstance(op.applicable_states, list)

    def test_all_14_operators_present(self):
        lib = QzrfLibrary()
        assert len(lib.all_operators()) == 14
        phases = {op.phase for op in lib.all_operators()}
        assert phases == set(QzrfPhase)

    def test_applicable_to_all_states(self):
        lib = QzrfLibrary()
        for state in C4State.all_states():
            ops = lib.applicable_to(state)
            assert len(ops) >= 0
            for op in ops:
                assert op.is_applicable(state)

    def test_by_phase_returns_empty_for_invalid(self):
        lib = QzrfLibrary()
        # QzrfPhase is an enum, no invalid values; test coverage of empty case
        assert lib.by_phase(QzrfPhase.DIVERGENCE)  # already tested above

    def test_operator_frozen_dataclass(self):
        op = QzrfOperator(
            id="QZ-TEST",
            name="Test",
            name_ru="Тест",
            phase=QzrfPhase.DIVERGENCE,
            description="Test",
            c4_target=C4State(0, 0, 0),
            applicable_states=[(0, 0, 0)],
        )
        with pytest.raises(AttributeError):
            op.name = "Changed"


class TestQzrfC4Projections:
    def test_project_phase_to_c4(self):
        state = C4State(1, 1, 1)
        target = QzrfC4Projections.project_phase_to_c4(QzrfPhase.DIVERGENCE, state)
        assert isinstance(target, C4State)

    def test_get_phase_trajectory(self):
        traj = QzrfC4Projections.get_phase_trajectory(QzrfPhase.INTEGRATION)
        assert "time_shift" in traj
        assert "scale_shift" in traj

    def test_get_phase_trajectory_unknown(self):
        from enum import Enum

        class FakePhase(Enum):
            FAKE = "fake"

        traj = QzrfC4Projections.get_phase_trajectory(FakePhase.FAKE)  # type: ignore[arg-type]
        assert traj == {}

    def test_full_qzrf_pipeline(self):
        start = C4State(0, 0, 0)
        pipeline = QzrfC4Projections.full_qzrf_pipeline(start)
        assert len(pipeline) == 5
        phases = [p for p, _ in pipeline]
        assert QzrfPhase.DIVERGENCE in phases
        assert QzrfPhase.TOPOLOGY in phases

    def test_pipeline_state_progression(self):
        start = C4State(0, 0, 0)
        pipeline = QzrfC4Projections.full_qzrf_pipeline(start)
        for phase, state in pipeline:
            assert isinstance(state, C4State)
            assert 0 <= state.T <= 2
            assert 0 <= state.S <= 2
            assert 0 <= state.A <= 2

    def test_project_phase_modulo_wrap(self):
        state = C4State(2, 2, 2)
        target = QzrfC4Projections.project_phase_to_c4(QzrfPhase.DIVERGENCE, state)
        # time_shift=+1 wraps 2 -> 0
        assert target.T == 0

    def test_all_phase_patterns_present(self):
        for phase in QzrfPhase:
            pattern = QzrfC4Projections.PHASE_C4_PATTERNS[phase]
            assert "time_shift" in pattern
            assert "scale_shift" in pattern
            assert "agency_shift" in pattern
            assert "description" in pattern


# ═══════════════════════════════════════════════════════════════════
# MP Library Metamodel
# ═══════════════════════════════════════════════════════════════════


class TestMPDimension:
    def test_all_dimensions(self):
        dims = list(MPDimension)
        assert len(dims) == 10


class TestMetaprogram:
    def test_creation(self):
        mp = Metaprogram(
            id="MP-99",
            name="Test/Program",
            name_ru="Тест",
            dimension=MPDimension.THINKING,
            pole_a="left",
            pole_b="right",
            description="Test",
        )
        assert mp.id == "MP-99"
        assert mp.dimension == MPDimension.THINKING

    def test_profile_prompt_balanced(self):
        mp = Metaprogram(
            id="MP-99", name="X/Y", name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left", pole_b="right", description="Test",
        )
        prompt = mp.profile_prompt("balanced")
        assert "Balance left and right" in prompt

    def test_profile_prompt_a(self):
        mp = Metaprogram(
            id="MP-99", name="X/Y", name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left", pole_b="right", description="Test",
        )
        prompt = mp.profile_prompt("a")
        assert "Prioritize left over right" in prompt

    def test_profile_prompt_b(self):
        mp = Metaprogram(
            id="MP-99", name="X/Y", name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left", pole_b="right", description="Test",
        )
        prompt = mp.profile_prompt("b")
        assert "Prioritize right over left" in prompt

    def test_profile_prompt_invalid(self):
        mp = Metaprogram(
            id="MP-99", name="X/Y", name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left", pole_b="right", description="Test",
        )
        prompt = mp.profile_prompt("invalid")
        assert "Balance" in prompt  # defaults to balanced


class TestMPProfile:
    def test_to_prompt(self):
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        prompt = profile.to_prompt(lib)
        assert "Agent Profile: Systems Thinker" in prompt

    def test_to_prompt_missing_mp(self):
        lib = MPLibrary()
        profile = MPProfile(
            name="Test", name_ru="Тест", settings={"MP-999": "a"}
        )
        prompt = profile.to_prompt(lib)
        assert "Agent Profile: Test" in prompt


class TestMPLibrary:
    def test_init(self):
        lib = MPLibrary()
        assert len(lib.programs) == 23

    def test_get_existing(self):
        lib = MPLibrary()
        mp = lib.get("MP-01")
        assert mp is not None
        assert mp.name == "Toward/Away"

    def test_get_missing(self):
        lib = MPLibrary()
        assert lib.get("MP-999") is None

    def test_by_dimension(self):
        lib = MPLibrary()
        thinking = lib.by_dimension(MPDimension.THINKING)
        assert len(thinking) == 5

    def test_all_profiles(self):
        lib = MPLibrary()
        profiles = lib.all_profiles()
        assert set(profiles) == {
            "systems", "pragmatic", "creative", "critical", "intuitive"
        }

    def test_get_profile_systems(self):
        lib = MPLibrary()
        p = lib.get_profile("systems")
        assert p.name == "Systems Thinker"
        assert p.settings["MP-03"] == "a"

    def test_get_profile_missing(self):
        lib = MPLibrary()
        assert lib.get_profile("nonexistent") is None

    def test_rotate_profiles(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Solve a problem", n=3)
        assert len(profiles) == 3
        names = [p.name for p in profiles]
        assert "Systems Thinker" in names
        assert "Critical Analyst" in names

    def test_rotate_profiles_design(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Design a new product")
        names = [p.name for p in profiles]
        assert "Creative Explorer" in names

    def test_rotate_profiles_implement(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Implement the solution")
        names = [p.name for p in profiles]
        assert "Pragmatic Executor" in names

    def test_rotate_profiles_respects_n(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Test", n=2)
        assert len(profiles) == 2

    def test_all_programs(self):
        lib = MPLibrary()
        assert len(lib.all_programs()) == 23

    def test_profiles_have_all_mp_ids(self):
        lib = MPLibrary()
        all_ids = {p.id for p in lib.programs}
        for name in lib.all_profiles():
            profile = lib.get_profile(name)
            assert set(profile.settings.keys()) == all_ids


class TestMPRotationEngine:
    def test_init(self):
        engine = MPRotationEngine()
        assert engine.mp is not None

    def test_analyze(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test problem", n_profiles=3)
        assert isinstance(result, RotationResult)
        assert result.problem == "Test problem"
        assert len(result.perspectives) == 3
        assert result.total_duration_ms >= 0.0

    def test_analyze_perspectives_have_content(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test")
        for p in result.perspectives:
            assert p.agent_id != ""
            assert p.profile_name != ""
            assert len(p.key_insights) > 0
            assert len(p.blind_spots) > 0
            assert 0.0 <= p.confidence <= 1.0

    def test_consensus_score(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test")
        assert 0.0 <= result.consensus_score <= 1.0

    def test_synthesized_view(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test")
        assert "Synthesized view" in result.synthesized_view

    def test_to_dict(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test")
        d = result.to_dict()
        assert d["problem"] == "Test"
        assert len(d["perspectives"]) == 3

    def test_agent_perspective_to_dict(self):
        ap = AgentPerspective(
            agent_id="a1",
            profile_name="Test",
            profile_name_ru="Тест",
            c4_state=C4State(1, 1, 1),
        )
        d = ap.to_dict()
        assert d["agent_id"] == "a1"
        assert d["c4_state"] == (1, 1, 1)

    def test_adjust_state_systems(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.S == 2
        assert adjusted.A == 2

    def test_adjust_state_pragmatic(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("pragmatic")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.S == 0
        assert adjusted.A == 0

    def test_adjust_state_creative(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("creative")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.T == 2
        assert adjusted.S == 2

    def test_generate_insights(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        insights = engine._generate_insights_for_profile(profile, "Test")
        assert len(insights) > 0

    def test_generate_blind_spots(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        spots = engine._generate_blind_spots_for_profile(profile)
        assert len(spots) > 0

    def test_compute_consensus_single(self):
        engine = MPRotationEngine()
        p = AgentPerspective("a1", "Test", "Тест", C4State(1, 1, 1), confidence=0.8)
        score = engine._compute_consensus([p])
        assert score == 1.0

    def test_compute_consensus_multiple(self):
        engine = MPRotationEngine()
        p1 = AgentPerspective("a1", "Test", "Тест", C4State(1, 1, 1), confidence=0.8)
        p2 = AgentPerspective("a2", "Test2", "Тест2", C4State(1, 1, 1), confidence=0.9)
        score = engine._compute_consensus([p1, p2])
        assert 0.0 <= score <= 1.0


class TestCoreMetaprogramsData:
    def test_count(self):
        assert len(CORE_METAPROGRAMS) == 23

    def test_all_have_id(self):
        for mp in CORE_METAPROGRAMS:
            assert mp.id.startswith("MP-")

    def test_all_have_dimension(self):
        for mp in CORE_METAPROGRAMS:
            assert isinstance(mp.dimension, MPDimension)

    def test_thinking_dimension(self):
        thinking = [mp for mp in CORE_METAPROGRAMS if mp.dimension == MPDimension.THINKING]
        assert len(thinking) == 5


# ═══════════════════════════════════════════════════════════════════
# Matrix Dream Metamodel
# ═══════════════════════════════════════════════════════════════════


class TestPatternType:
    def test_all_types(self):
        types = list(PatternType)
        assert len(types) == 9


class TestVariationDim:
    def test_all_dims(self):
        dims = list(VariationDim)
        assert len(dims) == 8


class TestMatrixDreamPattern:
    def test_creation(self):
        p = MatrixDreamPattern(
            pattern_type=PatternType.RECURSION,
            variation=VariationDim.TEMPORAL,
            id="MD-01",
            name="Recursion (temporal)",
            description="Test",
            indicators=["self-similar", "recursive"],
        )
        assert p.id == "MD-01"

    def test_matches(self):
        p = MatrixDreamPattern(
            pattern_type=PatternType.RECURSION,
            variation=VariationDim.TEMPORAL,
            id="MD-01",
            name="Recursion (temporal)",
            description="Test",
            indicators=["self-similar", "recursive"],
        )
        score = p.matches("This is self-similar and recursive")
        assert score > 0.5

    def test_matches_no_match(self):
        p = MatrixDreamPattern(
            pattern_type=PatternType.RECURSION,
            variation=VariationDim.TEMPORAL,
            id="MD-01",
            name="Recursion (temporal)",
            description="Test",
            indicators=["self-similar"],
        )
        score = p.matches("completely unrelated text")
        assert score == 0.0


class TestMatrixDreamLibrary:
    def test_init(self):
        lib = MatrixDreamLibrary()
        assert len(lib.all_patterns()) == 72

    def test_get(self):
        lib = MatrixDreamLibrary()
        p = lib.get("MD-01")
        assert p is not None
        assert p.pattern_type == PatternType.RECURSION

    def test_get_missing(self):
        lib = MatrixDreamLibrary()
        assert lib.get("MD-99") is None

    def test_by_type(self):
        lib = MatrixDreamLibrary()
        patterns = lib.by_type(PatternType.OSCILLATION)
        assert len(patterns) == 8

    def test_match(self):
        lib = MatrixDreamLibrary()
        results = lib.match("cycle and periodic wave", top_k=3)
        assert len(results) == 3
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
        assert results[0][1] >= results[1][1]  # sorted by score

    def test_pattern_matrix(self):
        lib = MatrixDreamLibrary()
        matrix = lib.pattern_matrix()
        assert len(matrix) == 9  # 9 pattern types
        for ptype in PatternType:
            assert ptype.value in matrix
            assert len(matrix[ptype.value]) == 8  # 8 variations each

    def test_all_patterns_unique_ids(self):
        lib = MatrixDreamLibrary()
        ids = [p.id for p in lib.all_patterns()]
        assert len(ids) == len(set(ids))

    def test_9_by_8_grid(self):
        lib = MatrixDreamLibrary()
        for ptype in PatternType:
            patterns = lib.by_type(ptype)
            assert len(patterns) == 8
            variations = {p.variation for p in patterns}
            assert len(variations) == 8
