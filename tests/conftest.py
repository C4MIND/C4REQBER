import sys
from pathlib import Path

import pytest


def pytest_configure(config):
    _root = Path(__file__).resolve().parent
    project_root = _root.parent
    for p in [str(project_root), str(project_root / "src")]:
        if p not in sys.path:
            sys.path.insert(0, p)


@pytest.fixture
def anyio_backend():
    """Restrict anyio tests to asyncio backend only."""
    return "asyncio"


@pytest.fixture(autouse=True)
def _isolate_calibration_store(tmp_path, monkeypatch):
    """Redirect the CalibrationTracker store to a per-test tmp file.

    Without this, any test that exercises validation calibration writes to
    the tracked repo file data/calibration.json (CalibrationTracker's
    default) — pollution that has historically been committed by accident.
    """
    monkeypatch.setenv("CALIBRATION_STORE", str(tmp_path / "calibration.json"))
