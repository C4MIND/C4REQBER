"""
TURBO-CDI v8.0 - Cognitive Bias Detector
Agent 2: Cognitive Systems (Kahneman)

Detects cognitive biases in transformation requests.
Protects users from their own cognitive limitations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from cognitive.user_profile.core import UserProfile


class BiasType(Enum):
    """Types of cognitive biases we can detect"""

    OPTIMISM_BIAS = "optimism_bias"
    PLANNING_FALLACY = "planning_fallacy"
    AVAILABILITY_BIAS = "availability_bias"
    ANCHORING = "anchoring"
    CONFIRMATION_BIAS = "confirmation_bias"
    SUNK_COST = "sunk_cost"
    STATUS_QUO_BIAS = "status_quo_bias"
    DUNNING_KRUGER = "dunning_kruger"
    RECENCY_BIAS = "recency_bias"
    SURVIVORSHIP_BIAS = "survivorship_bias"


# Explanations for each bias type
BIAS_EXPLANATIONS = {
    BiasType.OPTIMISM_BIAS: "Tendency to underestimate risks and overestimate success rates, often leading to unrealistic planning.",
    BiasType.PLANNING_FALLACY: "Underestimating time and resources needed for tasks, even when past experience shows otherwise.",
    BiasType.AVAILABILITY_BIAS: "Over-relying on easily recalled information, which may not be representative.",
    BiasType.ANCHORING: "Being overly influenced by initial information when making decisions.",
    BiasType.CONFIRMATION_BIAS: "Seeking information that confirms existing beliefs while ignoring contradictory evidence.",
    BiasType.SUNK_COST: "Continuing with a course of action because of previously invested resources, despite poor prospects.",
    BiasType.STATUS_QUO_BIAS: "Preferring things to stay the same, resisting change even when change might be beneficial.",
    BiasType.DUNNING_KRUGER: "Overestimating one's abilities in areas of low competence.",
    BiasType.RECENCY_BIAS: "Giving disproportionate weight to recent events or information.",
    BiasType.SURVIVORSHIP_BIAS: "Focusing only on successful examples while ignoring failures.",
}


@dataclass
class BiasWarning:
    """A detected cognitive bias with recommendation"""

    bias_type: BiasType
    severity: str  # "low", "medium", "high", "critical"
    message: str
    recommendation: str
    confidence: float  # 0-1


class BiasDetector:
    """
    Detects cognitive biases in transformation plans.

    Based on Kahneman's research in cognitive biases.
    Provides gentle nudges to help users avoid common pitfalls.
    """

    def __init__(self, user_profile: Optional[UserProfile] = None):
        self.user_profile = user_profile
        self.bias_history: List[BiasWarning] = []

    def analyze_transformation_plan(
        self, plan: Dict[str, Any], user_context: Dict[str, Any]
    ) -> List[BiasWarning]:
        """
        Analyze a transformation plan for cognitive biases.

        Args:
            plan: Transformation plan with path, effectiveness estimates, etc.
            user_context: Context about user, research mode, etc.

        Returns:
            List of bias warnings with recommendations
        """
        warnings = []

        # Check each bias type
        warnings.extend(self._check_optimism_bias(plan))
        warnings.extend(self._check_planning_fallacy(plan))
        warnings.extend(self._check_availability_bias(plan, user_context))
        warnings.extend(self._check_confirmation_bias(plan, user_context))
        warnings.extend(self._check_recency_bias(plan, user_context))
        warnings.extend(self._check_anchoring(plan))
        warnings.extend(self._check_sunk_cost(plan, user_context))
        warnings.extend(self._check_status_quo_bias(plan))
        warnings.extend(self._check_dunning_kruger(plan))
        warnings.extend(self._check_survivorship_bias())

        # Store for learning
        self.bias_history.extend(warnings)

        # Update user profile
        if self.user_profile:
            for w in warnings:
                bias_key = w.bias_type.value
                self.user_profile.bias_tendencies[bias_key] = (
                    self.user_profile.bias_tendencies.get(bias_key, 0) + 1
                )

        return warnings

    def _check_optimism_bias(self, plan: Dict) -> List[BiasWarning]:
        """Check for unrealistic optimism"""
        warnings = []
        path = plan.get("path", [])

        # Long chains in same direction
        if len(path) > 4:
            # Check if all steps go in same general direction
            directions = self._extract_directions(path)
            if len(set(directions)) == 1:
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.OPTIMISM_BIAS,
                        severity="high",
                        message=f"Long chain ({len(path)} steps) all in same direction suggests unrealistic optimism",
                        recommendation="Break into stages with intermediate checkpoints. Add MODULATE steps between major changes.",
                        confidence=0.85,
                    )
                )

        # Overly optimistic effectiveness estimate
        estimated_eff = plan.get("estimated_effectiveness", 0.5)
        if estimated_eff > 0.85:
            historical_avg = self._get_user_historical_avg()
            if historical_avg and estimated_eff > historical_avg + 0.2:
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.OPTIMISM_BIAS,
                        severity="medium",
                        message=f"Effectiveness estimate ({estimated_eff:.0%}) significantly above your historical average ({historical_avg:.0%})",
                        recommendation="Review similar past transformations. Consider what could go wrong.",
                        confidence=0.75,
                    )
                )

        return warnings

    def _check_planning_fallacy(self, plan: Dict) -> List[BiasWarning]:
        """Check for underestimation of time/complexity"""
        warnings = []
        path = plan.get("path", [])
        time_estimate = plan.get("time_estimate")

        # Complex path with tight timeline
        if len(path) >= 3 and time_estimate and time_estimate < len(path) * 2:
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.PLANNING_FALLACY,
                    severity="medium",
                    message=f"Complex transformation ({len(path)} steps) may take longer than estimated ({time_estimate} units)",
                    recommendation="Apply 2x multiplier to time estimate. Add buffer for unexpected obstacles.",
                    confidence=0.80,
                )
            )

        return warnings

    def _check_availability_bias(self, plan: Dict, context: Dict) -> List[BiasWarning]:
        """Check if user over-relies on familiar examples"""
        warnings = []
        domain = plan.get("domain")

        if self.user_profile and domain:
            # Check if domain is in user's favorites
            if domain in self.user_profile.frequent_domains[:3]:
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.AVAILABILITY_BIAS,
                        severity="low",
                        message=f"You've used '{domain}' frequently. Availability bias may limit view of alternatives.",
                        recommendation=f"Consider: Would a different domain offer a novel approach? Try cross-domain exploration.",
                        confidence=0.60,
                    )
                )

        return warnings

    def _check_confirmation_bias(self, plan: Dict, context: Dict) -> List[BiasWarning]:
        """Check if user seeks only confirming evidence"""
        warnings = []

        # User only looked at success stories
        research_mode = context.get("research_mode")
        if research_mode == "success_only":
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.CONFIRMATION_BIAS,
                    severity="high",
                    message="Research mode: 'success_only' detected. You may be missing critical failure modes.",
                    recommendation="Use research mode 'include_failures' to see what went wrong in similar cases.",
                    confidence=0.90,
                )
            )

        # User dismissed contradictory evidence
        if context.get("dismissed_warnings"):
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.CONFIRMATION_BIAS,
                    severity="medium",
                    message="Previously dismissed warnings may contain important information.",
                    recommendation="Revisit dismissed warnings with fresh perspective.",
                    confidence=0.70,
                )
            )

        return warnings

    def _check_recency_bias(self, plan: Dict, context: Dict) -> List[BiasWarning]:
        """Check if user overweights recent events"""
        warnings = []

        # Recent successful transformation in same domain
        recent_success = context.get("recent_success_domain")
        current_domain = plan.get("domain")

        if recent_success == current_domain:
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.RECENCY_BIAS,
                    severity="low",
                    message=f"Recent success in {current_domain} may create recency bias.",
                    recommendation="Ensure current situation is truly similar to the recent success case.",
                    confidence=0.55,
                )
            )

        return warnings

    def _check_anchoring(self, plan: Dict) -> List[BiasWarning]:
        """Check for heavy reliance on first operation"""
        warnings = []
        path = plan.get("path", [])

        if len(path) >= 3:
            first_op = path[0].get("operation", "") if isinstance(path[0], dict) else str(path[0])
            first_op_count = sum(
                1
                for step in path
                if (step.get("operation", "") if isinstance(step, dict) else str(step)) == first_op
            )
            if first_op_count / len(path) > 0.5:
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.ANCHORING,
                        severity="medium",
                        message=f"Over-reliance on initial operation ({first_op})",
                        recommendation="Consider alternative starting approaches",
                        confidence=0.75,
                    )
                )

        return warnings

    def _check_sunk_cost(self, plan: Dict, context: Dict) -> List[BiasWarning]:
        """Check for continuing with failed approach"""
        warnings = []
        history = context.get("history", [])

        if len(history) >= 2:
            recent_failures = [h for h in history[-3:] if not h.get("success", True)]
            if len(recent_failures) >= 2 and plan.get("path"):
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.SUNK_COST,
                        severity="high",
                        message="Persisting with approach after multiple failures",
                        recommendation="Consider pivoting to alternative strategy",
                        confidence=0.80,
                    )
                )

        return warnings

    def _check_status_quo_bias(self, plan: Dict) -> List[BiasWarning]:
        """Check for preference for maintaining current state"""
        warnings = []
        path = plan.get("path", [])

        if len(path) >= 3:
            # Count operations targeting "content" or similar current-state targets
            content_ops = sum(
                1
                for step in path
                if (step.get("target", "") if isinstance(step, dict) else str(step)) == "content"
            )
            if content_ops / len(path) > 0.7:
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.STATUS_QUO_BIAS,
                        severity="low",
                        message="Strong preference for maintaining current state",
                        recommendation="Consider transformative operations more actively",
                        confidence=0.70,
                    )
                )

        return warnings

    def _check_dunning_kruger(self, plan: Dict) -> List[BiasWarning]:
        """Check for high confidence with low historical effectiveness"""
        warnings = []
        plan_confidence = plan.get("confidence", plan.get("estimated_effectiveness", 0.5))
        domain = plan.get("domain")

        if self.user_profile and domain:
            hist_eff = self.user_profile.historical_effectiveness.get(domain)
            if hist_eff is not None and hist_eff < 0.4 and plan_confidence > 0.8:
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.DUNNING_KRUGER,
                        severity="high",
                        message=f"High confidence ({plan_confidence:.0%}) despite low historical effectiveness ({hist_eff:.0%})",
                        recommendation="Review past outcomes and adjust confidence calibration",
                        confidence=0.85,
                    )
                )

        return warnings

    def _check_survivorship_bias(self) -> List[BiasWarning]:
        """Check for limited domain exposure"""
        warnings = []

        if self.user_profile and len(self.user_profile.frequent_domains) < 3:
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.SURVIVORSHIP_BIAS,
                    severity="low",
                    message=f"Limited domain diversity (only {len(self.user_profile.frequent_domains)} domains explored)",
                    recommendation="Explore a wider range of domains for more robust solutions",
                    confidence=0.65,
                )
            )

        return warnings

    def _extract_directions(self, path: List[Dict]) -> List[str]:
        """Extract direction trends from path"""
        # Simplified: look at operation types
        directions = []
        for step in path:
            op = step.get("operation", "")
            if op in ["ACTIVATE", "DISRUPT"]:
                directions.append("expanding")
            elif op in ["INHIBIT"]:
                directions.append("contracting")
            else:
                directions.append("adjusting")
        return directions

    def _get_user_historical_avg(self) -> Optional[float]:
        """Get user's historical effectiveness average"""
        if not self.user_profile:
            return None

        values = list(self.user_profile.historical_effectiveness.values())
        if not values:
            return None

        return sum(values) / len(values)

    def generate_nudge(self, warnings: List[BiasWarning]) -> str:
        """
        Generate a gentle nudge to help user avoid bias.

        Based on Thaler & Sunstein's "Nudge" principles.
        """
        if not warnings:
            return ""

        # Get user sensitivity preference
        sensitivity = "medium"
        if self.user_profile and hasattr(self.user_profile, "bias_sensitivity"):
            sensitivity = self.user_profile.bias_sensitivity

        # Filter warnings based on sensitivity
        if sensitivity == "low":
            warnings = [w for w in warnings if w.severity in ["critical", "high"]]
        elif sensitivity == "high":
            pass  # Show all
        else:  # medium
            warnings = [w for w in warnings if w.severity in ["critical", "high", "medium"]]

        if not warnings:
            return ""

        # Prioritize by severity
        critical = [w for w in warnings if w.severity == "critical"]
        high = [w for w in warnings if w.severity == "high"]

        nudge_parts = []

        if critical:
            w = critical[0]
            bias_explanation = BIAS_EXPLANATIONS.get(w.bias_type, "")
            nudge_parts.extend(
                [
                    f"⚠️ CRITICAL BIAS DETECTED: {w.bias_type.value.replace('_', ' ').title()}",
                    f"   {bias_explanation}",
                    f"   Issue: {w.message}",
                    f"💡 Recommendation: {w.recommendation}",
                ]
            )
        elif high:
            w = high[0]
            bias_explanation = BIAS_EXPLANATIONS.get(w.bias_type, "")
            nudge_parts.extend(
                [
                    f"⚠️ Bias Detected: {w.bias_type.value.replace('_', ' ').title()}",
                    f"   {bias_explanation}",
                    f"   {w.message}",
                    f"💡 Consider: {w.recommendation}",
                ]
            )
        elif warnings:
            w = warnings[0]
            nudge_parts.extend([f"💭 {w.message}", f"Tip: {w.recommendation}"])

        return "\n".join(nudge_parts)

    def analyze_rag_query(
        self, query: str, sources: List[str], results: List[Dict]
    ) -> List[BiasWarning]:
        """Analyze RAG query for cognitive biases"""
        warnings = []

        # Confirmation bias: preferring user_docs over scientific sources
        if "user_docs" in sources and "scientific" not in sources:
            user_results = [r for r in results if r.get("source") == "user_doc"]
            if len(user_results) > len(results) * 0.8:  # >80% from user docs
                warnings.append(
                    BiasWarning(
                        bias_type=BiasType.CONFIRMATION_BIAS,
                        severity="medium",
                        message="Heavy reliance on personal documents may confirm existing beliefs",
                        recommendation="Consider including scientific sources for broader perspective",
                        confidence=0.7,
                    )
                )

        # Availability bias: query based on recently uploaded content
        if len(query.split()) < 5:  # Very short queries may be availability-biased
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.AVAILABILITY_BIAS,
                    severity="low",
                    message="Short queries may rely on easily recalled information",
                    recommendation="Try more specific queries to access diverse knowledge",
                    confidence=0.5,
                )
            )

        return warnings

    def analyze_document_upload(self, file_path: str, content_summary: Dict) -> List[BiasWarning]:
        """Analyze document upload for cognitive biases"""
        warnings = []

        # Survivorship bias: only uploading successful cases
        if "success" in file_path.lower() or "case study" in file_path.lower():
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.SURVIVORSHIP_BIAS,
                    severity="medium",
                    message="Uploading only success cases may ignore failures",
                    recommendation="Consider including diverse examples including failures",
                    confidence=0.6,
                )
            )

        # Single author bias: documents from one source
        if content_summary.get("authors_count", 1) == 1:
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.AVAILABILITY_BIAS,
                    severity="low",
                    message="Single-author documents may limit perspective",
                    recommendation="Include multiple viewpoints for balanced understanding",
                    confidence=0.5,
                )
            )

        return warnings

    def analyze_discovery_query(self, query: str, domain: str) -> List[BiasWarning]:
        """Analyze discovery query for cognitive biases"""
        warnings = []

        # Optimism bias: expecting to find gaps in "hot" areas
        hot_topics = ["ai", "quantum", "neural", "blockchain", "metaverse"]
        if any(topic in query.lower() for topic in hot_topics):
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.OPTIMISM_BIAS,
                    severity="low",
                    message="Searching in trending topics may overestimate gap significance",
                    recommendation="Balance with established domains for realistic assessment",
                    confidence=0.4,
                )
            )

        # Status quo bias: sticking to familiar domains
        if domain == "general":
            warnings.append(
                BiasWarning(
                    bias_type=BiasType.STATUS_QUO_BIAS,
                    severity="low",
                    message="Sticking to general domain may avoid uncomfortable discoveries",
                    recommendation="Try domain-specific exploration for deeper insights",
                    confidence=0.5,
                )
            )

        return warnings

    def get_bias_summary(self) -> Dict[str, Any]:
        """Get summary of detected biases"""
        if not self.bias_history:
            return {"total": 0, "by_type": {}}

        by_type = {}
        for w in self.bias_history:
            key = w.bias_type.value
            by_type[key] = by_type.get(key, 0) + 1

        return {
            "total": len(self.bias_history),
            "by_type": by_type,
            "most_common": max(by_type.items(), key=lambda x: x[1])[0] if by_type else None,
        }

    def process_bias_feedback(self, bias_type: BiasType, feedback: str) -> None:
        """Process user feedback on bias warnings to improve future detection"""
        if not self.user_profile:
            return

        # Track feedback for learning
        feedback_key = f"{bias_type.value}_feedback"
        current_feedback = getattr(self.user_profile, feedback_key, [])
        current_feedback.append({"feedback": feedback, "timestamp": datetime.now().isoformat()})

        # Keep only last 10 feedbacks
        current_feedback = current_feedback[-10:]
        setattr(self.user_profile, feedback_key, current_feedback)

        # Adjust sensitivity based on feedback
        if feedback in ["irrelevant", "annoying"]:
            # Reduce sensitivity for this bias type
            if hasattr(self.user_profile, "bias_sensitivity_levels"):
                levels = self.user_profile.bias_sensitivity_levels
                levels[bias_type.value] = max(0.1, levels.get(bias_type.value, 1.0) - 0.1)
            else:
                self.user_profile.bias_sensitivity_levels = {bias_type.value: 0.9}
