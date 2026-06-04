"""Comprehensive tests for Design of Experiments (DoE) module."""

from __future__ import annotations

import numpy as np
import pytest

from src.experiment_design.doe import (
    DesignType,
    DoEConfig,
    DoEResult,
    Factor,
    central_composite_design,
    fractional_factorial_design,
    full_factorial_design,
    latin_hypercube_sampling,
    randomized_block_design,
)


# -----------------------------------------------------------------------------
# Factor Validation
# -----------------------------------------------------------------------------


class TestFactorValidation:
    def test_valid_factor(self) -> None:
        factor = Factor(name="temperature", low=10.0, high=100.0, levels=3)
        factor.validate()

    def test_low_greater_than_or_equal_to_high_raises(self) -> None:
        with pytest.raises(ValueError, match="low must be < high"):
            Factor(name="temperature", low=100.0, high=100.0).validate()

    def test_low_greater_than_high_raises(self) -> None:
        with pytest.raises(ValueError, match="low must be < high"):
            Factor(name="temperature", low=200.0, high=100.0).validate()

    def test_levels_less_than_two_raises(self) -> None:
        with pytest.raises(ValueError, match="levels must be >= 2"):
            Factor(name="temperature", low=10.0, high=100.0, levels=1).validate()


# -----------------------------------------------------------------------------
# DoEConfig Validation
# -----------------------------------------------------------------------------


class TestDoEConfigValidation:
    def test_empty_factors_raises(self) -> None:
        config = DoEConfig(
            factors=[],
            design_type=DesignType.FULL_FACTORIAL,
        )
        with pytest.raises(ValueError, match="At least one factor required"):
            config.validate()

    def test_invalid_replicates_raises(self) -> None:
        config = DoEConfig(
            factors=[Factor(name="A", low=0.0, high=1.0)],
            design_type=DesignType.FULL_FACTORIAL,
            replicates=0,
        )
        with pytest.raises(ValueError, match="replicates must be >= 1"):
            config.validate()

    def test_lhs_samples_less_than_one_raises(self) -> None:
        config = DoEConfig(
            factors=[Factor(name="A", low=0.0, high=1.0)],
            design_type=DesignType.LATIN_HYPERCUBE,
            samples=0,
        )
        with pytest.raises(ValueError, match="samples must be >= 1"):
            config.validate()

    def test_fractional_without_resolution_raises(self) -> None:
        config = DoEConfig(
            factors=[Factor(name="A", low=0.0, high=1.0)],
            design_type=DesignType.FRACTIONAL_FACTORIAL,
            resolution=None,
        )
        with pytest.raises(ValueError, match="resolution required for fractional factorial"):
            config.validate()

    def test_fractional_resolution_less_than_three_raises(self) -> None:
        config = DoEConfig(
            factors=[Factor(name="A", low=0.0, high=1.0)],
            design_type=DesignType.FRACTIONAL_FACTORIAL,
            resolution=2,
        )
        with pytest.raises(ValueError, match="resolution must be >= 3"):
            config.validate()

    def test_valid_config_passes(self) -> None:
        config = DoEConfig(
            factors=[Factor(name="A", low=0.0, high=1.0)],
            design_type=DesignType.FULL_FACTORIAL,
            replicates=2,
        )
        config.validate()


# -----------------------------------------------------------------------------
# Full Factorial Design
# -----------------------------------------------------------------------------


class TestFullFactorialDesign:
    def test_two_factors_two_levels(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=10.0),
                Factor(name="B", low=-5.0, high=5.0),
            ],
            design_type=DesignType.FULL_FACTORIAL,
        )
        result = full_factorial_design(config)

        assert result.design_type == DesignType.FULL_FACTORIAL
        assert result.factor_names == ["A", "B"]
        assert result.design_matrix.shape == (4, 2)
        assert len(result.run_order) == 4
        assert set(result.run_order) == {0, 1, 2, 3}

        # Check all corner combinations are present
        expected = np.array([
            [0.0, -5.0],
            [0.0, 5.0],
            [10.0, -5.0],
            [10.0, 5.0],
        ])
        for row in expected:
            assert any(np.allclose(row, result.design_matrix[i]) for i in range(4))

    def test_three_factors_two_levels(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
                Factor(name="C", low=0.0, high=1.0),
            ],
            design_type=DesignType.FULL_FACTORIAL,
        )
        result = full_factorial_design(config)

        assert result.design_matrix.shape == (8, 3)
        assert len(result.run_order) == 8
        assert set(result.run_order) == set(range(8))

    def test_with_replicates(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.FULL_FACTORIAL,
            replicates=3,
        )
        result = full_factorial_design(config)

        assert result.design_matrix.shape == (12, 2)
        assert len(result.run_order) == 12

    def test_deterministic_with_seed(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.FULL_FACTORIAL,
            random_seed=42,
        )
        result1 = full_factorial_design(config)
        result2 = full_factorial_design(config)

        np.testing.assert_array_equal(result1.design_matrix, result2.design_matrix)
        np.testing.assert_array_equal(result1.run_order, result2.run_order)


