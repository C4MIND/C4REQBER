"""
C4REQBER API: v7 Shared Request/Response Schemas
All v7 routers use Pydantic models for request validation and response serialization.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ═══════════════════════════════════════════════════════════════════════════
# Shared / Generic
# ═══════════════════════════════════════════════════════════════════════════


class ErrorDetail(BaseModel):
    """ErrorDetail."""
    detail: str


# ═══════════════════════════════════════════════════════════════════════════
# C4
# ═══════════════════════════════════════════════════════════════════════════


class C4StateItem(BaseModel):
    """C4StateItem."""
    coords: list[int]
    label: str
    time: str
    scale: str
    agency: str


class C4Transition(BaseModel):
    """C4Transition."""
    operator: str
    from_state: str
    to_state: str
    description: str


class C4NavigateResponse(BaseModel):
    """C4NavigateResponse."""
    from_state: str
    to_state: str
    path_length: int
    operators: list[str]
    transitions: list[C4Transition]


class C4FingerprintResponse(BaseModel):
    """C4FingerprintResponse."""
    problem: str
    c4_state: str
    coords: tuple[int, int, int]
    time: str
    scale: str
    agency: str


class C4OperatorInfo(BaseModel):
    """C4OperatorInfo."""
    symbol: str
    name: str
    description: str
    period: int
    direction: str


class C4OperatorsResponse(BaseModel):
    """C4OperatorsResponse."""
    operators: list[C4OperatorInfo]
    theorem_9: str
    theorem_11: str


# ═══════════════════════════════════════════════════════════════════════════
# Metaprograms
# ═══════════════════════════════════════════════════════════════════════════


class MPProgramItem(BaseModel):
    """MPProgramItem."""
    code: str
    name: str
    category: str
    c4: str
    description: str
    keywords: list[str]
    opposite: str | None


class MPScoreItem(BaseModel):
    """MPScoreItem."""
    code: str
    name: str
    raw_score: float
    normalized_score: float
    keyword_hits: int
    matched_keywords: list[str]


class MPProgramsResponse(BaseModel):
    """MPProgramsResponse."""
    programs: list[MPProgramItem]
    counts: dict[str, int]
    total: int


class MPProfileResponse(BaseModel):
    """MPProfileResponse."""
    dominant_temporal: str | None
    dominant_scale: str | None
    dominant_agency: str | None
    c4_centroid: str | None
    category_distribution: dict[str, float]
    top_scores: list[MPScoreItem]


class MPShiftResponse(BaseModel):
    """MPShiftResponse."""
    suggestions: list[dict[str, Any]]
    dominant_count: int


# ═══════════════════════════════════════════════════════════════════════════
# QZRF
# ═══════════════════════════════════════════════════════════════════════════


class QZRFOperatorItem(BaseModel):
    """QZRFOperatorItem."""
    id: str
    name: str
    name_ru: str
    phase: str
    description: str
    c4_target: tuple[int, int, int]
    applicable_states: list[tuple[int, int, int]]


class QZRFOperatorsResponse(BaseModel):
    """QZRFOperatorsResponse."""
    operators: list[QZRFOperatorItem]
    phases: list[str]
    total: int


class QZRFOperatorSummary(BaseModel):
    """QZRFOperatorSummary."""
    id: str
    name: str
    phase: str


class QZRFTransformResponse(BaseModel):
    """QZRFTransformResponse."""
    from_state: str
    from_coords: tuple[int, int, int]
    operator: QZRFOperatorSummary
    applicable: bool
    target_state: tuple[int, int, int]
    target_label: str


class QZRFFingerprintResponse(BaseModel):
    """QZRFFingerprintResponse."""
    problem: str
    c4_state: str
    coords: tuple[int, int, int]
    applicable_operators: list[str]


class QZRFRouteResponse(BaseModel):
    """QZRFRouteResponse."""
    from_state: str
    to_state: str
    qzrf_sequence: list[str]
    c4_path_length: int
    c4_operators: list[str]


# ═══════════════════════════════════════════════════════════════════════════
# Discovery
# ═══════════════════════════════════════════════════════════════════════════


class DiscoveryAbduceResponse(BaseModel):
    """DiscoveryAbduceResponse."""
    request_id: str
    domain: str
    observations: list[str]
    hypotheses: list[dict[str, Any]]
    best_explanation: dict[str, Any] | None
    explanation: str
    metadata: dict[str, Any]


class DiscoveryInferResponse(BaseModel):
    """DiscoveryInferResponse."""
    request_id: str
    problem: str
    cycles: int
    hypotheses: list[dict[str, Any]]
    experiments: list[dict[str, Any]]
    surviving_hypotheses: list[dict[str, Any]]
    eliminated_hypotheses: list[dict[str, Any]]
    explanation: str
    metadata: dict[str, Any]


class DiscoveryFalsifyResponse(BaseModel):
    """DiscoveryFalsifyResponse."""
    hypothesis_id: str
    hypothesis_statement: str
    is_falsifiable: bool
    is_falsified: bool
    tests: list[dict[str, Any]]
    overall_severity: float
    corroboration: float
    demarcation: str
    modus_tollens_valid: bool
    explanation: str
    metadata: dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════
# Causal
# ═══════════════════════════════════════════════════════════════════════════


class CausalSCMResponse(BaseModel):
    """CausalSCMResponse."""
    nodes: list[str]
    endogenous: list[str]
    exogenous: list[str]
    edges: list[list[str]]
    topological_order: list[str]


class CausalDoResponse(BaseModel):
    """CausalDoResponse."""
    treatment: str
    outcome: str
    identifiable: bool
    reason: str
    adjustment_formula: str | None
    adjustment_set: list[str]


class CausalIntervention(BaseModel):
    """CausalIntervention."""
    target: str
    value: float


class CausalCounterfactualResponse(BaseModel):
    """CausalCounterfactualResponse."""
    evidence: dict[str, float]
    intervention: CausalIntervention
    target_variable: str
    factual_value: float | None
    counterfactual_value: float | None
    effect: float | None
    exogenous_values: dict[str, float]


# ═══════════════════════════════════════════════════════════════════════════
# LitIntel
# ═══════════════════════════════════════════════════════════════════════════


class LitIntelParadigmResponse(BaseModel):
    """LitIntelParadigmResponse."""
    domain: str
    probability: float
    confidence: float
    estimated_timeframe: str
    contributing_factors: list[str]
    breakthrough_claims: list[str]


class LitIntelContradictionItem(BaseModel):
    """LitIntelContradictionItem."""
    claim_a: str
    claim_b: str
    score: float
    similarity: float
    explanation: str


class LitIntelContradictResponse(BaseModel):
    """LitIntelContradictResponse."""
    claims_extracted: int
    contradictions_found: int
    contradictions: list[LitIntelContradictionItem]


class LitIntelTemporalResponse(BaseModel):
    """LitIntelTemporalResponse."""
    topic: str
    stability: float | None
    trend: str | None
    points: list[dict[str, Any]]
    boundaries: list[dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════
# TRIZ
# ═══════════════════════════════════════════════════════════════════════════


class TRIZPrincipleItem(BaseModel):
    """TRIZPrincipleItem."""
    number: int
    name: str
    description: str
    examples: list[str]
    sub_principles_count: int


class TRIZPrinciplesResponse(BaseModel):
    """TRIZPrinciplesResponse."""
    principles: list[TRIZPrincipleItem]
    total: int


class TRIZMatrixCell(BaseModel):
    """TRIZMatrixCell."""
    improving: int
    improving_name: str
    worsening: int
    worsening_name: str
    principles: list[int]


class TRIZMatrixResponse(BaseModel):
    """TRIZMatrixResponse."""
    parameters: dict[int, str]
    stats: dict[str, int]
    cells: list[TRIZMatrixCell]


class TRIZPrincipleDetail(BaseModel):
    """TRIZPrincipleDetail."""
    number: int
    name: str
    description: str
    explanation: str
    relevance_score: float
    examples: list[str]


class TRIZSolveResponse(BaseModel):
    """TRIZSolveResponse."""
    improving_param_id: int
    improving_param_name: str
    worsening_param_id: int
    worsening_param_name: str
    principles: list[TRIZPrincipleDetail]


class TRIZSolveTextResponse(BaseModel):
    """TRIZSolveTextResponse."""
    status: str
    message: str | None = None
    improving_param_id: int | None = None
    improving_param_name: str | None = None
    worsening_param_id: int | None = None
    worsening_param_name: str | None = None
    principles: list[TRIZPrincipleDetail] | None = None


# ═══════════════════════════════════════════════════════════════════════════
# Bayesian
# ═══════════════════════════════════════════════════════════════════════════


class BayesianMCMCResponse(BaseModel):
    """BayesianMCMCResponse."""
    n_chains: int
    n_samples: int
    accept_rate: float
    sample_mean: float
    sample_std: float
    samples_shape: list[int]
    samples_preview: list[float] | list[list[float]]


class BayesianBMAResponse(BaseModel):
    """BayesianBMAResponse."""
    model_probs: dict[str, float]
    model_evidences: dict[str, float]
    best_model: str


class BayesianBICResponse(BaseModel):
    """BayesianBICResponse."""
    best_model: str
    bic_scores: dict[str, float]


# ═══════════════════════════════════════════════════════════════════════════
# System Dynamics
# ═══════════════════════════════════════════════════════════════════════════


class SDStockItem(BaseModel):
    """SDStockItem."""
    name: str
    initial: float
    unit: str


class SDFlowItem(BaseModel):
    """SDFlowItem."""
    name: str
    source: str | None
    sink: str | None
    unit: str


class SDAuxItem(BaseModel):
    """SDAuxItem."""
    name: str
    unit: str


class SDModelResponse(BaseModel):
    """SDModelResponse."""
    name: str
    stocks: list[SDStockItem]
    flows: list[SDFlowItem]
    auxiliaries: list[SDAuxItem]
    stock_order: list[str]


class SDSimulateResponse(BaseModel):
    """SDSimulateResponse."""
    name: str
    t_span: tuple[float, float]
    n_steps: int
    time: list[float]
    stocks: dict[str, list[float]]


# ═══════════════════════════════════════════════════════════════════════════
# Simulations
# ═══════════════════════════════════════════════════════════════════════════


class SimulationPatternItem(BaseModel):
    """SimulationPatternItem."""
    id: str
    name: str
    domain: list[str] | str
    description: str
    has_run: bool


class SimulationsListResponse(BaseModel):
    """SimulationsListResponse."""
    patterns: list[SimulationPatternItem]
    total: int
    errors: list[str] | dict[str, Any]


class SimulationRunResponse(BaseModel):
    """SimulationRunResponse."""
    pattern_id: str
    status: str
    result: dict[str, Any] | None = None
    message: str | None = None
