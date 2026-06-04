from __future__ import annotations

import time

from c4.stratified_blocks import BlockRegistry, C4Block


class TestC4Block:
    def test_construction_with_minimal_fields(self) -> None:
        block = C4Block(id="b1", text="hello", layer=2, state="Present:Abstract:Other", stage="verify")
        assert block.id == "b1"
        assert block.text == "hello"
        assert block.layer == 2
        assert block.state == "Present:Abstract:Other"
        assert block.stage == "verify"
        assert block.verification is None
        assert block.path is None
        assert block.citations == []

    def test_badge_layer_1_verified(self) -> None:
        block = C4Block(id="b1", text="x", layer=1, state="Present:Concrete:Self", stage="discover", verification="verified")
        badge = block.badge
        assert "C1" in badge
        assert "✓" in badge
        assert "discover" in badge

    def test_badge_layer_3_falsified(self) -> None:
        block = C4Block(id="b1", text="x", layer=3, state="Future:Meta:System", stage="test", verification="falsified")
        badge = block.badge
        assert "C3" in badge
        assert "✗" in badge

    def test_badge_no_verification_symbol(self) -> None:
        block = C4Block(id="b1", text="x", layer=2, state="Present:Abstract:Other", stage="analyse")
        badge = block.badge
        assert "✓" not in badge
        assert "✗" not in badge


class TestBlockRegistry:
    def test_add_and_len(self) -> None:
        reg = BlockRegistry()
        assert len(reg) == 0
        reg.add(C4Block(id="a", text="t", layer=1, state="s", stage="st"))
        assert len(reg) == 1
        reg.add(C4Block(id="b", text="t", layer=1, state="s", stage="st"))
        assert len(reg) == 2

    def test_by_layer_filters_correctly(self) -> None:
        reg = BlockRegistry()
        reg.add(C4Block(id="a", text="t", layer=1, state="s", stage="st"))
        reg.add(C4Block(id="b", text="t", layer=2, state="s", stage="st"))
        reg.add(C4Block(id="c", text="t", layer=1, state="s", stage="st"))
        assert len(reg.by_layer(1)) == 2
        assert len(reg.by_layer(2)) == 1
        assert len(reg.by_layer(3)) == 0

    def test_by_path_filters_correctly(self) -> None:
        reg = BlockRegistry()
        reg.add(C4Block(id="a", text="t", layer=1, state="s", stage="st", path="p1"))
        reg.add(C4Block(id="b", text="t", layer=1, state="s", stage="st", path="p2"))
        reg.add(C4Block(id="c", text="t", layer=1, state="s", stage="st", path="p1"))
        assert len(reg.by_path("p1")) == 2
        assert len(reg.by_path("p2")) == 1
        assert len(reg.by_path("p3")) == 0

    def test_by_verification_filters_correctly(self) -> None:
        reg = BlockRegistry()
        reg.add(C4Block(id="a", text="t", layer=1, state="s", stage="st", verification="verified"))
        reg.add(C4Block(id="b", text="t", layer=1, state="s", stage="st", verification="falsified"))
        reg.add(C4Block(id="c", text="t", layer=1, state="s", stage="st", verification="verified"))
        assert len(reg.by_verification("verified")) == 2
        assert len(reg.by_verification("falsified")) == 1
        assert len(reg.by_verification("unknown")) == 0

    def test_provenance_returns_earlier_blocks(self) -> None:
        reg = BlockRegistry()
        b1 = C4Block(id="first", text="t", layer=1, state="s", stage="st")
        time.sleep(0.01)
        b2 = C4Block(id="second", text="t", layer=1, state="s", stage="st")
        time.sleep(0.01)
        b3 = C4Block(id="third", text="t", layer=1, state="s", stage="st")
        reg.add(b1)
        reg.add(b2)
        reg.add(b3)
        provenance = reg.provenance("third")
        assert len(provenance) == 2
        assert {b.id for b in provenance} == {"first", "second"}

    def test_provenance_unknown_id_returns_empty(self) -> None:
        reg = BlockRegistry()
        assert reg.provenance("nonexistent") == []

    def test_filter_combined_criteria(self) -> None:
        reg = BlockRegistry()
        reg.add(C4Block(id="a", text="t", layer=1, state="s", stage="st", path="p1", verification="verified"))
        reg.add(C4Block(id="b", text="t", layer=2, state="s", stage="st", path="p1", verification="verified"))
        reg.add(C4Block(id="c", text="t", layer=1, state="s", stage="st", path="p2", verification="verified"))
        reg.add(C4Block(id="d", text="t", layer=1, state="s", stage="st", path="p1", verification="falsified"))
        result = reg.filter(layer=1, path="p1", verification="verified")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_filter_no_criteria_returns_all(self) -> None:
        reg = BlockRegistry()
        reg.add(C4Block(id="a", text="t", layer=1, state="s", stage="st"))
        reg.add(C4Block(id="b", text="t", layer=2, state="s", stage="st"))
        assert len(reg.filter()) == 2
