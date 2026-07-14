"""
C4REQBER: КОМПАС Metamodel
7-level depth navigation system.

КОМПАС = Концептуальная Онтологическая Модульная Платформа Абстрактных Слоёв

7 levels of abstraction for navigating any problem space:
0. Факт (Fact)      — raw data, observations
1. Явление (Phenomenon) — patterns in facts
2. Закон (Law)      — regularities, rules
3. Принцип (Principle) — underlying mechanisms
4. Мета (Meta)      — frameworks, paradigms
5. Абсолют (Absolute) — universal truths
6. Трансценденция (Transcendence) — beyond system
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class CompassLevel(IntEnum):
    """7 levels of the КОМПАС depth scale."""

    FACT = 0  # Факт
    PHENOMENON = 1  # Явление
    LAW = 2  # Закон
    PRINCIPLE = 3  # Принцип
    META = 4  # Мета
    ABSOLUTE = 5  # Абсолют
    TRANSCENDENCE = 6  # Трансценденция


@dataclass
class CompassNode:
    """A node at a specific КОМПАС level."""

    level: CompassLevel
    content: str
    source: str = ""
    children: list[CompassNode] = field(default_factory=list)
    parent: CompassNode | None = None

    @property
    def level_name(self) -> str:
        return {
            0: "Факт",
            1: "Явление",
            2: "Закон",
            3: "Принцип",
            4: "Мета",
            5: "Абсолют",
            6: "Трансценденция",
        }.get(self.level, "Unknown")

    @property
    def level_name_en(self) -> str:
        return {
            0: "Fact",
            1: "Phenomenon",
            2: "Law",
            3: "Principle",
            4: "Meta",
            5: "Absolute",
            6: "Transcendence",
        }.get(self.level, "Unknown")


@dataclass
class CompassNavigation:
    """Result of navigating a problem through КОМПАС levels."""

    problem: str
    levels: dict[int, CompassNode] = field(default_factory=dict)
    current_level: int = 0
    path: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "current_level": self.current_level,
            "current_level_name": CompassLevel(self.current_level).name
            if 0 <= self.current_level <= 6
            else "Unknown",
            "levels": {
                level: {
                    "name": node.level_name,
                    "name_en": node.level_name_en,
                    "content": node.content,
                    "source": node.source,
                }
                for level, node in self.levels.items()
            },
            "path": self.path,
        }


class CompassEngine:
    """
    КОМПАС Engine: navigate problems across 7 depth levels.

    Usage:
        engine = CompassEngine()
        nav = engine.explore("Why does traffic congestion occur?")
        nav = engine.ascend(nav)  # Go deeper
        nav = engine.descend(nav) # Go shallower
    """

    LEVEL_DESCRIPTIONS = {
        0: {
            "name_ru": "Факт",
            "name_en": "Fact",
            "description": "Raw data, observations, measurements",
        },
        1: {
            "name_ru": "Явление",
            "name_en": "Phenomenon",
            "description": "Patterns, correlations, observed regularities",
        },
        2: {
            "name_ru": "Закон",
            "name_en": "Law",
            "description": "Formalized rules, equations, predictive models",
        },
        3: {
            "name_ru": "Принцип",
            "name_en": "Principle",
            "description": "Underlying mechanisms, causal explanations",
        },
        4: {
            "name_ru": "Мета",
            "name_en": "Meta",
            "description": "Frameworks, paradigms, ontologies",
        },
        5: {
            "name_ru": "Абсолют",
            "name_en": "Absolute",
            "description": "Universal truths, mathematical certainties",
        },
        6: {
            "name_ru": "Трансценденция",
            "name_en": "Transcendence",
            "description": "Beyond the system, unprovable axioms",
        },
    }

    def explore(self, problem: str) -> CompassNavigation:
        """Start exploring a problem at level 0 (Fact)."""
        nav = CompassNavigation(problem=problem, current_level=0)
        nav.levels[0] = CompassNode(
            level=CompassLevel.FACT,
            content=f"Problem statement: {problem}",
            source="user_input",
        )
        nav.path = [0]
        return nav

    def ascend(self, nav: CompassNavigation) -> CompassNavigation:
        """Go deeper (higher abstraction)."""
        if nav.current_level >= 6:
            return nav
        new_level = nav.current_level + 1
        nav.levels[new_level] = CompassNode(
            level=CompassLevel(new_level),
            content=f"Abstraction of level {nav.current_level}: {nav.levels[nav.current_level].content[:100]}...",
            source=f"derived_from_level_{nav.current_level}",
            parent=nav.levels[nav.current_level],
        )
        nav.levels[nav.current_level].children.append(nav.levels[new_level])
        nav.current_level = new_level
        nav.path.append(new_level)
        return nav

    def descend(self, nav: CompassNavigation) -> CompassNavigation:
        """Go shallower (lower abstraction)."""
        if nav.current_level <= 0:
            return nav
        nav.current_level -= 1
        nav.path.append(nav.current_level)
        return nav

    def jump_to(self, nav: CompassNavigation, level: int) -> CompassNavigation:
        """Jump to a specific level."""
        if 0 <= level <= 6:
            if level not in nav.levels:
                nav.levels[level] = CompassNode(
                    level=CompassLevel(level),
                    content=f"Level {level} analysis of: {nav.problem}",
                    source="jump",
                )
            nav.current_level = level
            nav.path.append(level)
        return nav

    def get_level_description(self, level: int) -> dict[str, str]:
        """Get description of a level."""
        return self.LEVEL_DESCRIPTIONS.get(
            level, {"name_ru": "?", "name_en": "?", "description": ""}
        )

    def analyze_depth(self, nav: CompassNavigation) -> dict[str, Any]:
        """Analyze how deeply the problem has been explored."""
        visited = set(nav.path)
        return {
            "max_depth_reached": max(nav.path) if nav.path else 0,
            "levels_visited": sorted(visited),
            "levels_missing": sorted(set(range(7)) - visited),
            "depth_ratio": len(visited) / 7.0,
            "is_complete": len(visited) == 7,
        }
