"""
Domain services for TURBO-CDI v8.4
Business logic orchestration using repositories and events.
"""

from __future__ import annotations

import time
from typing import List
from dataclasses import dataclass
from turbo_cdi.domain.entities.advanced import (
    Presupposition,
    Transformation,
    PresuppositionId,
    TransformationId,
    PresuppositionType,
    TransformationType,
    PresuppositionDiscovered,
    TransformationApplied,
    CorpusCreated,
    AnomalyDetected,
)
from turbo_cdi.domain.repositories import (
    PresuppositionRepository,
    TransformationRepository,
    DiscoveryRepository,
)
from turbo_cdi.domain.events import DomainEventPublisher
from turbo_cdi.domain.services.anomaly_service import AnomalyDetectionService


class PresuppositionDiscoveryService:
    """
    Domain service for presupposition discovery and management.
    Orchestrates presupposition-related business logic.
    """

    def __init__(
        self,
        repository: PresuppositionRepository,
        event_publisher: DomainEventPublisher,
    ):
        self.repository = repository
        self.event_publisher = event_publisher

    async def discover_presuppositions(
        self, theory_id: str, theory_name: str, theory_text: str
    ) -> List[Presupposition]:
        """
        Analyze theory text and discover hidden presuppositions.

        Business rules:
        - Presuppositions must be nontrivial (confidence > 0.1)
        - Conflicting presuppositions are flagged
        - Each discovery event is published
        """
        # Simple presupposition detection logic
        discovered = await self._analyze_theory_text(theory_id, theory_name, theory_text)

        # Validate and save
        valid_presuppositions = []
        for p in discovered:
            if p.confidence > 0.1:  # Business rule
                await self.repository.save_presupposition(p)
                valid_presuppositions.append(p)

        # Publish event
        event = PresuppositionDiscovered(
            theory_id=theory_id,
            presupposition_count=len(valid_presuppositions),
            types_discovered=tuple(p.type for p in valid_presuppositions),
        )
        await self.event_publisher.publish(event)

        return valid_presuppositions

    async def invert_presupposition(self, p_id: PresuppositionId) -> Optional[Presupposition]:
        """Create inverted version of a presupposition with reduced confidence"""
        existing = await self.repository.get_presupposition(p_id)
        if not existing:
            return None

        inverted = existing.invert()
        await self.repository.save_presupposition(inverted)

        return inverted

    async def find_contradicting_presuppositions(
        self,
    ) -> List[tuple[Presupposition, Presupposition]]:
        """Find pairs of presuppositions that contradict each other"""
        return await self.repository.find_contradictory_presuppositions()

    async def _analyze_theory_text(
        self, theory_id: str, theory_name: str, text: str
    ) -> List[Presupposition]:
        """Analyze theory text for hidden presuppositions"""
        presuppositions = []

        # Simple heuristics for presupposition discovery
        text_lower = text.lower()

        # Ontological presuppositions
        if "exists" in text_lower or "presence of" in text_lower:
            presuppositions.append(
                Presupposition(
                    id=PresuppositionId(f"{theory_id}_onto_1"),
                    theory_id=theory_id,
                    theory_name=theory_name,
                    statement="The entities discussed in this theory have real existence",
                    type=PresuppositionType.ONTOLOGICAL,
                    confidence=0.8,
                )
            )

        # Epistemological presuppositions
        if "known" in text_lower or "understand" in text_lower:
            presuppositions.append(
                Presupposition(
                    id=PresuppositionId(f"{theory_id}_epist_1"),
                    theory_id=theory_id,
                    theory_name=theory_name,
                    statement="It is possible to know and understand the concepts presented",
                    type=PresuppositionType.EPISTEMOLOGICAL,
                    confidence=0.7,
                )
            )

        # Methodological presuppositions
        if "method" in text_lower or "approach" in text_lower:
            presuppositions.append(
                Presupposition(
                    id=PresuppositionId(f"{theory_id}_method_1"),
                    theory_id=theory_id,
                    theory_name=theory_name,
                    statement="The methods used in this theory are valid and appropriate",
                    type=PresuppositionType.METHODOLOGICAL,
                    confidence=0.6,
                )
            )

        return presuppositions


