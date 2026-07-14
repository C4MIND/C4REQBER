"""
DiscoveryChainer — C4 discovery chaining via Theorem 11.

Mathematical foundation:
    C4Space = Z_3^3 (27 states). The belief-path algorithm (ported from
    adaptive-topology/formal-proofs/c4-comp-v5.agda:838-885) computes the
    canonical shortest path between any two states as a sequence of unit
    operators.  The diameter of C4Space is 6: any two states are at most
    6 steps apart.  Antipodal points (0,0,0) ↔ (2,2,2) are exactly 6
    steps apart.

    Cyclic distance per axis (belief-path):
        dist(a, b) = (b - a) mod 3
    Path = sequence of +1 operators changing one coordinate at a time.
    Total steps = Σ dist(axis) ≤ 6.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.c4.state import C4State


DB_PATH = Path(__file__).parent.parent.parent / "data" / "discovery_chain.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS discoveries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    problem     TEXT NOT NULL,
    t           INTEGER NOT NULL,
    s           INTEGER NOT NULL,
    a           INTEGER NOT NULL,
    result      TEXT NOT NULL,  -- JSON
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discoveries_problem ON discoveries(problem);
CREATE INDEX IF NOT EXISTS idx_discoveries_state ON discoveries(t, s, a);
"""

C4Op = str

_AXIS_OPS = ["tau+", "lambda+", "kappa+"]


@dataclass(frozen=True)
class DiscoveryRecord:
    """A stored discovery result."""

    problem: str
    state: C4State
    result: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "state": list(self.state.to_tuple()),
            "result": self.result,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ChainSuggestion:
    """Result of chaining: nearest past discovery + path to it."""

    problem: str
    from_state: C4State
    to_state: C4State
    path: list[C4Op]
    record: DiscoveryRecord
    distance: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "from_state": list(self.from_state.to_tuple()),
            "to_state": list(self.to_state.to_tuple()),
            "path": self.path,
            "distance": self.distance,
            "record": self.record.to_dict(),
        }


class DiscoveryChainer:
    """
    Chains discoveries through C4 state space using Theorem 11.

    Theorem 11 (Agda, c4-comp-v5.agda:838-885):
        For C4Space = Z_3^3, the canonical belief-path between any two
        states uses only forward (+1) unit operators per axis.  The
        maximum path length is 6 (diameter), realised by antipodal
        pairs such as (0,0,0) ↔ (2,2,2).
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(SCHEMA_SQL)

    @staticmethod
    def compute_path(from_state: C4State, to_state: C4State) -> list[C4Op]:
        """
        Return the canonical ≤6-step belief-path between two C4 states.

        Algorithm (ported from Agda belief-path):
            For each axis (T, S, A):
                diff = (target - source) mod 3
                append the corresponding + operator `diff` times.

        Examples:
            >>> DiscoveryChainer.compute_path(C4State(0,0,0), C4State(2,2,2))
            ['tau+', 'tau+', 'lambda+', 'lambda+', 'kappa+', 'kappa+']
            >>> DiscoveryChainer.compute_path(C4State(0,0,0), C4State(2,0,0))
            ['tau+', 'tau+']
            >>> DiscoveryChainer.compute_path(C4State(1,1,1), C4State(1,1,1))
            []
        """
        path: list[C4Op] = []
        src = from_state.to_tuple()
        dst = to_state.to_tuple()
        for axis, op_name in enumerate(_AXIS_OPS):
            diff = (dst[axis] - src[axis]) % 3
            path.extend([op_name] * diff)
        return path

    @staticmethod
    def path_distance(from_state: C4State, to_state: C4State) -> int:
        """C4 belief-path distance (sum of cyclic per-axis distances)."""
        src = from_state.to_tuple()
        dst = to_state.to_tuple()
        return sum((dst[i] - src[i]) % 3 for i in range(3))

    def store_discovery(
        self,
        problem: str,
        state: C4State,
        result: dict[str, Any],
    ) -> int:
        """Persist a discovery to SQLite and return its row id."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO discoveries (problem, t, s, a, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    problem,
                    state.T,
                    state.S,
                    state.A,
                    json.dumps(result, ensure_ascii=False, default=str),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return cur.lastrowid or 0

    def load_history(self, problem: str | None = None) -> list[DiscoveryRecord]:
        """Load stored discoveries, optionally filtered by problem."""
        rows: list[tuple[str, int, int, int, str, str]] = []
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if problem:
                rows = conn.execute(
                    "SELECT problem, t, s, a, result, created_at FROM discoveries WHERE problem = ? ORDER BY created_at",
                    (problem,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT problem, t, s, a, result, created_at FROM discoveries ORDER BY created_at",
                ).fetchall()

        records: list[DiscoveryRecord] = []
        for row in rows:
            records.append(
                DiscoveryRecord(
                    problem=row[0],
                    state=C4State(T=row[1], S=row[2], A=row[3]),
                    result=json.loads(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                )
            )
        return records

    def chain_from_history(
        self,
        problem: str,
        history: list[DiscoveryRecord],
    ) -> ChainSuggestion | None:
        """
        Find the nearest past discovery in C4 space and return the chain.

        If `history` is empty, falls back to loading from the database.
        Returns None when no prior discovery exists.
        """
        if not history:
            history = self.load_history(problem)
        if not history:
            return None

        # Find the record with minimum belief-path distance
        best_record = history[0]
        best_dist = self.path_distance(best_record.state, history[0].state)
        # We need a reference state — use the most recent record's state
        # or the state from the last record in history.
        reference_state = history[-1].state

        best_record = history[0]
        best_dist = self.path_distance(reference_state, best_record.state)
        for record in history[1:]:
            dist = self.path_distance(reference_state, record.state)
            if dist < best_dist:
                best_dist = dist
                best_record = record

        path = self.compute_path(reference_state, best_record.state)
        return ChainSuggestion(
            problem=problem,
            from_state=reference_state,
            to_state=best_record.state,
            path=path,
            record=best_record,
            distance=best_dist,
        )

    def get_state_after_path(self, start: C4State, path: list[C4Op]) -> C4State:
        """Apply a sequence of operators to a start state."""
        current = start
        for op in path:
            if op == "tau+":
                current = current.shift_time(1)
            elif op == "lambda+":
                current = current.shift_scale(1)
            elif op == "kappa+":
                current = current.shift_agency(1)
            elif op == "tau-":
                current = current.shift_time(-1)
            elif op == "lambda-":
                current = current.shift_scale(-1)
            elif op == "kappa-":
                current = current.shift_agency(-1)
            elif op == "iota":
                current = current.invert()
        return current
