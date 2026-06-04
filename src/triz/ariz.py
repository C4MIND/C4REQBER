"""
ARIZ-85C: Algorithm for Inventive Problem Solving — State Machine Implementation.

ARIZ is the crown jewel of TRIZ: a rigorous, step-by-step algorithm that guides
the problem-solver from an ill-defined problem to a concrete, inventive solution.

This module implements all 9 sections of ARIZ-85C as an explicit state machine:
  Section 1: Analysis        (steps 1.1 – 1.4)
  Section 2: Formulation     (steps 2.1 – 2.3)
  Section 3: Solution        (steps 3.1 – 3.3)
  Section 4: Analysis of Method (steps 4.1 – 4.3)
  Section 5: Implementation  (steps 5.1 – 5.3)
  Section 6: Verification    (steps 6.1 – 6.3)
  Section 7: Refinement      (steps 7.1 – 7.3)
  Section 8: Synthesis       (steps 8.1 – 8.3)
  Section 9: Finalization    (steps 9.1 – 9.3)

Each step has:
  - prompt_template:   guidance for LLM / human parsing
  - validation_rules:  callable predicates that check step output
  - transition_logic:  deterministic next-step selection

C4 Observer Integration:
  - O0 (initial observer)    → Section 1–2 (problem framing)
  - O1 (intermediate observer) → Section 3–5 (solution search)
  - O2 (systemic observer)   → Section 6–9 (verification & synthesis)
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

from src.c4.state import C4State


# =============================================================================
# ARIZ STEP DEFINITIONS
# =============================================================================

class ARIZSection(Enum):
    """The nine sections of ARIZ-85C."""

    ANALYSIS = auto()            # Section 1
    FORMULATION = auto()         # Section 2
    SOLUTION = auto()            # Section 3
    METHOD_ANALYSIS = auto()     # Section 4
    IMPLEMENTATION = auto()      # Section 5
    VERIFICATION = auto()        # Section 6
    REFINEMENT = auto()          # Section 7
    SYNTHESIS = auto()           # Section 8
    FINALIZATION = auto()        # Section 9


@dataclass
class ARIZStep:
    """
    A single step in the ARIZ-85C algorithm.

    Attributes:
        section:      Which ARIZ section this step belongs to.
        step_id:      Human-readable ID, e.g. "1.1", "3.2".
        name:         Short title.
        prompt:       Natural-language guidance for LLM parsing.
        validation:   Callable that accepts step_output (dict) and returns
                      (is_valid: bool, errors: List[str]).
        transitions:  Dict mapping condition -> next_step_id. Special key
                      "default" is the fallback.
        c4_observer:  Observer level for this step: "O0", "O1", or "O2".
    """
    section: ARIZSection
    step_id: str
    name: str
    prompt: str
    validation: Callable[[dict[str, Any]], tuple[bool, list[str]]]
    transitions: dict[str, str]
    c4_observer: str = "O0"

    def validate(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        return self.validation(output)

    def next_step(self, output: dict[str, Any]) -> str:
        """Determine the next step based on transition logic."""
        for condition, next_id in self.transitions.items():
            if condition == "default":
                continue
            if self._evaluate_condition(condition, output):
                return next_id
        return self.transitions.get("default", "9.3")

    def _evaluate_condition(self, condition: str, output: dict[str, Any]) -> bool:
        """Evaluate a simple condition string against step output using safe evaluator."""
        from src.utils.safe_eval import SafeExpressionEvaluator
        try:
            evaluator = SafeExpressionEvaluator()
            # Convert condition to safe expression with output variables
            result = evaluator.evaluate(condition, {**output, "True": True, "False": False})
            return bool(result)
        except (ValueError, KeyError, TypeError):
            return False


# =============================================================================
# DEFAULT VALIDATORS
# =============================================================================

def _non_empty_validator(keys: list[str]) -> Callable[[dict[str, Any]], tuple[bool, list[str]]]:
    """Factory: validate that specified keys exist and are non-empty."""
    def validator(output: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validator."""
        errors = []
        for k in keys:
            if k not in output or output[k] is None:
                errors.append(f"Missing or empty required field: '{k}'")
            elif isinstance(output[k], str) and output[k].strip() == "":
                errors.append(f"Missing or empty required field: '{k}'")
        return len(errors) == 0, errors
    return validator


