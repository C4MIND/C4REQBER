"""
TURBO-CDI: Multi-Agent Core Tests — Agent class (sync interface)
Tests for the Agent class in src/agents/multi/core.py
"""
from __future__ import annotations

import pytest

from src.agents.multi.core import Agent


class TestAgent:
    def test_initialization_defaults(self):
        agent = Agent()
        assert agent.name == "agent"
        assert agent.expertise == "general"
        assert agent.domain == "general"

    def test_initialization_custom(self):
        agent = Agent(name="expert_1", expertise="machine_learning", domain="ai")
        assert agent.name == "expert_1"
        assert agent.expertise == "machine_learning"
        assert agent.domain == "ai"

    def test_process_query_relevant(self):
        agent = Agent(name="ml_expert", expertise="machine_learning")
        result = agent.process({"type": "query", "content": "How does machine learning work?"})

        assert result is not None
        assert result["type"] == "response"
        assert result["agent"] == "ml_expert"
        assert result["confidence"] > 0.1
        assert "Analysis" in result["content"]

    def test_process_query_irrelevant(self):
        agent = Agent(name="ml_expert", expertise="machine_learning")
        result = agent.process({"type": "query", "content": "What is quantum physics?"})

        assert result is not None
        assert result["type"] == "ack"
        assert result["agent"] == "ml_expert"
        assert result["content"] == "Out of scope"

    def test_process_query_general_expertise(self):
        agent = Agent(name="general_agent", expertise="general")
        result = agent.process({"type": "query", "content": "What is machine learning?"})

        assert result is not None
        # With "general" expertise, name is used for keywords: ["general", "agent"]
        # "general" is in "What is general machine learning?" -> relevance > 0
        assert result["agent"] == "general_agent"

    def test_process_query_empty_content(self):
        agent = Agent(name="test", expertise="general")
        result = agent.process({"type": "query", "content": ""})

        assert result is not None
        assert result["type"] == "ack"
        assert result["content"] == "Out of scope"

    def test_process_proposal(self):
        agent = Agent(name="test")
        result = agent.process({"type": "proposal", "content": "New idea"})

        assert result is not None
        assert result["type"] == "vote"
        assert result["agent"] == "test"
        assert result["approval"] == 0.5

    def test_process_critique(self):
        agent = Agent(name="test")
        result = agent.process({"type": "critique", "content": "This is wrong"})

        assert result is not None
        assert result["type"] == "revision"
        assert result["agent"] == "test"
        assert "Consider alternative approach" in result["suggestions"]

    def test_process_data(self):
        agent = Agent(name="test")
        result = agent.process({"type": "data", "content": "Some data"})

        assert result is not None
        assert result["type"] == "analysis"
        assert result["agent"] == "test"
        assert "Data received and processed" in result["insights"]

    def test_process_unknown(self):
        agent = Agent(name="test")
        result = agent.process({"type": "unknown", "content": "Something"})

        assert result is not None
        assert result["type"] == "ack"
        assert result["agent"] == "test"
        assert result["content"] == "Message received"

    def test_process_no_type(self):
        agent = Agent(name="test")
        result = agent.process({"content": "No type specified"})

        assert result is not None
        assert result["type"] == "ack"
        assert result["content"] == "Message received"

    def test_handle_query_with_name_fallback(self):
        agent = Agent(name="physics_expert", expertise="general")
        result = agent.process({"type": "query", "content": "What is physics?"})

        assert result is not None
        assert result["type"] == "response"
        assert "physics" in result["content"].lower()

    def test_handle_query_relevance_calculation(self):
        agent = Agent(name="deep_learning", expertise="deep_learning")
        result = agent.process({"type": "query", "content": "deep learning neural networks"})

        assert result is not None
        assert result["type"] == "response"
        assert result["relevance"] > 0.1
        assert result["confidence"] == pytest.approx(min(1.0, result["relevance"] * 1.5), 0.01)

    def test_handle_query_single_keyword_match(self):
        agent = Agent(name="data_science", expertise="data_science")
        result = agent.process({"type": "query", "content": "data"})

        assert result is not None
        assert result["type"] == "response"
        assert result["relevance"] == pytest.approx(1 / 2, 0.01)

    def test_handle_query_zero_relevance(self):
        agent = Agent(name="crypto", expertise="cryptography")
        result = agent.process({"type": "query", "content": "biology"})

        assert result is not None
        assert result["type"] == "ack"
        assert result["content"] == "Out of scope"
