"""
Business rules and domain invariants for TURBO-CDI v8.4
Enforcing domain constraints and validation logic.
"""

from typing import Optional
from turbo_cdi.domain.entities import KnowledgeCorpus, Fact, Theory, Anomaly
from turbo_cdi.domain.entities.advanced import Presupposition, Transformation


class BusinessRuleViolation(Exception):
    """Raised when business rules are violated"""

    pass


class DomainValidators:
    """Collection of domain validation rules"""

    @staticmethod
    def validate_corpus_consistency(corpus: KnowledgeCorpus) -> None:
        """
        Validate corpus internal consistency.

        Business Rules:
        - All facts must belong to corpus domain
        - Anomalies must reference existing facts and theories
        - Theories must be non-empty
        - Corpus ID must be valid format
        """
        # Validate corpus ID format
        if not corpus.id.startswith("corpus_"):
            raise BusinessRuleViolation("Corpus ID must start with 'corpus_'")

        # Validate facts domain consistency
        for fact in corpus.facts:
            if fact.domain != corpus.domain:
                raise BusinessRuleViolation(
                    f"Fact domain '{fact.domain}' does not match corpus domain '{corpus.domain}'"
                )

        # Validate theories are non-empty
        for theory in corpus.theories:
            if not theory.principles or not theory.equations:
                raise BusinessRuleViolation(
                    f"Theory '{theory.name}' must have principles and equations"
                )

        # Validate anomalies reference existing elements
        fact_statements = {f.statement for f in corpus.facts}
        theory_names = {t.name for t in corpus.theories}

        for anomaly in corpus.anomalies:
            if anomaly.fact_statement not in fact_statements:
                raise BusinessRuleViolation(
                    f"Anomaly fact statement not found in corpus: '{anomaly.fact_statement}'"
                )
            if anomaly.theory_name not in theory_names:
                raise BusinessRuleViolation(
                    f"Anomaly theory name not found in corpus: '{anomaly.theory_name}'"
                )

    @staticmethod
    def validate_presupposition_quality(presupposition: Presupposition) -> None:
        """
        Validate presupposition quality and validity.

        Business Rules:
        - Confidence must be above threshold
        - Statement must be non-trivial
        - Type must be appropriate for content
        """
        # Confidence threshold
        if presupposition.confidence < 0.1:
            raise BusinessRuleViolation("Presupposition confidence too low (<0.1)")

        # Statement non-triviality
        trivial_indicators = ["the", "a", "an", "is", "are"]
        words = presupposition.statement.lower().split()
        non_trivial_words = [w for w in words if w not in trivial_indicators]

        if len(non_trivial_words) < 2:
            raise BusinessRuleViolation("Presupposition statement too trivial")

        # Type validation
        from turbo_cdi.domain.entities.advanced import PresuppositionType

        if presupposition.type == PresuppositionType.AXIOLOGICAL:
            # Axiological presuppositions should contain value judgments
            value_words = ["good", "bad", "better", "worse", "valuable", "important", "moral"]
            if not any(word in presupposition.statement.lower() for word in value_words):
                raise BusinessRuleViolation(
                    "Axiological presupposition must contain value judgments"
                )

    @staticmethod
    def validate_transformation_effectiveness(transformation: Transformation) -> None:
        """
        Validate transformation effectiveness and parameters.

        Business Rules:
        - Effectiveness must be sufficient
        - Resonance and effectiveness relationship
        - Concepts must be meaningfully different
        """
        # Minimum effectiveness threshold
        if transformation.effectiveness < 0.3:
            raise BusinessRuleViolation("Transformation effectiveness below minimum threshold")

        # Resonance-effectiveness relationship
        if transformation.effectiveness > transformation.resonance * 1.2:
            raise BusinessRuleViolation("Effectiveness cannot exceed resonance by more than 20%")

        # Concept difference (prevent trivial transformations)
        if (
            transformation.input_concept.lower().strip()
            == transformation.output_concept.lower().strip()
        ):
            raise BusinessRuleViolation(
                "Transformation input and output concepts cannot be identical"
            )

        # Domain-specific validation
        if transformation.domain == "mathematics":
            # Mathematics domain should have clear mapping
            if not DomainValidators._has_mathematical_transformation(
                transformation.input_concept, transformation.output_concept
            ):
                raise BusinessRuleViolation("Mathematical transformation lacks clear mapping")

    @staticmethod
    def validate_anomaly_impact(anomaly: Anomaly, corpus: KnowledgeCorpus) -> None:
        """
        Validate anomaly impact and criticality assessment.

        Business Rules:
        - Critical anomalies must affect core theories
        - High confidence anomalies need detailed descriptions
        """

        # Critical anomalies validation
        if anomaly.criticality == "CRITICAL":
            # Critical anomalies should affect foundational theories
            theory_names = {t.name for t in corpus.theories}
            if anomaly.theory_name not in theory_names:
                raise BusinessRuleViolation("Critical anomaly must reference existing theory")

            # Should have detailed conflict description
            if len(anomaly.conflict_description.split()) < 10:
                raise BusinessRuleViolation(
                    "Critical anomalies need detailed conflict descriptions"
                )

        # High confidence anomalies validation
        if anomaly.confidence > 0.8 and len(anomaly.conflict_description.split()) < 5:
            raise BusinessRuleViolation(
                "High-confidence anomalies need adequate conflict descriptions"
            )

    @staticmethod
    def validate_knowledge_integrity(fact: Fact, theory: Theory) -> bool:
        """
        Validate logical consistency between fact and theory.

        Returns True if consistent, False if potential conflict.
        """
        # Simple consistency check based on domain keywords
        fact_lower = fact.statement.lower()
        theory_lower = " ".join(theory.principles).lower()

        # Check for direct contradictions (simple negation detection)
        negation_indicators = ["not", "no", "never", "cannot", "doesn't", "isn't"]

        for neg in negation_indicators:
            if neg in fact_lower and any(
                phrase in theory_lower for phrase in fact_lower.replace(neg, "").split()
            ):
                return False  # Potential contradiction

            if neg in theory_lower and any(
                phrase in fact_lower for phrase in theory_lower.replace(neg, "").split()
            ):
                return False  # Potential contradiction

        return True  # No obvious contradiction found

    @staticmethod
    def _has_mathematical_transformation(input_concept: str, output_concept: str) -> bool:
        """Check if mathematical concepts have transformation relationship"""
        # Simple validation for mathematical transformations
        math_indicators = [
            "equation",
            "function",
            "variable",
            "constant",
            "derivative",
            "integral",
            "limit",
            "summation",
            "matrix",
            "vector",
        ]

        input_has_math = any(indicator in input_concept.lower() for indicator in math_indicators)
        output_has_math = any(indicator in output_concept.lower() for indicator in math_indicators)

        # At least one concept should have mathematical indicators
        return input_has_math or output_has_math
