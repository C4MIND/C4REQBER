"""
TURBO-CDI v8 — Discovery Lab

Systematic scientific discovery through cognitive transformations.
Implements the C4 Framework's 6-phase discovery methodology.

Phases:
1. Corpus Setup - Define bounded knowledge space
2. Anomaly Mining - Find contradictions in corpus
3. Presupposition Analysis - Extract and invert hidden assumptions
4. Transformation Lab - Apply Û operators systematically
5. Isomorphism Bridge - Find cross-domain structural mappings
6. Synthesis Engine - Combine insights into new theory
"""

import os
import json
import uuid
import logging
import asyncio
import weakref
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal, Any, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum

import aiosqlite
from pydantic import BaseModel, Field

# TURBO-CDI v8 imports
from .llm_adapter import llm_call
from .operators import apply_transformation

logger = logging.getLogger("discovery_lab")

# Track fire-and-forget background tasks to prevent GC
_active_tasks: weakref.WeakSet = weakref.WeakSet()


def _fire_and_forget(coro) -> asyncio.Task:
    """Create a background task and track it to prevent GC."""
    task = asyncio.create_task(coro)
    _active_tasks.add(task)
    task.add_done_callback(lambda t: _active_tasks.discard(t))
    return task


# ============================================================================
# DATABASE PATH
# ============================================================================

DEFAULT_DB_PATH = Path.home() / ".turbo-cdi" / "discovery.db"

# ============================================================================
# BACKGROUND JOB TRACKING — PERSISTENT
# ============================================================================

# Legacy in-memory store (deprecated, use DiscoveryJobStore)
_corpus_jobs: dict[str, dict] = {}


class JobStatus(BaseModel):
    """Status of background job"""

    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = 0
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class Fact(BaseModel):
    """A known fact in the knowledge corpus"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    statement: str
    source: Optional[str] = None
    year: Optional[int] = None
    domain: Optional[str] = None
    c4_state: Optional[str] = None  # "002" etc.


class Theory(BaseModel):
    """A theory in the knowledge corpus"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    principles: list[str] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)
    domain: Optional[str] = None


class KnowledgeCorpus(BaseModel):
    """A bounded knowledge corpus for discovery"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    domain: str
    epoch_end: str  # "1902", "1920", etc.
    subdomains: list[str] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    theories: list[Theory] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: Optional[str] = None
    project_id: Optional[str] = None


class Anomaly(BaseModel):
    """A contradiction or unexplained phenomenon"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    corpus_id: str
    type: Literal["empirical", "theoretical", "predictive", "unexplained"]
    fact_statement: str
    theory_name: str
    conflict_description: str
    criticality: Literal["low", "medium", "high", "critical"]
    c4_state: Optional[str] = None
    resolved: bool = False


