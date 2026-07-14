"""
C4REQBER: 153 Metaprograms Library - Patterns and profiles
"""
from __future__ import annotations

import random

from src.metamodels.mp.core import Metaprogram, MPDimension, MPProfile
from src.metamodels.mp.data import CORE_METAPROGRAMS


class MPLibrary:
    """
    Library of 153 Metaprograms.

    Key insight: Any agent with a fixed MP profile has blind spots.
    MP rotation = same problem analyzed through multiple perceptual lenses.
    """

    def __init__(self) -> None:
        self.programs: list[Metaprogram] = []
        self._build_core_programs()
        self._by_id: dict[str, Metaprogram] = {p.id: p for p in self.programs}
        self._by_dimension: dict[MPDimension, list[Metaprogram]] = {}
        for p in self.programs:
            self._by_dimension.setdefault(p.dimension, []).append(p)
        self._profiles: dict[str, MPProfile] = {}
        self._build_profiles()

    def _build_core_programs(self) -> None:
        """Build core MP library (subset of 153, extensible)."""
        self.programs.extend(CORE_METAPROGRAMS)

    def _build_profiles(self) -> None:
        """Build pre-configured MP profiles for agent rotation."""
        all_ids = [p.id for p in self.programs]

        # Profile: Systems Thinker
        self._profiles["systems"] = MPProfile(
            name="Systems Thinker",
            name_ru="Системный мыслитель",
            settings={mp_id: "balanced" for mp_id in all_ids},
            description="Balanced, holistic perspective with slight bias toward global thinking",
        )
        self._profiles["systems"].settings["MP-03"] = "a"  # Global
        self._profiles["systems"].settings["MP-15"] = "a"  # Abstract
        self._profiles["systems"].settings["MP-19"] = "a"  # Deep

        # Profile: Pragmatic Executor
        self._profiles["pragmatic"] = MPProfile(
            name="Pragmatic Executor",
            name_ru="Прагматичный исполнитель",
            settings={mp_id: "balanced" for mp_id in all_ids},
            description="Detail-oriented, procedure-focused, action-biased",
        )
        self._profiles["pragmatic"].settings["MP-02"] = "b"  # Procedures
        self._profiles["pragmatic"].settings["MP-03"] = "b"  # Detail
        self._profiles["pragmatic"].settings["MP-15"] = "b"  # Concrete
        self._profiles["pragmatic"].settings["MP-10"] = "a"  # Fast

        # Profile: Creative Explorer
        self._profiles["creative"] = MPProfile(
            name="Creative Explorer",
            name_ru="Творческий исследователь",
            settings={mp_id: "balanced" for mp_id in all_ids},
            description="Options-oriented, optimistic, possibility-focused",
        )
        self._profiles["creative"].settings["MP-02"] = "a"  # Options
        self._profiles["creative"].settings["MP-06"] = "a"  # Optimistic
        self._profiles["creative"].settings["MP-22"] = "a"  # Possibility
        self._profiles["creative"].settings["MP-20"] = "a"  # Goal

        # Profile: Critical Analyst
        self._profiles["critical"] = MPProfile(
            name="Critical Analyst",
            name_ru="Критический аналитик",
            settings={mp_id: "balanced" for mp_id in all_ids},
            description="Mismatch-seeking, evidence-based, pessimistic (for risk detection)",
        )
        self._profiles["critical"].settings["MP-04"] = "b"  # Mismatch
        self._profiles["critical"].settings["MP-06"] = "b"  # Pessimistic
        self._profiles["critical"].settings["MP-23"] = "a"  # Evidence
        self._profiles["critical"].settings["MP-05"] = "a"  # Rational

        # Profile: Intuitive Synthesizer
        self._profiles["intuitive"] = MPProfile(
            name="Intuitive Synthesizer",
            name_ru="Интуитивный синтезатор",
            settings={mp_id: "balanced" for mp_id in all_ids},
            description="Intuition-biased, similarity-seeking, pattern-focused",
        )
        self._profiles["intuitive"].settings["MP-05"] = "b"  # Intuitive
        self._profiles["intuitive"].settings["MP-04"] = "a"  # Match
        self._profiles["intuitive"].settings["MP-14"] = "b"  # Auditory (relational)

    def get(self, mp_id: str) -> Metaprogram | None:
        return self._by_id.get(mp_id)

    def by_dimension(self, dim: MPDimension) -> list[Metaprogram]:
        return self._by_dimension.get(dim, [])

    def get_profile(self, name: str) -> MPProfile | None:
        return self._profiles.get(name)

    def all_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def rotate_profiles(self, problem_text: str, n: int = 3) -> list[MPProfile]:
        """
        Select n diverse MP profiles for analyzing a problem.
        Ensures coverage of different perceptual angles.
        """
        all_profiles = list(self._profiles.values())
        # Simple heuristic: always include systems + critical + one based on problem text
        selected = [self._profiles["systems"], self._profiles["critical"]]

        # Pick third based on keywords in problem
        text_lower = problem_text.lower()
        if any(w in text_lower for w in ["design", "create", "new", "innovate"]):
            selected.append(self._profiles["creative"])
        elif any(w in text_lower for w in ["implement", "build", "execute", "deploy"]):
            selected.append(self._profiles["pragmatic"])
        elif any(w in text_lower for w in ["sense", "feel", "pattern", "intuition"]):
            selected.append(self._profiles["intuitive"])
        else:
            selected.append(
                random.choice(
                    [
                        p
                        for p in all_profiles
                        if p.name not in ["Systems Thinker", "Critical Analyst"]
                    ]
                )
            )

        return selected[:n]

    def all_programs(self) -> list[Metaprogram]:
        return list(self.programs)
