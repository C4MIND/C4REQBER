# SPDX-License-Identifier: AGPL-3.0
"""SLiM bridge — population genetics forward simulations.

Install: conda install -c conda-forge slim  (or)  brew install slim
Docs: https://messerlab.org/slim/
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult


logger = logging.getLogger(__name__)

DEFAULT_SLIM_SCRIPT = """
initialize() {
    initializeMutationRate(1e-7);
    initializeMutationType("m1", 0.5, "f", 0.0);
    initializeGenomicElementType("g1", m1, 1.0);
    initializeGenomicElement(g1, 0, 99999);
    initializeRecombinationRate(1e-8);
}
1 {
    sim.addSubpop("p1", 500);
}
10000 late() {
    catn("Final mutation count: " + size(sim.mutations));
    catn("Mean fitness: " + mean(p1.cachedFitness(NULL)));
}
"""


class SlimBridge(BaseSimulationAdapter):
    """Bridge to SLiM for forward population genetic simulations."""

    _engine_name = "slim"
    _package_checks = []
    _install_hint = (
        "conda install -c conda-forge slim  (or)  "
        "brew install slim  (or)  "
        "build from source: https://messerlab.org/slim/"
    )

    def is_available(self) -> bool:
        try:
            subprocess.run(["slim", "-v"], capture_output=True, check=True, timeout=5)
            return True
        except Exception:
            return False

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            script = data.get("script", DEFAULT_SLIM_SCRIPT)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".slim", delete=False) as f:
                f.write(script)
                script_path = f.name
            try:
                result = subprocess.run(
                    ["slim", script_path],
                    capture_output=True,
                    text=True,
                    timeout=data.get("timeout", 300),
                )
                if result.returncode != 0:
                    raise RuntimeError(f"SLiM failed: {result.stderr}")
                return {
                    "stdout": result.stdout[:5000],
                    "stderr": result.stderr[:2000],
                    "script_path": script_path,
                    "generations": data.get("generations", 10000),
                    "population_size": data.get("population_size", 500),
                }
            finally:
                os.unlink(script_path)

        return self._run_wrapped(_run, input_data)
