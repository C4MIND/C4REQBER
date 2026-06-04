"""Benchmark fixtures and configuration."""
import time
import warnings

import numpy as np
import pytest


@pytest.fixture
def benchmark_timer():
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start

    return Timer()


BENCHMARK_TIMEOUT = 10  # seconds per benchmark
MC_SAMPLE_COUNT = 50000  # reduced for benchmark speed
ISING_LATTICE = 20
MD_N_ATOMS = 30
N_BODY_PARTICLES = 50
THERMAL_GRID = 20
POISSON_GRID = 32
