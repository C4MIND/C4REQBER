"""
Pattern 51: Input-Output Model (Leontief Matrix)
Implements the classic Leontief input-output economic model for inter-industry analysis.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.linalg import inv


@dataclass
class InputOutputConfig:
    """Configuration for Leontief Input-Output model."""

    n_sectors: int = 5
    total_output: np.ndarray = None  # type: ignore[assignment]
    intermediate_demand: np.ndarray = None  # type: ignore[assignment]
    final_demand: np.ndarray = None  # type: ignore[assignment]
    value_added: np.ndarray = None  # type: ignore[assignment]
    random_seed: int = 42


class InputOutputModel:
    """
    Leontief Input-Output economic model.

    Models the interdependencies between different sectors of an economy,
    showing how output from one sector may become input to another.
    """

    def __init__(self, config: InputOutputConfig = None) -> None:  # type: ignore[assignment]
        self.config = config or InputOutputConfig()
        self._setup_data()

    def _setup_data(self) -> None:
        """Initialize model data with realistic sector relationships."""
        np.random.seed(self.config.random_seed)
        n = self.config.n_sectors

        if self.config.total_output is None:
            # Realistic sector outputs (in billions)
            self.total_output = np.array([500, 800, 600, 400, 300], dtype=float)  # type: ignore[unreachable]
        else:
            self.total_output = self.config.total_output.astype(float)  # type: ignore[has-type]

        if self.config.intermediate_demand is None:
            # Technical coefficients matrix (input requirements per unit output)
            # Rows: consuming sectors, Columns: producing sectors
            self.tech_coeffs = np.array(  # type: ignore[unreachable]
                [
                    [0.15, 0.20, 0.10, 0.05, 0.08],  # Agriculture
                    [0.25, 0.30, 0.20, 0.15, 0.10],  # Manufacturing
                    [0.10, 0.15, 0.25, 0.10, 0.12],  # Services
                    [0.08, 0.10, 0.12, 0.20, 0.15],  # Energy
                    [0.05, 0.08, 0.10, 0.08, 0.18],  # Construction
                ]
            )
        else:
            self.tech_coeffs = self.config.intermediate_demand  # type: ignore[has-type]

        if self.config.final_demand is None:
            self.final_demand = np.array([150, 200, 180, 100, 80], dtype=float)  # type: ignore[unreachable]
        else:
            self.final_demand = self.config.final_demand.astype(float)  # type: ignore[has-type]

        if self.config.value_added is None:
            self.value_added = (  # type: ignore[unreachable]
                self.total_output - self.tech_coeffs.sum(axis=0) * self.total_output
            )
        else:
            self.value_added = self.config.value_added.astype(float)  # type: ignore[has-type]

    def run(self) -> dict[str, Any]:
        """
        Execute the Input-Output analysis.

        Returns:
            Dict containing Leontief inverse, multipliers, and sector analysis
        """
        n = self.config.n_sectors

        # Calculate intermediate consumption matrix Z
        Z = self.tech_coeffs * self.total_output[np.newaxis, :]  # type: ignore[has-type]

        # Technical coefficients matrix A (input per unit output)
        A = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if self.total_output[j] > 0:  # type: ignore[has-type]
                    A[i, j] = Z[i, j] / self.total_output[j]  # type: ignore[has-type]

        # Leontief inverse: (I - A)^(-1)
        I = np.eye(n)
        try:
            L = inv(I - A)
        except np.linalg.LinAlgError:
            L = np.linalg.pinv(I - A)

        # Output multipliers (column sums of L)
        output_multipliers = L.sum(axis=0)

        # Income multipliers
        income_coeffs = self.value_added / self.total_output  # type: ignore[has-type]
        income_multipliers = L.T @ income_coeffs

        # Employment multipliers (assuming employment coefficients)
        employment_coeffs = np.random.uniform(0.001, 0.01, n)
        employment_multipliers = L.T @ employment_coeffs

        # Sectoral linkages
        backward_linkage = A.sum(axis=0)  # Input purchases
        forward_linkage = A.sum(axis=1)  # Output sales

        # Key sector identification
        total_linkage = backward_linkage + forward_linkage
        key_sectors = np.argsort(total_linkage)[-2:]

        # Impact analysis: change in final demand
        demand_shock = np.array([10, 0, 0, 0, 0])  # 10B increase in sector 1
        output_impact = L @ demand_shock

        return {
            "technical_coefficients": A.tolist(),
            "leontief_inverse": L.tolist(),
            "intermediate_matrix": Z.tolist(),
            "output_multipliers": output_multipliers.tolist(),
            "income_multipliers": income_multipliers.tolist(),
            "employment_multipliers": employment_multipliers.tolist(),
            "backward_linkages": backward_linkage.tolist(),
            "forward_linkages": forward_linkage.tolist(),
            "key_sectors": key_sectors.tolist(),
            "demand_shock_impact": output_impact.tolist(),
            "total_output": self.total_output.tolist(),  # type: ignore[has-type]
            "final_demand": self.final_demand.tolist(),  # type: ignore[has-type]
            "value_added": self.value_added.tolist(),  # type: ignore[has-type]
            "model_type": "leontief_input_output",
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 51,
            "name": "Input-Output Model",
            "category": "Macroeconomics",
            "description": "Leontief input-output analysis for inter-industry relationships",
            "author": "Wassily Leontief",
            "year": 1936,
            "parameters": [
                "n_sectors",
                "total_output",
                "intermediate_demand",
                "final_demand",
            ],
            "outputs": ["leontief_inverse", "multipliers", "linkages", "key_sectors"],
            "applications": ["economic_planning", "impact_analysis", "trade_policy"],
        }


# Unit Tests
import unittest


class TestInputOutputModel(unittest.TestCase):
    """TestInputOutputModel."""
    def test_model_initialization(self) -> None:
        """Test model initializes with correct dimensions."""
        config = InputOutputConfig(n_sectors=5)
        model = InputOutputModel(config)
        self.assertEqual(model.config.n_sectors, 5)
        self.assertEqual(len(model.total_output), 5)  # type: ignore[has-type]

    def test_leontief_inverse_calculation(self) -> None:
        """Test Leontief inverse is computed correctly."""
        config = InputOutputConfig(n_sectors=5, random_seed=42)
        model = InputOutputModel(config)
        result = model.run()

        # Leontief inverse should be positive
        L = np.array(result["leontief_inverse"])
        self.assertTrue(np.all(L >= 0))

        # Diagonal should be >= 1 (direct + indirect effects)
        self.assertTrue(np.all(np.diag(L) >= 1))

    def test_multiplier_properties(self) -> None:
        """Test that multipliers are reasonable."""
        config = InputOutputConfig(n_sectors=5, random_seed=42)
        model = InputOutputModel(config)
        result = model.run()

        # Output multipliers should be >= 1
        multipliers = np.array(result["output_multipliers"])
        self.assertTrue(np.all(multipliers >= 1))

        # Should have correct length
        self.assertEqual(len(multipliers), 5)

    def test_demand_shock_impact(self) -> None:
        """Test that demand shock produces expected output changes."""
        config = InputOutputConfig(n_sectors=5, random_seed=42)
        model = InputOutputModel(config)
        result = model.run()

        impact = np.array(result["demand_shock_impact"])
        # First sector should have largest impact (shock applied there)
        self.assertEqual(np.argmax(impact), 0)
        # All impacts should be non-negative
        self.assertTrue(np.all(impact >= 0))

    def test_metadata(self) -> None:
        """Test metadata returns correct information."""
        meta = InputOutputModel.get_metadata()
        self.assertEqual(meta["pattern_id"], 51)
        self.assertEqual(meta["name"], "Input-Output Model")
        self.assertIn("Macroeconomics", meta["category"])


if __name__ == "__main__":
    # Run demonstration
    config = InputOutputConfig(n_sectors=5)
    model = InputOutputModel(config)
    result = model.run()

    print("=" * 60)
    print("INPUT-OUTPUT MODEL (Leontief)")
    print("=" * 60)
    print(f"\nOutput Multipliers: {result['output_multipliers']}")
    print(f"Key Sectors: {result['key_sectors']}")
    print(f"Demand Shock Impact: {result['demand_shock_impact']}")
    print("\nMetadata:", InputOutputModel.get_metadata())

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for C4REQBER compatibility
InputOutputPattern = InputOutputModel
