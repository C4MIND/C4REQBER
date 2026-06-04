from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FalsificationTest:
    """FalsificationTest."""
    hypothesis: str
    prediction: str
    test_result: str  # "confirmed", "falsified", "inconclusive"
    confidence: float

@dataclass
class FalsificationResult:
    """FalsificationResult."""
    hypothesis: str
    tests: list[FalsificationTest] = field(default_factory=list[Any])
    is_falsified: bool = False
    corroboration: float = 0.0

def run_falsification(
    hypothesis: str,
    predictions: list[str],
    results: list[tuple[str, float]],
) -> FalsificationResult:
    """Run falsification tests on a hypothesis"""
    fr = FalsificationResult(hypothesis=hypothesis)
    falsified_count = 0
    confirmed_count = 0

    for pred, (result, confidence) in zip(predictions, results):  # noqa: B905
        test = FalsificationTest(
            hypothesis=hypothesis,
            prediction=pred,
            test_result=result,
            confidence=confidence,
        )
        fr.tests.append(test)
        if result == "falsified":
            falsified_count += 1
        elif result == "confirmed":
            confirmed_count += 1

    total = len(fr.tests)
    fr.is_falsified = falsified_count > 0
    fr.corroboration = confirmed_count / total if total > 0 else 0.0

    return fr
