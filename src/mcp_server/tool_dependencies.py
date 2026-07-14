from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

try:
    from src.bayesian.router import run_bma, run_mcmc
    from src.c4.engine import C4Space, C4State
    from src.causal.do_calculus import DoCalculus
    from src.export.manager import ExportManager
    from src.knowledge.orchestrator import MultiSourceSearcher
    from src.simulations.newton_bridge import NewtonBridge
    from src.triz.principles import search_principles as triz_search
    from src.verification.agda_bridge import AgdaBridge
    from src.verification.calibrator import VerificationCalibrator, VerificationContext
    from src.verification.coq_client import CoqClient
    from src.verification.dafny_client import DafnyClient
    from src.verification.lean4_client import Lean4Client

    HAS_TOOLS = True
except ImportError as exc:
    HAS_TOOLS = False
    logger.warning("Some tool dependencies not found: %s", exc)

__all__ = [
    "AgdaBridge",
    "C4Space",
    "C4State",
    "CoqClient",
    "DafnyClient",
    "DoCalculus",
    "ExportManager",
    "HAS_TOOLS",
    "Lean4Client",
    "MultiSourceSearcher",
    "NewtonBridge",
    "VerificationCalibrator",
    "VerificationContext",
    "run_bma",
    "run_mcmc",
    "triz_search",
]
