"""Post-audit honesty regressions — bayes skip, QE availability, nvidia CPU."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest


def test_bayesian_tracker_skips_heuristic():
    from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker

    t = BayesianHypothesisTracker(hypothesis="H", prior=0.5)
    t.update(
        {
            "predicted": 1.0,
            "observed": 1.0,
            "uncertainty": 0.01,
            "heuristic": True,
        },
        "noise",
    )
    assert t.posterior == 0.5
    assert len(t.evidence_log) == 0


def test_bayesian_tracker_skips_unavailable():
    from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker

    t = BayesianHypothesisTracker(hypothesis="H", prior=0.4)
    t.update(
        {"predicted": None, "observed": None, "status": "unavailable"},
        "sim",
    )
    assert t.posterior == 0.4


def test_qe_is_available_requires_pw_x(monkeypatch):
    from src.simulations.quantum_espresso_bridge import QuantumEspressoBridge

    monkeypatch.setattr(
        "src.simulations.quantum_espresso_bridge.shutil.which",
        lambda _: None,
    )
    bridge = QuantumEspressoBridge()
    assert bridge.is_available() is False


def test_nvidia_accelerate_cpu_kernel_not_accelerated():
    from src.simulations.nvidia_bridge import CudaMode, NvidiaBridge, NvidiaBridgeResult

    bridge = NvidiaBridge.__new__(NvidiaBridge)
    bridge._mode = CudaMode.CPU

    def fake_run(config):
        return NvidiaBridgeResult(
            status="partial",
            mode=CudaMode.CPU,
            data={"backend": "numpy_cpu", "result": [[1]]},
            metrics={},
        )

    pattern = SimpleNamespace(PATTERN_ID="matmul_test", run=lambda h: {})
    bridge.run_simulation = fake_run  # type: ignore[method-assign]
    bridge.is_available = lambda: True  # type: ignore[method-assign]
    bridge.is_gpu_mode = lambda: False  # type: ignore[method-assign]
    out = bridge.accelerate_pattern(pattern, {"type": "linear_algebra"})
    assert out["accelerated"] is False
    assert out.get("backend") == "numpy_cpu"


def test_amuse_note_is_default_sanity_when_no_hyp_bodies():
    """Document honesty: AMUSE uses canned 2-body unless params provided."""
    from src.simulations.amuse_bridge import AmuseBridge

    # Read source note contract via run stub path when amuse missing
    bridge = AmuseBridge()
    if bridge.is_available():
        pytest.skip("amuse installed — canned physics path separately verified in W1")
    result = bridge.run({"evolve": True})
    assert result.data.get("stub") is True or result.status.value == "unavailable"