class Presupposition(BaseModel):
    """A hidden assumption in a theory"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    theory_id: str
    theory_name: str
    statement: str
    type: Literal["ontological", "epistemological", "methodological", "metaphysical"]
    status: Literal["accepted", "questioned", "inverted"] = "accepted"
    inverted_statement: Optional[str] = None
    implications: list[str] = Field(default_factory=list)


class CognitiveState(BaseModel):
    """A knowledge state in F⟨T,D,A⟩ space"""

    knowledge: str
    t: int = Field(ge=0, le=2)
    d: int = Field(ge=0, le=2)
    a: int = Field(ge=0, le=2)
    justification: Optional[str] = None

    @property
    def code(self) -> str:
        return f"{self.t}{self.d}{self.a}"

    @property
    def archetype(self) -> str:
        # C4_ARCHETYPES not available in v8, return basic mapping
        archetypes = {
            "000": "Observer",
            "001": "Explorer",
            "002": "Builder",
            "010": "Theorist",
            "011": "Connector",
            "012": "Integrator",
            "020": "Metacognitive",
            "021": "Systems Thinker",
            "022": "Synthesizer",
            "100": "Historian",
            "101": "Analyst",
            "102": "Strategist",
            "110": "Philosopher",
            "111": "Researcher",
            "112": "Designer",
            "120": "Meta-Researcher",
            "121": "Architect",
            "122": "Visionary",
            "200": "Futurist",
            "201": "Innovator",
            "202": "Pioneer",
            "210": "Speculator",
            "211": "Inventor",
            "212": "Creator",
            "220": "Meta-Creator",
            "221": "Founder",
            "222": "Transcender",
        }
        return archetypes.get(self.code, "Unknown")


class Transformation(BaseModel):
    """A single operator application"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_state: CognitiveState
    to_state: CognitiveState
    operator: str  # "U_T+", "U_D+", etc.
    justification: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Trajectory(BaseModel):
    """A sequence of transformations"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    corpus_id: str
    start_state: CognitiveState
    current_state: CognitiveState
    transformations: list[Transformation] = Field(default_factory=list)
    goal_state: Optional[CognitiveState] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DomainMapping(BaseModel):
    """Structural isomorphism between domains"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_domain: str
    target_domain: str
    mappings: list[tuple[str, str]]  # [(source_concept, target_concept), ...]
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SynthesizedTheory(BaseModel):
    """A theory synthesized from discovery components"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    corpus_id: str
    name: str
    postulates: list[str]
    consequences: list[str]
    equations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    corpus_compatibility: float = Field(ge=0.0, le=1.0)
    predictions: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CreateCorpusRequest(BaseModel):
    name: str
    domain: str
    epoch_end: str
    subdomains: list[str] = Field(default_factory=list)
    auto_populate: bool = False
    project_id: Optional[str] = None


class AddFactRequest(BaseModel):
    statement: str
    source: Optional[str] = None
    year: Optional[int] = None


class AddTheoryRequest(BaseModel):
    name: str
    principles: list[str] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)


class DetectAnomaliesRequest(BaseModel):
    corpus_id: str


class ExtractPresuppositionsRequest(BaseModel):
    theory_id: str
    corpus_id: str


class InvertPresuppositionRequest(BaseModel):
    presupposition_id: str


class TransformRequest(BaseModel):
    corpus_id: str
    state: CognitiveState
    operator: Literal["U_T+", "U_T-", "U_D+", "U_D-", "U_A+", "U_A-"]


class FindPathRequest(BaseModel):
    corpus_id: str
    start_state: CognitiveState
    goal_state: CognitiveState


class DetectIsomorphismRequest(BaseModel):
    corpus_id: str
    source_domain: str
    target_domain: str
    context: Optional[str] = None


class ApplyIsomorphismRequest(BaseModel):
    mapping_id: str
    knowledge: str


class SynthesizeRequest(BaseModel):
    corpus_id: str
    inverted_presuppositions: list[str] = Field(default_factory=list)  # IDs
    trajectory_id: Optional[str] = None
    isomorphism_ids: list[str] = Field(default_factory=list)
    anomaly_ids: list[str] = Field(default_factory=list)


# ============================================================================
# DISCOVERY STORE (SQLite)
# ============================================================================


class DiscoveryStore:
    """Async SQLite storage for Discovery Lab"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._initialized = False

    async def initialize(self):
        """Initialize database and create tables"""
        if self._initialized:
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA busy_timeout=5000")

            # Corpus table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS corpus (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    epoch_end TEXT NOT NULL,
                    subdomains TEXT NOT NULL,
                    facts TEXT NOT NULL,
                    theories TEXT NOT NULL,
                    constraints TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    user_id TEXT,
                    project_id TEXT
                )
            """)

            # Anomalies table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id TEXT PRIMARY KEY,
                    corpus_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    fact_statement TEXT NOT NULL,
                    theory_name TEXT NOT NULL,
                    conflict_description TEXT NOT NULL,
                    criticality TEXT NOT NULL,
                    c4_state TEXT,
                    resolved INTEGER DEFAULT 0,
                    FOREIGN KEY (corpus_id) REFERENCES corpus(id)
                )
            """)

            # Presuppositions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS presuppositions (
                    id TEXT PRIMARY KEY,
                    theory_id TEXT NOT NULL,
                    theory_name TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'accepted',
                    inverted_statement TEXT,
                    implications TEXT
                )
            """)

            # Trajectories table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trajectories (
                    id TEXT PRIMARY KEY,
                    corpus_id TEXT NOT NULL,
                    start_state TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    transformations TEXT NOT NULL,
                    goal_state TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (corpus_id) REFERENCES corpus(id)
                )
            """)

            # Isomorphisms table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS isomorphisms (
                    id TEXT PRIMARY KEY,
                    corpus_id TEXT,
                    source_domain TEXT NOT NULL,
                    target_domain TEXT NOT NULL,
                    mappings TEXT NOT NULL,
                    confidence REAL,
                    justification TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Synthesized theories table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS synthesized_theories (
                    id TEXT PRIMARY KEY,
                    corpus_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    postulates TEXT NOT NULL,
                    consequences TEXT NOT NULL,
                    equations TEXT,
                    confidence REAL,
                    corpus_compatibility REAL,
                    predictions TEXT,
                    unresolved TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (corpus_id) REFERENCES corpus(id)
                )
            """)

            await db.execute("CREATE INDEX IF NOT EXISTS idx_corpus_user ON corpus(user_id)")
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_anomalies_corpus ON anomalies(corpus_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_trajectories_corpus ON trajectories(corpus_id)"
            )

            # Background jobs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS discovery_jobs (
                    job_id TEXT PRIMARY KEY,
                    corpus_id TEXT NOT NULL,
                    user_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    error TEXT,
                    result TEXT,
                    attempt_count INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    failed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_corpus ON discovery_jobs(corpus_id)"
            )
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_user ON discovery_jobs(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON discovery_jobs(status)")

            # Migration: add project_id if missing
            try:
                await db.execute("ALTER TABLE corpus ADD COLUMN project_id TEXT")
                logger.info("Migration: Added project_id column to corpus table")
            except Exception:
                pass

            # Migration: add attempt_count and max_attempts to discovery_jobs if missing
            try:
                await db.execute(
                    "ALTER TABLE discovery_jobs ADD COLUMN attempt_count INTEGER DEFAULT 0"
                )
                logger.info("Migration: Added attempt_count column to discovery_jobs table")
            except Exception:
                pass

            try:
                await db.execute(
                    "ALTER TABLE discovery_jobs ADD COLUMN max_attempts INTEGER DEFAULT 3"
                )
                logger.info("Migration: Added max_attempts column to discovery_jobs table")
            except Exception:
                pass

            await db.execute("CREATE INDEX IF NOT EXISTS idx_corpus_project ON corpus(project_id)")

            await db.commit()

        self._initialized = True
        logger.info(f"Discovery store initialized: {self.db_path}")

    # --- Corpus CRUD ---

    async def create_corpus(self, corpus: KnowledgeCorpus) -> KnowledgeCorpus:
        """Create a new knowledge corpus"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO corpus (id, name, domain, epoch_end, subdomains, facts, theories, constraints, created_at, user_id, project_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    corpus.id,
                    corpus.name,
                    corpus.domain,
                    corpus.epoch_end,
                    json.dumps(corpus.subdomains),
                    json.dumps([f.model_dump() for f in corpus.facts]),
                    json.dumps([t.model_dump() for t in corpus.theories]),
                    json.dumps(corpus.constraints),
                    corpus.created_at,
                    corpus.user_id,
                    corpus.project_id,
                ),
            )
            await db.commit()
        return corpus

    async def get_corpus(self, corpus_id: str) -> Optional[KnowledgeCorpus]:
        """Get corpus by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM corpus WHERE id = ?", (corpus_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return KnowledgeCorpus(
                    id=row["id"],
                    name=row["name"],
                    domain=row["domain"],
                    epoch_end=row["epoch_end"],
                    subdomains=json.loads(row["subdomains"]),
                    facts=[Fact(**f) for f in json.loads(row["facts"])],
                    theories=[Theory(**t) for t in json.loads(row["theories"])],
                    constraints=json.loads(row["constraints"]),
                    created_at=row["created_at"],
                    user_id=row["user_id"],
                    project_id=row["project_id"],
                )

    async def update_corpus(self, corpus: KnowledgeCorpus) -> KnowledgeCorpus:
        """Update corpus facts and theories"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE corpus SET facts = ?, theories = ?, constraints = ?
                WHERE id = ?
            """,
                (
                    json.dumps([f.model_dump() for f in corpus.facts]),
                    json.dumps([t.model_dump() for t in corpus.theories]),
                    json.dumps(corpus.constraints),
                    corpus.id,
                ),
            )
            await db.commit()
        return corpus

    async def list_corpus(
        self, user_id: Optional[str] = None, project_id: Optional[str] = None
    ) -> list[KnowledgeCorpus]:
        """List corpus filtered by user and/or project"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            conditions = []
            params = []

            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)

            if conditions:
                query = f"SELECT * FROM corpus WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
            else:
                query = "SELECT * FROM corpus ORDER BY created_at DESC LIMIT 20"

            async with db.execute(query, tuple(params)) as cursor:
                rows = await cursor.fetchall()
                return [
                    KnowledgeCorpus(
                        id=row["id"],
                        name=row["name"],
                        domain=row["domain"],
                        epoch_end=row["epoch_end"],
                        subdomains=json.loads(row["subdomains"]),
                        facts=[Fact(**f) for f in json.loads(row["facts"])],
                        theories=[Theory(**t) for t in json.loads(row["theories"])],
                        constraints=json.loads(row["constraints"]),
                        created_at=row["created_at"],
                        user_id=row["user_id"],
                        project_id=row["project_id"],
                    )
                    for row in rows
                ]

    # --- Anomalies CRUD ---

    async def save_anomaly(self, anomaly: Anomaly) -> Anomaly:
        """Save an anomaly"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO anomalies (id, corpus_id, type, fact_statement, theory_name, conflict_description, criticality, c4_state, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    anomaly.id,
                    anomaly.corpus_id,
                    anomaly.type,
                    anomaly.fact_statement,
                    anomaly.theory_name,
                    anomaly.conflict_description,
                    anomaly.criticality,
                    anomaly.c4_state,
                    1 if anomaly.resolved else 0,
                ),
            )
            await db.commit()
        return anomaly

    async def get_anomalies(self, corpus_id: str) -> list[Anomaly]:
        """Get all anomalies for corpus"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM anomalies WHERE corpus_id = ?", (corpus_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Anomaly(
                        id=row["id"],
                        corpus_id=row["corpus_id"],
                        type=row["type"],
                        fact_statement=row["fact_statement"],
                        theory_name=row["theory_name"],
                        conflict_description=row["conflict_description"],
                        criticality=row["criticality"],
                        c4_state=row["c4_state"],
                        resolved=bool(row["resolved"]),
                    )
                    for row in rows
                ]

    # --- Presuppositions CRUD ---

    async def save_presupposition(self, presup: Presupposition) -> Presupposition:
        """Save a presupposition"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO presuppositions (id, theory_id, theory_name, statement, type, status, inverted_statement, implications)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    presup.id,
                    presup.theory_id,
                    presup.theory_name,
                    presup.statement,
                    presup.type,
                    presup.status,
                    presup.inverted_statement,
                    json.dumps(presup.implications),
                ),
            )
            await db.commit()
        return presup

    async def get_presupposition(self, presup_id: str) -> Optional[Presupposition]:
        """Get presupposition by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM presuppositions WHERE id = ?", (presup_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return Presupposition(
                    id=row["id"],
                    theory_id=row["theory_id"],
                    theory_name=row["theory_name"],
                    statement=row["statement"],
                    type=row["type"],
                    status=row["status"],
                    inverted_statement=row["inverted_statement"],
                    implications=json.loads(row["implications"]) if row["implications"] else [],
                )

    async def get_presuppositions_for_theory(self, theory_id: str) -> list[Presupposition]:
        """Get all presuppositions for a theory"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM presuppositions WHERE theory_id = ?", (theory_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Presupposition(
                        id=row["id"],
                        theory_id=row["theory_id"],
                        theory_name=row["theory_name"],
                        statement=row["statement"],
                        type=row["type"],
                        status=row["status"],
                        inverted_statement=row["inverted_statement"],
                        implications=json.loads(row["implications"]) if row["implications"] else [],
                    )
                    for row in rows
                ]

    # --- Trajectories CRUD ---

    async def save_trajectory(self, traj: Trajectory) -> Trajectory:
        """Save a trajectory"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO trajectories (id, corpus_id, start_state, current_state, transformations, goal_state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    traj.id,
                    traj.corpus_id,
                    traj.start_state.model_dump_json(),
                    traj.current_state.model_dump_json(),
                    json.dumps([t.model_dump() for t in traj.transformations]),
                    traj.goal_state.model_dump_json() if traj.goal_state else None,
                    traj.created_at,
                ),
            )
            await db.commit()
        return traj

    async def get_trajectory(self, traj_id: str) -> Optional[Trajectory]:
        """Get trajectory by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM trajectories WHERE id = ?", (traj_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return Trajectory(
                    id=row["id"],
                    corpus_id=row["corpus_id"],
                    start_state=CognitiveState.model_validate_json(row["start_state"]),
                    current_state=CognitiveState.model_validate_json(row["current_state"]),
                    transformations=[
                        Transformation(**t) for t in json.loads(row["transformations"])
                    ],
                    goal_state=CognitiveState.model_validate_json(row["goal_state"])
                    if row["goal_state"]
                    else None,
                    created_at=row["created_at"],
                )

    # --- Isomorphisms CRUD ---

    async def save_isomorphism(self, iso: DomainMapping) -> DomainMapping:
        """Save an isomorphism"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO isomorphisms (id, corpus_id, source_domain, target_domain, mappings, confidence, justification, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    iso.id,
                    None,
                    iso.source_domain,
                    iso.target_domain,
                    json.dumps(iso.mappings),
                    iso.confidence,
                    iso.justification,
                    iso.created_at,
                ),
            )
            await db.commit()
        return iso

    async def get_isomorphism(self, iso_id: str) -> Optional[DomainMapping]:
        """Get isomorphism by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM isomorphisms WHERE id = ?", (iso_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return DomainMapping(
                    id=row["id"],
                    source_domain=row["source_domain"],
                    target_domain=row["target_domain"],
                    mappings=json.loads(row["mappings"]),
                    confidence=row["confidence"],
                    justification=row["justification"],
                    created_at=row["created_at"],
                )

    # --- Synthesized theories CRUD ---

    async def save_theory(self, theory: SynthesizedTheory) -> SynthesizedTheory:
        """Save a synthesized theory"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO synthesized_theories (id, corpus_id, name, postulates, consequences, equations, confidence, corpus_compatibility, predictions, unresolved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    theory.id,
                    theory.corpus_id,
                    theory.name,
                    json.dumps(theory.postulates),
                    json.dumps(theory.consequences),
                    json.dumps(theory.equations),
                    theory.confidence,
                    theory.corpus_compatibility,
                    json.dumps(theory.predictions),
                    json.dumps(theory.unresolved),
                    theory.created_at,
                ),
            )
            await db.commit()
        return theory


