"""Tests for src/api/v8_routers/arxiv_v8.py"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v8_routers.arxiv_v8 import ArxivSearchRequest, router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestArxivV8Router:
    def test_router_prefix(self):
        assert router.prefix == "/arxiv"

    def test_search_papers(self):
        with patch("src.knowledge.arxiv_client.ArxivClient") as mock_client:
            mock_client.return_value.search.return_value = [{"title": "Paper 1"}, {"title": "Paper 2"}]
            response = client.get("/arxiv/search?q=quantum&max_results=10")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["papers"]) == 2

    def test_get_paper_found(self):
        with patch("src.knowledge.arxiv_client.ArxivClient") as mock_client:
            mock_client.return_value.get_paper.return_value = {"title": "Paper 1", "arxiv_id": "1234"}
            response = client.get("/arxiv/paper/1234")
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Paper 1"

    def test_get_paper_not_found(self):
        with patch("src.knowledge.arxiv_client.ArxivClient") as mock_client:
            mock_client.return_value.get_paper.return_value = None
            response = client.get("/arxiv/paper/9999")
            assert response.status_code == 404

    def test_get_full_text_no_key(self):
        with patch("src.knowledge.arxiv_client.ArxivClient") as mock_client:
            mock_client.return_value.api_key = None
            response = client.get("/arxiv/paper/1234/fulltext")
            assert response.status_code == 501

    def test_get_full_text_with_key(self):
        with patch("src.knowledge.arxiv_client.ArxivClient") as mock_client:
            mock_client.return_value.api_key = "key"
            mock_client.return_value.get_full_text.return_value = "Full text content"
            response = client.get("/arxiv/paper/1234/fulltext")
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "Full text content"
