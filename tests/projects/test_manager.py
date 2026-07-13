"""Tests for src/projects/manager.py - using in-memory SQLite."""

from __future__ import annotations

from typing import Any

import pytest

from projects.manager import (
    Milestone,
    ProjectManager,
    ProjectStatus,
    ResearchProject,
    Task,
    TaskStatus,
)


@pytest.fixture
def manager(tmp_path: Any) -> ProjectManager:
    db = tmp_path / "test_projects.db"
    return ProjectManager(str(db))


class TestProjectCRUD:
    def test_create_project(self, manager: ProjectManager) -> None:
        project = ResearchProject(
            id=None,
            name="Quantum Gravity",
            description="Unification of GR and QM",
            domain="physics",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
            objectives=["Derive equations", "Run simulations"],
            collaborators=["Alice", "Bob"],
            tags=["quantum", "gravity"],
        )
        pid = manager.create_project(project)
        assert isinstance(pid, int)
        assert pid > 0

    def test_get_project(self, manager: ProjectManager) -> None:
        project = ResearchProject(
            id=None,
            name="Test",
            description="D",
            domain="ai",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(project)
        fetched = manager.get_project(pid)
        assert fetched is not None
        assert fetched.name == "Test"
        assert fetched.domain == "ai"

    def test_get_project_missing(self, manager: ProjectManager) -> None:
        assert manager.get_project(9999) is None

    def test_list_projects(self, manager: ProjectManager) -> None:
        for i in range(3):
            p = ResearchProject(
                id=None,
                name=f"P{i}",
                description="D",
                domain="ai",
                status=ProjectStatus.ACTIVE.value,
                created_at="",
                updated_at="",
            )
            manager.create_project(p)
        projects = manager.list_projects()
        assert len(projects) == 3

    def test_list_projects_by_status(self, manager: ProjectManager) -> None:
        active = ResearchProject(
            id=None,
            name="A",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        completed = ResearchProject(
            id=None,
            name="C",
            description="D",
            domain="x",
            status=ProjectStatus.COMPLETED.value,
            created_at="",
            updated_at="",
        )
        manager.create_project(active)
        manager.create_project(completed)
        assert len(manager.list_projects(status="active")) == 1
        assert len(manager.list_projects(status="completed")) == 1

    def test_list_projects_by_domain(self, manager: ProjectManager) -> None:
        p1 = ResearchProject(
            id=None,
            name="A",
            description="D",
            domain="physics",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        p2 = ResearchProject(
            id=None,
            name="B",
            description="D",
            domain="ai",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        manager.create_project(p1)
        manager.create_project(p2)
        assert len(manager.list_projects(domain="physics")) == 1

    def test_update_project_status(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="X",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        manager.update_project_status(pid, "completed")
        fetched = manager.get_project(pid)
        assert fetched.status == "completed"

    def test_add_hypothesis_to_project(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="X",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        manager.add_hypothesis_to_project(pid, 101)
        manager.add_hypothesis_to_project(pid, 102)
        manager.add_hypothesis_to_project(pid, 101)  # duplicate
        fetched = manager.get_project(pid)
        assert 101 in fetched.hypotheses
        assert 102 in fetched.hypotheses
        assert len(fetched.hypotheses) == 2


class TestTaskOperations:
    def test_create_task(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        task = Task(
            id=None,
            project_id=pid,
            title="T1",
            description="Desc",
            status=TaskStatus.TODO.value,
            priority=3,
            due_date=None,
            created_at="",
            tags=["urgent"],
        )
        tid = manager.create_task(task)
        assert isinstance(tid, int)

    def test_get_project_tasks(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        for i in range(3):
            t = Task(
                id=None,
                project_id=pid,
                title=f"T{i}",
                description="D",
                status=TaskStatus.TODO.value,
                priority=i + 1,
                due_date=None,
                created_at="",
            )
            manager.create_task(t)
        tasks = manager.get_project_tasks(pid)
        assert len(tasks) == 3

    def test_get_project_tasks_by_status(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        t1 = Task(
            id=None,
            project_id=pid,
            title="T1",
            description="D",
            status=TaskStatus.TODO.value,
            priority=1,
            due_date=None,
            created_at="",
        )
        t2 = Task(
            id=None,
            project_id=pid,
            title="T2",
            description="D",
            status=TaskStatus.DONE.value,
            priority=1,
            due_date=None,
            created_at="",
        )
        manager.create_task(t1)
        manager.create_task(t2)
        assert len(manager.get_project_tasks(pid, status="todo")) == 1
        assert len(manager.get_project_tasks(pid, status="done")) == 1

    def test_complete_task(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        t = Task(
            id=None,
            project_id=pid,
            title="T",
            description="D",
            status=TaskStatus.IN_PROGRESS.value,
            priority=1,
            due_date=None,
            created_at="",
        )
        tid = manager.create_task(t)
        manager.complete_task(tid)
        tasks = manager.get_project_tasks(pid, status="done")
        assert len(tasks) == 1
        assert tasks[0].completed_at is not None


class TestMilestoneOperations:
    def test_create_milestone(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        ms = Milestone(
            id=None,
            project_id=pid,
            title="M1",
            description="D",
            target_date="2025-01-01",
            deliverables=["paper"],
        )
        mid = manager.create_milestone(ms)
        assert isinstance(mid, int)

    def test_get_project_milestones(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        for i in range(2):
            ms = Milestone(
                id=None,
                project_id=pid,
                title=f"M{i}",
                description="D",
                target_date=f"2025-0{i + 1}-01",
                deliverables=[],
            )
            manager.create_milestone(ms)
        milestones = manager.get_project_milestones(pid)
        assert len(milestones) == 2


class TestResearchLog:
    def test_add_log_entry(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        lid = manager.add_log_entry(pid, "observation", "Found correlation", tags=["key"])
        assert isinstance(lid, int)

    def test_get_research_log(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        manager.add_log_entry(pid, "observation", "O1")
        manager.add_log_entry(pid, "idea", "I1")
        manager.add_log_entry(pid, "observation", "O2")
        logs = manager.get_research_log(pid)
        assert len(logs) == 3
        obs = manager.get_research_log(pid, entry_type="observation")
        assert len(obs) == 2


class TestProjectStats:
    def test_get_project_stats(self, manager: ProjectManager) -> None:
        p = ResearchProject(
            id=None,
            name="P",
            description="D",
            domain="x",
            status=ProjectStatus.ACTIVE.value,
            created_at="",
            updated_at="",
        )
        pid = manager.create_project(p)
        for i in range(3):
            t = Task(
                id=None,
                project_id=pid,
                title=f"T{i}",
                description="D",
                status=TaskStatus.TODO.value,
                priority=1,
                due_date=None,
                created_at="",
            )
            manager.create_task(t)
        manager.complete_task(1)  # first task
        ms = Milestone(
            id=None,
            project_id=pid,
            title="M",
            description="D",
            target_date="2025-01-01",
            deliverables=[],
        )
        manager.create_milestone(ms)
        manager.add_log_entry(pid, "observation", "O")

        stats = manager.get_project_stats(pid)
        assert stats["total_tasks"] == 3
        assert stats["total_milestones"] == 1
        assert stats["log_entries"] == 1
        assert "tasks" in stats
        assert "completed_milestones" in stats
