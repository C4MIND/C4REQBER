"""Tests for src/api/v8_routers/scimatic_v8.py"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v8_routers.scimatic_v8 import SciMaticExportRequest, SciMaticSearchResponse, router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestSciMaticV8Router:
    def test_router_prefix(self):
        assert router.prefix == "/scimatic"

    def test_search_scimatic_no_key(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = None
            response = client.get("/scimatic/search?q=quantum")
            assert response.status_code == 501

    def test_search_scimatic_with_key(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = "key"
            mock_client.return_value.search.return_value = {"papers": [{"title": "P1"}], "total": 1}
            response = client.get("/scimatic/search?q=quantum")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["papers"]) == 1

    def test_search_scimatic_with_sources(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = "key"
            mock_client.return_value.search.return_value = {"papers": [{"title": "P1"}], "total": 1}
            response = client.get("/scimatic/search?q=quantum&sources=arxiv,pubmed")
            assert response.status_code == 200

    def test_search_scimatic_error(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = "key"
            mock_client.return_value.search.return_value = {"error": "API error", "status": 503}
            response = client.get("/scimatic/search?q=quantum")
            assert response.status_code == 503

    def test_export_bibtex_no_key(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = None
            response = client.post("/scimatic/export", json={"paper_ids": ["1"]})
            assert response.status_code == 501

    def test_export_bibtex_with_key(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = "key"
            mock_client.return_value.export_bibtex.return_value = "@article{test}"
            response = client.post("/scimatic/export", json={"paper_ids": ["1"]})
            assert response.status_code == 200
            data = response.json()
            assert data["bibtex"] == "@article{test}"

    def test_export_bibtex_empty(self):
        with patch("src.api.v8_routers.scimatic_v8.SciMaticClient") as mock_client:
            mock_client.return_value.api_key = "key"
            mock_client.return_value.export_bibtex.return_value = ""
            response = client.post("/scimatic/export", json={"paper_ids": ["1"]})
            assert response.status_code == 503
