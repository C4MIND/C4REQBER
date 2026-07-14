# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import re
from typing import Any


class ParsimonyScorer:
    """Score hypothesis parsimony. Lower is better (penalty)."""

    def __init__(self) -> None:
        pass

    def score(self, hypothesis_text: str) -> dict[str, Any]:
        """Compute parsimony metrics for a hypothesis.

        Returns: overall_parsimony (0=perfect, 1=worst), parameter_count,
                description_length, predictive_density.
        """
        params = self._count_free_parameters(hypothesis_text)
        desc_len = self._description_length(hypothesis_text)
        pred_count = self._count_predictions(hypothesis_text)

        # Normalize to [0, 1]
        param_penalty = min(1.0, params / 20.0)
        length_penalty = min(1.0, desc_len / 2000.0)
        pred_density = pred_count / max(1, desc_len / 100.0)
        density_penalty = 1.0 - min(1.0, pred_density)

        overall = 0.4 * param_penalty + 0.3 * length_penalty + 0.3 * density_penalty

        return {
            "overall_parsimony": round(1.0 - overall, 4),  # invert: 1=most parsimonious
            "parameter_count": params,
            "description_length_chars": desc_len,
            "description_length_words": len(hypothesis_text.split()),
            "predictions": pred_count,
            "predictive_density": round(pred_density, 4),
            "interpretation": self._interpret(1.0 - overall),
        }

    def _count_free_parameters(self, text: str) -> int:
        """Estimate number of free parameters in hypothesis."""
        # Count numerical constants and adjustable variables
        numbers = re.findall(r"[\d]+\.?[\d]*", text)
        # Find explicit parameter mentions
        param_indicators = [
            "parameter", "constant", "coefficient", "factor",
            "rate", "threshold", "temperature", "pressure", "density",
            "mass", "energy", "time", "length", "velocity", "frequency",
            "alpha", "beta", "gamma", "delta", "epsilon", "lambda",
        ]
        count = 0
        text_l = text.lower()
        for pi in param_indicators:
            count += len(re.findall(rf"\b{pi}\b", text_l))
        return min(count + len(numbers) // 3, 50)

    def _description_length(self, text: str) -> int:
        return len(text)

    def _count_predictions(self, text: str) -> int:
        indicators = ["predict", "implies", "therefore", "thus", "hence", "yields", "follows", "should", "will"]
        text_l = text.lower()
        count = 0
        for ind in indicators:
            count += len(re.findall(rf"\b{ind}\b", text_l))
        return max(1, count)

    def _interpret(self, parsimony: float) -> str:
        if parsimony >= 0.9:
            return "highly parsimonious — minimal assumptions"
        if parsimony >= 0.7:
            return "parsimonious — reasonable complexity"
        if parsimony >= 0.5:
            return "moderately complex — some overfitting risk"
        if parsimony >= 0.3:
            return "overparameterized — likely overfit"
        return "severe overparameterization — needs simplification"

    def penalty(self, hypothesis_text: str) -> float:
        """Return quality penalty (0 to -15)."""
        s = self.score(hypothesis_text)
        return round(-15 * (1 - s["overall_parsimony"]), 2)


__all__ = ["ParsimonyScorer"]
