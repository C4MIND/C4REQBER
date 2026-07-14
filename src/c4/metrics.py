"""
C4 Metrics — Formal distance functions on Z₃³.

Provides two distinct notions of distance:
- undirected_distance: a true metric (symmetric, triangle inequality)
- directed_distance: an asymmetric directed distance (non-metric)

Reference: formal-proofs/c4-comp-v5.agda
"""
from __future__ import annotations

from src.c4.state import C4State


def undirected_distance(a: C4State, b: C4State) -> int:
    """
    Symmetric modular metric on Z₃³.

    d(a,b) = Σ min(|aᵢ-bᵢ|, 3-|aᵢ-bᵢ|)  for i ∈ {t,s,a}

    Properties:
        - Non-negative: d(a,b) ≥ 0
        - Symmetric: d(a,b) = d(b,a)
        - Triangle inequality: d(a,c) ≤ d(a,b) + d(b,c)
        - Identity: d(a,b) = 0 ⟺ a = b

    Diameter of Z₃³ under this metric = 3.
    Antipodal pairs (e.g., (0,0,0) and (2,2,2)) are at distance 3.

    This is a true metric space — suitable for geometric analysis,
    clustering, and embedding into Euclidean space.
    """
    return a.distance(b)


def directed_distance(a: C4State, b: C4State) -> int:
    """
    Asymmetric directed distance on Z₃³.

    d_dir(a,b) = Σ (bᵢ - aᵢ) mod 3  for i ∈ {t,s,a}

    Properties:
        - Non-negative: d_dir(a,b) ≥ 0
        - NOT symmetric: d_dir(a,b) ≠ d_dir(b,a) in general
        - Directed triangle inequality: d_dir(a,c) ≤ d_dir(a,b) + d_dir(b,c)
        - Identity: d_dir(a,b) = 0 ⟺ a = b

    Diameter of Z₃³ under this distance = 6.
    Example: d_dir((0,0,0), (2,2,2)) = 2+2+2 = 6.

    This is NOT a metric (fails symmetry). It measures the number of
    forward cyclic shifts needed to reach b from a, per axis.
    Matches Agda formal proofs: time-dist, scale-dist, agency-dist.

    Suitable for:
        - Canonical path length computation
        - Directed graph analysis
        - Temporal/ordered navigation
    """
    return a.directed_distance(b)
