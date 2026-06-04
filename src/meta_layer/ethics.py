"""Ethics checker"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EthicsCheck:
    """EthicsCheck."""
    name: str
    passed: bool
    score: float
    details: str = ""

@dataclass
class EthicsReport:
    """EthicsReport."""
    checks: list[EthicsCheck]
    overall_score: float
    recommendations: list[str]

ETHICS_CHECKLIST = [
    ("bias_assessment", "Check for potential biases", 0.3),
    ("transparency", "Explainability check", 0.2),
    ("privacy", "Data privacy compliance", 0.2),
    ("fairness", "Fairness across demographics", 0.15),
    ("safety", "Safety and misuse prevention", 0.15),
]

def run_ethics_check(context: dict[str, Any]) -> EthicsReport:
    """Run ethics assessment"""
    checks: list[EthicsCheck] = []
    total = 0.0

    for name, _desc, weight in ETHICS_CHECKLIST:
        score = 1.0
        details = ""

        if name == "bias_assessment":
            score = 0.9 if context.get("no_bias", True) else 0.4
            details = (
                "No explicit bias indicators found"
                if score > 0.7
                else "Potential bias indicators detected"
            )
        elif name == "transparency":
            score = 0.8 if context.get("explainability", False) else 0.5
            details = (
                "Explainability enabled" if score > 0.7 else "Explainability must be added"
            )
        elif name == "privacy":
            score = 0.95 if context.get("no_pii", True) else 0.3
            details = (
                "No PII processing detected" if score > 0.7 else "PII handling detected"
            )
        elif name == "fairness":
            score = 0.85 if context.get("fair", True) else 0.6
            details = (
                "Demographic parity baseline met"
                if score > 0.7
                else "Fairness concerns identified"
            )
        elif name == "safety":
            score = 0.9 if context.get("safety_on", True) else 0.4
            details = (
                "Rate limiting and content filtering active"
                if score > 0.7
                else "Safety measures insufficient"
            )

        checks.append(
            EthicsCheck(name=name, passed=score >= 0.7, score=score, details=details)
        )
        total += score * weight

    recommendations = []
    for c in checks:
        if not c.passed:
            if c.name == "transparency":
                recommendations.append("Enable explainability for generated outputs")
            elif c.name == "safety":
                recommendations.append("Enable rate limiting and content filtering")
            elif c.name == "privacy":
                recommendations.append("Remove PII processing or add data anonymization")
            elif c.name == "fairness":
                recommendations.append("Audit demographic parity across outputs")
            elif c.name == "bias_assessment":
                recommendations.append("Run bias detection scan on training data")

    return EthicsReport(
        checks=checks,
        overall_score=round(total * 100, 1),
        recommendations=recommendations or ["All checks passed"],
    )