def _always_valid(output: dict[str, Any]) -> tuple[bool, list[str]]:
    return True, []


# =============================================================================
# ARIZ-85C STEP REGISTRY
# =============================================================================

ARIZ_STEPS: dict[str, ARIZStep] = {}


def _register(step: ARIZStep) -> None:
    ARIZ_STEPS[step.step_id] = step


# ------------------------------------------------------------------
# SECTION 1: ANALYSIS (1.1 – 1.4)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.ANALYSIS,
    step_id="1.1",
    name="Problem Analysis",
    prompt=(
        "Analyze the given problem statement. Identify:\n"
        "  1. The system and its components\n"
        "  2. The intended useful function\n"
        "  3. The harmful effect or deficiency\n"
        "  4. The operating environment and constraints\n"
        "Return a structured dict with keys: system, useful_function, harmful_effect, environment."
    ),
    validation=_non_empty_validator(["system", "useful_function", "harmful_effect"]),
    transitions={"default": "1.2"},
    c4_observer="O0",
))

_register(ARIZStep(
    section=ARIZSection.ANALYSIS,
    step_id="1.2",
    name="Conflicting Pairs Identification",
    prompt=(
        "From the problem analysis, extract the conflicting pairs:\n"
        "  - Parameter A: what improves when we take action\n"
        "  - Parameter B: what worsens as a consequence\n"
        "Return dict with keys: improving_parameter, worsening_parameter, conflict_description."
    ),
    validation=_non_empty_validator(["improving_parameter", "worsening_parameter"]),
    transitions={"default": "1.3"},
    c4_observer="O0",
))

_register(ARIZStep(
    section=ARIZSection.ANALYSIS,
    step_id="1.3",
    name="Technical Contradiction Formulation",
    prompt=(
        "Formulate the technical contradiction in standard TRIZ format:\n"
        "  'If we do [ACTION], then [PARAMETER A] improves but [PARAMETER B] worsens.'\n"
        "Also map to TRIZ 39 engineering parameters if possible.\n"
        "Return dict with keys: contradiction_statement, action, triz_improving_id, triz_worsening_id."
    ),
    validation=_non_empty_validator(["contradiction_statement", "action"]),
    transitions={"default": "1.4"},
    c4_observer="O0",
))

_register(ARIZStep(
    section=ARIZSection.ANALYSIS,
    step_id="1.4",
    name="Mini-Problem Formulation",
    prompt=(
        "Reformulate the problem as a 'mini-problem':\n"
        "  'How can we achieve [USEFUL FUNCTION] without [HARMFUL EFFECT]\n"
        "   while keeping the existing system as unchanged as possible?'\n"
        "Return dict with keys: mini_problem, ideal_outcome, constraints."
    ),
    validation=_non_empty_validator(["mini_problem", "ideal_outcome"]),
    transitions={"default": "2.1"},
    c4_observer="O0",
))


# ------------------------------------------------------------------
# SECTION 2: FORMULATION (2.1 – 2.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.FORMULATION,
    step_id="2.1",
    name="Physical Contradiction",
    prompt=(
        "Identify the underlying physical contradiction:\n"
        "  'The [ELEMENT] must be [PROPERTY] to [USEFUL REASON],\n"
        "   AND must be [OPPOSITE] to [AVOID HARM].'\n"
        "Return dict with keys: element, property, opposite, useful_reason, avoid_harm."
    ),
    validation=_non_empty_validator(["element", "property", "opposite"]),
    transitions={"default": "2.2"},
    c4_observer="O0",
))

_register(ARIZStep(
    section=ARIZSection.FORMULATION,
    step_id="2.2",
    name="Ideal Final Result (IFR)",
    prompt=(
        "Formulate the Ideal Final Result (IFR):\n"
        "  'The [ELEMENT] performs [USEFUL FUNCTION] by itself,\n"
        "   without any additional mechanisms, energy, or complexity.'\n"
        "Return dict with keys: ifr_statement, ideal_element, ideal_mechanism."
    ),
    validation=_non_empty_validator(["ifr_statement"]),
    transitions={"default": "2.3"},
    c4_observer="O1",
))

