"""
TURBO-CDI: Trends of Evolution
TRIZ S-curve analysis and technology forecasting
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class EvolutionStage(Enum):
    """Stages of technology evolution."""

    BIRTH = "birth"  # Initial concept
    GROWTH = "growth"  # Rapid improvement
    MATURITY = "maturity"  # Slowing improvements
    DECLINE = "decline"  # Diminishing returns


@dataclass
class SCurveAnalysis:
    """S-curve analysis result."""

    technology: str
    current_stage: EvolutionStage
    maturity_percent: float  # 0-100

    # Metrics
    performance_trend: str  # improving/stable/declining
    patent_activity: str  # high/medium/low
    market_growth: str  # high/medium/low

    # Predictions
    time_to_maturity: Optional[int]  # years
    next_paradigm: Optional[str]

    # Recommendations
    strategy: str
    investment_recommendation: str


class TrendsOfEvolution:
    """
    TRIZ Trends of Evolution analyzer.

    Predicts technology evolution using S-curves and
    TRIZ trends of technical system evolution.
    """

    # 8 TRIZ Trends of Evolution
    TRENDS = {
        "s_curve": "S-curve maturity",
        "idealization": "Ideal final result",
        "dynamization": "Increasing dynamism",
        "automation": "Increasing automation",
        "structural": "Structural evolution",
        "coordination": "Coordination evolution",
        "complexity": "Complexity then simplicity",
        "controllability": "Controllability evolution",
    }

    def __init__(self):
        pass

    def analyze_technology(
        self, technology: str, metrics: Optional[List[float]] = None
    ) -> SCurveAnalysis:
        """
        Analyze technology maturity using S-curve.

        Args:
            technology: Technology name
            metrics: Performance metrics over time (optional)

        Returns:
            SCurveAnalysis with stage and predictions
        """
        # If no metrics provided, estimate based on keywords
        if not metrics:
            stage, maturity = self._estimate_from_keywords(technology)
        else:
            stage, maturity = self._calculate_from_metrics(metrics)

        # Determine trends
        performance = self._assess_performance_trend(technology, stage)
        patents = self._assess_patent_activity(technology, stage)
        market = self._assess_market_growth(technology, stage)

        # Generate predictions
        time_to_maturity = self._predict_time_to_maturity(stage, maturity)
        next_paradigm = self._predict_next_paradigm(technology, stage)

        # Generate recommendations
        strategy = self._recommend_strategy(stage)
        investment = self._recommend_investment(stage, maturity)

        return SCurveAnalysis(
            technology=technology,
            current_stage=stage,
            maturity_percent=maturity,
            performance_trend=performance,
            patent_activity=patents,
            market_growth=market,
            time_to_maturity=time_to_maturity,
            next_paradigm=next_paradigm,
            strategy=strategy,
            investment_recommendation=investment,
        )

    def _estimate_from_keywords(self, technology: str) -> Tuple[EvolutionStage, float]:
        """Estimate maturity from technology keywords."""
        tech_lower = technology.lower()

        # Emerging keywords
        emerging = ["quantum", "ai", "blockchain", "crispr", "graphene", "fusion"]
        # Growth keywords
        growth = ["electric vehicle", "solar", "wind", "5g", "vr", "ar"]
        # Mature keywords
        mature = ["lithium-ion", "silicon", "lcd", "hard disk", "gasoline"]
        # Declining keywords
        decline = ["coal", "crt", "film camera", "floppy disk"]

        for keyword in emerging:
            if keyword in tech_lower:
                return EvolutionStage.BIRTH, 15.0

        for keyword in growth:
            if keyword in tech_lower:
                return EvolutionStage.GROWTH, 45.0

        for keyword in mature:
            if keyword in tech_lower:
                return EvolutionStage.MATURITY, 75.0

        for keyword in decline:
            if keyword in tech_lower:
                return EvolutionStage.DECLINE, 90.0

        # Default
        return EvolutionStage.GROWTH, 50.0

    def _calculate_from_metrics(
        self, metrics: List[float]
    ) -> Tuple[EvolutionStage, float]:
        """Calculate maturity from performance metrics."""
        if len(metrics) < 2:
            return EvolutionStage.GROWTH, 50.0

        # Calculate growth rate
        recent_growth = (
            (metrics[-1] - metrics[-2]) / metrics[-2] if metrics[-2] > 0 else 0
        )

        # Calculate second derivative (acceleration)
        if len(metrics) >= 3:
            growth_1 = (
                (metrics[-2] - metrics[-3]) / metrics[-3] if metrics[-3] > 0 else 0
            )
            acceleration = recent_growth - growth_1
        else:
            acceleration = 0

        # Determine stage
        if recent_growth > 0.2 and acceleration > 0:
            return EvolutionStage.GROWTH, 40.0
        elif recent_growth > 0.05:
            return EvolutionStage.MATURITY, 70.0
        elif recent_growth < 0:
            return EvolutionStage.DECLINE, 85.0
        else:
            return EvolutionStage.BIRTH, 20.0

    def _assess_performance_trend(self, technology: str, stage: EvolutionStage) -> str:
        """Assess performance trend."""
        trends = {
            EvolutionStage.BIRTH: "improving",
            EvolutionStage.GROWTH: "improving",
            EvolutionStage.MATURITY: "stable",
            EvolutionStage.DECLINE: "declining",
        }
        return trends.get(stage, "stable")

    def _assess_patent_activity(self, technology: str, stage: EvolutionStage) -> str:
        """Assess patent activity."""
        activity = {
            EvolutionStage.BIRTH: "low",
            EvolutionStage.GROWTH: "high",
            EvolutionStage.MATURITY: "medium",
            EvolutionStage.DECLINE: "low",
        }
        return activity.get(stage, "medium")

    def _assess_market_growth(self, technology: str, stage: EvolutionStage) -> str:
        """Assess market growth."""
        growth = {
            EvolutionStage.BIRTH: "low",
            EvolutionStage.GROWTH: "high",
            EvolutionStage.MATURITY: "medium",
            EvolutionStage.DECLINE: "declining",
        }
        return growth.get(stage, "medium")

    def _predict_time_to_maturity(
        self, stage: EvolutionStage, maturity: float
    ) -> Optional[int]:
        """Predict years to full maturity."""
        if stage == EvolutionStage.DECLINE:
            return 0

        remaining = 95 - maturity  # Target 95% maturity

        # Different technologies mature at different rates
        years_per_percent = {
            EvolutionStage.BIRTH: 0.5,
            EvolutionStage.GROWTH: 0.3,
            EvolutionStage.MATURITY: 0.8,
        }

        rate = years_per_percent.get(stage, 0.5)
        return int(remaining * rate)

    def _predict_next_paradigm(
        self, technology: str, stage: EvolutionStage
    ) -> Optional[str]:
        """Predict next technological paradigm."""
        paradigms = {
            "lithium-ion": "solid-state batteries",
            "silicon solar": "perovskite solar",
            "lcd display": "microled",
            "gasoline engine": "electric motors",
            "hard disk": "solid-state storage",
        }

        tech_lower = technology.lower()
        for key, next_tech in paradigms.items():
            if key in tech_lower:
                return next_tech

        return None

    def _recommend_strategy(self, stage: EvolutionStage) -> str:
        """Recommend innovation strategy."""
        strategies = {
            EvolutionStage.BIRTH: "Invest in R&D, focus on proof-of-concept",
            EvolutionStage.GROWTH: "Scale production, capture market share",
            EvolutionStage.MATURITY: "Optimize efficiency, reduce costs",
            EvolutionStage.DECLINE: "Prepare transition, harvest profits",
        }
        return strategies.get(stage, "Monitor and evaluate")

    def _recommend_investment(self, stage: EvolutionStage, maturity: float) -> str:
        """Recommend investment level."""
        if stage == EvolutionStage.GROWTH:
            return "HIGH - Maximum growth potential"
        elif stage == EvolutionStage.BIRTH and maturity < 20:
            return "MODERATE - High risk, high reward"
        elif stage == EvolutionStage.MATURITY:
            return "LOW - Stable returns, limited upside"
        else:
            return "AVOID - Declining technology"

    def render_s_curve(self, analysis: SCurveAnalysis, width: int = 60) -> str:
        """Render ASCII S-curve visualization."""
        # Simplified S-curve
        height = 10

        lines = ["", f"S-Curve: {analysis.technology}", "=" * width, ""]

        # Draw curve
        for y in range(height, -1, -1):
            line = ""
            for x in range(width):
                # S-curve function: sigmoid
                normalized_x = (x / width) * 10 - 5
                s_value = 1 / (1 + math.exp(-normalized_x))
                curve_y = int(s_value * height)

                if y == curve_y:
                    line += "█"
                elif y == 0:
                    line += "─"
                else:
                    line += " "

            # Add y-axis labels
            if y == height:
                line = "100%│" + line
            elif y == height // 2:
                line = " 50%│" + line
            elif y == 0:
                line = "  0%├" + line + "─"
            else:
                line = "    │" + line

            lines.append(line)

        # X-axis
        lines.append("    └" + "─" * width)
        lines.append("     Birth      Growth      Maturity    Decline")

        # Current position marker
        pos = int(analysis.maturity_percent / 100 * width)
        marker = " " * (pos + 5) + "▲ Current"
        lines.append(marker)

        # Info
        lines.extend(
            [
                "",
                f"Stage: {analysis.current_stage.value.upper()}",
                f"Maturity: {analysis.maturity_percent:.0f}%",
            ]
        )

        if analysis.time_to_maturity:
            lines.append(f"Time to maturity: ~{analysis.time_to_maturity} years")

        if analysis.next_paradigm:
            lines.append(f"Next paradigm: {analysis.next_paradigm}")

        lines.append("")

        return "\n".join(lines)


# Singleton
_trends: Optional[TrendsOfEvolution] = None


def get_trends_analyzer() -> TrendsOfEvolution:
    """Get singleton trends analyzer."""
    global _trends
    if _trends is None:
        _trends = TrendsOfEvolution()
    return _trends
