"""LLM test fixtures"""
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@pytest.fixture
def mock_llm_response():
    return {
        "content": "Test response",
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


@pytest.fixture
def mock_provider_config():
    return {
        "provider": "openrouter",
        "model": "test-model",
        "api_key": "test-key",
        "base_url": "http://localhost:8000",
    }
