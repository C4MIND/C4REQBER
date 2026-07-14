"""Tests for biology and ecology pattern libraries.

Targets:
- src/patterns/library/protein_folding.py
- src/patterns/library/gene_regulatory.py
- src/patterns/library/metapopulation.py
- src/patterns/library/epidemic_sir.py
- src/patterns/library/epidemic_seir.py
- src/patterns/library/neural_mass.py
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.core import Hypothesis, SimulationStatus
from patterns.library.epidemic_seir import EpidemicSEIRPattern, SEIRConfig
from patterns.library.epidemic_sir import SIRConfig, SIREpidemicPattern
from patterns.library.gene_regulatory import (
    GeneRegulatoryConfig,
    GeneRegulatoryPattern,
    GRNModel,
)
from patterns.library.metapopulation import (
    MetapopulationConfig,
    MetapopulationModel,
    MetapopulationPattern,
    Patch,
)
from patterns.library.neural_mass import (
    NeuralMassConfig,
    NeuralMassModel,
    NeuralMassPattern,
)
from patterns.library.protein_folding import (
    FoldingModel,
    ProteinFoldingConfig,
    ProteinFoldingPattern,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run(pattern, hypothesis, config):
    """Run an async pattern synchronously."""
    return asyncio.run(pattern.run(hypothesis, config))


def _mock_hypothesis(title: str = "Test", description: str = "Test hypothesis") -> Hypothesis:
    return Hypothesis(title=title, description=description)


def _make_mock_solve_ivp(n_states: int = 3):
    """Factory for mocked solve_ivp returning deterministic data."""

    def mock_solve_ivp(func, t_span, y0, t_eval, method):
        sol = MagicMock()
        sol.t = np.array(t_eval)
        # Deterministic fake trajectory
        sol.y = np.random.RandomState(42).rand(n_states, len(t_eval)) * 100
        return sol

    return mock_solve_ivp


# ---------------------------------------------------------------------------
# ProteinFoldingPattern
# ---------------------------------------------------------------------------
class TestProteinFoldingPattern:
    """Tests for ProteinFoldingPattern."""

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("Protein folding", "Structure prediction", True),
            ("Molecular dynamics", "Conformational change", True),
            ("Quantum mechanics", "Wave function", False),
        ],
    )
    def test_can_simulate(self, title, desc, expected):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis(title, desc)
        assert pattern.can_simulate(hypo) is expected

    def test_parse_config_defaults(self):
        pattern = ProteinFoldingPattern()
        cfg = pattern._parse_config({})
        assert isinstance(cfg, ProteinFoldingConfig)
        assert cfg.model == FoldingModel.GO_MODEL
        assert cfg.num_residues == 50

    def test_parse_config_custom(self):
        pattern = ProteinFoldingPattern()
        cfg = pattern._parse_config(
            {
                "model": "ca_only",
                "num_residues": 10,
                "temperature": 400.0,
                "epsilon": 2.5,
            }
        )
        assert cfg.model == FoldingModel.CA_ONLY
        assert cfg.num_residues == 10
        assert cfg.temperature == 400.0
        assert cfg.epsilon == 2.5

    @pytest.mark.parametrize(
        "model_name,expected_model",
        [
            ("go_model", FoldingModel.GO_MODEL),
            ("ca_only", FoldingModel.CA_ONLY),
            ("harmonic", FoldingModel.HARMONIC),
            ("lattice", FoldingModel.LATTICE),
        ],
    )
    def test_parse_config_models(self, model_name, expected_model):
        pattern = ProteinFoldingPattern()
        cfg = pattern._parse_config({"model": model_name})
        assert cfg.model == expected_model

    def test_run_go_model_mocked(self):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis("Protein folding", "Native structure prediction")
        mock_result = {
            "metrics": {
                "num_residues": 5,
                "num_native_contacts": 2,
                "final_rmsd": 1.2,
                "final_q": 0.85,
                "mean_q": 0.6,
                "final_rg": 5.0,
                "mean_rg": 4.5,
                "final_energy": -10.0,
                "mean_energy": -8.0,
                "folded": True,
                "model": "go_model",
            },
            "logs": ["Go model simulation completed"],
            "trajectory_coords": [],
            "q_values": [0.5, 0.85],
            "rg_values": [4.0, 5.0],
            "energies": [-5.0, -10.0],
        }
        with patch.object(pattern, "_go_model_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"num_residues": 5, "model": "go_model"})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "go_model"
        assert result.metrics["folded"] is True
        assert result.confidence_score > 0

    def test_run_ca_only_mocked(self):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis("Protein", "CA only test")
        mock_result = {
            "metrics": {"num_residues": 5, "final_rg": 3.0, "mean_rg": 2.8, "model": "ca_only"},
            "logs": ["C-alpha only simulation completed"],
            "rg_values": [2.5, 3.0],
        }
        with patch.object(pattern, "_ca_only_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "ca_only", "num_residues": 5})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "ca_only"

    def test_run_harmonic_mocked(self):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis("Protein", "Harmonic test")
        mock_result = {
            "metrics": {
                "num_residues": 5,
                "mean_rmsd": 0.5,
                "rmsd_fluctuation": 0.1,
                "model": "harmonic",
            },
            "logs": ["Harmonic network simulation completed"],
            "rmsd_values": [0.4, 0.5, 0.6],
        }
        with patch.object(pattern, "_harmonic_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "harmonic", "num_residues": 5})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "harmonic"

    def test_run_lattice_mocked(self):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis("Protein", "Lattice test")
        mock_result = {
            "metrics": {
                "num_residues": 5,
                "hp_sequence": "HHPPH",
                "max_hh_contacts": 2,
                "mean_hh_contacts": 1.5,
                "model": "lattice",
            },
            "logs": ["Lattice model simulation completed"],
            "hh_contacts": [1, 2, 1],
        }
        with patch.object(pattern, "_lattice_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "lattice", "num_residues": 5})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "lattice"

    def test_run_error_handling(self):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis("Protein", "Error test")
        with patch.object(pattern, "_go_model_simulation", side_effect=KeyError("missing_key")):
            result = _run(pattern, hypo, {"model": "go_model"})
        assert result.status == SimulationStatus.FAILED
        assert "missing_key" in result.error_message

    def test_prepare_native_structure(self):
        pattern = ProteinFoldingPattern()
        pattern.config = ProteinFoldingConfig(num_residues=10)
        pattern._prepare_native_structure()
        assert pattern.native_structure is not None
        assert pattern.native_structure.shape == (10, 3)
        assert pattern.native_contacts is not None

    def test_calculate_q_no_contacts(self):
        pattern = ProteinFoldingPattern()
        pattern.native_contacts = []
        coords = np.zeros((5, 3))
        q = pattern._calculate_q(coords)
        assert q == 0.0

    def test_calculate_radius_of_gyration(self):
        pattern = ProteinFoldingPattern()
        coords = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        rg = pattern._calculate_radius_of_gyration(coords)
        assert rg > 0

    def test_calculate_rmsd(self):
        pattern = ProteinFoldingPattern()
        c1 = np.array([[0, 0, 0], [1, 0, 0]])
        c2 = np.array([[0, 0, 0], [2, 0, 0]])
        rmsd = pattern._calculate_rmsd(c1, c2)
        expected = np.sqrt(0.5)
        assert rmsd == pytest.approx(expected)

    def test_get_metadata(self):
        meta = ProteinFoldingPattern.get_metadata()
        assert meta["id"] == "protein_folding"
        assert "parameters" in meta
        assert "references" in meta

    def test_estimate_resources(self):
        pattern = ProteinFoldingPattern()
        hypo = Hypothesis(parameters={"num_residues": 100, "t_max": 1000.0, "dt": 0.001})
        resources = pattern.estimate_resources(hypo)
        assert resources["cpu_cores"] == 1
        assert resources["gpu_required"] is False
        assert resources["memory_gb"] > 0

    def test_config_to_dict(self):
        cfg = ProteinFoldingConfig(model=FoldingModel.GO_MODEL, num_residues=10)
        d = cfg.to_dict()
        assert d["model"] == "go_model"
        assert d["num_residues"] == 10


# ---------------------------------------------------------------------------
# GeneRegulatoryPattern
# ---------------------------------------------------------------------------
class TestGeneRegulatoryPattern:
    """Tests for GeneRegulatoryPattern."""

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("Gene regulatory network", "Cell fate decision", True),
            ("GRN dynamics", "Boolean attractor analysis", True),
            ("Newtonian mechanics", "Force and motion", False),
        ],
    )
    def test_can_simulate(self, title, desc, expected):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis(title, desc)
        assert pattern.can_simulate(hypo) is expected

    def test_parse_config_defaults(self):
        pattern = GeneRegulatoryPattern()
        cfg = pattern._parse_config({})
        assert isinstance(cfg, GeneRegulatoryConfig)
        assert cfg.model == GRNModel.HYBRID
        assert cfg.num_genes == 5

    def test_parse_config_custom(self):
        pattern = GeneRegulatoryPattern()
        cfg = pattern._parse_config(
            {
                "model": "boolean",
                "num_genes": 3,
                "connectivity": 0.5,
                "gamma": 2.0,
                "alpha": 20.0,
                "update_mode": "asynchronous",
            }
        )
        assert cfg.model == GRNModel.BOOLEAN
        assert cfg.num_genes == 3
        assert cfg.connectivity == 0.5
        assert cfg.gamma == 2.0
        assert cfg.alpha == 20.0
        assert cfg.update_mode == "asynchronous"

    @pytest.mark.parametrize(
        "model_name,expected_model",
        [
            ("boolean", GRNModel.BOOLEAN),
            ("ode", GRNModel.ODE),
            ("hybrid", GRNModel.HYBRID),
            ("threshold", GRNModel.THRESHOLD),
        ],
    )
    def test_parse_config_models(self, model_name, expected_model):
        pattern = GeneRegulatoryPattern()
        cfg = pattern._parse_config({"model": model_name})
        assert cfg.model == expected_model

    def test_run_boolean_mocked(self):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis("Gene network", "Boolean dynamics")
        mock_result = {
            "metrics": {
                "num_genes": 3,
                "num_edges": 2,
                "attractor_state": [1, 0, 1],
                "attractor_type": "fixed_point",
                "trajectory_length": 5,
                "hamming_distance_initial_final": 1,
                "model": "boolean",
            },
            "logs": ["Boolean network simulation completed"],
            "trajectory": [[0, 0, 0], [1, 0, 1]],
            "attractor": [1, 0, 1],
        }
        with patch.object(pattern, "_boolean_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "boolean", "num_genes": 3})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "boolean"
        assert result.metrics["attractor_type"] == "fixed_point"

    def test_run_ode_mocked(self):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis("Gene network", "ODE dynamics")
        mock_result = {
            "metrics": {
                "num_genes": 3,
                "num_edges": 2,
                "final_expression": [0.5, 0.8, 0.2],
                "mean_expression": 0.5,
                "expression_variance": 0.05,
                "num_active_genes": 2,
                "model": "ode",
            },
            "logs": ["ODE simulation completed"],
            "time": [0, 1, 2],
            "expression": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        }
        with patch.object(pattern, "_ode_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "ode", "num_genes": 3})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "ode"

    def test_run_hybrid_mocked(self):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis("Gene network", "Hybrid dynamics")
        mock_result = {
            "metrics": {
                "num_genes": 3,
                "total_switches": 5,
                "final_boolean_state": [1, 0, 1],
                "mean_switches_per_gene": 1.67,
                "model": "hybrid",
            },
            "logs": ["Hybrid simulation completed"],
            "time": [0, 1, 2],
            "levels": [[0.1, 0.2], [0.3, 0.4]],
            "boolean": [[0, 1], [1, 0]],
        }
        with patch.object(pattern, "_hybrid_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "hybrid", "num_genes": 3})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "hybrid"

    def test_run_threshold_mocked(self):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis("Gene network", "Threshold dynamics")
        mock_result = {
            "metrics": {
                "num_genes": 3,
                "final_expression": [0.5, 0.8, 0.2],
                "mean_expression": 0.5,
                "model": "threshold",
            },
            "logs": ["Threshold simulation completed"],
            "time": [0, 1, 2],
            "expression": [[0.1, 0.2], [0.3, 0.4]],
        }
        with patch.object(pattern, "_threshold_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "threshold", "num_genes": 3})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "threshold"

    def test_run_error_handling(self):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis("Gene", "Error test")
        with patch.object(pattern, "_boolean_simulation", side_effect=TypeError("invalid type")):
            result = _run(pattern, hypo, {"model": "boolean"})
        assert result.status == SimulationStatus.FAILED
        assert "invalid type" in result.error_message

    def test_generate_network(self):
        pattern = GeneRegulatoryPattern()
        pattern.rng = np.random.default_rng(seed=42)
        pattern.config = GeneRegulatoryConfig(num_genes=5, connectivity=0.5)
        pattern._generate_network()
        assert pattern.adjacency is not None
        assert pattern.adjacency.shape == (5, 5)
        assert pattern.regulation_types is not None
        assert pattern.regulation_types.shape == (5, 5)
        # No self-loops
        assert np.all(np.diag(pattern.adjacency) == 0)

    def test_hill_activation(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(hill_n=2.0, theta=0.5)
        val = pattern._hill_activation(0.5)
        assert 0 <= val <= 1

    def test_hill_repression(self):
        pattern = GeneRegulatoryPattern()
        pattern.config = GeneRegulatoryConfig(hill_n=2.0, theta=0.5)
        val = pattern._hill_repression(0.5)
        assert 0 <= val <= 1

    def test_find_all_attractors(self):
        pattern = GeneRegulatoryPattern()
        pattern.rng = np.random.default_rng(seed=42)
        pattern.config = GeneRegulatoryConfig(num_genes=3, connectivity=1.0)
        pattern._generate_network()
        attractors = pattern._find_all_attractors()
        assert isinstance(attractors, list)

    def test_get_metadata(self):
        meta = GeneRegulatoryPattern.get_metadata()
        assert meta["id"] == "gene_regulatory"
        assert "parameters" in meta

    def test_estimate_resources(self):
        pattern = GeneRegulatoryPattern()
        hypo = Hypothesis(parameters={"num_genes": 10})
        resources = pattern.estimate_resources(hypo)
        assert resources["cpu_cores"] == 1
        assert resources["gpu_required"] is False

    def test_config_to_dict(self):
        cfg = GeneRegulatoryConfig(model=GRNModel.ODE, num_genes=8)
        d = cfg.to_dict()
        assert d["model"] == "ode"
        assert d["num_genes"] == 8


# ---------------------------------------------------------------------------
# MetapopulationPattern
# ---------------------------------------------------------------------------
class TestMetapopulationPattern:
    """Tests for MetapopulationPattern."""

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("Metapopulation dynamics", "Fragmentation effects", True),
            ("Habitat patches", "Levins model analysis", True),
            ("Quantum field", "Particle interactions", False),
        ],
    )
    def test_can_simulate(self, title, desc, expected):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis(title, desc)
        assert pattern.can_simulate(hypo) is expected

    def test_parse_config_defaults(self):
        pattern = MetapopulationPattern()
        cfg = pattern._parse_config({})
        assert isinstance(cfg, MetapopulationConfig)
        assert cfg.model == MetapopulationModel.LEVINS
        assert cfg.num_patches == 20

    def test_parse_config_custom(self):
        pattern = MetapopulationPattern()
        cfg = pattern._parse_config(
            {
                "model": "spatial",
                "num_patches": 10,
                "c": 0.2,
                "e": 0.1,
                "years": 50,
                "rescue_effect": True,
            }
        )
        assert cfg.model == MetapopulationModel.SPATIAL
        assert cfg.num_patches == 10
        assert cfg.c == 0.2
        assert cfg.e == 0.1
        assert cfg.years == 50
        assert cfg.rescue_effect is True

    @pytest.mark.parametrize(
        "model_name,expected_model",
        [
            ("levins", MetapopulationModel.LEVINS),
            ("levins_hanski", MetapopulationModel.LEVINS_Hanski),
            ("incidence_function", MetapopulationModel.INCIDENCE_FUNCTION),
            ("spatial", MetapopulationModel.SPATIAL),
        ],
    )
    def test_parse_config_models(self, model_name, expected_model):
        pattern = MetapopulationPattern()
        cfg = pattern._parse_config({"model": model_name})
        assert cfg.model == expected_model

    def test_run_levins_mocked(self):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis("Metapopulation", "Levins model")
        mock_result = {
            "metrics": {
                "final_occupancy": 0.5,
                "mean_occupancy": 0.48,
                "equilibrium_occupancy": 0.5,
                "metapopulation_capacity": 2.0,
                "colonization_events": 10,
                "extinction_events": 5,
                "persistence": True,
                "c_e_ratio": 2.0,
                "model": "levins",
            },
            "logs": ["Levins simulation completed"],
            "occupancy": [0.5, 0.5, 0.5],
        }
        with patch.object(pattern, "_levins_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "levins", "num_patches": 10})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "levins"
        assert result.metrics["persistence"] is True

    def test_run_levins_hanski_mocked(self):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis("Metapopulation", "Hanski rescue")
        mock_result = {
            "metrics": {
                "final_occupancy": 0.6,
                "mean_occupancy": 0.55,
                "equilibrium_occupancy": 0.6,
                "mean_effective_extinction": 0.03,
                "rescue_effect": True,
                "persistence": True,
                "model": "levins_hanski",
            },
            "logs": ["Hanski simulation completed"],
            "occupancy": [0.5, 0.6],
            "effective_extinction": [0.05, 0.03],
        }
        with patch.object(pattern, "_levins_hanski_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "levins_hanski", "rescue_effect": True})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "levins_hanski"

    def test_run_incidence_function_mocked(self):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis("Metapopulation", "Incidence function")
        mock_result = {
            "metrics": {
                "final_occupancy_rate": 0.7,
                "mean_occupancy_rate": 0.65,
                "num_patches": 10,
                "num_occupied_final": 7,
                "area_occupancy_correlation": 0.5,
                "persistence": True,
                "model": "incidence_function",
            },
            "logs": ["Incidence function simulation completed"],
            "occupancy_rates": [0.5, 0.7],
            "patch_occupancy": [[True, False], [False, True]],
            "patch_areas": [10.0, 20.0],
            "patch_incidences": [0.5, 0.5],
        }
        with patch.object(pattern, "_incidence_function_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "incidence_function"})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "incidence_function"

    def test_run_spatial_mocked(self):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis("Metapopulation", "Spatial simulation")
        mock_result = {
            "metrics": {
                "final_total_population": 500,
                "mean_total_population": 450.0,
                "final_occupied_patches": 8,
                "mean_occupied_patches": 7.5,
                "model": "spatial",
            },
            "logs": ["Spatial simulation completed"],
            "total_population": [400, 500],
            "occupied_patches": [7, 8],
        }
        with patch.object(pattern, "_spatial_simulation", return_value=mock_result):
            result = _run(pattern, hypo, {"model": "spatial"})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["model"] == "spatial"

    def test_run_error_handling(self):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis("Metapopulation", "Error test")
        with patch.object(pattern, "_levins_simulation", side_effect=TypeError("bad config")):
            result = _run(pattern, hypo, {"model": "levins"})
        assert result.status == SimulationStatus.FAILED
        assert "bad config" in result.error_message

    def test_generate_landscape(self):
        pattern = MetapopulationPattern()
        pattern.rng = np.random.default_rng(seed=42)
        pattern.config = MetapopulationConfig(num_patches=5)
        pattern._generate_landscape()
        assert len(pattern.patches) == 5
        for p in pattern.patches:
            assert isinstance(p, Patch)
            assert p.area > 0

    def test_patch_distance_to(self):
        p1 = Patch(0, 10.0, 0.0, 0.0)
        p2 = Patch(1, 10.0, 3.0, 4.0)
        assert p1.distance_to(p2) == 5.0

    def test_get_metadata(self):
        meta = MetapopulationPattern.get_metadata()
        assert meta["id"] == "metapopulation"
        assert "parameters" in meta

    def test_estimate_resources(self):
        pattern = MetapopulationPattern()
        hypo = Hypothesis(parameters={"num_patches": 50, "years": 200})
        resources = pattern.estimate_resources(hypo)
        assert resources["cpu_cores"] == 1
        assert resources["gpu_required"] is False

    def test_config_to_dict(self):
        cfg = MetapopulationConfig(model=MetapopulationModel.SPATIAL, num_patches=15)
        d = cfg.to_dict()
        assert d["model"] == "spatial"
        assert d["num_patches"] == 15


# ---------------------------------------------------------------------------
# SIREpidemicPattern
# ---------------------------------------------------------------------------
class TestSIREpidemicPattern:
    """Tests for SIREpidemicPattern."""

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("SIR model", "Epidemic outbreak analysis", True),
            ("Herd immunity", "Vaccination strategy", True),
            ("Fluid dynamics", "Turbulence modeling", False),
        ],
    )
    def test_can_simulate(self, title, desc, expected):
        pattern = SIREpidemicPattern()
        hypo = _mock_hypothesis(title, desc)
        assert pattern.can_simulate(hypo) is expected

    def test_parse_config_defaults(self):
        pattern = SIREpidemicPattern()
        cfg = pattern._parse_config({})
        assert isinstance(cfg, SIRConfig)
        assert cfg.N == 1000000.0
        assert cfg.beta == 0.3
        assert cfg.gamma == 0.1

    def test_parse_config_custom(self):
        pattern = SIREpidemicPattern()
        cfg = pattern._parse_config(
            {"N": 500000, "I0": 100, "beta": 0.5, "gamma": 0.2, "t_max": 200}
        )
        assert cfg.N == 500000.0
        assert cfg.I0 == 100.0
        assert cfg.beta == 0.5
        assert cfg.gamma == 0.2
        assert cfg.t_max == 200.0

    @patch("patterns.library.epidemic_sir.solve_ivp")
    def test_run_happy_path(self, mock_solve_ivp):
        pattern = SIREpidemicPattern()
        hypo = _mock_hypothesis("Epidemic", "SIR model test")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=3)
        result = _run(pattern, hypo, {"N": 1000, "I0": 10, "t_max": 10, "dt": 1})
        assert result.status == SimulationStatus.COMPLETED
        assert "R0" in result.metrics
        assert "peak_infections" in result.metrics
        assert result.confidence_score >= 0

    @patch("patterns.library.epidemic_sir.solve_ivp")
    def test_run_error_handling(self, mock_solve_ivp):
        pattern = SIREpidemicPattern()
        hypo = _mock_hypothesis("Epidemic", "Error test")
        mock_solve_ivp.side_effect = KeyError("missing")
        result = _run(pattern, hypo, {})
        assert result.status == SimulationStatus.FAILED
        assert "missing" in result.error_message

    @patch("patterns.library.epidemic_sir.solve_ivp")
    def test_run_r0_less_than_one(self, mock_solve_ivp):
        pattern = SIREpidemicPattern()
        hypo = _mock_hypothesis("Epidemic", "No outbreak")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=3)
        result = _run(pattern, hypo, {"beta": 0.05, "gamma": 0.1})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics["R0"] == 0.5
        assert result.metrics["herd_immunity_threshold"] == 0.0

    def test_calculate_confidence(self):
        pattern = SIREpidemicPattern()
        results = {
            "metrics": {
                "R0": 2.5,
                "peak_infections": 100,
                "attack_rate": 0.4,
                "herd_immunity_threshold": 0.6,
                "generation_time_days": 10,
            }
        }
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.9

    def test_get_metadata(self):
        meta = SIREpidemicPattern.get_metadata()
        assert meta["id"] == "epidemic_sir"
        assert "parameters" in meta

    def test_estimate_resources(self):
        pattern = SIREpidemicPattern()
        hypo = Hypothesis(parameters={"t_max": 200.0})
        resources = pattern.estimate_resources(hypo)
        assert resources["cpu_cores"] == 1
        assert resources["gpu_required"] is False


# ---------------------------------------------------------------------------
# EpidemicSEIRPattern
# ---------------------------------------------------------------------------
class TestEpidemicSEIRPattern:
    """Tests for EpidemicSEIRPattern."""

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("SEIR model", "Disease with incubation", True),
            ("Pandemic simulation", "Compartmental dynamics", True),
            ("Stock market", "Price prediction", False),
        ],
    )
    def test_can_simulate(self, title, desc, expected):
        pattern = EpidemicSEIRPattern()
        hypo = _mock_hypothesis(title, desc)
        assert pattern.can_simulate(hypo) is expected

    def test_parse_config_defaults(self):
        pattern = EpidemicSEIRPattern()
        cfg = pattern._parse_config({})
        assert isinstance(cfg, SEIRConfig)
        assert cfg.model_type == "seir"
        assert cfg.N == 100000
        assert cfg.beta == 0.5

    def test_parse_config_custom(self):
        pattern = EpidemicSEIRPattern()
        cfg = pattern._parse_config(
            {
                "model_type": "seirs",
                "N": 50000,
                "I0": 50,
                "beta": 0.8,
                "sigma": 0.3,
                "gamma": 0.15,
                "omega": 0.01,
                "stochastic": True,
                "n_realizations": 50,
            }
        )
        assert cfg.model_type == "seirs"
        assert cfg.N == 50000
        assert cfg.I0 == 50
        assert cfg.beta == 0.8
        assert cfg.sigma == 0.3
        assert cfg.gamma == 0.15
        assert cfg.omega == 0.01
        assert cfg.stochastic is True
        assert cfg.n_realizations == 50

    @pytest.mark.parametrize("model_type", ["sir", "seir", "seirs"])
    @patch("patterns.library.epidemic_seir.solve_ivp")
    def test_run_deterministic_models(self, mock_solve_ivp, model_type):
        pattern = EpidemicSEIRPattern()
        hypo = _mock_hypothesis("Epidemic", f"{model_type.upper()} test")
        n_states = 3 if model_type == "sir" else 4
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=n_states)
        result = _run(pattern, hypo, {"model_type": model_type, "N": 1000, "t_max": 10, "dt": 1})
        assert result.status == SimulationStatus.COMPLETED
        assert "R0" in result.metrics
        assert "peak_infections" in result.metrics
        assert result.confidence_score >= 0

    @patch("patterns.library.epidemic_seir.solve_ivp")
    def test_run_error_handling(self, mock_solve_ivp):
        pattern = EpidemicSEIRPattern()
        hypo = _mock_hypothesis("Epidemic", "Error test")
        mock_solve_ivp.side_effect = TypeError("bad args")
        result = _run(pattern, hypo, {"model_type": "seir"})
        assert result.status == SimulationStatus.FAILED
        assert "bad args" in result.error_message

    @patch("patterns.library.epidemic_seir.solve_ivp")
    def test_run_with_seed(self, mock_solve_ivp):
        pattern = EpidemicSEIRPattern()
        hypo = _mock_hypothesis("Epidemic", "Seed test")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=4)
        result = _run(pattern, hypo, {"model_type": "seir", "random_seed": 123})
        assert result.status == SimulationStatus.COMPLETED

    @patch("patterns.library.epidemic_seir.solve_ivp")
    def test_analyze_results_structure(self, mock_solve_ivp):
        pattern = EpidemicSEIRPattern()
        pattern.config = SEIRConfig(N=1000, model_type="seir")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=4)
        # Set up minimal trajectories
        pattern.time_points = np.array([0, 1, 2])
        pattern.trajectories = {
            "S": np.array([990, 900, 800]),
            "E": np.array([0, 50, 80]),
            "I": np.array([10, 40, 100]),
            "R": np.array([0, 10, 20]),
        }
        result = pattern._analyze_results()
        assert "metrics" in result
        assert "logs" in result
        assert "R0" in result["metrics"]
        assert "attack_rate" in result["metrics"]

    def test_analyze_results_empty(self):
        pattern = EpidemicSEIRPattern()
        pattern.trajectories = {}
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert "No simulation data" in result["logs"]

    def test_get_metadata(self):
        meta = EpidemicSEIRPattern.get_metadata()
        assert meta["id"] == "epidemic_seir"
        assert "name" in meta

    def test_estimate_resources(self):
        pattern = EpidemicSEIRPattern()
        hypo = Hypothesis(parameters={"stochastic": True, "n_realizations": 100, "t_max": 200})
        resources = pattern.estimate_resources(hypo)
        assert resources["cpu_cores"] == 1
        assert resources["gpu_required"] is False
        assert resources["estimated_time_seconds"] > 0


# ---------------------------------------------------------------------------
# NeuralMassPattern
# ---------------------------------------------------------------------------
class TestNeuralMassPattern:
    """Tests for NeuralMassPattern."""

    @pytest.mark.parametrize(
        "title,desc,expected",
        [
            ("Neural mass model", "EEG alpha rhythm", True),
            ("Jansen-Rit", "Epilepsy seizure simulation", True),
            ("Fluid dynamics", "Navier-Stokes", False),
        ],
    )
    def test_can_simulate(self, title, desc, expected):
        pattern = NeuralMassPattern()
        hypo = _mock_hypothesis(title, desc)
        assert pattern.can_simulate(hypo) is expected

    def test_parse_config_defaults(self):
        pattern = NeuralMassPattern()
        cfg = pattern._parse_config({})
        assert isinstance(cfg, NeuralMassConfig)
        assert cfg.model == NeuralMassModel.JANSEN_RIT
        assert cfg.He == 3.25
        assert cfg.t_max == 10.0

    def test_parse_config_custom(self):
        pattern = NeuralMassPattern()
        cfg = pattern._parse_config(
            {
                "model": "wendling",
                "He": 5.0,
                "Hi": 30.0,
                "ke": 150.0,
                "ki": 75.0,
                "P": 300.0,
                "sigma_noise": 10.0,
                "t_max": 5.0,
                "output_type": "lfp",
            }
        )
        assert cfg.model == NeuralMassModel.WENDLING
        assert cfg.He == 5.0
        assert cfg.Hi == 30.0
        assert cfg.ke == 150.0
        assert cfg.ki == 75.0
        assert cfg.P == 300.0
        assert cfg.sigma_noise == 10.0
        assert cfg.t_max == 5.0
        assert cfg.output_type == "lfp"

    @pytest.mark.parametrize(
        "model_name,expected_model",
        [
            ("jansen_rit", NeuralMassModel.JANSEN_RIT),
            ("wendling", NeuralMassModel.WENDLING),
            ("wilson_cowan", NeuralMassModel.WILSON_COWAN),
        ],
    )
    def test_parse_config_models(self, model_name, expected_model):
        pattern = NeuralMassPattern()
        cfg = pattern._parse_config({"model": model_name})
        assert cfg.model == expected_model

    @patch("patterns.library.neural_mass.solve_ivp")
    def test_run_jansen_rit(self, mock_solve_ivp):
        pattern = NeuralMassPattern()
        hypo = _mock_hypothesis("Neural mass", "Alpha rhythm")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=6)
        result = _run(pattern, hypo, {"model": "jansen_rit", "t_max": 1.0, "dt": 0.1})
        assert result.status == SimulationStatus.COMPLETED
        assert "dominant_freq" in result.metrics
        assert "eeg_mean_amplitude" in result.metrics
        assert result.confidence_score >= 0

    @patch("patterns.library.neural_mass.solve_ivp")
    def test_run_wendling(self, mock_solve_ivp):
        pattern = NeuralMassPattern()
        hypo = _mock_hypothesis("Neural mass", "Epilepsy")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=6)
        result = _run(pattern, hypo, {"model": "wendling", "t_max": 1.0, "dt": 0.1})
        assert result.status == SimulationStatus.COMPLETED
        assert result.metrics.get("model") == "wendling"

    @patch("patterns.library.neural_mass.solve_ivp")
    def test_run_wilson_cowan(self, mock_solve_ivp):
        pattern = NeuralMassPattern()
        hypo = _mock_hypothesis("Neural mass", "Firing rates")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=2)
        result = _run(pattern, hypo, {"model": "wilson_cowan", "t_max": 1.0, "dt": 0.1})
        assert result.status == SimulationStatus.COMPLETED
        assert "mean_excitatory" in result.metrics

    @patch("patterns.library.neural_mass.solve_ivp")
    def test_run_error_handling(self, mock_solve_ivp):
        pattern = NeuralMassPattern()
        hypo = _mock_hypothesis("Neural mass", "Error test")
        mock_solve_ivp.side_effect = TypeError("bad equation")
        result = _run(pattern, hypo, {"model": "jansen_rit"})
        assert result.status == SimulationStatus.FAILED
        assert "bad equation" in result.error_message

    def test_sigmoid(self):
        pattern = NeuralMassPattern()
        pattern.config = NeuralMassConfig(e0=2.5, v0=6.0, r=0.56)
        v = np.array([0.0, 6.0, 12.0])
        s = pattern._sigmoid(v)
        assert len(s) == 3
        assert np.all(s >= 0)
        assert np.all(s <= 2 * pattern.config.e0)

    def test_sigmoid_scalar(self):
        pattern = NeuralMassPattern()
        pattern.config = NeuralMassConfig(e0=2.5, v0=6.0, r=0.56)
        s = pattern._sigmoid_scalar(6.0)
        assert s > 0
        assert s <= 2 * pattern.config.e0

    def test_jansen_rit_equations_shape(self):
        pattern = NeuralMassPattern()
        pattern.config = NeuralMassConfig(He=3.25, Hi=22.0, ke=100.0, ki=50.0)
        pattern.noise_stream = None
        y = np.zeros(6)
        dydt = pattern._jansen_rit_equations(0.0, y)
        assert dydt.shape == (6,)

    def test_wendling_equations(self):
        pattern = NeuralMassPattern()
        pattern.config = NeuralMassConfig()
        pattern.noise_stream = None
        y = np.zeros(8)
        dydt = pattern._wendling_equations(0.0, y)
        assert len(dydt) == 6  # Returns Jansen-Rit for first 6 states

    def test_wilson_cowan_equations(self):
        pattern = NeuralMassPattern()
        y = np.array([0.1, 0.1])
        dydt = pattern._wilson_cowan_equations(0.0, y)
        assert len(dydt) == 2

    def test_calculate_eeg_metrics(self):
        pattern = NeuralMassPattern()
        t = np.linspace(0, 1, 100)
        eeg = np.sin(2 * np.pi * 10 * t)  # 10 Hz signal
        metrics = pattern._calculate_eeg_metrics(t, eeg, None, None, None)
        assert "dominant_freq" in metrics
        assert "alpha_power" in metrics
        assert "eeg_mean_amplitude" in metrics
        assert metrics["eeg_mean_amplitude"] < 1e-3  # Sine wave mean ~0

    def test_calculate_eeg_metrics_with_firing(self):
        pattern = NeuralMassPattern()
        t = np.linspace(0, 1, 100)
        eeg = np.zeros(100)
        firing_e = np.ones(100) * 5.0
        firing_p = np.ones(100) * 3.0
        firing_i = np.ones(100) * 2.0
        metrics = pattern._calculate_eeg_metrics(t, eeg, firing_e, firing_p, firing_i)
        assert "mean_firing_e" in metrics
        assert "mean_firing_p" in metrics
        assert "mean_firing_i" in metrics
        assert metrics["mean_firing_e"] == 5.0

    def test_calculate_confidence(self):
        pattern = NeuralMassPattern()
        pattern.config = NeuralMassConfig(model=NeuralMassModel.JANSEN_RIT)
        results = {
            "metrics": {
                "dominant_freq": 10.0,
                "alpha_power": 100.0,
                "eeg_std": 0.1,
                "alpha_peak_freq": 10.0,
            }
        }
        score = pattern._calculate_confidence(results)
        assert 0 <= score <= 0.95

    def test_get_metadata(self):
        meta = NeuralMassPattern.get_metadata()
        assert meta["id"] == "neural_mass"
        assert "parameters" in meta

    def test_estimate_resources(self):
        pattern = NeuralMassPattern()
        hypo = Hypothesis(parameters={"t_max": 10.0, "dt": 0.001})
        resources = pattern.estimate_resources(hypo)
        assert resources["cpu_cores"] == 1
        assert resources["gpu_required"] is False
        assert resources["memory_gb"] > 0

    def test_config_to_dict(self):
        cfg = NeuralMassConfig(model=NeuralMassModel.WENDLING, He=5.0)
        d = cfg.to_dict()
        assert d["model"] == "wendling"
        assert d["He"] == 5.0


# ---------------------------------------------------------------------------
# Integration-style tests with tiny real configs
# ---------------------------------------------------------------------------
class TestTinyIntegration:
    """Lightweight integration tests using minimal configs."""

    def test_protein_folding_tiny_go(self):
        pattern = ProteinFoldingPattern()
        hypo = _mock_hypothesis("Protein", "Tiny folding test")
        result = _run(
            pattern,
            hypo,
            {
                "model": "go_model",
                "num_residues": 5,
                "t_max": 0.01,
                "dt": 0.001,
                "record_interval": 1,
            },
        )
        assert result.status == SimulationStatus.COMPLETED
        assert "final_rmsd" in result.metrics

    def test_metapopulation_tiny_levins(self):
        pattern = MetapopulationPattern()
        hypo = _mock_hypothesis("Metapopulation", "Tiny levins test")
        result = _run(pattern, hypo, {"model": "levins", "years": 5, "num_patches": 5})
        assert result.status == SimulationStatus.COMPLETED
        assert "final_occupancy" in result.metrics

    def test_gene_regulatory_tiny_boolean(self):
        pattern = GeneRegulatoryPattern()
        hypo = _mock_hypothesis("Gene", "Tiny boolean test")
        result = _run(
            pattern,
            hypo,
            {"model": "boolean", "num_genes": 3, "num_steps": 5},
        )
        assert result.status == SimulationStatus.COMPLETED
        assert "attractor_state" in result.metrics

    @patch("patterns.library.epidemic_sir.solve_ivp")
    def test_sir_tiny(self, mock_solve_ivp):
        pattern = SIREpidemicPattern()
        hypo = _mock_hypothesis("Epidemic", "Tiny SIR")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=3)
        result = _run(pattern, hypo, {"N": 100, "I0": 5, "t_max": 5, "dt": 1})
        assert result.status == SimulationStatus.COMPLETED

    @patch("patterns.library.epidemic_seir.solve_ivp")
    def test_seir_tiny(self, mock_solve_ivp):
        pattern = EpidemicSEIRPattern()
        hypo = _mock_hypothesis("Epidemic", "Tiny SEIR")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=4)
        result = _run(pattern, hypo, {"model_type": "seir", "N": 100, "t_max": 5, "dt": 1})
        assert result.status == SimulationStatus.COMPLETED

    @patch("patterns.library.neural_mass.solve_ivp")
    def test_neural_mass_tiny(self, mock_solve_ivp):
        pattern = NeuralMassPattern()
        hypo = _mock_hypothesis("Neural", "Tiny neural mass")
        mock_solve_ivp.side_effect = _make_mock_solve_ivp(n_states=6)
        result = _run(pattern, hypo, {"t_max": 0.1, "dt": 0.01})
        assert result.status == SimulationStatus.COMPLETED
