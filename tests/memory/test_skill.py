"""Tests for src/memory/skill.py"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch


_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from src.memory.skill import (
    EXAMPLE_SKILL,
    Skill,
    SkillCurator,
    SkillExecutionResult,
    SkillRegistry,
    initialize_skill_system,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_skills_dir(tmp_path):
    return str(tmp_path / "skills")


@pytest.fixture
def curator(temp_skills_dir):
    return SkillCurator(skills_dir=temp_skills_dir)


@pytest.fixture
def sample_skill():
    return Skill(
        name="test_skill",
        description="A test skill",
        tags=["test", "auto-created"],
        effectiveness_score=0.75,
        created="2026-05-01",
        last_used="2026-05-01",
        steps=[{"action": "step1", "description": "do something"}],
        verification=["check1"],
        usage_count=5,
        skill_type="scientific",
        estimated_time_saved=30,
    )


@pytest.fixture
def curator_with_skill(temp_skills_dir, sample_skill):
    c = SkillCurator(skills_dir=temp_skills_dir)
    c.skills[sample_skill.name] = sample_skill
    return c


@pytest.fixture
def registry(curator):
    return SkillRegistry(curator)


@pytest.fixture
def mock_yaml_data():
    return {
        "name": "yaml_skill",
        "description": "Loaded from YAML",
        "tags": ["yaml", "test"],
        "effectiveness_score": 0.8,
        "created": "2026-05-01",
        "last_used": "2026-05-02",
        "steps": [{"action": "test"}],
        "verification": [],
        "usage_count": 2,
        "skill_type": "engineering",
        "estimated_time_saved": 60,
    }


# ═══════════════════════════════════════════════════════════════════
# Skill dataclass
# ═══════════════════════════════════════════════════════════════════


class TestSkill:
    def test_default_init(self):
        skill = Skill(name="test", description="desc")
        assert skill.tags == []
        assert skill.effectiveness_score == 0.5
        assert skill.created == ""
        assert skill.last_used == ""
        assert skill.steps == []
        assert skill.verification == []
        assert skill.usage_count == 0
        assert skill.skill_type == "general"
        assert skill.estimated_time_saved == 0

    def test_full_init(self, sample_skill):
        assert sample_skill.name == "test_skill"
        assert sample_skill.effectiveness_score == 0.75
        assert sample_skill.skill_type == "scientific"


# ═══════════════════════════════════════════════════════════════════
# SkillCurator initialization
# ═══════════════════════════════════════════════════════════════════


class TestSkillCuratorInit:
    def test_init_creates_dir(self, temp_skills_dir):
        c = SkillCurator(skills_dir=temp_skills_dir)
        assert Path(temp_skills_dir).exists()
        assert c.skills == {}

    def test_init_loads_yaml(self, temp_skills_dir, mock_yaml_data):
        yaml_content = """
name: yaml_skill
description: Loaded from YAML
tags: [yaml, test]
effectiveness_score: 0.8
created: '2026-05-01'
last_used: '2026-05-02'
steps:
  - action: test
