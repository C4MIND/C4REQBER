"""Falsification Engine — Popper + Lakatos + Kuhn"""

from .lakatos import ProgrammeEvaluation, ResearchProgramme, evaluate_programme
from .popper import FalsificationResult, FalsificationTest, run_falsification
from .router import router as falsification_router


__all__ = [
    "FalsificationTest",
    "run_falsification",
    "FalsificationResult",
    "ResearchProgramme",
    "evaluate_programme",
    "ProgrammeEvaluation",
    "falsification_router",
]
