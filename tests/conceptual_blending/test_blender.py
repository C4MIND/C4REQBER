"""
TURBO-CDI: Conceptual Blending Tests
"""
from __future__ import annotations

import pytest

from src.conceptual_blending.blender import BlendResult, ConceptualBlender, InputSpace
from src.conceptual_blending.examples import CLOCK_BUDDHA, EXAMPLES, SHIP_EARTH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def blender():
    return ConceptualBlender()


@pytest.fixture
def simple_input1():
    return InputSpace(
        name="space1",
        entities=["a", "b", "c"],
        relations=[("a", "connects", "b"), ("b", "supports", "c")],
        attributes={"a": ["tall", "round"], "b": ["short"], "c": ["wide"]},
    )


@pytest.fixture
def simple_input2():
    return InputSpace(
        name="space2",
        entities=["a", "d", "e"],
        relations=[("a", "connects", "d"), ("d", "moves", "e")],
        attributes={"a": ["tall", "sharp"], "d": ["fast"], "e": ["light"]},
    )


@pytest.fixture
def semantic_input1():
    return InputSpace(
        name="war",
        entities=["blade", "shield"],
        relations=[("blade", "cuts", "shield"), ("blade", "pierces", "shield")],
        attributes={"blade": ["sharp", "metal"], "shield": ["strong"]},
    )


@pytest.fixture
def semantic_input2():
    return InputSpace(
        name="debate",
        entities=["sharp_word", "counterargument"],
        relations=[
            ("sharp_word", "cuts", "counterargument"),
            ("sharp_word", "pierces", "counterargument"),
        ],
        attributes={"sharp_word": ["rhetorical"], "counterargument": ["logical"]},
    )


@pytest.fixture
def clock_input():
    data = CLOCK_BUDDHA[0]
    return InputSpace(
        name=data["name"],
        entities=data["entities"],
        relations=[tuple(r) for r in data["relations"]],
        attributes=data["attributes"],
    )


@pytest.fixture
def buddha_input():
    data = CLOCK_BUDDHA[1]
    return InputSpace(
        name=data["name"],
        entities=data["entities"],
        relations=[tuple(r) for r in data["relations"]],
        attributes=data["attributes"],
    )


@pytest.fixture
def ship_input():
    data = SHIP_EARTH[0]
    return InputSpace(
        name=data["name"],
        entities=data["entities"],
        relations=[tuple(r) for r in data["relations"]],
        attributes=data["attributes"],
    )


@pytest.fixture
def earth_input():
    data = SHIP_EARTH[1]
    return InputSpace(
        name=data["name"],
        entities=data["entities"],
        relations=[tuple(r) for r in data["relations"]],
        attributes=data["attributes"],
    )


# ---------------------------------------------------------------------------
# 1. InputSpace dataclass
# ---------------------------------------------------------------------------

class TestInputSpace:
    def test_creation_basic(self):
        space = InputSpace(
            name="test",
            entities=["x", "y"],
            relations=[("x", "links", "y")],
            attributes={"x": ["a1"], "y": ["a2"]},
        )
        assert space.name == "test"
        assert space.entities == ["x", "y"]
        assert space.relations == [("x", "links", "y")]

    def test_empty_entities(self):
        space = InputSpace(name="empty", entities=[], relations=[], attributes={})
        assert space.entities == []


# ---------------------------------------------------------------------------
# 2. BlendResult dataclass
# ---------------------------------------------------------------------------

class TestBlendResult:
    def test_creation(self):
        result = BlendResult(
            blend_name="test_blend",
            generic_space=["shared"],
            blended_entities=["shared", "a", "b"],
            emergent_structure=["a/b: gains {'x'}"],
            cross_space_mappings=[("a", "b")],
            coherence_score=0.5,
        )
        assert result.blend_name == "test_blend"
        assert result.coherence_score == 0.5


# ---------------------------------------------------------------------------
# 3. Basic blending
# ---------------------------------------------------------------------------

