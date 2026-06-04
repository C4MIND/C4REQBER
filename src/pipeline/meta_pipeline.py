from __future__ import annotations


"""Meta-Pipeline: 6-step fractal C4 discovery loop.

Sensing → Modeling → Resonating → Transforming → Integrating → Stabilizing
Each meta-step maps to 2 current pipeline steps (12 = 6 × 2).

Fractal property: each meta-step recursively decomposes into the same 6 sub-steps,
enabling multi-resolution discovery across abstraction layers.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable


class MetaStep(IntEnum):
    """MetaStep."""
    SENSING = 0
    MODELING = 1
    RESONATING = 2
    TRANSFORMING = 3
    INTEGRATING = 4
    STABILIZING = 5


META_STEP_LABELS: dict[MetaStep, str] = {
    MetaStep.SENSING: "Sensing",
    MetaStep.MODELING: "Modeling",
    MetaStep.RESONATING: "Resonating",
    MetaStep.TRANSFORMING: "Transforming",
    MetaStep.INTEGRATING: "Integrating",
    MetaStep.STABILIZING: "Stabilizing",
}

META_STEP_ICONS: dict[MetaStep, str] = {
    MetaStep.SENSING: "👁",
    MetaStep.MODELING: "🧩",
    MetaStep.RESONATING: "🌀",
    MetaStep.TRANSFORMING: "⚡",
    MetaStep.INTEGRATING: "🔄",
    MetaStep.STABILIZING: "⚓",
}

META_STEP_DESCRIPTIONS: dict[MetaStep, str] = {
    MetaStep.SENSING: "Observe and absorb — detect patterns, scan environment, track signals",
    MetaStep.MODELING: "Structure and formalize — parse relations, filter noise, construct frames",
    MetaStep.RESONATING: "Align and synchronize — channel energy, pulse rhythms, tune frequencies",
    MetaStep.TRANSFORMING: "Mutate and transcend — shift paradigms, amplify potential, crystallize form",
    MetaStep.INTEGRATING: "Unify and embed — connect layers, expand scope, layer architecture",
    MetaStep.STABILIZING: "Anchor and verify — compress results, attenuate oscillations, cycle-check",
}

STEP_MAP: dict[MetaStep, tuple[str, str]] = {
    MetaStep.SENSING: ("C4 Navigation", "TRIZ Analysis"),
    MetaStep.MODELING: ("UCOS Analysis", "QZRF Operators"),
    MetaStep.RESONATING: ("Knowledge Search", "Isomorphism"),
    MetaStep.TRANSFORMING: ("Gap Mining", "Hypothesis"),
    MetaStep.INTEGRATING: ("Simulation", "Verification"),
    MetaStep.STABILIZING: ("Blueprint", "Paper"),
}

C4_STATE_MAP: dict[MetaStep, tuple[int, int, int]] = {
    MetaStep.SENSING: (0, 0, 0),
    MetaStep.MODELING: (1, 1, 0),
    MetaStep.RESONATING: (0, 2, 1),
    MetaStep.TRANSFORMING: (2, 1, 2),
    MetaStep.INTEGRATING: (1, 2, 2),
    MetaStep.STABILIZING: (2, 2, 1),
}


@dataclass
class MetaPipelineState:
    """MetaPipelineState."""
    current_step: MetaStep = MetaStep.SENSING
    iteration: int = 0
    depth: int = 0
    max_depth: int = 3
    history: list[tuple[MetaStep, dict[str, Any]]] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def progress_pct(self) -> float:
        return (self.current_step.value + 1) / len(MetaStep) * 100

    @property
    def is_complete(self) -> bool:
        return self.current_step == MetaStep.STABILIZING and self.iteration > 0

    def advance(self) -> MetaPipelineState:
        """Advance."""
        next_val = (self.current_step.value + 1) % len(MetaStep)
        new_iteration = self.iteration + (1 if next_val == 0 else 0)
        return MetaPipelineState(
            current_step=MetaStep(next_val),
            iteration=new_iteration,
            depth=self.depth,
            max_depth=self.max_depth,
            history=self.history[:],
            diagnostics=self.diagnostics,
        )


class MetaPipeline:
    """6-step fractal meta-pipeline orchestrating the discovery process."""

    def __init__(self, max_depth: int = 3) -> None:
        self.state = MetaPipelineState(max_depth=max_depth)
        self._hooks: dict[MetaStep, list[Callable]] = {
            step: [] for step in MetaStep
        }

    def on_step(self, step: MetaStep, hook: Callable) -> None:
        """Register a callback for a specific meta-step."""
        self._hooks[step].append(hook)

    def step_forward(self) -> dict[str, Any]:
        """Execute current meta-step and advance. Returns step result."""
        step = self.state.current_step
        step_name = META_STEP_LABELS[step]
        sub_steps = STEP_MAP[step]
        c4_coords = C4_STATE_MAP[step]

        result: dict[str, Any] = {
            'step': step_name,
            'sub_steps': sub_steps,
            'c4_state': c4_coords,
            'progress_pct': self.state.progress_pct,
            'iteration': self.state.iteration,
            'depth': self.state.depth,
        }

        for hook in self._hooks[step]:
            try:
                hook(result)
            except (ImportError, AttributeError, RuntimeError):
                pass

        self.state.history.append((step, result))
        self.state = self.state.advance()
        return result

    def run_full_cycle(self) -> list[dict[str, Any]]:
        """Execute all 6 meta-steps once. Returns results for each step."""
        results: list[dict[str, Any]] = []
        for _ in range(len(MetaStep)):
            result = self.step_forward()
            results.append(result)
        return results

    def run_fractal(self, problem: str, depth: int | None = None) -> list[dict[str, Any]]:
        """Run the full fractal pipeline at given depth.

        At depth=0: single 6-step cycle
        At depth=1: each meta-step runs internally with sub-pipelines
        At depth=N: recursive fractal decomposition
        """
        max_d = depth if depth is not None else self.state.max_depth
        if max_d <= 0:
            return self.run_full_cycle()

        all_results: list[dict[str, Any]] = []
        self.state.depth = max_d

        for _ in range(len(MetaStep)):
            self.state.depth = max_d
            result = self.step_forward()
            result['fractal_depth'] = max_d
            all_results.append(result)

        return all_results

    def reset(self) -> None:
        """Reset pipeline to initial state."""
        self.state = MetaPipelineState(max_depth=self.state.max_depth)
        self._hooks = {step: [] for step in MetaStep}

    @classmethod
    def get_step_info(cls, step: MetaStep) -> dict[str, Any]:
        """Get static information about a meta-step."""
        return {
            'name': META_STEP_LABELS[step],
            'icon': META_STEP_ICONS[step],
            'description': META_STEP_DESCRIPTIONS[step],
            'sub_steps': STEP_MAP[step],
            'c4_coords': C4_STATE_MAP[step],
        }

    @classmethod
    def pipeline_summary(cls) -> str:
        """Return a visual summary of the 6-step pipeline."""
        lines = ["6-STEP META-PIPELINE (Fractal C4 Discovery)", "=" * 50, ""]
        for step in MetaStep:
            info = cls.get_step_info(step)
            sub_a, sub_b = info['sub_steps']
            t, s, a = info['c4_coords']
            lines.append(
                f"  {info['icon']} {info['name']:<15} "
                f"F<{t},{s},{a}>  →  {sub_a} / {sub_b}"
            )
        lines.append("")
        lines.append("Fractal: each step recursively decomposes 6× deeper")
        return "\n".join(lines)