# -----------------------------------------------------------------------------
# Fractional Factorial Design
# -----------------------------------------------------------------------------


class TestFractionalFactorialDesign:
    def test_basic_2_5_minus_1(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
                Factor(name="C", low=0.0, high=1.0),
                Factor(name="D", low=0.0, high=1.0),
                Factor(name="E", low=0.0, high=1.0),
            ],
            design_type=DesignType.FRACTIONAL_FACTORIAL,
            resolution=5,
        )
        result = fractional_factorial_design(config)

        assert result.design_type == DesignType.FRACTIONAL_FACTORIAL
        assert result.factor_names == ["A", "B", "C", "D", "E"]
        assert result.design_matrix.shape[0] >= 2
        assert result.design_matrix.shape[1] == 5
        assert len(result.run_order) == result.design_matrix.shape[0]

    def test_resolution_validation(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
                Factor(name="C", low=0.0, high=1.0),
                Factor(name="D", low=0.0, high=1.0),
            ],
            design_type=DesignType.FRACTIONAL_FACTORIAL,
            resolution=3,
        )
        result = fractional_factorial_design(config)

        assert result.design_type == DesignType.FRACTIONAL_FACTORIAL
        assert result.design_matrix.shape[1] == 4

    def test_with_replicates(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
                Factor(name="C", low=0.0, high=1.0),
            ],
            design_type=DesignType.FRACTIONAL_FACTORIAL,
            resolution=3,
            replicates=2,
        )
        result = fractional_factorial_design(config)

        assert result.design_matrix.shape[0] % 2 == 0
        assert len(result.run_order) == result.design_matrix.shape[0]


# -----------------------------------------------------------------------------
# Latin Hypercube Design
# -----------------------------------------------------------------------------


class TestLatinHypercubeDesign:
    def test_basic_design(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
                Factor(name="C", low=0.0, high=1.0),
            ],
            design_type=DesignType.LATIN_HYPERCUBE,
            samples=20,
        )
        result = latin_hypercube_sampling(config)

        assert result.design_type == DesignType.LATIN_HYPERCUBE
        assert result.factor_names == ["A", "B", "C"]
        assert result.design_matrix.shape == (20, 3)
        assert len(result.run_order) == 20
        assert set(result.run_order) == set(range(20))

    def test_correct_dimensions(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=-10.0, high=10.0),
                Factor(name="B", low=0.0, high=100.0),
            ],
            design_type=DesignType.LATIN_HYPERCUBE,
            samples=50,
        )
        result = latin_hypercube_sampling(config)

        assert result.design_matrix.shape == (50, 2)
        assert np.all(result.design_matrix[:, 0] >= -10.0)
        assert np.all(result.design_matrix[:, 0] <= 10.0)
        assert np.all(result.design_matrix[:, 1] >= 0.0)
        assert np.all(result.design_matrix[:, 1] <= 100.0)

    def test_deterministic_with_seed(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.LATIN_HYPERCUBE,
            samples=10,
            random_seed=123,
        )
        result1 = latin_hypercube_sampling(config)
        result2 = latin_hypercube_sampling(config)

        np.testing.assert_array_equal(result1.design_matrix, result2.design_matrix)
        np.testing.assert_array_equal(result1.run_order, result2.run_order)


# -----------------------------------------------------------------------------
# Central Composite Design
# -----------------------------------------------------------------------------


