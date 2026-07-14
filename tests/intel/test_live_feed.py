from __future__ import annotations

import sys
import time

import src.intel.live_feed as lf


ORIGINAL_CACHE_PATH = lf.FEED_CACHE_PATH
ORIGINAL_CHECK = lf.LiveFeed._check_network
lf.LiveFeed._check_network = staticmethod(lambda: False)


def _make_feed(tmp_path):
    cache_file = tmp_path / "feed_cache.json"
    lf.FEED_CACHE_PATH = cache_file
    feed = lf.LiveFeed()
    return feed, cache_file


class TestProblemDataclass:
    def test_problem_creation_and_age(self):
        t0 = time.time()
        p = lf.Problem(
            id="reddit/r/ML:001",
            title="Test problem",
            source="reddit",
            url="https://example.com",
            severity=0.7,
            discovered_at=t0 - 120,
        )
        assert p.id == "reddit/r/ML:001"
        assert p.title == "Test problem"
        assert p.source == "reddit"
        assert p.url == "https://example.com"
        assert p.severity == 0.7
        assert 1.9 < p.age_minutes < 2.1


class TestHypothesisDataclass:
    def test_hypothesis_creation(self):
        h = lf.Hypothesis(
            id="hyp:001",
            title="Test hypothesis",
            source_problems=["p1", "p2"],
            confidence=0.8,
            domain="biology",
        )
        assert h.id == "hyp:001"
        assert h.title == "Test hypothesis"
        assert h.source_problems == ["p1", "p2"]
        assert h.confidence == 0.8
        assert h.domain == "biology"
        assert hasattr(h, "generated_at")


class TestLiveFeed:
    def test_starts_empty(self, tmp_path):
        feed, _ = _make_feed(tmp_path)
        assert len(feed.problems) == 0
        assert len(feed.hypotheses) == 0

    def test_is_tutorial(self):
        assert lf.LiveFeed._is_tutorial("How to train a model") is True
        assert lf.LiveFeed._is_tutorial("Python Tutorial for beginners") is True
        assert lf.LiveFeed._is_tutorial("Complete guide to PyTorch") is True
        assert lf.LiveFeed._is_tutorial("Introduction to deep learning") is True
        assert lf.LiveFeed._is_tutorial("Machine Learning 101") is True
        assert lf.LiveFeed._is_tutorial("Course on neural networks") is True
        assert lf.LiveFeed._is_tutorial("Novel approach to protein folding") is False
        assert lf.LiveFeed._is_tutorial("") is False

    def test_is_show_hn(self):
        assert lf.LiveFeed._is_show_hn("Show HN: My new project") is True
        assert lf.LiveFeed._is_show_hn("show hn: something") is True
        assert lf.LiveFeed._is_show_hn("Show HN") is True
        assert lf.LiveFeed._is_show_hn("Ask HN: What do you think?") is False
        assert lf.LiveFeed._is_show_hn("Show HN Project") is True

    def test_cache_path_exists_after_save(self, tmp_path):
        feed, cache_file = _make_feed(tmp_path)
        assert not cache_file.exists()
        feed._save_cache()
        assert cache_file.exists()

    def test_feed_stop_sets_running_false(self, tmp_path):
        feed, _ = _make_feed(tmp_path)
        feed._running = True
        feed.stop()
        assert feed._running is False


def teardown_module():
    lf.FEED_CACHE_PATH = ORIGINAL_CACHE_PATH
    lf.LiveFeed._check_network = ORIGINAL_CHECK
