"""
C4REQBER: Research Project Manager
Manage research projects, milestones, and tasks
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ProjectStatus(Enum):
    """ProjectStatus."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class TaskStatus(Enum):
    """TaskStatus."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Task."""
    id: int | None
    project_id: int
    title: str
    description: str
    status: str
    priority: int  # 1-5
    due_date: str | None
    created_at: str
    completed_at: str | None = None
    tags: list[str] = None  # type: ignore[assignment]


@dataclass
class Milestone:
    """Milestone."""
    id: int | None
    project_id: int
    title: str
    description: str
    target_date: str
    completed_date: str | None = None
    deliverables: list[str] = None  # type: ignore[assignment]


@dataclass
class ResearchProject:
    """ResearchProject."""
    id: int | None
    name: str
    description: str
    domain: str
    status: str
    created_at: str
    updated_at: str
    start_date: str | None = None
    end_date: str | None = None
    objectives: list[str] = None  # type: ignore[assignment]
    hypotheses: list[int] = None  # type: ignore  # Discovery IDs
    collaborators: list[str] = None  # type: ignore[assignment]
    tags: list[str] = None  # type: ignore[assignment]
    notes: str = ""


class ProjectManager:
    """
    Manage research projects with tasks, milestones, and timeline.
    """

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "projects.db"  # type: ignore[assignment]

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize project database."""
        with sqlite3.connect(self.db_path) as conn:
            # Projects table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    domain TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    objectives TEXT,  -- JSON
                    hypotheses TEXT,  -- JSON array
                    collaborators TEXT,  -- JSON
                    tags TEXT,  -- JSON
                    notes TEXT
                )
            """)

            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'todo',
                    priority INTEGER DEFAULT 3,
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    tags TEXT,  -- JSON
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # Milestones table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_date TEXT,
                    completed_date TEXT,
                    deliverables TEXT,  -- JSON
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # Research log / journal
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    date TEXT NOT NULL,
                    entry_type TEXT,  -- 'observation', 'idea', 'result', 'problem'
                    content TEXT NOT NULL,
                    tags TEXT,
                    related_discoveries TEXT  -- JSON
                )
            """)

            conn.commit()

    # Project operations
    def create_project(self, project: ResearchProject) -> int:
        """Create new research project."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            cursor = conn.execute(
                """INSERT INTO projects
                   (name, description, domain, status, created_at, updated_at,
                    start_date, end_date, objectives, hypotheses, collaborators, tags, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project.name,
                    project.description,
                    project.domain,
                    project.status,
                    now,
                    now,
                    project.start_date,
                    project.end_date,
                    json.dumps(project.objectives) if project.objectives else None,
                    json.dumps(project.hypotheses) if project.hypotheses else None,
                    json.dumps(project.collaborators)
                    if project.collaborators
                    else None,
                    json.dumps(project.tags) if project.tags else None,
                    project.notes,
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_project(self, project_id: int) -> ResearchProject | None:
        """Get project by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return self._row_to_project(row) if row else None

    def list_projects(
        self, status: str | None = None, domain: str | None = None
    ) -> list[ResearchProject]:
        """List projects with filters."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM projects WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            query += " ORDER BY updated_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_project(row) for row in rows]

    def update_project_status(self, project_id: int, status: str) -> None:
        """Update project status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE projects
                   SET status = ?, updated_at = ?
                   WHERE id = ?""",
                (status, datetime.now().isoformat(), project_id),
            )
            conn.commit()

    def add_hypothesis_to_project(self, project_id: int, discovery_id: int) -> None:
        """Link a discovery/hypothesis to project."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT hypotheses FROM projects WHERE id = ?", (project_id,)
            )
            row = cursor.fetchone()

            if row and row[0]:
                hypotheses = json.loads(row[0])
            else:
                hypotheses = []

            if discovery_id not in hypotheses:
                hypotheses.append(discovery_id)

            conn.execute(
                "UPDATE projects SET hypotheses = ?, updated_at = ? WHERE id = ?",
                (json.dumps(hypotheses), datetime.now().isoformat(), project_id),
            )
            conn.commit()

    # Task operations
    def create_task(self, task: Task) -> int:
        """Create task in project."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO tasks
                   (project_id, title, description, status, priority, due_date, created_at, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.project_id,
                    task.title,
                    task.description,
                    task.status,
                    task.priority,
                    task.due_date,
                    datetime.now().isoformat(),
                    json.dumps(task.tags) if task.tags else None,
                ),
            )
            conn.commit()

            # Update project timestamp
            conn.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), task.project_id),
            )
            conn.commit()

            return cursor.lastrowid  # type: ignore[return-value]

    def get_project_tasks(
        self, project_id: int, status: str | None = None
    ) -> list[Task]:
        """Get tasks for project."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM tasks WHERE project_id = ?"
            params = [project_id]

            if status:
                query += " AND status = ?"
                params.append(status)  # type: ignore[arg-type]

            query += " ORDER BY priority DESC, due_date ASC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]

    def complete_task(self, task_id: int) -> None:
        """Mark task as completed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE tasks
                   SET status = 'done', completed_at = ?
                   WHERE id = ?""",
                (datetime.now().isoformat(), task_id),
            )
            conn.commit()

    # Milestone operations
    def create_milestone(self, milestone: Milestone) -> int:
        """Create project milestone."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO milestones
                   (project_id, title, description, target_date, deliverables)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    milestone.project_id,
                    milestone.title,
                    milestone.description,
                    milestone.target_date,
                    json.dumps(milestone.deliverables)
                    if milestone.deliverables
                    else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_project_milestones(self, project_id: int) -> list[Milestone]:
        """Get milestones for project."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT * FROM milestones
                   WHERE project_id = ?
                   ORDER BY target_date ASC""",
                (project_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_milestone(row) for row in rows]

    # Research log
    def add_log_entry(
        self,
        project_id: int,
        entry_type: str,
        content: str,
        tags: list[str] | None = None,
        related_discoveries: list[int] | None = None,
    ) -> int:
        """Add entry to research log."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO research_log
                   (project_id, date, entry_type, content, tags, related_discoveries)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    project_id,
                    datetime.now().isoformat(),
                    entry_type,
                    content,
                    json.dumps(tags) if tags else None,
                    json.dumps(related_discoveries) if related_discoveries else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_research_log(
        self, project_id: int, entry_type: str | None = None
    ) -> list[dict]:  # type: ignore[type-arg]
        """Get research log entries."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM research_log WHERE project_id = ?"
            params = [project_id]

            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)  # type: ignore[arg-type]

            query += " ORDER BY date DESC"

            cursor = conn.execute(query, params)
            return [self._row_to_log_entry(row) for row in cursor.fetchall()]

    # Statistics
    def get_project_stats(self, project_id: int) -> dict[str, Any]:
        """Get project statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # Task counts
            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM tasks WHERE project_id = ? GROUP BY status",
                (project_id,),
            )
            stats["tasks"] = {row[0]: row[1] for row in cursor.fetchall()}

            # Total tasks
            cursor = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ?", (project_id,)
            )
            stats["total_tasks"] = cursor.fetchone()[0]

            # Completed milestones
            cursor = conn.execute(
                """SELECT COUNT(*) FROM milestones
                   WHERE project_id = ? AND completed_date IS NOT NULL""",
                (project_id,),
            )
            stats["completed_milestones"] = cursor.fetchone()[0]

            # Total milestones
            cursor = conn.execute(
                "SELECT COUNT(*) FROM milestones WHERE project_id = ?", (project_id,)
            )
            stats["total_milestones"] = cursor.fetchone()[0]

            # Log entries
            cursor = conn.execute(
                "SELECT COUNT(*) FROM research_log WHERE project_id = ?", (project_id,)
            )
            stats["log_entries"] = cursor.fetchone()[0]

            return stats

    # Helper methods
    def _row_to_project(self, row: Any) -> ResearchProject:
        return ResearchProject(
            id=row[0],
            name=row[1],
            description=row[2],
            domain=row[3],
            status=row[4],
            created_at=row[5],
            updated_at=row[6],
            start_date=row[7],
            end_date=row[8],
            objectives=json.loads(row[9]) if row[9] else [],
            hypotheses=json.loads(row[10]) if row[10] else [],
            collaborators=json.loads(row[11]) if row[11] else [],
            tags=json.loads(row[12]) if row[12] else [],
            notes=row[13] if row[13] else "",
        )

    def _row_to_task(self, row: Any) -> Task:
        return Task(
            id=row[0],
            project_id=row[1],
            title=row[2],
            description=row[3],
            status=row[4],
            priority=row[5],
            due_date=row[6],
            created_at=row[7],
            completed_at=row[8],
            tags=json.loads(row[9]) if row[9] else [],
        )

    def _row_to_milestone(self, row: Any) -> Milestone:
        return Milestone(
            id=row[0],
            project_id=row[1],
            title=row[2],
            description=row[3],
            target_date=row[4],
            completed_date=row[5],
            deliverables=json.loads(row[6]) if row[6] else [],
        )

    def _row_to_log_entry(self, row: Any) -> dict[str, Any]:
        return {
            "id": row[0],
            "project_id": row[1],
            "date": row[2],
            "entry_type": row[3],
            "content": row[4],
            "tags": json.loads(row[5]) if row[5] else [],
            "related_discoveries": json.loads(row[6]) if row[6] else [],
        }
