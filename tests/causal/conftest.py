"""Shared fixtures for causal engine tests."""
from __future__ import annotations

import numpy as np
import pytest

from src.causal.scm import StructuralCausalModel


@pytest.fixture
def simple_chain_scm() -> StructuralCausalModel:
    scm = StructuralCausalModel()
    scm.add_node("Z", is_exogenous=True, noise=lambda: np.random.randn())
    scm.add_node("X", parents=["Z"], mechanism=lambda z, u: z + u)
    scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)
    return scm


@pytest.fixture
def fork_scm() -> StructuralCausalModel:
    scm = StructuralCausalModel()
    scm.add_node("Z", is_exogenous=True, noise=lambda: np.random.randn())
    scm.add_node("X", parents=["Z"], mechanism=lambda z, u: z + u)
    scm.add_node("Y", parents=["Z"], mechanism=lambda z, u: z + u)
    return scm


@pytest.fixture
def collider_scm() -> StructuralCausalModel:
    scm = StructuralCausalModel()
    scm.add_node("X", is_exogenous=True, noise=lambda: np.random.randn())
    scm.add_node("Y", is_exogenous=True, noise=lambda: np.random.randn())
    scm.add_node("Z", parents=["X", "Y"], mechanism=lambda x, y, u: x + y + u)
    return scm


@pytest.fixture
def frontdoor_scm() -> StructuralCausalModel:
    scm = StructuralCausalModel()
    scm.add_node("X", is_exogenous=True, noise=lambda: np.random.randn())
    scm.add_node("Z", parents=["X"], mechanism=lambda x, u: x + u)
    scm.add_node("Y", parents=["Z"], mechanism=lambda z, u: z + u)
    return scm


@pytest.fixture
def backdoor_scm() -> StructuralCausalModel:
    scm = StructuralCausalModel()
    scm.add_node("Z", is_exogenous=True, noise=lambda: np.random.randn())
    scm.add_node("X", parents=["Z"], mechanism=lambda z, u: z + u)
    scm.add_node("Y", parents=["Z", "X"], mechanism=lambda z, x, u: z + x + u)
    return scm
