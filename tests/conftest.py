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
