"""Design of Experiments (DoE) for C4REQBER.

Provides factorial designs, Latin Hypercube Sampling, Response Surface
Methodology (central composite), and randomized block designs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import numpy as np
from numpy.typing import NDArray


class DesignType(Enum):
    """DesignType."""
    FULL_FACTORIAL = auto()
    FRACTIONAL_FACTORIAL = auto()
    LATIN_HYPERCUBE = auto()
    CENTRAL_COMPOSITE = auto()
    RANDOMIZED_BLOCK = auto()


@dataclass(frozen=True)
class Factor:
    """Factor."""
    name: str
    low: float
    high: float
    levels: int = 2

    def validate(self) -> None:
        """Validate."""
        if self.low >= self.high:
            raise ValueError(f"Factor {self.name}: low must be < high")
        if self.levels < 2:
            raise ValueError(f"Factor {self.name}: levels must be >= 2")


@dataclass(frozen=True)
class DoEConfig:
    """DoEConfig."""
    factors: list[Factor]
    design_type: DesignType
    replicates: int = 1
    random_seed: int | None = None
    # Fractional factorial specific
    resolution: int | None = None
    # LHS specific
    samples: int = 10
    # CCD specific
    alpha: str | float = "rotatable"
    center_points: int = 4
    # Block design specific
    blocks: int | None = None

    def validate(self) -> None:
        """Validate."""
        if not self.factors:
            raise ValueError("At least one factor required")
        for f in self.factors:
            f.validate()
        if self.replicates < 1:
            raise ValueError("replicates must be >= 1")
        if self.design_type == DesignType.LATIN_HYPERCUBE and self.samples < 1:
            raise ValueError("samples must be >= 1")
        if self.design_type == DesignType.FRACTIONAL_FACTORIAL:
            if self.resolution is None:
                raise ValueError("resolution required for fractional factorial")
            if self.resolution < 3:
                raise ValueError("resolution must be >= 3")


@dataclass(frozen=True)
class DoEResult:
    """DoEResult."""
    design_matrix: NDArray[np.float64]
    factor_names: list[str]
    design_type: DesignType
    run_order: NDArray[np.int64]
    block_assignments: NDArray[np.int64] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_type": self.design_type.name,
            "factor_names": self.factor_names,
            "n_runs": self.design_matrix.shape[0],
            "n_factors": self.design_matrix.shape[1],
            "design_matrix": self.design_matrix.tolist(),
            "run_order": self.run_order.tolist(),
            "block_assignments": (
                self.block_assignments.tolist() if self.block_assignments is not None else None
            ),
        }


def _validate_and_encode(
    factors: list[Factor],
) -> tuple[list[str], NDArray[np.float64], NDArray[np.float64], list[int]]:
    names = [f.name for f in factors]
    lows = np.array([f.low for f in factors], dtype=np.float64)
    highs = np.array([f.high for f in factors], dtype=np.float64)
    levels = [f.levels for f in factors]
    return names, lows, highs, levels


def full_factorial_design(config: DoEConfig) -> DoEResult:
    """Full factorial design."""
    config.validate()
    names, lows, highs, levels = _validate_and_encode(config.factors)
    grids = [np.linspace(0, 1, lv) for lv in levels]
    mesh = np.meshgrid(*grids, indexing="ij")
    design = np.column_stack([m.ravel() for m in mesh])
    design = lows + design * (highs - lows)
    if config.replicates > 1:
        design = np.repeat(design, config.replicates, axis=0)
    rng = np.random.default_rng(config.random_seed)
    run_order = rng.permutation(len(design))
    design = design[run_order]
    return DoEResult(
        design_matrix=design,
        factor_names=names,
        design_type=DesignType.FULL_FACTORIAL,
        run_order=run_order,
    )


def fractional_factorial_design(config: DoEConfig) -> DoEResult:
    """Fractional factorial design."""
    config.validate()
    if config.resolution is None:
        raise ValueError("resolution required")
    names, lows, highs, _levels = _validate_and_encode(config.factors)
    k = len(config.factors)
    p = max(1, k - config.resolution + 1)
    full_runs = 2**k
    fraction = 2**p
    n_runs = full_runs // fraction
    if n_runs < 2**config.resolution:
        n_runs = 2**config.resolution
        p = int(np.log2(full_runs / n_runs))
    design = np.zeros((n_runs, k), dtype=np.float64)
    basic = np.array(
        np.meshgrid(*[np.array([-1, 1])] * (k - p), indexing="ij")
    ).T.reshape(-1, k - p)
    design[:, : k - p] = basic[:n_runs]
    for i in range(k - p, k):
        col_idx = (i - (k - p)) % (k - p)
        design[:, i] = design[:, col_idx]
    design = (design + 1) / 2
    design = lows + design * (highs - lows)
    if config.replicates > 1:
        design = np.repeat(design, config.replicates, axis=0)
    rng = np.random.default_rng(config.random_seed)
    run_order = rng.permutation(len(design))
    design = design[run_order]
    return DoEResult(
        design_matrix=design,
        factor_names=names,
        design_type=DesignType.FRACTIONAL_FACTORIAL,
        run_order=run_order,
    )


def latin_hypercube_sampling(config: DoEConfig) -> DoEResult:
    """Latin hypercube sampling."""
    config.validate()
    names, lows, highs, _levels = _validate_and_encode(config.factors)
    k = len(config.factors)
    n = config.samples
    rng = np.random.default_rng(config.random_seed)
    design = np.zeros((n, k), dtype=np.float64)
    for j in range(k):
        perm = rng.permutation(n)
        design[:, j] = (perm + rng.random(n)) / n
    design = lows + design * (highs - lows)
    if config.replicates > 1:
        design = np.repeat(design, config.replicates, axis=0)
    run_order = rng.permutation(len(design))
    design = design[run_order]
    return DoEResult(
        design_matrix=design,
        factor_names=names,
        design_type=DesignType.LATIN_HYPERCUBE,
        run_order=run_order,
    )


def central_composite_design(config: DoEConfig) -> DoEResult:
    """Central composite design."""
    config.validate()
    names, lows, highs, _levels = _validate_and_encode(config.factors)
    k = len(config.factors)
    corners = np.array(np.meshgrid(*[np.array([-1, 1])] * k, indexing="ij")).T.reshape(-1, k)
    if isinstance(config.alpha, str):
        if config.alpha == "rotatable":
            alpha_val = 2 ** (k / 4)
        elif config.alpha == "face":
            alpha_val = 1.0
        elif config.alpha == "orthogonal":
            nc = 2**k
            n0 = config.center_points
            alpha_val = ((nc + n0) * 2**k / (4 * nc)) ** 0.25 if nc > 0 else 1.0
        else:
            raise ValueError(f"Unknown alpha type: {config.alpha}")
    else:
        alpha_val = float(config.alpha)
    star = np.zeros((2 * k, k), dtype=np.float64)
    for i in range(k):
        star[2 * i, i] = -alpha_val
        star[2 * i + 1, i] = alpha_val
    center = np.zeros((config.center_points, k), dtype=np.float64)
    design = np.vstack([corners, star, center])
    design = (design + 1) / 2
    design = lows + design * (highs - lows)
    if config.replicates > 1:
        design = np.repeat(design, config.replicates, axis=0)
    rng = np.random.default_rng(config.random_seed)
    run_order = rng.permutation(len(design))
    design = design[run_order]
    return DoEResult(
        design_matrix=design,
        factor_names=names,
        design_type=DesignType.CENTRAL_COMPOSITE,
        run_order=run_order,
    )


def randomized_block_design(config: DoEConfig) -> DoEResult:
    """Randomized block design."""
    config.validate()
    if config.blocks is None or config.blocks < 2:
        raise ValueError("blocks must be >= 2 for randomized block design")
    names, lows, highs, levels = _validate_and_encode(config.factors)
    int(np.prod([lv for lv in levels]))
    n_blocks = config.blocks
    design = []
    block_assign = []
    rng = np.random.default_rng(config.random_seed)
    for b in range(n_blocks):
        grids = [np.linspace(0, 1, lv) for lv in levels]
        mesh = np.meshgrid(*grids, indexing="ij")
        block_design = np.column_stack([m.ravel() for m in mesh])
        block_design = lows + block_design * (highs - lows)
        perm = rng.permutation(len(block_design))
        block_design = block_design[perm]
        if config.replicates > 1:
            block_design = np.repeat(block_design, config.replicates, axis=0)
        design.append(block_design)
        block_assign.extend([b] * len(block_design))
    design_arr = np.vstack(design)
    block_assign_arr = np.array(block_assign, dtype=np.int64)
    run_order = rng.permutation(len(design_arr))
    design_arr = design_arr[run_order]
    block_assign_arr = block_assign_arr[run_order]
    return DoEResult(
        design_matrix=design_arr,
        factor_names=names,
        design_type=DesignType.RANDOMIZED_BLOCK,
        run_order=run_order,
        block_assignments=block_assign_arr,
    )


def generate_design(config: DoEConfig) -> DoEResult:
    """Generate design."""
    generators = {
        DesignType.FULL_FACTORIAL: full_factorial_design,
        DesignType.FRACTIONAL_FACTORIAL: fractional_factorial_design,
        DesignType.LATIN_HYPERCUBE: latin_hypercube_sampling,
        DesignType.CENTRAL_COMPOSITE: central_composite_design,
        DesignType.RANDOMIZED_BLOCK: randomized_block_design,
    }
    gen = generators.get(config.design_type)
    if gen is None:
        raise ValueError(f"Unsupported design type: {config.design_type}")
    return gen(config)
