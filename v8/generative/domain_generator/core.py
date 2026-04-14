"""
TURBO-CDI v8.0 - Domain Generator
Agent 3: Generative Systems

Auto-synthesizes novel domain profiles from partial information.
Generates complete transformation signatures for new domains.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import random
import math
import os
import sys
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules import PentadOperation, SeptetObject

# Configurable path with fallback
V7_DATA_PATH = os.environ.get(
    "TURBO_CDI_V7_DATA", Path(__file__).parent.parent.parent.parent / "v7" / "data"
)


def load_domain_profiles():
    """Load domain profiles from v7 data with fallback"""
    try:
        data_path = str(V7_DATA_PATH)
        if data_path not in sys.path:
            sys.path.insert(0, data_path)
        from data.domain_profiles import ALL_DOMAINS

        return ALL_DOMAINS
    except ImportError:
        return {}


@dataclass
class DomainSignature:
    """Generated signature for a domain"""

    domain_name: str
    category: str  # humanities, exact_sciences, boundary
    pentad_weights: Dict[str, float]
    septet_weights: Dict[str, float]
    reversibility_profile: Dict[str, float]
    confidence: float  # 0-1, how confident in the generation
    basis_domains: List[str]  # Which domains this was derived from


class DomainGenerator:
    """
    Generates novel domain profiles through analogical reasoning.

    Uses bridge disciplines as templates to generate profiles for
    new or hybrid domains.
    """

    def __init__(self):
        self._bridge_domains: Dict[str, Dict] = {}
        self._loaded_profiles = False

    def _load_reference_profiles(self):
        """Load existing domain profiles as reference"""
        if self._loaded_profiles:
            return

        try:
            ALL_DOMAINS = load_domain_profiles()

            # Identify bridge domains (those that appear in both cultures)
            self._bridge_domains = {
                k: v
                for k, v in ALL_DOMAINS.items()
                if any(
                    x in k.lower()
                    for x in [
                        "logic",
                        "statistic",
                        "computer",
                        "cognitive",
                        "linguistic",
                        "archaeology",
                    ]
                )
            }
            self._loaded_profiles = True

        except Exception as e:
            print(f"Warning: Could not load domain profiles: {e}")
            self._loaded_profiles = True  # Mark as loaded to avoid retrying

    def generate_from_description(
        self, domain_name: str, description: str, similar_to: Optional[List[str]] = None
    ) -> DomainSignature:
        """
        Generate a domain profile from a text description.

        Args:
            domain_name: Name of the new domain
            description: Text description of the domain
            similar_to: Optional list of similar existing domains

        Returns:
            Generated DomainSignature
        """
        self._load_reference_profiles()

        # Parse description for keywords
        keywords = self._extract_keywords(description.lower())

        # Determine category
        category = self._infer_category(keywords)

        # Find basis domains
        basis = similar_to or self._find_basis_domains(keywords, category)

        # Generate pentad weights
        pentad = self._generate_pentad(keywords, basis, category)

        # Generate septet weights
        septet = self._generate_septet(keywords, basis, category)

        # Generate reversibility profile
        reversibility = self._generate_reversibility(category)

        # Calculate confidence
        confidence = self._calculate_confidence(basis, keywords)

        return DomainSignature(
            domain_name=domain_name,
            category=category,
            pentad_weights=pentad,
            septet_weights=septet,
            reversibility_profile=reversibility,
            confidence=confidence,
            basis_domains=basis,
        )

    def _extract_keywords(self, description: str) -> Dict[str, float]:
        """Extract and weight keywords from description"""
        keywords = {}

        # Operation-related keywords
        op_keywords = {
            "activate": [
                "create",
                "build",
                "start",
                "initiate",
                "generate",
                "construct",
            ],
            "inhibit": ["prevent", "stop", "block", "constrain", "limit", "restrict"],
            "modulate": ["adjust", "tune", "calibrate", "adapt", "modify", "tweak"],
            "regulate": ["control", "govern", "manage", "coordinate", "direct"],
            "disrupt": [
                "transform",
                "revolutionize",
                "break",
                "shift",
                "change radically",
            ],
        }

        for op, words in op_keywords.items():
            weight = sum(1.5 if word in description else 0 for word in words)
            if weight > 0:
                keywords[op] = min(weight / 3, 1.0)  # Cap at 1.0

        # Object-related keywords
        obj_keywords = {
            "STATE": ["state", "condition", "mode", "status", "phase"],
            "STRUCTURE": [
                "structure",
                "form",
                "organization",
                "arrangement",
                "framework",
            ],
            "CONTENT": ["content", "meaning", "information", "data", "substance"],
            "FUNCTION": ["function", "purpose", "goal", "objective", "aim"],
            "RELATIONS": [
                "relation",
                "connection",
                "link",
                "relationship",
                "association",
            ],
            "MEMORY": ["memory", "history", "past", "record", "recall"],
            "BOUNDARY": ["boundary", "limit", "edge", "border", "threshold"],
        }

        for obj, words in obj_keywords.items():
            weight = sum(1.5 if word in description else 0 for word in words)
            if weight > 0:
                keywords[obj] = min(weight / 3, 1.0)

        # Category indicators
        if any(
            w in description
            for w in ["human", "social", "culture", "art", "philosophy"]
        ):
            keywords["_category_humanities"] = 0.8
        if any(
            w in description
            for w in ["math", "physics", "science", "computation", "formal"]
        ):
            keywords["_category_exact"] = 0.8
        if any(
            w in description
            for w in ["bridge", "interdisciplinary", "interface", "connect"]
        ):
            keywords["_category_boundary"] = 0.8

        return keywords

    def _infer_category(self, keywords: Dict[str, float]) -> str:
        """Infer domain category from keywords"""
        if keywords.get("_category_boundary", 0) > 0.5:
            return "boundary"
        elif keywords.get("_category_exact", 0) > keywords.get(
            "_category_humanities", 0
        ):
            return "exact_sciences"
        else:
            return "humanities"

    def _find_basis_domains(
        self, keywords: Dict[str, float], category: str
    ) -> List[str]:
        """Find most similar existing domains as basis"""
        if not self._bridge_domains:
            return ["general"]

        # Score each bridge domain by keyword overlap
        scores = []
        for domain_id, profile in self._bridge_domains.items():
            score = 0

            # Check category match
            if hasattr(profile, "category") and profile.category == category:
                score += 2

            # Check name overlap with keywords
            domain_words = domain_id.lower().replace("/", " ").split()
            for word in domain_words:
                if word in keywords:
                    score += keywords[word]

            scores.append((domain_id, score))

        # Return top 3 matches
        scores.sort(key=lambda x: x[1], reverse=True)
        return [d[0] for d in scores[:3]] if scores else ["general"]

    def _generate_pentad(
        self, keywords: Dict[str, float], basis: List[str], category: str
    ) -> Dict[str, float]:
        """Generate pentad operation weights"""
        # Start with category defaults
        if category == "humanities":
            weights = {
                "ACTIVATE": 0.20,
                "INHIBIT": 0.15,
                "MODULATE": 0.30,
                "REGULATE": 0.20,
                "DISRUPT": 0.15,
            }
        elif category == "exact_sciences":
            weights = {
                "ACTIVATE": 0.35,
                "INHIBIT": 0.10,
                "MODULATE": 0.05,
                "REGULATE": 0.25,
                "DISRUPT": 0.25,
            }
        else:  # boundary
            weights = {
                "ACTIVATE": 0.25,
                "INHIBIT": 0.15,
                "MODULATE": 0.20,
                "REGULATE": 0.25,
                "DISRUPT": 0.15,
            }

        # Adjust based on keywords
        for op in ["activate", "inhibit", "modulate", "regulate", "disrupt"]:
            if op in keywords:
                op_upper = op.upper()
                if op_upper in weights:
                    weights[op_upper] = min(0.5, weights[op_upper] + keywords[op] * 0.2)

        # Normalize to sum to 1.0
        total = sum(weights.values())
        return {k: round(v / total, 4) for k, v in weights.items()}

    def _generate_septet(
        self, keywords: Dict[str, float], basis: List[str], category: str
    ) -> Dict[str, float]:
        """Generate septet object weights"""
        # Start with category defaults
        if category == "humanities":
            weights = {
                "STATE": 0.15,
                "STRUCTURE": 0.15,
                "CONTENT": 0.35,
                "FUNCTION": 0.10,
                "RELATIONS": 0.15,
                "MEMORY": 0.05,
                "BOUNDARY": 0.05,
            }
        elif category == "exact_sciences":
            weights = {
                "STATE": 0.20,
                "STRUCTURE": 0.35,
                "CONTENT": 0.10,
                "FUNCTION": 0.15,
                "RELATIONS": 0.10,
                "MEMORY": 0.05,
                "BOUNDARY": 0.05,
            }
        else:  # boundary
            weights = {
                "STATE": 0.15,
                "STRUCTURE": 0.25,
                "CONTENT": 0.15,
                "FUNCTION": 0.15,
                "RELATIONS": 0.15,
                "MEMORY": 0.10,
                "BOUNDARY": 0.05,
            }

        # Adjust based on keywords
        for obj in [
            "STATE",
            "STRUCTURE",
            "CONTENT",
            "FUNCTION",
            "RELATIONS",
            "MEMORY",
            "BOUNDARY",
        ]:
            if obj in keywords:
                weights[obj] = min(0.5, weights[obj] + keywords[obj] * 0.2)

        # Normalize to sum to 1.0
        total = sum(weights.values())
        return {k: round(v / total, 4) for k, v in weights.items()}

    def _generate_reversibility(self, category: str) -> Dict[str, float]:
        """Generate reversibility profile"""
        if category == "humanities":
            # Humanities tend toward extremes (fully reversible or not)
            return {"yes": 0.35, "conditional": 0.30, "no": 0.35}
        else:
            # Exact sciences tend toward conditional reversibility
            return {"yes": 0.05, "conditional": 0.90, "no": 0.05}

    def _calculate_confidence(
        self, basis: List[str], keywords: Dict[str, float]
    ) -> float:
        """Calculate confidence in the generation"""
        # More basis domains = higher confidence
        basis_score = min(len(basis) / 3, 1.0) * 0.4

        # More keywords matched = higher confidence
        keyword_score = min(len(keywords) / 5, 1.0) * 0.6

        return round(basis_score + keyword_score, 2)

    def generate_hybrid(
        self,
        domain_name: str,
        parent_domains: List[str],
        hybrid_ratio: Optional[List[float]] = None,
    ) -> DomainSignature:
        """
        Generate a hybrid domain by combining existing domains.

        Args:
            domain_name: Name for the new hybrid domain
            parent_domains: List of parent domain IDs to combine
            hybrid_ratio: Optional weighting for each parent (must sum to 1.0)

        Returns:
            Generated hybrid DomainSignature
        """
        self._load_reference_profiles()

        if len(parent_domains) < 2:
            raise ValueError("Need at least 2 parent domains for hybrid")

        try:
            ALL_DOMAINS = load_domain_profiles()

            # Get parent profiles
            parents = []
            for pid in parent_domains:
                if pid in ALL_DOMAINS:
                    parents.append(ALL_DOMAINS[pid])

            if len(parents) < 2:
                raise ValueError(
                    f"Could not find at least 2 parent domains: {parent_domains}"
                )

            # Default equal ratio
            if hybrid_ratio is None:
                hybrid_ratio = [1.0 / len(parents)] * len(parents)

            # Normalize ratio
            total = sum(hybrid_ratio)
            hybrid_ratio = [r / total for r in hybrid_ratio]

            # Blend pentad distributions
            blended_pentad = self._blend_distributions(
                [p.pentad for p in parents], hybrid_ratio
            )

            # Blend septet distributions
            blended_septet = self._blend_distributions(
                [p.septet for p in parents], hybrid_ratio
            )

            # Determine category
            categories = [p.category for p in parents]
            category = "boundary" if len(set(categories)) > 1 else categories[0]

            return DomainSignature(
                domain_name=domain_name,
                category=category,
                pentad_weights=blended_pentad,
                septet_weights=blended_septet,
                reversibility_profile=self._generate_reversibility(category),
                confidence=0.75,  # Higher confidence for explicit blending
                basis_domains=parent_domains,
            )

        except Exception as e:
            raise ValueError(f"Could not generate hybrid: {e}")

    def _blend_distributions(
        self, distributions: List[Any], ratios: List[float]
    ) -> Dict[str, float]:
        """Blend multiple distributions according to ratios"""
        result = {}

        # Get all attributes
        attrs = [a for a in dir(distributions[0]) if not a.startswith("_")]

        for attr in attrs:
            blended = 0
            for dist, ratio in zip(distributions, ratios):
                val = getattr(dist, attr, 0)
                blended += val * ratio
            result[attr] = round(blended, 4)

        return result

    def suggest_domains_for(self, transformation_goal: str) -> List[Tuple[str, float]]:
        """
        Suggest existing domains that might help achieve a transformation goal.

        Args:
            transformation_goal: Description of what user wants to achieve

        Returns:
            List of (domain_name, relevance_score) tuples
        """
        self._load_reference_profiles()

        keywords = self._extract_keywords(transformation_goal.lower())

        suggestions = []

        # Score each known domain
        for domain_id, profile in self._bridge_domains.items():
            score = 0

            # Check if domain keywords match goal keywords
            domain_words = domain_id.lower().replace("/", " ").split()
            for word in domain_words:
                if word in keywords:
                    score += keywords[word]

            if score > 0:
                suggestions.append((domain_id, round(score, 2)))

        # Sort by relevance
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:5]
