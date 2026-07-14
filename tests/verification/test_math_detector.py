from __future__ import annotations

import pytest

from src.verification.math_detector import detect_math_structure, should_attempt_formal_verification


class TestDetectMathStructure:
    def test_category_a_rich_equation(self) -> None:
        result = detect_math_structure(
            "The O(n log n) algorithm satisfies d/dt H(t) = 0 with T >= 2.27K"
        )
        assert result["category"] == "A"
        assert len(result["matched_structures"]) >= 3

    def test_category_c_qualitative(self) -> None:
        result = detect_math_structure("Sleep serves a metabolic clearance function")
        assert result["category"] == "C"
        assert result["matched_structures"] == []

    def test_category_b_mixed(self) -> None:
        result = detect_math_structure(
            "The algorithm achieves O(n log n) through divide-and-conquer"
        )
        assert result["category"] == "B"

    def test_empty_string_category_c(self) -> None:
        result = detect_math_structure("")
        assert result["category"] == "C"
        assert result["verifiability_score"] == 0.0

    def test_verifiability_scores(self) -> None:
        a = detect_math_structure(
            "The O(n log n) algorithm satisfies d/dt H(t) = 0 with T >= 2.27K"
        )
        b = detect_math_structure(
            "The algorithm achieves O(n log n) through divide-and-conquer"
        )
        c = detect_math_structure("Sleep serves a metabolic clearance function")

        assert a["verifiability_score"] > 0.7
        assert b["verifiability_score"] < 0.7
        assert c["verifiability_score"] == 0.0


class TestShouldAttemptFormalVerification:
    def test_should_attempt_a_b_true_c_false(self) -> None:
        assert should_attempt_formal_verification(
            "The O(n log n) algorithm satisfies d/dt H(t) = 0 with T >= 2.27K"
        ) is True
        assert should_attempt_formal_verification(
            "The algorithm achieves O(n log n) through divide-and-conquer"
        ) is True
        assert should_attempt_formal_verification(
            "Sleep serves a metabolic clearance function"
        ) is False
