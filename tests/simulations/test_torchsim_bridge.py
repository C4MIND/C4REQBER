"""Tests for src/simulations/torchsim_bridge.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest


# Skip if optional dependency not available
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="torch not installed")

from simulations.torchsim_bridge import (
    MDIntegrator,
    RelaxationMethod,
    TorchSimBridge,
    TorchSimResult,
    get_torchsim_bridge,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def bridge_unavailable():
    """TorchSimBridge with availability forced to False."""
    bridge = TorchSimBridge(device="cpu")
    bridge._available = False
    bridge._initialized = True
    bridge._device = "cpu"
    return bridge


@pytest.fixture
def bridge_available():
    """TorchSimBridge with mocked backend."""
    bridge = TorchSimBridge(device="cpu")
    bridge._available = True
    bridge._initialized = True
    bridge._device = "cpu"
    bridge._torch_sim = MagicMock()
    bridge._torch = MagicMock()
    return bridge


@pytest.fixture
def mock_pattern():
    """Mock pattern with PATTERN_ID and run method."""
    pattern = MagicMock()
    pattern.PATTERN_ID = "molecular_dynamics_test"
    pattern.run = MagicMock(return_value={"status": "ok", "source": "pattern"})
    return pattern


# ═══════════════════════════════════════════════════════════════════
# Initialization & Availability
# ═══════════════════════════════════════════════════════════════════


class TestTorchSimBridgeInit:
    """Test TorchSimBridge initialization."""

    def test_init_default(self):
        bridge = TorchSimBridge()
        assert bridge._device == "auto"
        assert bridge._initialized is False

    def test_init_explicit_device(self):
        bridge = TorchSimBridge(device="cuda:0")
        assert bridge._device == "cuda:0"

    def test_lazy_init_unavailable(self, bridge_unavailable):
        bridge_unavailable._lazy_init()
        assert bridge_unavailable._available is False

    def test_is_available_false(self, bridge_unavailable):
        assert bridge_unavailable.is_available() is False

    def test_is_available_true(self, bridge_available):
        assert bridge_available.is_available() is True

    def test_device_property(self, bridge_available):
        assert bridge_available.device == "cpu"

    def test_check_availability_false(self):
        bridge = TorchSimBridge()
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            assert bridge._check_availability() is False

    def test_init_torch_sim_cpu(self, bridge_available):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        bridge_available._torch = None
        with patch.dict("sys.modules", {"torch": mock_torch}):
            bridge_available._init_torch_sim()
            assert bridge_available._device == "cpu"

    def test_init_torch_sim_cuda(self, bridge_available):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        bridge_available._torch = None
        bridge_available._device = "auto"
        with patch.dict("sys.modules", {"torch": mock_torch}):
            bridge_available._init_torch_sim()
            assert bridge_available._device == "cuda:0"

    def test_init_torch_sim_mps(self, bridge_available):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        bridge_available._torch = None
        bridge_available._device = "auto"
        with patch.dict("sys.modules", {"torch": mock_torch}):
            bridge_available._init_torch_sim()
            assert bridge_available._device == "mps"


# ═══════════════════════════════════════════════════════════════════
# Listing Methods
# ═══════════════════════════════════════════════════════════════════


class TestListingMethods:
    """Test listing supported models/integrators."""

    def test_list_supported_models(self, bridge_available):
        models = bridge_available.list_supported_models()
        assert any("mace" in m for m in models)
        assert "lennard_jones" in models
        assert "morse" in models

    def test_list_supported_integrators(self, bridge_available):
        integrators = bridge_available.list_supported_integrators()
        assert "nve" in integrators
        assert "nvt_langevin" in integrators
        assert "npt_langevin" in integrators

    def test_list_supported_relaxation_methods(self, bridge_available):
        methods = bridge_available.list_supported_relaxation_methods()
        assert "fire" in methods
        assert "gradient_descent" in methods
        assert "lbfgs" in methods
        assert "bfgs" in methods


# ═══════════════════════════════════════════════════════════════════
# TorchSimResult
# ═══════════════════════════════════════════════════════════════════


class TestTorchSimResult:
    """Test TorchSimResult dataclass."""

    def test_defaults(self):
        result = TorchSimResult(status="success", engine="torchsim", final_energy=0.0, n_atoms=1, n_steps=0)
        assert result.metrics == {}
        assert result.trajectory_path is None
        assert result.error_message is None

    def test_custom_metrics(self):
        result = TorchSimResult(
            status="success",
            engine="torchsim",
            final_energy=1.0,
            n_atoms=10,
            n_steps=100,
            metrics={"temperature": 300.0},
        )
        assert result.metrics["temperature"] == 300.0


# ═══════════════════════════════════════════════════════════════════
# Create State
# ═══════════════════════════════════════════════════════════════════


class TestCreateState:
    """Test create_state method."""

    def test_create_state_unavailable(self, bridge_unavailable):
        with pytest.raises(RuntimeError, match="TorchSim not installed"):
            bridge_unavailable.create_state([(0.0, 0.0, 0.0)], [1])

    def test_create_state_with_list(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_torch = bridge_available._torch
        mock_state = MagicMock()
        mock_state.to.return_value = mock_state
        mock_ts.SimState.return_value = mock_state
        mock_ts.units.AtomicMass.to.return_value = MagicMock()

        result = bridge_available.create_state(
            positions=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
            atomic_numbers=[1, 1],
            cell=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            pbc=True,
        )
        assert result is mock_state
        mock_state.to.assert_called_once_with("cpu")

    def test_create_state_with_tensors(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_state = MagicMock()
        mock_state.to.return_value = mock_state
        mock_ts.SimState.return_value = mock_state
        mock_ts.units.AtomicMass.to.return_value = MagicMock()

        mock_pos = MagicMock()
        mock_nums = MagicMock()
        result = bridge_available.create_state(positions=mock_pos, atomic_numbers=mock_nums)
        assert result is mock_state


# ═══════════════════════════════════════════════════════════════════
# Molecular Dynamics
# ═══════════════════════════════════════════════════════════════════


class TestMolecularDynamics:
    """Test run_molecular_dynamics method."""

    def test_md_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_molecular_dynamics({})
        assert result.status == "error"
        assert "not installed" in result.error_message

    def test_md_success(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_final_state = MagicMock()
        mock_final_state.positions.shape = [10, 3]
        mock_results = {"energy": -5.0}
        mock_ts.integrate.return_value = (mock_final_state, mock_results)

        with patch.object(bridge_available, "_create_state_from_config", return_value=MagicMock(positions=MagicMock(shape=(10, 3)))):
            with patch.object(bridge_available, "_create_model", return_value=MagicMock()):
                result = bridge_available.run_molecular_dynamics({
                    "positions": [[0.0, 0.0, 0.0]] * 10,
                    "atomic_numbers": [1] * 10,
                    "n_steps": 100,
                    "temperature": 300.0,
                })
                assert result.status == "success"
                assert result.engine == "torchsim"
                assert result.final_energy == -5.0
                assert result.n_atoms == 10
                assert result.n_steps == 100

    def test_md_error(self, bridge_available):
        with patch.object(bridge_available, "_create_state_from_config", side_effect=ValueError("bad state")):
            result = bridge_available.run_molecular_dynamics({
                "positions": [[0.0, 0.0, 0.0]],
                "atomic_numbers": [1],
            })
            assert result.status == "error"
            assert "bad state" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# Relaxation
# ═══════════════════════════════════════════════════════════════════


class TestRelaxation:
    """Test run_relaxation method."""

    def test_relaxation_unavailable(self, bridge_unavailable):
        result = bridge_unavailable.run_relaxation({})
        assert result.status == "error"
        assert "not installed" in result.error_message

    def test_relaxation_success(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_final_state = MagicMock()
        mock_final_state.positions.shape = [5, 3]
        mock_results = {"energy": -3.0, "n_steps": 50}
        mock_ts.optimize.return_value = (mock_final_state, mock_results)

        with patch.object(bridge_available, "_create_state_from_config", return_value=MagicMock(positions=MagicMock(shape=(5, 3)))):
            with patch.object(bridge_available, "_create_model", return_value=MagicMock()):
                result = bridge_available.run_relaxation({
                    "positions": [[0.0, 0.0, 0.0]] * 5,
                    "atomic_numbers": [1] * 5,
                    "method": "fire",
                    "max_steps": 500,
                })
                assert result.status == "success"
                assert result.engine == "torchsim"
                assert result.final_energy == -3.0
                assert result.n_steps == 50

    def test_relaxation_error(self, bridge_available):
        with patch.object(bridge_available, "_create_state_from_config", side_effect=KeyError("missing")):
            result = bridge_available.run_relaxation({})
            assert result.status == "error"
            assert "missing" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# Pattern Acceleration
# ═══════════════════════════════════════════════════════════════════


class TestAcceleratePattern:
    """Test accelerate_pattern method."""

    def test_accelerate_unavailable(self, bridge_unavailable, mock_pattern):
        result = bridge_unavailable.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()
        assert result["source"] == "pattern"

    def test_accelerate_not_atomistic(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "cfd_test"
        result = bridge_available.accelerate_pattern(mock_pattern, {})
        mock_pattern.run.assert_called_once()

    def test_accelerate_atomistic_md(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "molecular_dynamics_test"
        mock_result = TorchSimResult(
            status="success",
            engine="torchsim",
            final_energy=-1.0,
            n_atoms=10,
            n_steps=100,
            execution_time=1.0,
        )

        with patch.object(bridge_available, "run_molecular_dynamics", return_value=mock_result):
            result = bridge_available.accelerate_pattern(mock_pattern, {"simulation_type": "md"})
            assert result["status"] == "success"
            assert result["accelerated"] is True
            assert result["engine"] == "torchsim"

    def test_accelerate_atomistic_relaxation(self, bridge_available, mock_pattern):
        mock_pattern.PATTERN_ID = "molecular_dynamics_test"
        mock_result = TorchSimResult(
            status="success",
            engine="torchsim",
            final_energy=-1.0,
            n_atoms=10,
            n_steps=50,
            execution_time=0.5,
        )

        with patch.object(bridge_available, "run_relaxation", return_value=mock_result):
            result = bridge_available.accelerate_pattern(mock_pattern, {"simulation_type": "relaxation"})
            assert result["status"] == "success"
            assert result["accelerated"] is True

    def test_is_atomistic_by_pattern_id(self, bridge_available):
        pattern = MagicMock()
        pattern.PATTERN_ID = "atomic_structure"
        assert bridge_available._is_atomistic_pattern(pattern, {}) is True

    def test_is_atomistic_by_hypothesis_title(self, bridge_available):
        pattern = MagicMock()
        pattern.PATTERN_ID = "generic"
        assert bridge_available._is_atomistic_pattern(pattern, {"title": "molecular dynamics simulation"}) is True

    def test_is_atomistic_by_positions(self, bridge_available):
        pattern = MagicMock()
        pattern.PATTERN_ID = "generic"
        assert bridge_available._is_atomistic_pattern(pattern, {"positions": [[0.0, 0.0, 0.0]]}) is True

    def test_is_atomistic_false(self, bridge_available):
        pattern = MagicMock()
        pattern.PATTERN_ID = "weather_forecast"
        assert bridge_available._is_atomistic_pattern(pattern, {"title": "weather"}) is False

    def test_extract_atomistic_config(self, bridge_available, mock_pattern):
        mock_pattern.get_default_config = MagicMock(return_value={"temperature": 300.0, "n_steps": 1000})
        result = bridge_available._extract_atomistic_config(mock_pattern, {
            "positions": [[0.0, 0.0, 0.0]],
            "temperature": 500.0,
        })
        assert result["temperature"] == 500.0
        assert result["n_steps"] == 1000


# ═══════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════


class TestInternalHelpers:
    """Test internal helper methods."""

    def test_create_state_from_config(self, bridge_available):
        with patch.object(bridge_available, "create_state", return_value=MagicMock()) as mock_create:
            state = bridge_available._create_state_from_config({
                "positions": [[0.0, 0.0, 0.0]],
                "atomic_numbers": [1],
                "cell": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                "pbc": False,
            })
            mock_create.assert_called_once()

    def test_create_state_from_config_no_positions(self, bridge_available):
        with pytest.raises((ValueError, TypeError), match="positions required|NoneType"):
            bridge_available._create_state_from_config({})

    def test_create_model_from_config(self, bridge_available):
        model = MagicMock()
        result = bridge_available._create_model("custom_model", {"custom_model": model})
        assert result is model

    def test_create_model_dotted_name(self, bridge_available):
        with patch.object(bridge_available, "is_available", return_value=False):
            with pytest.raises(RuntimeError, match="TorchSim not available"):
                bridge_available._create_model("some.package.model", {})

    def test_create_model_lennard_jones(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_model = MagicMock()
        mock_ts.models.LennardJonesModel.return_value = mock_model
        result = bridge_available._create_model("lennard_jones", {})
        assert result is mock_model

    def test_create_model_morse(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_model = MagicMock()
        mock_ts.models.MorseModel.return_value = mock_model
        result = bridge_available._create_model("morse", {})
        assert result is mock_model

    def test_create_model_soft_sphere(self, bridge_available):
        mock_ts = bridge_available._torch_sim
        mock_model = MagicMock()
        mock_ts.models.SoftSphereModel.return_value = mock_model
        result = bridge_available._create_model("soft_sphere", {})
        assert result is mock_model

    def test_create_model_unknown(self, bridge_available):
        with pytest.raises(ValueError, match="Unknown model"):
            bridge_available._create_model("unknown_model", {})

    def test_build_integrator_kwargs_nvt(self, bridge_available):
        kwargs = bridge_available._build_integrator_kwargs("nvt_langevin", {"gamma": 0.2})
        assert kwargs["gamma"] == 0.2

    def test_build_integrator_kwargs_npt(self, bridge_available):
        kwargs = bridge_available._build_integrator_kwargs("npt_langevin", {"pressure": 2.0, "gamma": 0.3})
        assert kwargs["pressure"] == 2.0
        assert kwargs["gamma"] == 0.3

    def test_build_integrator_kwargs_nve(self, bridge_available):
        kwargs = bridge_available._build_integrator_kwargs("nve", {})
        assert "gamma" not in kwargs
        assert "pressure" not in kwargs

    def test_build_integrator_kwargs_with_timestep(self, bridge_available):
        kwargs = bridge_available._build_integrator_kwargs("nve", {"timestep": 0.5})
        assert kwargs["timestep"] == 0.5

    def test_build_integrator_kwargs_with_seed(self, bridge_available):
        kwargs = bridge_available._build_integrator_kwargs("nve", {"seed": 42})
        assert kwargs["seed"] == 42


# ═══════════════════════════════════════════════════════════════════
# Enum Classes
# ═══════════════════════════════════════════════════════════════════


class TestEnums:
    """Test MDIntegrator and RelaxationMethod enums."""

    def test_md_integrator_values(self):
        assert MDIntegrator.NVE == "nve"
        assert MDIntegrator.NVT_LANGEVIN == "nvt_langevin"
        assert MDIntegrator.NPT_LANGEVIN == "npt_langevin"

    def test_relaxation_method_values(self):
        assert RelaxationMethod.FIRE == "fire"
        assert RelaxationMethod.GRADIENT_DESCENT == "gradient_descent"
        assert RelaxationMethod.LBFGS == "lbfgs"
        assert RelaxationMethod.BFGS == "bfgs"


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════


class TestSingleton:
    """Test get_torchsim_bridge singleton."""

    def test_singleton(self):
        b1 = get_torchsim_bridge()
        b2 = get_torchsim_bridge()
        assert b1 is b2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
