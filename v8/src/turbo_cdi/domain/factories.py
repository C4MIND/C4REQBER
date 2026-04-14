"""
Domain factories for creating complex domain entities.
"""

from typing import List, Optional
from turbo_cdi.domain.entities import (
    KnowledgeCorpus,
    CorpusId,
    Fact,
    Theory,
    Anomaly,
    AnomalyType,
    Severity,
)
from turbo_cdi.domain.entities.advanced import (
    Presupposition,
    PresuppositionId,
    PresuppositionType,
    Transformation,
    TransformationId,
    TransformationType,
)


class KnowledgeCorpusFactory:
    """Factory for creating KnowledgeCorpus instances"""

    @staticmethod
    def create_empty(
        corpus_id: str,
        name: str,
        domain: str,
        subdomains: Optional[List[str]] = None,
        epoch_end: str = "2024",
    ) -> KnowledgeCorpus:
        """Create empty corpus"""
        return KnowledgeCorpus(
            id=CorpusId(corpus_id),
            name=name,
            domain=domain,
            subdomains=tuple(subdomains or []),
            epoch_end=epoch_end,
        )

    @staticmethod
    def create_with_facts(
        corpus_id: str,
        name: str,
        domain: str,
        facts: List[Fact],
        theories: Optional[List[Theory]] = None,
        subdomains: Optional[List[str]] = None,
    ) -> KnowledgeCorpus:
        """Create corpus with initial facts"""
        return KnowledgeCorpus(
            id=CorpusId(corpus_id),
            name=name,
            domain=domain,
            subdomains=tuple(subdomains or []),
            facts=frozenset(facts),
            theories=frozenset(theories or []),
        )

    @staticmethod
    def create_from_dict(data: dict) -> KnowledgeCorpus:
        """Create corpus from dictionary data"""
        facts = []
        if "facts" in data:
            for f in data["facts"]:
                facts.append(
                    Fact(
                        id=f["id"],
                        statement=f["statement"],
                        source=f["source"],
                        year=f.get("year"),
                        domain=f["domain"],
                        confidence=f.get("confidence", 1.0),
                    )
                )

        theories = []
        if "theories" in data:
            for t in data["theories"]:
                theories.append(
                    Theory(id=t["id"], name=t["name"], principles=tuple(t["principles"]))
                )

        return KnowledgeCorpus(
            id=CorpusId(data["id"]),
            name=data["name"],
            domain=data["domain"],
            subdomains=tuple(data.get("subdomains", [])),
            epoch_end=data.get("epoch_end", "2024"),
            facts=frozenset(facts),
            theories=frozenset(theories),
        )


class PresuppositionFactory:
    """Factory for creating Presupposition instances"""

    @staticmethod
    def create_discovered(
        theory_id: str,
        theory_name: str,
        statement: str,
        presup_type: PresuppositionType,
        confidence: float = 0.8,
    ) -> Presupposition:
        """Create newly discovered presupposition"""
        return Presupposition(
            id=PresuppositionId(f"presup_{theory_id}_{hash(statement) % 10000}"),
            theory_id=theory_id,
            theory_name=theory_name,
            statement=statement,
            type=presup_type,
            confidence=confidence,
        )

    @staticmethod
    def create_from_analysis(
        theory_id: str, theory_name: str, analysis_result: dict
    ) -> Presupposition:
        """Create presupposition from LLM analysis result"""
        return Presupposition(
            id=PresuppositionId(
                f"presup_{theory_id}_{hash(analysis_result.get('statement', '')) % 10000}"
            ),
            theory_id=theory_id,
            theory_name=theory_name,
            statement=analysis_result.get("statement", ""),
            type=PresuppositionType(analysis_result.get("type", "ontological")),
            confidence=analysis_result.get("confidence", 0.8),
        )


class TransformationFactory:
    """Factory for creating Transformation instances"""

    @staticmethod
    def create_applied(
        transformation_type: TransformationType,
        input_concept: str,
        output_concept: str,
        domain: str,
        operator: str,
        resonance: float,
        effectiveness: float,
    ) -> Transformation:
        """Create transformation that was applied"""
        return Transformation(
            id=TransformationId(f"trans_{hash((input_concept, output_concept, operator)) % 10000}"),
            type=transformation_type,
            input_concept=input_concept,
            output_concept=output_concept,
            domain=domain,
            operator=operator,
            resonance=resonance,
            effectiveness=effectiveness,
        )

    @staticmethod
    def create_qzrf_transformation(
        from_state: str, to_state: str, domain: str, operator: str, resonance: float
    ) -> Transformation:
        """Create QZRF transformation"""
        return Transformation(
            id=TransformationId(f"qzrf_{hash((from_state, to_state, operator)) % 10000}"),
            type=TransformationType.BRIDGE,
            input_concept=from_state,
            output_concept=to_state,
            domain=domain,
            operator=operator,
            resonance=resonance,
            effectiveness=resonance * 0.9,  # Slightly less than resonance
        )


