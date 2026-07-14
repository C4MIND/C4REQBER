"""Pattern test fixtures"""
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@pytest.fixture
def sample_hypothesis():
    return {
        "title": "Test Synthesis",
        "description": "A test hypothesis for pattern simulation",
        "parameters": {},
    }


@pytest.fixture
def base_config():
    from src.patterns.library.base import BaseConfig
    return BaseConfig()
