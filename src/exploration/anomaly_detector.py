"""
c4reqber: Anomaly Detector

Finds anomalies in literature embeddings and simulation residuals.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np


logger = logging.getLogger("c4reqber.exploration")


class AnomalyDetector:
    """Detect anomalies in scientific data."""

    def detect_literature_anomalies(
        self,
        embeddings: np.ndarray,
        papers: list[dict[str, Any]],
        contamination: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Find outlier papers in embedding space.

        Args:
            embeddings: Array of shape (n_papers, dim).
            papers: List of paper dicts.
            contamination: Expected fraction of outliers.

        Returns:
            List of anomalous papers.
        """
        if len(papers) < 10 or embeddings.shape[0] != len(papers):
            return []

        try:
            from sklearn.ensemble import IsolationForest

            clf = IsolationForest(contamination=contamination, random_state=42)
            outliers = clf.fit_predict(embeddings)
            anomalous = [papers[i] for i in np.where(outliers == -1)[0]]
            return anomalous
        except Exception as e:
            logger.warning("Literature anomaly detection failed: %s", e)
            return []

    def detect_simulation_residuals(
        self,
        predicted: np.ndarray,
        expected: np.ndarray,
        threshold_sigma: float = 3.0,
    ) -> list[int]:
        """Find simulation results that deviate from theory.

        Args:
            predicted: Predicted values from simulation.
            expected: Theoretically expected values.
            threshold_sigma: Number of std deviations for outlier.

        Returns:
            Indices of anomalous results.
        """
        residuals = np.abs(predicted - expected)
        std = np.std(residuals)
        if std == 0:
            return []
        threshold = threshold_sigma * std
        return [int(i) for i in np.where(residuals > threshold)[0]]

    def detect_embedding_outliers(
        self,
        embeddings: np.ndarray,
        threshold_percentile: float = 95.0,
    ) -> list[int]:
        """Find embeddings with highest distance from centroid.

        Args:
            embeddings: Array of shape (n, dim).
            threshold_percentile: Percentile for outlier threshold.

        Returns:
            Indices of outlier embeddings.
        """
        centroid = np.mean(embeddings, axis=0)
        distances = np.linalg.norm(embeddings - centroid, axis=1)
        threshold = np.percentile(distances, threshold_percentile)
        return [int(i) for i in np.where(distances > threshold)[0]]
