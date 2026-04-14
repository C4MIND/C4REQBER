"""
Integration tests for application use cases.
"""

import pytest
from unittest.mock import AsyncMock
from turbo_cdi.application.use_cases import (
    DiscoverKnowledgeUseCase,
    DiscoverKnowledgeRequest,
    DiscoverKnowledgeResponse,
    CorpusNotFoundError,
    ValidationError,
)
from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId, Anomaly, AnomalyType, Severity


@pytest.mark.asyncio
class TestDiscoverKnowledgeUseCase:
    """Test the DiscoverKnowledgeUseCase"""

    async def test_successful_discovery(self):
        """Test successful knowledge discovery"""
        # Arrange
        mock_repository = AsyncMock()
        mock_service = AsyncMock()

        corpus = KnowledgeCorpus(id="test_corpus", name="Test Corpus", domain="physics")

        anomalies = [
            Anomaly(
                id="anom_1",
                corpus_id="test_corpus",
                type=AnomalyType.EMPIRICAL,
                fact_statement="Test fact",
                theory_name="Test theory",
                conflict_description="Test conflict",
                criticality=Severity.MEDIUM,
            )
        ]

        mock_repository.get_corpus.return_value = corpus
        mock_service.detect_anomalies.return_value = anomalies

        use_case = DiscoverKnowledgeUseCase(
            discovery_service=mock_service, repository=mock_repository
        )

        request = DiscoverKnowledgeRequest(corpus_id="test_corpus")

        # Act
        response = await use_case.execute(request)

        # Assert
        assert isinstance(response, DiscoverKnowledgeResponse)
        assert response.corpus_id == "test_corpus"
        assert len(response.anomalies) == 1
        assert response.anomaly_count == 1
        assert response.processing_time >= 0

        # Verify interactions
        mock_repository.get_corpus.assert_called_once_with(CorpusId("test_corpus"))
        mock_service.detect_anomalies.assert_called_once_with(corpus)
        mock_repository.save_corpus.assert_called_once()

    async def test_corpus_not_found(self):
        """Test when corpus doesn't exist"""
        # Arrange
        mock_repository = AsyncMock()
        mock_repository.get_corpus.return_value = None

        use_case = DiscoverKnowledgeUseCase(
            discovery_service=AsyncMock(), repository=mock_repository
        )

        request = DiscoverKnowledgeRequest(corpus_id="nonexistent")

        # Act & Assert
        with pytest.raises(CorpusNotFoundError, match="not found"):
            await use_case.execute(request)

    async def test_invalid_request(self):
        """Test invalid request validation"""
        use_case = DiscoverKnowledgeUseCase(discovery_service=AsyncMock(), repository=AsyncMock())

        # Empty corpus_id should raise ValidationError
        request = DiscoverKnowledgeRequest(corpus_id="")

        with pytest.raises(ValidationError):
            await use_case.execute(request)

    async def test_anomaly_threshold_filtering(self):
        """Test that anomaly threshold affects results"""
        # This would test if anomalies below threshold are filtered
        # Implementation depends on domain service logic
        pass
