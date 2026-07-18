"""W1 anti-fraud tests: STUB bridges must call real solver APIs when inputs exist.

These tests inject fake engine modules and assert mdrun / case.run / evolve_model /
pw.x (or aiida run_get_node) are invoked. Returning stub:True after a successful
mock call is a failure.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.simulations.base_adapter import SimStatus


def test_gromacs_calls_gmxapi_mdrun(tmp_path: Path) -> None:
    tpr = tmp_path / "sys.tpr"
    tpr.write_bytes(b"fake-tpr")

    md = MagicMock()
    md.output.trajectory.result.return_value = str(tmp_path / "traj.xtc")

    fake_gmx = types.ModuleType("gmxapi")
    fake_gmx.__version__ = "0.0-test"
    fake_gmx.read_tpr = MagicMock(return_value="sim-input")
    fake_gmx.modify_input = MagicMock(side_effect=lambda **kw: kw["input"])
    fake_gmx.mdrun = MagicMock(return_value=md)

    from src.simulations.gromacs_bridge import GromacsBridge

    bridge = GromacsBridge()
    with patch.dict(sys.modules, {"gmxapi": fake_gmx}):
        with patch.object(GromacsBridge, "is_available", return_value=True):
            with patch.object(GromacsBridge, "_can_import", return_value=True):
                result = bridge.run({"tpr": str(tpr), "nsteps": 10})

    fake_gmx.read_tpr.assert_called_once()
    fake_gmx.mdrun.assert_called_once()
    md.run.assert_called_once()
    assert result.status == SimStatus.SUCCESS
    assert result.data.get("executed") is True
    assert result.data.get("stub") is False
    assert result.data.get("backend") == "gmxapi"


def test_gromacs_cli_fallback_calls_subprocess(tmp_path: Path) -> None:
    tpr = tmp_path / "sys.tpr"
    tpr.write_bytes(b"fake-tpr")

    from src.simulations.gromacs_bridge import GromacsBridge

    bridge = GromacsBridge()
    fake_proc = MagicMock(returncode=0, stdout="Done", stderr="")

    with patch.object(GromacsBridge, "is_available", return_value=True):
        with patch.object(GromacsBridge, "_can_import", return_value=False):
            with patch(
                "src.simulations.gromacs_bridge.shutil.which",
                side_effect=lambda c: "/usr/bin/gmx" if c == "gmx" else None,
            ):
                with patch(
                    "src.simulations.gromacs_bridge.subprocess.run", return_value=fake_proc
                ) as run:
                    result = bridge.run({"tpr": str(tpr), "nsteps": 5})

    run.assert_called_once()
    cmd = run.call_args[0][0]
    assert cmd[0].endswith("gmx") or "gmx" in cmd[0]
    assert "mdrun" in cmd
    assert result.status == SimStatus.SUCCESS
    assert result.data["executed"] is True
    assert result.data["stub"] is False


def test_openfoam_calls_case_run(tmp_path: Path) -> None:
    case_dir = tmp_path / "cavity"
    case_dir.mkdir()

    fake_case = MagicMock()
    fake_foamlib = types.ModuleType("foamlib")
    fake_foamlib.FoamCase = MagicMock(return_value=fake_case)

    from src.simulations.openfoam_bridge import OpenFOAMBridge

    bridge = OpenFOAMBridge()
    with patch.dict(sys.modules, {"foamlib": fake_foamlib}):
        with patch.object(OpenFOAMBridge, "is_available", return_value=True):
            result = bridge.run({"case_dir": str(case_dir)})

    fake_foamlib.FoamCase.assert_called_once()
    fake_case.run.assert_called_once()
    assert result.status == SimStatus.SUCCESS
    assert result.data["executed"] is True
    assert result.data["stub"] is False


def test_amuse_calls_evolve_model() -> None:
    fake_particles = MagicMock()
    fake_particles.__len__ = lambda self: 2
    # distance helper for final_sep
    pos0 = MagicMock()
    pos1 = MagicMock()
    dist = MagicMock()
    dist.value_in.return_value = 1.05
    pos0.distance_to.return_value = dist
    fake_particles.__getitem__ = lambda self, i: MagicMock(position=pos0 if i == 0 else pos1)

    gravity = MagicMock()
    gravity.particles.add_particles = MagicMock()
    gravity.particles.new_channel_to.return_value = MagicMock()
    type(gravity).__name__ = "Hermite"

    hermite_mod = types.ModuleType("amuse.community.hermite.interface")
    hermite_mod.Hermite = MagicMock(return_value=gravity)

    amuse_root = types.ModuleType("amuse")
    datamodel = types.ModuleType("amuse.datamodel")
    units_mod = types.ModuleType("amuse.units")

    class _U:
        def __or__(self, other):
            return self

        def __ror__(self, other):
            return self

    units_mod.units = types.SimpleNamespace(MSun=_U(), AU=_U(), kms=_U(), yr=_U())
    datamodel.Particles = MagicMock(return_value=fake_particles)

    # Build package hierarchy for importlib
    community = types.ModuleType("amuse.community")
    hermite_pkg = types.ModuleType("amuse.community.hermite")

    from src.simulations.amuse_bridge import AmuseBridge

    modules = {
        "amuse": amuse_root,
        "amuse.datamodel": datamodel,
        "amuse.units": units_mod,
        "amuse.community": community,
        "amuse.community.hermite": hermite_pkg,
        "amuse.community.hermite.interface": hermite_mod,
    }
    bridge = AmuseBridge()
    with patch.dict(sys.modules, modules):
        with patch.object(AmuseBridge, "is_available", return_value=True):
            with patch.object(
                AmuseBridge, "_first_gravity_class", return_value=hermite_mod.Hermite
            ):
                result = bridge.run({"evolve_time_yr": 0.01})

    gravity.evolve_model.assert_called_once()
    assert result.status == SimStatus.SUCCESS
    assert result.data["executed"] is True
    assert result.data["stub"] is False
    assert "Hermite" in result.data.get("gravity_community", "")


def test_qe_calls_pw_x(tmp_path: Path) -> None:
    inp = tmp_path / "scf.in"
    inp.write_text("&CONTROL\n/\n", encoding="utf-8")

    from src.simulations.quantum_espresso_bridge import QuantumEspressoBridge

    bridge = QuantumEspressoBridge()
    fake_proc = MagicMock(returncode=0, stderr="")

    def fake_run(cmd, **kwargs):
        # write energy line to stdout file if stdout is a file handle
        stdout = kwargs.get("stdout")
        if hasattr(stdout, "write"):
            stdout.write("!    total energy              =   -12.345 Ry\n")
        return fake_proc

    with patch.object(QuantumEspressoBridge, "is_available", return_value=True):
        with patch(
            "src.simulations.quantum_espresso_bridge.shutil.which",
            return_value="/usr/bin/pw.x",
        ):
            with patch(
                "src.simulations.quantum_espresso_bridge.subprocess.run",
                side_effect=fake_run,
            ) as run:
                result = bridge.run({"input_file": str(inp)})

    run.assert_called_once()
    assert run.call_args[0][0][0].endswith("pw.x") or "pw.x" in run.call_args[0][0][0]
    assert result.status == SimStatus.SUCCESS
    assert result.data["executed"] is True
    assert result.data["stub"] is False
    assert result.data.get("total_energy_ry") == pytest.approx(-12.345)


def test_w1_bridges_refuse_without_inputs() -> None:
    """Missing inputs still refuse — that is honesty, not theater."""
    from src.simulations.amuse_bridge import AmuseBridge
    from src.simulations.gromacs_bridge import GromacsBridge
    from src.simulations.openfoam_bridge import OpenFOAMBridge
    from src.simulations.quantum_espresso_bridge import QuantumEspressoBridge

    for bridge_cls, payload in [
        (GromacsBridge, {}),
        (OpenFOAMBridge, {}),
        (QuantumEspressoBridge, {}),
    ]:
        bridge = bridge_cls()
        with patch.object(bridge_cls, "is_available", return_value=True):
            result = bridge.run(payload)
        assert result.status == SimStatus.UNAVAILABLE
        assert result.data.get("stub") is True or result.data.get("executed") is False
