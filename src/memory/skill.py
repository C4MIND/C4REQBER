from __future__ import annotations

import logging


"""
Skill Tier + Auto-Creation System for C44TCDI v4.1.
Hermes-style reusable prompt+tools bundles with effectiveness scoring.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    """Reusable prompt+tools bundle."""
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    effectiveness_score: float = 0.5
    created: str = ""
    last_used: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    usage_count: int = 0
    skill_type: str = "general"  # general, cognitive, scientific, engineering
    estimated_time_saved: int = 0  # minutes saved per use


@dataclass
class SkillExecutionResult:
    """Result of executing a skill."""
    skill_name: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    error_message: str = ""


class SkillCurator:
    """Curates and scores skills based on effectiveness."""

    def __init__(self, skills_dir: str = ".kilo/skills") -> None:
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._load_skills()
        self.logger = logging.getLogger("SkillCurator")

    def _load_skills(self) -> None:
        """Load all skills from directory."""
        self.skills: dict[str, Skill] = {}
        if not self.skills_dir.exists():
            return

        for yaml_file in self.skills_dir.glob("*.yaml"):
            try:
                import yaml  # type: ignore[import-untyped]
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                skill = Skill(**data)
                self.skills[skill.name] = skill
                self.logger.debug(f"Loaded skill: {skill.name}")
            except (ImportError, AttributeError, ConnectionError) as e:
                self.logger.error(f"Failed to load {yaml_file}: {e}")

    def after_task(self, task_name: str, result: dict[str, Any]) -> Skill | None:
        """Analyze task, extract reusable patterns, create skill if useful."""
        self.logger.info(f"Analyzing task: {task_name}")

        # What worked?
        success_patterns = self._extract_patterns(task_name, result)
        if not success_patterns:
            self.logger.info("No reusable patterns found")
            return None

        # Is it reusable?
        if not self._is_reusable(success_patterns):
            self.logger.info("Patterns not generalizable enough")
            return None

        # Generalize to YAML bundle
        skill = self._create_skill(success_patterns, task_name)
        if not skill:
            return None

        # Score effectiveness
        skill.effectiveness_score = self._estimate_effectiveness(skill)

        # Store
        self._save_skill(skill)
        self.logger.info(f"Created skill: {skill.name} (score: {skill.effectiveness_score:.2f})")

        return skill

    def _extract_patterns(self, task: str, result: dict) -> list[dict]:
        """Extract reusable steps from successful task."""
        patterns = []

        # Extract from result steps
        if "steps" in result:
            patterns.extend(result["steps"])

        # Extract from result actions
        if "actions" in result:
            for action in result["actions"]:
                if isinstance(action, dict):
                    patterns.append(action)
                elif isinstance(action, str):
                    patterns.append({"action": action, "description": ""})

        # Extract from result plugins
        if "plugins_executed" in result:
            for plugin in result["plugins_executed"]:
                patterns.append({
                    "action": "run_plugin",
                    "plugin": plugin.get("name", ""),
                    "description": plugin.get("display_name", ""),
                })

        return patterns

    def _is_reusable(self, patterns: list) -> bool:
        """Check if patterns are generalizable."""
        if len(patterns) < 3:
            return False

        # Check if patterns have clear actions
        actions = [p.get("action") for p in patterns if isinstance(p, dict)]
        unique_actions = set(a for a in actions if a)

        # Need at least 2 unique actions
        return len(unique_actions) >= 2

    def _create_skill(self, patterns: list, context: str) -> Skill | None:
        """Create skill YAML bundle."""
        try:
            # Generate skill name from context
            name = context.lower().replace(" ", "_").replace("-", "_")[:50]
            if not name:
                name = f"skill_{int(time.time())}"

            # Check if skill already exists
            if name in self.skills:
                self.logger.warning(f"Skill {name} already exists, skipping")
                return None

            skill = Skill(
                name=name,
                description=f"Auto-generated from {context}",
                tags=["auto-created"] + self._extract_tags(context),
                created=time.strftime("%Y-%m-%d"),
                steps=patterns,
                skill_type=self._classify_skill_type(context),
            )

            self.logger.info(f"Created skill: {skill.name}")
            return skill

        except (ImportError, AttributeError, ConnectionError) as e:
            self.logger.error(f"Failed to create skill: {e}")
            return None

    def _extract_tags(self, context: str) -> list[str]:
        """Extract relevant tags from context."""
        tags = []
        context_lower = context.lower()

        if "discover" in context_lower or "hypothesis" in context_lower:
            tags.append("discovery")
        if "c4" in context_lower or "cognitive" in context_lower:
            tags.append("c4")
        if "triz" in context_lower or "contradiction" in context_lower:
            tags.append("triz")
        if "validation" in context_lower or "verify" in context_lower:
            tags.append("validation")
        if "paradigm" in context_lower or "shift" in context_lower:
            tags.append("paradigm-shift")

        return tags[:5]  # Max 5 tags

    def _classify_skill_type(self, context: str) -> str:
        """Classify skill type based on context."""
        context_lower = context.lower()

        if any(w in context_lower for w in ["scientif", "research", "paper", "hypothesis"]):
            return "scientific"
        if any(w in context_lower for w in ["engineer", "design", "build", "invent"]):
            return "engineering"
        if any(w in context_lower for w in ["strateg", "decision", "plan"]):
            return "strategic"
        return "general"

    def _estimate_effectiveness(self, skill: Skill) -> float:
        """Estimate how helpful this skill will be (0.0-1.0)."""
        score = 0.5  # Base score

        # More steps = more useful
        if len(skill.steps) > 5:
            score += 0.2
        elif len(skill.steps) > 3:
            score += 0.1

        # Has verification = more reliable
        if "verification" in skill.tags:
            score += 0.2

        # Has specific skill type = more targeted
        if skill.skill_type != "general":
            score += 0.1

        # Has good tags = better organized
        if len(skill.tags) >= 3:
            score += 0.1

        return min(score, 1.0)

    def _save_skill(self, skill: Skill) -> None:
        """Save skill to YAML file."""
        import yaml

        path = self.skills_dir / f"{skill.name}.yaml"
        data = {
            "name": skill.name,
            "description": skill.description,
            "tags": skill.tags,
            "effectiveness_score": skill.effectiveness_score,
            "created": skill.created,
            "last_used": skill.last_used,
            "steps": skill.steps,
            "verification": skill.verification,
            "usage_count": skill.usage_count,
            "skill_type": skill.skill_type,
            "estimated_time_saved": skill.estimated_time_saved,
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        self.skills[skill.name] = skill
        self.logger.info(f"Saved skill to {path}")

    def rank_skills(self, query: str | None = None) -> list[Skill]:
        """Rank skills by effectiveness score, optionally filter by query."""
        skills = list(self.skills.values())

        if query:
            query_lower = query.lower()
            skills = [
                s for s in skills
                if query_lower in s.name.lower() or
                   query_lower in s.description.lower() or
                   any(query_lower in tag for tag in s.tags)
            ]

        skills.sort(key=lambda s: s.effectiveness_score, reverse=True)
        return skills

    def load_skill(self, name: str) -> Skill | None:
        """Load a specific skill."""
        return self.skills.get(name)

    def apply_skill(self, name: str, context: dict) -> SkillExecutionResult:
        """Apply skill steps to current context."""
        skill = self.load_skill(name)
        if not skill:
            return SkillExecutionResult(
                skill_name=name,
                success=False,
                error_message=f"Skill not found: {name}",
            )

        start_time = time.time()

        try:
            # Update usage
            skill.usage_count += 1
            skill.last_used = time.strftime("%Y-%m-%d")
            self._save_skill(skill)

            # Apply steps (simplified - in real implementation would execute each step)
            result = {
                "skill": skill.name,
                "steps_applied": len(skill.steps),
                "context_updated": context,
                "skill_type": skill.skill_type,
            }

            execution_time = time.time() - start_time

            return SkillExecutionResult(
                skill_name=skill.name,
                success=True,
                output=result,
                execution_time=execution_time,
            )

        except (ImportError, AttributeError, ConnectionError) as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Skill {skill.name} execution failed: {e}")
            return SkillExecutionResult(
                skill_name=skill.name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
            )

    def get_statistics(self) -> dict[str, Any]:
        """Get skill system statistics."""
        if not self.skills:
            return {
                "total_skills": 0,
                "avg_effectiveness": 0.0,
                "total_usage": 0,
                "by_type": {},
            }

        total_usage = sum(s.usage_count for s in self.skills.values())
        avg_score = sum(s.effectiveness_score for s in self.skills.values()) / len(self.skills)

        by_type: dict[str, int] = {}
        for s in self.skills.values():
            by_type[s.skill_type] = by_type.get(s.skill_type, 0) + 1

        return {
            "total_skills": len(self.skills),
            "avg_effectiveness": round(avg_score, 2),
            "total_usage": total_usage,
            "by_type": by_type,
            "top_skills": [
                {"name": s.name, "score": s.effectiveness_score, "usage": s.usage_count}
                for s in sorted(self.skills.values(), key=lambda x: x.effectiveness_score, reverse=True)[:5]
            ],
        }


class SkillRegistry:
    """Registry for discovering and managing skills."""

    def __init__(self, curator: SkillCurator) -> None:
        self.curator = curator
        self.logger = logging.getLogger("SkillRegistry")

    def discover_skills(self, query: str | None = None) -> list[dict[str, Any]]:
        """Discover skills, optionally filtered by query."""
        skills = self.curator.rank_skills(query)
        return [
            {
                "name": s.name,
                "description": s.description,
                "tags": s.tags,
                "score": s.effectiveness_score,
                "usage": s.usage_count,
                "type": s.skill_type,
                "last_used": s.last_used,
            }
            for s in skills
        ]

    def get_skill_details(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about a skill."""
        skill = self.curator.load_skill(name)
        if not skill:
            return None

        return {
            "name": skill.name,
            "description": skill.description,
            "tags": skill.tags,
            "steps": skill.steps,
            "verification": skill.verification,
            "effectiveness_score": skill.effectiveness_score,
            "usage_count": skill.usage_count,
            "last_used": skill.last_used,
            "skill_type": skill.skill_type,
            "estimated_time_saved": skill.estimated_time_saved,
        }

    def execute_skill(self, name: str, context: dict) -> dict[str, Any]:
        """Execute a skill and return results."""
        result = self.curator.apply_skill(name, context)
        return {
            "skill_name": result.skill_name,
            "success": result.success,
            "output": result.output,
            "execution_time": result.execution_time,
            "error": result.error_message if not result.success else None,
        }

    def update_skill_usage(self, name: str) -> None:
        """Update skill usage statistics."""
        skill = self.curator.load_skill(name)
        if skill:
            skill.usage_count += 1
            skill.last_used = time.strftime("%Y-%m-%d")
            self.curator._save_skill(skill)
            self.logger.info(f"Updated usage for skill: {name}")

    def get_next_skill_for_task(self, task_description: str) -> str | None:
        """Recommend the best skill for a given task."""
        # Simple keyword matching (in production would use embeddings)
        task_lower = task_description.lower()

        best_skill = None
        best_score = 0.0

        for skill in self.curator.skills.values():
            score = 0.0

            # Check name match
            if skill.name.lower() in task_lower:
                score += 0.5

            # Check description match
            if skill.description.lower() in task_lower:
                score += 0.3

            # Check tags match
            for tag in skill.tags:
                if tag in task_lower:
                    score += 0.1

            # Boost by effectiveness
            score *= skill.effectiveness_score

            if score > best_score:
                best_score = score
                best_skill = skill.name

        return best_skill


# Example skill bundle (YAML format)
EXAMPLE_SKILL = """
name: c4-discovery-bundle
description: Complete C4 discovery workflow with validation
tags: [discovery, c4, validation, paradigm-shift]
effectiveness_score: 0.95
created: 2026-05-05
last_used: 2026-05-05
steps:
  - action: navigate_c4
    description: Map problem to C4 cognitive space
  - action: run_triz_analysis
    description: Apply TRIZ contradiction matrix
  - action: search_knowledge
    description: Query 12+ knowledge sources
  - action: mine_gaps
    description: Find research gaps with LLM
  - action: validate_novelty
    description: 3-pass novelty check
verification:
  - check_bayesian: true
  - check_monte_carlo: true
  - check_falsifier: true
skill_type: scientific
estimated_time_saved: 120
"""

# Initialize skill system (called from main)
def initialize_skill_system(skills_dir: str = ".kilo/skills") -> SkillRegistry:
    """Initialize the skill system."""
    curator = SkillCurator(skills_dir)
    registry = SkillRegistry(curator)
    return registry