# ============================================================================
# PERSISTENT JOB STORE
# ============================================================================


class DiscoveryJobStore:
    """Persistent storage for background jobs using SQLite"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH

    async def create_job(self, job_id: str, corpus_id: str, user_id: Optional[str] = None) -> dict:
        """Create new job record"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO discovery_jobs (job_id, corpus_id, user_id, status, progress)
                VALUES (?, ?, ?, 'pending', 0)
            """,
                (job_id, corpus_id, user_id),
            )
            await db.commit()

        return {
            "job_id": job_id,
            "corpus_id": corpus_id,
            "status": "pending",
            "progress": 0,
            "error": None,
        }

    async def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        error: Optional[str] = None,
        result: Optional[dict] = None,
    ) -> dict:
        """Update job status and progress"""
        updates = ["updated_at = CURRENT_TIMESTAMP"]
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == "completed":
                updates.append("completed_at = CURRENT_TIMESTAMP")
            elif status == "failed":
                updates.append("failed_at = CURRENT_TIMESTAMP")

        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)

        if error is not None:
            updates.append("error = ?")
            params.append(error)

        if result is not None:
            updates.append("result = ?")
            params.append(json.dumps(result))

        params.append(job_id)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"""
                UPDATE discovery_jobs 
                SET {", ".join(updates)}
                WHERE job_id = ?
            """,
                tuple(params),
            )
            await db.commit()

        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> Optional[dict]:
        """Get job by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM discovery_jobs WHERE job_id = ?", (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                return {
                    "job_id": row["job_id"],
                    "corpus_id": row["corpus_id"],
                    "user_id": row["user_id"],
                    "status": row["status"],
                    "progress": row["progress"],
                    "error": row["error"],
                    "result": json.loads(row["result"]) if row["result"] else None,
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    "failed_at": row["failed_at"],
                    "updated_at": row["updated_at"],
                }

    async def get_corpus_job(self, corpus_id: str) -> Optional[dict]:
        """Get most recent job for corpus"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM discovery_jobs 
                   WHERE corpus_id = ? 
                   ORDER BY started_at DESC LIMIT 1""",
                (corpus_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                return {
                    "job_id": row["job_id"],
                    "status": row["status"],
                    "progress": row["progress"],
                    "error": row["error"],
                    "result": json.loads(row["result"]) if row["result"] else None,
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                }

    async def get_user_jobs(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get recent jobs for user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM discovery_jobs 
                   WHERE user_id = ? 
                   ORDER BY started_at DESC LIMIT ?""",
                (user_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "job_id": r["job_id"],
                        "corpus_id": r["corpus_id"],
                        "status": r["status"],
                        "progress": r["progress"],
                        "started_at": r["started_at"],
                        "completed_at": r["completed_at"],
                    }
                    for r in rows
                ]

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Delete completed/failed jobs older than N days"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                DELETE FROM discovery_jobs 
                WHERE status IN ('completed', 'failed')
                AND updated_at < datetime('now', '-' || ? || ' days')
            """,
                (days,),
            )
            await db.commit()
            return cursor.rowcount

    async def increment_attempt(self, job_id: str) -> dict:
        """Increment attempt counter for retry logic"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE discovery_jobs 
                SET attempt_count = attempt_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """,
                (job_id,),
            )
            await db.commit()
        return await self.get_job(job_id)

    async def can_retry(self, job_id: str) -> bool:
        """Check if job can be retried"""
        job = await self.get_job(job_id)
        if not job:
            return False
        return job["status"] == "failed" and job.get("attempt_count", 0) < job.get(
            "max_attempts", 3
        )

    async def reset_for_retry(self, job_id: str) -> dict:
        """Reset job for retry attempt"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE discovery_jobs 
                SET status = 'pending',
                    progress = 0,
                    error = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """,
                (job_id,),
            )
            await db.commit()
        return await self.get_job(job_id)

    async def get_failed_jobs_needing_retry(self) -> list[dict]:
        """Get all failed jobs that haven't exceeded max attempts"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM discovery_jobs 
                WHERE status = 'failed'
                AND attempt_count < max_attempts
                ORDER BY failed_at ASC
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "job_id": r["job_id"],
                        "corpus_id": r["corpus_id"],
                        "user_id": r["user_id"],
                        "attempt_count": r["attempt_count"],
                        "max_attempts": r["max_attempts"],
                        "error": r["error"],
                        "failed_at": r["failed_at"],
                    }
                    for r in rows
                ]


_job_store: Optional[DiscoveryJobStore] = None


async def get_job_store() -> DiscoveryJobStore:
    """Get or create the global job store"""
    global _job_store
    if _job_store is None:
        _job_store = DiscoveryJobStore()
    return _job_store


# ============================================================================
# GLOBAL STORE INSTANCE
# ============================================================================

_store: Optional[DiscoveryStore] = None


async def get_discovery_store() -> DiscoveryStore:
    """Get or create the global discovery store"""
    global _store
    if _store is None:
        _store = DiscoveryStore()
        await _store.initialize()
    return _store


# ============================================================================
# LLM PROMPTS FOR DISCOVERY
# ============================================================================

CORPUS_AUTO_POPULATE_PROMPT = """You are a historian of science. Given a domain and epoch, list the key facts, experiments, and theories that were known.

