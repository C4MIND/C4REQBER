"""
TURBO-CDI v8.0 - Self-Modifier
Agent 4: Meta Systems

Auto-tuning capabilities: the system improves itself based on observations.
Adjusts parameters, optimizes performance, learns from experience.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import math
import threading


@dataclass
class TuningAction:
    """A self-modification action"""

    timestamp: datetime
    parameter: str
    old_value: float
    new_value: float
    reason: str
    confidence: float  # 0-1, confidence in this change
    rollback_available: bool = True


@dataclass
class TuningReport:
    """Report on self-tuning activities"""

    timestamp: datetime
    actions_taken: List[TuningAction]
    improvements: Dict[str, float]  # metric -> improvement %
    regressions: Dict[str, float]  # metric -> regression %
    recommendations: List[str]
    auto_tune_enabled: bool


class SelfModifier:
    """
    Self-modification and auto-tuning system.

    Capabilities:
    - Parameter optimization based on performance data
    - Calibration adjustment from outcome tracking
    - Strategy adaptation based on success rates
    - Automatic rollback on regression detection

    Philosophy: "The system that improves itself must also protect itself"
    """

    def __init__(self, conservative_mode: bool = True):
        self.conservative_mode = conservative_mode
        self.tuning_history: List[TuningAction] = []
        self.parameters: Dict[str, float] = {}
        self._initialize_defaults()
        self._rollback_stack: List[Dict[str, float]] = []
        self._rollback_lock = threading.Lock()

    def _initialize_defaults(self):
        """Initialize default parameters"""
        self.parameters = {
            # Effectiveness calculation weights
            "effectiveness_base_weight": 0.7,
            "effectiveness_domain_weight": 0.3,
            # Bias detection thresholds
            "bias_confidence_threshold": 0.6,
            "bias_severity_threshold": 0.5,
            # Navigation optimization
            "navigation_cost_weight": 1.0,
            "navigation_resonance_weight": 0.5,
            # Calibration learning rate
            "calibration_learning_rate": 0.1,
            "calibration_decay": 0.01,
            # Pattern synthesis thresholds
            "pattern_novelty_threshold": 0.5,
            "pattern_effectiveness_threshold": 0.6,
            # Peer review thresholds
            "peer_review_pass_threshold": 0.7,
            "peer_review_warning_threshold": 0.5,
            # Bridge discovery
            "bridge_similarity_threshold": 0.6,
            "bridge_min_samples": 5,
        }

    def tune_from_outcomes(
        self,
        domain: str,
        predicted_effectiveness: float,
        actual_effectiveness: float,
        n_samples: int,
    ) -> Optional[TuningAction]:
        """
        Tune parameters based on outcome tracking data.

        Args:
            domain: Domain being tuned
            predicted: Predicted effectiveness
            actual: Actual effectiveness
            n_samples: Number of samples

        Returns:
            TuningAction if adjustment made, None otherwise
        """
        error = abs(predicted_effectiveness - actual_effectiveness)

        # Only tune if we have enough samples and significant error
        if n_samples < 5 or error < 0.1:
            return None

        # Adjust learning rate based on error magnitude
        current_lr = self.parameters["calibration_learning_rate"]

        if error > 0.3:  # Large error -> increase learning
            new_lr = min(0.5, current_lr * 1.2)
            reason = f"Large prediction error ({error:.2f}) in {domain}"
        elif error < 0.05:  # Small error -> decrease learning (stable)
            new_lr = max(0.01, current_lr * 0.9)
            reason = f"Good calibration in {domain}, reducing learning rate"
        else:
            return None

        return self._apply_tuning(
            "calibration_learning_rate",
            new_lr,
            reason,
            confidence=1.0 - error,  # Higher confidence with lower error
        )

    def tune_from_performance(
        self, operation: str, duration_ms: float, benchmark_ms: float
    ) -> Optional[TuningAction]:
        """
        Tune parameters based on performance metrics.

        Args:
            operation: Operation performed
            duration_ms: Actual duration
            benchmark_ms: Target duration

        Returns:
            TuningAction if adjustment made
        """
        ratio = duration_ms / benchmark_ms if benchmark_ms > 0 else 1.0

        if ratio < 1.2:  # Within 20% of target
            return None

        # Performance issue detected
        if operation == "navigation" and ratio > 2.0:
            # Reduce navigation complexity weight
            old_weight = self.parameters["navigation_resonance_weight"]
            new_weight = old_weight * 0.8  # Reduce resonance consideration

            return self._apply_tuning(
                "navigation_resonance_weight",
                new_weight,
                f"Navigation slow ({duration_ms:.1f}ms > {benchmark_ms:.1f}ms)",
                confidence=0.7,
            )

        elif operation == "bias_detection" and ratio > 1.5:
            # Simplify bias detection
            old_threshold = self.parameters["bias_confidence_threshold"]
            new_threshold = min(0.8, old_threshold + 0.05)

            return self._apply_tuning(
                "bias_confidence_threshold",
                new_threshold,
                f"Bias detection slow ({duration_ms:.1f}ms)",
                confidence=0.6,
            )

        return None

    def tune_from_calibration(
        self, domain: str, brier_score: float, historical_brier: Optional[float] = None
    ) -> Optional[TuningAction]:
        """
        Tune based on calibration metrics.

        Args:
            domain: Domain being analyzed
            brier_score: Current Brier score
            historical_brier: Previous Brier score for comparison

        Returns:
            TuningAction if adjustment made
        """
        # Check for calibration drift
        if historical_brier and brier_score > historical_brier * 1.3:
            # Calibration getting worse
            old_weight = self.parameters["effectiveness_domain_weight"]
            new_weight = min(0.5, old_weight + 0.05)  # Trust domain data more

            return self._apply_tuning(
                "effectiveness_domain_weight",
                new_weight,
                f"Calibration drift in {domain}: {historical_brier:.3f} -> {brier_score:.3f}",
                confidence=0.75,
            )

        # Very good calibration -> can rely more on base effectiveness
        if brier_score < 0.03:
            old_weight = self.parameters["effectiveness_base_weight"]
            new_weight = min(0.9, old_weight + 0.02)

            return self._apply_tuning(
                "effectiveness_base_weight",
                new_weight,
                f"Excellent calibration in {domain}, trusting base model more",
                confidence=0.8,
            )

        return None

    def _apply_tuning(
        self, parameter: str, new_value: float, reason: str, confidence: float
    ) -> Optional[TuningAction]:
        """
        Apply a tuning action with safeguards.

        Args:
            parameter: Parameter to change
            new_value: New value
            reason: Reason for change
            confidence: Confidence in change (0-1)

        Returns:
            TuningAction if applied, None if rejected
        """
        if parameter not in self.parameters:
            return None

        old_value = self.parameters[parameter]

        # Conservative mode: require higher confidence
        if self.conservative_mode and confidence < 0.7:
            return None

        # Validate change magnitude (prevent wild swings)
        change_ratio = (
            abs(new_value - old_value) / old_value if old_value != 0 else abs(new_value)
        )
        if change_ratio > 0.5:  # Max 50% change at once
            new_value = old_value * (1.5 if new_value > old_value else 0.5)

        # Save for rollback
        self._rollback_stack.append(dict(self.parameters))
        if len(self._rollback_stack) > 10:  # Keep last 10
            self._rollback_stack.pop(0)

        # Apply change
        self.parameters[parameter] = round(new_value, 4)

        action = TuningAction(
            timestamp=datetime.now(),
            parameter=parameter,
            old_value=old_value,
            new_value=self.parameters[parameter],
            reason=reason,
            confidence=confidence,
        )

        self.tuning_history.append(action)
        return action

    def rollback(self, n_steps: int = 1) -> bool:
        """Rollback to previous state with thread safety."""
        with self._rollback_lock:
            if n_steps > len(self._rollback_stack):
                return False

            target_state = self._rollback_stack[-n_steps]
            self.parameters = target_state.copy()
            self._rollback_stack = self._rollback_stack[:-n_steps]
            return True

    def generate_tuning_report(self) -> TuningReport:
        """
        Generate report on self-tuning activities.

        Returns:
            TuningReport with analysis
        """
        recent_actions = self.tuning_history[-50:]  # Last 50 actions

        # Analyze improvements/regressions
        # (In real system, would track actual metric changes)
        improvements = {}
        regressions = {}

        for action in recent_actions:
            change_ratio = (
                (action.new_value - action.old_value) / action.old_value
                if action.old_value != 0
                else 0
            )

            # Simple heuristic: if parameter name contains positive words
            if any(
                word in action.parameter for word in ["weight", "rate", "threshold"]
            ):
                if change_ratio > 0:
                    improvements[action.parameter] = change_ratio * 100
                else:
                    regressions[action.parameter] = abs(change_ratio) * 100

        # Generate recommendations
        recommendations = []

        if len(self.tuning_history) > 20:
            recommendations.append(
                "High tuning frequency detected. Consider stabilizing parameters."
            )

        if len(regressions) > len(improvements):
            recommendations.append(
                "More regressions than improvements. Review tuning strategy."
            )

        if not self.conservative_mode:
            recommendations.append(
                "Conservative mode disabled. Enable for production stability."
            )

        return TuningReport(
            timestamp=datetime.now(),
            actions_taken=recent_actions,
            improvements=improvements,
            regressions=regressions,
            recommendations=recommendations,
            auto_tune_enabled=True,
        )

    def get_parameter(self, name: str) -> Optional[float]:
        """Get current parameter value"""
        return self.parameters.get(name)

    def set_parameter(self, name: str, value: float, manual: bool = True) -> bool:
        """
        Manually set parameter value.

        Args:
            name: Parameter name
            value: New value
            manual: Whether this is manual override

        Returns:
            True if set successfully
        """
        if name not in self.parameters:
            return False

        # Type validation
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (TypeError, ValueError):
                return False

        if manual:
            with self._rollback_lock:
                old_value = self.parameters[name]
                self._rollback_stack.append(dict(self.parameters))
                if len(self._rollback_stack) > 10:
                    self._rollback_stack.pop(0)

        self.parameters[name] = round(value, 4)

        if manual:
            self.tuning_history.append(
                TuningAction(
                    timestamp=datetime.now(),
                    parameter=name,
                    old_value=old_value,
                    new_value=value,
                    reason="Manual override",
                    confidence=1.0,
                    rollback_available=True,
                )
            )

        return True

    def get_all_parameters(self) -> Dict[str, float]:
        """Get all current parameters"""
        return dict(self.parameters)

    def export_config(self) -> Dict[str, Any]:
        """Export current configuration for persistence"""
        return {
            "parameters": self.parameters,
            "conservative_mode": self.conservative_mode,
            "tuning_history_count": len(self.tuning_history),
            "last_updated": datetime.now().isoformat(),
        }

    def import_config(self, config: Dict[str, Any]) -> bool:
        """Import configuration"""
        try:
            if "parameters" in config:
                self.parameters.update(config["parameters"])
            if "conservative_mode" in config:
                self.conservative_mode = config["conservative_mode"]
            return True
        except Exception:
            return False
