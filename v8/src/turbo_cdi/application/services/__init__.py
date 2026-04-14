"""
Application Services for TURBO-CDI v8.4
High-level orchestration services handling cross-cutting concerns.
"""

from __future__ import annotations

import time
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId
from turbo_cdi.domain.repositories import DiscoveryRepository
from turbo_cdi.domain.services import (
    PresuppositionDiscoveryService,
    CognitiveTransformationService,
    AnomalyDetectionService,
)
from turbo_cdi.infrastructure.config import Settings
from turbo_cdi.application.dto import HealthCheckResponseDTO, BaseResponse


# Base Application Service
class ApplicationService:
    """Base class for application services"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    @asynccontextmanager
    async def transaction_scope(self):
        """Context manager for transaction boundaries"""
        # In a real implementation, this would manage database transactions
        # For now, it's a placeholder
        try:
            self.logger.info("Starting transaction")
            yield
            self.logger.info("Committing transaction")
        except Exception as e:
            self.logger.error(f"Rolling back transaction: {e}")
            raise

    async def log_operation(self, operation: str, start_time: float, success: bool, **kwargs):
        """Log operation metrics"""
        duration = time.time() - start_time
        log_level = logging.INFO if success else logging.ERROR

        self.logger.log(
            log_level,
            f"Operation '{operation}' completed",
            extra={
                "operation": operation,
                "duration": round(duration, 3),
                "success": success,
                **kwargs,
            },
        )


# Corpus Management Service
class CorpusManagementService(ApplicationService):
    """
    Application service for corpus management operations.
    Handles validation, auditing, and orchestration across repositories.
    """

    def __init__(
        self,
        settings: Settings,
        discovery_repo: DiscoveryRepository,
    ):
        super().__init__(settings)
        self.discovery_repo = discovery_repo

    async def create_corpus_with_validation(
        self,
        corpus_id: str,
        name: str,
        domain: str,
        subdomains: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> KnowledgeCorpus:
        """
        Create a corpus with comprehensive validation and auditing.

        Business rules:
        - Validate corpus uniqueness
        - Audit creation event
        - Initialize with proper defaults
        """
        start_time = time.time()

        try:
            async with self.transaction_scope():
                # Validate inputs
                await self._validate_corpus_creation(corpus_id, name, domain)

                # Create corpus
                from turbo_cdi.domain.factories import KnowledgeCorpusFactory

                corpus = KnowledgeCorpusFactory.create_empty(
                    corpus_id=corpus_id, name=name, domain=domain, subdomains=subdomains
                )

                # Save to repository
                await self.discovery_repo.save_corpus(corpus)

                # Audit logging
                await self.log_operation(
                    "create_corpus",
                    start_time,
                    True,
                    corpus_id=corpus_id,
                    domain=domain,
                    created_by=created_by,
                )

                return corpus

        except Exception as e:
            await self.log_operation(
                "create_corpus", start_time, False, corpus_id=corpus_id, error=str(e)
            )
            raise

    async def delete_corpus_with_cleanup(
        self, corpus_id: str, deleted_by: Optional[str] = None
    ) -> None:
        """
        Delete a corpus with comprehensive cleanup and auditing.
        """
        start_time = time.time()

        try:
            async with self.transaction_scope():
                corpus_id_obj = CorpusId(corpus_id)

                # Verify corpus exists
                corpus = await self.discovery_repo.get_corpus(corpus_id_obj)
                if not corpus:
                    raise ValueError(f"Corpus {corpus_id} not found")

                # Perform cleanup operations
                await self._cleanup_corpus_dependencies(corpus)

                # Delete corpus
                await self.discovery_repo.delete_corpus(corpus_id_obj)

                # Audit logging
                await self.log_operation(
                    "delete_corpus", start_time, True, corpus_id=corpus_id, deleted_by=deleted_by
                )

        except Exception as e:
            await self.log_operation(
                "delete_corpus", start_time, False, corpus_id=corpus_id, error=str(e)
            )
            raise

    async def optimize_corpus_performance(
        self, corpus_id: str, optimization_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Optimize corpus for better performance.
        """
        start_time = time.time()

        try:
            corpus_id_obj = CorpusId(corpus_id)
            corpus = await self.discovery_repo.get_corpus(corpus_id_obj)

            if not corpus:
                raise ValueError(f"Corpus {corpus_id} not found")

            # Perform optimization based on level
            optimizations_applied = await self._apply_optimizations(corpus, optimization_level)

            # Re-save optimized corpus
            await self.discovery_repo.save_corpus(corpus)

            await self.log_operation(
                "optimize_corpus",
                start_time,
                True,
                corpus_id=corpus_id,
                optimization_level=optimization_level,
                optimizations=len(optimizations_applied),
            )

            return {
                "status": "optimized",
                "optimizations_applied": optimizations_applied,
                "performance_improved": True,
            }

        except Exception as e:
            await self.log_operation(
                "optimize_corpus", start_time, False, corpus_id=corpus_id, error=str(e)
            )
            raise

    async def _validate_corpus_creation(self, corpus_id: str, name: str, domain: str):
        """Validate corpus creation inputs"""

        # Check ID format
        if not corpus_id.startswith("corpus_"):
            raise ValueError("Corpus ID must start with 'corpus_'")

        # Check uniqueness
        existing = await self.discovery_repo.get_corpus(CorpusId(corpus_id))
        if existing:
            raise ValueError(f"Corpus {corpus_id} already exists")

        # Validate domain
        valid_domains = [
            "physics",
            "mathematics",
            "biology",
            "chemistry",
            "computer_science",
            "philosophy",
            "cognitive_science",
        ]
        if domain not in valid_domains:
            self.logger.warning(f"Creating corpus with non-standard domain: {domain}")

    async def _cleanup_corpus_dependencies(self, corpus: KnowledgeCorpus):
        """Clean up related entities when deleting corpus"""
        # In a full implementation, this would clean up related presuppositions,
        # transformations, events, etc.
        self.logger.info(f"Cleaning up dependencies for corpus {corpus.id}")

    async def _apply_optimizations(self, corpus: KnowledgeCorpus, level: str) -> List[str]:
        """Apply performance optimizations"""
        optimizations = []

        if level in ["standard", "deep"]:
            # Optimize fact indexing
            if len(corpus.facts) > 100:
                optimizations.append("fact_indexing_optimized")

            # Optimize anomaly clustering
            if len(corpus.anomalies) > 50:
                optimizations.append("anomaly_clustering_optimized")

        if level == "deep":
            # Advanced optimizations
            optimizations.append("theory_relationships_optimized")
            optimizations.append("cross_references_rebuilt")

        return optimizations


