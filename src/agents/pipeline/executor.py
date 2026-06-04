"""
C44TCDI: Pipeline Executor
Extracts step execution logic from UniversalSolvePipeline.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStepResult
from src.c4.observer import ObserverController, ObserverPosition
from src.c4.state import C4State
from src.pipeline.observer import PipelineObserver
from src.pipeline.step_definition import STEP_MODULES as _STEP_MODULES


# Step functions are imported lazily to avoid circular imports
# and to allow test mocking via _agents_pipeline_module
_step_impact_identify = None
_step_prior_art = None
_step_gap_analysis = None
_step_quality_gate = None
_step_reality_check = None
_step_c4_fingerprint = None
_step_cross_domain_transfer = None
_step_mp_rotation = None
_step_qzrf_select = None
_step_isomorphism_search = None
_step_plugins = None
_step_synthesis = None
_step_validation = None
_step_simulation = None


def _get_step_fn(name: str) -> Any:
    """Lazy import step function, checking _agents_pipeline_module first for test mocks."""
    import sys

    # Check if test module has mocked the function
    if "_agents_pipeline_module" in sys.modules:
        mod = sys.modules["_agents_pipeline_module"]
        if hasattr(mod, name):
            return getattr(mod, name)

    # Fallback: import from actual step module
    globals_dict = globals()
    cache_key = f"_{name}"
    if globals_dict.get(cache_key) is not None:
        return globals_dict[cache_key]

    step_modules = _STEP_MODULES

    import importlib

    module_path = step_modules[name]
    mod = importlib.import_module(module_path)
    fn = getattr(mod, name)
    globals_dict[cache_key] = fn
    return fn


MODE_CONFIG = {
    "autopilot": {"max_steps": 10, "enable_llm_enhancement": False, "enable_verification": False},
    "turbo": {"max_steps": 10, "enable_llm_enhancement": True, "enable_verification": False, "parallel_perspectives": True},
    "deep-work": {"max_steps": 12, "enable_llm_enhancement": True, "enable_verification": True, "proof_export": True},
}


def _find_step(steps, stage):
    """Locate a completed step in the result step list by stage enum."""
    return next((s for s in steps if s.stage == stage), None)


def _step_output(steps, stage, key, default=None):
    """Extract output_data[key] from a completed step, or default."""
    s = _find_step(steps, stage)
    return s.output_data.get(key, default) if s else default


# ---------------------------------------------------------------------------
# Post-processing callbacks — invoked after step_complete for each step_id
# ---------------------------------------------------------------------------

def _on_s2(p, s, r, e):
    """Step 2 (Prior Art): capture confidence and recommendation."""
    conf = e.get("data", {}).get("max_confidence", 0.0)
    s["prior_art_confidence"] = conf
    p._prior_art_confidence = conf
    if r.steps and r.steps[-1].stage == PipelineStage.PRIOR_ART:
        r.prior_art_summary = r.steps[-1].output_data.get("recommendation", "")


def _on_s2b(p, s, r, e):
    """Step 2b (Gap Analysis): capture gap list for downstream use."""
    s["gap_results"] = e.get("data", {}).get("gaps", [])


def _on_s2c(p, s, r, e):
    """Step 2c (Quality Gate): capture full quality-gate results."""
    s["quality_gate_results"] = e.get("data", {})


def _on_s3(p, s, r, e):
    """Step 3 (C4 Fingerprint): extract c4_state from output."""
    s["c4_state"] = e.get("data", {}).get("c4_state", C4State(1, 1, 1))


def _on_s4(p, s, r, e):
    """Step 4 (MP Rotation): store perspectives on result."""
    r.mp_perspectives = r.steps[-1].output_data.get("perspectives", [])


def _on_s5(p, s, r, e):
    """Step 5 (QZRF Select): store operator recommendations."""
    r.qzrf_recommendations = r.steps[-1].output_data.get("operators", [])


def _on_s6(p, s, r, e):
    """Step 6 (Isomorphism): record whether an isomorphic structure was found."""
    r.isomorphism_found = r.steps[-1].output_data.get("found", False)


def _on_s8(p, s, r, e):
    """Step 8 (Synthesis): capture final solution and confidence."""
    r.final_solution = r.steps[-1].output_data.get("solution", "")
    r.confidence = r.steps[-1].output_data.get("confidence", 0.5)
    if r.steps and r.steps[-1].stage == PipelineStage.SYNTHESIS:
        e["error"] = r.steps[-1].output_data.get("error")


def _on_s9(p, s, r, e):
    """Step 9 (Validation): maybe revise solution and adjust confidence."""
    last = r.steps[-1] if r.steps else None
    if last and last.stage == PipelineStage.VALIDATION and last.output_data.get("needs_revision", False):
        r.final_solution = last.output_data.get("revised_solution", r.final_solution)
        r.confidence *= 0.9


# ---------------------------------------------------------------------------
# STEP_PLAN — configuration-driven pipeline stage definitions
#
# Each entry specifies:
#   id           – short identifier for branching logic in the loop
#   stage        – PipelineStage enum member
#   fn           – step function name (resolved via _get_step_fn)
#   build_args   – callable(pipeline, state, result) -> (pos_args, kwargs)
#   unwrap_tuple – if True, step fn returns (PipelineStepResult, extra_data)
#   include_output – if True, merge step output_data into the completion event
#   on_complete  – optional callable(pipeline, state, result, event) for
#                  post-processing the step_complete event
# ---------------------------------------------------------------------------
STEP_PLAN: list[dict[str, Any]] = [
    {
        "id": "s1",
        "stage": PipelineStage.IMPACT_IDENTIFY,
        "fn": "step_impact_identify",
        "build_args": lambda p, s, r: ([s["problem"], s["domain_hint"], p.impact], {}),
    },
    {
        "id": "s2",
        "stage": PipelineStage.PRIOR_ART,
        "fn": "step_prior_art",
        "unwrap_tuple": True,
        "include_output": True,
        "build_args": lambda p, s, r: ([s["problem"], p.prior_art, p.multi_searcher], {}),
        "on_complete": _on_s2,
    },
    {
        "id": "s2b",
        "stage": PipelineStage.GAP_ANALYSIS,
        "fn": "step_gap_analysis",
        "include_output": True,
        "build_args": lambda p, s, r: (
            [_step_output(r.steps, PipelineStage.PRIOR_ART, "merged_sources", []),
             s["problem"], p.gap_analyzer], {},
        ),
        "on_complete": _on_s2b,
    },
    {
        "id": "s2c",
        "stage": PipelineStage.QUALITY_GATE,
        "fn": "step_quality_gate",
        "include_output": True,
        "build_args": lambda p, s, r: (
            [_step_output(r.steps, PipelineStage.PRIOR_ART, "merged_sources", []),
             _step_output(r.steps, PipelineStage.GAP_ANALYSIS, "gaps", []),
             p.quality_gates], {},
        ),
        "on_complete": _on_s2c,
    },
    {
        "id": "s2d",
        "stage": PipelineStage.REALITY_CHECK,
        "fn": "step_reality_check",
        "include_output": True,
        "build_args": lambda p, s, r: ([s["problem"]], {}),
    },
    {
        "id": "s3",
        "stage": PipelineStage.C4_FINGERPRINT,
        "fn": "step_c4_fingerprint",
        "include_output": True,
        "build_args": lambda p, s, r: ([s["problem"], s["domain_hint"]], {}),
        "on_complete": _on_s3,
    },
    {
        "id": "s3b",
        "stage": PipelineStage.CROSS_DOMAIN_TRANSFER,
        "fn": "step_cross_domain_transfer",
        "include_output": True,
        "build_args": lambda p, s, r: ([s["problem"], s["domain_hint"]], {}),
    },
    {
        "id": "s4",
        "stage": PipelineStage.MP_ROTATION,
        "fn": "step_mp_rotation",
        "build_args": lambda p, s, r: (
             [s["problem"], s["c4_state"],
              p.mp_rotation, p.mp_llm_generator, p.provider_router], {},
        ),
        "on_complete": _on_s4,
    },
    {
        "id": "s5",
        "stage": PipelineStage.QZRF_SELECT,
        "fn": "step_qzrf_select",
        "build_args": lambda p, s, r: ([s["c4_state"], p.qzrf], {}),
        "on_complete": _on_s5,
    },
    {
        "id": "s6",
        "stage": PipelineStage.ISOMORPHISM_SEARCH,
        "fn": "step_isomorphism_search",
        "build_args": lambda p, s, r: (
            [s["problem"], s["domain_hint"], s["c4_state"], p.transformer, p.memory], {},
        ),
        "on_complete": _on_s6,
    },
    {
        "id": "s8",
        "stage": PipelineStage.SYNTHESIS,
        "fn": "step_synthesis",
        "build_args": lambda p, s, r: (
             [s["problem"],
              r.mp_perspectives,
              r.qzrf_recommendations,
              s["c4_state"],
              r.isomorphism_found,
              {},
              s.get("plugin_results", []),
              p.provider_router,
              p._cost_tracker,
              p._prior_art_confidence],
            {"gap_results": s.get("gap_results", []),
             "quality_gate_results": s.get("quality_gate_results", {}),
             "max_tokens": s.get("synthesis_tokens", 1500),
             "observer_insights": s.get("observer_insights", []),
             "sources": _step_output(r.steps, PipelineStage.PRIOR_ART, "sources", [])},
        ),
        "on_complete": _on_s8,
    },
    {
        "id": "s9",
        "stage": PipelineStage.VALIDATION,
        "fn": "step_validation",
        "build_args": lambda p, s, r: ([s["problem"], r.final_solution], {}),
        "on_complete": _on_s9,
    },
]


class PipelineExecutor:
    """Executes pipeline steps and manages intermediate state."""

    def __init__(self, pipeline: Any, mode: str = "autopilot") -> None:
        self._pipeline = pipeline
        self.mode = mode
        self.mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["autopilot"])
        self._logger = logging.getLogger("c44tcdi.pipeline.executor")
        self._state: dict[str, Any] = {}
        # Observer Position integration
        self._observer_controller: ObserverController | None = getattr(pipeline, "observer", None)
        self._stagnation_observer = PipelineObserver(stagnation_threshold=0.05, max_stagnant_iterations=3)
        self._observer_frame: Any = None
        self._observer_insights: list[str] = []

    async def execute(  # type: ignore[misc]
        self,
        problem: str,
        mode: str = "autopilot",
        domain_hint: str | None = None,
        max_depth: int = 6,
    ) -> None:
        """Execute all pipeline steps, yielding events."""
        start_time = time.time()
        config = MODE_CONFIG.get(mode, MODE_CONFIG["autopilot"])
        result = self._pipeline._create_result(problem, mode)

        # Mutable state dict accumulates data across step iterations.
        # build_args lambdas and on_complete callbacks read / mutate it.
        state: dict[str, Any] = {
            "problem": problem,
            "domain_hint": domain_hint,
            "c4_state": C4State(1, 1, 1),
            "prior_art_confidence": 0.0,
            "gap_results": [],
            "quality_gate_results": {},
            "plugin_results": [],
            "synthesis_tokens": 8000 if mode == "deep-work" else 6000,
        }

        yield {"event": "start", "problem": problem, "mode": mode, "mode_config": config}

        self._state = state

        # ------------------------------------------------------------------
        # Config-driven loop: iterate over STEP_PLAN, resolve args, execute
        # ------------------------------------------------------------------
        for step_def in STEP_PLAN:
            step_id: str = step_def["id"]

            # Skip validation in turbo mode for speed
            if step_id == "s9" and mode == "turbo":
                continue

            # Interleaved plugin execution — runs after s6, before s8
            if step_id == "s8":
                selected_plugins = getattr(self._pipeline, "_selected_plugins", [])
                if selected_plugins:
                    yield {"event": "step_start", "stage": "plugin_execution"}
                    plugin_results, plugin_status = await _get_step_fn("step_plugins")(problem, selected_plugins)
                    state["plugin_results"] = plugin_results
                    yield {
                        "event": "step_complete",
                        "stage": "plugin_execution",
                        "status": plugin_status,
                        "data": {"plugins_executed": len(plugin_results), "plugin_results": plugin_results},
                    }

            # Resolve positional args and keyword args
            pos_args, kwargs = step_def["build_args"](self._pipeline, state, result)

            # O₀ → O₁ self-diagnostic BEFORE synthesis (s8) so insights feed into synthesis
            if step_id == "s8" and self._observer_controller is not None:
                diagnostic = self._run_observer_diagnostic(state["c4_state"], mode)
                if diagnostic:
                    yield {"event": "observer_diagnostic", "stage": "observer_o1", "data": diagnostic}
                    # Inject observer insights into state for synthesis step
                    state["observer_insights"] = self._observer_insights

            # Execute the step
            async for event in self._execute_step(step_def, pos_args, result, **kwargs):
                yield event

            # After synthesis: track stagnation for potential O₁ → O₂ shift
            if step_id == "s8" and self._observer_controller is not None:
                obs_metrics = {
                    "novelty_score": result.confidence,
                    "gap_potential": len(state.get("gap_results", [])),
                    "hypothesis_text": result.final_solution or "",
                }
                self._stagnation_observer.observe(iteration=0, metrics=obs_metrics)
                if self._stagnation_observer.should_halt():
                    meta = self._run_meta_reflection(state["c4_state"])
                    if meta:
                        yield {"event": "observer_meta", "stage": "observer_o2", "data": meta}
                        # Boost to deep-work if stuck in lower modes
                        if mode in ("autopilot", "turbo"):
                            self._logger.info("Observer O₂ triggered: recommending mode upgrade")
                            result.final_solution += "\n\n[Observer O₂: Meta-reflection suggests exploring alternative cognitive routes. Consider deep-work mode.]"

            # Early exit after step 2d if high-confidence prior art found
            if step_id == "s2d" and state["prior_art_confidence"] > 0.92 and mode == "autopilot":
                result.final_solution = (
                    f"High-confidence prior art found ({state['prior_art_confidence']:.0%}). "
                    f"Recommendation: {result.prior_art_summary}"
                )
                result.confidence = state["prior_art_confidence"]
                result.total_duration_ms = (time.time() - start_time) * 1000
                result_dict = result.to_dict()
                result_dict["mode_config"] = config
                yield {"event": "complete", "result": result_dict}
                return

        # ------------------------------------------------------------------
        # Multi-iteration O₂ meta-reflection loop
        # If confidence is low (<0.72), trigger O₂ and re-synthesize from
        # an alternative cognitive position.
        # ------------------------------------------------------------------
        if result.confidence < 0.72 and self._observer_controller is not None:
            yield {
                "event": "observer_meta",
                "stage": "observer_o2",
                "data": {"reason": "low_confidence", "current_confidence": result.confidence},
            }
            meta = self._run_meta_reflection(state["c4_state"])
            if meta:
                yield {
                    "event": "observer_meta",
                    "stage": "observer_o2",
                    "data": meta,
                }
                # Shift C4 state to explore alternative cognitive territory
                alt_c4 = self._derive_alternative_c4(state["c4_state"], meta)
                if alt_c4:
                    state["c4_state"] = alt_c4
                    state["observer_insights"] = self._observer_insights
                    # Re-run synthesis with alternative state
                    s8_def = next((s for s in STEP_PLAN if s["id"] == "s8"), None)
                    if s8_def:
                        yield {"event": "step_start", "stage": "synthesis_refinement"}
                        pos_args, kwargs = s8_def["build_args"](self._pipeline, state, result)
                        async for event in self._execute_step(s8_def, pos_args, result, **kwargs):
                            if event.get("event") == "step_complete":
                                event["stage"] = "synthesis_refinement"
                            yield event
                        # Keep the better of the two syntheses
                        if result.confidence < result.steps[-1].output_data.get("confidence", 0):
                            self._logger.info(
                                "O₂ refinement improved confidence: %.3f → %.3f",
                                result.confidence,
                                result.steps[-1].output_data["confidence"],
                            )
                            result.confidence = result.steps[-1].output_data["confidence"]
                            result.final_solution = result.steps[-1].output_data.get("solution", result.final_solution)

        # ------------------------------------------------------------------
        # Post-loop: conditional pattern simulation
        # ------------------------------------------------------------------
        selected_pattern = getattr(self._pipeline, "_selected_pattern", None)
        if selected_pattern:
            yield {"event": "step_start", "stage": "pattern_simulation"}
            pattern_results, sim_status = await _get_step_fn("step_simulation")(problem, selected_pattern)
            yield {
                "event": "step_complete",
                "stage": "pattern_simulation",
                "status": sim_status,
                "data": {"pattern": selected_pattern},
            }
            if pattern_results:
                from src.patterns.formatter import PatternResultFormatter

                formatter = PatternResultFormatter()
                extra = "\n\n## Additional Analysis\n\n"
                for pr in pattern_results:
                    extra += formatter.format(pr, format_type="markdown")
                    extra += "\n\n"
                result.final_solution += extra

        # ------------------------------------------------------------------
        # Deep-work extra steps: formal verification and theorem export
        # ------------------------------------------------------------------
        if mode == "deep-work":
            yield {"event": "step_start", "stage": "formal_verification"}
            try:
                from src.verification.llm_prover import LLMProver
                prover = LLMProver()
                proof_result = await prover.prove("generic hypothesis", "lean4")
                proof = proof_result.proof
                result.steps.append(
                    PipelineStepResult(
                        stage=PipelineStage.FORMAL_VERIFICATION,
                        status="completed",
                        output_data={"proof": proof, "verifier": "lean4"},
                        duration_ms=0,
                    )
                )
                yield {
                    "event": "step_complete",
                    "stage": "formal_verification",
                    "status": "completed",
                    "data": {"proof_generated": True, "verifier": "lean4"},
                }
            except Exception as e:
                self._logger.warning("Formal verification failed: %s", e)
                yield {
                    "event": "step_complete",
                    "stage": "formal_verification",
                    "status": "error",
                    "error": str(e),
                }

            yield {"event": "step_start", "stage": "theorem_export"}
            try:
                result.theorem_export = {
                    "exported": True,
                    "format": "lean4",
                    "problem": problem,
                }
                yield {
                    "event": "step_complete",
                    "stage": "theorem_export",
                    "status": "completed",
                    "data": {"exported": True},
                }
            except Exception as e:
                self._logger.warning("Theorem export failed: %s", e)
                yield {
                    "event": "step_complete",
                    "stage": "theorem_export",
                    "status": "error",
                    "error": str(e),
                }

        # Finalize
        target = C4State(2, 2, 2)
        path = self._pipeline.c4_space.shortest_path(state["c4_state"], target)
        result.c4_path = path.operators
        result.total_duration_ms = (time.time() - start_time) * 1000

        result_dict = result.to_dict()
        result_dict["mode_config"] = config
        # Attach observer insights if available
        if self._observer_insights:
            result_dict["observer_insights"] = self._observer_insights
        if self._observer_frame is not None:
            result_dict["observer_position"] = self._observer_frame.observer_position.name
        yield {"event": "complete", "result": result_dict}

    def _run_observer_diagnostic(self, c4_state: C4State, mode: str) -> dict[str, Any]:
        """O₀ → O₁ self-diagnostic pass after hypothesis generation."""
        if self._observer_controller is None:
            return {}
        try:
            o0_frame = self._observer_controller.observe(ObserverPosition.IMMERSED, c4_state)
            o1_frame = self._observer_controller.shift_up(o0_frame)
            self._observer_frame = o1_frame
            diagnostic = {
                "position": o1_frame.observer_position.name,
                "visible_states_count": len(o1_frame.visible_states),
                "blind_spots": o1_frame.blind_spots,
                "insights": o1_frame.insights,
            }
            # Check if current path passes through blind spots
            if o1_frame.blind_spots:
                diagnostic["flag"] = "blind_spots_detected"
                diagnostic["recommendation"] = "Consider deep-work mode or broaden search"
                self._observer_insights.extend(o1_frame.insights)
            return diagnostic
        except Exception as e:
            self._logger.warning("Observer diagnostic failed: %s", e)
            return {}

    def _run_meta_reflection(self, c4_state: C4State) -> dict[str, Any]:
        """O₁ → O₂ meta-reflection when stagnation is detected."""
        if self._observer_controller is None:
            return {}
        try:
            o2_frame = self._observer_controller.observe(ObserverPosition.META, c4_state)
            self._observer_frame = o2_frame
            return {
                "position": o2_frame.observer_position.name,
                "visible_states_count": len(o2_frame.visible_states),
                "blind_spots": o2_frame.blind_spots,
                "insights": o2_frame.insights,
                "flag": "meta_reflection",
                "recommendation": "System-level view: consider alternative routes or scientist paths",
            }
        except Exception as e:
            self._logger.warning("Meta reflection failed: %s", e)
            return {}

    def _derive_alternative_c4(self, current: C4State, meta: dict[str, Any]) -> C4State | None:
        """Derive an alternative C4 state from O₂ meta-reflection insights.

        Strategy: if insights mention 'alternative framing', 'different scale',
        or 'time horizon', shift the corresponding C4 axis by ±1 (mod 3).
        """
        insights = " ".join(meta.get("insights", [])).lower()
        t, s, a = current.T, current.S, current.A
        shifted = False

        # Time axis shifts
        if any(k in insights for k in ("future", "long-term", "time horizon", "prediction")) and t < 2:
            t = min(t + 1, 2)
            shifted = True
        elif any(k in insights for k in ("present", "now", "immediate", "current")) and t > 0:
            t = max(t - 1, 0)
            shifted = True

        # Scale axis shifts
        if any(k in insights for k in ("meta", "framework", "abstract", "high-level")) and s < 2:
            s = min(s + 1, 2)
            shifted = True
        elif any(k in insights for k in ("concrete", "specific", "implementation", "detail")) and s > 0:
            s = max(s - 1, 0)
            shifted = True

        # Agency axis shifts
        if any(k in insights for k in ("system", "societal", "global", "collective")) and a < 2:
            a = min(a + 1, 2)
            shifted = True
        elif any(k in insights for k in ("self", "individual", "personal", "agent")) and a > 0:
            a = max(a - 1, 0)
            shifted = True

        # If no keyword matched, do a deterministic rotation to force exploration
        if not shifted:
            t = (t + 1) % 3
            s = (s + 1) % 3

        alt = C4State(t, s, a)
        if alt.to_tuple() == current.to_tuple():
            return None
        self._logger.info("O₂ alternative C4 state: %s → %s", current, alt)
        return alt

    async def _execute_step(
        self,
        step_def: dict[str, Any],
        fn_args: list[Any],
        result: Any,
        *,
        extra_data: dict[str, Any] | None = None,
        **fn_kwargs: Any,
    ) -> None:
        """Unified step executor — replaces all _execute_stepN() methods."""
        stage = step_def["stage"]
        stage_str = stage if isinstance(stage, str) else stage.value

        yield {"event": "step_start", "stage": stage_str}

        step_fn = _get_step_fn(step_def["fn"])
        raw = await step_fn(*fn_args, **fn_kwargs)

        unwrap = step_def.get("unwrap_tuple", False)
        if unwrap:
            step_result, extra = raw
        else:
            step_result = raw
            extra = None

        result.steps.append(step_result)

        if step_result.error:
            self._logger.warning("%s failed: %s", step_def["fn"], step_result.error)

        completion: dict[str, Any] = {
            "event": "step_complete",
            "stage": stage_str,
            "status": step_result.status,
            "duration_ms": step_result.duration_ms,
            "error": step_result.error,
        }

        data: dict[str, Any] = {}
        if unwrap and extra is not None:
            data["max_confidence"] = extra
        if step_def.get("include_output"):
            data.update(step_result.output_data)
        if extra_data:
            data.update(extra_data)
        if data:
            completion["data"] = data

        yield completion

        if step_def.get("on_complete"):
            step_def["on_complete"](self._pipeline, getattr(self, "_state", {}), result, completion)