_register(ARIZStep(
    section=ARIZSection.FORMULATION,
    step_id="2.3",
    name="X-Element Definition",
    prompt=(
        "Define the X-element: the unknown resource, substance, field, or mechanism\n"
        "that would resolve the physical contradiction and achieve the IFR.\n"
        "Consider: substances in the system, in the environment, or that can be introduced.\n"
        "Return dict with keys: x_element_candidates, chosen_x_element, reasoning."
    ),
    validation=_non_empty_validator(["x_element_candidates"]),
    transitions={"default": "3.1"},
    c4_observer="O1",
))


# ------------------------------------------------------------------
# SECTION 3: SOLUTION (3.1 – 3.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.SOLUTION,
    step_id="3.1",
    name="Su-Field Model Construction",
    prompt=(
        "Construct a Su-Field model for the problem:\n"
        "  - S1: the object being acted upon\n"
        "  - S2: the tool or instrument\n"
        "  - F: the field coupling them\n"
        "Identify if the Su-Field is complete, incomplete, or harmful.\n"
        "Return dict with keys: s1, s2, field_type, model_status, notation."
    ),
    validation=_non_empty_validator(["s1", "s2", "field_type"]),
    transitions={"default": "3.2"},
    c4_observer="O1",
))

_register(ARIZStep(
    section=ARIZSection.SOLUTION,
    step_id="3.2",
    name="Standard Solutions Application",
    prompt=(
        "Apply the 76 Standard Solutions to the Su-Field model:\n"
        "  1. Check Class 1 if Su-Field is incomplete\n"
        "  2. Check Class 2 if Su-Field is harmful\n"
        "  3. Check Class 3 for system transitions\n"
        "  4. Check Class 4 if measurement/detection is needed\n"
        "  5. Check Class 5 for simplification\n"
        "Return dict with keys: applicable_solutions, selected_solution, rationale."
    ),
    validation=_non_empty_validator(["applicable_solutions"]),
    transitions={"default": "3.3"},
    c4_observer="O1",
))

_register(ARIZStep(
    section=ARIZSection.SOLUTION,
    step_id="3.3",
    name="40 Principles Application",
    prompt=(
        "Apply the 40 Inventive Principles using the TRIZ contradiction matrix:\n"
        "  - improving parameter → row\n"
        "  - worsening parameter → column\n"
        "List recommended principles and explain how each applies.\n"
        "Return dict with keys: recommended_principles, chosen_principle, application_description."
    ),
    validation=_non_empty_validator(["recommended_principles"]),
    transitions={"default": "4.1"},
    c4_observer="O1",
))


# ------------------------------------------------------------------
# SECTION 4: METHOD ANALYSIS (4.1 – 4.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.METHOD_ANALYSIS,
    step_id="4.1",
    name="Evaluate Separation Principles",
    prompt=(
        "Evaluate the 4 separation principles for the physical contradiction:\n"
        "  1. In Time: can the property alternate over time?\n"
        "  2. In Space: can different parts have different properties?\n"
        "  3. Parts/Whole: can the whole have one property and parts the other?\n"
        "  4. Under Conditions: can conditions determine which property dominates?\n"
        "Return dict with keys: time_feasible, space_feasible, parts_feasible, conditions_feasible, best_principle."
    ),
    validation=_non_empty_validator(["best_principle"]),
    transitions={"default": "4.2"},
    c4_observer="O1",
))

_register(ARIZStep(
    section=ARIZSection.METHOD_ANALYSIS,
    step_id="4.2",
    name="Substance-Field Resources Check",
    prompt=(
        "Identify Substance-Field Resources (SFR) in the system and environment:\n"
        "  - Internal resources: substances, fields, voids already in the system\n"
        "  - External resources: substances, fields, energy from the environment\n"
        "  - Derived resources: waste products, byproducts, secondary effects\n"
        "Return dict with keys: internal_resources, external_resources, derived_resources, best_resource."
    ),
    validation=_non_empty_validator(["internal_resources", "external_resources"]),
    transitions={"default": "4.3"},
    c4_observer="O1",
))

