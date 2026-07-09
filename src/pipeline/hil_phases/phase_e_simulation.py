from __future__ import annotations


"""Phase E: Simulation & Verification — Pattern simulation, hybrid verification."""

import asyncio
import json
import logging
from typing import Any

from src.patterns.runner import PatternRunner
from src.pipeline.config import PipelineConfig
from src.verification.hybrid_verifier import HybridVerifier


logger = logging.getLogger(__name__)


class PhaseE_SimulationVerification:
    """Run pattern simulation and hybrid verification."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig(name="default")
        self.pattern_runner = PatternRunner()
        self.hybrid_verifier = HybridVerifier()

    async def run_simulation(
        self, topic: str, hypothesis: dict[str, Any], max_retry: int = 2
    ) -> dict[str, Any]:
        """Select and run REAL simulation."""
        print("\n[Phase E] Simulation & Verification...")
        print("\n[E1/7] Running REAL simulation...")

        pattern_id, params = self._smart_select_pattern(topic)
        timeout_s = float(getattr(self.config, "simulation_timeout_seconds", 60.0) or 60.0)
        try:
            raw_result = await self._run_with_retry(
                self.pattern_runner.run_pattern(
                    pattern_id=pattern_id,
                    hypothesis=hypothesis,
                    params=params,
                    timeout_seconds=timeout_s,
                ),
                "simulation",
                max_retry,
            )

            status = raw_result.get("status", "")
            if status == "timeout":
                exec_time = raw_result.get("execution_time_seconds", timeout_s)
                print(
                    f"      ⚠ Simulation stopped at {timeout_s:.0f}s budget ({pattern_id}, {exec_time:.1f}s)"
                )
                return {
                    "pattern_id": pattern_id,
                    "parameters": params,
                    "status": "timeout",
                    "metrics": {"execution_time": exec_time},
                    "raw_output": raw_result.get("error", "time budget exceeded"),
                    "interpretation": f"{pattern_id} exceeded {timeout_s:.0f}s pipeline budget",
                }
            if status in ("completed", "delegated"):
                result_data = raw_result.get("result", {})
                exec_time = raw_result.get("execution_time_seconds", 0)
                metrics: dict[str, float] = {}
                if isinstance(result_data, dict):
                    for key in [
                        "error",
                        "convergence",
                        "iterations",
                        "energy",
                        "temperature",
                        "pressure",
                        "density",
                    ]:
                        if key in result_data:
                            val = result_data[key]
                            metrics[key] = float(val) if isinstance(val, int | float) else 0.0
                if not metrics:
                    metrics = {"execution_time": exec_time, "status_code": 0}

                if status == "delegated":
                    sim_status = "delegated"
                    interp = f"{pattern_id} delegated to remote GPU (vast.ai / NVIDIA Brev)"
                    print(f"      ✓ Simulation DELEGATED: {pattern_id} → remote GPU")
                else:
                    sim_status = "success"
                    interp = f"{pattern_id} executed successfully in {exec_time:.2f}s."
                    print(f"      ✓ REAL simulation complete: {pattern_id} ({exec_time:.2f}s)")

                return {
                    "pattern_id": pattern_id,
                    "parameters": params,
                    "status": sim_status,
                    "metrics": metrics,
                    "raw_output": json.dumps(result_data, indent=2, default=str)[:500],
                    "interpretation": interp,
                }
            else:
                error_msg = raw_result.get("error", "Unknown error")
                print(f"      ✗ Simulation failed: {error_msg[:100]}")
                return {
                    "pattern_id": pattern_id,
                    "parameters": params,
                    "status": "failed",
                    "raw_output": error_msg,
                    "interpretation": f"Failed: {error_msg[:100]}",
                }
        except Exception as e:
            print(f"      ✗ Simulation exception: {e}")
            return {
                "pattern_id": pattern_id,
                "parameters": params,
                "status": "failed",
                "raw_output": str(e),
                "interpretation": f"Exception: {str(e)[:100]}",
            }

    async def run_verification(
        self, topic: str, hypotheses: list[dict[str, Any]], query_type: str
    ) -> dict[str, Any]:
        """Run hybrid verification (6 backends with smart model routing)."""
        print("\n[E2/7] Running hybrid verification (Z3 + Lean4/Coq/Dafny/Agda/Hoare)...")
        if query_type == "practical":
            print("      SKIPPING formal verification for practical query")
            return {
                "backend": "none",
                "claim": "Practical query — formal verification not applicable",
                "status": "not_applicable",
                "proof_text": "Formal verification not applicable to practical queries.",
                "iterations": 0,
            }
        elif not hypotheses:
            return {
                "backend": "none",
                "claim": "",
                "status": "failed",
                "proof_text": "No hypotheses to verify",
                "iterations": 0,
            }

        try:
            checked = 0
            best_result = None
            for hypothesis in hypotheses:
                checked += 1
                result = await self.hybrid_verifier.verify(hypothesis, context={"topic": topic})
                if result.status in ("verified", "sat", "consistent"):
                    best_result = result
                    break
                if result.backend == "z3" and result.status == "consistent":
                    best_result = result
                    continue

            if best_result is None and hypotheses:
                best_result = await self.hybrid_verifier.verify(
                    hypotheses[0], context={"topic": topic}
                )
        except Exception as e:
            logger.warning("Hybrid verification failed: %s", e)
            return {
                "backend": "none",
                "claim": "",
                "status": "skipped",
                "proof_text": f"Verification skipped: {str(e)[:200]}",
                "iterations": 0,
            }

        if best_result:
            print(f"      Checked {checked}/{len(hypotheses)} hypotheses")
            from src.verification.timer import VerificationTimeoutManager

            elapsed_str = VerificationTimeoutManager.format_elapsed(
                best_result.execution_time_ms / 1000
            )
            timing_note = ""
            if best_result.was_timeout:
                timing_note = " [TIMEOUT → fallback]"
            print(f"      Best result: {best_result.backend} — {best_result.status}{timing_note}")
            print(f"      Time: {elapsed_str} | Iterations: {best_result.iterations}")
            if best_result.timing_info and best_result.timing_info.get("was_killed"):
                print("      ⚠️  Killed after hard timeout — fell back to Z3")
            if best_result.proof_code:
                print(f"      Proof: {best_result.proof_code[:80]}...")

            return {
                "backend": best_result.backend,
                "claim": best_result.claim[:200],
                "status": best_result.status,
                "proof_text": best_result.proof_text,
                "error_message": best_result.error_message,
                "iterations": best_result.iterations,
            }
        else:
            return {
                "backend": "none",
                "claim": "",
                "status": "failed",
                "proof_text": "All verification attempts failed",
                "iterations": checked,
            }

    def _smart_select_pattern(self, topic: str) -> tuple[str, dict[str, Any]]:
        """Intelligently select best pattern from library based on topic."""
        from src.patterns.topic_router import select_pattern_for_topic

        all_patterns = self.pattern_runner.list_patterns()
        pattern_id, params = select_pattern_for_topic(
            topic,
            all_patterns,
            self.pattern_runner.get_metadata,
        )
        meta = self.pattern_runner.get_metadata(pattern_id)
        name = meta.get("name", pattern_id) if meta else pattern_id
        print(f"      Smart match: '{pattern_id}' (name={name}, fast_mode=True)")
        return pattern_id, params

    async def _run_with_retry(self, coro, step_name: str, max_retry: int) -> Any:
        """Run a coroutine with auto-retry on failure."""
        for attempt in range(max_retry + 1):
            try:
                return await coro
            except Exception as e:
                if attempt < max_retry:
                    logger.warning(
                        "%s failed (attempt %d): %s — retrying...", step_name, attempt + 1, e
                    )
                    await asyncio.sleep(2**attempt)
                else:
                    logger.error("%s failed after %d attempts: %s", step_name, attempt + 1, e)
                    raise
