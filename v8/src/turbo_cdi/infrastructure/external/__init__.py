"""
External service adapters for TURBO-CDI v8.4
Adapters implement protocols defined in domain layer.
"""

import asyncio
import aiohttp
import logging
import re
from typing import Protocol, runtime_checkable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from turbo_cdi.domain.services import LLMClient as LLMClientProtocol

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker for external services"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None

    async def __aenter__(self):
        if self.failure_count >= self.failure_threshold:
            if self.last_failure_time:
                elapsed = asyncio.get_event_loop().time() - self.last_failure_time
                if elapsed < self.recovery_timeout:
                    raise Exception("Circuit breaker is open")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()
        else:
            self.failure_count = max(0, self.failure_count - 1)


class LLMClient:
    """
    Simple mock LLM client for testing.

    Returns mock responses without external API calls.
    """

    def __init__(
        self,
        api_key: str = "mock_key",
        model: str = "mock-model",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    async def query(self, prompt: str) -> str:
        """
        Mock LLM query - returns sample anomaly data for testing.

        In production, this would call actual LLM API.
        """
        # Mock response for anomaly detection
        if "anomalies" in prompt.lower():
            return """[
                {
                    "type": "empirical",
                    "fact_statement": "Sample fact that may conflict",
                    "theory_name": "Sample theory",
                    "conflict_description": "Mock anomaly for testing",
                    "criticality": "medium"
                }
            ]"""

        # Default mock response
        return '{"anomalies": []}'

    async def close(self):
        """Mock close method"""
        pass


class CorpusValidatorImpl:
    """
    Implementation of corpus validation.

    Checks business rules for knowledge corpora.
    """

    def is_valid(self, corpus) -> bool:
        """Validate a knowledge corpus"""
        if not corpus.name.strip():
            return False
        if not corpus.domain.strip():
            return False
        if corpus.fact_count == 0 and corpus.theory_count == 0:
            return False  # Empty corpus
        return True