_register(ARIZStep(
    section=ARIZSection.METHOD_ANALYSIS,
    step_id="4.3",
    name="Trends of Evolution Alignment",
    prompt=(
        "Check alignment with TRIZ Trends of Technical System Evolution:\n"
        "  1. Increasing ideality\n"
        "  2. Increasing dynamism and controllability\n"
        "  3. Transition to super-system or micro-level\n"
        "  4. Increasing automation\n"
        "Return dict with keys: trend_alignment, evolution_stage, future_direction."
    ),
    validation=_non_empty_validator(["trend_alignment"]),
    transitions={"default": "5.1"},
    c4_observer="O2",
))


# ------------------------------------------------------------------
# SECTION 5: IMPLEMENTATION (5.1 – 5.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.IMPLEMENTATION,
    step_id="5.1",
    name="Solution Concept Generation",
    prompt=(
        "Generate a concrete solution concept combining:\n"
        "  - the chosen X-element\n"
        "  - the selected separation principle\n"
        "  - the applicable standard solution or inventive principle\n"
        "Describe the mechanism, structure, or process clearly.\n"
        "Return dict with keys: concept_name, concept_description, mechanism, expected_benefits."
    ),
    validation=_non_empty_validator(["concept_name", "concept_description", "mechanism"]),
    transitions={"default": "5.2"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.IMPLEMENTATION,
    step_id="5.2",
    name="Anticipating Failures",
    prompt=(
        "Anticipate potential failures of the proposed solution:\n"
        "  1. New harmful effects introduced\n"
        "  2. Loss of useful functions\n"
        "  3. Implementation complexity or cost\n"
        "  4. Environmental or safety concerns\n"
        "Return dict with keys: potential_failures, mitigation_strategies, risk_level."
    ),
    validation=_non_empty_validator(["potential_failures", "mitigation_strategies"]),
    transitions={"default": "5.3"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.IMPLEMENTATION,
    step_id="5.3",
    name="Resource Optimization",
    prompt=(
        "Optimize the solution for minimal resource consumption:\n"
        "  - Can any parts be eliminated?\n"
        "  - Can the X-element come from waste or the environment?\n"
        "  - Can multiple functions be combined into fewer components?\n"
        "Return dict with keys: optimized_concept, eliminated_parts, resource_savings."
    ),
    validation=_non_empty_validator(["optimized_concept"]),
    transitions={"default": "6.1"},
    c4_observer="O2",
))


# ------------------------------------------------------------------
# SECTION 6: VERIFICATION (6.1 – 6.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.VERIFICATION,
    step_id="6.1",
    name="Technical Contradiction Resolution Check",
    prompt=(
        "Verify that the technical contradiction is resolved:\n"
        "  - Does [PARAMETER A] still improve?\n"
        "  - Is [PARAMETER B] no longer worsened?\n"
        "  - Are there new contradictions introduced?\n"
        "Return dict with keys: contradiction_resolved, parameter_a_status, parameter_b_status, new_contradictions."
    ),
    validation=_non_empty_validator(["contradiction_resolved"]),
    transitions={
        "contradiction_resolved == False": "7.1",
        "default": "6.2",
    },
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.VERIFICATION,
    step_id="6.2",
    name="Physical Contradiction Resolution Check",
    prompt=(
        "Verify that the physical contradiction is resolved:\n"
        "  - Can [ELEMENT] be [PROPERTY] and [OPPOSITE] as required?\n"
        "  - Is the separation principle correctly applied?\n"
        "  - Does the IFR move closer to ideal?\n"
        "Return dict with keys: physical_contradiction_resolved, separation_applied, ifr_progress."
    ),
    validation=_non_empty_validator(["physical_contradiction_resolved"]),
    transitions={
        "physical_contradiction_resolved == False": "7.1",
        "default": "6.3",
    },
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.VERIFICATION,
    step_id="6.3",
    name="Su-Field Completeness Check",
    prompt=(
        "Verify the Su-Field model of the solution:\n"
        "  - Is the Su-Field complete (S1, S2, F all present)?\n"
        "  - Is the field appropriate for the interaction?\n"
        "  - Are there harmful side-effects in the model?\n"
        "Return dict with keys: sufield_complete, field_appropriate, side_effects."
    ),
    validation=_non_empty_validator(["sufield_complete"]),
    transitions={
        "sufield_complete == False": "7.1",
        "default": "7.1",
    },
    c4_observer="O2",
))


