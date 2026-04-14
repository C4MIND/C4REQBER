"""
Command Handlers for TURBO-CDI v8.4 CQRS Implementation
Handles command execution with domain service orchestration.
"""

from __future__ import annotations

import time
from typing import Optional, List
from datetime import datetime

from turbo_cdi.application.use_cases.commands import (
    CreateCorpusCommand,
    UpdateCorpusCommand,
    DeleteCorpusCommand,
    DiscoverKnowledgeCommand,
    AnalyzePresuppositionsCommand,
    InvertPresuppositionCommand,
    ApplyTransformationCommand,
    OptimizeCorpusCommand,
    HealthCheckCommand,
    BaseResponse,
)
from turbo_cdi.application.dto import (
    CorpusResponseDTO,
    DiscoveryResponseDTO,
    PresuppositionAnalysisResponseDTO,
    TransformationResponseDTO,
    HealthCheckResponseDTO,
    CorpusDetailDTO,
    AnomalyDTO,
    PresuppositionDTO,
    TransformationDTO,
)
from turbo_cdi.domain.entities import CorpusId
from turbo_cdi.domain.entities.advanced import PresuppositionType, TransformationType
from turbo_cdi.domain.repositories import (
    DiscoveryRepository,
    PresuppositionRepository,
    TransformationRepository,
)
from turbo_cdi.domain.services import (
    PresuppositionDiscoveryService,
    CognitiveTransformationService,
    AnomalyDetectionService,
)
from turbo_cdi.domain.factories import KnowledgeCorpusFactory, KnowledgeCorpusBuilder
from turbo_cdi.domain.events import DomainEventPublisher


# Base Handler
class CommandHandler:
    """Base class for command handlers"""

    def __init__(self, event_publisher: Optional[DomainEventPublisher] = None):
        self.event_publisher = event_publisher


