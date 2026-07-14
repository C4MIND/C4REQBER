"""Tests for src/patterns/library/base.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.library.base import (
    BaseConfig,
    BasePattern,
    GPUMixin,
    quaternion_conjugate,
    quaternion_multiply,
    quaternion_rotate_vector,
    rotation_matrix_from_quaternion,
    vectorized_cross,
    vectorized_dot,
)


class TestBaseConfig:
    def test_defaults(self):
        cfg = BaseConfig()
        assert cfg.name == "default"
        assert cfg.precision == "float64"
        assert cfg.max_iterations == 1000
        assert cfg.tolerance == 1e-6
        assert cfg.verbose is False

    def test_custom_values(self):
        cfg = BaseConfig(name="custom", max_iterations=500)
        assert cfg.name == "custom"
        assert cfg.max_iterations == 500


class TestBasePattern:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BasePattern()

    def test_subclass_must_implement(self):
        class MinimalPattern(BasePattern):
            def _validate_config(self):
                pass

            def run(self, hypothesis=None):
                return {}

        mp = MinimalPattern()
        assert mp.config is not None
        assert mp.PATTERN_ID == "base"
        meta = mp.get_metadata()
        assert "pattern_id" in meta

    def test_get_metadata_structure(self):
        class MinimalPattern(BasePattern):
            def _validate_config(self):
                pass

            def run(self, hypothesis=None):
                return {}

        meta = MinimalPattern.get_metadata()
        assert "pattern_id" in meta
        assert "version" in meta
        assert "context" in meta
        assert "forces" in meta
        assert "solution" in meta
        assert "complexity" in meta
        assert "domain" in meta


class TestGPUMixin:
    def test_init_no_gpu(self):
        with patch("importlib.import_module", side_effect=ImportError):
            mixin = GPUMixin()
            assert mixin.gpu_available is False

    def test_to_gpu_no_gpu(self):
        with patch("importlib.import_module", side_effect=ImportError):
            mixin = GPUMixin()
            arr = np.array([1, 2, 3])
            result = mixin.to_gpu(arr)
            np.testing.assert_array_equal(result, arr)

    def test_to_cpu_no_gpu(self):
        with patch("importlib.import_module", side_effect=ImportError):
            mixin = GPUMixin()
            arr = np.array([1, 2, 3])
            result = mixin.to_cpu(arr)
            np.testing.assert_array_equal(result, arr)

    def test_gpu_parallel_no_gpu_raises(self):
        with patch("importlib.import_module", side_effect=ImportError):
            mixin = GPUMixin()
            with pytest.raises(RuntimeError, match="GPU not available"):
                mixin.gpu_parallel(None, (1,), (1,))


class TestVectorizedDot:
    def test_basic(self):
        a = np.array([[1, 0, 0], [0, 1, 0]])
        b = np.array([[1, 0, 0], [0, 1, 0]])
        result = vectorized_dot(a, b)
        np.testing.assert_array_almost_equal(result, [1, 1])

    def test_orthogonal(self):
        a = np.array([[1, 0, 0]])
        b = np.array([[0, 1, 0]])
        result = vectorized_dot(a, b)
        assert result[0] == 0


class TestVectorizedCross:
    def test_basic(self):
        a = np.array([[1, 0, 0]])
        b = np.array([[0, 1, 0]])
        result = vectorized_cross(a, b)
        np.testing.assert_array_almost_equal(result[0], [0, 0, 1])


class TestQuaternionMultiply:
    def test_identity(self):
        q1 = np.array([1, 0, 0, 0])
        q2 = np.array([1, 0, 0, 0])
        result = quaternion_multiply(q1, q2)
        np.testing.assert_array_almost_equal(result, [1, 0, 0, 0])

    def test_multi_array(self):
        q1 = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        q2 = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        result = quaternion_multiply(q1, q2)
        assert result.shape == (2, 4)


class TestQuaternionConjugate:
    def test_basic(self):
        q = np.array([1, 2, 3, 4])
        result = quaternion_conjugate(q)
        np.testing.assert_array_equal(result, [1, -2, -3, -4])

    def test_multi_array(self):
        q = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])
        result = quaternion_conjugate(q)
        expected = np.array([[1, -2, -3, -4], [5, -6, -7, -8]])
        np.testing.assert_array_equal(result, expected)


class TestQuaternionRotateVector:
    def test_rotate_x_axis(self):
        # 90-degree rotation around z-axis
        theta = np.pi / 2
        q = np.array([np.cos(theta / 2), 0, 0, np.sin(theta / 2)])
        v = np.array([1, 0, 0])
        result = quaternion_rotate_vector(q, v)
        np.testing.assert_array_almost_equal(result, [0, 1, 0], decimal=5)

    def test_no_rotation(self):
        q = np.array([1, 0, 0, 0])
        v = np.array([1, 2, 3])
        result = quaternion_rotate_vector(q, v)
        np.testing.assert_array_almost_equal(result, [1, 2, 3])


class TestRotationMatrixFromQuaternion:
    def test_identity(self):
        q = np.array([1, 0, 0, 0])
        R = rotation_matrix_from_quaternion(q)
        np.testing.assert_array_almost_equal(R, np.eye(3))

    def test_shape(self):
        q = np.array([[1, 0, 0, 0], [1, 0, 0, 0]])
        R = rotation_matrix_from_quaternion(q)
        assert R.shape == (2, 3, 3)
