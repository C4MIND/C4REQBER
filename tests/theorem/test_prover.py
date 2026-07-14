"""Tests for src/theorem/prover.py — Theorem, ProofStep, Lean code generator."""
from __future__ import annotations

from src.theorem.prover import (
    LEAN_PREAMBLE,
    ProofStatus,
    ProofStep,
    ProverBackend,
    Theorem,
    TheoremProver,
    generate_lean_proof_skeleton,
    get_theorem_prover,
    hypothesis_to_lean,
)


class TestProverBackend:
    def test_all_backends(self):
        assert ProverBackend.LEAN.value == "lean"
        assert ProverBackend.AGDA.value == "agda"
        assert ProverBackend.HASKELL.value == "haskell"
        assert ProverBackend.SIMULATION.value == "simulation"


class TestProofStatus:
    def test_all_statuses(self):
        assert ProofStatus.PENDING.value == "pending"
        assert ProofStatus.PROVED.value == "proved"
        assert ProofStatus.ERROR.value == "error"


class TestProofStep:
    def test_construction(self):
        step = ProofStep(
            id="s1",
            tactic="intro h",
            goal_before="P → Q",
            goal_after="Q",
            justification="by modus ponens",
            line_number=1,
        )
        assert step.id == "s1"
        assert step.tactic == "intro h"
        assert step.line_number == 1

    def test_none_goal_after(self):
        step = ProofStep(
            id="s2",
            tactic="apply",
            goal_before="P",
            goal_after=None,
            justification="trivial",
            line_number=2,
        )
        assert step.goal_after is None


class TestTheorem:
    def test_construction(self):
        theorem = Theorem(
            id="t1",
            hypothesis_id="h1",
            statement="Every natural number has a successor",
            formal_statement="∀ n : ℕ, ∃ m : ℕ, m = n + 1",
            backend=ProverBackend.LEAN,
            status=ProofStatus.PENDING,
            proof_steps=[],
            error_message=None,
            confidence=0.9,
            created_at="2026-01-01",
            proved_at=None,
        )
        assert theorem.id == "t1"
        assert theorem.proof_steps == []

    def test_with_steps(self):
        step = ProofStep("s1", "intros", "⊢ True", "True", "trivial", 1)
        theorem = Theorem(
            id="t2",
            hypothesis_id="h2",
            statement="True is true",
            formal_statement="True",
            backend=ProverBackend.LEAN,
            status=ProofStatus.PROVED,
            proof_steps=[step],
            error_message=None,
            confidence=1.0,
            created_at="2026-01-01",
            proved_at="2026-01-02",
        )
        assert len(theorem.proof_steps) == 1


class TestLeanPreamble:
    def test_preamble_not_empty(self):
        assert "Mathlib" in LEAN_PREAMBLE
        assert "C4REQBER" in LEAN_PREAMBLE


class TestHypothesisToLean:
    def test_existential(self):
        result = hypothesis_to_lean(
            "there exists x such that x is prime",
            domain="math",
        )
        assert "theorem" in result

    def test_for_all(self):
        result = hypothesis_to_lean(
            "for all primes p, p is odd",
            domain="math",
        )
        assert "theorem" in result

    def test_implication(self):
        result = hypothesis_to_lean(
            "if it rains then the ground is wet",
            domain="general",
        )
        assert "theorem" in result

    def test_simple(self):
        result = hypothesis_to_lean(
            "energy is conserved",
            domain="physics",
        )
        assert "theorem" in result

    def test_empty_hypothesis(self):
        result = hypothesis_to_lean("")
        assert "theorem" in result


class TestGenerateLeanProofSkeleton:
    def test_generates_complete_file(self):
        result = generate_lean_proof_skeleton("P implies P")
        assert "import Mathlib" in result
        assert "theorem" in result
        assert "end C4REQBER" in result

    def test_contains_sorry(self):
        result = generate_lean_proof_skeleton("All swans are white")
        assert "sorry" in result


class TestTheoremProver:
    def test_instantiation(self):
        prover = TheoremProver(backend=ProverBackend.SIMULATION)
        assert prover is not None
        assert prover.backend == ProverBackend.SIMULATION

    def test_get_theorem_prover(self):
        prover = get_theorem_prover(backend="simulation")
        assert prover is not None
