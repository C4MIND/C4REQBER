"""Tests for TURBO-CDI L1 Causal Engine integration."""
from __future__ import annotations

import numpy as np

from src.causal import (
    CounterfactualEngine,
    CounterfactualQuery,
    DoCalculus,
    FCIAlgorithm,
    GESAlgorithm,
    Intervention,
    PCAlgorithm,
    StructuralCausalModel,
    run_causal_discovery,
)


class TestIntegration:
    def test_full_pipeline(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: np.random.randn())
        scm.add_node("Z", parents=["U"], mechanism=lambda u, n: u + n)
        scm.add_node("X", parents=["Z"], mechanism=lambda z, n: z + n)
        scm.add_node("Y", parents=["X", "Z"], mechanism=lambda x, z, n: x + z + n)

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        assert isinstance(identifiable, bool)

        engine = CounterfactualEngine(scm)
        result = engine.what_if(
            evidence={"X": 1.0, "Z": 0.5},
            intervention_target="X",
            intervention_value=2.0,
            target_variable="Y",
        )
        assert result.effect is not None

    def test_discovery_on_scm_data(self) -> None:
        np.random.seed(42)
        scm = StructuralCausalModel()
        scm.add_node("A", is_exogenous=True, noise=lambda: np.random.randn())
        scm.add_node("B", parents=["A"], mechanism=lambda a, n: a + n)
        scm.add_node("C", parents=["B"], mechanism=lambda b, n: b + n)

        samples = scm.sample(500)
        data = np.column_stack([samples["A"], samples["B"], samples["C"]])

        graph = run_causal_discovery(data, algorithm="pc", var_names=["A", "B", "C"])
        assert graph.number_of_nodes() == 3

    def test_causal_effect_consistency(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: 3 * x + u)

        ace = scm.get_causal_effect("X", "Y")
        assert abs(ace - 3.0) < 0.05

        calc = DoCalculus(scm)
        identifiable, _ = calc.is_identifiable("X", "Y")
        assert identifiable

    def test_all_algorithms(self) -> None:
        np.random.seed(42)
        data = np.random.randn(200, 3)

        pc_graph = run_causal_discovery(data, algorithm="pc")
        fci_graph = run_causal_discovery(data, algorithm="fci")
        ges_graph = run_causal_discovery(data, algorithm="ges")

        assert pc_graph.number_of_nodes() == 3
        assert fci_graph.number_of_nodes() == 3
        assert ges_graph.number_of_nodes() == 3

    def test_module_imports(self) -> None:
        from src.causal import __all__
        assert "StructuralCausalModel" in __all__
        assert "DoCalculus" in __all__
        assert "CounterfactualEngine" in __all__
        assert "PCAlgorithm" in __all__
        assert "FCIAlgorithm" in __all__
        assert "GESAlgorithm" in __all__