# ------------------------------------------------------------------
# SECTION 7: REFINEMENT (7.1 – 7.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.REFINEMENT,
    step_id="7.1",
    name="Backtrack to Previous Step",
    prompt=(
        "If verification failed, determine where to backtrack:\n"
        "  - Was the X-element wrong? → go to 2.3\n"
        "  - Was the separation principle wrong? → go to 4.1\n"
        "  - Was the standard solution wrong? → go to 3.2\n"
        "  - Was the principle wrong? → go to 3.3\n"
        "Return dict with keys: backtrack_target, reason_for_backtrack, revised_assumption."
    ),
    validation=_non_empty_validator(["backtrack_target", "reason_for_backtrack"]),
    transitions={"default": "7.2"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.REFINEMENT,
    step_id="7.2",
    name="Apply Alternative Approach",
    prompt=(
        "Apply an alternative TRIZ tool to the same problem:\n"
        "  - Try a different separation principle\n"
        "  - Try a different standard solution class\n"
        "  - Try analogical thinking or biological inspiration\n"
        "Return dict with keys: alternative_approach, alternative_solution, comparison."
    ),
    validation=_non_empty_validator(["alternative_approach", "alternative_solution"]),
    transitions={"default": "7.3"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.REFINEMENT,
    step_id="7.3",
    name="Check for Sub-Problems",
    prompt=(
        "Decompose the problem into sub-problems if the main problem remains unsolved:\n"
        "  - Each sub-problem should be simpler than the original\n"
        "  - Sub-problems should be independently solvable\n"
        "Return dict with keys: sub_problems, sub_solutions, integration_plan."
    ),
    validation=_non_empty_validator(["sub_problems"]),
    transitions={"default": "8.1"},
    c4_observer="O2",
))


# ------------------------------------------------------------------
# SECTION 8: SYNTHESIS (8.1 – 8.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.SYNTHESIS,
    step_id="8.1",
    name="Combine Partial Solutions",
    prompt=(
        "Synthesize the final solution by combining all partial results:\n"
        "  - Merge alternative solutions where they reinforce each other\n"
        "  - Resolve conflicts between partial solutions\n"
        "  - Ensure the whole is greater than the sum of parts\n"
        "Return dict with keys: synthesized_solution, component_solutions, synergy_description."
    ),
    validation=_non_empty_validator(["synthesized_solution"]),
    transitions={"default": "8.2"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.SYNTHESIS,
    step_id="8.2",
    name="Final Su-Field Model",
    prompt=(
        "Construct the final Su-Field model of the synthesized solution:\n"
        "  - S1 (final object)\n"
        "  - S2 (final tool / X-element)\n"
        "  - F (final field)\n"
        "  - Any S3 mediators\n"
        "Return dict with keys: final_s1, final_s2, final_f, final_s3, final_notation."
    ),
    validation=_non_empty_validator(["final_s1", "final_s2", "final_f"]),
    transitions={"default": "8.3"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.SYNTHESIS,
    step_id="8.3",
    name="C4 State Mapping",
    prompt=(
        "Map the solution trajectory to C4 cognitive states:\n"
        "  - Starting state (problem framing)\n"
        "  - Intermediate states (analysis and formulation)\n"
        "  - Ending state (synthesized solution)\n"
        "Describe the observer transitions (O0 → O1 → O2).\n"
        "Return dict with keys: c4_start, c4_end, c4_path, observer_transitions."
    ),
    validation=_non_empty_validator(["c4_start", "c4_end", "c4_path"]),
    transitions={"default": "9.1"},
    c4_observer="O2",
))


# ------------------------------------------------------------------
# SECTION 9: FINALIZATION (9.1 – 9.3)
# ------------------------------------------------------------------

