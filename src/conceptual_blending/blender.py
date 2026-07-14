"""Conceptual Blending implementation"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InputSpace:
    """InputSpace."""
    name: str
    entities: list[str]
    relations: list[tuple[str, str, str]]  # (entity_a, relation, entity_b)
    attributes: dict[str, list[str]]  # entity -> [attributes]

@dataclass
class BlendResult:
    """BlendResult."""
    blend_name: str
    generic_space: list[str]  # Common structure
    blended_entities: list[str]
    emergent_structure: list[str]
    cross_space_mappings: list[tuple[str, str]]  # (from_input1, from_input2)
    coherence_score: float

class ConceptualBlender:
    """ConceptualBlender."""
    def blend(
        self,
        input1: InputSpace,
        input2: InputSpace,
        blend_name: str = "blend",
    ) -> BlendResult:
        # Find generic space (common structure)
        """Blend."""
        common_entities = set(input1.entities) & set(input2.entities)
        generic = list(common_entities)

        # Find cross-space mappings
        mappings: list[tuple[str, str]] = []
        for e1 in input1.entities:
            for e2 in input2.entities:
                if e1.lower() == e2.lower() or any(
                    attr.lower() in (a or "").lower()
                    for attr in (input1.attributes.get(e1, []) + input1.attributes.get(e2, []))
                    for a in [e2]
                ):
                    if e1 != e2:
                        # Semantic similarity based on shared relations
                        r1 = {r[1] for r in input1.relations if r[0] == e1 or r[2] == e1}
                        r2 = {r[1] for r in input2.relations if r[0] == e2 or r[2] == e2}
                        if r1 & r2:
                            mappings.append((e1, e2))

        # Blend entities
        blended = list(set(input1.entities) | set(input2.entities))

        # Emergent structure — entities with new properties from the blend
        emergent: list[str] = []
        for e1, e2 in mappings:
            attrs1 = set(input1.attributes.get(e1, []))
            attrs2 = set(input2.attributes.get(e2, []))
            new_attrs = attrs1 ^ attrs2  # Symmetric difference
            if new_attrs:
                emergent.append(f"{e1}/{e2}: gains {new_attrs}")

        # Coherence score based on mapping overlap
        coherence = len(mappings) / max(len(input1.entities) + len(input2.entities), 1)

        return BlendResult(
            blend_name=blend_name,
            generic_space=generic,
            blended_entities=blended,
            emergent_structure=emergent,
            cross_space_mappings=mappings,
            coherence_score=min(coherence * 2, 1.0),
        )
