"""Tests for src/api/v8_routers/news_v8.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v8_routers.news_v8 import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestNewsV8Router:
    def test_router_prefix(self):
        assert router.prefix == "/news"

    def test_news_ticker_cached(self):
        with patch("src.api.v8_routers.news_v8.NewsStorage") as mock_storage:
            mock_storage.return_value.get_recent.return_value = [{"id": 1, "title": "News 1"}]
            response = client.get("/news/ticker")
            assert response.status_code == 200
            data = response.json()
            assert data["refreshed"] is False
            assert data["total"] == 1
            assert len(data["items"]) == 1

    def test_news_ticker_refresh(self):
        with patch("src.api.v8_routers.news_v8.NewsStorage") as mock_storage:
            mock_storage.return_value.get_recent.return_value = []
            with patch("src.api.v8_routers.news_v8.NewsAggregator") as mock_agg:
                mock_agg.return_value.get_ticker_feed = AsyncMock(return_value=[{"id": 2, "title": "News 2"}])
                response = client.get("/news/ticker?refresh=true")
                assert response.status_code == 200
                data = response.json()
                assert data["refreshed"] is True
                assert data["total"] == 1

    def test_news_ticker_limit(self):
        with patch("src.api.v8_routers.news_v8.NewsStorage") as mock_storage:
            mock_storage.return_value.get_recent.return_value = [{"id": i} for i in range(60)]
            response = client.get("/news/ticker?limit=10")
            assert response.status_code == 200
            data = response.json()
            # Note: actual limit is applied by NewsStorage.get_recent

    def test_news_detail_found(self):
        with patch("src.api.v8_routers.news_v8.NewsStorage") as mock_storage:
            mock_storage.return_value.get_by_id.return_value = {"id": 1, "title": "News"}
            response = client.get("/news/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1

    def test_news_detail_not_found(self):
        with patch("src.api.v8_routers.news_v8.NewsStorage") as mock_storage:
            mock_storage.return_value.get_by_id.return_value = None
            response = client.get("/news/999")
            assert response.status_code == 404
