from __future__ import annotations

import pytest

from src.simulations.virtual_bio import (
    SIMULATION_CATALOG,
    BioSimConfig,
    VirtualBioOrchestrator,
)


REQUIRED_DOMAINS = [
    "molecular_dynamics",
    "protein_docking",
    "gene_network",
    "metabolic_flux",
    "population_genetics",
    "quantum_chemistry",
]

REQUIRED_ENGINES = ["openmm", "vina", "boolean_net", "cobra", "slim", "psi4"]


class TestSimulationCatalog:
    def test_catalog_has_minimum_entries(self):
        assert len(SIMULATION_CATALOG) >= 6, (
            f"Expected at least 6 domains, got {len(SIMULATION_CATALOG)}"
        )

    def test_all_required_domains_present(self):
        for domain in REQUIRED_DOMAINS:
            assert domain in SIMULATION_CATALOG, f"Missing domain: {domain}"

    def test_all_configs_are_biosimconfig(self):
        for domain, cfg in SIMULATION_CATALOG.items():
            assert isinstance(cfg, BioSimConfig), (
                f"Config for {domain} is not BioSimConfig: {type(cfg)}"
            )

    def test_required_engines_present(self):
        present_engines = {cfg.engine for cfg in SIMULATION_CATALOG.values()}
        for engine in REQUIRED_ENGINES:
            assert engine in present_engines, f"Missing engine: {engine}"

    def test_gpu_required_flags(self):
        gpu_domains = {"molecular_dynamics", "quantum_chemistry"}
        cpu_domains = {"protein_docking", "gene_network", "metabolic_flux", "population_genetics"}
        for domain in gpu_domains:
            cfg = SIMULATION_CATALOG[domain]
            assert cfg.gpu_required is True, f"{domain} should require GPU"
        for domain in cpu_domains:
            cfg = SIMULATION_CATALOG[domain]
            assert cfg.gpu_required is False, f"{domain} should not require GPU"

    def test_all_configs_have_positive_runtime(self):
        for domain, cfg in SIMULATION_CATALOG.items():
            assert cfg.estimated_runtime_seconds > 0, (
                f"Non-positive runtime for {domain}: {cfg.estimated_runtime_seconds}"
            )

    def test_all_configs_have_cost(self):
        for domain, cfg in SIMULATION_CATALOG.items():
            if cfg.gpu_required:
                assert cfg.vastai_cost_per_hour > 0, (
                    f"GPU domain {domain} should have positive cost"
                )
            else:
                assert cfg.vastai_cost_per_hour >= 0, f"Invalid cost for {domain}"

    def test_all_configs_have_memory(self):
        for domain, cfg in SIMULATION_CATALOG.items():
            assert cfg.memory_required_gb > 0, (
                f"Non-positive memory for {domain}: {cfg.memory_required_gb}"
            )

    def test_all_configs_have_install_check(self):
        for domain, cfg in SIMULATION_CATALOG.items():
            assert cfg.install_check and isinstance(cfg.install_check, str), (
                f"Missing or invalid install_check for {domain}"
            )


class TestVirtualBioOrchestratorListAvailable:
    def test_list_available_returns_list(self):
        orch = VirtualBioOrchestrator()
        result = orch.list_available()
        assert isinstance(result, list)
        assert len(result) >= 6

    def test_list_available_items_have_required_keys(self):
        orch = VirtualBioOrchestrator()
        result = orch.list_available()
        for item in result:
            assert "domain" in item
            assert "engine" in item
            assert "available" in item
            assert isinstance(item["available"], bool)
            assert "gpu_required" in item
            assert "estimated_runtime" in item
            assert "cost" in item

    def test_list_available_covers_all_domains(self):
        orch = VirtualBioOrchestrator()
        result = orch.list_available()
        returned_domains = {item["domain"] for item in result}
        for domain in REQUIRED_DOMAINS:
            assert domain in returned_domains, f"Missing domain in list_available: {domain}"


class TestVirtualBioOrchestratorEstimateCost:
    def test_estimate_cost_returns_dict(self):
        orch = VirtualBioOrchestrator()
        result = orch.estimate_cost("molecular_dynamics")
        assert isinstance(result, dict)

    def test_estimate_cost_has_expected_keys(self):
        orch = VirtualBioOrchestrator()
        result = orch.estimate_cost("molecular_dynamics")
        expected_keys = {
            "domain", "engine", "gpu_required", "runtime_hours",
            "estimated_cost_usd", "platform", "memory_gb",
        }
        assert expected_keys.issubset(set(result.keys())), (
            f"Missing keys: {expected_keys - set(result.keys())}"
        )

    def test_estimate_cost_gpu_domain_has_cost(self):
        orch = VirtualBioOrchestrator()
        result = orch.estimate_cost("molecular_dynamics", runtime_hours=2.0)
        assert result["estimated_cost_usd"] > 0
        assert result["domain"] == "molecular_dynamics"
        assert result["engine"] == "openmm"
        assert result["gpu_required"] is True
        assert result["runtime_hours"] == 2.0
        assert result["platform"] == "vast.ai RTX 4090"
        assert result["memory_gb"] == 8

    def test_estimate_cost_cpu_domain_is_free(self):
        orch = VirtualBioOrchestrator()
        result = orch.estimate_cost("gene_network")
        assert result["estimated_cost_usd"] == 0.0
        assert result["platform"] == "local CPU"
        assert result["gpu_required"] is False

    def test_estimate_cost_unknown_domain(self):
        orch = VirtualBioOrchestrator()
        result = orch.estimate_cost("nonexistent_domain")
        assert "error" in result
        assert "Unknown domain" in result["error"]

    def test_estimate_cost_all_known_domains(self):
        orch = VirtualBioOrchestrator()
        for domain in REQUIRED_DOMAINS:
            result = orch.estimate_cost(domain)
            assert "error" not in result, f"Error for {domain}: {result}"
            assert result["domain"] == domain


class TestBioSimConfigDataClass:
    def test_can_create_biosimconfig(self):
        cfg = BioSimConfig(
            domain="test",
            engine="test_engine",
            gpu_required=False,
            estimated_runtime_seconds=100,
            vastai_cost_per_hour=0.0,
            memory_required_gb=1,
            install_check="echo test",
        )
        assert cfg.domain == "test"
        assert cfg.engine == "test_engine"
        assert cfg.gpu_required is False

    def test_biosimconfig_has_all_fields(self):
        from dataclasses import fields

        field_names = {f.name for f in fields(BioSimConfig)}
        expected = {
            "domain", "engine", "gpu_required", "estimated_runtime_seconds",
            "vastai_cost_per_hour", "memory_required_gb", "install_check",
        }
        assert field_names == expected


class TestModuleImports:
    def test_imports_virtual_bio(self):
        import src.simulations.virtual_bio

        assert hasattr(src.simulations.virtual_bio, "VirtualBioOrchestrator")
        assert hasattr(src.simulations.virtual_bio, "BioSimConfig")
        assert hasattr(src.simulations.virtual_bio, "SIMULATION_CATALOG")
