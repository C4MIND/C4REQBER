from __future__ import annotations

from typing import Any


"""
Reqber v8 — News API Router
GET /v8/news/ticker — live ticker feed
GET /v8/news/{id} — single news item
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from src.news.aggregator import NewsAggregator
from src.news.storage import NewsStorage


logger = logging.getLogger("reqber.api.v8.news")
router = APIRouter(prefix="/news", tags=["v8-news"])


@router.get("/ticker")
async def news_ticker(limit: int = Query(50, ge=1, le=100), refresh: bool = False) -> dict[str, Any]:
    """Return combined news feed for the live ticker. Set refresh=true to re-aggregate."""
    storage = NewsStorage()

    if refresh:
        aggregator = NewsAggregator(storage)
        feed = await aggregator.get_ticker_feed(limit=limit)
        return {"items": feed, "total": len(feed), "refreshed": True}

    cached = storage.get_recent(limit=limit)
    if cached:
        return {"items": cached, "total": len(cached), "refreshed": False}

    aggregator = NewsAggregator(storage)
    feed = await aggregator.get_ticker_feed(limit=limit)
    return {"items": feed, "total": len(feed), "refreshed": True}


@router.get("/{news_id}")
async def news_detail(news_id: int) -> dict[str, Any]:
    """Get a single news feed item by ID."""
    storage = NewsStorage()
    item = storage.get_by_id(news_id)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    return item