class TestBasicBlending:
    def test_returns_blend_result(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2)
        assert isinstance(result, BlendResult)

    def test_finds_generic_space(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2)
        assert "a" in result.generic_space  # 'a' is in both

    def test_blended_entities_union(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2)
        assert set(result.blended_entities) == {"a", "b", "c", "d", "e"}

    def test_finds_cross_mappings_semantic(self, blender, semantic_input1, semantic_input2):
        result = blender.blend(semantic_input1, semantic_input2)
        assert ("blade", "sharp_word") in result.cross_space_mappings

    def test_emergent_structure_semantic(self, blender, semantic_input1, semantic_input2):
        result = blender.blend(semantic_input1, semantic_input2)
        emergent_texts = "\n".join(result.emergent_structure)
        assert "metal" in emergent_texts or "rhetorical" in emergent_texts

    def test_coherence_in_range(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2)
        assert 0.0 <= result.coherence_score <= 1.0

    def test_no_cross_mappings_without_shared_relations(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2)
        assert result.cross_space_mappings == []


# ---------------------------------------------------------------------------
# 4. Clock-Buddha example
# ---------------------------------------------------------------------------

class TestClockBuddha:
    def test_blend_clock_buddha(self, blender, clock_input, buddha_input):
        result = blender.blend(clock_input, buddha_input, "clock_buddha")
        assert result.blend_name == "clock_buddha"

    def test_time_in_generic(self, blender, clock_input, buddha_input):
        result = blender.blend(clock_input, buddha_input)
        assert "time" in result.generic_space

    def test_clock_buddha_has_blended_entities(self, blender, clock_input, buddha_input):
        result = blender.blend(clock_input, buddha_input)
        assert "hands" in result.blended_entities
        assert "body" in result.blended_entities
        assert "mechanism" in result.blended_entities
        assert "meditation" in result.blended_entities


# ---------------------------------------------------------------------------
# 5. Ship-Earth example
# ---------------------------------------------------------------------------

class TestShipEarth:
    def test_blend_ship_earth(self, blender, ship_input, earth_input):
        result = blender.blend(ship_input, earth_input, "spaceship_earth")
        assert result.blend_name == "spaceship_earth"

    def test_example_exists(self):
        assert "ship_earth" in EXAMPLES


# ---------------------------------------------------------------------------
# 6. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_inputs(self, blender):
        empty1 = InputSpace(name="e1", entities=[], relations=[], attributes={})
        empty2 = InputSpace(name="e2", entities=[], relations=[], attributes={})
        result = blender.blend(empty1, empty2)
        assert result.generic_space == []
        assert result.blended_entities == []
        assert result.coherence_score == 0.0

    def test_identical_inputs(self, blender):
        inp = InputSpace(
            name="dup",
            entities=["x", "y"],
            relations=[("x", "connects", "y")],
            attributes={"x": ["tall"], "y": ["short"]},
        )
        result = blender.blend(inp, inp)
        assert set(result.generic_space) == {"x", "y"}
        assert len(result.blended_entities) == 2

    def test_no_shared_entities_no_mappings(self, blender):
        inp1 = InputSpace(
            name="island1",
            entities=["apple", "banana"],
            relations=[("apple", "grows_on", "banana")],
            attributes={"apple": ["red"], "banana": ["yellow"]},
        )
        inp2 = InputSpace(
            name="island2",
            entities=["car", "dog"],
            relations=[("car", "chases", "dog")],
            attributes={"car": ["fast"], "dog": ["loud"]},
        )
        result = blender.blend(inp1, inp2)
        assert result.generic_space == []
        assert result.cross_space_mappings == []
        assert result.coherence_score == 0.0

    def test_blend_name_default(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2)
        assert result.blend_name == "blend"

    def test_blend_name_custom(self, blender, simple_input1, simple_input2):
        result = blender.blend(simple_input1, simple_input2, "my_blend")
        assert result.blend_name == "my_blend"


# ---------------------------------------------------------------------------
# 7. Coherence score edge cases
# ---------------------------------------------------------------------------

class TestCoherenceScore:
    def test_full_coherence_capped(self, blender):
        # Two different inputs where every entity maps
        inp1 = InputSpace(
            name="set1",
            entities=["b", "d"],
            relations=[("b", "links", "d")],
            attributes={"b": ["hot"], "d": ["cold"]},
        )
        inp2 = InputSpace(
            name="set2",
            entities=["hot_node", "cold_node"],
            relations=[("hot_node", "links", "cold_node")],
            attributes={"hot_node": ["burning"], "cold_node": ["freezing"]},
        )
        result = blender.blend(inp1, inp2)
        assert result.coherence_score == 1.0

    def test_zero_entities_safe(self, blender):
        inp = InputSpace(name="none", entities=[], relations=[], attributes={})
        result = blender.blend(inp, inp)
        assert result.coherence_score == 0.0