_register(ARIZStep(
    section=ARIZSection.FINALIZATION,
    step_id="9.1",
    name="Solution Documentation",
    prompt=(
        "Document the final solution comprehensively:\n"
        "  1. Problem statement\n"
        "  2. Contradictions identified\n"
        "  3. X-element and separation principle used\n"
        "  4. Final mechanism / structure / process\n"
        "  5. Expected benefits and metrics\n"
        "Return dict with keys: problem, contradictions, x_element, mechanism, benefits."
    ),
    validation=_non_empty_validator(["problem", "mechanism", "benefits"]),
    transitions={"default": "9.2"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.FINALIZATION,
    step_id="9.2",
    name="Patentability Assessment",
    prompt=(
        "Assess the patentability / novelty of the solution:\n"
        "  1. Is the X-element usage novel in this context?\n"
        "  2. Is the separation principle application non-obvious?\n"
        "  3. Are there prior art conflicts?\n"
        "Return dict with keys: novelty_score, non_obviousness, prior_art_risks, patent_recommendation."
    ),
    validation=_non_empty_validator(["novelty_score", "patent_recommendation"]),
    transitions={"default": "9.3"},
    c4_observer="O2",
))

_register(ARIZStep(
    section=ARIZSection.FINALIZATION,
    step_id="9.3",
    name="Final Acceptance",
    prompt=(
        "Final check: is the solution accepted?\n"
        "  - Does it solve the mini-problem?\n"
        "  - Is it feasible with available resources?\n"
        "  - Does it move toward the Ideal Final Result?\n"
        "Return dict with keys: accepted, acceptance_criteria_met, next_actions."
    ),
    validation=_non_empty_validator(["accepted"]),
    transitions={"default": "9.3"},  # terminal
    c4_observer="O2",
))


# =============================================================================
# ARIZ STATE MACHINE ENGINE
# =============================================================================

@dataclass
class ARIZState:
    """Runtime state of the ARIZ-85C algorithm."""
    current_step_id: str = "1.1"
    history: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "current_step_id": self.current_step_id,
            "history": self.history,
            "context": self.context,
            "completed": self.completed,
        }


