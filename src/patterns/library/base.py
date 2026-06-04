"""
Base classes and mixins for C4REQBER patterns.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class GPUMixin:
    """
    Mixin for GPU-accelerated computations.
    Provides CUDA/Numba support for O(N^2) or higher complexity algorithms.
    """

    def __init__(self) -> None:
        self._gpu_available = False
        self._cuda = None
        self._gpu_context = None
        self._init_gpu()

    def _init_gpu(self) -> None:
        """Initialize GPU context if available."""
        try:
            import numba.cuda as cuda
            if cuda.is_available():
                self._cuda = cuda
                self._gpu_available = True
                self._gpu_context = cuda.current_context()
                logger.info(f"GPU initialized: {cuda.gpus.current.name}")
            else:
                logger.warning("CUDA not available, falling back to CPU")
        except ImportError:
            logger.warning("Numba not installed, GPU acceleration unavailable")
        except Exception as e:
            logger.warning(f"GPU initialization failed: {e}")

    @property
    def gpu_available(self) -> bool:
        """Check if GPU is available for computation."""
        return self._gpu_available

    def to_gpu(self, arr: np.ndarray) -> Any:
        """Transfer numpy array to GPU memory."""
        if not self._gpu_available:
            return arr
        return self._cuda.to_device(arr)  # type: ignore[attr-defined]

    def to_cpu(self, gpu_arr: Any) -> np.ndarray:
        """Transfer data from GPU to CPU memory."""
        if not self._gpu_available:
            return gpu_arr  # type: ignore[no-any-return]
        return gpu_arr.copy_to_host()  # type: ignore[no-any-return]

    def gpu_parallel(self, func: Any, blockspergrid: tuple, threadsperblock: tuple, *args: Any) -> None:
        """Execute function on GPU with given grid configuration."""
        if not self._gpu_available:
            raise RuntimeError("GPU not available")
        func[blockspergrid, threadsperblock](*args)


@dataclass
class BaseConfig:
    """Base configuration for all patterns."""
    name: str = "default"
    precision: str = "float64"
    max_iterations: int = 1000
    tolerance: float = 1e-6
    verbose: bool = False


class BasePattern(ABC):
    """Abstract base class for all C4REQBER patterns."""

    PATTERN_ID: str = "base"
    PATTERN_VERSION: str = "6.5.0"

    def __init__(self, config: BaseConfig | None = None) -> None:
        self.config = config or BaseConfig()
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        pass

    @abstractmethod
    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the pattern simulation."""
        pass

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata following Christopher Alexander structure."""
        return {
            "pattern_id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "context": "",
            "forces": [],
            "solution": "",
            "complexity": "",
            "domain": ""
        }


def vectorized_dot(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Vectorized dot product for array of vectors."""
    return np.einsum('...i,...i->...', a, b)  # type: ignore[no-any-return]


def vectorized_cross(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Vectorized cross product for array of vectors."""
    return np.cross(a, b)  # type: ignore[no-any-return]


def quaternion_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """
    Multiply two quaternions (or arrays of quaternions).
    q = [w, x, y, z]
    """
    w1, x1, y1, z1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
    w2, x2, y2, z2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]

    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2

    return np.stack([w, x, y, z], axis=-1)


def quaternion_conjugate(q: np.ndarray) -> np.ndarray:
    """Compute conjugate of quaternion(s)."""
    return np.stack([q[..., 0], -q[..., 1], -q[..., 2], -q[..., 3]], axis=-1)


def quaternion_rotate_vector(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """
    Rotate vector(s) v by quaternion(s) q.
    v_pure = [0, v_x, v_y, v_z]
    v_rotated = q * v_pure * q_conj
    """
    v_pure = np.concatenate([np.zeros(v.shape[:-1] + (1,)), v], axis=-1)
    q_conj = quaternion_conjugate(q)
    temp = quaternion_multiply(q, v_pure)
    result = quaternion_multiply(temp, q_conj)
    return result[..., 1:]


def rotation_matrix_from_quaternion(q: np.ndarray) -> np.ndarray:
    """Convert quaternion(s) to rotation matrix/matrices."""
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]

    R = np.empty(q.shape[:-1] + (3, 3))
    R[..., 0, 0] = 1 - 2*(y*y + z*z)
    R[..., 0, 1] = 2*(x*y - w*z)
    R[..., 0, 2] = 2*(x*z + w*y)
    R[..., 1, 0] = 2*(x*y + w*z)
    R[..., 1, 1] = 1 - 2*(x*x + z*z)
    R[..., 1, 2] = 2*(y*z - w*x)
    R[..., 2, 0] = 2*(x*z - w*y)
    R[..., 2, 1] = 2*(y*z + w*x)
    R[..., 2, 2] = 1 - 2*(x*x + y*y)

    return R
