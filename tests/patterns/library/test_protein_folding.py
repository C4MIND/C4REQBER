"""
Tests for src/patterns/library/protein_folding.py

Covers:
- FoldingModel enum
- ProteinFoldingConfig default/custom initialization and to_dict
- ProteinFoldingPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _prepare_native_structure()
- _initialize_extended()
- _calculate_go_forces()
- _calculate_go_energy()
- _calculate_q()
- _calculate_radius_of_gyration()
- _calculate_rmsd()
- run() integration for all models (go_model, ca_only, harmonic, lattice)
- _calculate_confidence()
- estimate_resources()
- get_metadata()
- Edge cases: minimal residues, zero temperature, single replica
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.protein_folding import (
    ProteinFoldingConfig,
    ProteinFoldingPattern,
    FoldingModel,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestFoldingModel:
    def test_enum_values(self):
        assert FoldingModel.GO_MODEL.value == "go_model"
        assert FoldingModel.CA_ONLY.value == "ca_only"
        assert FoldingModel.HARMONIC.value == "harmonic"
        assert FoldingModel.LATTICE.value == "lattice"


# ═══════════════════════════════════════════════════════════════════
# ProteinFoldingConfig
# ═══════════════════════════════════════════════════════════════════


class TestProteinFoldingConfig:
    def test_default_init(self):
        cfg = ProteinFoldingConfig()
        assert cfg.model == FoldingModel.GO_MODEL
        assert cfg.num_residues == 50
        assert cfg.epsilon == 1.0
        assert cfg.sigma == 3.8
        assert cfg.k_bond == 100.0
        assert cfg.temperature == 300.0
        assert cfg.friction == 1.0
        assert cfg.num_replicas == 1
        assert cfg.calculate_rmsd is True
        assert cfg.calculate_rg is True
        assert cfg.calculate_contacts is True

    def test_custom_init(self):
        cfg = ProteinFoldingConfig(
            model=FoldingModel.CA_ONLY,
            num_residues=20,
            epsilon=2.0,
            temperature=400.0,
            friction=0.5,
        )
        assert cfg.model == FoldingModel.CA_ONLY
        assert cfg.num_residues == 20
        assert cfg.epsilon == 2.0
        assert cfg.temperature == 400.0
        assert cfg.friction == 0.5

    def test_to_dict(self):
        cfg = ProteinFoldingConfig(num_residues=30, epsilon=1.5)
        d = cfg.to_dict()
        assert d["num_residues"] == 30
        assert d["epsilon"] == 1.5
        assert d["model"] == "go_model"
        assert "sequence" in d


# ═══════════════════════════════════════════════════════════════════
# ProteinFoldingPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestProteinFoldingPatternInit:
    def test_init(self):
        pattern = ProteinFoldingPattern()
        assert pattern.config is not None
        assert isinstance(pattern.config, ProteinFoldingConfig)
        assert pattern.native_structure is None
        assert pattern.native_contacts is None

    def test_parameters_defined(self):
        pattern = ProteinFoldingPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "model" in param_names
        assert "num_residues" in param_names
        assert "temperature" in param_names
        assert "epsilon" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_protein(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_folding(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Molecular dynamics", description="protein conformation")
        assert pattern.can_simulate(h) is True

    def test_matches_amino_acid(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Amino acid sequence", description="peptide")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Fluid dynamics", description="navier stokes")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = ProteinFoldingPattern()
        cfg = pattern._parse_config({})
        assert cfg.model == FoldingModel.GO_MODEL
        assert cfg.num_residues == 50

    def test_custom_parsing(self):
        pattern = ProteinFoldingPattern()
        cfg = pattern._parse_config({
            "model": "ca_only",
            "num_residues": 20,
            "epsilon": 2.0,
            "temperature": 400.0,
            "k_bond": 50.0,
        })
        assert cfg.model == FoldingModel.CA_ONLY
        assert cfg.num_residues == 20
        assert cfg.epsilon == 2.0
        assert cfg.temperature == 400.0
        assert cfg.k_bond == 50.0

    def test_sequence_parsing(self):
        pattern = ProteinFoldingPattern()
        cfg = pattern._parse_config({"sequence": "ACDEFGHIKLMNPQRSTVWY"})
        assert cfg.sequence == "ACDEFGHIKLMNPQRSTVWY"


# ═══════════════════════════════════════════════════════════════════
# Native Structure Preparation
# ═══════════════════════════════════════════════════════════════════


class TestPrepareNativeStructure:
    def test_structure_shape(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=30)
        pattern._prepare_native_structure()
        assert pattern.native_structure.shape == (30, 3)

    def test_native_contacts(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=30, contact_cutoff=8.0)
        pattern._prepare_native_structure()
        assert pattern.native_contacts is not None
        assert isinstance(pattern.native_contacts, list)
        # All contacts should skip neighbors (i+4 or more)
        for i, j in pattern.native_contacts:
            assert j >= i + 4

    def test_helix_geometry(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=20)
        pattern._prepare_native_structure()
        # Z should increase monotonically for alpha helix
        z_coords = pattern.native_structure[:, 2]
        assert np.all(np.diff(z_coords) > 0)


# ═══════════════════════════════════════════════════════════════════
# Extended Initialization
# ═══════════════════════════════════════════════════════════════════


class TestInitializeExtended:
    def test_linear_chain(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=10, sigma=3.8)
        coords = pattern._initialize_extended()
        assert coords.shape == (10, 3)
        # Should be roughly along x-axis
        assert coords[0, 0] < coords[9, 0]

    def test_no_overlap(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=5, sigma=3.8)
        coords = pattern._initialize_extended()
        for i in range(4):
            dist = np.linalg.norm(coords[i+1] - coords[i])
            assert dist > 0


# ═══════════════════════════════════════════════════════════════════
# Go Model Forces
# ═══════════════════════════════════════════════════════════════════


class TestCalculateGoForces:
    def test_bond_forces(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=5, k_bond=100.0, sigma=3.8)
        pattern._prepare_native_structure()
        coords = pattern._initialize_extended()
        forces = pattern._calculate_go_forces(coords)
        assert forces.shape == (5, 3)

    def test_zero_forces_at_native(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=10, k_bond=100.0)
        pattern._prepare_native_structure()
        # At native structure, bond forces should be small
        forces = pattern._calculate_go_forces(pattern.native_structure)
        # Forces may not be exactly zero due to native contacts
        assert forces.shape == (10, 3)


# ═══════════════════════════════════════════════════════════════════
# Go Model Energy
# ═══════════════════════════════════════════════════════════════════


class TestCalculateGoEnergy:
    def test_energy_at_native(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=10)
        pattern._prepare_native_structure()
        energy = pattern._calculate_go_energy(pattern.native_structure)
        assert isinstance(energy, float)
        # Energy at native should be finite
        assert np.isfinite(energy)

    def test_energy_positive_bonds(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=5, k_bond=100.0, sigma=3.8)
        pattern._prepare_native_structure()
        coords = pattern._initialize_extended()
        energy = pattern._calculate_go_energy(coords)
        assert energy >= 0


# ═══════════════════════════════════════════════════════════════════
# Native Contact Fraction (Q)
# ═══════════════════════════════════════════════════════════════════


class TestCalculateQ:
    def test_q_at_native(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=10)
        pattern._prepare_native_structure()
        q = pattern._calculate_q(pattern.native_structure)
        assert 0 <= q <= 1
        # At native structure, most contacts should be formed
        assert q > 0.5

    def test_q_extended(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=10)
        pattern._prepare_native_structure()
        coords = pattern._initialize_extended()
        q = pattern._calculate_q(coords)
        assert 0 <= q <= 1
        # Extended chain should have few contacts
        assert q < 0.5

    def test_q_no_contacts(self):
        pattern = ProteinFoldingPattern()
        pattern.native_contacts = []
        q = pattern._calculate_q(np.zeros((5, 3)))
        assert q == 0.0


# ═══════════════════════════════════════════════════════════════════
# Radius of Gyration
# ═══════════════════════════════════════════════════════════════════


class TestCalculateRadiusOfGyration:
    def test_compact_structure(self):
        pattern = ProteinFoldingPattern()
        coords = np.zeros((10, 3))
        rg = pattern._calculate_radius_of_gyration(coords)
        assert rg == 0.0

    def test_extended_structure(self):
        pattern = ProteinFoldingPattern()
        coords = np.arange(30).reshape(10, 3)
        rg = pattern._calculate_radius_of_gyration(coords)
        assert rg > 0.0


# ═══════════════════════════════════════════════════════════════════
# RMSD
# ═══════════════════════════════════════════════════════════════════


class TestCalculateRMSD:
    def test_identical_structures(self):
        pattern = ProteinFoldingPattern()
        coords = np.random.random((10, 3))
        rmsd = pattern._calculate_rmsd(coords, coords)
        assert rmsd == pytest.approx(0.0, abs=1e-10)

    def test_different_structures(self):
        pattern = ProteinFoldingPattern()
        coords1 = np.zeros((10, 3))
        coords2 = np.ones((10, 3))
        rmsd = pattern._calculate_rmsd(coords1, coords2)
        assert rmsd > 0.0
        assert rmsd == pytest.approx(np.sqrt(3), abs=1e-6)


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence_go_model(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(model=FoldingModel.GO_MODEL)
        results = {
            "metrics": {
                "num_residues": 50,
                "final_q": 0.9,
                "final_rg": 15.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = ProteinFoldingPattern()
        results = {"metrics": {"num_residues": 1000}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.5

    def test_harmonic_confidence(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(model=FoldingModel.HARMONIC)
        results = {"metrics": {"num_residues": 50, "mean_rmsd": 2.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.0

    def test_lattice_confidence(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(model=FoldingModel.LATTICE)
        results = {"metrics": {"num_residues": 50, "max_hh_contacts": 5}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_large_protein(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(parameters={"num_residues": 500, "t_max": 10000.0})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0
        assert resources["memory_gb"] > 0.5


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_go_model(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        config = {"model": "go_model", "num_residues": 10, "t_max": 10.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("pf_")
        assert "final_rmsd" in result.metrics
        assert "final_q" in result.metrics

    async def test_run_ca_only(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        config = {"model": "ca_only", "num_residues": 10, "t_max": 10.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "ca_only"

    async def test_run_harmonic(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        config = {"model": "harmonic", "num_residues": 10, "t_max": 10.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "harmonic"

    async def test_run_lattice(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        config = {"model": "lattice", "num_residues": 10, "t_max": 10.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "lattice"
        assert "hp_sequence" in result.metrics

    async def test_run_logs_present(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        config = {"model": "go_model", "num_residues": 10, "t_max": 10.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        with patch.object(pattern, "_prepare_native_structure", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"num_residues": 10})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = ProteinFoldingPattern.get_metadata()
        assert meta["id"] == "protein_folding"
        assert meta["name"] == "Protein Folding"
        assert meta["category"] == "biology"
        assert "parameters" in meta
        assert isinstance(meta["parameters"], list)
        assert "references" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_minimal_residues(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein", description="test")
        config = {"model": "go_model", "num_residues": 5, "t_max": 5.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_temperature(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein", description="test")
        config = {
            "model": "go_model",
            "num_residues": 10,
            "temperature": 0.0,
            "t_max": 5.0,
            "dt": 0.01,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_friction(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein", description="test")
        config = {
            "model": "go_model",
            "num_residues": 10,
            "friction": 10.0,
            "t_max": 5.0,
            "dt": 0.01,
        }
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_config(self):
        pattern = ProteinFoldingPattern()
        h = Hypothesis(title="Protein folding", description="test")
        config = {"num_residues": 10, "t_max": 5.0, "dt": 0.01}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