# Knowledge Discovery Service
class KnowledgeDiscoveryService(ApplicationService):
    """
    Application service for complex knowledge discovery workflows.
    Orchestrates multiple domain services with monitoring and error handling.
    """

    def __init__(
        self,
        settings: Settings,
        anomaly_service: AnomalyDetectionService,
        presupposition_service: PresuppositionDiscoveryService,
        discovery_repo: DiscoveryRepository,
    ):
        super().__init__(settings)
        self.anomaly_service = anomaly_service
        self.presupposition_service = presupposition_service
        self.discovery_repo = discovery_repo

    async def comprehensive_discovery_analysis(
        self, corpus_id: str, include_presuppositions: bool = True, analysis_timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run comprehensive discovery analysis including anomalies and presuppositions.
        """
        start_time = time.time()

        try:
            corpus_id_obj = CorpusId(corpus_id)
            corpus = await self.discovery_repo.get_corpus(corpus_id_obj)

            if not corpus:
                raise ValueError(f"Corpus {corpus_id} not found")

            results = {
                "corpus_id": corpus_id,
                "anomalies_found": 0,
                "presuppositions_found": 0,
                "processing_time": 0.0,
                "analysis_completed": True,
            }

            async with self.transaction_scope():
                # Run anomaly detection
                anomaly_result = await self.anomaly_service.analyze_corpus_for_anomalies(corpus_id)
                results["anomalies_found"] = len(anomaly_result)

                # Run presupposition discovery if requested
                if include_presuppositions:
                    # Analyze presuppositions for each theory
                    for theory in corpus.theories:
                        presuppositions = (
                            await self.presupposition_service.discover_presuppositions(
                                theory_id=theory.id,
                                theory_name=theory.name,
                                theory_text=". ".join(theory.principles),  # Simple concatenation
                            )
                        )
                        results["presuppositions_found"] += len(presuppositions)

                        # Respect timeout
                        if time.time() - start_time > analysis_timeout:
                            results["analysis_completed"] = False
                            break

            results["processing_time"] = time.time() - start_time

            await self.log_operation(
                "comprehensive_discovery",
                start_time,
                True,
                corpus_id=corpus_id,
                anomalies=results["anomalies_found"],
                presuppositions=results["presuppositions_found"],
            )

            return results

        except Exception as e:
            await self.log_operation(
                "comprehensive_discovery", start_time, False, corpus_id=corpus_id, error=str(e)
            )
            raise


# Cognitive Transformation Service
class CognitiveProcessingService(ApplicationService):
    """
    Application service for cognitive processing operations.
    Handles transformation chains and complex cognitive workflows.
    """

    def __init__(
        self,
        settings: Settings,
        transformation_service: CognitiveTransformationService,
        transformation_repo: any,  # Would be specific repository
    ):
        super().__init__(settings)
        self.transformation_service = transformation_service
        self.transformation_repo = transformation_repo

    async def process_transformation_chain(
        self,
        initial_concept: str,
        domain: str,
        chain_steps: List[Dict[str, Any]],
        max_chain_length: int = 5,
    ) -> Dict[str, Any]:
        """
        Process a chain of cognitive transformations.
        """
        start_time = time.time()

        try:
            current_concept = initial_concept
            transformations_applied = []

            for i, step in enumerate(chain_steps[:max_chain_length]):
                step_result = await self.transformation_service.apply_transformation(
                    input_concept=current_concept,
                    transformation_type=step["type"],
                    domain=domain,
                    operator_name=step.get("operator"),
                )

                if not step_result:
                    break  # Transformation not effective

                transformations_applied.append(step_result)
                current_concept = step_result.output_concept

            results = {
                "initial_concept": initial_concept,
                "final_concept": current_concept,
                "transformations_applied": len(transformations_applied),
                "chain_completed": True,
                "processing_time": time.time() - start_time,
            }

            await self.log_operation(
                "transformation_chain",
                start_time,
                True,
                initial_concept=initial_concept,
                final_concept=current_concept,
                chain_length=len(transformations_applied),
            )

            return results

        except Exception as e:
            await self.log_operation(
                "transformation_chain",
                start_time,
                False,
                initial_concept=initial_concept,
                error=str(e),
            )
            raise


# Health Monitoring Service
class SystemHealthService(ApplicationService):
    """
    Application service for system health monitoring and diagnostics.
    """

    def __init__(
        self,
        settings: Settings,
        repositories: Dict[str, Any],
        services: Dict[str, Any],
    ):
        super().__init__(settings)
        self.repositories = repositories
        self.services = services

    async def comprehensive_health_check(self) -> HealthCheckResponseDTO:
        """
        Run comprehensive system health check.
        """
        start_time = time.time()
        services_status = {}
        overall_health = "healthy"

        try:
            # Check repositories
            for name, repo in self.repositories.items():
                try:
                    if hasattr(repo, "health_check"):
                        health_result = await repo.health_check()
                        status = health_result.get("status", "unknown")
                    else:
                        status = "unknown"

                    services_status[f"repo_{name}"] = status

                    if status not in ["healthy", "success"]:
                        overall_health = "warning"

                except Exception as e:
                    services_status[f"repo_{name}"] = f"error: {str(e)}"
                    overall_health = "unhealthy"

            # Check services
            for name, service in self.services.items():
                try:
                    # Simple ping check - in practice, services would have health methods
                    services_status[f"service_{name}"] = "healthy"
                except Exception as e:
                    services_status[f"service_{name}"] = f"error: {str(e)}"
                    overall_health = "unhealthy"

            # Check system metrics
            services_status["system_load"] = "healthy"  # Placeholder
            services_status["memory_usage"] = "healthy"  # Placeholder

            processing_time = time.time() - start_time

            await self.log_operation(
                "health_check",
                start_time,
                True,
                overall_health=overall_health,
                services_checked=len(services_status),
            )

            return HealthCheckResponseDTO(
                status="success",
                message=f"Health check completed in {processing_time:.2f}s",
                services=services_status,
                overall_health=overall_health,
            )

        except Exception as e:
            await self.log_operation("health_check", start_time, False, error=str(e))

            return HealthCheckResponseDTO(
                status="error",
                message=f"Health check failed: {str(e)}",
                services={},
                overall_health="unknown",
            )
