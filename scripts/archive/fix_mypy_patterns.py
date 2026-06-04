#!/usr/bin/env python3
"""Comprehensive mypy error fixer for src/patterns"""
import re
from pathlib import Path


PATTERNS_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI/src/patterns")
CHANGED = set()


def apply_fixes(content: str, filepath: Path) -> str:
    rel = str(filepath.relative_to(PATTERNS_DIR))

    # --- FIX 1: can_simulate missing @classmethod ---
    # "def can_simulate(self, hypothesis: Hypothesis) -> bool:" → @classmethod variant
    old = "    def can_simulate(self, hypothesis: Hypothesis) -> bool:"
    new = "    @classmethod\n    def can_simulate(cls, hypothesis: Hypothesis) -> bool:"
    if old in content:
        content = content.replace(old, new)
        CHANGED.add(rel)

    # --- FIX 2: run signature with extra required config param ---
    # Pattern: "async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:"
    # or Dict[str, Any] or Dict[str,Any]
    for pat_old, pat_new in [
        (
            "async def run(\n        self, hypothesis: Hypothesis, config: Dict[str, Any]\n    ) -> SimulationResult:",
            "async def run(\n        self, hypothesis: Hypothesis | None = None, config: Dict[str, Any] | None = None\n    ) -> SimulationResult:",
        ),
        (
            "async def run(\n        self, hypothesis: Hypothesis, config: dict[str, Any]\n    ) -> SimulationResult:",
            "async def run(\n        self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None\n    ) -> SimulationResult:",
        ),
        (
            "async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> SimulationResult:",
            "async def run(self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None) -> SimulationResult:",
        ),
        (
            "async def run(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> SimulationResult:",
            "async def run(self, hypothesis: Hypothesis | None = None, config: Dict[str, Any] | None = None) -> SimulationResult:",
        ),
        (
            "async def run(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Coroutine[Any, Any, SimulationResult]:",
            "async def run(self, hypothesis: Hypothesis | None = None, config: Dict[str, Any] | None = None) -> Coroutine[Any, Any, SimulationResult]:",
        ),
        (
            "async def run(self, hypothesis: Hypothesis, config: dict[str, Any]) -> Coroutine[Any, Any, SimulationResult]:",
            "async def run(self, hypothesis: Hypothesis | None = None, config: dict[str, Any] | None = None) -> Coroutine[Any, Any, SimulationResult]:",
        ),
    ]:
        if pat_old in content:
            content = content.replace(pat_old, pat_new)
            CHANGED.add(rel)

    # --- FIX 3: estimate_resources with extra hypothesis param ---
    # The parent now supports optional hypothesis (will be fixed in core.py)
    for pat_old, pat_new in [
        (
            "def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:",
            "def estimate_resources(self, hypothesis: Hypothesis | None = None) -> Dict[str, Any]:",
        ),
        (
            "def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:",
            "def estimate_resources(self, hypothesis: Hypothesis | None = None) -> dict[str, Any]:",
        ),
    ]:
        if pat_old in content:
            content = content.replace(pat_old, pat_new)
            CHANGED.add(rel)

    # --- FIX 4: Runtime attributes set by @simulation_pattern decorator ---
    # Replace cls.name, cls.category, cls.description with getattr
    for attr in ["name", "category", "description", "id"]:
        for prefix in ["cls.", "self.__class__."]:
            old_pat = f"{prefix}{attr}"
            new_pat = f"getattr({prefix[:-1]}, '{attr}', '')"
            if old_pat in content:
                content = content.replace(old_pat, new_pat)
                CHANGED.add(rel)

    # --- FIX 5: Implicit Optional - int/float/str/bool with None default ---
    for typ in ["int", "float", "str", "bool"]:
        # Function parameters: self, var: int = None
        content = re.sub(
            rf'(\w+)\s*:\s*{typ}\s*=\s*None',
            rf'\1: {typ} | None = None',
            content,
        )

    # dict[str, Any] = None
    content = re.sub(
        r'(\w+)\s*:\s*dict\[str,\s*Any\]\s*=\s*None',
        r'\1: dict[str, Any] | None = None',
        content
    )
    # list[str] = None, list[float] = None, list[int] = None
    for lt in ["str", "float", "int", "dict"]:
        content = re.sub(
            rf'(\w+)\s*:\s*list\[{lt}\]\s*=\s*None',
            rf'\1: list[{lt}] | None = None',
            content,
        )

    # --- FIX 6: np.ndarray = None → np.ndarray | None = None ---
    content = re.sub(
        r'(\w+)\s*:\s*np\.ndarray\s*=\s*None',
        r'\1: np.ndarray | None = None',
        content,
    )
    # ndarray[Any, Any] = None
    content = re.sub(
        r'(\w+)\s*:\s*ndarray\[Any,\s*Any\]\s*=\s*None',
        r'\1: ndarray[Any, Any] | None = None',
        content,
    )
    # ndarray[Any, dtype[...]] = None
    content = re.sub(
        r'(\w+)\s*:\s*ndarray\[Any,\s*dtype\[floating\[Any\]\],\s*Any\]\s*=\s*None',
        r'\1: ndarray[Any, dtype[floating[Any]], Any] | None = None',
        content,
    )

    # --- FIX 7: missing -> None on __init__ (only in class body) ---
    # Only fix __init__ that doesn't already have -> None
    content = re.sub(
        r'def __init__\(self,([^)]*)\):(?![^\n]*->\s*None)',
        r'def __init__(self,\1) -> None:',
        content,
    )

    # --- FIX 8: unreachable code (statement after return) —
    # These are complex, skip automated fix

    # --- FIX 9: floating[Any] assignment to float annot →
    # Use float() or .item() — too complex for regex, skip

    # --- FIX 10: ndarray | None index access —
    # Need None checks, too complex for regex, skip

    # --- FIX 11: model: MAPKModel = GPCRModel(…) type mismatch —
    # Skip, manual fix needed

    return content


def main():
    py_files = sorted(PATTERNS_DIR.rglob("*.py"))
    for fp in py_files:
        try:
            original = fp.read_text()
            fixed = apply_fixes(original, fp)
            if fixed != original:
                fp.write_text(fixed)
                print(f"  FIXED: {fp.relative_to(PATTERNS_DIR)}")
        except Exception as e:
            print(f"  ERROR: {fp.relative_to(PATTERNS_DIR)}: {e}")

    print(f"\nChanged {len(CHANGED)} files")
    for c in sorted(CHANGED):
        print(f"  - {c}")


if __name__ == "__main__":
    main()
