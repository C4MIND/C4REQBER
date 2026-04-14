"""
TURBO-CDI v8.0 - Bridge Engine
Agent 7: Cross-Domain Discovery

Automatically discovers structural homomorphisms between domains.
Identifies bridge disciplines and cross-domain analogies.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import math


@dataclass
class BridgeMapping:
    """A discovered bridge between two domains"""

    source_domain: str
    target_domain: str
    similarity_score: float  # 0-1
    shared_operations: List[str]  # Operations that work similarly
    shared_objects: List[str]  # Objects that map between domains
    analogies: List[Dict[str, str]]  # Specific analogies
    bridge_type: str  # "isomorphism", "homomorphism", "metaphor"


@dataclass
class BridgeDiscipline:
    """A discipline that bridges multiple domains"""

    name: str
    connects: List[str]  # List of domain categories it connects
    bridge_score: float  # How effective as a bridge
    disciplines: List[str]  # Specific sub-disciplines


class BridgeEngine:
    """
    Discovers and manages cross-domain bridges.

    Based on analysis showing 6 bridge disciplines connect
    humanities and exact sciences through Formal Systems Theory.

    Features:
    - Automatic bridge discovery via signature comparison
    - Bridge discipline identification
    - Cross-domain analogy generation
    - Structural homomorphism detection
    """

    # Known bridge disciplines from our analysis
    KNOWN_BRIDGE_DISCIPLINES = {
        "logic": BridgeDiscipline(
            name="Logic",
            connects=["humanities", "exact_sciences"],
            bridge_score=0.95,
            disciplines=["formal_logic", "philosophical_logic", "mathematical_logic"],
        ),
        "statistics": BridgeDiscipline(
            name="Statistics",
            connects=["humanities", "exact_sciences"],
            bridge_score=0.90,
            disciplines=[
                "mathematical_statistics",
                "social_statistics",
                "bayesian_methods",
            ],
        ),
        "computer_science": BridgeDiscipline(
            name="Computer Science",
            connects=["humanities", "exact_sciences"],
            bridge_score=0.88,
            disciplines=[
                "algorithms",
                "computational_linguistics",
                "digital_humanities",
            ],
        ),
        "cognitive_science": BridgeDiscipline(
            name="Cognitive Science",
            connects=["humanities", "exact_sciences"],
            bridge_score=0.85,
            disciplines=["psychology", "neuroscience", "philosophy_of_mind", "ai"],
        ),
        "linguistics": BridgeDiscipline(
            name="Linguistics",
            connects=["humanities", "exact_sciences"],
            bridge_score=0.82,
            disciplines=["formal_grammar", "semantics", "computational_linguistics"],
        ),
        "archaeology": BridgeDiscipline(
            name="Archaeology",
            connects=["humanities", "exact_sciences"],
            bridge_score=0.78,
            disciplines=[
                "cultural_archaeology",
                "scientific_dating",
                "material_analysis",
            ],
        ),
    }

    def __init__(self):
        self._domains: Dict[str, Dict] = {}
        self._bridges: List[BridgeMapping] = []
        self._loaded = False

    def _load_domains(self):
        """Load domain profiles for analysis"""
        if self._loaded:
            return

        try:
            import sys

            sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/v7")
            from data.domain_profiles import ALL_DOMAINS

            self._domains = ALL_DOMAINS
            self._loaded = True
        except Exception as e:
            print(f"Warning: Could not load domain profiles: {e}")
            self._loaded = True

    def discover_bridges(
        self, source_category: Optional[str] = None, min_similarity: float = 0.6
    ) -> List[BridgeMapping]:
        """
        Discover bridge mappings between domains.

        Args:
            source_category: Filter by category ("humanities", "exact_sciences")
            min_similarity: Minimum similarity threshold

        Returns:
            List of BridgeMapping objects
        """
        self._load_domains()

        if not self._domains:
            return []

        bridges = []
        domain_ids = list(self._domains.keys())

        # Compare all domain pairs
        for i, d1 in enumerate(domain_ids):
            for d2 in domain_ids[i + 1 :]:
                profile1 = self._domains[d1]
                profile2 = self._domains[d2]

                # Filter by category if specified
                if source_category:
                    cat1 = getattr(profile1, "category", "")
                    cat2 = getattr(profile2, "category", "")
                    if cat1 != source_category and cat2 != source_category:
                        continue
                    if cat1 == cat2:  # Only cross-category bridges
                        continue

                # Calculate similarity
                similarity = self._calculate_domain_similarity(profile1, profile2)

                if similarity >= min_similarity:
                    bridge = self._create_bridge_mapping(
                        d1, d2, profile1, profile2, similarity
                    )
                    bridges.append(bridge)

        # Sort by similarity
        bridges.sort(key=lambda b: b.similarity_score, reverse=True)
        return bridges

    def _calculate_domain_similarity(self, profile1: Any, profile2: Any) -> float:
        """Calculate similarity score between two domain profiles"""
        scores = []

        # Compare pentad distributions
        if hasattr(profile1, "pentad") and hasattr(profile2, "pentad"):
            pentad_sim = self._compare_distributions(profile1.pentad, profile2.pentad)
            scores.append(pentad_sim * 0.4)  # 40% weight

        # Compare septet distributions
        if hasattr(profile1, "septet") and hasattr(profile2, "septet"):
            septet_sim = self._compare_distributions(profile1.septet, profile2.septet)
            scores.append(septet_sim * 0.4)  # 40% weight

        # Compare reversibility profiles
        if hasattr(profile1, "reversibility_yes") and hasattr(
            profile2, "reversibility_yes"
        ):
            rev_sim = 1.0 - abs(profile1.reversibility_yes - profile2.reversibility_yes)
            scores.append(rev_sim * 0.2)  # 20% weight

        return sum(scores) if scores else 0.0

    def _compare_distributions(self, dist1: Any, dist2: Any) -> float:
        """Compare two distributions using cosine similarity"""
        # Get all attributes
        attrs = [
            a
            for a in dir(dist1)
            if not a.startswith("_") and not callable(getattr(dist1, a))
        ]

        if not attrs:
            return 0.0

        # Calculate dot product and magnitudes
        dot_product = 0.0
        mag1 = 0.0
        mag2 = 0.0

        for attr in attrs:
            v1 = getattr(dist1, attr, 0)
            v2 = getattr(dist2, attr, 0)

            dot_product += v1 * v2
            mag1 += v1**2
            mag2 += v2**2

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (math.sqrt(mag1) * math.sqrt(mag2))

    def _create_bridge_mapping(
        self, d1: str, d2: str, profile1: Any, profile2: Any, similarity: float
    ) -> BridgeMapping:
        """Create a bridge mapping from compared profiles"""
        # Find shared operations
        shared_ops = []
        if hasattr(profile1, "pentad") and hasattr(profile2, "pentad"):
            for op in ["ACTIVATE", "INHIBIT", "MODULATE", "REGULATE", "DISRUPT"]:
                w1 = getattr(profile1.pentad, op, 0)
                w2 = getattr(profile2.pentad, op, 0)
                if w1 > 0.1 and w2 > 0.1:  # Both use this operation
                    shared_ops.append(op)

        # Find shared objects
        shared_objs = []
        if hasattr(profile1, "septet") and hasattr(profile2, "septet"):
            for obj in [
                "STATE",
                "STRUCTURE",
                "CONTENT",
                "FUNCTION",
                "RELATIONS",
                "MEMORY",
                "BOUNDARY",
            ]:
                w1 = getattr(profile1.septet, obj, 0)
                w2 = getattr(profile2.septet, obj, 0)
                if w1 > 0.1 and w2 > 0.1:
                    shared_objs.append(obj)

        # Generate analogies
        analogies = self._generate_analogies(profile1, profile2)

        # Determine bridge type
        if similarity > 0.85:
            bridge_type = "isomorphism"
        elif similarity > 0.7:
            bridge_type = "homomorphism"
        else:
            bridge_type = "metaphor"

        return BridgeMapping(
            source_domain=d1,
            target_domain=d2,
            similarity_score=round(similarity, 3),
            shared_operations=shared_ops,
            shared_objects=shared_objs,
            analogies=analogies,
            bridge_type=bridge_type,
        )

    def _generate_analogies(self, profile1: Any, profile2: Any) -> List[Dict[str, str]]:
        """Generate specific analogies between domains"""
        analogies = []

        # This is a simplified version
        # In practice, would use more sophisticated analogy generation

        # Check for similar operation patterns
        if hasattr(profile1, "signature") and hasattr(profile2, "signature"):
            sig1 = profile1.signature
            sig2 = profile2.signature

            if sig1 and sig2:
                analogies.append(
                    {
                        "type": "signature",
                        "source": sig1,
                        "target": sig2,
                        "description": f"Both use {sig1.split(' × ')[0]} operations",
                    }
                )

        return analogies

    def find_bridge_disciplines(self) -> List[BridgeDiscipline]:
        """
        Identify disciplines that serve as bridges.

        Returns:
            List of BridgeDiscipline objects
        """
        return list(self.KNOWN_BRIDGE_DISCIPLINES.values())

    def get_cross_domain_suggestions(
        self, domain: str, n_suggestions: int = 5
    ) -> List[Tuple[str, float, str]]:
        """
        Get suggested domains for cross-domain transfer.

        Args:
            domain: Source domain
            n_suggestions: Number of suggestions

        Returns:
            List of (target_domain, similarity, reasoning)
        """
        self._load_domains()

        if domain not in self._domains:
            return []

        source_profile = self._domains[domain]
        source_category = getattr(source_profile, "category", "")

        suggestions = []

        for other_id, other_profile in self._domains.items():
            if other_id == domain:
                continue

            other_category = getattr(other_profile, "category", "")

            # Only suggest cross-category mappings
            if other_category == source_category:
                continue

            similarity = self._calculate_domain_similarity(
                source_profile, other_profile
            )

            if similarity > 0.5:  # Threshold for suggestion
                reasoning = self._generate_reasoning(
                    source_profile, other_profile, similarity
                )
                suggestions.append((other_id, round(similarity, 3), reasoning))

        # Sort by similarity
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:n_suggestions]

    def _generate_reasoning(
        self, profile1: Any, profile2: Any, similarity: float
    ) -> str:
        """Generate human-readable reasoning for bridge"""
        reasons = []

        # Check pentad similarity
        if hasattr(profile1, "pentad") and hasattr(profile2, "pentad"):
            shared = []
            for op in ["ACTIVATE", "INHIBIT", "MODULATE", "REGULATE", "DISRUPT"]:
                w1 = getattr(profile1.pentad, op, 0)
                w2 = getattr(profile2.pentad, op, 0)
                if abs(w1 - w2) < 0.1:  # Similar weights
                    shared.append(op)

            if shared:
                reasons.append(f"share {', '.join(shared)} operations")

        # Check septet similarity
        if hasattr(profile1, "septet") and hasattr(profile2, "septet"):
            shared = []
            for obj in ["STRUCTURE", "CONTENT", "STATE"]:
                w1 = getattr(profile1.septet, obj, 0)
                w2 = getattr(profile2.septet, obj, 0)
                if abs(w1 - w2) < 0.15:
                    shared.append(obj)

            if shared:
                reasons.append(f"focus on {', '.join(shared)}")

        if reasons:
            return f"High structural similarity: {' and '.join(reasons)}"
        else:
            return f"Similar transformation profile ({similarity:.0%} match)"

    def validate_bridge_hypothesis(self, domain1: str, domain2: str) -> Dict[str, Any]:
        """
        Validate whether two domains form a valid bridge.

        Returns:
            Validation report
        """
        self._load_domains()

        if domain1 not in self._domains or domain2 not in self._domains:
            return {"valid": False, "error": "One or both domains not found"}

        profile1 = self._domains[domain1]
        profile2 = self._domains[domain2]

        similarity = self._calculate_domain_similarity(profile1, profile2)

        cat1 = getattr(profile1, "category", "unknown")
        cat2 = getattr(profile2, "category", "unknown")

        is_cross_category = cat1 != cat2
        is_similar_enough = similarity >= 0.6

        return {
            "valid": is_cross_category and is_similar_enough,
            "similarity": round(similarity, 3),
            "cross_category": is_cross_category,
            "categories": (cat1, cat2),
            "meets_threshold": is_similar_enough,
            "bridge_type": "isomorphism"
            if similarity > 0.85
            else "homomorphism"
            if similarity > 0.7
            else "metaphor",
        }

    def analyze_bridge_network(self) -> Dict[str, Any]:
        """
        Analyze the entire bridge network.

        Returns:
            Network analysis report
        """
        self._load_domains()

        bridges = self.discover_bridges(min_similarity=0.6)

        # Count connections per domain
        domain_connections = {}
        for bridge in bridges:
            for domain in [bridge.source_domain, bridge.target_domain]:
                if domain not in domain_connections:
                    domain_connections[domain] = 0
                domain_connections[domain] += 1

        # Find most connected domains
        most_connected = sorted(
            domain_connections.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Bridge type distribution
        type_counts = {}
        for bridge in bridges:
            bt = bridge.bridge_type
            type_counts[bt] = type_counts.get(bt, 0) + 1

        return {
            "total_bridges": len(bridges),
            "domains_connected": len(domain_connections),
            "most_connected": most_connected,
            "bridge_types": type_counts,
            "average_similarity": round(
                sum(b.similarity_score for b in bridges) / len(bridges), 3
            )
            if bridges
            else 0,
        }
