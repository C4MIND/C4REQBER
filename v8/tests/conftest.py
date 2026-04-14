"""
Pytest configuration and fixtures.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock
from turbo_cdi.infrastructure.config import Settings
from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Provide test settings"""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:", llm_api_key="test_key", debug_mode=True
    )


@pytest.fixture
def container(settings):
    """Provide DI container with test configuration"""
    return Container(config=settings)


@pytest.fixture
async def sample_corpus():
    """Provide a sample knowledge corpus for testing"""
    return KnowledgeCorpus(
        id="test_corpus",
        name="Test Physics Corpus",
        domain="physics",
        subdomains=("quantum", "relativity"),
    )


@pytest.fixture
def mock_repository():
    """Provide a mock discovery repository"""
    mock = AsyncMock()
    mock.get_corpus.return_value = None
    mock.save_corpus.return_value = None
    mock.corpus_exists.return_value = True
    return mock


@pytest.fixture
def mock_llm_client():
    """Provide a mock LLM client"""
    mock = AsyncMock()
    mock.query.return_value = '{"anomalies": []}'
    return mock
