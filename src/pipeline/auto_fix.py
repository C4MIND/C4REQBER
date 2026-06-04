from __future__ import annotations

import importlib
import importlib.util
import logging
import re
import sys
from dataclasses import dataclass
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Sequence


logger = logging.getLogger(__name__)


@dataclass
class AutoFix:
    """AutoFix."""
    pattern: re.Pattern[str]
    replacement: str
    severity: str  # "fatal" | "warning"
    description: str


AUTO_FIX_REGISTRY: list[AutoFix] = [
    AutoFix(
        pattern=re.compile(
            r"from\s+src\.knowledge\.multi_source\s+import\s+MultiSourceSearcher"
        ),
        replacement="from src.knowledge.orchestrator import MultiSourceSearcher",
        severity="warning",
        description="MultiSourceSearcher moved to orchestrator.py; multi_source.py is a backward-compat shim",
    ),
    AutoFix(
        pattern=re.compile(
            r"from\s+cli\.display\s+import\s+LayoutManager"
        ),
        replacement="from src.cli.layout_manager import LayoutManager",
        severity="fatal",
        description="cli.display module deleted; LayoutManager lives in src.cli.layout_manager",
    ),
    AutoFix(
        pattern=re.compile(
            r"from\s+src\.agents\.pipeline\.steps\.base\s+import\s+PipelineStage"
        ),
        replacement="from src.agents.pipeline.steps.base import PipelineStage",
        severity="warning",
        description="PipelineStage.GAP_ANALYSIS missing warning — already added in Phase 0",
    ),
    AutoFix(
        pattern=re.compile(
            r"UniversalSolvePipeline\(\s*config\s*=\s*config\s*\)"
        ),
        replacement="UniversalSolvePipeline()",
        severity="fatal",
        description="UniversalSolvePipeline no longer accepts config kwarg; use provider_router instead",
    ),
    AutoFix(
        pattern=re.compile(
            r"result\s*\.\s*get\s*\(\s*['\"]confidence['\"]\s*,\s*0\s*\)"
        ),
        replacement="result.confidence",
        severity="warning",
        description="PipelineResult is a dataclass; use result.confidence instead of result.get('confidence', 0)",
    ),
    AutoFix(
        pattern=re.compile(
            r"sim\s*\.\s*__dict__\s+if\s+not\s+isinstance\s*\(\s*sim\s*,\s*dict\s*\)"
        ),
        replacement="sim",
        severity="warning",
        description="Pass dict directly instead of extracting __dict__ from non-dict objects",
    ),
]

KNOWN_BROKEN: dict[str, str | None] = {
    "src.knowledge.multi_source": "src.knowledge.orchestrator",
    "cli.display": None,
    "src.llm.fallback_multiprovider": "src.llm.fallback",
}


class SelfHealingImporter(MetaPathFinder):
    """SelfHealingImporter."""
    _fixed: set[str] = set()

    @staticmethod
    def _reconstruct_import_line(fullname: str, attrname: str | None = None) -> str:
        if attrname:
            return f"from {fullname} import {attrname}"
        return f"import {fullname}"

    @staticmethod
    def attempt_fix(import_line: str) -> str | None:
        """Attempt fix."""
        for fix in AUTO_FIX_REGISTRY:
            if fix.pattern.search(import_line):
                return fix.pattern.sub(fix.replacement, import_line)
        return None

    @classmethod
    def log_fix(cls, fix: AutoFix, original: str, fixed: str) -> None:
        """Log fix."""
        cls._fixed.add(original)
        log_func = logger.warning if fix.severity == "warning" else logger.error
        log_func(
            "SelfHealingImporter: [%s] %s\n  Original: %s\n  Fixed:    %s",
            fix.severity.upper(),
            fix.description,
            original,
            fixed,
        )

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Find spec."""
        if fullname in KNOWN_BROKEN:
            replacement = KNOWN_BROKEN[fullname]
            if replacement is None:
                logger.error(
                    "SelfHealingImporter: Module %s has been deleted. "
                    "No replacement available.",
                    fullname,
                )
                return None
            logger.warning(
                "SelfHealingImporter: Redirecting import %s -> %s",
                fullname,
                replacement,
            )
            return importlib.util.find_spec(replacement)

        if fullname == "src.llm.fallback":
            logger.warning(
                "SelfHealingImporter: Module %s not found on disk. Skipping.",
                fullname,
            )
            return None

        return None


def _register() -> None:
    if not any(isinstance(h, SelfHealingImporter) for h in sys.meta_path):
        sys.meta_path.insert(0, SelfHealingImporter())  # type: ignore[arg-type]


_register()
