"""Tests for UTA-20 operators and UTA/QZRF/Fractal27 bridge."""

import pytest

from src.operators.uta import UTAFamily, UTALibrary, UTAMode, UTAOperator
from src.operators.uta_bridge import (
    FRACTAL27_TO_UTA,
    QZRF_TO_FRACTAL27,
    apply_qzrf,
    get_uta_by_fractal,
    resolve_qzrf_to_operators,
    resolve_qzrf_to_utas,
)


class TestUTAFamily:
    """Tests for UTAFamily enum."""

    def test_family_count(self):
        """There are exactly 5 families."""
        assert len(UTAFamily) == 5

    def test_family_values(self):
        """Each family has the expected value."""
        assert UTAFamily.SENSING.value == "sensing"
        assert UTAFamily.PROCESSING.value == "processing"
        assert UTAFamily.MODULATING.value == "modulating"
        assert UTAFamily.STRUCTURING.value == "structuring"
        assert UTAFamily.FLOWING.value == "flowing"


class TestUTAMode:
    """Tests for UTAMode enum."""

    def test_mode_count(self):
        """There are exactly 4 modes."""
        assert len(UTAMode) == 4


class TestUTALibrary:
    """Tests for UTALibrary."""

    def test_operator_count(self):
        """Library contains exactly 20 operators."""
        lib = UTALibrary()
        assert len(lib.OPERATORS) == 20

    def test_get_by_id(self):
        """Operators can be retrieved by ID."""
        lib = UTALibrary()
        op = lib.get("UT-01")
        assert op is not None
        assert op.name == "Detect"

    def test_get_by_name(self):
        """Operators can be retrieved by name (case-insensitive)."""
        lib = UTALibrary()
        op = lib.get("detect")
        assert op is not None
        assert op.id == "UT-01"

    def test_get_by_name_mixed_case(self):
        """Operator lookup is case-insensitive."""
        lib = UTALibrary()
        op = lib.get("DeTeCt")
        assert op is not None
        assert op.id == "UT-01"

    def test_get_missing_returns_none(self):
        """Missing operator returns None."""
        lib = UTALibrary()
        assert lib.get("nonexistent") is None

    def test_by_family(self):
        """Operators can be filtered by family."""
        lib = UTALibrary()
        sensing = lib.by_family(UTAFamily.SENSING)
        assert len(sensing) == 4
        assert all(op.family == UTAFamily.SENSING for op in sensing)

    def test_families_cover_all_operators(self):
        """All 20 operators belong to one of the 5 families."""
        lib = UTALibrary()
        total = sum(len(lib.by_family(f)) for f in UTAFamily)
        assert total == 20

    def test_apply_operator(self):
        """Applying an operator adds the expected marker."""
        lib = UTALibrary()
        ctx = {"input": "test"}
        result = lib.apply("UT-01", ctx)
        assert result["_detected"] is True
        assert result["input"] == "test"

    def test_apply_by_name(self):
        """Applying by name works the same as by ID."""
        lib = UTALibrary()
        ctx = {}
        result = lib.apply("compress", ctx)
        assert result["_compressed"] is True

    def test_apply_missing_is_noop(self):
        """Applying a missing operator is a no-op."""
        lib = UTALibrary()
        ctx = {"input": "test"}
        result = lib.apply("missing", ctx)
        assert result == ctx

    def test_apply_sequence(self):
        """Sequences apply operators in order."""
        lib = UTALibrary()
        ctx = {}
        result = lib.apply_sequence(["detect", "parse"], ctx)
        assert result["_detected"] is True
        assert result["_parsed"] is True

    def test_all_ids_unique(self):
        """All operator IDs are unique."""
        lib = UTALibrary()
        ids = [op.id for op in lib.OPERATORS]
        assert len(ids) == len(set(ids))

    def test_all_names_unique(self):
        """All operator names are unique."""
        lib = UTALibrary()
        names = [op.name for op in lib.OPERATORS]
        assert len(names) == len(set(names))


class TestUTAOperator:
    """Tests for UTAOperator dataclass."""

    def test_operator_is_frozen(self):
        """Operators are immutable."""
        op = UTAOperator(
            id="UT-99",
            name="Test",
            family=UTAFamily.SENSING,
            description="Test operator",
            apply=lambda ctx: ctx,
        )
        with pytest.raises(AttributeError):
            op.name = "Changed"


class TestUTABridge:
    """Tests for UTA/QZRF/Fractal27 bridge mappings."""

    def test_qzrf_to_fractal27_has_14_entries(self):
        """QZRF mapping covers all 14 QZRF strategies."""
        assert len(QZRF_TO_FRACTAL27) == 14

    def test_fractal27_to_uta_keys(self):
        """Fractal27 mapping contains expected keys."""
        expected = {"tau+", "tau-", "sigma", "delta", "rho", "iota",
                    "lambda+", "lambda-", "kappa+", "kappa-", "mu", "phi",
                    "shift", "cycle"}
        assert expected.issubset(FRACTAL27_TO_UTA.keys())

    def test_resolve_qzrf_to_utas(self):
        """QZRF IDs resolve to lists of UTA names."""
        names = resolve_qzrf_to_utas("QZ-01")
        assert isinstance(names, list)
        assert len(names) > 0

    def test_resolve_qzrf_to_operators(self):
        """QZRF IDs resolve to actual UTAOperator objects."""
        ops = resolve_qzrf_to_operators("QZ-01")
        assert all(isinstance(op, UTAOperator) for op in ops)

    def test_apply_qzrf(self):
        """apply_qzrf transforms a context via mapped UTA operators."""
        ctx = {"input": "test"}
        result = apply_qzrf("QZ-01", ctx)
        assert isinstance(result, dict)
        # At least one UTA marker should be present
        assert any(k.startswith("_") for k in result.keys())

    def test_get_uta_by_fractal(self):
        """get_uta_by_fractal returns operators for a fractal key."""
        ops = get_uta_by_fractal("tau+")
        assert len(ops) > 0
        assert all(isinstance(op, UTAOperator) for op in ops)

    def test_fractal27_uta_names_exist(self):
        """Every UTA name referenced in FRACTAL27_TO_UTA exists in the library."""
        lib = UTALibrary()
        all_names = set()
        for names in FRACTAL27_TO_UTA.values():
            all_names.update(names)
        missing = [name for name in all_names if lib.get(name) is None]
        assert missing == [], f"Missing UTA operators: {missing}"

    def test_bridge_integration_sequence(self):
        """End-to-end: QZRF -> Fractal27 -> UTA -> context transform."""
        lib = UTALibrary()
        for qzrf_id in QZRF_TO_FRACTAL27:
            ctx = {"test": True}
            uta_names = resolve_qzrf_to_utas(qzrf_id)
            result = lib.apply_sequence(uta_names, ctx)
            assert isinstance(result, dict)
            # Original context preserved
            assert result["test"] is True