# Corpus Command Handlers
class CreateCorpusHandler(CommandHandler):
    """Handles corpus creation commands"""

    def __init__(
        self,
        repository: DiscoveryRepository,
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.repository = repository

    async def handle(self, command: CreateCorpusCommand) -> CorpusResponseDTO:
        """Handle corpus creation"""
        try:
            corpus_id = CorpusId(command.request.id)

            # Check if corpus already exists
            existing = await self.repository.get_corpus(corpus_id)
            if existing:
                return CorpusResponseDTO(
                    status="error", message=f"Corpus {corpus_id} already exists", corpus=None
                )

            # Create corpus using factory
            corpus = KnowledgeCorpusFactory.create_empty(
                corpus_id=command.request.id,
                name=command.request.name,
                domain=command.request.domain,
                subdomains=command.request.subdomains,
                epoch_end=command.request.epoch_end,
            )

            # Save to repository
            await self.repository.save_corpus(corpus)

            # Create response DTO
            corpus_dto = CorpusDetailDTO.from_entity(corpus)
            response = CorpusResponseDTO(
                status="success", message="Corpus created successfully", corpus=corpus_dto
            )

            # TODO: Publish domain events when event system is fully implemented

            return response

        except Exception as e:
            return CorpusResponseDTO(
                status="error", message=f"Failed to create corpus: {str(e)}", corpus=None
            )


class UpdateCorpusHandler(CommandHandler):
    """Handles corpus update commands"""

    def __init__(
        self,
        repository: DiscoveryRepository,
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.repository = repository

    async def handle(self, command: UpdateCorpusCommand) -> CorpusResponseDTO:
        """Handle corpus update"""
        try:
            corpus_id = CorpusId(command.corpus_id)
            corpus = await self.repository.get_corpus(corpus_id)

            if not corpus:
                return CorpusResponseDTO(
                    status="error", message=f"Corpus {corpus_id} not found", corpus=None
                )

            # Update fields if provided
            updated_name = command.name or corpus.name
            updated_domain = command.domain or corpus.domain
            updated_subdomains = (
                command.subdomains if command.subdomains is not None else corpus.subdomains
            )

            # Create updated corpus (immutable, so we create new instance)
            # For now, we'll recreate it - in practice you'd have update methods
            updated_corpus = KnowledgeCorpusFactory.create_empty(
                corpus_id=command.corpus_id,
                name=updated_name,
                domain=updated_domain,
                subdomains=updated_subdomains,
                epoch_end=corpus.epoch_end,
            )

            # Transfer facts, theories, anomalies from original
            if corpus.facts:
                updated_corpus = updated_corpus.add_facts(list(corpus.facts))
            if corpus.theories:
                updated_corpus = updated_corpus.add_theories(list(corpus.theories))
            if corpus.anomalies:
                updated_corpus = updated_corpus.add_anomalies(list(corpus.anomalies))

            await self.repository.save_corpus(updated_corpus)

            corpus_dto = CorpusDetailDTO.from_entity(updated_corpus)
            return CorpusResponseDTO(
                status="success", message="Corpus updated successfully", corpus=corpus_dto
            )

        except Exception as e:
            return CorpusResponseDTO(
                status="error", message=f"Failed to update corpus: {str(e)}", corpus=None
            )


class DeleteCorpusHandler(CommandHandler):
    """Handles corpus deletion commands"""

    def __init__(
        self,
        repository: DiscoveryRepository,
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.repository = repository

    async def handle(self, command: DeleteCorpusCommand) -> BaseResponse:
        """Handle corpus deletion"""
        try:
            corpus_id = CorpusId(command.corpus_id)

            # Check if corpus exists
            corpus = await self.repository.get_corpus(corpus_id)
            if not corpus:
                return BaseResponse(status="error", message=f"Corpus {corpus_id} not found")

            # Delete corpus
            await self.repository.delete_corpus(corpus_id)

            return BaseResponse(
                status="success", message=f"Corpus {corpus_id} deleted successfully"
            )

        except Exception as e:
            return BaseResponse(status="error", message=f"Failed to delete corpus: {str(e)}")


# Discovery Command Handler
class DiscoverKnowledgeHandler(CommandHandler):
    """Handles knowledge discovery commands"""

    def __init__(
        self,
        discovery_service: AnomalyDetectionService,
        repository: DiscoveryRepository,
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.discovery_service = discovery_service
        self.repository = repository

    async def handle(self, command: DiscoverKnowledgeCommand) -> DiscoveryResponseDTO:
        """Handle knowledge discovery"""
        start_time = time.time()

        try:
            corpus_id = CorpusId(command.request.corpus_id)
            corpus = await self.repository.get_corpus(corpus_id)

            if not corpus:
                return DiscoveryResponseDTO(
                    status="error",
                    message=f"Corpus {corpus_id} not found",
                    corpus_id=command.request.corpus_id,
                    anomalies=[],
                    anomaly_count=0,
                    processing_time=round(time.time() - start_time, 2),
                )

            # Run anomaly detection
            anomalies = await self.discovery_service.analyze_corpus_for_anomalies(
                command.request.corpus_id
            )

            # Convert to DTOs
            anomaly_dtos = [AnomalyDTO.from_entity(a) for a in anomalies]

            processing_time = time.time() - start_time

            return DiscoveryResponseDTO(
                status="success",
                message=f"Discovery completed, found {len(anomalies)} anomalies",
                corpus_id=command.request.corpus_id,
                anomalies=anomaly_dtos,
                anomaly_count=len(anomalies),
                processing_time=round(processing_time, 2),
            )

        except Exception as e:
            return DiscoveryResponseDTO(
                status="error",
                message=f"Discovery failed: {str(e)}",
                corpus_id=command.request.corpus_id,
                anomalies=[],
                anomaly_count=0,
                processing_time=round(time.time() - start_time, 2),
            )


# Presupposition Command Handler
class AnalyzePresuppositionsHandler(CommandHandler):
    """Handles presupposition analysis commands"""

    def __init__(
        self,
        presupposition_service: PresuppositionDiscoveryService,
        repository: PresuppositionRepository,
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.presupposition_service = presupposition_service
        self.repository = repository

    async def handle(
        self, command: AnalyzePresuppositionsCommand
    ) -> PresuppositionAnalysisResponseDTO:
        """Handle presupposition analysis"""
        try:
            # Discover presuppositions
            presuppositions = await self.presupposition_service.discover_presuppositions(
                theory_id=command.request.theory_id,
                theory_name="Unknown Theory",  # Would be looked up in real implementation
                theory_text=command.request.theory_text,
            )

            # Convert to DTOs
            presupposition_dtos = [PresuppositionDTO.from_entity(p) for p in presuppositions]

            # Calculate analysis score
            avg_confidence = (
                sum(p.confidence for p in presuppositions) / len(presuppositions)
                if presuppositions
                else 0.0
            )

            return PresuppositionAnalysisResponseDTO(
                status="success",
                message=f"Found {len(presuppositions)} presuppositions",
                theory_id=command.request.theory_id,
                presuppositions=presupposition_dtos,
                analysis_score=round(avg_confidence, 2),
            )

        except Exception as e:
            return PresuppositionAnalysisResponseDTO(
                status="error",
                message=f"Presupposition analysis failed: {str(e)}",
                theory_id=command.request.theory_id,
                presuppositions=[],
                analysis_score=0.0,
            )


# Transformation Command Handler
class ApplyTransformationHandler(CommandHandler):
    """Handles transformation commands"""

    def __init__(
        self,
        transformation_service: CognitiveTransformationService,
        repository: TransformationRepository,
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.transformation_service = transformation_service
        self.repository = repository

    async def handle(self, command: ApplyTransformationCommand) -> TransformationResponseDTO:
        """Handle transformation application"""
        try:
            # Map string to enum
            trans_type_mapping = {
                "invert": TransformationType.INVERT,
                "bridge": TransformationType.BRIDGE,
                "synthesize": TransformationType.SYNTHESIZE,
                "abstract": TransformationType.ABSTRACT,
                "concretize": TransformationType.CONCRETIZE,
            }

            transformation_type = trans_type_mapping.get(command.request.transformation_type)
            if not transformation_type:
                return TransformationResponseDTO(
                    status="error",
                    message=f"Invalid transformation type: {command.request.transformation_type}",
                    transformation=None,
                    transformation_applied=False,
                )

            # Apply transformation
            transformation = await self.transformation_service.apply_transformation(
                input_concept=command.request.input_concept,
                transformation_type=transformation_type,
                domain=command.request.domain,
                operator_name=command.request.operator,
            )

            if transformation:
                transformation_dto = TransformationDTO.from_entity(transformation)
                return TransformationResponseDTO(
                    status="success",
                    message="Transformation applied successfully",
                    transformation=transformation_dto,
                    transformation_applied=True,
                )
            else:
                return TransformationResponseDTO(
                    status="success",
                    message="Transformation was not effective enough",
                    transformation=None,
                    transformation_applied=False,
                )

        except Exception as e:
            return TransformationResponseDTO(
                status="error",
                message=f"Transformation failed: {str(e)}",
                transformation=None,
                transformation_applied=False,
            )


# Health Check Handler
class HealthCheckHandler(CommandHandler):
    """Handles health check commands"""

    def __init__(
        self,
        repositories: dict[str, any],  # service_name -> repository instance
        event_publisher: Optional[DomainEventPublisher] = None,
    ):
        super().__init__(event_publisher)
        self.repositories = repositories

    async def handle(self, command: HealthCheckCommand) -> HealthCheckResponseDTO:
        """Handle health check"""
        services_status = {}
        overall_health = "healthy"

        # Check each repository
        for service_name, repo in self.repositories.items():
            try:
                if hasattr(repo, "health_check"):
                    health_result = await repo.health_check()
                    services_status[service_name] = health_result.get("status", "unknown")
                else:
                    services_status[service_name] = "unknown"

                # If any service is unhealthy, overall health is unhealthy
                if health_result.get("status") not in ["healthy", "success"]:
                    overall_health = "unhealthy"

            except Exception as e:
                services_status[service_name] = f"error: {str(e)}"
                overall_health = "unhealthy"

        message = f"System health: {overall_health}"

        if command.include_detailed and overall_health == "unhealthy":
            unhealthy_services = [
                name
                for name, status in services_status.items()
                if status not in ["healthy", "success"]
            ]
            message += f". Unhealthy services: {', '.join(unhealthy_services)}"

        return HealthCheckResponseDTO(
            status="success" if overall_health == "healthy" else "warning",
            message=message,
            services=services_status,
            overall_health=overall_health,
        )


# Command Bus (Mediator Pattern)
class CommandBus:
    """Command bus for routing commands to handlers"""

    def __init__(self):
        self.handlers: dict[type, CommandHandler] = {}

    def register(self, command_type: type, handler: CommandHandler):
        """Register a handler for a command type"""
        self.handlers[command_type] = handler

    async def execute(self, command: any) -> any:
        """Execute a command using its registered handler"""
        handler = self.handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler registered for command type {type(command)}")

        return await handler.handle(command)
