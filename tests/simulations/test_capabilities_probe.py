"""Unit tests for capabilities_probe — engine/verifier registry integrity."""
from __future__ import annotations

from src.simulations.capabilities_probe import _ENGINE_SPECS, _VERIFIER_SPECS, probe_capabilities


class TestCapabilitiesProbeRegistry:
    def test_engine_registry_count(self) -> None:
        assert len(_ENGINE_SPECS) >= 37

    def test_verifier_registry_includes_new_backends(self) -> None:
        ids = {spec[0] for spec in _VERIFIER_SPECS}
        for backend in ("cvc5", "tla", "alloy", "lean4", "z3"):
            assert backend in ids

    def test_probe_returns_structured_report(self) -> None:
        report = probe_capabilities()
        data = report.to_dict()
        assert "engines" in data
        assert "verifiers" in data
        assert len(data["engines"]) == len(_ENGINE_SPECS)
        assert len(data["verifiers"]) >= 9
        for eng in data["engines"]:
            assert eng["id"]
            assert eng["status"] in ("available", "slow", "unavailable")
        for ver in data["verifiers"]:
            assert ver["id"]
            assert "available" in ver