Domain: {domain}
Subdomains: {subdomains}
Epoch: Before {epoch_end}

List:
1. Key FACTS (observations, experimental results) - up to 10
2. Key THEORIES (principles, laws, equations) - up to 5

Format as JSON:
{{
  "facts": [
    {{"statement": "...", "source": "...", "year": 1887}}
  ],
  "theories": [
    {{"name": "...", "principles": ["..."], "equations": ["..."]}}
  ]
}}

Be historically accurate. Only include what was known BEFORE {epoch_end}."""


ANOMALY_DETECTION_PROMPT = """You are a philosopher of science analyzing a knowledge corpus for contradictions.

CORPUS FACTS:
{facts}

CORPUS THEORIES:
{theories}

Find CONTRADICTIONS between facts and theories:
1. Empirical anomalies: facts that contradict theory predictions
2. Theoretical contradictions: theories that contradict each other
3. Unexplained phenomena: observations without theoretical explanation

For each contradiction, rate criticality:
- "low": minor inconsistency
- "medium": notable discrepancy
- "high": fundamental problem
- "critical": paradigm-threatening contradiction

Format as JSON array:
[
  {{
    "type": "empirical|theoretical|predictive",
    "fact_statement": "...",
    "theory_name": "...",
    "conflict_description": "...",
    "criticality": "low|medium|high|critical"
  }}
]

Be thorough. These contradictions are seeds for discovery."""


PRESUPPOSITION_EXTRACTION_PROMPT = """You are an epistemologist analyzing hidden assumptions in a theory.

THEORY: {theory_name}
PRINCIPLES: {principles}
EQUATIONS: {equations}

Extract HIDDEN ASSUMPTIONS (presuppositions) that this theory implicitly accepts:
- What does this theory take for granted?
- What "obvious" truths does it assume?
- What philosophical commitments are embedded?

Classify each as:
- ontological: assumptions about what EXISTS
- epistemological: assumptions about how we KNOW
- methodological: assumptions about how to INVESTIGATE
- metaphysical: assumptions about REALITY's nature

Format as JSON array:
[
  {{
    "statement": "...",
    "type": "ontological|epistemological|methodological|metaphysical"
  }}
]

These hidden assumptions are often where breakthrough insights hide."""


PRESUPPOSITION_INVERT_PROMPT = """You are a creative scientist questioning fundamental assumptions.

ORIGINAL ASSUMPTION: "{statement}"
TYPE: {type}

Generate the INVERSE assumption. What if this were FALSE?

Then explore:
1. What would the world look like if the inverse were true?
2. What implications would this have for our theories?
3. What new possibilities does this open?

Format as JSON:
{{
  "inverted_statement": "...",
  "implications": ["...", "...", "..."]
}}

Be bold. Many scientific revolutions came from inverting "obvious" assumptions."""


TRANSFORM_OPERATOR_PROMPTS = {
    "U_D+": """GENERALIZATION OPERATOR (D+1: {from_level} → {to_level})

Current knowledge: "{knowledge}"
Current state: F⟨T={t}, D={d}, A={a}⟩

Apply the GENERALIZATION operator:
- Move from specific to general
- From concrete instance to abstract principle
- From pattern to meta-pattern

Generate the MORE GENERAL version of this knowledge.
What abstract principle underlies this specific observation?

Format as JSON:
{{
  "new_knowledge": "...",
  "justification": "..."
}}""",
    "U_D-": """SPECIFICATION OPERATOR (D-1: {from_level} → {to_level})

Current knowledge: "{knowledge}"
Current state: F⟨T={t}, D={d}, A={a}⟩

Apply the SPECIFICATION operator:
- Move from general to specific
- From abstract principle to concrete instance
- From meta-pattern to pattern

Generate a MORE SPECIFIC version of this knowledge.
What concrete example demonstrates this principle?

Format as JSON:
{{
  "new_knowledge": "...",
  "justification": "..."
}}""",
    "U_T+": """TEMPORAL GENERALIZATION OPERATOR (T+1: {from_level} → {to_level})

Current knowledge: "{knowledge}"
Current state: F⟨T={t}, D={d}, A={a}⟩

Apply the TEMPORAL GENERALIZATION operator:
- Move from past to present, or present to future
- From "this happened" to "this always happens"
- From observation to law

If this was true THEN, is it ALWAYS true?
Transform this from temporal fact to universal principle.

Format as JSON:
{{
  "new_knowledge": "...",
  "justification": "..."
}}""",
    "U_T-": """TEMPORAL SPECIFICATION OPERATOR (T-1: {from_level} → {to_level})

Current knowledge: "{knowledge}"
Current state: F⟨T={t}, D={d}, A={a}⟩

Apply the TEMPORAL SPECIFICATION operator:
- Move from future to present, or present to past
- From "will happen" to "is happening" to "happened"
- From prediction to observation

Ground this knowledge in a specific temporal instance.

Format as JSON:
{{
  "new_knowledge": "...",
  "justification": "..."
}}""",
    "U_A+": """AGENCY EXPANSION OPERATOR (A+1: {from_level} → {to_level})