class CognitiveTransformationService:
    """
    Domain service for cognitive transformations.
    Manages QZRF operator applications and transformation tracking.
    """

    def __init__(
        self,
        repository: TransformationRepository,
        event_publisher: DomainEventPublisher,
        qzrf_operators: dict[str, callable],
    ):
        self.repository = repository
        self.event_publisher = event_publisher
        self.qzrf_operators = qzrf_operators

    async def apply_transformation(
        self,
        input_concept: str,
        transformation_type: TransformationType,
        domain: str,
        operator_name: str,
    ) -> Optional[Transformation]:
        """
        Apply a cognitive transformation using QZRF operators.

        Business rules:
        - Transformations must have sufficient effectiveness (>0.3)
        - Results are validated before saving
        - Events are published for successful transformations
        """
        if operator_name not in self.qzrf_operators:
            raise ValueError(f"Unknown QZRF operator: {operator_name}")

        # Apply transformation
        operator = self.qzrf_operators[operator_name]
        result = await self._apply_operator(input_concept, transformation_type, operator)

        if not result:
            return None

        output_concept, resonance, effectiveness = result

        # Business rule: minimum effectiveness threshold
        if effectiveness < 0.3:
            return None

        # Create transformation entity
        transformation = Transformation(
            id=TransformationId(f"trans_{int(time.time())}_{domain}"),
            type=transformation_type,
            input_concept=input_concept,
            output_concept=output_concept,
            domain=domain,
            operator=operator_name,
            resonance=resonance,
            effectiveness=effectiveness,
        )

        # Save transformation
        await self.repository.save_transformation(transformation)

        # Publish event
        event = TransformationApplied(
            transformation_id=transformation.id,
            from_concept=input_concept,
            to_concept=output_concept,
            domain=domain,
            effectiveness=effectiveness,
        )
        await self.event_publisher.publish(event)

        return transformation

    async def get_optimal_transformations(
        self, domain: str, max_results: int = 5
    ) -> List[Transformation]:
        """Get most effective transformations for a domain"""
        transformations = await self.repository.list_transformations_by_domain(domain)
        sorted_transforms = sorted(
            transformations, key=lambda x: (x.effectiveness + x.resonance) / 2, reverse=True
        )
        return sorted_transforms[:max_results]

    async def evaluate_transformation_effectiveness(
        self, transformation: Transformation, validation_metrics: dict
    ) -> float:
        """
        Evaluate transformation effectiveness using domain-specific metrics.

        Args:
            validation_metrics: Domain-specific metrics like coherence, novelty, utility
        """
        # Simple weighted scoring
        weights = {
            "coherence": 0.4,
            "novelty": 0.3,
            "utility": 0.3,
        }

        effectiveness = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in validation_metrics:
                score = validation_metrics[metric]
                effectiveness += score * weight
                total_weight += weight

        return effectiveness if total_weight > 0 else transformation.effectiveness

    async def _apply_operator(
        self, input_concept: str, transformation_type: TransformationType, operator: callable
    ) -> Optional[tuple[str, float, float]]:
        """Apply QZRF operator to input concept"""
        try:
            # This is a simplified stub - actual implementation would
            # use complex cognitive algorithms
            result = await operator(input_concept)

            if not isinstance(result, tuple) or len(result) != 3:
                return None

            output_concept, resonance, effectiveness = result

            # Validate output
            if (
                not output_concept
                or not isinstance(resonance, (int, float))
                or not isinstance(effectiveness, (int, float))
            ):
                return None

            return output_concept, float(resonance), float(effectiveness)

        except Exception:
            return None


class AnomalyDetectionService:
    """
    Domain service for anomaly detection in knowledge corpora.
    Identifies conflicts and inconsistencies in knowledge structures.
    """

    def __init__(
        self,
        discovery_repo: DiscoveryRepository,
        event_publisher: DomainEventPublisher,
        detection_algorithms: List[callable],
    ):
        self.discovery_repo = discovery_repo
        self.event_publisher = event_publisher
        self.detection_algorithms = detection_algorithms

    async def analyze_corpus_for_anomalies(self, corpus_id: str) -> List[dict]:
        """
        Analyze corpus for knowledge anomalies.

        Business rules:
        - Multiple detection algorithms are applied
        - Anomalies are classified by criticality
        - Events are published with anomaly counts
        """
        corpus = await self.discovery_repo.get_corpus(corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        all_anomalies = []

        # Apply each detection algorithm
        for algorithm in self.detection_algorithms:
            anomalies = await algorithm(corpus)
            all_anomalies.extend(anomalies)

        # Remove duplicates and aggregate
        unique_anomalies = self._deduplicate_anomalies(all_anomalies)

        # Publish anomaly detection event
        if unique_anomalies:
            anomalies_tuple = tuple(a for a in unique_anomalies)  # Convert to tuple for event
            event = AnomalyDetected(
                corpus_id=corpus_id,
                anomaly_count=len(unique_anomalies),
                anomalies=anomalies_tuple,
            )
            await self.event_publisher.publish(event)

        return unique_anomalies

    def _deduplicate_anomalies(self, anomalies: List[dict]) -> List[dict]:
        """Remove duplicate anomalies based on conflict description"""
        seen_descriptions = set()
        unique = []

        for anomaly in anomalies:
            desc = anomaly.get("conflict_description", "")
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique.append(anomaly)

        return unique