class AnomalyFactory:
    """Factory for creating Anomaly instances"""

    @staticmethod
    def create_detected(
        corpus_id: str,
        anomaly_type: AnomalyType,
        fact_statement: str,
        theory_name: str,
        conflict_description: str,
        criticality: Severity = Severity.MEDIUM,
        confidence: float = 0.8,
    ) -> Anomaly:
        """Create detected anomaly"""
        return Anomaly(
            id=f"anom_{corpus_id}_{hash((fact_statement, theory_name)) % 10000}",
            corpus_id=corpus_id,
            type=anomaly_type,
            fact_statement=fact_statement,
            theory_name=theory_name,
            conflict_description=conflict_description,
            criticality=criticality,
            confidence=confidence,
        )

    @staticmethod
    def create_from_llm_analysis(corpus_id: str, analysis_result: dict) -> Anomaly:
        """Create anomaly from LLM analysis"""
        return Anomaly(
            id=f"anom_{corpus_id}_{hash(analysis_result.get('fact_statement', '')) % 10000}",
            corpus_id=corpus_id,
            type=AnomalyType(analysis_result.get("type", "empirical")),
            fact_statement=analysis_result.get("fact_statement", ""),
            theory_name=analysis_result.get("theory_name", ""),
            conflict_description=analysis_result.get("conflict_description", ""),
            criticality=Severity(analysis_result.get("criticality", "medium")),
            confidence=analysis_result.get("confidence", 0.8),
        )


class KnowledgeCorpusBuilder:
    """Builder for creating complex KnowledgeCorpus with validation"""

    def __init__(self):
        self.corpus_id: Optional[str] = None
        self.name: Optional[str] = None
        self.domain: Optional[str] = None
        self.subdomains: List[str] = []
        self.epoch_end: str = "2024"
        self.facts: List[Fact] = []
        self.theories: List[Theory] = []
        self.anomalies: List[Anomaly] = []

    def with_id(self, corpus_id: str) -> "KnowledgeCorpusBuilder":
        """Set corpus ID"""
        self.corpus_id = corpus_id
        return self

    def with_name(self, name: str) -> "KnowledgeCorpusBuilder":
        """Set corpus name"""
        self.name = name
        return self

    def with_domain(self, domain: str) -> "KnowledgeCorpusBuilder":
        """Set corpus domain"""
        self.domain = domain
        return self

    def with_subdomains(self, subdomains: List[str]) -> "KnowledgeCorpusBuilder":
        """Set subdomains"""
        self.subdomains = subdomains
        return self

    def with_epoch_end(self, epoch_end: str) -> "KnowledgeCorpusBuilder":
        """Set epoch end"""
        self.epoch_end = epoch_end
        return self

    def add_fact(self, fact: Fact) -> "KnowledgeCorpusBuilder":
        """Add a fact"""
        self.facts.append(fact)
        return self

    def add_facts(self, facts: List[Fact]) -> "KnowledgeCorpusBuilder":
        """Add multiple facts"""
        self.facts.extend(facts)
        return self

    def add_theory(self, theory: Theory) -> "KnowledgeCorpusBuilder":
        """Add a theory"""
        self.theories.append(theory)
        return self

    def add_theories(self, theories: List[Theory]) -> "KnowledgeCorpusBuilder":
        """Add multiple theories"""
        self.theories.extend(theories)
        return self

    def add_anomaly(self, anomaly: Anomaly) -> "KnowledgeCorpusBuilder":
        """Add an anomaly"""
        self.anomalies.append(anomaly)
        return self

    def validate_and_build(self) -> KnowledgeCorpus:
        """Validate all components and build corpus"""
        if not self.corpus_id:
            raise ValueError("Corpus ID is required")
        if not self.name:
            raise ValueError("Corpus name is required")
        if not self.domain:
            raise ValueError("Corpus domain is required")

        # Validate facts have correct domain
        for fact in self.facts:
            if fact.domain != self.domain:
                raise ValueError(
                    f"Fact domain '{fact.domain}' does not match corpus domain '{self.domain}'"
                )

        # Validate consistency
        fact_statements = {f.statement for f in self.facts}
        theory_names = {t.name for t in self.theories}

        for anomaly in self.anomalies:
            if anomaly.fact_statement not in fact_statements:
                raise ValueError(
                    f"Anomaly fact statement not found in corpus facts: '{anomaly.fact_statement}'"
                )
            if anomaly.theory_name not in theory_names:
                raise ValueError(
                    f"Anomaly theory name not found in corpus theories: '{anomaly.theory_name}'"
                )

        return KnowledgeCorpus(
            id=CorpusId(self.corpus_id),
            name=self.name,
            domain=self.domain,
            subdomains=tuple(self.subdomains),
            epoch_end=self.epoch_end,
            facts=frozenset(self.facts),
            theories=frozenset(self.theories),
            anomalies=frozenset(self.anomalies),
        )


