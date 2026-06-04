"""Tests for TURBO-CDI L1 Causal Engine — __init__.py exports."""
from __future__ import annotations


class TestExports:
    def test_all_classes_importable(self) -> None:
        from src.causal import (
            CounterfactualEngine,
            CounterfactualQuery,
            CounterfactualResult,
            DoCalculus,
            FCIAlgorithm,
            GESAlgorithm,
            Intervention,
            PCAlgorithm,
            StructuralCausalModel,
            run_causal_discovery,
        )

        assert StructuralCausalModel is not None
        assert DoCalculus is not None
        assert CounterfactualEngine is not None
        assert PCAlgorithm is not None
        assert FCIAlgorithm is not None
        assert GESAlgorithm is not None
        assert Intervention is not None
        assert CounterfactualQuery is not None
        assert CounterfactualResult is not None
        assert run_causal_discovery is not None
