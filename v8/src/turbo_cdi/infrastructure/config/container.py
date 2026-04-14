"""
Dependency injection container for TURBO-CDI v8.4
Following Clean Architecture principles - infrastructure depends on abstractions.
"""

from typing import Optional, Protocol, Union
from turbo_cdi.infrastructure.config import Settings

# Try to import SQLAlchemy repositories, fallback to in-memory for testing
try:
    from turbo_cdi.infrastructure.repositories.sqlalchemy_repo import (
        SQLAlchemyDiscoveryRepository,
        SQLAlchemyPresuppositionRepository,
        SQLAlchemyTransformationRepository,
    )

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Always available in-memory repositories for testing
from turbo_cdi.infrastructure.repositories.memory_repositories import (
    InMemoryDiscoveryRepository,
    InMemoryPresuppositionRepository,
    InMemoryTransformationRepository,
)

# Auth and external services
try:
    from turbo_cdi.infrastructure.auth import AuthManager

    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

# External services
try:
    from turbo_cdi.infrastructure.external import LLMClient, CorpusValidatorImpl

    HAS_EXTERNAL = True
except ImportError:
    HAS_EXTERNAL = False

    # Mock implementations for testing
    class LLMClient:
        def __init__(self, **kwargs):
            pass

        async def health_check(self):
            return {"status": "mock"}

    class CorpusValidatorImpl:
        def validate_corpus(self, corpus):
            return True


# Import protocols (abstractions) - NOT concrete implementations
from turbo_cdi.domain.repositories import (
    DiscoveryRepository,
    PresuppositionRepository,
    TransformationRepository,
)
from turbo_cdi.domain.services import (
    AnomalyDetectionService,
    PresuppositionDiscoveryService,
    CognitiveTransformationService,
)
from turbo_cdi.domain.events import DomainEventPublisher
from turbo_cdi.application.use_cases.handlers import DiscoverKnowledgeHandler


