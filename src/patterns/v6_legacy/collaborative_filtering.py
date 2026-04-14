"""
TURBO-CDI v6.0 - Collaborative Filtering Pattern
Matrix factorization for recommendation systems.

Pattern Structure (Christopher Alexander):
- Context: E-commerce, content platforms, personalization
- Forces: Sparsity, cold start, scalability, accuracy
- Solution: Latent factor models with regularization
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CFAlgorithm(Enum):
    """Available collaborative filtering algorithms"""

    SVD = "svd"  # Singular Value Decomposition
    NMF = "nmf"  # Non-negative Matrix Factorization
    ALS = "als"  # Alternating Least Squares
    SGD = "sgd"  # Stochastic Gradient Descent


@dataclass
class CollaborativeFilteringConfig:
    """Configuration for collaborative filtering"""

    algorithm: CFAlgorithm = CFAlgorithm.ALS

    # Matrix dimensions
    n_users: int = 100
    n_items: int = 50

    # Latent factors
    n_factors: int = 10

    # Sparsity
    sparsity: float = 0.9  # Fraction of missing ratings

    # Data generation
    rating_range: Tuple[float, float] = (1.0, 5.0)

    # Training
    learning_rate: float = 0.01
    regularization: float = 0.1
    n_epochs: int = 20
    batch_size: int = 32

    # SGD specific
    decay: float = 0.99

    # Evaluation
    test_ratio: float = 0.2

    # Cold start
    cold_start_users: int = 5  # Users with no ratings


class CollaborativeFilteringPattern:
    """
    Collaborative filtering using matrix factorization.

    Algorithms:
    - SVD: Singular Value Decomposition
    - NMF: Non-negative Matrix Factorization
    - ALS: Alternating Least Squares
    - SGD: Stochastic Gradient Descent

    R ≈ U · V^T
    Where R is the rating matrix, U is user factors, V is item factors
    """

    PATTERN_ID = "collaborative_filtering"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[CollaborativeFilteringConfig] = None):
        self.config = config or CollaborativeFilteringConfig()
        self.ratings: Optional[np.ndarray] = (
            None  # Rating matrix (with NaN for missing)
        )
        self.mask: Optional[np.ndarray] = None  # Known ratings mask
        self.U: Optional[np.ndarray] = None  # User factors
        self.V: Optional[np.ndarray] = None  # Item factors
        self.train_mask: Optional[np.ndarray] = None
        self.test_mask: Optional[np.ndarray] = None
        self.history: Dict[str, List[float]] = {"train_loss": [], "test_rmse": []}

        self._initialize()

    def _initialize(self):
        """Initialize collaborative filtering"""
        cfg = self.config

        # Generate or load rating matrix
        self.ratings = self._generate_ratings()

        # Create mask for known ratings
        self.mask = ~np.isnan(self.ratings)

        # Train/test split
        known_indices = np.where(self.mask)
        n_known = len(known_indices[0])
        n_test = int(n_known * cfg.test_ratio)

        test_idx = np.random.choice(n_known, size=n_test, replace=False)

        self.train_mask = np.zeros_like(self.mask)
        self.test_mask = np.zeros_like(self.mask)

        self.train_mask[known_indices[0][test_idx], known_indices[1][test_idx]] = False
        self.test_mask[known_indices[0][test_idx], known_indices[1][test_idx]] = True

        # Remaining are train
        self.train_mask = self.mask.copy()
        self.train_mask[self.test_mask] = False

        # Initialize factors
        self.U = np.random.normal(0, 0.1, (cfg.n_users, cfg.n_factors))
        self.V = np.random.normal(0, 0.1, (cfg.n_items, cfg.n_factors))

        # NMF: ensure non-negative
        if cfg.algorithm == CFAlgorithm.NMF:
            self.U = np.abs(self.U) * 0.1
            self.V = np.abs(self.V) * 0.1

    def _generate_ratings(self) -> np.ndarray:
        """Generate synthetic rating matrix"""
        cfg = self.config

        # True latent factors
        true_U = np.random.randn(cfg.n_users, cfg.n_factors)
        true_V = np.random.randn(cfg.n_items, cfg.n_factors)

        # Generate ratings with noise
        ratings = true_U @ true_V.T
        ratings += np.random.randn(cfg.n_users, cfg.n_items) * 0.5

        # Scale to rating range
        r_min, r_max = cfg.rating_range
        ratings = (ratings - ratings.min()) / (ratings.max() - ratings.min())
        ratings = ratings * (r_max - r_min) + r_min

        # Make sparse
        mask = np.random.random((cfg.n_users, cfg.n_items)) < (1 - cfg.sparsity)
        ratings = np.where(mask, ratings, np.nan)

        # Cold start users
        for u in range(min(cfg.cold_start_users, cfg.n_users)):
            ratings[u, :] = np.nan
            # Give them 1-2 ratings
            n_ratings = np.random.randint(1, 3)
            items = np.random.choice(cfg.n_items, size=n_ratings, replace=False)
            ratings[u, items] = np.random.uniform(*cfg.rating_range, size=n_ratings)

        return ratings

    def _predict(self) -> np.ndarray:
        """Predict all ratings"""
        return self.U @ self.V.T

    def _calculate_loss(self, use_mask: np.ndarray) -> float:
        """Calculate MSE loss"""
        predictions = self._predict()
        errors = (predictions - self.ratings) ** 2
        errors[~use_mask] = 0
        mse = np.sum(errors) / np.sum(use_mask)

        # Add regularization
        reg = self.config.regularization * (np.sum(self.U**2) + np.sum(self.V**2))

        return mse + reg

    def _calculate_rmse(self, use_mask: np.ndarray) -> float:
        """Calculate RMSE on masked ratings"""
        predictions = self._predict()
        errors = (predictions - self.ratings) ** 2
        errors[~use_mask] = 0
        mse = np.sum(errors) / np.sum(use_mask)
        return np.sqrt(mse)

    def _als_step(self):
        """One ALS iteration"""
        cfg = self.config

        # Fix V, solve for U
        for i in range(cfg.n_users):
            known_items = np.where(self.train_mask[i])[0]
            if len(known_items) > 0:
                V_known = self.V[known_items]
                r_known = self.ratings[i, known_items]

                # (V^T V + λI) u = V^T r
                A = V_known.T @ V_known + cfg.regularization * np.eye(cfg.n_factors)
                b = V_known.T @ r_known
                self.U[i] = np.linalg.solve(A, b)

        # Fix U, solve for V
        for j in range(cfg.n_items):
            known_users = np.where(self.train_mask[:, j])[0]
            if len(known_users) > 0:
                U_known = self.U[known_users]
                r_known = self.ratings[known_users, j]

                A = U_known.T @ U_known + cfg.regularization * np.eye(cfg.n_factors)
                b = U_known.T @ r_known
                self.V[j] = np.linalg.solve(A, b)

    def _sgd_step(self):
        """One SGD iteration"""
        cfg = self.config

        # Sample a batch
        known_users, known_items = np.where(self.train_mask)
        n_samples = len(known_users)

        indices = np.random.permutation(n_samples)

        for idx in indices:
            i, j = known_users[idx], known_items[idx]

            # Prediction error
            pred = self.U[i] @ self.V[j]
            error = self.ratings[i, j] - pred

            # Gradients
            u_grad = -error * self.V[j] + cfg.regularization * self.U[i]
            v_grad = -error * self.U[i] + cfg.regularization * self.V[j]

            # Update
            self.U[i] -= cfg.learning_rate * u_grad
            self.V[j] -= cfg.learning_rate * v_grad

            # NMF constraint
            if cfg.algorithm == CFAlgorithm.NMF:
                self.U[i] = np.maximum(0, self.U[i])
                self.V[j] = np.maximum(0, self.V[j])

    def _svd_step(self):
        """SVD decomposition (batch, not iterative)"""
        # Fill missing with mean
        ratings_filled = self.ratings.copy()
        col_means = np.nanmean(ratings_filled, axis=0)
        for j in range(self.config.n_items):
            ratings_filled[np.isnan(ratings_filled[:, j]), j] = col_means[j]

        # Center
        ratings_filled -= np.mean(ratings_filled)

        # SVD
        U, s, Vt = np.linalg.svd(ratings_filled, full_matrices=False)

        # Truncate
        k = self.config.n_factors
        self.U = U[:, :k] * np.sqrt(s[:k])
        self.V = Vt[:k, :].T * np.sqrt(s[:k])

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run collaborative filtering training"""
        cfg = self.config

        logger.info(f"Starting collaborative filtering: {cfg.algorithm.value}")
        logger.info(f"Matrix: {cfg.n_users} users × {cfg.n_items} items")
        logger.info(
            f"Known ratings: {np.sum(self.train_mask)} train, {np.sum(self.test_mask)} test"
        )

        # SVD is non-iterative
        if cfg.algorithm == CFAlgorithm.SVD:
            self._svd_step()
            train_rmse = self._calculate_rmse(self.train_mask)
            test_rmse = self._calculate_rmse(self.test_mask)
            self.history["train_loss"].append(train_rmse)
            self.history["test_rmse"].append(test_rmse)
        else:
            # Iterative algorithms
            for epoch in range(cfg.n_epochs):
                if cfg.algorithm == CFAlgorithm.ALS:
                    self._als_step()
                elif cfg.algorithm in [CFAlgorithm.SGD, CFAlgorithm.NMF]:
                    self._sgd_step()

                # Evaluate
                train_rmse = self._calculate_rmse(self.train_mask)
                test_rmse = self._calculate_rmse(self.test_mask)

                self.history["train_loss"].append(train_rmse)
                self.history["test_rmse"].append(test_rmse)

                # Decay learning rate for SGD
                if cfg.algorithm in [CFAlgorithm.SGD, CFAlgorithm.NMF]:
                    cfg.learning_rate *= cfg.decay

                if epoch % 5 == 0:
                    logger.debug(
                        f"Epoch {epoch}: train_rmse={train_rmse:.4f}, test_rmse={test_rmse:.4f}"
                    )

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format output"""
        cfg = self.config

        predictions = self._predict()

        # Calculate metrics
        train_rmse = self._calculate_rmse(self.train_mask)
        test_rmse = self._calculate_rmse(self.test_mask)

        # MAE
        mae_mask = self.test_mask
        mae = np.mean(np.abs(predictions[mae_mask] - self.ratings[mae_mask]))

        # Recommendations for cold start users
        cold_start_recs = self._recommend_for_cold_start()

        # Factor analysis
        user_factor_variance = np.var(self.U, axis=0)
        item_factor_variance = np.var(self.V, axis=0)

        return {
            "algorithm": cfg.algorithm.value,
            "final_rmse": {
                "train": float(train_rmse),
                "test": float(test_rmse),
            },
            "mae": float(mae),
            "history": {
                "train_rmse": [
                    float(x)
                    for x in self.history["train_loss"][
                        :: max(1, len(self.history["train_loss"]) // 20)
                    ]
                ],
                "test_rmse": [
                    float(x)
                    for x in self.history["test_rmse"][
                        :: max(1, len(self.history["test_rmse"]) // 20)
                    ]
                ],
            },
            "predictions_sample": predictions[:5, :5].tolist(),
            "cold_start_recommendations": cold_start_recs,
            "factor_analysis": {
                "user_factor_variance": user_factor_variance.tolist(),
                "item_factor_variance": item_factor_variance.tolist(),
                "dominant_factors": int(np.sum(user_factor_variance > 0.1)),
            },
            "data_stats": {
                "n_users": cfg.n_users,
                "n_items": cfg.n_items,
                "n_ratings_train": int(np.sum(self.train_mask)),
                "n_ratings_test": int(np.sum(self.test_mask)),
                "sparsity": float(1 - np.sum(self.mask) / (cfg.n_users * cfg.n_items)),
            },
            "config": {
                "n_factors": cfg.n_factors,
                "regularization": cfg.regularization,
                "n_epochs": cfg.n_epochs,
            },
        }

    def _recommend_for_cold_start(self) -> List[Dict]:
        """Generate recommendations for cold start users"""
        cfg = self.config
        recs = []

        for u in range(min(cfg.cold_start_users, cfg.n_users)):
            # Predict ratings for this user
            predictions = self.U[u] @ self.V.T

            # Get items they haven't rated
            unrated = np.where(~self.mask[u])[0]

            if len(unrated) > 0:
                # Top-N recommendations
                top_items = unrated[np.argsort(predictions[unrated])[-5:][::-1]]
                recs.append(
                    {
                        "user": u,
                        "recommended_items": top_items.tolist(),
                        "predicted_ratings": predictions[top_items].tolist(),
                    }
                )

        return recs

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Collaborative Filtering",
            "category": "EXTENDED",
            "domain": ["E-commerce", "Content Platforms", "Personalization"],
            "description": "Matrix factorization for recommendation systems",
            "computational_complexity": "O(I·N·K²) for ALS, O(I·N·K) for SGD",
            "typical_runtime": "seconds to minutes",
            "accuracy": "High (state-of-the-art for collaborative filtering)",
            "assumptions": [
                "Latent factor structure",
                "Stationary preferences",
                "Sparse but not too sparse",
            ],
            "parameters": [
                {
                    "name": "algorithm",
                    "type": "enum",
                    "options": ["svd", "nmf", "als", "sgd"],
                    "default": "als",
                },
                {
                    "name": "n_factors",
                    "type": "int",
                    "default": 10,
                },
                {
                    "name": "regularization",
                    "type": "float",
                    "default": 0.1,
                },
                {
                    "name": "learning_rate",
                    "type": "float",
                    "default": 0.01,
                },
            ],
        }


# Unit tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: ALS algorithm
    print("\n=== Test 1: ALS Algorithm ===")
    config = CollaborativeFilteringConfig(
        algorithm=CFAlgorithm.ALS,
        n_users=100,
        n_items=50,
        n_factors=10,
        sparsity=0.8,
        n_epochs=20,
    )
    sim = CollaborativeFilteringPattern(config)
    result = sim.run()
    print(f"✓ Test RMSE: {result['final_rmse']['test']:.4f}")
    print(f"  MAE: {result['mae']:.4f}")
    print(f"  Sparsity: {result['data_stats']['sparsity']:.1%}")
    assert result["final_rmse"]["test"] < 2.0, (
        "RMSE should be reasonable for synthetic data"
    )

    # Test 2: SGD algorithm
    print("\n=== Test 2: SGD Algorithm ===")
    config = CollaborativeFilteringConfig(
        algorithm=CFAlgorithm.SGD,
        n_users=100,
        n_items=50,
        n_factors=10,
        sparsity=0.8,
        n_epochs=20,
        learning_rate=0.02,
    )
    sim = CollaborativeFilteringPattern(config)
    result = sim.run()
    print(f"✓ SGD Test RMSE: {result['final_rmse']['test']:.4f}")

    # Test 3: SVD (fast, non-iterative)
    print("\n=== Test 3: SVD Algorithm ===")
    config = CollaborativeFilteringConfig(
        algorithm=CFAlgorithm.SVD,
        n_users=100,
        n_items=50,
        n_factors=10,
        sparsity=0.7,
    )
    sim = CollaborativeFilteringPattern(config)
    result = sim.run()
    print(f"✓ SVD Test RMSE: {result['final_rmse']['test']:.4f}")

    # Test 4: Sparsity effect
    print("\n=== Test 4: Sparsity Effect ===")
    for sparsity in [0.5, 0.8, 0.9, 0.95]:
        config = CollaborativeFilteringConfig(
            algorithm=CFAlgorithm.ALS,
            n_users=100,
            n_items=50,
            n_factors=10,
            sparsity=sparsity,
            n_epochs=15,
        )
        sim = CollaborativeFilteringPattern(config)
        result = sim.run()
        print(f"  Sparsity {sparsity:.0%}: RMSE={result['final_rmse']['test']:.4f}")

    # Test 5: Cold start recommendations
    print("\n=== Test 5: Cold Start Recommendations ===")
    config = CollaborativeFilteringConfig(
        algorithm=CFAlgorithm.ALS,
        n_users=50,
        n_items=30,
        n_factors=8,
        cold_start_users=5,
        n_epochs=20,
    )
    sim = CollaborativeFilteringPattern(config)
    result = sim.run()
    print(
        f"✓ Generated {len(result['cold_start_recommendations'])} cold start recommendations"
    )
    if result["cold_start_recommendations"]:
        rec = result["cold_start_recommendations"][0]
        print(f"  Sample: User {rec['user']} -> items {rec['recommended_items'][:3]}")

    print("\n✅ All collaborative filtering tests passed!")
