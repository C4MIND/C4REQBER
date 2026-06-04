"""TRIZ test fixtures"""
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@pytest.fixture
def sample_contradiction():
    return {
        "improving": "speed",
        "worsening": "accuracy",
        "principles": [1, 15, 28],
    }


@pytest.fixture
def triz_bridge():
    from src.triz.bridge import TRIZBridge
    return TRIZBridge()
