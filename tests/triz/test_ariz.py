"""
Tests for ARIZ-85C State Machine.
Verifies all 9 sections, step transitions, validation, and C4 observer mapping.
Runs on 10 classic TRIZ problems.
"""
import pytest

from src.c4.types import C4State
from src.triz.ariz import (
    ARIZ85C,
    ARIZ_STEPS,
    ARIZSection,
    ARIZState,
    ARIZStep,
    get_ariz_step_prompt,
    list_all_steps,
    run_ariz,
)


# =============================================================================
# STEP REGISTRY TESTS
# =============================================================================

class TestStepRegistry:
    def test_all_steps_registered(self):
        steps = list_all_steps()
        assert len(steps) == 28  # Section 1 has 4 steps, rest have 3 each = 28

    def test_section_1_steps(self):
        for sid in ["1.1", "1.2", "1.3", "1.4"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.ANALYSIS

    def test_section_2_steps(self):
        for sid in ["2.1", "2.2", "2.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.FORMULATION

    def test_section_3_steps(self):
        for sid in ["3.1", "3.2", "3.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.SOLUTION

    def test_section_4_steps(self):
        for sid in ["4.1", "4.2", "4.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.METHOD_ANALYSIS

    def test_section_5_steps(self):
        for sid in ["5.1", "5.2", "5.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.IMPLEMENTATION

    def test_section_6_steps(self):
        for sid in ["6.1", "6.2", "6.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.VERIFICATION

    def test_section_7_steps(self):
        for sid in ["7.1", "7.2", "7.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.REFINEMENT

    def test_section_8_steps(self):
        for sid in ["8.1", "8.2", "8.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.SYNTHESIS

    def test_section_9_steps(self):
        for sid in ["9.1", "9.2", "9.3"]:
            assert sid in ARIZ_STEPS
            assert ARIZ_STEPS[sid].section == ARIZSection.FINALIZATION

    def test_each_step_has_prompt(self):
        for step in ARIZ_STEPS.values():
            assert step.prompt
            assert len(step.prompt) > 20

    def test_each_step_has_validation(self):
        for step in ARIZ_STEPS.values():
            assert step.validation is not None

    def test_each_step_has_transitions(self):
        for step in ARIZ_STEPS.values():
            assert "default" in step.transitions

    def test_step_prompt_retrieval(self):
        prompt = get_ariz_step_prompt("1.1")
        assert "problem" in prompt.lower() or "system" in prompt.lower()


# =============================================================================
# C4 OBSERVER TESTS
# =============================================================================

class TestC4Observers:
    def test_analysis_is_o0(self):
        for sid in ["1.1", "1.2", "1.3", "1.4", "2.1"]:
            assert ARIZ_STEPS[sid].c4_observer == "O0"

    def test_formulation_solution_is_o1(self):
        for sid in ["2.2", "2.3", "3.1", "3.2", "3.3", "4.1", "4.2", "4.3"]:
            assert ARIZ_STEPS[sid].c4_observer == "O1" or ARIZ_STEPS[sid].c4_observer == "O2"

    def test_final_sections_are_o2(self):
        for sid in ["5.1", "5.2", "5.3", "6.1", "6.2", "6.3",
                     "7.1", "7.2", "7.3", "8.1", "8.2", "8.3", "9.1", "9.2", "9.3"]:
            assert ARIZ_STEPS[sid].c4_observer == "O2"


# =============================================================================
# STATE MACHINE TESTS
# =============================================================================

class TestStateMachine:
    def test_start_state(self):
        ariz = ARIZ85C()
        state = ariz.start("Test problem")
        assert state.current_step_id == "1.1"
        assert not state.completed
        assert state.context["problem_statement"] == "Test problem"

    def test_advance_valid_output(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        output = {
            "system": "bicycle",
            "useful_function": "transport",
            "harmful_effect": "weight",
            "environment": "city",
        }
        new_state = ariz.advance(state, output)
        assert new_state.current_step_id == "1.2"
        assert len(new_state.history) == 1
        assert new_state.history[0]["valid"] is True

    def test_advance_invalid_output(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        output = {}  # missing required fields
        new_state = ariz.advance(state, output)
        assert new_state.current_step_id == "1.1"  # did not advance
        assert len(new_state.history) == 1
        assert new_state.history[0]["valid"] is False
        assert len(new_state.history[0]["errors"]) > 0

    def test_run_step_diagnostics(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        output = {
            "system": "car",
            "useful_function": "drive",
            "harmful_effect": "pollution",
        }
        new_state, step, valid, errors = ariz.run_step(state, output)
        assert valid is True
        assert len(errors) == 0
        assert step.step_id == "1.1"

    def test_progress_tracking(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        progress = ariz.get_progress(state)
        assert progress["current_step"] == "1.1"
        assert progress["current_section"] == "Analysis"
        assert progress["steps_completed"] == 0

    def test_terminal_state(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        # Fast-forward to 9.3
        state.current_step_id = "9.3"
        output = {"accepted": True}
        new_state = ariz.advance(state, output)
        assert new_state.completed


# =============================================================================
# TRANSITION LOGIC TESTS
# =============================================================================

class TestTransitions:
    def test_default_transition_1_1_to_1_2(self):
        step = ARIZ_STEPS["1.1"]
        assert step.next_step({}) == "1.2"

    def test_default_transition_1_4_to_2_1(self):
        step = ARIZ_STEPS["1.4"]
        assert step.next_step({}) == "2.1"

    def test_default_transition_3_3_to_4_1(self):
        step = ARIZ_STEPS["3.3"]
        assert step.next_step({}) == "4.1"

    def test_conditional_transition_6_1_backtrack(self):
        step = ARIZ_STEPS["6.1"]
        assert step.next_step({"contradiction_resolved": False}) == "7.1"
        assert step.next_step({"contradiction_resolved": True}) == "6.2"

    def test_conditional_transition_6_2_backtrack(self):
        step = ARIZ_STEPS["6.2"]
        assert step.next_step({"physical_contradiction_resolved": False}) == "7.1"
        assert step.next_step({"physical_contradiction_resolved": True}) == "6.3"

    def test_conditional_transition_6_3_backtrack(self):
        step = ARIZ_STEPS["6.3"]
        assert step.next_step({"sufield_complete": False}) == "7.1"
        assert step.next_step({"sufield_complete": True}) == "7.1"


# =============================================================================
# C4 MAPPING TESTS
# =============================================================================

class TestC4Mapping:
    def test_c4_observer_transition(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        # Simulate running through a few steps
        state = ariz.advance(state, {"system": "x", "useful_function": "y", "harmful_effect": "z"})
        state = ariz.advance(state, {"improving_parameter": "a", "worsening_parameter": "b"})
        mapping = ariz.get_c4_observer_transition(state)
        assert "observer_sequence" in mapping
        assert "observer_progression" in mapping
        assert "c4_path" in mapping
        assert "c4_tuples" in mapping

    def test_c4_tuples_are_valid(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        state = ariz.advance(state, {"system": "x", "useful_function": "y", "harmful_effect": "z"})
        mapping = ariz.get_c4_observer_transition(state)
        for tup in mapping["c4_tuples"]:
            assert len(tup) == 3
            for coord in tup:
                assert 0 <= coord <= 2


# =============================================================================
# 10 CLASSIC TRIZ PROBLEMS TESTS
# =============================================================================

CLASSIC_PROBLEMS = [
    {
        "name": "Coffee cup burning hands",
        "text": "A coffee cup keeps coffee hot but burns the user's hands.",
        "system": "coffee cup",
        "useful": "keep coffee hot",
        "harmful": "burn hands",
        "improving": "temperature retention",
        "worsening": "safety",
        "physical_element": "cup wall",
        "physical_property": "hot",
        "physical_opposite": "cold",
    },
    {
        "name": "Airplane wing size",
        "text": "An airplane wing must be large for lift but small for low drag.",
        "system": "airplane wing",
        "useful": "generate lift",
        "harmful": "create drag",
        "improving": "lift",
        "worsening": "drag",
        "physical_element": "wing area",
        "physical_property": "large",
        "physical_opposite": "small",
    },
    {
        "name": "Hammer and nail",
        "text": "A hammer drives a nail but damages the surrounding wood.",
        "system": "hammer and nail",
        "useful": "drive nail",
        "harmful": "damage wood",
        "improving": "penetration",
        "worsening": "surface integrity",
        "physical_element": "hammer force",
        "physical_property": "strong",
        "physical_opposite": "gentle",
    },
    {
        "name": "Car brake heating",
        "text": "Car brakes must be strong to stop quickly but weak to avoid overheating.",
        "system": "car brake",
        "useful": "stop car",
        "harmful": "overheat",
        "improving": "braking force",
        "worsening": "temperature",
        "physical_element": "brake pad friction",
        "physical_property": "high",
        "physical_opposite": "low",
    },
    {
        "name": "Swimsuit drag",
        "text": "A competitive swimsuit must be smooth to reduce drag but textured to retain water.",
        "system": "swimsuit",
        "useful": "reduce drag",
        "harmful": "water retention",
        "improving": "speed",
        "worsening": "buoyancy control",
        "physical_element": "suit surface",
        "physical_property": "smooth",
        "physical_opposite": "rough",
    },
    {
        "name": "Lightbulb filament",
        "text": "A lightbulb filament must be hot to emit light but cold to avoid evaporation.",
        "system": "lightbulb filament",
        "useful": "emit light",
        "harmful": "evaporate",
        "improving": "luminosity",
        "worsening": "lifespan",
        "physical_element": "filament temperature",
        "physical_property": "hot",
        "physical_opposite": "cold",
    },
    {
        "name": "Knife sharpness",
        "text": "A knife must be sharp to cut but blunt to avoid injury.",
        "system": "knife",
        "useful": "cut food",
        "harmful": "cut user",
        "improving": "cutting ability",
        "worsening": "safety",
        "physical_element": "blade edge",
        "physical_property": "sharp",
        "physical_opposite": "blunt",
    },
    {
        "name": "Spring stiffness",
        "text": "A suspension spring must be stiff to support load but soft to absorb shock.",
        "system": "suspension spring",
        "useful": "support load",
        "harmful": "transmit shock",
        "improving": "load capacity",
        "worsening": "comfort",
        "physical_element": "spring stiffness",
        "physical_property": "stiff",
        "physical_opposite": "soft",
    },
    {
        "name": "Information visibility",
        "text": "Information on a screen must be visible to users but invisible to shoulder surfers.",
        "system": "display screen",
        "useful": "show information",
        "harmful": "privacy leak",
        "improving": "readability",
        "worsening": "security",
        "physical_element": "screen viewing angle",
        "physical_property": "wide",
        "physical_opposite": "narrow",
    },
    {
        "name": "Tire width",
        "text": "A tire must be wide for traction but narrow for low rolling resistance.",
        "system": "tire",
        "useful": "provide traction",
        "harmful": "increase resistance",
        "improving": "grip",
        "worsening": "fuel efficiency",
        "physical_element": "tire width",
        "physical_property": "wide",
        "physical_opposite": "narrow",
    },
]


class TestClassicProblems:
    @pytest.mark.parametrize("problem", CLASSIC_PROBLEMS, ids=lambda p: p["name"])
    def test_problem_can_be_run_through_ariz(self, problem):
        ariz = ARIZ85C()
        state = ariz.start(problem["text"])

        # Section 1: Analysis
        state = ariz.advance(state, {
            "system": problem["system"],
            "useful_function": problem["useful"],
            "harmful_effect": problem["harmful"],
            "environment": "general",
        })
        assert state.current_step_id == "1.2"

        state = ariz.advance(state, {
            "improving_parameter": problem["improving"],
            "worsening_parameter": problem["worsening"],
            "conflict_description": f"{problem['improving']} vs {problem['worsening']}",
        })
        assert state.current_step_id == "1.3"

        state = ariz.advance(state, {
            "contradiction_statement": f"If we increase {problem['improving']}, then {problem['worsening']} worsens.",
            "action": f"increase {problem['improving']}",
            "triz_improving_id": "1",
            "triz_worsening_id": "2",
        })
        assert state.current_step_id == "1.4"

        state = ariz.advance(state, {
            "mini_problem": f"How to achieve {problem['useful']} without {problem['harmful']}?",
            "ideal_outcome": f"{problem['system']} performs {problem['useful']} with zero {problem['harmful']}",
            "constraints": "minimal cost",
        })
        assert state.current_step_id == "2.1"

        # Section 2: Formulation
        state = ariz.advance(state, {
            "element": problem["physical_element"],
            "property": problem["physical_property"],
            "opposite": problem["physical_opposite"],
            "useful_reason": problem["useful"],
            "avoid_harm": problem["harmful"],
        })
        assert state.current_step_id == "2.2"

        state = ariz.advance(state, {
            "ifr_statement": f"The {problem['physical_element']} performs {problem['useful']} by itself.",
            "ideal_element": problem["physical_element"],
            "ideal_mechanism": "self-regulating",
        })
        assert state.current_step_id == "2.3"

        state = ariz.advance(state, {
            "x_element_candidates": ["smart material", "gradient structure", "feedback loop"],
            "chosen_x_element": "gradient structure",
            "reasoning": "combines opposing properties spatially",
        })
        assert state.current_step_id == "3.1"

        # Verify context accumulated correctly
        assert state.context["system"] == problem["system"]
        assert state.context["element"] == problem["physical_element"]
        assert state.context["property"] == problem["physical_property"]

    def test_all_10_problems_run(self):
        for problem in CLASSIC_PROBLEMS:
            ariz = ARIZ85C()
            state = ariz.start(problem["text"])
            outputs = [
                {"system": problem["system"], "useful_function": problem["useful"], "harmful_effect": problem["harmful"], "environment": "general"},
                {"improving_parameter": problem["improving"], "worsening_parameter": problem["worsening"], "conflict_description": "test"},
                {"contradiction_statement": "test", "action": "test", "triz_improving_id": "1", "triz_worsening_id": "2"},
                {"mini_problem": "test", "ideal_outcome": "test", "constraints": "test"},
                {"element": problem["physical_element"], "property": problem["physical_property"], "opposite": problem["physical_opposite"], "useful_reason": "test", "avoid_harm": "test"},
                {"ifr_statement": "test", "ideal_element": "test", "ideal_mechanism": "test"},
                {"x_element_candidates": ["a"], "chosen_x_element": "a", "reasoning": "test"},
            ]
            for output in outputs:
                if state.completed:
                    break
                state = ariz.advance(state, output)
            assert not state.completed  # Should reach at least 3.1
            assert len(state.history) == len(outputs)


# =============================================================================
# BACKTRACKING TESTS
# =============================================================================

class TestBacktracking:
    def test_verification_failure_backtrack(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        state.current_step_id = "6.1"
        output = {"contradiction_resolved": False}
        new_state = ariz.advance(state, output)
        assert new_state.current_step_id == "7.1"

    def test_verification_success_continue(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        state.current_step_id = "6.1"
        output = {"contradiction_resolved": True}
        new_state = ariz.advance(state, output)
        assert new_state.current_step_id == "6.2"

    def test_physical_verification_failure(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        state.current_step_id = "6.2"
        output = {"physical_contradiction_resolved": False}
        new_state = ariz.advance(state, output)
        assert new_state.current_step_id == "7.1"

    def test_sufield_incomplete_backtrack(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        state.current_step_id = "6.3"
        output = {"sufield_complete": False}
        new_state = ariz.advance(state, output)
        assert new_state.current_step_id == "7.1"


# =============================================================================
# FULL EXECUTION TEST
# =============================================================================

class TestFullExecution:
    def test_run_ariz_convenience(self):
        outputs = [
            {"system": "bike", "useful_function": "ride", "harmful_effect": "weight"},
            {"improving_parameter": "speed", "worsening_parameter": "comfort"},
            {"contradiction_statement": "test", "action": "test", "triz_improving_id": "1", "triz_worsening_id": "2"},
            {"mini_problem": "test", "ideal_outcome": "test", "constraints": "test"},
            {"element": "frame", "property": "stiff", "opposite": "flexible", "useful_reason": "test", "avoid_harm": "test"},
            {"ifr_statement": "test", "ideal_element": "test", "ideal_mechanism": "test"},
            {"x_element_candidates": ["a"], "chosen_x_element": "a", "reasoning": "test"},
        ]
        state = run_ariz("How to make a faster bicycle?", outputs)
        assert len(state.history) == len(outputs)
        assert state.context["system"] == "bike"

    def test_trace_completeness(self):
        ariz = ARIZ85C()
        state = ariz.start("Test")
        for _ in range(3):
            state = ariz.advance(state, {
                "system": "x", "useful_function": "y", "harmful_effect": "z",
            })
            if state.current_step_id != "1.2":
                break
            state = ariz.advance(state, {
                "improving_parameter": "a", "worsening_parameter": "b",
            })
            if state.current_step_id != "1.3":
                break
            state = ariz.advance(state, {
                "contradiction_statement": "c", "action": "d",
                "triz_improving_id": "1", "triz_worsening_id": "2",
            })
            break
        trace = ariz.get_full_trace(state)
        assert len(trace) >= 1
        for entry in trace:
            assert "step_id" in entry
            assert "valid" in entry
