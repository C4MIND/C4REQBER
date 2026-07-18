"""W6 proof: PARTIAL bridges are honest (labels + no fake accelerate)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def test_newton_runner_n_body_is_numpy_not_brand():
    from src.simulations.newton_runner import run_newton_simulation

    out = run_newton_simulation(
        {"type": "n_body", "num_particles": 8, "num_steps": 5, "force_numpy_fallback": True}
    )
    assert out["executed"] is True
    assert out["stub"] is False
    assert out["backend"] == "numpy_fallback"
    assert out["engine_truth"] == "not_newton_physics"
    assert out["status"] == "partial"
    assert "positions" in out["data"]


def test_newton_runner_refuses_empty_completed_for_cfd():
    from src.simulations.newton_runner import run_newton_simulation

    out = run_newton_simulation({"type": "cfd", "force_numpy_fallback": True})
    assert out["status"] == "unavailable"
    assert out["stub"] is True
    assert out["executed"] is False
    assert out["engine_truth"] == "not_newton_physics"


def test_newton_accelerate_not_true_on_numpy_fallback(monkeypatch):
    from src.simulations.newton_bridge import NewtonBridge, NewtonMode, NewtonResult

    bridge = NewtonBridge.__new__(NewtonBridge)
    bridge._mode = NewtonMode.CPU
    bridge.config = MagicMock()

    def fake_run(config):
        return NewtonResult(
            status="partial",
            mode=NewtonMode.CPU,
            data={
                "backend": "numpy_fallback",
                "engine_truth": "not_newton_physics",
                "positions": [[0, 0, 0]],
            },
            metrics={"backend": "numpy_fallback"},
        )

    pattern = SimpleNamespace(PATTERN_ID="n_body", run=lambda h: {"ok": True})
    monkeypatch.setattr(bridge, "is_available", lambda: True)
    monkeypatch.setattr(bridge, "is_gpu_mode", lambda: True)
    monkeypatch.setattr(bridge, "can_accelerate", lambda _p: True)
    monkeypatch.setattr(bridge, "run_simulation", fake_run)
    monkeypatch.setattr(
        bridge,
        "_extract_pattern_config",
        lambda p, h: {"type": "n_body"},
    )

    out = bridge.accelerate_pattern(pattern, {"type": "n_body"})
    assert out["accelerated"] is False
    assert out["engine_truth"] == "not_newton_physics"
    assert out["backend"] == "numpy_fallback"


def test_jaxsim_fallback_is_unavailable_not_success():
    from src.simulations.jaxsim_bridge import JaxSimBridge, RigidBodyConfig

    bridge = JaxSimBridge.__new__(JaxSimBridge)
    cfg = RigidBodyConfig(model_path=None, duration=0.1, dt=0.01, integrate=True)
    out = bridge._fallback_simulation(cfg)
    assert out["status"] == "unavailable"
    assert out["stub"] is True
    assert out["executed"] is False
    assert out.get("engine") != "jaxsim_fallback" or out["stub"] is True


def test_jaxsim_urdf_path_uses_from_urdf_and_marks_executed(monkeypatch):
    from src.simulations import jaxsim_bridge as jb
    from src.simulations.jaxsim_bridge import JaxSimBridge, RigidBodyConfig

    class FakeModel:
        def dof(self):
            return 2

        def kinetic_energy(self, q, qd):
            return 1.0

        def potential_energy(self, q):
            return 2.0

        def forward_dynamics(self, q, qd, tau):
            return q * 0

    class FakeSim:
        def __init__(self, model, dt=0.001):
            self.model = model
            self.dt = dt

        def set_gravity(self, g):
            return None

        def step(self, q, qd):
            return (q, qd)

    calls = {"from_urdf": 0, "step": 0}

    def fake_from_urdf(path):
        calls["from_urdf"] += 1
        assert path == "/tmp/bot.urdf"
        return FakeModel()

    real_step = FakeSim.step

    def counting_step(self, q, qd):
        calls["step"] += 1
        return real_step(self, q, qd)

    FakeSim.step = counting_step

    bridge = JaxSimBridge.__new__(JaxSimBridge)
    bridge._jaxsim = object()
    bridge._device = "cpu"
    bridge._available = True

    monkeypatch.setattr(jb, "np", np)
    # Patch imports inside method via injecting modules
    import sys
    import types

    jaxsim_mod = types.ModuleType("jaxsim")
    jaxsim_mod.Model = SimpleNamespace(from_urdf=staticmethod(fake_from_urdf))
    jaxsim_mod.Simulator = FakeSim
    jax_mod = types.ModuleType("jax")
    jnp_mod = types.ModuleType("jax.numpy")
    jnp_mod.array = np.asarray
    jnp_mod.zeros = np.zeros
    monkeypatch.setitem(sys.modules, "jaxsim", jaxsim_mod)
    monkeypatch.setitem(sys.modules, "jax", jax_mod)
    monkeypatch.setitem(sys.modules, "jax.numpy", jnp_mod)

    cfg = RigidBodyConfig(
        model_path="/tmp/bot.urdf",
        duration=0.003,
        dt=0.001,
        integrate=True,
        gravity=(0, 0, -9.81),
    )
    out = bridge._execute_rigid_body_simulation(cfg)
    assert calls["from_urdf"] == 1
    assert calls["step"] >= 1
    assert out["executed"] is True
    assert out["stub"] is False
    assert out["backend"] == "jaxsim_urdf"
    assert out["status"] == "success"


def test_nvidia_cfd_pattern_not_accelerated_as_matmul():
    from src.simulations.nvidia_bridge import NvidiaBridge

    bridge = NvidiaBridge.__new__(NvidiaBridge)
    pattern = SimpleNamespace(PATTERN_ID="cfd", run=lambda h: {"physics": True})
    out = bridge.accelerate_pattern(pattern, {"domain": "fluid"})  # no type=
    assert out["accelerated"] is False
    assert out.get("backend") == "pattern_fallback"
    assert out["data"]["physics"] is True


def test_nvidia_nccl_refuses_fake_all_reduce():
    from src.simulations.nvidia_bridge import NCCLWrapper, NvidiaBridge

    bridge = NvidiaBridge.__new__(NvidiaBridge)
    nccl = NCCLWrapper(bridge)
    nccl._world_size = 4
    with pytest.raises(NotImplementedError):
        nccl.all_reduce(np.ones(3))


def test_xarray_real_dataset_marks_executed(tmp_path):
    pytest.importorskip("xarray")
    import xarray as xr

    from src.simulations.base_adapter import SimStatus
    from src.simulations.xarray_bridge import XarrayBridge

    path = tmp_path / "t.nc"
    xr.Dataset({"temperature": (("x",), [1.0, 2.0, 3.0])}).to_netcdf(path)
    bridge = XarrayBridge()
    if not bridge.is_available():
        pytest.skip("xarray not available to adapter")
    result = bridge.run({"path": str(path), "variable": "temperature"})
    assert result.status == SimStatus.SUCCESS
    assert result.data.get("executed") is True
    assert result.data.get("stub") is False
    assert result.data.get("backend") == "xarray"
    assert result.data.get("mean") == pytest.approx(2.0)


def test_wrf_without_file_stays_stub():
    from src.simulations.base_adapter import SimStatus
    from src.simulations.wrf_bridge import WrfBridge

    bridge = WrfBridge()
    if not bridge.is_available():
        pytest.skip("wrf-python not installed")
    result = bridge.run({})
    assert result.status == SimStatus.UNAVAILABLE
    assert result.data.get("stub") is True
    assert result.data.get("executed") is False
