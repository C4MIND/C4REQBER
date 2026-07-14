"""
Locust load-test harness for C4REQBER v8 API endpoints.

Usage:
    locust -f locustfile.py --host http://localhost:8000
"""
from locust import HttpUser, task, between
import random


class AgendaUser(HttpUser):
    """Simulate users generating and approving research agendas."""

    wait_time = between(1, 3)

    @task(3)
    def generate_agenda(self) -> None:
        """POST /v8/agenda/generate with a small knowledge graph."""
        payload = {
            "knowledge_graph": {
                "nodes": ["A", "B", "C"],
                "edges": [["A", "B"], ["B", "C"]],
            },
            "recent_results": [{"score": 0.9, "insight": "test"}],
            "n_questions": 3,
        }
        self.client.post("/v8/agenda/generate", json=payload)

    @task(2)
    def approve_question(self) -> None:
        """POST /v8/agenda/approve with random action."""
        action = random.choice(["approve", "reject", "modify"])
        payload = {
            "question_text": "Does X cause Y in quantum systems?",
            "action": action,
            "modified_text": "Modified question text" if action == "modify" else None,
        }
        self.client.post("/v8/agenda/approve", json=payload)

    @task(1)
    def get_progress(self) -> None:
        """GET /v8/agenda/progress."""
        self.client.get("/v8/agenda/progress")


class ExplorationUser(HttpUser):
    """Simulate users exploring anomalies and generating questions."""

    wait_time = between(1, 4)

    @task(3)
    def detect_anomalies(self) -> None:
        """POST /v8/exploration/anomalies with sample data."""
        n = random.randint(5, 20)
        payload = {
            "embeddings": [[random.random() for _ in range(8)] for _ in range(n)],
            "papers": [{"title": f"Paper {i}"} for i in range(n)],
            "predicted": [random.random() * 10 for _ in range(n)],
            "expected": [random.random() * 10 for _ in range(n)],
            "contamination": 0.05,
            "threshold_sigma": 3.0,
        }
        self.client.post("/v8/exploration/anomalies", json=payload)

    @task(2)
    def generate_questions(self) -> None:
        """POST /v8/exploration/questions."""
        payload = {
            "existing_questions": ["Does X cause Y?"],
            "topic": "causal inference in quantum systems",
            "n_candidates": 20,
            "top_k": 3,
        }
        self.client.post("/v8/exploration/questions", json=payload)

    @task(1)
    def extend_formal(self) -> None:
        """POST /v8/exploration/extend-formal."""
        payload = {
            "library": "mathlib4",
            "language": "lean4",
            "concept_gap": "continuity of composed functions",
        }
        self.client.post("/v8/exploration/extend-formal", json=payload)
