from __future__ import annotations

import src.simulations.config as sc


class TestSimulationConfig:
    def test_load_returns_valid_config_without_file(self, tmp_path, monkeypatch):
        nonexistent = tmp_path / "does_not_exist" / "simulations.json"
        monkeypatch.setattr(sc, "CONFIG_PATH", nonexistent)

        cfg = sc.SimulationConfig.load()
        assert cfg.mode == "auto"
        assert cfg.cost_limit_per_run == 5.00
        assert cfg.fallback_to_protocol is True
        assert cfg.gpu_type == "RTX_4090"

    def test_can_run_gpu_returns_bool(self):
        cfg = sc.SimulationConfig()
        assert isinstance(cfg.can_run_gpu, bool)

        cfg2 = sc.SimulationConfig(local_cuda=True)
        assert cfg2.can_run_gpu is True

        cfg3 = sc.SimulationConfig(local_metal=True)
        assert cfg3.can_run_gpu is True

        cfg4 = sc.SimulationConfig(vastai_key="test-key")
        assert cfg4.can_run_gpu is True

    def test_should_run_simulations_mode_off(self):
        cfg = sc.SimulationConfig(mode="off")
        assert cfg.should_run_simulations is False

    def test_should_run_simulations_mode_cpu_only(self):
        cfg = sc.SimulationConfig(mode="cpu_only")
        assert cfg.should_run_simulations is True

    def test_should_run_simulations_mode_auto(self):
        cfg = sc.SimulationConfig(mode="auto")
        assert cfg.should_run_simulations is True

    def test_should_run_simulations_mode_gpu_no_hardware(self):
        cfg = sc.SimulationConfig(mode="gpu", local_cuda=False, local_metal=False, vastai_key="")
        assert cfg.should_run_simulations is False

    def test_should_run_simulations_mode_gpu_with_hardware(self):
        cfg = sc.SimulationConfig(mode="gpu", local_cuda=True)
        assert cfg.should_run_simulations is True

    def test_should_generate_protocol_off_with_fallback(self):
        cfg = sc.SimulationConfig(mode="off", fallback_to_protocol=True)
        assert cfg.should_generate_protocol is True

    def test_should_generate_protocol_off_no_fallback(self):
        cfg = sc.SimulationConfig(mode="off", fallback_to_protocol=False)
        assert cfg.should_generate_protocol is False

    def test_should_generate_protocol_cpu_only_no_gpu(self):
        cfg = sc.SimulationConfig(mode="cpu_only", fallback_to_protocol=True,
                                  local_cuda=False, local_metal=False, vastai_key="")
        assert cfg.should_generate_protocol is True


class TestDetectHardware:
    def test_returns_dict_with_required_keys(self):
        hw = sc.detect_hardware()
        assert isinstance(hw, dict)
        for key in ("metal", "cuda", "nvidia_gpu", "apple_gpu"):
            assert key in hw
            assert isinstance(hw[key], bool)


class TestAutoConfigure:
    def test_returns_simulation_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sc, "detect_hardware", lambda: {"metal": False, "cuda": False, "nvidia_gpu": False, "apple_gpu": False})
        nonexistent = tmp_path / "nonexistent" / "simulations.json"
        monkeypatch.setattr(sc, "CONFIG_PATH", nonexistent)

        cfg = sc.auto_configure()
        assert isinstance(cfg, sc.SimulationConfig)
        assert cfg.mode in ("auto", "gpu", "cpu_only", "off")
