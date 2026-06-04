import pytest

from src.pipeline.observer import PipelineObserver


class TestPipelineObserver:
    def setup_method(self):
        self.observer = PipelineObserver(stagnation_threshold=0.05, max_stagnant_iterations=3)

    def test_hash_hypothesis_deterministic(self):
        h1 = self.observer._hash_hypothesis("same text")
        h2 = self.observer._hash_hypothesis("same text")
        assert h1 == h2

    def test_hash_hypothesis_different_texts(self):
        h1 = self.observer._hash_hypothesis("first hypothesis")
        h2 = self.observer._hash_hypothesis("second hypothesis different")
        assert h1 != h2

    def test_should_halt_identical_hashes(self):
        text = "same hypothesis repeated"
        for i in range(3):
            self.observer.observe(
                i,
                {
                    "novelty_score": 0.5,
                    "gap_potential": 0.5,
                    "hypothesis_text": text,
                    "abort_reasons": [],
                },
            )
        assert self.observer.should_halt() is True

    def test_should_not_halt_different_hashes(self):
        gap_potentials = [0.5, 0.3, 0.7]
        for i in range(3):
            self.observer.observe(
                i,
                {
                    "novelty_score": 0.5,
                    "gap_potential": gap_potentials[i],
                    "hypothesis_text": f"hypothesis iteration {i}",
                    "abort_reasons": [],
                },
            )
        assert self.observer.should_halt() is False

    def test_should_halt_plateau(self):
        for i in range(3):
            self.observer.observe(
                i,
                {
                    "novelty_score": 0.5,
                    "gap_potential": 0.5,
                    "hypothesis_text": f"hypo{i}",
                    "abort_reasons": [],
                },
            )
        assert self.observer.should_halt() is True
