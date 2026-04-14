"""
TURBO-CDI: Skills System
Modular skills for research assistance
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class Skill(ABC):
    """Base class for skills."""

    name: str = ""
    description: str = ""
    usage: str = ""

    @abstractmethod
    def execute(self, args: str) -> str:
        """Execute skill with arguments."""
        pass


class SkillRegistry:
    """Registry for all available skills."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill):
        """Register a skill."""
        self._skills[skill.name] = skill

    def has_skill(self, name: str) -> bool:
        """Check if skill exists."""
        return name in self._skills

    def execute(self, name: str, args: str) -> str:
        """Execute skill by name."""
        if name not in self._skills:
            return f"Skill '{name}' not found"

        try:
            return self._skills[name].execute(args)
        except Exception as e:
            return f"Error executing {name}: {e}"

    def list_skills(self) -> List[str]:
        """List all skill names."""
        return list(self._skills.keys())

    def get_all_skills(self) -> Dict[str, Skill]:
        """Get all skills."""
        return self._skills.copy()