verification: []
usage_count: 2
skill_type: engineering
estimated_time_saved: 60
"""
        Path(temp_skills_dir).mkdir(parents=True, exist_ok=True)
        (Path(temp_skills_dir) / "yaml_skill.yaml").write_text(yaml_content)

        with patch.object(SkillCurator, "_load_skills", return_value=None):
            c = SkillCurator(skills_dir=temp_skills_dir)
        c._load_skills()
        assert "yaml_skill" in c.skills
        assert c.skills["yaml_skill"].name == "yaml_skill"

    def test_init_load_failure(self, temp_skills_dir):
        Path(temp_skills_dir).mkdir(parents=True, exist_ok=True)
        # Create invalid yaml
        (Path(temp_skills_dir) / "bad.yaml").write_text("not: valid: yaml: [")

        with patch.object(SkillCurator, "_load_skills", return_value=None):
            c = SkillCurator(skills_dir=temp_skills_dir)
        # The bad yaml will cause a scanner error during _load_skills
        try:
            c._load_skills()
        except Exception:
            pass
        assert "bad" not in c.skills


# ═══════════════════════════════════════════════════════════════════
# after_task
# ═══════════════════════════════════════════════════════════════════


class TestAfterTask:
    def test_no_patterns(self, curator):
        result = curator.after_task("test task", {})
        assert result is None

    def test_not_reusable(self, curator):
        result = curator.after_task("test", {"steps": [{"action": "a"}]})
        assert result is None

    def test_creates_skill(self, curator):
        result = curator.after_task("test task", {
            "steps": [
                {"action": "analyze", "description": "step 1"},
                {"action": "design", "description": "step 2"},
                {"action": "implement", "description": "step 3"},
            ]
        })

        assert result is not None
        assert result.name == "test_task"
        assert result.skill_type == "general"
        assert "auto-created" in result.tags
        assert result.effectiveness_score >= 0.5

    def test_with_plugins(self, curator):
        result = curator.after_task("test", {
            "plugins_executed": [
                {"name": "plugin1", "display_name": "Plugin One"},
            ],
            "steps": [
                {"action": "a1"},
                {"action": "a2"},
                {"action": "a3"},
            ]
        })

        assert result is not None
        assert any("run_plugin" in str(s) for s in result.steps)

    def test_duplicate_skill_skipped(self, curator_with_skill):
        result = curator_with_skill.after_task("test_skill", {
            "steps": [
                {"action": "a1"}, {"action": "a2"}, {"action": "a3"},
            ]
        })
        assert result is None

    def test_with_actions_string(self, curator):
        result = curator.after_task("test", {
            "actions": ["action1", "action2", "action3"],
            "steps": [
                {"action": "s1"}, {"action": "s2"}, {"action": "s3"},
            ]
        })
        assert result is not None


# ═══════════════════════════════════════════════════════════════════
# _extract_patterns
# ═══════════════════════════════════════════════════════════════════


class TestExtractPatterns:
    def test_from_steps(self, curator):
        patterns = curator._extract_patterns("t", {"steps": [{"a": 1}, {"b": 2}]})
        assert len(patterns) == 2

    def test_from_actions(self, curator):
        patterns = curator._extract_patterns("t", {
            "actions": [
                {"action": "a1"},
                "string_action",
            ]
        })
        assert len(patterns) == 2
        assert patterns[1] == {"action": "string_action", "description": ""}

    def test_from_plugins(self, curator):
        patterns = curator._extract_patterns("t", {
            "plugins_executed": [{"name": "p1", "display_name": "P1"}]
        })
        assert len(patterns) == 1
        assert patterns[0]["action"] == "run_plugin"

    def test_empty(self, curator):
        assert curator._extract_patterns("t", {}) == []


# ═══════════════════════════════════════════════════════════════════
# _is_reusable
# ═══════════════════════════════════════════════════════════════════


class TestIsReusable:
    def test_too_few_patterns(self, curator):
        assert curator._is_reusable([{"action": "a"}, {"action": "b"}]) is False

    def test_single_unique_action(self, curator):
        assert curator._is_reusable([
            {"action": "a"}, {"action": "a"}, {"action": "a"},
        ]) is False

    def test_multiple_unique_actions(self, curator):
        assert curator._is_reusable([
            {"action": "a"}, {"action": "b"}, {"action": "c"},
        ]) is True

    def test_mixed_types(self, curator):
        assert curator._is_reusable([
            {"action": "a"}, {"action": "b"}, "string",
        ]) is True


# ═══════════════════════════════════════════════════════════════════
# _create_skill
# ═══════════════════════════════════════════════════════════════════


class TestCreateSkill:
    def test_basic(self, curator):
        skill = curator._create_skill(
            [{"action": "a1"}, {"action": "a2"}],
            "Test Task",
        )
        assert skill is not None
        assert skill.name == "test_task"
        assert skill.description == "Auto-generated from Test Task"

    def test_empty_context(self, curator):
        skill = curator._create_skill([{"action": "a"}], "")
        assert skill is not None
        assert skill.name.startswith("skill_")

    def test_long_context_truncated(self, curator):
        long_name = "a " * 100
        skill = curator._create_skill([{"action": "a"}], long_name)
        assert len(skill.name) <= 50

    def test_duplicate_returns_none(self, curator_with_skill):
        result = curator_with_skill._create_skill(
            [{"action": "a"}], "test_skill"
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# _extract_tags
# ═══════════════════════════════════════════════════════════════════


class TestExtractTags:
    def test_discovery(self, curator):
        assert "discovery" in curator._extract_tags("discover new hypothesis")

    def test_c4(self, curator):
        assert "c4" in curator._extract_tags("c4 cognitive analysis")

    def test_triz(self, curator):
        assert "triz" in curator._extract_tags("triz contradiction matrix")

    def test_validation(self, curator):
        assert "validation" in curator._extract_tags("validation and verify")

    def test_paradigm(self, curator):
        assert "paradigm-shift" in curator._extract_tags("paradigm shift analysis")

    def test_max_tags(self, curator):
        tags = curator._extract_tags("discover c4 triz validation paradigm")
        assert len(tags) <= 5

    def test_no_tags(self, curator):
        assert curator._extract_tags("generic task") == []


# ═══════════════════════════════════════════════════════════════════
# _classify_skill_type
# ═══════════════════════════════════════════════════════════════════


class TestClassifySkillType:
    def test_scientific(self, curator):
        assert curator._classify_skill_type("scientific research paper") == "scientific"
        assert curator._classify_skill_type("hypothesis generation") == "scientific"

    def test_engineering(self, curator):
        assert curator._classify_skill_type("engineering design build") == "engineering"
        assert curator._classify_skill_type("invent new tool") == "engineering"

    def test_strategic(self, curator):
        assert curator._classify_skill_type("strategic decision plan") == "strategic"

    def test_general(self, curator):
        assert curator._classify_skill_type("generic task") == "general"


# ═══════════════════════════════════════════════════════════════════
# _estimate_effectiveness
# ═══════════════════════════════════════════════════════════════════


class TestEstimateEffectiveness:
    def test_base_score(self, curator):
        skill = Skill(name="t", description="d")
        assert curator._estimate_effectiveness(skill) == 0.5

    def test_many_steps(self, curator):
        skill = Skill(name="t", description="d", steps=[{"a": i} for i in range(6)])
        assert curator._estimate_effectiveness(skill) >= 0.7

    def test_few_steps(self, curator):
        skill = Skill(name="t", description="d", steps=[{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}])
        assert curator._estimate_effectiveness(skill) >= 0.6

    def test_verification_tag(self, curator):
        skill = Skill(name="t", description="d", tags=["verification"])
        assert curator._estimate_effectiveness(skill) >= 0.7

    def test_specific_type(self, curator):
        skill = Skill(name="t", description="d", skill_type="scientific")
        assert curator._estimate_effectiveness(skill) >= 0.6

    def test_many_tags(self, curator):
        skill = Skill(name="t", description="d", tags=["a", "b", "c"])
        assert curator._estimate_effectiveness(skill) >= 0.6

    def test_max_score(self, curator):
        skill = Skill(
            name="t",
            description="d",
            steps=[{"a": i} for i in range(10)],
            tags=["verification", "a", "b", "c"],
            skill_type="scientific",
        )
        assert curator._estimate_effectiveness(skill) <= 1.0


# ═══════════════════════════════════════════════════════════════════
# _save_skill / rank_skills / load_skill
# ═══════════════════════════════════════════════════════════════════


class TestSaveAndLoad:
    def test_save_skill(self, curator, sample_skill):
        curator._save_skill(sample_skill)
        path = Path(curator.skills_dir) / "test_skill.yaml"
        assert path.exists()

    def test_load_skill(self, curator_with_skill):
        skill = curator_with_skill.load_skill("test_skill")
        assert skill is not None
        assert skill.name == "test_skill"

    def test_load_skill_missing(self, curator_with_skill):
        assert curator_with_skill.load_skill("missing") is None

    def test_rank_skills(self, curator_with_skill):
        curator_with_skill.skills["low"] = Skill(name="low", description="d", effectiveness_score=0.3)
        ranked = curator_with_skill.rank_skills()
        assert ranked[0].name == "test_skill"
        assert ranked[-1].name == "low"

    def test_rank_skills_with_query(self, curator_with_skill):
        curator_with_skill.skills["other"] = Skill(name="other", description="other desc", tags=["other"])
        ranked = curator_with_skill.rank_skills(query="test")
        assert len(ranked) == 1
        assert ranked[0].name == "test_skill"

    def test_rank_skills_by_tag(self, curator_with_skill):
        curator_with_skill.skills["tagged"] = Skill(
            name="tagged", description="d", tags=["test"], effectiveness_score=0.9
        )
        ranked = curator_with_skill.rank_skills(query="test")
        assert any(s.name == "tagged" for s in ranked)


# ═══════════════════════════════════════════════════════════════════
# apply_skill
# ═══════════════════════════════════════════════════════════════════


class TestApplySkill:
    def test_apply_existing_skill(self, curator_with_skill):
        context = {"key": "value"}
        result = curator_with_skill.apply_skill("test_skill", context)

        assert isinstance(result, SkillExecutionResult)
        assert result.success is True
        assert result.skill_name == "test_skill"
        assert "steps_applied" in result.output
        assert result.execution_time >= 0

    def test_apply_missing_skill(self, curator):
        result = curator.apply_skill("missing", {})
        assert result.success is False
        assert "not found" in result.error_message

    def test_apply_updates_usage(self, curator_with_skill):
        original_count = curator_with_skill.skills["test_skill"].usage_count
        curator_with_skill.apply_skill("test_skill", {})
        assert curator_with_skill.skills["test_skill"].usage_count == original_count + 1

    def test_apply_error(self, curator_with_skill):
        with patch.object(curator_with_skill, "_save_skill", side_effect=ConnectionError("fail")):
            result = curator_with_skill.apply_skill("test_skill", {})
            assert result.success is False
            assert "fail" in result.error_message


# ═══════════════════════════════════════════════════════════════════
# get_statistics
# ═══════════════════════════════════════════════════════════════════


class TestGetStatistics:
    def test_empty(self, curator):
        stats = curator.get_statistics()
        assert stats["total_skills"] == 0
        assert stats["avg_effectiveness"] == 0.0
        assert stats["total_usage"] == 0

    def test_with_skills(self, curator_with_skill):
        curator_with_skill.skills["s2"] = Skill(
            name="s2", description="d", skill_type="engineering", usage_count=3, effectiveness_score=0.6
        )
        stats = curator_with_skill.get_statistics()
        assert stats["total_skills"] == 2
        assert stats["avg_effectiveness"] == pytest.approx(0.675, abs=0.01)
        assert stats["total_usage"] == 8
        assert stats["by_type"]["scientific"] == 1
        assert stats["by_type"]["engineering"] == 1
        assert len(stats["top_skills"]) <= 5


# ═══════════════════════════════════════════════════════════════════
# SkillRegistry
# ═══════════════════════════════════════════════════════════════════


class TestSkillRegistry:
    def test_init(self, curator):
        registry = SkillRegistry(curator)
        assert registry.curator is curator

    def test_discover_skills(self, registry):
        skills = registry.discover_skills()
        assert isinstance(skills, list)

    def test_get_skill_details(self, registry, curator_with_skill):
        registry = SkillRegistry(curator_with_skill)
        details = registry.get_skill_details("test_skill")
        assert details is not None
        assert details["name"] == "test_skill"
        assert "steps" in details
        assert "verification" in details

    def test_get_skill_details_missing(self, registry):
        assert registry.get_skill_details("missing") is None

    def test_execute_skill(self, registry, curator_with_skill):
        registry = SkillRegistry(curator_with_skill)
        result = registry.execute_skill("test_skill", {})
        assert result["success"] is True
        assert result["skill_name"] == "test_skill"

    def test_execute_skill_error(self, registry):
        result = registry.execute_skill("missing", {})
        assert result["success"] is False
        assert result["error"] is not None

    def test_update_skill_usage(self, registry, curator_with_skill):
        registry = SkillRegistry(curator_with_skill)
        original = curator_with_skill.skills["test_skill"].usage_count
        registry.update_skill_usage("test_skill")
        assert curator_with_skill.skills["test_skill"].usage_count == original + 1

    def test_update_skill_usage_missing(self, registry):
        registry.update_skill_usage("missing")  # Should not raise

    def test_get_next_skill_for_task(self, registry, curator_with_skill):
        registry = SkillRegistry(curator_with_skill)
        skill_name = registry.get_next_skill_for_task("test_skill something")
        assert skill_name == "test_skill"

    def test_get_next_skill_no_match(self, registry):
        assert registry.get_next_skill_for_task("completely unrelated task") is None

    def test_get_next_skill_by_description(self, registry, curator_with_skill):
        registry = SkillRegistry(curator_with_skill)
        skill_name = registry.get_next_skill_for_task("A test skill for analysis")
        assert skill_name == "test_skill"


# ═══════════════════════════════════════════════════════════════════
# initialize_skill_system
# ═══════════════════════════════════════════════════════════════════


class TestInitializeSkillSystem:
    def test_returns_registry(self, temp_skills_dir):
        registry = initialize_skill_system(temp_skills_dir)
        assert isinstance(registry, SkillRegistry)
        assert isinstance(registry.curator, SkillCurator)


# ═══════════════════════════════════════════════════════════════════
# EXAMPLE_SKILL
# ═══════════════════════════════════════════════════════════════════


class TestExampleSkill:
    def test_is_string(self):
        assert isinstance(EXAMPLE_SKILL, str)
        assert "c4-discovery-bundle" in EXAMPLE_SKILL
        assert "discovery" in EXAMPLE_SKILL


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_skill_name_normalization(self, curator):
        skill = curator._create_skill([{"action": "a"}], "My-Task Name")
        assert skill is not None
        assert skill.name == "my_task_name"

    def test_skill_execution_result_defaults(self):
        result = SkillExecutionResult(skill_name="test", success=True)
        assert result.output == {}
        assert result.execution_time == 0.0
        assert result.error_message == ""

    def test_curator_load_skills_no_dir(self, tmp_path):
        dir_path = tmp_path / "nonexistent" / "skills"
        c = SkillCurator(skills_dir=str(dir_path))
        assert c.skills == {}

    def test_rank_skills_empty_after_filter(self, curator_with_skill):
        ranked = curator_with_skill.rank_skills(query="nonexistent_xyz")
        assert ranked == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