class TestCentralCompositeDesign:
    def test_rotatable_alpha(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.CENTRAL_COMPOSITE,
            alpha="rotatable",
        )
        result = central_composite_design(config)

        assert result.design_type == DesignType.CENTRAL_COMPOSITE
        assert result.factor_names == ["A", "B"]
        # 2^k corners + 2k star points + center_points
        expected_runs = 4 + 4 + config.center_points
        assert result.design_matrix.shape == (expected_runs, 2)

    def test_face_centered_alpha(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
                Factor(name="C", low=0.0, high=1.0),
            ],
            design_type=DesignType.CENTRAL_COMPOSITE,
            alpha="face",
            center_points=6,
        )
        result = central_composite_design(config)

        expected_runs = 8 + 6 + 6  # 2^3 + 2*3 + 6
        assert result.design_matrix.shape == (expected_runs, 3)

    def test_numeric_alpha(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
            ],
            design_type=DesignType.CENTRAL_COMPOSITE,
            alpha=1.5,
            center_points=2,
        )
        result = central_composite_design(config)

        expected_runs = 2 + 2 + 2  # 2^1 + 2*1 + 2
        assert result.design_matrix.shape == (expected_runs, 1)

    def test_unknown_alpha_raises(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
            ],
            design_type=DesignType.CENTRAL_COMPOSITE,
            alpha="invalid",
        )
        with pytest.raises(ValueError, match="Unknown alpha type"):
            central_composite_design(config)

    def test_with_replicates(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.CENTRAL_COMPOSITE,
            alpha="rotatable",
            replicates=2,
        )
        result = central_composite_design(config)

        base_runs = 4 + 4 + config.center_points
        assert result.design_matrix.shape == (base_runs * 2, 2)


# -----------------------------------------------------------------------------
# Randomized Block Design
# -----------------------------------------------------------------------------


class TestRandomizedBlockDesign:
    def test_basic_design(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.RANDOMIZED_BLOCK,
            blocks=3,
        )
        result = randomized_block_design(config)

        assert result.design_type == DesignType.RANDOMIZED_BLOCK
        assert result.factor_names == ["A", "B"]
        assert result.block_assignments is not None
        assert len(result.block_assignments) == result.design_matrix.shape[0]
        assert set(result.block_assignments) == {0, 1, 2}
        assert len(result.run_order) == result.design_matrix.shape[0]

    def test_blocks_less_than_two_raises(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
            ],
            design_type=DesignType.RANDOMIZED_BLOCK,
            blocks=1,
        )
        with pytest.raises(ValueError, match="blocks must be >= 2"):
            randomized_block_design(config)

    def test_blocks_none_raises(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
            ],
            design_type=DesignType.RANDOMIZED_BLOCK,
            blocks=None,
        )
        with pytest.raises(ValueError, match="blocks must be >= 2"):
            randomized_block_design(config)

    def test_with_replicates(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
            ],
            design_type=DesignType.RANDOMIZED_BLOCK,
            blocks=2,
            replicates=3,
        )
        result = randomized_block_design(config)

        # 2 levels * 2 blocks * 3 replicates = 12
        assert result.design_matrix.shape[0] == 12
        assert result.block_assignments is not None
        assert len(result.block_assignments) == 12


# -----------------------------------------------------------------------------
# DoEResult Serialization
# -----------------------------------------------------------------------------


class TestDoEResultSerialization:
    def test_to_dict_full_factorial(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
                Factor(name="B", low=0.0, high=1.0),
            ],
            design_type=DesignType.FULL_FACTORIAL,
        )
        result = full_factorial_design(config)
        d = result.to_dict()

        assert d["design_type"] == "FULL_FACTORIAL"
        assert d["factor_names"] == ["A", "B"]
        assert d["n_runs"] == 4
        assert d["n_factors"] == 2
        assert isinstance(d["design_matrix"], list)
        assert isinstance(d["run_order"], list)
        assert d["block_assignments"] is None

    def test_to_dict_randomized_block(self) -> None:
        config = DoEConfig(
            factors=[
                Factor(name="A", low=0.0, high=1.0),
            ],
            design_type=DesignType.RANDOMIZED_BLOCK,
            blocks=2,
        )
        result = randomized_block_design(config)
        d = result.to_dict()

        assert d["design_type"] == "RANDOMIZED_BLOCK"
        assert d["block_assignments"] is not None
        assert isinstance(d["block_assignments"], list)
        assert len(d["block_assignments"]) == d["n_runs"]

    def test_to_dict_structure(self) -> None:
        design = np.array([[0.0, 1.0], [1.0, 0.0]])
        run_order = np.array([1, 0])
        result = DoEResult(
            design_matrix=design,
            factor_names=["X", "Y"],
            design_type=DesignType.LATIN_HYPERCUBE,
            run_order=run_order,
        )
        d = result.to_dict()

        assert set(d.keys()) == {
            "design_type",
            "factor_names",
            "n_runs",
            "n_factors",
            "design_matrix",
            "run_order",
            "block_assignments",
        }
        assert d["design_matrix"] == [[0.0, 1.0], [1.0, 0.0]]
        assert d["run_order"] == [1, 0]