Current knowledge: "{knowledge}"
Current state: F⟨T={t}, D={d}, A={a}⟩

Apply the AGENCY EXPANSION operator:
- Move from Self to Other, or Other to System
- From "I observe" to "we observe" to "it is observed"
- From personal to interpersonal to systemic

Expand the scope of agency in this knowledge.

Format as JSON:
{{
  "new_knowledge": "...",
  "justification": "..."
}}""",
    "U_A-": """AGENCY CONTRACTION OPERATOR (A-1: {from_level} → {to_level})

Current knowledge: "{knowledge}"
Current state: F⟨T={t}, D={d}, A={a}⟩

Apply the AGENCY CONTRACTION operator:
- Move from System to Other, or Other to Self
- From systemic to personal perspective
- From "it is observed" to "I observe"

Contract the scope of agency in this knowledge.

Format as JSON:
{{
  "new_knowledge": "...",
  "justification": "..."
}}""",
}

LEVEL_NAMES = {
    "T": {0: "Past", 1: "Present", 2: "Future"},
    "D": {0: "Concrete", 1: "Abstract", 2: "Meta"},
    "A": {0: "Self", 1: "Other", 2: "System"},
}


ISOMORPHISM_DETECTION_PROMPT = """You are a mathematician looking for STRUCTURAL ISOMORPHISMS between domains.

Source domain: {source_domain}
Target domain: {target_domain}
Context: {context}

An isomorphism is a structural correspondence where:
- Concepts in one domain MAP to concepts in another
- RELATIONSHIPS are preserved under the mapping
- The "shape" of knowledge is the same, only labels differ

Famous example:
- Riemann Geometry → General Relativity
- "Curved manifold" ↔ "Spacetime"
- "Metric tensor" ↔ "Gravitational potential"
- "Geodesic" ↔ "Free fall trajectory"

Find similar structural correspondences between {source_domain} and {target_domain}.

Format as JSON:
{{
  "mappings": [
    ["{source_domain} concept", "{target_domain} concept"],
    ...
  ],
  "confidence": 0.0-1.0,
  "justification": "..."
}}

Be creative but rigorous. True isomorphisms preserve structure, not just analogies."""


SYNTHESIS_PROMPT = """You are a theoretical scientist synthesizing a new theory from discovered components.

INVERTED ASSUMPTIONS:
{inverted_presuppositions}

DERIVED PRINCIPLES (from cognitive transformations):
{derived_principles}

DOMAIN MAPPINGS (isomorphisms):
{isomorphisms}

ANOMALIES TO EXPLAIN:
{anomalies}

CORPUS FACTS (for compatibility check):
{corpus_facts}

Synthesize a NEW THEORY that:
1. Incorporates the inverted assumptions
2. Builds on the derived principles
3. Uses the domain mappings for new insights
4. Explains the anomalies
5. Is compatible with known facts

Format as JSON:
{{
  "name": "...",
  "postulates": ["...", "..."],
  "consequences": ["...", "..."],
  "equations": ["..."],
  "confidence": 0.0-1.0,
  "corpus_compatibility": 0.0-1.0,
  "predictions": ["...", "..."],
  "unresolved": ["..."]
}}