class ARIZ85C:
    """
    ARIZ-85C State Machine.

    Usage:
        ariz = ARIZ85C()
        state = ariz.start(problem_text="How to make a faster bicycle?")
        while not state.completed:
            step = ariz.get_current_step(state)
            # LLM or human processes step.prompt and produces output
            output = {...}
            state = ariz.advance(state, output)
    """

    def __init__(self) -> None:
        self.steps = ARIZ_STEPS

    def start(self, problem_text: str, initial_context: dict[str, Any] | None = None) -> ARIZState:
        """Initialize ARIZ with a problem statement."""
        ctx = initial_context or {}
        ctx["problem_statement"] = problem_text
        return ARIZState(
            current_step_id="1.1",
            history=[],
            context=ctx,
            completed=False,
        )

    def get_current_step(self, state: ARIZState) -> ARIZStep:
        """Retrieve the current step definition."""
        if state.current_step_id not in self.steps:
            raise ValueError(f"Unknown step: {state.current_step_id}")
        return self.steps[state.current_step_id]

    def advance(
        self,
        state: ARIZState,
        step_output: dict[str, Any],
    ) -> ARIZState:
        """
        Advance the state machine by one step.

        Args:
            state: Current ARIZ runtime state.
            step_output: Output dict produced for the current step.

        Returns:
            Updated ARIZState with next step selected.
        """
        step = self.get_current_step(state)

        # Validate
        is_valid, errors = step.validate(step_output)
        if not is_valid:
            # Do not advance; record validation failure
            new_state = copy.deepcopy(state)
            new_state.history.append({
                "step_id": step.step_id,
                "output": step_output,
                "valid": False,
                "errors": errors,
            })
            return new_state

        # Determine next step
        next_step_id = step.next_step(step_output)

        # Check for terminal
        completed = next_step_id == step.step_id and step.step_id == "9.3"

        # Update context with step output
        new_state = copy.deepcopy(state)
        new_state.history.append({
            "step_id": step.step_id,
            "output": step_output,
            "valid": True,
            "errors": [],
        })
        new_state.context.update(step_output)
        new_state.current_step_id = next_step_id
        new_state.completed = completed
        return new_state

    def run_step(
        self,
        state: ARIZState,
        step_output: dict[str, Any],
    ) -> tuple[ARIZState, ARIZStep, bool, list[str]]:
        """
        Run a single step and return full diagnostics.

        Returns:
            (new_state, current_step, was_valid, errors)
        """
        step = self.get_current_step(state)
        is_valid, errors = step.validate(step_output)
        if not is_valid:
            new_state = copy.deepcopy(state)
            new_state.history.append({
                "step_id": step.step_id,
                "output": step_output,
                "valid": False,
                "errors": errors,
            })
            return new_state, step, False, errors

        next_step_id = step.next_step(step_output)
        completed = next_step_id == step.step_id and step.step_id == "9.3"

        new_state = copy.deepcopy(state)
        new_state.history.append({
            "step_id": step.step_id,
            "output": step_output,
            "valid": True,
            "errors": [],
        })
        new_state.context.update(step_output)
        new_state.current_step_id = next_step_id
        new_state.completed = completed
        return new_state, step, True, []

    def get_full_trace(self, state: ARIZState) -> list[dict[str, Any]]:
        """Return the complete execution trace."""
        return state.history

    def get_c4_observer_transition(self, state: ARIZState) -> dict[str, Any]:
        """
        Map the ARIZ execution history to C4 observer transitions.
        """
        observer_sequence = []
        for entry in state.history:
            sid = entry["step_id"]
            if sid in self.steps:
                observer_sequence.append(self.steps[sid].c4_observer)

        # Unique observer progression
        progression = []
        last = None
        for obs in observer_sequence:
            if obs != last:
                progression.append(obs)
                last = obs

        # C4 state mapping
        observer_to_c4 = {
            "O0": C4State(T=1, S=0, A=0),  # Present, Concrete, Self
            "O1": C4State(T=2, S=1, A=1),  # Future, Abstract, Other
            "O2": C4State(T=1, S=2, A=2),  # Present, Meta, System
        }

        c4_path = [observer_to_c4.get(o, C4State(T=1, S=0, A=0)) for o in progression]

        return {
            "observer_sequence": observer_sequence,
            "observer_progression": progression,
            "c4_path": [str(s) for s in c4_path],
            "c4_tuples": [s.to_tuple() for s in c4_path],
        }

    def get_progress(self, state: ARIZState) -> dict[str, Any]:
        """Return human-readable progress information."""
        step = self.get_current_step(state)
        section_names = {
            ARIZSection.ANALYSIS: "Analysis",
            ARIZSection.FORMULATION: "Formulation",
            ARIZSection.SOLUTION: "Solution",
            ARIZSection.METHOD_ANALYSIS: "Method Analysis",
            ARIZSection.IMPLEMENTATION: "Implementation",
            ARIZSection.VERIFICATION: "Verification",
            ARIZSection.REFINEMENT: "Refinement",
            ARIZSection.SYNTHESIS: "Synthesis",
            ARIZSection.FINALIZATION: "Finalization",
        }
        return {
            "current_step": step.step_id,
            "current_section": section_names.get(step.section, "Unknown"),
            "step_name": step.name,
            "observer_level": step.c4_observer,
            "steps_completed": len(state.history),
            "is_completed": state.completed,
        }


# =============================================================================
# CONVENIENCE API
# =============================================================================

def run_ariz(problem_text: str, step_outputs: list[dict[str, Any]]) -> ARIZState:
    """
    Run ARIZ-85C through a pre-determined sequence of step outputs.
    Useful for testing and scripted execution.
    """
    ariz = ARIZ85C()
    state = ariz.start(problem_text)
    for output in step_outputs:
        if state.completed:
            break
        state = ariz.advance(state, output)
    return state


def get_ariz_step_prompt(step_id: str) -> str:
    """Get the LLM prompt for a specific ARIZ step."""
    if step_id not in ARIZ_STEPS:
        raise ValueError(f"Unknown step: {step_id}")
    return ARIZ_STEPS[step_id].prompt


def list_all_steps() -> list[dict[str, str]]:
    """List all ARIZ steps with metadata."""
    return [
        {
            "step_id": s.step_id,
            "name": s.name,
            "section": s.section.name,
            "observer": s.c4_observer,
        }
        for s in ARIZ_STEPS.values()
    ]
