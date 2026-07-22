"""Regression: package install must use ``python -m pip``, never ``pip pip``."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from src.cli.package_manager import PackageSpec, _install_direct


def test_install_direct_uses_python_m_pip() -> None:
    pkg = PackageSpec(
        id="numpy",
        name="NumPy",
        pip_name="numpy",
        description="test",
        category="core",
    )
    with patch("src.cli.package_manager.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ok, _msg = _install_direct(pkg)
        assert ok
        cmd = run.call_args[0][0]
        assert cmd[0] == sys.executable
        assert cmd[1:4] == ["-m", "pip", "install"]
        # Never the broken ["pip", "pip", "install", ...] shape
        assert not (len(cmd) >= 3 and cmd[0].endswith("pip") and cmd[1] == "pip")
