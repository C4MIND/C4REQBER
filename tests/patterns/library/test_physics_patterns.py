"""
Comprehensive pytest unit tests for physics and mathematics pattern libraries.

Mocks numpy, scipy, and matplotlib to ensure fast, isolated tests.
Covers:
- PercolationPattern
- PoissonSolverPattern
- OpenQuantumPattern
- WildfirePattern
- SpectralEstimationPattern
"""

from __future__ import annotations

import asyncio
import math
import sys
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from patterns.core import Hypothesis, SimulationResult, SimulationStatus


# ═══════════════════════════════════════════════════════════════════════════════
# MockArray - realistic numpy array substitute
# ═══════════════════════════════════════════════════════════════════════════════


class MockArray:
    """Lightweight array-like object supporting tuple indexing and common ops."""

    def __init__(self, data):
        if isinstance(data, MockArray):
            self._data = data._data
        elif isinstance(data, list):
            self._data = data
        else:
            self._data = [data]
        self.shape = self._get_shape()
        self.dtype = float
        self.ndim = len(self.shape)

    def _get_shape(self):
        shape = []
        d = self._data
        while isinstance(d, list):
            shape.append(len(d))
            d = d[0] if d else None
        return tuple(shape)

    def _norm_idx(self, idx, length):
        if isinstance(idx, int):
            if idx < 0:
                idx = length + idx
            if 0 <= idx < length:
                return idx
            return None
        return idx

    def __getitem__(self, key):
        if isinstance(key, tuple):
            d = self._data
            for k in key:
                if isinstance(d, list):
                    if isinstance(k, int):
                        nk = self._norm_idx(k, len(d))
                        if nk is None:
                            return 0.0
                        d = d[nk]
                    elif isinstance(k, slice):
                        d = d[k]
                    else:
                        return 0.0
                else:
                    return 0.0
            return MockArray(d) if isinstance(d, list) else d
        if isinstance(key, int):
            if isinstance(self._data, list):
                nk = self._norm_idx(key, len(self._data))
                if nk is None:
                    return 0.0
                val = self._data[nk]
                return MockArray(val) if isinstance(val, list) else val
            return self._data
        if isinstance(key, slice):
            return MockArray(self._data[key])
        if isinstance(key, list):
            return MockArray([self[i] for i in key])
        if hasattr(key, "__iter__") and not isinstance(key, (str, bytes)):
            return MockArray([self[i] for i in key])
        return 0.0

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            d = self._data
            keys = list(key)
            for k in keys[:-1]:
                if isinstance(k, int):
                    nk = self._norm_idx(k, len(d))
                    d = d[nk]
                elif isinstance(k, slice):
                    d = d[k]
            last = keys[-1]
            if isinstance(last, slice):
                d[last] = [value] * len(d[last]) if not hasattr(value, "__iter__") or isinstance(value, (int, float, str)) else list(value)
            else:
                nk = self._norm_idx(last, len(d))
                d[nk] = value
        elif isinstance(key, int):
            nk = self._norm_idx(key, len(self._data))
            self._data[nk] = value
        elif isinstance(key, slice):
            for i, v in enumerate(value):
                self._data[key.start + i] = v

    def reshape(self, shape):
        flat = self._flat()
        total = 1
        for s in shape:
            total *= s
        if len(flat) != total:
            flat = flat + [0.0] * (total - len(flat)) if total > len(flat) else flat[:total]

        def nest(sizes, data):
            if not sizes:
                return data.pop(0) if data else 0.0
            size = sizes[0]
            return [nest(sizes[1:], data) for _ in range(size)]

        return MockArray(nest(list(shape), list(flat)))

    def __add__(self, other):
        return self._binop(other, lambda a, b: a + b)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self._binop(other, lambda a, b: a - b)

    def __rsub__(self, other):
        return self._binop(other, lambda a, b: b - a)

    def __mul__(self, other):
        return self._binop(other, lambda a, b: a * b)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return self._binop(other, lambda a, b: a / b if b != 0 else 0.0)

    def __pow__(self, other):
        return self._binop(other, lambda a, b: a ** b)

    def __neg__(self):
        return self._unaryop(lambda a: -a)

    def __abs__(self):
        return self._unaryop(lambda a: abs(a))

    def __matmul__(self, other):
        # Simple matrix multiply for 2D
        if self.ndim == 2 and hasattr(other, "ndim") and other.ndim == 2:
            n = self.shape[0]
            m = other.shape[1]
            p = self.shape[1]
            result = [[sum(self[i, k] * other[k, j] for k in range(p)) for j in range(m)] for i in range(n)]
            return MockArray(result)
        if self.ndim == 1 and hasattr(other, "ndim") and other.ndim == 1:
            return sum(a * b for a, b in zip(self._flat(), other._flat()))
        return MockArray([0.0])

    def __lt__(self, other):
        return self._binop(other, lambda a, b: a < b)

    def __le__(self, other):
        return self._binop(other, lambda a, b: a <= b)

    def __gt__(self, other):
        return self._binop(other, lambda a, b: a > b)

    def __ge__(self, other):
        return self._binop(other, lambda a, b: a >= b)

    def __eq__(self, other):
        return self._binop(other, lambda a, b: a == b)

    def __and__(self, other):
        return self._binop(other, lambda a, b: a and b)

    def __or__(self, other):
        return self._binop(other, lambda a, b: a or b)

    def __invert__(self):
        return self._unaryop(lambda a: not a)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, item):
        return item in self._flat()

    def _flat(self):
        def flatten(d):
            if not isinstance(d, list):
                yield d
            else:
                for item in d:
                    yield from flatten(item)
        return list(flatten(self._data))

    def _binop(self, other, op):
        if isinstance(other, (int, float, bool, complex)):
            return MockArray(self._map(lambda x: op(x, other)))
        if hasattr(other, "_data"):
            return MockArray(self._map2(other._data, op))
        return MockArray(self._map(lambda x: op(x, other)))

    def _unaryop(self, op):
        return MockArray(self._map(op))

    def _map(self, f):
        def apply(d):
            if not isinstance(d, list):
                return f(d)
            return [apply(x) for x in d]
        return apply(self._data)

    def _map2(self, other_data, f):
        def apply(d1, d2):
            if not isinstance(d1, list):
                return f(d1, d2)
            return [apply(x, y) for x, y in zip(d1, d2)]
        return apply(self._data, other_data)

    def flatten(self):
        return MockArray(self._flat())

    def tolist(self):
        return self._data

    def copy(self):
        import copy
        return MockArray(copy.deepcopy(self._data))

    @property
    def T(self):
        if self.ndim == 2:
            return MockArray([[self[j, i] for j in range(self.shape[0])] for i in range(self.shape[1])])
        return self

    @property
    def real(self):
        return self._unaryop(lambda x: x.real if hasattr(x, "real") else x)

    @property
    def imag(self):
        return self._unaryop(lambda x: x.imag if hasattr(x, "imag") else 0)

    def conj(self):
        return self._unaryop(lambda x: x.conjugate() if hasattr(x, "conjugate") else x)

    def sum(self, axis=None):
        if axis is None:
            return sum(self._flat())
        return sum(self._flat())

    def mean(self, axis=None):
        f = self._flat()
        return sum(f) / len(f) if f else 0.0

    def std(self, axis=None):
        f = self._flat()
        if not f:
            return 0.0
        m = sum(float(v) for v in f) / len(f)
        return math.sqrt(sum((float(v) - m) ** 2 for v in f) / len(f))

    def max(self, axis=None):
        return max(self._flat()) if self._flat() else 0.0

    def min(self, axis=None):
        return min(self._flat()) if self._flat() else 0.0

    def argmin(self, axis=None):
        f = self._flat()
        return f.index(min(f)) if f else 0

    def argmax(self, axis=None):
        f = self._flat()
        return f.index(max(f)) if f else 0

    def __repr__(self):
        return f"MockArray({self._data})"


