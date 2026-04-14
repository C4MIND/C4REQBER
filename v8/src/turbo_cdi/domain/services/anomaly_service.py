"""
Enhanced Anomaly Detection Service for TURBO-CDI v8.4
Production-ready implementation with multiple detection algorithms.
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Callable
from datetime import datetime

from turbo_cdi.domain.entities import KnowledgeCorpus, Anomaly, AnomalyType, Severity
from turbo_cdi.domain.repositories import DiscoveryRepository
from turbo_cdi.domain.events import DomainEventPublisher
from turbo_cdi.domain.entities.advanced import AnomalyDetected


class AnomalyDetectionService:
    """
    Domain service for anomaly detection in knowledge corpora.
    Implements multiple detection algorithms with configurable sensitivity.
    """

    def __init__(
        self,
        discovery_repo: DiscoveryRepository,
        event_publisher: DomainEventPublisher,
        detection_algorithms: List[Callable],
        min_confidence_threshold: float = 0.6,
    ):
        self.discovery_repo = discovery_repo
        self.event_publisher = event_publisher
        self.detection_algorithms = detection_algorithms
        self.min_confidence_threshold = min_confidence_threshold

    async def analyze_corpus_for_anomalies(
        self, corpus_id: str, algorithms: List[str] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Run anomaly detection analysis on a knowledge corpus.

        Args:
            corpus_id: ID of corpus to analyze
            algorithms: Specific algorithms to run (None = all)
            **kwargs: Algorithm-specific parameters

        Returns:
            List of detected anomalies as dictionaries
        """
        # Retrieve corpus
        from turbo_cdi.domain.entities import CorpusId

        corpus = await self.discovery_repo.get_corpus(CorpusId(corpus_id))
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        detected_anomalies = []
        execution_start = time.time()

        # Run all detection algorithms
        algorithms_to_run = algorithms or ["statistical", "logical", "semantic", "structural"]

        for algorithm_name in algorithms_to_run:
            if algorithm_name == "statistical":
                anomalies = await self._statistical_anomaly_detection(corpus, **kwargs)
            elif algorithm_name == "logical":
                anomalies = await self._logical_anomaly_detection(corpus, **kwargs)
            elif algorithm_name == "semantic":
                anomalies = await self._semantic_anomaly_detection(corpus, **kwargs)
            elif algorithm_name == "structural":
                anomalies = await self._structural_anomaly_detection(corpus, **kwargs)
            else:
                continue

            detected_anomalies.extend(anomalies)

        # Remove duplicates and filter by confidence
        unique_anomalies = self._deduplicate_anomalies(detected_anomalies)
        filtered_anomalies = [
            a for a in unique_anomalies if a.get("confidence", 0) >= self.min_confidence_threshold
        ]

        # Publish domain event if anomalies detected
        if filtered_anomalies:
            # Convert to event format (simplified)
            anomaly_summaries = [
                {
                    "type": a["type"],
                    "fact_statement": a["fact_statement"],
                    "theory_name": a["theory_name"],
                    "conflict_description": a["conflict_description"],
                }
                for a in filtered_anomalies
            ]

            event = AnomalyDetected(
                corpus_id=corpus_id,
                anomaly_count=len(filtered_anomalies),
                anomalies=anomaly_summaries,
            )
            await self.event_publisher.publish(event)

        execution_time = time.time() - execution_start

        return {
            "corpus_id": corpus_id,
            "anomalies_found": len(filtered_anomalies),
            "anomalies": filtered_anomalies,
            "execution_time": round(execution_time, 3),
            "algorithms_used": algorithms_to_run,
        }

    async def _statistical_anomaly_detection(self, corpus: KnowledgeCorpus, **kwargs) -> List[Dict]:
        """Statistical anomaly detection based on knowledge patterns"""
        anomalies = []

        # Check for facts without sources
        for fact in corpus.facts:
            if not fact.source or fact.source.strip() == "":
                anomalies.append(
                    {
                        "type": "empirical",
                        "fact_statement": fact.statement,
                        "theory_name": "All Theories",  # Affects all theories
                        "conflict_description": f"Fact '{fact.statement}' has no source citation",
                        "criticality": "low",
                        "confidence": 0.8,
                        "detected_at": datetime.now(),
                    }
                )

        # Check for overly confident facts (potential bias)
        confidence_threshold = kwargs.get("confidence_threshold", 0.95)
        for fact in corpus.facts:
            if getattr(fact, "confidence", 1.0) > confidence_threshold:
                anomalies.append(
                    {
                        "type": "empirical",
                        "fact_statement": fact.statement,
                        "theory_name": "Quality Assessment",
                        "conflict_description": f"Fact has very high confidence ({getattr(fact, 'confidence', 1.0):.2f}) - potential overconfidence",
                        "criticality": "medium",
                        "confidence": 0.6,
                        "detected_at": datetime.now(),
                    }
                )

        return anomalies

    async def _logical_anomaly_detection(self, corpus: KnowledgeCorpus, **kwargs) -> List[Dict]:
        """Logical consistency checking across facts and theories"""
        anomalies = []

        # Check for contradictory facts (simple text-based detection)
        fact_statements = [fact.statement.lower() for fact in corpus.facts]

        for i, fact1 in enumerate(corpus.facts):
            for fact2 in corpus.facts[i + 1 :]:
                if self._statements_are_contradictory(fact1.statement, fact2.statement):
                    anomalies.append(
                        {
                            "type": "logical",
                            "fact_statement": fact1.statement,
                            "theory_name": "Consistency Check",
                            "conflict_description": f"Contradictory facts: '{fact1.statement}' vs '{fact2.statement}'",
                            "criticality": "high",
                            "confidence": 0.9,
                            "detected_at": datetime.now(),
                        }
                    )

        # Check theory internal consistency
        for theory in corpus.theories:
            consistency_issues = self._check_theory_consistency(theory)
            if consistency_issues:
                for issue in consistency_issues:
                    anomalies.append(
                        {
                            "type": "logical",
                            "fact_statement": f"Theory '{theory.name}' principles",
                            "theory_name": theory.name,
                            "conflict_description": issue,
                            "criticality": "medium",
                            "confidence": 0.7,
                            "detected_at": datetime.now(),
                        }
                    )

        return anomalies

    async def _semantic_anomaly_detection(self, corpus: KnowledgeCorpus, **kwargs) -> List[Dict]:
        """Semantic analysis for knowledge coherence"""
        anomalies = []

        # Check domain consistency
        corpus_domain = corpus.domain.lower()
        for fact in corpus.facts:
            if corpus_domain not in fact.domain.lower():
                anomalies.append(
                    {
                        "type": "semantic",
                        "fact_statement": fact.statement,
                        "theory_name": f"{corpus_domain.title()} Domain Consistency",
                        "conflict_description": f"Fact domain '{fact.domain}' doesn't match corpus domain '{corpus.domain}'",
                        "criticality": "medium",
                        "confidence": 0.8,
                        "detected_at": datetime.now(),
                    }
                )

        # TODO: Add more sophisticated semantic analysis
        # - Concept relationship validation
        # - Domain ontology compliance
        # - Cross-reference verification

        return anomalies

    async def _structural_anomaly_detection(self, corpus: KnowledgeCorpus, **kwargs) -> List[Dict]:
        """Structural analysis of knowledge organization"""
        anomalies = []

        # Check for isolated facts (not referenced by any theory)
        fact_statements = {fact.statement for fact in corpus.facts}
        referenced_facts = set()

        for theory in corpus.theories:
            # Simple text matching for fact references in theories
            theory_text = f"{theory.name} {' '.join(getattr(theory, 'principles', []))}"
            for fact in corpus.facts:
                if fact.statement.lower() in theory_text.lower():
                    referenced_facts.add(fact.statement)

        unreferenced_facts = fact_statements - referenced_facts
        for fact_statement in unreferenced_facts:
            anomalies.append(
                {
                    "type": "structural",
                    "fact_statement": fact_statement,
                    "theory_name": "Knowledge Structure",
                    "conflict_description": "Fact is not referenced by any theory - potential knowledge gap",
                    "criticality": "low",
                    "confidence": 0.5,
                    "detected_at": datetime.now(),
                }
            )

        return anomalies

    def _deduplicate_anomalies(self, anomalies: List[Dict]) -> List[Dict]:
        """Remove duplicate anomalies based on conflict description"""
        seen_descriptions = set()
        unique = []

        for anomaly in sorted(anomalies, key=lambda x: x.get("confidence", 0), reverse=True):
            desc = anomaly.get("conflict_description", "")
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique.append(anomaly)

        return unique

    def _statements_are_contradictory(self, stmt1: str, stmt2: str) -> bool:
        """Simple contradiction detection between statements"""
        # Very basic implementation - in reality would use NLP
        stmt1_lower = stmt1.lower()
        stmt2_lower = stmt2.lower()

        contradiction_pairs = [
            ("true", "false"),
            ("yes", "no"),
            ("positive", "negative"),
            ("exists", "not exists"),
            ("present", "absent"),
        ]

        for pos, neg in contradiction_pairs:
            if pos in stmt1_lower and neg in stmt2_lower:
                return True
            if neg in stmt1_lower and pos in stmt2_lower:
                return True

        return False

    def _check_theory_consistency(self, theory) -> List[str]:
        """Check internal consistency of a theory"""
        issues = []

        # Get theory principles
        principles = getattr(theory, "principles", [])
        if not principles:
            issues.append("Theory has no principles defined")
            return issues

        # Check for self-contradictory principles
        principle_texts = [str(p).lower() for p in principles]
        for i, p1 in enumerate(principle_texts):
            for p2 in principle_texts[i + 1 :]:
                if self._statements_are_contradictory(p1, p2):
                    issues.append(f"Contradictory principles: '{p1}' vs '{p2}'")

        return issues

    async def get_detection_statistics(self) -> Dict[str, Any]:
        """Get statistics about anomaly detection performance"""
        return {
            "total_analyses": 0,  # TODO: Track actual metrics
            "average_anomalies_found": 0,
            "most_common_anomaly_types": [],
            "average_confidence": 0,
            "algorithms_available": ["statistical", "logical", "semantic", "structural"],
        }