class PresuppositionBuilder:
    """Builder for creating complex Presupposition with validation"""

    def __init__(self):
        self.presup_id: Optional[str] = None
        self.theory_id: Optional[str] = None
        self.theory_name: Optional[str] = None
        self.statement: Optional[str] = None
        self.presup_type: Optional[PresuppositionType] = None
        self.confidence: float = 0.8

    def with_id(self, presup_id: str) -> "PresuppositionBuilder":
        """Set presupposition ID"""
        self.presup_id = presup_id
        return self

    def with_theory(self, theory_id: str, theory_name: str) -> "PresuppositionBuilder":
        """Set theory context"""
        self.theory_id = theory_id
        self.theory_name = theory_name
        return self

    def with_statement(self, statement: str) -> "PresuppositionBuilder":
        """Set presupposition statement"""
        self.statement = statement
        return self

    def with_type(self, presup_type: PresuppositionType) -> "PresuppositionBuilder":
        """Set presupposition type"""
        self.presup_type = presup_type
        return self

    def with_confidence(self, confidence: float) -> "PresuppositionBuilder":
        """Set confidence level"""
        self.confidence = confidence
        return self

    def validate_and_build(self) -> Presupposition:
        """Validate and build presupposition"""
        if not self.presup_id:
            if not (self.theory_id and self.statement):
                raise ValueError(
                    "Presupposition ID required or theory_id and statement for auto-generation"
                )
            self.presup_id = f"presup_{self.theory_id}_{hash(self.statement) % 10000}"

        if not self.theory_id or not self.theory_name:
            raise ValueError("Theory context (ID and name) is required")
        if not self.statement or not self.statement.strip():
            raise ValueError("Statement cannot be empty")
        if not self.presup_type:
            raise ValueError("Presupposition type is required")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        return Presupposition(
            id=PresuppositionId(self.presup_id),
            theory_id=self.theory_id,
            theory_name=self.theory_name,
            statement=self.statement,
            type=self.presup_type,
            confidence=self.confidence,
        )


class TransformationBuilder:
    """Builder for creating complex Transformation with validation"""

    def __init__(self):
        self.trans_id: Optional[str] = None
        self.transformation_type: Optional[TransformationType] = None
        self.input_concept: Optional[str] = None
        self.output_concept: Optional[str] = None
        self.domain: Optional[str] = None
        self.operator: Optional[str] = None
        self.resonance: float = 0.0
        self.effectiveness: float = 0.0

    def with_id(self, trans_id: str) -> "TransformationBuilder":
        """Set transformation ID"""
        self.trans_id = trans_id
        return self

    def with_type(self, trans_type: TransformationType) -> "TransformationBuilder":
        """Set transformation type"""
        self.transformation_type = trans_type
        return self

    def with_input_concept(self, concept: str) -> "TransformationBuilder":
        """Set input concept"""
        self.input_concept = concept
        return self

    def with_output_concept(self, concept: str) -> "TransformationBuilder":
        """Set output concept"""
        self.output_concept = concept
        return self

    def with_domain(self, domain: str) -> "TransformationBuilder":
        """Set domain"""
        self.domain = domain
        return self

    def with_operator(self, operator: str) -> "TransformationBuilder":
        """Set QZRF operator"""
        self.operator = operator
        return self

    def with_resonance(self, resonance: float) -> "TransformationBuilder":
        """Set resonance level"""
        self.resonance = resonance
        return self

    def with_effectiveness(self, effectiveness: float) -> "TransformationBuilder":
        """Set effectiveness level"""
        self.effectiveness = effectiveness
        return self

    def validate_and_build(self) -> Transformation:
        """Validate and build transformation"""
        if not self.trans_id:
            if not (self.input_concept and self.output_concept and self.operator):
                raise ValueError(
                    "Transformation ID required or concepts and operator for auto-generation"
                )
            self.trans_id = (
                f"trans_{hash((self.input_concept, self.output_concept, self.operator)) % 10000}"
            )

        required_attrs = [
            self.transformation_type,
            self.input_concept,
            self.output_concept,
            self.domain,
            self.operator,
        ]

        if any(attr is None for attr in required_attrs):
            raise ValueError("Transformation type, concepts, domain, and operator are required")

        if not self.input_concept.strip() or not self.output_concept.strip():
            raise ValueError("Input and output concepts cannot be empty")

        if not (0.0 <= self.resonance <= 1.0) or not (0.0 <= self.effectiveness <= 1.0):
            raise ValueError("Resonance and effectiveness must be between 0.0 and 1.0")

        return Transformation(
            id=TransformationId(self.trans_id),
            type=self.transformation_type,
            input_concept=self.input_concept,
            output_concept=self.output_concept,
            domain=self.domain,
            operator=self.operator,
            resonance=self.resonance,
            effectiveness=self.effectiveness,
        )
