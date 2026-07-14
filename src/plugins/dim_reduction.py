"""Dimension Reduction Plugin — PCA, explained variance, simple t-SNE stub.

Does NOT duplicate: matrix_mult (linear algebra), text_distance (similarity).
UNIQUE: Dimensionality reduction for high-D hypothesis spaces and embeddings.
"""
from __future__ import annotations

import math
from typing import Any


def pca(data: list[list[float]], n_components: int = 2) -> dict[str, Any]:
    """Principal Component Analysis via covariance eigendecomposition.

    Simple power iteration for top components. No numpy needed.
    """
    if not data or not data[0]:
        return {"error": "Need non-empty data matrix"}

    n_samples = len(data)
    n_features = len(data[0])

    # Center the data
    means = [sum(row[i] for row in data) / n_samples for i in range(n_features)]
    centered = [[data[i][j] - means[j] for j in range(n_features)] for i in range(n_samples)]

    # Covariance matrix
    cov = [[0.0] * n_features for _ in range(n_features)]
    for i in range(n_features):
        for j in range(n_features):
            cov[i][j] = sum(centered[k][i] * centered[k][j] for k in range(n_samples)) / (n_samples - 1) if n_samples > 1 else 0.0

    # Power iteration for top eigenvectors
    eigenvalues = []
    eigenvectors = []
    residual = [row[:] for row in cov]

    for _ in range(min(n_components, n_features)):
        # Power iteration
        vec = [1.0] * n_features
        for _ in range(50):
            new_vec = [sum(residual[i][j] * vec[j] for j in range(n_features)) for i in range(n_features)]
            norm = math.sqrt(sum(v * v for v in new_vec))
            if norm < 1e-12:
                break
            vec = [v / norm for v in new_vec]

        # Rayleigh quotient for eigenvalue
        av = [sum(cov[i][j] * vec[j] for j in range(n_features)) for i in range(n_features)]
        eigval = sum(vec[i] * av[i] for i in range(n_features))

        eigenvalues.append(round(eigval, 6))
        eigenvectors.append(vec[:])

        # Deflate covariance
        for i in range(n_features):
            for j in range(n_features):
                residual[i][j] -= eigval * vec[i] * vec[j]

    # Project data onto eigenvectors
    total_var = sum(abs(e) for e in eigenvalues) if eigenvalues else 1.0
    explained = [round(e / total_var, 4) for e in eigenvalues]

    projection = []
    for row in centered:
        proj = [round(sum(row[j] * eig[j] for j in range(n_features)), 6) for eig in eigenvectors]
        projection.append(proj)

    return {
        "components": n_components,
        "eigenvalues": eigenvalues,
        "explained_variance_ratio": explained,
        "cumulative_variance": round(sum(explained), 4),
        "projection": projection[:20],
        "n_samples": n_samples,
        "n_features": n_features,
    }


def explained_variance(vectors: list[list[float]]) -> dict[str, Any]:
    """Analyze variance structure of a dataset.

    Returns per-dimension variance and total.
    """
    if not vectors or not vectors[0]:
        return {"error": "Need non-empty data"}

    n = len(vectors)
    dims = len(vectors[0])
    variances = []

    for d in range(dims):
        mean = sum(v[d] for v in vectors) / n
        var = sum((v[d] - mean) ** 2 for v in vectors) / n
        variances.append(round(var, 6))

    total = sum(variances)
    normalized = [round(v / total, 4) for v in variances] if total > 0 else [0.0] * dims
    dominant_dim = variances.index(max(variances)) if variances else 0

    return {
        "variances": variances,
        "variance_ratio": normalized,
        "dominant_dimension": dominant_dim,
        "total_variance": round(total, 6),
        "n": n,
        "dims": dims,
    }


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run dimensionality reduction.

    metric: "pca" | "variance"
    data: list of lists (matrix)
    n_components: int (for PCA)
    """
    metric = kwargs.get("metric", "pca")
    data = kwargs.get("data", [])

    try:
        if metric == "variance":
            return explained_variance(data)
        else:
            return pca(data, kwargs.get("n_components", 2))
    except Exception as e:
        return {"error": str(e), "metric": metric}
