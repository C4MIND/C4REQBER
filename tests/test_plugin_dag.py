"""Tests for plugin DAG execution."""
from __future__ import annotations

import pytest

from src.plugins.dag import PluginDAG, PluginNode


class TestPluginDAG:
    """Test suite for PluginDAG."""

    def test_add_node(self):
        dag = PluginDAG()
        dag.add_node("swot", config={"depth": 3})
        assert "swot" in dag._nodes
        assert dag._nodes["swot"].config == {"depth": 3}

    def test_add_edge(self):
        dag = PluginDAG()
        dag.add_edge("swot", "five_whys")
        assert "swot" in dag._edges
        assert "five_whys" in dag._edges["swot"]
        assert dag._in_degree["five_whys"] == 1

    def test_validate_no_cycle(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        assert dag.validate() is True

    def test_validate_with_cycle(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        dag.add_edge("c", "a")
        assert dag.validate() is False

    def test_topological_sort_linear(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        order = dag.topological_sort()
        assert order == ["a", "b", "c"]

    def test_topological_sort_diamond(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")
        dag.add_edge("a", "c")
        dag.add_edge("b", "d")
        dag.add_edge("c", "d")
        order = dag.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_topological_sort_cycle_raises(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")
        dag.add_edge("b", "a")
        with pytest.raises(ValueError, match="cycle"):
            dag.topological_sort()

    def test_execute_linear_with_mock(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")

        calls = []

        def mock_executor(plugin_id, problem, **kwargs):
            calls.append((plugin_id, problem, dict(kwargs)))
            return {"plugin_id": plugin_id, "problem": problem}

        results = dag.execute("test-problem", executor=mock_executor)
        assert len(calls) == 2
        assert calls[0][0] == "a"
        assert calls[1][0] == "b"
        assert "a_result" in calls[1][2]
        assert results["a"]["plugin_id"] == "a"
        assert results["b"]["plugin_id"] == "b"

    def test_execute_passes_context(self):
        dag = PluginDAG()
        dag.add_edge("first", "second")

        def mock_executor(plugin_id, problem, **kwargs):
            return {"received_context_keys": list(kwargs.keys())}

        results = dag.execute("p", executor=mock_executor)
        # second should receive first_result in its kwargs
        second_ctx = results["second"]["received_context_keys"]
        assert "first_result" in second_ctx

    def test_execute_error_handling(self):
        dag = PluginDAG()
        dag.add_node("bad")

        def failing_executor(plugin_id, problem, **kwargs):
            raise RuntimeError("boom")

        results = dag.execute("p", executor=failing_executor)
        assert "error" in results["bad"]
        assert results["bad"]["error"] == "boom"

    def test_from_list(self):
        dag = PluginDAG.from_list(["x", "y", "z"])
        assert dag.topological_sort() == ["x", "y", "z"]

    def test_from_edges(self):
        dag = PluginDAG.from_edges(
            [("a", "b"), ("b", "c")],
            configs={"a": {"x": 1}},
        )
        assert dag.topological_sort() == ["a", "b", "c"]
        assert dag._nodes["a"].config == {"x": 1}

    def test_to_dict(self):
        dag = PluginDAG()
        dag.add_edge("a", "b")
        d = dag.to_dict()
        assert d["valid"] is True
        assert len(d["nodes"]) == 2

    def test_isolated_nodes(self):
        dag = PluginDAG()
        dag.add_node("x")
        dag.add_node("y")
        order = dag.topological_sort()
        assert set(order) == {"x", "y"}

    def test_complex_dag(self):
        dag = PluginDAG()
        dag.add_edge("swot", "pareto")
        dag.add_edge("five_whys", "pareto")
        dag.add_edge("pareto", "synthesis")
        dag.add_node("extra")
        order = dag.topological_sort()
        assert order.index("swot") < order.index("pareto")
        assert order.index("five_whys") < order.index("pareto")
        assert order.index("pareto") < order.index("synthesis")
        assert "extra" in order
