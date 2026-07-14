from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/social", tags=["v8-social"])


class SocialPostRequest(BaseModel):
    """SocialPostRequest."""
    platform: str  # "mastodon", "grok", "scimatic"
    content: str
    confidence: float = 0.0
    media_urls: list[str] | None = None
    schedule_time: str | None = None


class GrokSearchRequest(BaseModel):
    """GrokSearchRequest."""
    query: str
    max_results: int = 20


@router.post("/mastodon/post")
async def post_mastodon(req: SocialPostRequest) -> dict[str, Any]:
    """Post to Mastodon (free)."""
    from src.social.mastodon_client import MastodonClient
    client = MastodonClient()

    if not client.access_token:  # type: ignore[attr-defined]
        raise HTTPException(status_code=501, detail="MASTODON_TOKEN required")

    result = await client.post_status(req.content)  # type: ignore[attr-defined]
    return result


@router.post("/grok/post")
async def post_grok(req: SocialPostRequest) -> dict[str, Any]:
    """Post to X via Grok (paid)."""
    from src.social.grok_client import GrokClient
    client = GrokClient()

    if not client.api_key:
        raise HTTPException(status_code=501, detail="GROK_API_KEY required (X.ai paid tier)")

    result = client.post_tweet(req.content)  # type: ignore[attr-defined]
    return result


@router.get("/grok/search")
async def search_grok(q: str, max_results: int = 20) -> dict[str, Any]:
    """Search X for real-time info."""
    from src.social.grok_client import GrokClient
    client = GrokClient()

    if not client.api_key:
        raise HTTPException(status_code=501, detail="GROK_API_KEY required")

    return client.search_realtime(q, max_results)  # type: ignore[attr-defined]


@router.post("/scimatic/export")
async def export_scimatic(req: dict) -> dict[str, Any]:
    """Export to SciMatic."""
    from src.social.scimatic_export import SciMaticClient
    client = SciMaticClient()
    if not getattr(client, 'api_key', None):
        raise HTTPException(status_code=501, detail="SCIMATIC_API_KEY required")
    result = client.export(req.get("discovery", {}))
    return result


@router.post("/post")
async def create_post(req: SocialPostRequest) -> dict[str, Any]:
    """Create a social media post on the specified platform."""
    if req.platform == "mastodon":
        from src.social.mastodon_client import MastodonClient
        mc = MastodonClient()
        if not mc.access_token:  # type: ignore[attr-defined]
            raise HTTPException(status_code=501, detail="MASTODON_TOKEN required")
        return await mc.post_status(req.content)  # type: ignore[attr-defined]
    elif req.platform in ("twitter", "x"):
        from src.social.twitter_client import TwitterClient
        tc = TwitterClient()
        if not tc.configured:
            raise HTTPException(status_code=501, detail="TWITTER_API_KEY + TWITTER_ACCESS_TOKEN required. Get keys: https://developer.x.com")
        return await tc.post_tweet(req.content)
    elif req.platform == "scimatic":
        return await export_scimatic({"discovery": {"text": req.content}, "format": "json"})
    raise HTTPException(status_code=422, detail=f"Unsupported platform: {req.platform}. Use mastodon, twitter, or scimatic.")


@router.get("/timeline")
async def get_timeline(platform: str = "mastodon", limit: int = 20) -> list:
    """Get social media timeline."""
    if platform == "mastodon":
        from src.social.mastodon_client import MastodonClient
        mc = MastodonClient()
        if not mc.access_token:
            raise HTTPException(status_code=501, detail="MASTODON_ACCESS_TOKEN required")
        return await mc.get_timeline(limit=limit)
    if platform in ("twitter", "x"):
        from src.social.twitter_client import TwitterClient
        tc = TwitterClient()
        if not tc.configured:
            raise HTTPException(status_code=501, detail="TWITTER_API_KEY required")
        return await tc.search_tweets("science research discovery", limit)
    raise HTTPException(status_code=422, detail=f"Unsupported platform: {platform}. Use mastodon or twitter.")


@router.get("/posts/{post_id}")
async def get_post(post_id: str, platform: str = "mastodon") -> dict[str, Any]:
    """Get post by ID."""
    if platform == "mastodon":
        from src.social.mastodon_client import MastodonClient
        mc = MastodonClient()
        if not mc.access_token:
            raise HTTPException(status_code=501, detail="MASTODON_ACCESS_TOKEN required")
        return await mc.get_status(post_id)
    raise HTTPException(status_code=404, detail=f"Post retrieval not supported for: {platform}")
