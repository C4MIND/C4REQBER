"""
TURBO-CDI v7.0 Pytest Configuration
Shared fixtures for test suite
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_c4_state():
    """Sample C4 state for testing"""
    from core.meta_prime_engine import C4State, TimeAxis, ScaleAxis, AgencyAxis
    return C4State(TimeAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF)


@pytest.fixture
def meta_prime_api():
    """MetaPrimeAPI instance for testing"""
    from core.meta_prime_engine import MetaPrimeAPI
    return MetaPrimeAPI()


@pytest.fixture
def sample_domain():
    """Sample domain name for testing"""
    return "mathematics"
