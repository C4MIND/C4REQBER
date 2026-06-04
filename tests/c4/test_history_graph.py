from __future__ import annotations

from c4.history_graph import HistoryGraph, HistoryNode


class TestHistoryGraphAdd:
    def test_add_single_node(self):
        g = HistoryGraph()
        node = HistoryNode(id="n1", query="test", result_summary="ok", c4_state=(0, 0, 0))
        g.add(node)
        assert len(g) == 1

    def test_add_two_nodes(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q1", result_summary="r1", c4_state=(0, 0, 0)))
        g.add(HistoryNode(id="b", query="q2", result_summary="r2", c4_state=(1, 1, 1)))
        assert len(g) == 2

    def test_add_node_with_dependencies(self):
        g = HistoryGraph()
        parent = HistoryNode(id="p", query="q", result_summary="r", c4_state=(0, 0, 0))
        g.add(parent)
        child = HistoryNode(
            id="c", query="q2", result_summary="r2", c4_state=(1, 0, 0),
            dependencies=["p"],
        )
        g.add(child)
        assert len(g) == 2
        dependents = g.find_dependents("p")
        assert len(dependents) == 1
        assert dependents[0].id == "c"


class TestHistoryGraphFindByState:
    def test_find_existing_state(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q", result_summary="r", c4_state=(1, 2, 0)))
        g.add(HistoryNode(id="b", query="q", result_summary="r", c4_state=(0, 0, 0)))
        found = g.find_by_state((1, 2, 0))
        assert len(found) == 1
        assert found[0].id == "a"

    def test_find_nonexistent_state(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q", result_summary="r", c4_state=(0, 0, 0)))
        found = g.find_by_state((2, 2, 2))
        assert found == []

    def test_find_multiple_same_state(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q1", result_summary="r", c4_state=(1, 1, 1)))
        g.add(HistoryNode(id="b", query="q2", result_summary="r", c4_state=(1, 1, 1)))
        found = g.find_by_state((1, 1, 1))
        assert len(found) == 2


class TestHistoryGraphAncestors:
    def test_ancestors_no_dependencies(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q", result_summary="r", c4_state=(0, 0, 0)))
        ancestors = g.ancestors("a")
        assert len(ancestors) == 1
        assert ancestors[0].id == "a"

    def test_ancestors_chain(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q", result_summary="r", c4_state=(0, 0, 0)))
        g.add(HistoryNode(id="b", query="q", result_summary="r", c4_state=(0, 0, 0), dependencies=["a"]))
        g.add(HistoryNode(id="c", query="q", result_summary="r", c4_state=(0, 0, 0), dependencies=["b"]))
        ancestors = g.ancestors("c")
        ids = [n.id for n in ancestors]
        assert "c" in ids
        assert "b" in ids
        assert "a" in ids

    def test_ancestors_respects_max_depth(self):
        g = HistoryGraph()
        g.add(HistoryNode(id="a", query="q", result_summary="r", c4_state=(0, 0, 0)))
        g.add(HistoryNode(id="b", query="q", result_summary="r", c4_state=(0, 0, 0), dependencies=["a"]))
        g.add(HistoryNode(id="c", query="q", result_summary="r", c4_state=(0, 0, 0), dependencies=["b"]))
        ancestors = g.ancestors("c", max_depth=2)
        ids = [n.id for n in ancestors]
        assert "c" in ids
        assert "b" in ids
        assert "a" not in ids


class TestHistoryGraphFindByHypothesis:
    def test_find_matching_hypothesis(self):
        g = HistoryGraph()
        g.add(HistoryNode(
            id="a", query="q", result_summary="r", c4_state=(0, 0, 0),
            hypotheses=["gravity is curvature"],
        ))
        found = g.find_by_hypothesis("curvature")
        assert len(found) == 1
        assert found[0].id == "a"


class TestHistoryGraphFindByConclusion:
    def test_find_matching_conclusion(self):
        g = HistoryGraph()
        g.add(HistoryNode(
            id="a", query="q", result_summary="r", c4_state=(0, 0, 0),
            conclusions=["gravity is curvature of spacetime"],
        ))
        found = g.find_by_conclusion("curvature")
        assert len(found) == 1
        assert found[0].id == "a"


class TestHistoryGraphNodes:
    def test_nodes_empty(self):
        g = HistoryGraph()
        assert g.nodes == []

    def test_nodes_timestamp_order(self):
        import time
        g = HistoryGraph()
        older = HistoryNode(
            id="old", query="q", result_summary="r", c4_state=(0, 0, 0),
            timestamp=time.time() - 1000,
        )
        newer = HistoryNode(
            id="new", query="q", result_summary="r", c4_state=(0, 0, 0),
            timestamp=time.time(),
        )
        g.add(older)
        g.add(newer)
        nodes = g.nodes
        assert nodes[0].id == "new"
        assert nodes[1].id == "old"
