"""W5 proof: Vast.ai SSH exec is real (mocked OpenSSH), never fake deployed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_execute_without_host_still_unavailable():
    from src.simulations.vastai_delegate import VastAIDelegate

    delegate = VastAIDelegate(api_key="test-key-not-real")
    inst = SimpleNamespace(instance_id="i-1", host="", ssh_port=22)
    result = await delegate._execute_simulation(inst, {"engine": "newton", "remote_argv": ["true"]})
    assert result.get("status") == "unavailable"
    assert result.get("stub") is True
    assert result.get("executed") is False


@pytest.mark.asyncio
async def test_ssh_exec_calls_openssh_and_marks_executed(monkeypatch):
    """Anti-fraud: success path must invoke ssh subprocess twice (upload + run)."""
    from src.simulations.vastai_delegate import InstanceInfo, VastAIDelegate

    calls: list[tuple] = []

    class FakeProc:
        def __init__(self, rc: int, out: bytes, err: bytes = b""):
            self.returncode = rc
            self._out = out
            self._err = err

        async def communicate(self, stdin=None):
            return self._out, self._err

        def kill(self):
            return None

        async def wait(self):
            return self.returncode

    async def fake_create(*argv, **kwargs):
        calls.append(argv)
        # First call: upload (cat > ...); second: remote_argv
        if any("cat >" in str(a) for a in argv):
            return FakeProc(0, b"")
        payload = b'{"status":"completed","energy":-42.0,"executed":true,"stub":false}\n'
        return FakeProc(0, payload)

    monkeypatch.setattr(
        "src.simulations.vastai_delegate.asyncio.create_subprocess_exec",
        fake_create,
    )
    monkeypatch.setattr(
        "src.simulations.vastai_delegate.os.path.isfile",
        lambda p: False,
    )

    delegate = VastAIDelegate(api_key="test-key")
    inst = InstanceInfo(
        instance_id="42",
        price=0.4,
        gpu_name="RTX 4090",
        gpu_ram_gb=24.0,
        host="1.2.3.4",
        ssh_port=22022,
    )
    result = await delegate._execute_simulation(
        inst,
        {
            "engine": "newton",
            "remote_argv": [
                "python3",
                "-m",
                "newton_runner",
                "--config",
                "/tmp/c4_sim_config.json",
            ],
        },
    )

    assert len(calls) >= 2, f"expected upload+run ssh calls, got {len(calls)}: {calls}"
    assert all(c[0] == "ssh" for c in calls)
    assert any("22022" in c or c[c.index("-p") + 1] == "22022" for c in calls if "-p" in c)
    assert result["executed"] is True
    assert result["stub"] is False
    assert result["status"] == "completed"
    assert result.get("energy") == -42.0
    assert result.get("ssh_host") == "1.2.3.4"


@pytest.mark.asyncio
async def test_run_simulation_success_false_when_ssh_stub(monkeypatch):
    from src.simulations.vastai_delegate import InstanceInfo, SimulationResult, VastAIDelegate

    delegate = VastAIDelegate(api_key="k")

    async def fake_find(_req):
        return {"instance_id": "9", "price": 0.3, "gpu_name": "A100", "gpu_ram_gb": 40}

    async def fake_create(_id, _image):
        return InstanceInfo("9", 0.3, "A100", 40.0, "10.0.0.1", 22)

    async def fake_exec(_inst, _cfg):
        return {"status": "unavailable", "stub": True, "executed": False, "error": "nope"}

    async def fake_destroy(_id):
        return True

    monkeypatch.setattr(delegate, "find_gpu_instance", fake_find)
    monkeypatch.setattr(delegate, "_create_instance", fake_create)
    monkeypatch.setattr(delegate, "_execute_simulation", fake_exec)
    monkeypatch.setattr(delegate, "_destroy_instance", fake_destroy)

    out = await delegate.run_simulation("newton", {"remote_argv": ["true"]})
    assert isinstance(out, SimulationResult)
    assert out.success is False
    assert out.data.get("stub") is True


@pytest.mark.asyncio
async def test_vastai_runner_never_claims_deployed_without_execute(monkeypatch):
    from src.compute.vastai_runner import VastAIRunner

    runner = VastAIRunner()
    runner.api_key = "k"

    async def fake_list(max_price: float = 0.05):
        return [{"gpu_name": "RTX 4090", "dph_total": 0.4}]

    monkeypatch.setattr(runner, "list_gpus", fake_list)
    out = await runner.run_simulation("n_body", execute=False)
    assert out["status"] != "deployed"
    assert out["executed"] is False
    assert out.get("stub") is True
    assert out["status"] == "offer_only"


@pytest.mark.asyncio
async def test_ssh_empty_stdout_not_completed(monkeypatch):
    """Anti-fraud: rc=0 without JSON must not become success."""
    from src.simulations.vastai_delegate import InstanceInfo, VastAIDelegate

    class FakeProc:
        def __init__(self, rc: int, out: bytes, err: bytes = b""):
            self.returncode = rc
            self._out = out
            self._err = err

        async def communicate(self, stdin=None):
            return self._out, self._err

        def kill(self):
            return None

        async def wait(self):
            return self.returncode

    async def fake_create(*argv, **kwargs):
        if any("cat >" in str(a) for a in argv):
            return FakeProc(0, b"")
        return FakeProc(0, b"")  # empty stdout

    monkeypatch.setattr(
        "src.simulations.vastai_delegate.asyncio.create_subprocess_exec",
        fake_create,
    )
    monkeypatch.setattr(
        "src.simulations.vastai_delegate.os.path.isfile",
        lambda p: False,
    )

    delegate = VastAIDelegate(api_key="test-key")
    inst = InstanceInfo("1", 0.4, "RTX", 24.0, "9.9.9.9", 22)
    result = await delegate._execute_simulation(inst, {"engine": "newton", "remote_argv": ["true"]})
    assert result["executed"] is False
    assert result["stub"] is True
    assert result["status"] == "unavailable"


@pytest.mark.asyncio
async def test_vastai_runner_execute_true_uses_delegate(monkeypatch):
    from src.compute.vastai_runner import VastAIRunner
    from src.simulations.vastai_delegate import SimulationResult

    runner = VastAIRunner()

    async def fake_run(engine, config):
        assert engine == "newton"
        assert config.get("pattern_id") == "n_body"
        return SimulationResult(
            success=True,
            data={"status": "completed", "executed": True, "stub": False, "steps": 10},
            cost_usd=0.01,
            duration_seconds=1.5,
            logs="ok",
        )

    monkeypatch.setattr(runner._delegate, "run_simulation", fake_run)
    out = await runner.run_simulation("n_body", execute=True, engine="newton")
    assert out["executed"] is True
    assert out["success"] is True
    assert out["status"] == "completed"
    assert out["data"]["steps"] == 10
