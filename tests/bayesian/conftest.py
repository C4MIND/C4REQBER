"""Bayesian test fixtures"""
import sys
from pathlib import Path

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@pytest.fixture
def sample_data():
    rng = np.random.default_rng(42)
    return rng.normal(0, 1, 100)


@pytest.fixture
def sample_prior():
    return {"mu_0": 0.0, "kappa_0": 1.0, "alpha_0": 1.0, "beta_0": 1.0}