# ═══════════════════════════════════════════════════════════════════════════════
# Shared fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def hypothesis() -> Hypothesis:
    return Hypothesis(
        title="Test hypothesis",
        description="Test description with relevant keywords",
        parameters={"lattice_size": 10, "grid_size": 16, "n_qubits": 1},
    )


@pytest.fixture
def mock_np() -> MagicMock:
    """Return a mock numpy module with realistic array behavior."""
    mock = MagicMock()
    mock.ndarray = MockArray

    def _array(data, dtype=None):
        if isinstance(data, MockArray):
            return data
        if hasattr(data, "__iter__") and not isinstance(data, (str, bytes)):
            return MockArray(list(data))
        return MockArray([data])

    mock.array = _array

    def _zeros(shape, dtype=None):
        if isinstance(shape, int):
            return MockArray([0.0] * shape)
        total = 1
        for s in shape:
            total *= s

        def nest(sizes, val):
            if not sizes:
                return val
            return [nest(sizes[1:], val) for _ in range(sizes[0])]

        return MockArray(nest(list(shape), 0.0))

    mock.zeros = _zeros

    def _ones(shape, dtype=None):
        if isinstance(shape, int):
            return MockArray([1.0] * shape)

        def nest(sizes, val):
            if not sizes:
                return val
            return [nest(sizes[1:], val) for _ in range(sizes[0])]

        return MockArray(nest(list(shape), 1.0))

    mock.ones = _ones

    def _eye(n, dtype=None):
        return MockArray([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])

    mock.eye = _eye

    def _linspace(start, stop, num):
        if num <= 1:
            return MockArray([float(start)])
        step = (stop - start) / (num - 1)
        return MockArray([float(start + i * step) for i in range(num)])

    mock.linspace = _linspace

    def _arange(*args):
        if len(args) == 1:
            start, stop, step = 0, args[0], 1
        elif len(args) == 2:
            start, stop, step = args[0], args[1], 1
        else:
            start, stop, step = args
        return MockArray([float(start + i * step) for i in range(int((stop - start) / step))])

    mock.arange = _arange

    def _mean(x, axis=None):
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return arr
        if axis == 0 and arr.ndim == 2:
            return MockArray([sum(arr[i, j] for i in range(arr.shape[0])) / arr.shape[0] for j in range(arr.shape[1])])
        return arr.mean()

    def _std(x, axis=None):
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return 0.0
        if axis == 0 and arr.ndim == 2:
            means = [sum(arr[i, j] for i in range(arr.shape[0])) / arr.shape[0] for j in range(arr.shape[1])]
            return MockArray([math.sqrt(sum((arr[i, j] - means[j]) ** 2 for i in range(arr.shape[0])) / arr.shape[0]) for j in range(arr.shape[1])])
        return arr.std()

    def _sum(x, axis=None):
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return arr
        return arr.sum()

    def _max(x, axis=None):
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return arr
        return arr.max()

    def _min(x, axis=None):
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return arr
        return arr.min()

    def _abs(x):
        if isinstance(x, (int, float, complex)):
            return abs(x)
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return abs(arr)
        return abs(arr)

    def _sqrt(x):
        if isinstance(x, (int, float, complex)):
            return math.sqrt(x) if x >= 0 else 0.0
        if isinstance(x, MockArray):
            return x._unaryop(lambda v: math.sqrt(v) if v >= 0 else 0.0)
        return math.sqrt(x) if x >= 0 else 0.0

    def _log(x):
        if isinstance(x, (int, float, complex)):
            return math.log(x) if x > 0 else 0.0
        if isinstance(x, MockArray):
            return x._unaryop(lambda v: math.log(v) if v > 0 else 0.0)
        return math.log(x) if x > 0 else 0.0

    def _log2(x):
        if isinstance(x, (int, float, complex)):
            return math.log2(x) if x > 0 else 0.0
        if isinstance(x, MockArray):
            return x._unaryop(lambda v: math.log2(v) if v > 0 else 0.0)
        return math.log2(x) if x > 0 else 0.0

    def _exp(x):
        if isinstance(x, (int, float, complex)):
            return math.exp(x)
        if isinstance(x, MockArray):
            return x._unaryop(lambda v: math.exp(v))
        return math.exp(x)

    def _trace(x):
        arr = _to_mock(x)
        if isinstance(arr, (int, float, complex)):
            return arr
        if arr.ndim == 2:
            return sum(arr[i, i] for i in range(arr.shape[0]))
        return sum(arr._flat())

    def _real(x):
        if isinstance(x, complex):
            return x.real
        if isinstance(x, (int, float)):
            return x
        arr = _to_mock(x)
        if isinstance(arr, complex):
            return arr.real
        if isinstance(arr, (int, float)):
            return arr
        return arr.real

    def _argmin(x, axis=None):
        arr = _to_mock(x)
        return arr.argmin()

    def _argmax(x, axis=None):
        arr = _to_mock(x)
        return arr.argmax()

    def _random(shape):
        if isinstance(shape, int):
            return MockArray([0.5] * shape)
        total = 1
        for s in shape:
            total *= s

        def nest(sizes):
            if not sizes:
                return 0.5
            return [nest(sizes[1:]) for _ in range(sizes[0])]

        return MockArray(nest(list(shape)))

    mock.random = _random

    def _meshgrid(*xi, indexing="xy"):
        # Return two MockArrays for 2D meshgrid
        x = xi[0] if hasattr(xi[0], "__iter__") else [xi[0]]
        y = xi[1] if hasattr(xi[1], "__iter__") else [xi[1]]
        nx, ny = len(x), len(y)
        X = [[float(x[j] if indexing == "xy" else x[i]) for j in range(ny)] for i in range(nx)]
        Y = [[float(y[i] if indexing == "xy" else y[j]) for j in range(ny)] for i in range(nx)]
        return MockArray(X), MockArray(Y)

    mock.meshgrid = _meshgrid

    def _hanning(n):
        return MockArray([0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) if n > 1 else 1.0 for i in range(n)])

    mock.hanning = _hanning
    mock.hamming = _hanning
    mock.blackman = _hanning
    mock.bartlett = _hanning

    def _fft_fft(x, n=None):
        size = n if n is not None else (len(x) if hasattr(x, "__len__") else 1)
        return MockArray([complex(1.0, 0.0)] * size)

    mock.fft.fft = _fft_fft

    def _fftfreq(n, d):
        return MockArray([float(i) / (n * d) for i in range(n)])

    mock.fft.fftfreq = _fftfreq

    def _polyfit(x, y, deg):
        return MockArray([0.0] * (deg + 1))

    mock.polyfit = _polyfit

    def _polyval(p, x):
        return sum(c * (x ** i) for i, c in enumerate(reversed(p._flat() if hasattr(p, "_flat") else p)))

    mock.polyval = _polyval

    def _linalg_eigvalsh(a):
        arr = _to_mock(a)
        n = arr.shape[0] if arr.ndim >= 1 else 1
        return MockArray([1.0 / n] * n)

    def _linalg_eigh(a):
        arr = _to_mock(a)
        n = arr.shape[0] if arr.ndim >= 1 else 1
        return _linalg_eigvalsh(a), _eye(n)

    def _linalg_norm(a):
        if isinstance(a, MockArray):
            return math.sqrt(sum(v ** 2 for v in a._flat()))
        return abs(a)

    mock.linalg.eigvalsh = _linalg_eigvalsh
    mock.linalg.eigh = _linalg_eigh
    mock.linalg.norm = _linalg_norm
    mock.linalg.LinAlgError = Exception
    mock.linalg.inv = lambda a: a

    def _sinc(x):
        if isinstance(x, MockArray):
            return x._unaryop(lambda v: 1.0 if abs(v) < 1e-10 else math.sin(math.pi * v) / (math.pi * v))
        return 1.0 if abs(x) < 1e-10 else math.sin(math.pi * x) / (math.pi * x)

    mock.sinc = _sinc

    def _clip(a, a_min, a_max):
        arr = _to_mock(a)
        return arr._unaryop(lambda v: max(a_min, min(a_max, v)))

    mock.clip = _clip

    def _roll(a, shift, axis=None):
        return _to_mock(a)

    mock.roll = _roll

    def _where(condition, x=None, y=None):
        cond = _to_mock(condition)
        if x is None and y is None:
            # Single-argument form: return indices of True values
            flat = cond._flat()
            indices = [i for i, v in enumerate(flat) if v]
            if cond.ndim == 1:
                return (MockArray(indices),)
            elif cond.ndim == 2:
                rows = [i // cond.shape[1] for i in indices]
                cols = [i % cond.shape[1] for i in indices]
                return (MockArray(rows), MockArray(cols))
            return (MockArray(indices),)
        return cond._binop(0, lambda c, _: x if c else y)

    mock.where = _where
    mock.isrealobj = lambda x: True
    mock.isclose = lambda a, b, atol=1e-8: abs(a - b) <= atol if not hasattr(a, "_flat") else all(abs(x - y) <= atol for x, y in zip(_to_mock(a)._flat(), _to_mock(b)._flat()))
    mock.allclose = lambda a, b, atol=1e-8: all(abs(x - y) <= atol for x, y in zip(_to_mock(a)._flat(), _to_mock(b)._flat()))

    mock.pi = math.pi
    mock.cos = lambda x: math.cos(x) if not hasattr(x, "_flat") else _to_mock(x)._unaryop(math.cos)
    mock.sin = lambda x: math.sin(x) if not hasattr(x, "_flat") else _to_mock(x)._unaryop(math.sin)
    mock.tan = lambda x: math.tan(x)
    mock.sqrt = _sqrt
    mock.log = _log
    mock.log2 = _log2
    mock.exp = _exp
    mock.abs = _abs
    mock.mean = _mean
    mock.std = _std
    mock.sum = _sum
    mock.max = _max
    mock.min = _min
    mock.real = _real
    mock.trace = _trace
    mock.argmin = _argmin
    mock.argmax = _argmax
    mock.outer = lambda a, b: MockArray([[x * y for y in (_to_mock(b)._flat() if hasattr(b, "_flat") else [b])] for x in (_to_mock(a)._flat() if hasattr(a, "_flat") else [a])])

    class _RNG:
        def random(self, shape=None):
            if shape is None:
                return 0.5
            return _random(shape)

        def choice(self, a, p=None):
            return 0

        def exponential(self, scale):
            return scale

        def randn(self, *shape):
            total = 1
            for s in shape:
                total *= s
            return MockArray([0.0] * total)

        def rand(self, *shape):
            total = 1
            for s in shape:
                total *= s
            return MockArray([0.5] * total)

    mock_rng = _RNG()
    mock.random.default_rng = MagicMock(return_value=mock_rng)
    mock.random.randn = mock_rng.randn
    mock.random.rand = mock_rng.rand
    mock.random.random = lambda: 0.5
    mock.random.seed = lambda x: None
    mock.random.RandomState = lambda seed=None: mock_rng

    def _to_mock(x):
        if isinstance(x, MockArray):
            return x
        if isinstance(x, (int, float, complex, bool)) or x is None:
            return x
        if hasattr(x, "__iter__") and not isinstance(x, (str, bytes)):
            return MockArray(list(x))
        return MockArray([x])

    # For np.trapezoid - simple rectangle rule
    def _trapz(y, x=None, dx=1.0):
        arr_y = _to_mock(y)
        flat = arr_y._flat()
        if x is not None:
            arr_x = _to_mock(x)
            flat_x = arr_x._flat()
            return sum((flat_x[i+1] - flat_x[i]) * (flat[i] + flat[i+1]) / 2 for i in range(len(flat)-1))
        return sum(v * dx for v in flat)

    mock.trapz = _trapz

    def _var(x, axis=None):
        arr = _to_mock(x)
        flat = arr._flat()
        if not flat:
            return 0.0
        m = sum(flat) / len(flat)
        return sum((v - m) ** 2 for v in flat) / len(flat)

    mock.var = _var

    def _zeros_like(a, dtype=None):
        arr = _to_mock(a)
        return MockArray(arr._map(lambda _: 0.0))

    mock.zeros_like = _zeros_like

    def _full(shape, fill_value, dtype=None):
        if isinstance(shape, int):
            return MockArray([float(fill_value)] * shape)
        def nest(sizes, val):
            if not sizes:
                return val
            return [nest(sizes[1:], val) for _ in range(sizes[0])]
        return MockArray(nest(list(shape), float(fill_value)))

    mock.full = _full

    def _radians(x):
        if isinstance(x, MockArray):
            return x._unaryop(lambda v: v * math.pi / 180.0)
        return x * math.pi / 180.0

    mock.radians = _radians
    mock.degrees = lambda x: x * 180.0 / math.pi if not isinstance(x, MockArray) else x._unaryop(lambda v: v * 180.0 / math.pi)

    def _diag(v, k=0):
        arr = _to_mock(v)
        if arr.ndim == 1:
            n = len(arr) + abs(k)
            result = [[0.0] * n for _ in range(n)]
            for i, val in enumerate(arr._flat()):
                if k >= 0:
                    result[i][i + k] = val
                else:
                    result[i - k][i] = val
            return MockArray(result)
        elif arr.ndim == 2:
            n = min(arr.shape[0], arr.shape[1])
            return MockArray([arr[i, i + k] for i in range(n - abs(k))])
        return arr

    mock.diag = _diag

    def _maximum(a, b):
        arr_a = _to_mock(a)
        return arr_a._binop(b, lambda x, y: max(x, y))

    mock.maximum = _maximum
    mock.minimum = lambda a, b: _to_mock(a)._binop(b, lambda x, y: min(x, y))

    return mock


def _to_mock(x):
    if isinstance(x, MockArray):
        return x
    if isinstance(x, (int, float, complex, bool)) or x is None:
        return x
    if hasattr(x, "__iter__") and not isinstance(x, (str, bytes)):
        return MockArray(list(x))
    return MockArray([x])


@pytest.fixture
def mock_scipy() -> MagicMock:
    """Return a mock scipy module."""
    mock = MagicMock()

    class _CSR:
        def __init__(self, data, shape):
            self.shape = shape
            self._data = data

        def toarray(self):
            return MockArray([[1.0]])

        def __matmul__(self, other):
            return other

    mock.sparse.csr_matrix = lambda arg, shape=None: _CSR(arg, shape or (1, 1))
    mock.sparse.linalg.cg = lambda A, b, **kwargs: (b, 0)
    mock.stats.chi2.ppf = lambda q, df: 1.0

    def _find_peaks(x, **kwargs):
        return ([0], {"peak_heights": [1.0]})

    mock.signal.find_peaks = _find_peaks
    return mock


@pytest.fixture
def mock_plt() -> MagicMock:
    """Return a mock matplotlib.pyplot module."""
    return MagicMock()


# ═══════════════════════════════════════════════════════════════════════════════
# PercolationPattern
# ═══════════════════════════════════════════════════════════════════════════════


class TestPercolationPattern:
    """Tests for PercolationPattern with mocked numpy."""

    @pytest.fixture
    def patched_percolation(self, mock_np):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "numpy.random": mock_np.random,
            },
        ):
            from patterns.library.percolation import PercolationPattern, PercolationConfig
            yield PercolationPattern, PercolationConfig

    @pytest.mark.parametrize(
        "config_dict,expected_attrs",
        [
            (
                {"lattice_size": 10, "dimension": 2, "n_realizations": 5},
                {"lattice_size": 10, "dimension": 2, "n_realizations": 5},
            ),
            (
                {"lattice_size": 20, "dimension": 3, "algorithm": "dfs"},
                {"lattice_size": 20, "dimension": 3, "algorithm": "dfs"},
            ),
            ({}, {"lattice_size": 100, "dimension": 2}),
        ],
    )
    def test_parse_config(self, patched_percolation, config_dict, expected_attrs):
        pattern_cls, PercolationConfig = patched_percolation
        pattern = pattern_cls()
        cfg = pattern._parse_config(config_dict)
        for attr, expected in expected_attrs.items():
            assert getattr(cfg, attr) == expected

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("Percolation threshold", "Study cluster connectivity", True),
            ("Phase transition", "Critical phenomena analysis", True),
            ("Quantum mechanics", "Wave function evolution", False),
        ],
    )
    def test_can_simulate(self, patched_percolation, title, desc, expected):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        h = Hypothesis(title=title, description=desc)
        assert pattern.can_simulate(h) is expected

    @pytest.mark.asyncio
    async def test_run_success(self, patched_percolation, hypothesis):
        pattern_cls, PercolationConfig = patched_percolation
        pattern = pattern_cls()
        config = {"lattice_size": 10, "dimension": 2, "n_realizations": 2, "n_p_values": 3}
        result = await pattern.run(hypothesis, config)
        assert isinstance(result, SimulationResult)
        assert result.status == SimulationStatus.COMPLETED
        assert "percolation_threshold" in result.metrics
        assert result.logs

    @pytest.mark.asyncio
    async def test_run_with_invalid_config(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        h = Hypothesis(title="percolation", description="cluster analysis")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    def test_find_clusters_union_find_2d(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        occupied = MockArray([[True, True], [True, True]])
        clusters = pattern._find_clusters_union_find(occupied, 2, 2)
        assert isinstance(clusters, dict)

    def test_find_clusters_union_find_3d(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        occupied = MockArray([[[True, True], [True, True]], [[True, True], [True, True]]])
        clusters = pattern._find_clusters_union_find(occupied, 2, 3)
        assert isinstance(clusters, dict)

    def test_find_clusters_dfs_2d(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        occupied = MockArray([[True, True], [True, True]])
        clusters = pattern._find_clusters_dfs(occupied, 2, 2)
        assert isinstance(clusters, dict)

    def test_check_percolation_2d(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        clusters = {0: {(0, 0), (1, 0), (2, 0)}}
        assert pattern._check_percolation(clusters, 3, 2) is True

    def test_check_percolation_3d(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        clusters = {0: {(0, 0, 0), (1, 0, 0), (2, 0, 0)}}
        assert pattern._check_percolation(clusters, 3, 3) is True

    def test_analyze_results_empty(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        pattern.results_by_p = {}
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert result["logs"] == ["No results"]

    def test_analyze_results_with_data(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        pattern.config = MagicMock(lattice_size=10, dimension=2, n_realizations=100)
        pattern.results_by_p = {
            0.4: {"percolation_prob": 0.3, "max_cluster_size": 0.1, "avg_cluster_size": 5.0},
            0.6: {"percolation_prob": 0.7, "max_cluster_size": 0.5, "avg_cluster_size": 20.0},
        }
        result = pattern._analyze_results()
        assert "percolation_threshold" in result["metrics"]
        assert "logs" in result

    def test_calculate_confidence(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        results = {
            "metrics": {
                "n_realizations": 500,
                "threshold_error": 0.01,
                "lattice_size": 200,
            }
        }
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 1.0

    def test_estimate_resources(self, patched_percolation):
        pattern_cls, _ = patched_percolation
        pattern = pattern_cls()
        h = Hypothesis(parameters={"lattice_size": 100, "dimension": 2, "n_realizations": 100})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "estimated_time_seconds" in resources


# ═══════════════════════════════════════════════════════════════════════════════
# PoissonSolverPattern
# ═══════════════════════════════════════════════════════════════════════════════


class TestPoissonSolverPattern:
    """Tests for PoissonSolverPattern with mocked numpy and scipy."""

    @pytest.fixture
    def patched_poisson(self, mock_np, mock_scipy):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "scipy": mock_scipy,
                "scipy.sparse": mock_scipy.sparse,
                "scipy.sparse.linalg": mock_scipy.sparse.linalg,
            },
        ):
            from patterns.library.poisson_solver import PoissonSolverPattern, PoissonConfig
            yield PoissonSolverPattern, PoissonConfig

    @pytest.mark.parametrize(
        "config_dict,expected",
        [
            ({"grid_size": 64, "equation": "laplace"}, {"nx": 64, "equation": "laplace"}),
            ({"dimensions": "3d", "grid_size": 32}, {"nx": 32, "ny": 32, "nz": 32}),
            ({}, {"nx": 128, "equation": "poisson"}),
        ],
    )
    def test_parse_config(self, patched_poisson, config_dict, expected):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        cfg = pattern._parse_config(config_dict)
        for attr, val in expected.items():
            assert getattr(cfg, attr) == val

    @pytest.mark.asyncio
    async def test_run_multigrid(self, patched_poisson, hypothesis):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        config = {"grid_size": 16, "equation": "poisson", "max_iterations": 2}
        result = await pattern.run(hypothesis, config)
        assert isinstance(result, SimulationResult)
        assert result.status == SimulationStatus.COMPLETED
        assert "iterations" in result.metrics

    @pytest.mark.asyncio
    async def test_run_direct_solver(self, patched_poisson, hypothesis):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        config = {"grid_size": 16, "use_direct": True, "max_iterations": 2}
        result = await pattern.run(hypothesis, config)
        assert isinstance(result, SimulationResult)
        assert result.status == SimulationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_failure_empty_config(self, patched_poisson):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        result = await pattern.run(Hypothesis(), {})
        assert result.status == SimulationStatus.COMPLETED

    def test_can_simulate_matching(self, patched_poisson):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        h = Hypothesis(title="Poisson solver", description="electrostatic potential")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_non_matching(self, patched_poisson):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        h = Hypothesis(title="Quantum mechanics", description="wave function")
        assert pattern.can_simulate(h) is False

    def test_calculate_confidence(self, patched_poisson):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        results = {
            "metrics": {
                "converged": 1.0,
                "residual_ratio": 1e-7,
                "conservation_error": 1e-12,
                "iterations": 20,
            }
        }
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 1.0

    def test_estimate_resources(self, patched_poisson):
        pattern_cls, _ = patched_poisson
        pattern = pattern_cls()
        h = Hypothesis(parameters={"grid_size": 128, "max_iterations": 100})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources

    def test_coarsen_config(self, patched_poisson):
        pattern_cls, PoissonConfig = patched_poisson
        pattern = pattern_cls()
        cfg = PoissonConfig(nx=64, ny=64)
        coarse = pattern._coarsen_config(cfg)
        assert coarse.nx == 32
        assert coarse.ny == 32


# ═══════════════════════════════════════════════════════════════════════════════
# OpenQuantumPattern
# ═══════════════════════════════════════════════════════════════════════════════


class TestOpenQuantumPattern:
    """Tests for OpenQuantumPattern with mocked numpy."""

    @pytest.fixture
    def patched_open_quantum(self, mock_np):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "numpy.random": mock_np.random,
            },
        ):
            from patterns.library.open_quantum import OpenQuantumPattern, OpenQuantumConfig
            yield OpenQuantumPattern, OpenQuantumConfig

    @pytest.mark.parametrize(
        "config_dict,expected",
        [
            ({"n_qubits": 2, "t_final": 5.0}, {"n_qubits": 2, "hilbert_dim": 4, "t_final": 5.0}),
            ({"method": "jump", "n_trajectories": 50}, {"method": "jump", "n_trajectories": 50}),
            ({"initial_state": "excited"}, {"initial_state": "excited"}),
            ({}, {"n_qubits": 1, "hilbert_dim": 2}),
        ],
    )
    def test_parse_config(self, patched_open_quantum, config_dict, expected):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        cfg = pattern._parse_config(config_dict)
        for attr, val in expected.items():
            assert getattr(cfg, attr) == val

    @pytest.mark.asyncio
    async def test_run_lindblad(self, patched_open_quantum, hypothesis, mock_np):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        pattern.rng = mock_np.random.default_rng()
        config = {"n_qubits": 1, "t_final": 1.0, "dt": 0.5, "method": "lindblad"}
        result = await pattern.run(hypothesis, config)
        assert isinstance(result, SimulationResult)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_population" in result.metrics

    @pytest.mark.asyncio
    async def test_run_quantum_jump(self, patched_open_quantum, hypothesis, mock_np):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        pattern.rng = mock_np.random.default_rng()
        config = {"n_qubits": 1, "t_final": 1.0, "dt": 0.5, "method": "jump", "n_trajectories": 2}
        result = await pattern.run(hypothesis, config)
        assert isinstance(result, SimulationResult)
        assert result.status == SimulationStatus.COMPLETED
        assert "final_population" in result.metrics

    @pytest.mark.asyncio
    async def test_run_failure_empty_config(self, patched_open_quantum, mock_np):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        pattern.rng = mock_np.random.default_rng()
        result = await pattern.run(Hypothesis(), {})
        assert result.status == SimulationStatus.COMPLETED

    def test_can_simulate_matching(self, patched_open_quantum):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        h = Hypothesis(title="Open quantum", description="Lindblad master equation")
        assert pattern.can_simulate(h) is True

    def test_can_simulate_non_matching(self, patched_open_quantum):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        h = Hypothesis(title="Classical mechanics", description="Newtonian physics")
        assert pattern.can_simulate(h) is False

    def test_initialize_density_matrix(self, patched_open_quantum):
        pattern_cls, OpenQuantumConfig = patched_open_quantum
        pattern = pattern_cls()
        cfg = OpenQuantumConfig(initial_state="ground")
        rho = pattern._initialize_density_matrix(cfg)
        assert rho[0, 0] == 1.0

        cfg = OpenQuantumConfig(initial_state="excited")
        rho = pattern._initialize_density_matrix(cfg)
        assert rho[-1, -1] == 1.0

        cfg = OpenQuantumConfig(initial_state="mixed")
        rho = pattern._initialize_density_matrix(cfg)
        assert rho[0, 0] == rho[1][1]

    def test_build_hamiltonian(self, patched_open_quantum):
        pattern_cls, OpenQuantumConfig = patched_open_quantum
        pattern = pattern_cls()
        cfg = OpenQuantumConfig(n_qubits=1, omega=2.0)
        H = pattern._build_hamiltonian(cfg)
        assert H.ndim == 2
        assert H.shape[0] == 2
        assert H.shape[1] == 2

    def test_build_jump_operators(self, patched_open_quantum):
        pattern_cls, OpenQuantumConfig = patched_open_quantum
        pattern = pattern_cls()
        cfg = OpenQuantumConfig(n_qubits=1, T1=100.0, T2=50.0)
        ops = pattern._build_jump_operators(cfg)
        assert isinstance(ops, list)

    def test_calculate_purity(self, patched_open_quantum):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        rho = MockArray([[0.5, 0.0], [0.0, 0.5]])
        purity = pattern._calculate_purity(rho)
        assert 0 <= purity <= 1.0

    def test_calculate_confidence(self, patched_open_quantum):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        results = {
            "metrics": {
                "final_purity": 0.8,
                "final_population": 0.5,
                "n_steps": 200,
                "T1_input": 100.0,
                "T1_measured": 105.0,
            }
        }
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 1.0

    def test_estimate_resources(self, patched_open_quantum):
        pattern_cls, _ = patched_open_quantum
        pattern = pattern_cls()
        h = Hypothesis(parameters={"n_qubits": 2, "t_final": 10.0, "dt": 0.01, "method": "lindblad"})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources


# ═══════════════════════════════════════════════════════════════════════════════
# WildfirePattern
# ═══════════════════════════════════════════════════════════════════════════════


class TestWildfirePattern:
    """Tests for WildfirePattern with mocked numpy."""

    @pytest.fixture
    def patched_wildfire(self, mock_np):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "numpy.random": mock_np.random,
            },
        ):
            from patterns.library.wildfire import WildfirePattern, WildfireConfig
            yield WildfirePattern, WildfireConfig

    @pytest.mark.parametrize(
        "config_kwargs,expected",
        [
            ({"nx": 50, "ny": 50}, {"nx": 50, "ny": 50}),
            ({"fuel_type": "grass", "wind_speed": 20.0}, {"fuel_type": "grass", "wind_speed": 20.0}),
            ({"spotting_enabled": False}, {"spotting_enabled": False}),
        ],
    )
    def test_config_init(self, patched_wildfire, config_kwargs, expected):
        _, WildfireConfig = patched_wildfire
        cfg = WildfireConfig(**config_kwargs)
        for attr, val in expected.items():
            assert getattr(cfg, attr) == val

    def test_pattern_init(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        cfg = WildfireConfig(nx=10, ny=10)
        pattern = WildfirePattern(cfg)
        assert pattern.config.nx == 10
        assert pattern.config.ny == 10

    def test_rothermel_ros(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig())
        ros = pattern._rothermel_ros()
        assert isinstance(ros, float)
        assert ros > 0

    def test_slope_factor(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig(slope=0.2))
        sf = pattern._slope_factor(5, 5)
        assert isinstance(sf, float)

    def test_fire_intensity_calc(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig())
        intensity = pattern._fire_intensity_calc(10.0)
        assert isinstance(intensity, float)
        assert intensity > 0

    def test_spotting(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig(spotting_enabled=True))
        pattern.fire_intensity = MockArray([[0.0] * 10 for _ in range(10)])
        pattern.fire_intensity[5, 5] = 5000.0
        n_before = len(pattern.spot_fires)
        pattern._spotting([(5, 5)], 1.0)
        assert len(pattern.spot_fires) >= n_before

    def test_crown_fire_transition(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig(crown_fire_enabled=True, fuel_type="conifer"))
        pattern.fire_intensity = MockArray([[0.0] * 10 for _ in range(10)])
        pattern.fire_intensity[5, 5] = 5000.0
        pattern._crown_fire_transition()
        assert pattern.crown_fire[5, 5] is True

    def test_burned_area(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig(nx=10, ny=10))
        pattern.fuel = MockArray([[0.0] * 10 for _ in range(10)])
        area = pattern._calculate_burned_area()
        assert isinstance(area, float)

    def test_fire_perimeter(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig(nx=10, ny=10))
        pattern.fuel = MockArray([[1.0] * 10 for _ in range(10)])
        for i in range(3, 7):
            for j in range(3, 7):
                pattern.fuel[i, j] = 0.0
        perimeter = pattern._calculate_fire_perimeter()
        assert isinstance(perimeter, float)
        assert perimeter >= 0

    def test_suppression(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        pattern = WildfirePattern(WildfireConfig(suppression_enabled=True, suppression_start=0.5))
        pattern.fire_intensity = MockArray([[100.0] * 10 for _ in range(10)])
        pattern._suppression(1.0)
        flat = pattern.fire_intensity._flat()
        assert all(v <= 100.0 for v in flat)

    def test_run(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        cfg = WildfireConfig(nx=10, ny=10, hours=1, dt=60, output_interval=1)
        pattern = WildfirePattern(cfg)
        result = pattern.run()
        assert isinstance(result, dict)
        assert "burned_area_ha" in result
        assert "final_state" in result
        assert "fire_behavior" in result
        assert result["final_state"]["total_burned_ha"] >= 0

    def test_run_with_hypothesis(self, patched_wildfire):
        WildfirePattern, WildfireConfig = patched_wildfire
        cfg = WildfireConfig(nx=10, ny=10, hours=1, dt=60, output_interval=1)
        pattern = WildfirePattern(cfg)
        hypothesis = {"wind_speed": 30.0}
        result = pattern.run(hypothesis)
        assert isinstance(result, dict)
        assert "time_hours" in result

    def test_metadata(self, patched_wildfire):
        WildfirePattern, _ = patched_wildfire
        meta = WildfirePattern.get_metadata()
        assert meta["id"] == "wildfire"
        assert "parameters" in meta


# ═══════════════════════════════════════════════════════════════════════════════
# SpectralEstimationPattern
# ═══════════════════════════════════════════════════════════════════════════════


class TestSpectralEstimationPattern:
    """Tests for SpectralEstimationPattern with mocked numpy and scipy."""

    @pytest.fixture
    def patched_spectral(self, mock_np, mock_scipy):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "scipy": mock_scipy,
                "scipy.signal": mock_scipy.signal,
                "scipy.stats": mock_scipy.stats,
            },
        ):
            from patterns.library.spectral_estimation import (
                SpectralEstimationPattern,
                SpectralEstimationConfig,
                SpectralMethod,
            )
            yield SpectralEstimationPattern, SpectralEstimationConfig, SpectralMethod

    @pytest.mark.parametrize(
        "method_name,expected_method",
        [
            ("PERIODOGRAM", "periodogram"),
            ("WELCH", "welch"),
            ("MTM", "multitaper"),
            ("BARTLETT", "bartlett"),
        ],
    )
    def test_config_method(self, patched_spectral, method_name, expected_method):
        _, SpectralEstimationConfig, SpectralMethod = patched_spectral
        method = getattr(SpectralMethod, method_name)
        cfg = SpectralEstimationConfig(method=method)
        assert cfg.method == method
        assert cfg.method.value == expected_method

    def test_pattern_init(self, patched_spectral):
        SpectralEstimationPattern, SpectralEstimationConfig, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        assert pattern.frequencies is None
        assert pattern.psd is None

    def test_generate_test_signal(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        signal = pattern._generate_test_signal()
        assert isinstance(signal, MockArray)
        assert len(signal) == pattern.config.n_samples

    def test_get_window(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        for window_name in ["hann", "hamming", "blackman", "bartlett", "boxcar", "unknown"]:
            cfg = pattern.config
            cfg.window = window_name
            w = pattern._get_window(64)
            assert len(w) == 64

    def test_detrend_constant(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        x = MockArray([5.0] * 100)
        y = pattern._detrend(x)
        assert all(abs(v) < 1e-10 for v in y._flat())

    def test_detrend_linear(self, patched_spectral):
        SpectralEstimationPattern, SpectralEstimationConfig, _ = patched_spectral
        cfg = SpectralEstimationConfig(detrend="linear")
        pattern = SpectralEstimationPattern(cfg)
        x = MockArray(list(range(100)))
        y = pattern._detrend(x)
        assert all(abs(v) < 1e-10 for v in y._flat())

    @pytest.mark.parametrize(
        "method",
        ["periodogram", "welch", "multitaper", "bartlett"],
    )
    def test_run_methods(self, patched_spectral, method):
        SpectralEstimationPattern, SpectralEstimationConfig, SpectralMethod = patched_spectral
        method_map = {
            "periodogram": SpectralMethod.PERIODOGRAM,
            "welch": SpectralMethod.WELCH,
            "multitaper": SpectralMethod.MTM,
            "bartlett": SpectralMethod.BARTLETT,
        }
        cfg = SpectralEstimationConfig(method=method_map[method], n_samples=256, nperseg=64, noverlap=32)
        pattern = SpectralEstimationPattern(cfg)
        result = pattern.run()
        assert isinstance(result, dict)
        assert result["method"] == method
        assert "frequencies" in result
        assert "psd" in result
        assert "peak_frequencies" in result
        assert "total_power" in result

    def test_run_with_signal(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        signal = MockArray([1.0] * 256)
        result = pattern.run({"signal": signal})
        assert isinstance(result, dict)
        assert "psd" in result
        assert "spectral_centroid" in result
        assert "spectral_bandwidth" in result

    def test_compute_confidence_intervals(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        psd = MockArray([1.0, 2.0, 3.0])
        lower, upper = pattern._compute_confidence_intervals(psd)
        assert len(lower) == len(psd)
        assert len(upper) == len(psd)

    def test_format_output(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        x = MockArray([1.0] * 64)
        freqs = MockArray([0.0, 1.0, 2.0])
        psd = MockArray([1.0, 2.0, 3.0])
        result = pattern._format_output(x, freqs, psd)
        assert "method" in result
        assert "frequencies" in result
        assert "psd" in result
        assert "config" in result

    def test_metadata(self, patched_spectral):
        _, _, SpectralMethod = patched_spectral
        SpectralEstimationPattern, _, _ = patched_spectral
        meta = SpectralEstimationPattern.get_metadata()
        assert meta["id"] == "spectral_estimation"
        assert "parameters" in meta

    def test_dpss_tapers(self, patched_spectral):
        SpectralEstimationPattern, _, _ = patched_spectral
        pattern = SpectralEstimationPattern()
        tapers = pattern._dpss_tapers(64, 4.0, 8)
        assert len(tapers) == 8


# ═══════════════════════════════════════════════════════════════════════════════
# Integration / cross-pattern tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPatternIntegration:
    """Cross-pattern integration tests."""

    def test_all_patterns_have_run_method(self, mock_np, mock_scipy):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "numpy.random": mock_np.random,
                "scipy": mock_scipy,
                "scipy.sparse": mock_scipy.sparse,
                "scipy.sparse.linalg": mock_scipy.sparse.linalg,
                "scipy.signal": mock_scipy.signal,
                "scipy.stats": mock_scipy.stats,
            },
        ):
            from patterns.library.percolation import PercolationPattern
            from patterns.library.poisson_solver import PoissonSolverPattern
            from patterns.library.open_quantum import OpenQuantumPattern
            from patterns.library.wildfire import WildfirePattern
            from patterns.library.spectral_estimation import SpectralEstimationPattern

            assert hasattr(PercolationPattern, "run")
            assert hasattr(PoissonSolverPattern, "run")
            assert hasattr(OpenQuantumPattern, "run")
            assert hasattr(WildfirePattern, "run")
            assert hasattr(SpectralEstimationPattern, "run")

    def test_all_patterns_return_dict_or_simresult(self, mock_np, mock_scipy):
        with patch.dict(
            "sys.modules",
            {
                "numpy": mock_np,
                "numpy.random": mock_np.random,
                "scipy": mock_scipy,
                "scipy.sparse": mock_scipy.sparse,
                "scipy.sparse.linalg": mock_scipy.sparse.linalg,
                "scipy.signal": mock_scipy.signal,
                "scipy.stats": mock_scipy.stats,
            },
        ):
            from patterns.library.wildfire import WildfirePattern, WildfireConfig
            from patterns.library.spectral_estimation import SpectralEstimationPattern


            wf = WildfirePattern(WildfireConfig(nx=10, ny=10, hours=1, dt=60, output_interval=1))
            result = wf.run()
            assert isinstance(result, dict)

            se = SpectralEstimationPattern()
            result = se.run()
            assert isinstance(result, dict)