Be bold but rigorous. Great theories start with surprising assumptions."""


# ============================================================================
# LLM HELPER
# ============================================================================


async def llm_call_with_fallback(
    prompt: str,
    max_tokens: int = 2000,
    use_cache: bool = True,
    require_json: bool = False,
) -> str:
    """
    Call LLM with resilience features (caching, retries, fallback).

    Args:
        prompt: The prompt to send
        max_tokens: Max tokens to generate
        use_cache: Whether to use response cache
        require_json: Whether to require valid JSON output

    Returns:
        Generated text or fallback response
    """
    try:
        response = await llm_call(prompt, max_tokens=max_tokens)

        if require_json:
            parsed = parse_json_response(response)
            if parsed is None:
                logger.warning("LLM returned non-JSON when JSON was required")
                return '{"error": "Invalid JSON response"}'

        return response

    except Exception as e:
        logger.error(f"Unexpected error in llm_call: {e}")
        return '{"error": "Unexpected error"}' if require_json else "Error"


def parse_json_response(text: str) -> Any:
    """Extract JSON from LLM response"""
    import re

    json_match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ============================================================================
# DISCOVERY LOGIC
# ============================================================================


async def auto_populate_corpus(corpus: KnowledgeCorpus) -> KnowledgeCorpus:
    """Auto-populate corpus with known facts and theories using LLM"""
    prompt = CORPUS_AUTO_POPULATE_PROMPT.format(
        domain=corpus.domain,
        subdomains=", ".join(corpus.subdomains) if corpus.subdomains else corpus.domain,
        epoch_end=corpus.epoch_end,
    )

    response = await llm_call_with_fallback(prompt)
    data = parse_json_response(response)

    if data:
        if "facts" in data:
            for f in data["facts"]:
                corpus.facts.append(
                    Fact(
                        statement=f.get("statement", ""),
                        source=f.get("source"),
                        year=f.get("year"),
                        domain=corpus.domain,
                    )
                )
        if "theories" in data:
            for t in data["theories"]:
                corpus.theories.append(
                    Theory(
                        name=t.get("name", "Unknown"),
                        principles=t.get("principles", []),
                        equations=t.get("equations", []),
                        domain=corpus.domain,
                    )
                )

    return corpus


async def _populate_corpus_background(
    corpus_id: str, job_id: str, user_id: Optional[str] = None
) -> None:
    """
    Background task for corpus population.
    Updates job status as it progresses (PERSISTENT — survives restarts).
    """
    job_store = await get_job_store()

    try:
        await job_store.update_job(job_id, status="processing", progress=10)

        store = await get_discovery_store()
        corpus = await store.get_corpus(corpus_id)

        if not corpus:
            await job_store.update_job(
                job_id, status="failed", progress=0, error="Corpus not found"
            )
            return

        await job_store.update_job(job_id, progress=20)

        prompt = CORPUS_AUTO_POPULATE_PROMPT.format(
            domain=corpus.domain,
            subdomains=", ".join(corpus.subdomains) if corpus.subdomains else corpus.domain,
            epoch_end=corpus.epoch_end,
        )

        await job_store.update_job(job_id, progress=30)

        response = await llm_call_with_fallback(prompt)
        await job_store.update_job(job_id, progress=60)

        data = parse_json_response(response)
        await job_store.update_job(job_id, progress=70)

        facts_added = 0
        theories_added = 0

        if data:
            if "facts" in data:
                for f in data["facts"]:
                    corpus.facts.append(
                        Fact(
                            statement=f.get("statement", ""),
                            source=f.get("source"),
                            year=f.get("year"),
                            domain=corpus.domain,
                        )
                    )
                    facts_added += 1

            if "theories" in data:
                for t in data["theories"]:
                    corpus.theories.append(
                        Theory(
                            name=t.get("name", "Unknown"),
                            principles=t.get("principles", []),
                            equations=t.get("equations", []),
                            domain=corpus.domain,
                        )
                    )
                    theories_added += 1

        await job_store.update_job(job_id, progress=90)

        await store.update_corpus(corpus)

        await job_store.update_job(
            job_id,
            status="completed",
            progress=100,
            result={
                "facts_added": facts_added,
                "theories_added": theories_added,
                "corpus_id": corpus_id,
            },
        )
        logger.info(
            f"Corpus {corpus_id} population completed: {facts_added} facts, {theories_added} theories"
        )

    except Exception as e:
        logger.error(f"Corpus population failed: {e}")

        await job_store.increment_attempt(job_id)

        if await job_store.can_retry(job_id):
            logger.info(f"Job {job_id} will be retried")
            await job_store.update_job(job_id, status="failed", error=f"{str(e)} (will retry)")
        else:
            logger.error(f"Job {job_id} exceeded max attempts")
            await job_store.update_job(job_id, status="failed", error=str(e))


async def detect_anomalies(corpus: KnowledgeCorpus) -> list[Anomaly]:
    """Detect contradictions in corpus using LLM"""
    facts_text = "\n".join([f"- {f.statement} ({f.source}, {f.year})" for f in corpus.facts])
    theories_text = "\n".join(
        [f"- {t.name}: {'; '.join(t.principles[:3])}" for t in corpus.theories]
    )

    prompt = ANOMALY_DETECTION_PROMPT.format(facts=facts_text, theories=theories_text)
    response = await llm_call_with_fallback(prompt)
    data = parse_json_response(response)

    anomalies = []
    if data and isinstance(data, list):
        for a in data:
            anomalies.append(
                Anomaly(
                    corpus_id=corpus.id,
                    type=a.get("type", "empirical"),
                    fact_statement=a.get("fact_statement", ""),
                    theory_name=a.get("theory_name", ""),
                    conflict_description=a.get("conflict_description", ""),
                    criticality=a.get("criticality", "medium"),
                )
            )

    return anomalies


async def extract_presuppositions(theory: Theory) -> list[Presupposition]:
    """Extract hidden assumptions from theory using LLM"""
    prompt = PRESUPPOSITION_EXTRACTION_PROMPT.format(
        theory_name=theory.name,
        principles="; ".join(theory.principles),
        equations="; ".join(theory.equations) if theory.equations else "none",
    )

    response = await llm_call_with_fallback(prompt)
    data = parse_json_response(response)

    presups = []
    if data and isinstance(data, list):
        for p in data:
            presups.append(
                Presupposition(
                    theory_id=theory.id,
                    theory_name=theory.name,
                    statement=p.get("statement", ""),
                    type=p.get("type", "ontological"),
                )
            )

    return presups


async def invert_presupposition(presup: Presupposition) -> Presupposition:
    """Invert a presupposition and explore implications"""
    prompt = PRESUPPOSITION_INVERT_PROMPT.format(statement=presup.statement, type=presup.type)

    response = await llm_call_with_fallback(prompt)
    data = parse_json_response(response)

    if data:
        presup.inverted_statement = data.get("inverted_statement", f"NOT: {presup.statement}")
        presup.implications = data.get("implications", [])
        presup.status = "inverted"

    return presup


async def apply_transformation(state: CognitiveState, operator: str) -> CognitiveState:
    """Apply a cognitive operator to transform knowledge"""
    new_t, new_d, new_a = state.t, state.d, state.a

    if operator == "U_T+":
        new_t = min(2, state.t + 1)
        axis, from_level, to_level = (
            "T",
            LEVEL_NAMES["T"][state.t],
            LEVEL_NAMES["T"][new_t],
        )
    elif operator == "U_T-":
        new_t = max(0, state.t - 1)
        axis, from_level, to_level = (
            "T",
            LEVEL_NAMES["T"][state.t],
            LEVEL_NAMES["T"][new_t],
        )
    elif operator == "U_D+":
        new_d = min(2, state.d + 1)
        axis, from_level, to_level = (
            "D",
            LEVEL_NAMES["D"][state.d],
            LEVEL_NAMES["D"][new_d],
        )
    elif operator == "U_D-":
        new_d = max(0, state.d - 1)
        axis, from_level, to_level = (
            "D",
            LEVEL_NAMES["D"][state.d],
            LEVEL_NAMES["D"][new_d],
        )
    elif operator == "U_A+":
        new_a = min(2, state.a + 1)
        axis, from_level, to_level = (
            "A",
            LEVEL_NAMES["A"][state.a],
            LEVEL_NAMES["A"][new_a],
        )
    elif operator == "U_A-":
        new_a = max(0, state.a - 1)
        axis, from_level, to_level = (
            "A",
            LEVEL_NAMES["A"][state.a],
            LEVEL_NAMES["A"][new_a],
        )
    else:
        raise ValueError(f"Unknown operator: {operator}")

    if (new_t, new_d, new_a) == (state.t, state.d, state.a):
        return CognitiveState(
            knowledge=state.knowledge,
            t=state.t,
            d=state.d,
            a=state.a,
            justification=f"Boundary reached: cannot apply {operator}",
        )

    prompt_template = TRANSFORM_OPERATOR_PROMPTS.get(operator)
    if not prompt_template:
        raise ValueError(f"No prompt for operator: {operator}")

    prompt = prompt_template.format(
        knowledge=state.knowledge,
        t=state.t,
        d=state.d,
        a=state.a,
        from_level=from_level,
        to_level=to_level,
    )

    response = await llm_call_with_fallback(prompt)
    data = parse_json_response(response)

    if data:
        return CognitiveState(
            knowledge=data.get("new_knowledge", state.knowledge),
            t=new_t,
            d=new_d,
            a=new_a,
            justification=data.get("justification", ""),
        )
    else:
        return CognitiveState(
            knowledge=state.knowledge,
            t=new_t,
            d=new_d,
            a=new_a,
            justification="Transformation applied (no LLM response)",
        )


async def find_shortest_path(start: CognitiveState, goal: CognitiveState) -> list[str]:
    """Find shortest path of operators from start to goal (BFS in Z_3^3)"""
    from collections import deque

    start_coords = (start.t, start.d, start.a)
    goal_coords = (goal.t, goal.d, goal.a)

    if start_coords == goal_coords:
        return []

    queue = deque([(start_coords, [])])
    visited = {start_coords}

    operators = [
        ("U_T+", lambda c: (min(2, c[0] + 1), c[1], c[2])),
        ("U_T-", lambda c: (max(0, c[0] - 1), c[1], c[2])),
        ("U_D+", lambda c: (c[0], min(2, c[1] + 1), c[2])),
        ("U_D-", lambda c: (c[0], max(0, c[1] - 1), c[2])),
        ("U_A+", lambda c: (c[0], c[1], min(2, c[2] + 1))),
        ("U_A-", lambda c: (c[0], c[1], max(0, c[2] - 1))),
    ]

    while queue:
        coords, path = queue.popleft()

        for op_name, op_fn in operators:
            new_coords = op_fn(coords)
            if new_coords == coords:
                continue
            if new_coords in visited:
                continue

            new_path = path + [op_name]

            if new_coords == goal_coords:
                return new_path

            visited.add(new_coords)
            queue.append((new_coords, new_path))

    return []


async def detect_isomorphism(source: str, target: str, context: str = "") -> DomainMapping:
    """Detect structural isomorphism between domains"""
    prompt = ISOMORPHISM_DETECTION_PROMPT.format(
        source_domain=source,
        target_domain=target,
        context=context or "scientific theories",
    )

    response = await llm_call_with_fallback(prompt)
    data = parse_json_response(response)

    if data:
        return DomainMapping(
            source_domain=source,
            target_domain=target,
            mappings=data.get("mappings", []),
            confidence=data.get("confidence", 0.5),
            justification=data.get("justification", ""),
        )
    else:
        return DomainMapping(
            source_domain=source,
            target_domain=target,
            mappings=[],
            confidence=0.0,
            justification="No isomorphism detected",
        )


async def synthesize_theory(
    corpus: KnowledgeCorpus,
    inverted_presups: list[Presupposition],
    trajectory: Optional[Trajectory],
    isomorphisms: list[DomainMapping],
    anomalies: list[Anomaly],
) -> SynthesizedTheory:
    """Synthesize a new theory from discovery components"""

    inverted_text = (
        "\n".join(
            [
                f"- Original: {p.statement}\n  Inverted: {p.inverted_statement}"
                for p in inverted_presups
                if p.inverted_statement
            ]
        )
        or "None"
    )

    principles_text = "None"
    if trajectory and trajectory.transformations:
        principles_text = "\n".join(
            [
                f"- {t.to_state.knowledge} (from {t.operator})"
                for t in trajectory.transformations[-5:]
            ]
        )

    iso_text = (
        "\n".join(
            [
                f"- {iso.source_domain} → {iso.target_domain}: {iso.mappings[:3]}"
                for iso in isomorphisms
            ]
        )
        or "None"
    )

    anomalies_text = (
        "\n".join(
            [
                f"- {a.conflict_description} (criticality: {a.criticality})"
                for a in anomalies
                if not a.resolved
            ]
        )
        or "None"
    )

    facts_text = "\n".join([f"- {f.statement}" for f in corpus.facts[:10]])

    prompt = SYNTHESIS_PROMPT.format(
        inverted_presuppositions=inverted_text,
        derived_principles=principles_text,
        isomorphisms=iso_text,
        anomalies=anomalies_text,
        corpus_facts=facts_text,
    )

    response = await llm_call_with_fallback(prompt, max_tokens=3000)
    data = parse_json_response(response)

    if data:
        return SynthesizedTheory(
            corpus_id=corpus.id,
            name=data.get("name", "Unnamed Theory"),
            postulates=data.get("postulates", []),
            consequences=data.get("consequences", []),
            equations=data.get("equations", []),
            confidence=data.get("confidence", 0.5),
            corpus_compatibility=data.get("corpus_compatibility", 0.5),
            predictions=data.get("predictions", []),
            unresolved=data.get("unresolved", []),
        )
    else:
        return SynthesizedTheory(
            corpus_id=corpus.id,
            name="Synthesis Failed",
            postulates=["Unable to synthesize theory"],
            consequences=[],
            confidence=0.0,
            corpus_compatibility=0.0,
        )


# ============================================================================
# DISCOVERY LAB — MAIN ENGINE
# ============================================================================


class DiscoveryLab:
    """
    Main discovery engine implementing all 6 phases of the methodology.

    Phases:
    1. Corpus Setup - Define bounded knowledge space
    2. Anomaly Mining - Find contradictions in corpus
    3. Presupposition Analysis - Extract and invert hidden assumptions
    4. Transformation Lab - Apply Û operators systematically
    5. Isomorphism Bridge - Find cross-domain structural mappings
    6. Synthesis Engine - Combine insights into new theory
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.store = DiscoveryStore(db_path)
        self.job_store = DiscoveryJobStore(db_path)

    async def initialize(self):
        """Initialize the lab (database, etc.)"""
        await self.store.initialize()

    # --- Phase 1: Corpus Setup ---

    async def create_corpus(
        self,
        name: str,
        domain: str,
        epoch_end: str,
        subdomains: list[str] = None,
        auto_populate: bool = False,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> KnowledgeCorpus:
        """Create a new knowledge corpus"""
        corpus = KnowledgeCorpus(
            name=name,
            domain=domain,
            epoch_end=epoch_end,
            subdomains=subdomains or [],
            user_id=user_id,
            project_id=project_id,
        )

        await self.store.create_corpus(corpus)

        if auto_populate:
            await auto_populate_corpus(corpus)
            await self.store.update_corpus(corpus)

        return corpus

    async def get_corpus(self, corpus_id: str) -> Optional[KnowledgeCorpus]:
        """Get corpus by ID"""
        return await self.store.get_corpus(corpus_id)

    async def list_corpuses(
        self, user_id: Optional[str] = None, project_id: Optional[str] = None
    ) -> list[KnowledgeCorpus]:
        """List corpuses filtered by user and/or project"""
        return await self.store.list_corpus(user_id, project_id)

    async def add_fact(
        self,
        corpus_id: str,
        statement: str,
        source: Optional[str] = None,
        year: Optional[int] = None,
    ) -> KnowledgeCorpus:
        """Add a fact to corpus"""
        corpus = await self.store.get_corpus(corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        fact = Fact(statement=statement, source=source, year=year, domain=corpus.domain)
        corpus.facts.append(fact)
        await self.store.update_corpus(corpus)
        return corpus

    async def add_theory(
        self,
        corpus_id: str,
        name: str,
        principles: list[str] = None,
        equations: list[str] = None,
    ) -> KnowledgeCorpus:
        """Add a theory to corpus"""
        corpus = await self.store.get_corpus(corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        theory = Theory(
            name=name,
            principles=principles or [],
            equations=equations or [],
            domain=corpus.domain,
        )
        corpus.theories.append(theory)
        await self.store.update_corpus(corpus)
        return corpus

    # --- Phase 2: Anomaly Mining ---

    async def detect_anomalies(self, corpus_id: str) -> list[Anomaly]:
        """Detect anomalies in corpus"""
        corpus = await self.store.get_corpus(corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        anomalies = await detect_anomalies(corpus)

        for a in anomalies:
            await self.store.save_anomaly(a)

        return anomalies

    async def get_anomalies(self, corpus_id: str) -> list[Anomaly]:
        """Get all anomalies for corpus"""
        return await self.store.get_anomalies(corpus_id)

    async def resolve_anomaly(self, anomaly_id: str) -> None:
        """Mark anomaly as resolved"""
        async with aiosqlite.connect(self.store.db_path) as db:
            await db.execute("UPDATE anomalies SET resolved = 1 WHERE id = ?", (anomaly_id,))
            await db.commit()

    # --- Phase 3: Presupposition Analysis ---

    async def extract_presuppositions(self, corpus_id: str, theory_id: str) -> list[Presupposition]:
        """Extract presuppositions from a theory"""
        corpus = await self.store.get_corpus(corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        theory = None
        for t in corpus.theories:
            if t.id == theory_id:
                theory = t
                break

        if not theory:
            raise ValueError(f"Theory {theory_id} not found")

        presups = await extract_presuppositions(theory)

        for p in presups:
            await self.store.save_presupposition(p)

        return presups

    async def get_presuppositions(self, theory_id: str) -> list[Presupposition]:
        """Get presuppositions for a theory"""
        return await self.store.get_presuppositions_for_theory(theory_id)

    async def invert_presupposition(self, presup_id: str) -> Presupposition:
        """Invert a presupposition"""
        presup = await self.store.get_presupposition(presup_id)
        if not presup:
            raise ValueError(f"Presupposition {presup_id} not found")

        presup = await invert_presupposition(presup)
        await self.store.save_presupposition(presup)
        return presup

    # --- Phase 4: Transformation Lab ---

    async def apply_operator(
        self, state: CognitiveState, operator: str
    ) -> tuple[CognitiveState, Transformation]:
        """Apply a cognitive transformation operator"""
        new_state = await apply_transformation(state, operator)

        transformation = Transformation(
            from_state=state,
            to_state=new_state,
            operator=operator,
            justification=new_state.justification or "",
        )

        return new_state, transformation

    async def start_trajectory(self, corpus_id: str, state: CognitiveState) -> Trajectory:
        """Start a new transformation trajectory"""
        traj = Trajectory(corpus_id=corpus_id, start_state=state, current_state=state)

        await self.store.save_trajectory(traj)
        return traj

    async def apply_to_trajectory(self, traj_id: str, operator: str) -> Trajectory:
        """Apply transformation to trajectory"""
        traj = await self.store.get_trajectory(traj_id)
        if not traj:
            raise ValueError(f"Trajectory {traj_id} not found")

        new_state = await apply_transformation(traj.current_state, operator)

        transformation = Transformation(
            from_state=traj.current_state,
            to_state=new_state,
            operator=operator,
            justification=new_state.justification or "",
        )

        traj.transformations.append(transformation)
        traj.current_state = new_state

        await self.store.save_trajectory(traj)
        return traj

    async def get_trajectory(self, traj_id: str) -> Optional[Trajectory]:
        """Get trajectory by ID"""
        return await self.store.get_trajectory(traj_id)

    async def find_path(self, start_state: CognitiveState, goal_state: CognitiveState) -> list[str]:
        """Find shortest path between two cognitive states"""
        return await find_shortest_path(start_state, goal_state)

    # --- Phase 5: Isomorphism Bridge ---

    async def detect_isomorphism(
        self, source_domain: str, target_domain: str, context: str = ""
    ) -> DomainMapping:
        """Detect isomorphism between domains"""
        iso = await detect_isomorphism(source_domain, target_domain, context)
        await self.store.save_isomorphism(iso)
        return iso

    async def apply_isomorphism(self, mapping_id: str, knowledge: str) -> dict:
        """Apply isomorphism to transfer knowledge between domains"""
        iso = await self.store.get_isomorphism(mapping_id)
        if not iso:
            raise ValueError(f"Isomorphism {mapping_id} not found")

        mapping_text = "\n".join([f"- {s} → {t}" for s, t in iso.mappings])

        prompt = f"""Apply this domain mapping to transform knowledge:

MAPPING ({iso.source_domain} → {iso.target_domain}):
{mapping_text}

KNOWLEDGE TO TRANSFORM:
"{knowledge}"

Transform this knowledge from {iso.source_domain} to {iso.target_domain}.
What is the equivalent statement in the target domain?

Respond with just the transformed knowledge statement."""

        response = await llm_call_with_fallback(prompt, max_tokens=500)

        return {
            "original": knowledge,
            "transformed": response.strip(),
            "source_domain": iso.source_domain,
            "target_domain": iso.target_domain,
        }

    # --- Phase 6: Synthesis Engine ---

    async def synthesize_theory(
        self,
        corpus_id: str,
        inverted_presupposition_ids: list[str] = None,
        trajectory_id: Optional[str] = None,
        isomorphism_ids: list[str] = None,
        anomaly_ids: list[str] = None,
    ) -> SynthesizedTheory:
        """Synthesize a new theory from discovery components"""
        corpus = await self.store.get_corpus(corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {corpus_id} not found")

        inverted_presups = []
        for pid in inverted_presupposition_ids or []:
            p = await self.store.get_presupposition(pid)
            if p and p.status == "inverted":
                inverted_presups.append(p)

        trajectory = None
        if trajectory_id:
            trajectory = await self.store.get_trajectory(trajectory_id)

        isomorphisms = []
        for iso_id in isomorphism_ids or []:
            iso = await self.store.get_isomorphism(iso_id)
            if iso:
                isomorphisms.append(iso)

        anomalies = []
        for aid in anomaly_ids or []:
            async with aiosqlite.connect(self.store.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM anomalies WHERE id = ?", (aid,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        anomalies.append(
                            Anomaly(
                                id=row["id"],
                                corpus_id=row["corpus_id"],
                                type=row["type"],
                                fact_statement=row["fact_statement"],
                                theory_name=row["theory_name"],
                                conflict_description=row["conflict_description"],
                                criticality=row["criticality"],
                                resolved=bool(row["resolved"]),
                            )
                        )

        theory = await synthesize_theory(
            corpus, inverted_presups, trajectory, isomorphisms, anomalies
        )

        await self.store.save_theory(theory)
        return theory

    async def get_synthesized_theories(self, corpus_id: str) -> list[SynthesizedTheory]:
        """Get all synthesized theories for corpus"""
        async with aiosqlite.connect(self.store.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM synthesized_theories WHERE corpus_id = ? ORDER BY created_at DESC",
                (corpus_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    SynthesizedTheory(
                        id=row["id"],
                        corpus_id=row["corpus_id"],
                        name=row["name"],
                        postulates=json.loads(row["postulates"]),
                        consequences=json.loads(row["consequences"]),
                        equations=json.loads(row["equations"]) if row["equations"] else [],
                        confidence=row["confidence"],
                        corpus_compatibility=row["corpus_compatibility"],
                        predictions=json.loads(row["predictions"]) if row["predictions"] else [],
                        unresolved=json.loads(row["unresolved"]) if row["unresolved"] else [],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]

    # --- Background Jobs ---

    async def start_population_job(self, corpus_id: str, user_id: Optional[str] = None) -> dict:
        """Start background corpus population job"""
        import time

        job_id = f"{corpus_id}_{int(time.time())}"

        await self.job_store.create_job(job_id=job_id, corpus_id=corpus_id, user_id=user_id)

        _fire_and_forget(_populate_corpus_background(corpus_id, job_id, user_id))

        return {"corpus_id": corpus_id, "job_id": job_id, "job_status": "pending"}

    async def get_job_status(self, corpus_id: str) -> Optional[dict]:
        """Get status of corpus population job"""
        return await self.job_store.get_corpus_job(corpus_id)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Models
    "Fact",
    "Theory",
    "KnowledgeCorpus",
    "Anomaly",
    "Presupposition",
    "CognitiveState",
    "Transformation",
    "Trajectory",
    "DomainMapping",
    "SynthesizedTheory",
    # Store
    "DiscoveryStore",
    "DiscoveryJobStore",
    # Main Engine
    "DiscoveryLab",
    # Request models
    "CreateCorpusRequest",
    "AddFactRequest",
    "AddTheoryRequest",
    "DetectAnomaliesRequest",
    "ExtractPresuppositionsRequest",
    "InvertPresuppositionRequest",
    "TransformRequest",
    "FindPathRequest",
    "DetectIsomorphismRequest",
    "ApplyIsomorphismRequest",
    "SynthesizeRequest",
    # Functions
    "auto_populate_corpus",
    "detect_anomalies",
    "extract_presuppositions",
    "invert_presupposition",
    "apply_transformation",
    "find_shortest_path",
    "detect_isomorphism",
    "synthesize_theory",
    "llm_call_with_fallback",
    "parse_json_response",
    # Constants
    "DEFAULT_DB_PATH",
    "LEVEL_NAMES",
    "TRANSFORM_OPERATOR_PROMPTS",
]
