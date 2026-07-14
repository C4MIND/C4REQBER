"""Discovery module — L5 Discovery Methodology for c4-cdi-turbo v7.

Includes merged litintel modules (already_shifted, contradiction, paradigm_shift, temporal_kg).
"""
from __future__ import annotations

from src.discovery.abduction import (
    AbductionEngine,
    AbductionResult,
    Observation,
    ibe_score,
    rank_hypotheses,
    retroduction,
    select_best_explanation,
)
from src.discovery.abduction import (
    Hypothesis as AbductionHypothesis,
)
from src.discovery.already_shifted import AlreadyShiftedDetector
from src.discovery.contradiction import (
    CitationSentimentAnalyzer,
    Claim,
    ClaimExtractor,
    ContradictionDetector,
    ContradictionResult,
)
from src.discovery.falsification import (
    FalsificationEngine,
    FalsificationReport,
    TestResult,
    demarcation,
    evaluate_hypothesis,
    is_falsifiable,
    modus_tollens,
    severity_score,
)
from src.discovery.falsification import (
    Hypothesis as FalsificationHypothesis,
)
from src.discovery.paradigm_shift import (
    AnomalyDetector,
    AnomalyResult,
    CrisisIndicator,
    CrisisSignal,
    ParadigmShiftDetector,
    ParadigmShiftWarning,
    ScientificClaim,
    TemporalClaimAnalyzer,
)
from src.discovery.strong_inference import (
    Experiment,
    InferenceResult,
    StrongInferenceEngine,
    bayesian_update,
    design_crucial_experiment,
    eliminate_falsified,
    generate_competing_hypotheses,
    recycle_hypotheses,
)
from src.discovery.strong_inference import (
    Hypothesis as StrongInferenceHypothesis,
)
from src.discovery.temporal_kg import (
    ConsensusEvolution,
    ConsensusQuery,
    TemporalKnowledgeGraph,
    TimeStampedClaim,
)


__all__ = [
    # Abduction
    "AbductionEngine",
    "AbductionResult",
    "AbductionHypothesis",
    "Observation",
    "ibe_score",
    "rank_hypotheses",
    "retroduction",
    "select_best_explanation",
    # Strong Inference
    "StrongInferenceEngine",
    "InferenceResult",
    "StrongInferenceHypothesis",
    "Experiment",
    "bayesian_update",
    "design_crucial_experiment",
    "eliminate_falsified",
    "generate_competing_hypotheses",
    "recycle_hypotheses",
    # Falsification
    "FalsificationEngine",
    "FalsificationReport",
    "FalsificationHypothesis",
    "TestResult",
    "demarcation",
    "evaluate_hypothesis",
    "is_falsifiable",
    "modus_tollens",
    "severity_score",
    # litintel → discovery (merged)
    "AlreadyShiftedDetector",
    "Claim",
    "ClaimExtractor",
    "CitationSentimentAnalyzer",
    "ContradictionDetector",
    "ContradictionResult",
    "AnomalyDetector",
    "AnomalyResult",
    "CrisisIndicator",
    "CrisisSignal",
    "ParadigmShiftDetector",
    "ParadigmShiftWarning",
    "ScientificClaim",
    "TemporalClaimAnalyzer",
    "ConsensusEvolution",
    "ConsensusQuery",
    "TemporalKnowledgeGraph",
    "TimeStampedClaim",
]