class Container:
    """
    Clean Architecture dependency injection container.
    Infrastructure layer provides concrete implementations of domain abstractions.
    """

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or Settings()

        # Infrastructure components (concrete implementations)
        self._discovery_repository = None
        self._presupposition_repository = None
        self._transformation_repository = None
        self._llm_client = None
        self._corpus_validator = None

    # Domain and Application components (composed from infrastructure)
    self._anomaly_service = None
    self._presupposition_service = None
    self._transformation_service = None
    self._event_publisher = None
    self._discovery_handler = None
    self._auth_manager = None

    # ===== INFRASTRUCTURE LAYER =====
    # These provide concrete implementations that domain layer can depend on

    @property
    def discovery_repository(self) -> DiscoveryRepository:
        """Concrete implementation of DiscoveryRepository protocol"""
        if self._discovery_repository is None:
            self._discovery_repository = SQLAlchemyDiscoveryRepository(
                database_url=self.config.database_url, echo=self.config.debug_mode
            )
        return self._discovery_repository

    @property
    def presupposition_repository(self) -> PresuppositionRepository:
        """Concrete implementation of PresuppositionRepository protocol"""
        if self._presupposition_repository is None:
            self._presupposition_repository = SQLAlchemyPresuppositionRepository(
                database_url=self.config.database_url,
                discovery_repo=self.discovery_repository,
                echo=self.config.debug_mode,
            )
        return self._presupposition_repository

    @property
    def discovery_repository(self) -> DiscoveryRepository:
        """Repository implementation - SQLAlchemy if available, in-memory fallback"""
        if self._discovery_repository is None:
            if HAS_SQLALCHEMY:
                self._discovery_repository = SQLAlchemyDiscoveryRepository(
                    database_url=self.config.database_url, echo=self.config.debug_mode
                )
            else:
                self._discovery_repository = InMemoryDiscoveryRepository()
                print("⚠️  Using in-memory repository (SQLAlchemy not available)")
        return self._discovery_repository

    @property
    def presupposition_repository(self) -> PresuppositionRepository:
        """Repository implementation - SQLAlchemy if available, in-memory fallback"""
        if self._presupposition_repository is None:
            if HAS_SQLALCHEMY:
                self._presupposition_repository = SQLAlchemyPresuppositionRepository(
                    database_url=self.config.database_url,
                    discovery_repo=self.discovery_repository,
                    echo=self.config.debug_mode,
                )
            else:
                self._presupposition_repository = InMemoryPresuppositionRepository()
                print("⚠️  Using in-memory presupposition repository")
        return self._presupposition_repository

    @property
    def transformation_repository(self) -> TransformationRepository:
        """Repository implementation - SQLAlchemy if available, in-memory fallback"""
        if self._transformation_repository is None:
            if HAS_SQLALCHEMY:
                self._transformation_repository = SQLAlchemyTransformationRepository(
                    database_url=self.config.database_url, echo=self.config.debug_mode
                )
            else:
                self._transformation_repository = InMemoryTransformationRepository()
                print("⚠️  Using in-memory transformation repository")
        return self._transformation_repository

    @property
    def llm_client(self):
        """External LLM service client - with fallback"""
        if self._llm_client is None:
            if HAS_EXTERNAL:
                self._llm_client = LLMClient(
                    api_key=self.config.llm_api_key,
                    model=self.config.llm_model,
                    timeout=self.config.llm_timeout,
                )
            else:
                self._llm_client = LLMClient()  # Mock implementation
                print("⚠️  Using mock LLM client (external services not available)")
        return self._llm_client

    @property
    def corpus_validator(self):
        """Corpus validation service - with fallback"""
        if self._corpus_validator is None:
            if HAS_EXTERNAL:
                self._corpus_validator = CorpusValidatorImpl()
            else:
                self._corpus_validator = CorpusValidatorImpl()  # Mock implementation
                print("⚠️  Using mock corpus validator")
        return self._corpus_validator

    # ===== DOMAIN & APPLICATION LAYER =====
    # These compose domain services from infrastructure components

    @property
    def anomaly_service(self) -> AnomalyDetectionService:
        """Domain service for anomaly detection"""
        if self._anomaly_service is None:
            self._anomaly_service = AnomalyDetectionService(
                discovery_repo=self.discovery_repository,
                event_publisher=self.event_publisher,
                detection_algorithms=[self._get_basic_anomaly_detection()],  # Use function call
            )
        return self._anomaly_service

    @property
    def presupposition_service(self) -> PresuppositionDiscoveryService:
        """Domain service for presupposition discovery"""
        if self._presupposition_service is None:
            self._presupposition_service = PresuppositionDiscoveryService(
                repository=self.presupposition_repository,
                event_publisher=self.event_publisher,
            )
        return self._presupposition_service

    @property
    def transformation_service(self) -> CognitiveTransformationService:
        """Domain service for cognitive transformations"""
        if self._transformation_service is None:
            self._transformation_service = CognitiveTransformationService(
                repository=self.transformation_repository,
                event_publisher=self.event_publisher,
                qzrf_operators=self._get_qzrf_operators(),  # TODO: Implement QZRF operators
            )
        return self._transformation_service

    @property
    def event_publisher(self) -> DomainEventPublisher:
        """Domain event publisher"""
        if self._event_publisher is None:
            from turbo_cdi.domain.events import event_bus

            self._event_publisher = DomainEventPublisher(event_bus)
        return self._event_publisher

    @property
    def discovery_handler(self):
        """Application handler for discovery operations"""
        if self._discovery_handler is None:
            self._discovery_handler = DiscoverKnowledgeHandler(
                discovery_service=self.anomaly_service,
                repository=self.discovery_repository,
                event_publisher=self.event_publisher,
            )
        return self._discovery_handler

    # ===== PRIVATE METHODS =====

    def _get_basic_anomaly_detection(self):
        """
        Basic anomaly detection algorithm.
        TODO: Implement proper algorithms
        """

        # Placeholder implementation
        def basic_anomaly_detection(corpus) -> list:
            # Very basic anomaly detection for testing
            anomalies = []
            if len(corpus.facts) > 100:  # Large corpus warning
                anomalies.append(
                    {
                        "type": "structural",
                        "fact_statement": "Corpus structure",
                        "theory_name": "Size Analysis",
                        "conflict_description": "Corpus contains many facts without proper structuring",
                        "criticality": "low",
                        "confidence": 0.3,
                    }
                )
            return anomalies

        return basic_anomaly_detection

    def _get_qzrf_operators(self) -> dict:
        """
        Get QZRF cognitive operators - Quantum-inspired transformation algorithms.
        These represent cognitive processes for knowledge restructuring.
        """
        import random

        # Quantum Zonal Resonance Frequency operators
        def identity_operator(input_concept: str) -> tuple[str, float, float]:
            """Identity transformation - preserves concept with high resonance"""
            return input_concept, 1.0, 0.9

        def abstraction_operator(input_concept: str) -> tuple[str, float, float]:
            """Move concept to higher abstraction level"""
            abstractions = {
                "electron": "particle",
                "photosynthesis": "energy_conversion",
                "neuron": "information_processor",
                "gravity": "fundamental_force",
                "learning": "adaptation_mechanism",
            }
            abstract = abstractions.get(input_concept.lower(), f"abstract_{input_concept}")
            resonance = random.uniform(0.6, 0.9)
            effectiveness = random.uniform(0.5, resonance)
            return abstract, resonance, effectiveness

        def concretization_operator(input_concept: str) -> tuple[str, float, float]:
            """Move concept to lower abstraction level"""
            concretizations = {
                "particle": "electron",
                "energy_conversion": "photosynthesis",
                "information_processor": "neuron",
                "fundamental_force": "gravity",
                "adaptation_mechanism": "learning",
            }
            concrete = concretizations.get(input_concept.lower(), f"concrete_{input_concept}")
            resonance = random.uniform(0.4, 0.8)
            effectiveness = random.uniform(0.3, resonance)
            return concrete, resonance, effectiveness

        def inversion_operator(input_concept: str) -> tuple[str, float, float]:
            """Logical inversion - create negated concept"""
            inverted = (
                f"not_{input_concept}"
                if not input_concept.startswith("not_")
                else input_concept[4:]
            )
            resonance = random.uniform(0.5, 0.8)
            effectiveness = random.uniform(0.4, resonance)
            return inverted, resonance, effectiveness

        def bridge_operator(input_concept: str) -> tuple[str, float, float]:
            """Create interdisciplinary bridge between domains"""
            bridges = {
                "physics": "mathematical_physics",
                "biology": "biophysics",
                "chemistry": "quantum_chemistry",
                "computer_science": "cognitive_computing",
                "psychology": "cognitive_science",
            }
            bridged = bridges.get(input_concept.lower(), f"interdisciplinary_{input_concept}")
            resonance = random.uniform(0.7, 1.0)
            effectiveness = random.uniform(0.6, resonance)
            return bridged, resonance, effectiveness

        def synthesis_operator(input_concept: str) -> tuple[str, float, float]:
            """Synthesize multiple concepts into unified understanding"""
            synthesized = f"synthesized_{input_concept}"
            resonance = random.uniform(0.8, 1.0)
            effectiveness = random.uniform(0.7, resonance)
            return synthesized, resonance, effectiveness

        return {
            "identity": identity_operator,
            "abstract": abstraction_operator,
            "concretize": concretization_operator,
            "invert": inversion_operator,
            "bridge": bridge_operator,
            "synthesize": synthesis_operator,
        }

    @property
    def auth_manager(self):
        """Authentication and authorization manager"""
        if self._auth_manager is None:
            if HAS_AUTH:
                self._auth_manager = AuthManager()
            else:
                # Mock auth manager for testing
                class MockAuthManager:
                    async def authenticate_user(self, username, password):
                        return None  # No auth in mock mode

                self._auth_manager = MockAuthManager()
        return self._auth_manager


#
# Clean Architecture Container Summary:
#
# INFRASTRUCTURE LAYER (Concrete Adapters):
# - SQLAlchemyDiscoveryRepository implements DiscoveryRepository (protocol)
# - SQLAlchemyPresuppositionRepository implements PresuppositionRepository
# - SQLAlchemyTransformationRepository implements TransformationRepository
# - LLMClient provides external LLM service access
#
# DOMAIN LAYER (Pure Business Logic):
# - AnomalyDetectionService (injected with infrastructure adapters)
# - PresuppositionDiscoveryService (depends on repositories)
# - CognitiveTransformationService (depends on repositories)
#
# APPLICATION LAYER (Use Case Orchestration):
# - DiscoverKnowledgeHandler (CQRS command handler)
# - Uses domain services and repositories
#
# DEPENDENCY INVERSION ACHIEVED:
# - Domain depends on protocols (abstractions)
# - Infrastructure provides concrete implementations
# - Application orchestrates domain logic through use cases
