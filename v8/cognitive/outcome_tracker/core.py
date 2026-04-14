"""
TURBO-CDI v8.0 - Outcome Tracker
Agent 1: Empirical Systems

Real-world outcome tracking and calibration.
Implements Taleb's "skin in the game" principle.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
import json


@dataclass
class Prediction:
    """A prediction before transformation is applied"""

    id: str
    transformation_id: str
    domain: str
    predicted_effectiveness: float
    predicted_reversibility: float
    context: Dict
    timestamp: datetime
    user_id: Optional[str] = None


@dataclass
class Outcome:
    """Actual outcome after transformation"""

    prediction_id: str
    actual_effectiveness: float
    actual_reversibility: float
    user_satisfaction: float  # 0-1 scale
    side_effects: List[str]
    timestamp: datetime
    notes: Optional[str] = None


@dataclass
class CalibrationScore:
    """Calibration metrics"""

    brier: float  # Mean squared error (0 = perfect)
    n_samples: int
    confidence: str  # "low", "medium", "high", "unknown"
    calibration_curve: Optional[List[tuple]] = None

    def is_well_calibrated(self, threshold: float = 0.1) -> bool:
        """Check if Brier score indicates good calibration"""
        return self.brier <= threshold


@dataclass
class Insight:
    """Insight from outcome analysis"""

    type: str
    message: str
    severity: str  # "info", "low", "medium", "high"
    recommendation: str


class OutcomeTracker:
    """
    Tracks predictions vs actual outcomes.
    Updates domain profiles based on empirical data.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".turbo-cdi" / "outcomes.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.predictions: Dict[str, Prediction] = {}
        self.outcomes: Dict[str, Outcome] = {}
        self._counter = 0
        self._load()

    def _generate_id(self) -> str:
        """Generate unique prediction ID"""
        self._counter += 1
        return f"pred_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._counter}"

    def _load(self):
        """Load stored predictions and outcomes"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    # Deserialize predictions and outcomes
                    for p_data in data.get("predictions", []):
                        p_data["timestamp"] = datetime.fromisoformat(
                            p_data["timestamp"]
                        )
                        pred = Prediction(**p_data)
                        self.predictions[pred.id] = pred
                    for o_data in data.get("outcomes", []):
                        o_data["timestamp"] = datetime.fromisoformat(
                            o_data["timestamp"]
                        )
                        out = Outcome(**o_data)
                        self.outcomes[out.prediction_id] = out
            except Exception as e:
                print(f"Warning: Could not load outcomes: {e}")

    def _save(self):
        """Save predictions and outcomes to disk"""
        data = {
            "predictions": [
                {**p.__dict__, "timestamp": p.timestamp.isoformat()}
                for p in self.predictions.values()
            ],
            "outcomes": [
                {**o.__dict__, "timestamp": o.timestamp.isoformat()}
                for o in self.outcomes.values()
            ],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def record_prediction(
        self,
        transformation_id: str,
        domain: str,
        predicted_effectiveness: float,
        predicted_reversibility: float,
        context: Dict,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Record a prediction before transformation is applied.

        Returns: prediction_id to use when recording outcome
        """
        pred = Prediction(
            id=self._generate_id(),
            transformation_id=transformation_id,
            domain=domain,
            predicted_effectiveness=predicted_effectiveness,
            predicted_reversibility=predicted_reversibility,
            context=context,
            timestamp=datetime.now(),
            user_id=user_id,
        )
        self.predictions[pred.id] = pred
        self._save()
        return pred.id

    def record_outcome(
        self,
        prediction_id: str,
        actual_effectiveness: float,
        actual_reversibility: float,
        user_satisfaction: float = 0.5,
        side_effects: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> CalibrationScore:
        """
        Record actual outcome after transformation.

        Returns: Calibration report comparing prediction vs actual
        """
        if prediction_id not in self.predictions:
            raise ValueError(f"Unknown prediction: {prediction_id}")

        outcome = Outcome(
            prediction_id=prediction_id,
            actual_effectiveness=actual_effectiveness,
            actual_reversibility=actual_reversibility,
            user_satisfaction=user_satisfaction,
            side_effects=side_effects or [],
            timestamp=datetime.now(),
            notes=notes,
        )
        self.outcomes[prediction_id] = outcome

        # Generate calibration report
        prediction = self.predictions[prediction_id]
        report = self._calculate_single_calibration(prediction, outcome)

        self._save()
        return report

    def _calculate_single_calibration(
        self, prediction: Prediction, outcome: Outcome
    ) -> CalibrationScore:
        """Calculate calibration for a single prediction-outcome pair"""
        error = (prediction.predicted_effectiveness - outcome.actual_effectiveness) ** 2

        confidence = "unknown"
        if error < 0.01:
            confidence = "high"
        elif error < 0.05:
            confidence = "medium"
        else:
            confidence = "low"

        return CalibrationScore(brier=error, n_samples=1, confidence=confidence)

    def calculate_calibration(
        self, domain: Optional[str] = None, operation: Optional[str] = None
    ) -> CalibrationScore:
        """
        Calculate calibration score: how well predictions match reality.

        Brier score: mean squared error (0 = perfect, 0.25 = random)
        """
        pairs = []

        for pred_id, pred in self.predictions.items():
            if pred_id not in self.outcomes:
                continue

            # Filter by domain if specified
            if domain and pred.domain != domain:
                continue

            outcome = self.outcomes[pred_id]
            pairs.append((pred.predicted_effectiveness, outcome.actual_effectiveness))

        if not pairs:
            return CalibrationScore(brier=0.0, n_samples=0, confidence="unknown")

        # Calculate Brier score
        brier = sum((p - a) ** 2 for p, a in pairs) / len(pairs)

        # Determine confidence level
        if brier < 0.05:
            confidence = "high"
        elif brier < 0.15:
            confidence = "medium"
        else:
            confidence = "low"

        return CalibrationScore(
            brier=brier, n_samples=len(pairs), confidence=confidence
        )

    def get_insights(self) -> List[Insight]:
        """Generate insights from tracked outcomes"""
        insights = []

        # Check calibration drift
        calibration = self.calculate_calibration()
        if calibration.n_samples >= 5:
            if calibration.brier > 0.15:
                insights.append(
                    Insight(
                        type="calibration_drift",
                        message=f"Predictions are miscalibrated (Brier: {calibration.brier:.3f})",
                        severity="high",
                        recommendation="Adjust prediction confidence intervals downward",
                    )
                )
            elif calibration.brier < 0.03:
                insights.append(
                    Insight(
                        type="calibration_good",
                        message=f"Excellent calibration (Brier: {calibration.brier:.3f})",
                        severity="info",
                        recommendation="Current prediction model is working well",
                    )
                )

        # Analyze domain effectiveness
        domain_stats = self._get_domain_stats()
        if domain_stats:
            best_domain = max(domain_stats.items(), key=lambda x: x[1]["avg"])
            insights.append(
                Insight(
                    type="domain_effectiveness",
                    message=f"'{best_domain[0]}' shows highest effectiveness ({best_domain[1]['avg']:.2f})",
                    severity="info",
                    recommendation=f"Consider patterns from {best_domain[0]} for similar transformations",
                )
            )

        return insights

    def _get_domain_stats(self) -> Dict[str, Dict]:
        """Calculate statistics per domain"""
        stats = {}

        for pred_id, outcome in self.outcomes.items():
            if pred_id not in self.predictions:
                continue

            pred = self.predictions[pred_id]
            domain = pred.domain

            if domain not in stats:
                stats[domain] = {"values": [], "count": 0}

            stats[domain]["values"].append(outcome.actual_effectiveness)
            stats[domain]["count"] += 1

        # Calculate averages
        for domain, data in stats.items():
            if data["values"]:
                data["avg"] = sum(data["values"]) / len(data["values"])

        return stats

    def get_pending_predictions(self) -> List[Prediction]:
        """Get predictions waiting for outcomes"""
        return [p for p in self.predictions.values() if p.id not in self.outcomes]

    def get_stats(self) -> Dict:
        """Get summary statistics"""
        return {
            "total_predictions": len(self.predictions),
            "recorded_outcomes": len(self.outcomes),
            "pending_outcomes": len(self.get_pending_predictions()),
            "calibration": {
                "brier": self.calculate_calibration().brier,
                "confidence": self.calculate_calibration().confidence,
            }
            if self.outcomes
            else None,
        }
