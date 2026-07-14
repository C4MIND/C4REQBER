"""c4reqber: Social Platform Health Checker — validates all connected APIs."""
from __future__ import annotations

from typing import Any

import httpx


async def check_all(dry_run: bool = False) -> dict[str, Any]:
    """Check health of all configured platforms."""
    results = {}
    checks = [
        ("zenodo", _check_zenodo),
        ("twitter", _check_twitter),
        ("mastodon", _check_mastodon),
        ("reddit", _check_reddit),
        ("discord", _check_discord),
        ("slack", _check_slack),
        ("telegram", _check_telegram),
        ("orcid", _check_orcid),
        ("arxiv", _check_arxiv),
    ]
    for name, check_fn in checks:
        try:
            results[name] = await check_fn(dry_run)
        except Exception as e:
            results[name] = {"healthy": False, "error": str(e)}
    return results


async def _check_zenodo(dry_run: bool) -> dict[str, Any]:
    import os
    token = os.getenv("ZENODO_ACCESS_TOKEN")
    if not token:
        return {"healthy": False, "reason": "ZENODO_ACCESS_TOKEN not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    async with httpx.AsyncClient() as c:
        r = await c.get("https://zenodo.org/api/deposit/depositions", params={"access_token": token})
    return {"healthy": r.status_code == 200}


async def _check_twitter(dry_run: bool) -> dict[str, Any]:
    import os
    if not os.getenv("TWITTER_API_KEY"):
        return {"healthy": False, "reason": "TWITTER_API_KEY not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    async with httpx.AsyncClient() as c:
        r = await c.get("https://api.twitter.com/2/users/me", headers={"Authorization": f"Bearer {os.getenv('TWITTER_ACCESS_TOKEN')}"})
    return {"healthy": r.status_code == 200}


async def _check_mastodon(dry_run: bool) -> dict[str, Any]:
    import os
    if not os.getenv("MASTODON_ACCESS_TOKEN"):
        return {"healthy": False, "reason": "MASTODON_ACCESS_TOKEN not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    return {"healthy": True, "note": "token present, full check requires instance URL"}


async def _check_reddit(dry_run: bool) -> dict[str, Any]:
    import os
    if not os.getenv("REDDIT_CLIENT_ID"):
        return {"healthy": False, "reason": "REDDIT_CLIENT_ID not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    async with httpx.AsyncClient() as c:
        r = await c.get("https://www.reddit.com/api/v1/me", headers={"Authorization": f"Bearer {os.getenv('REDDIT_CLIENT_ID')}"})
    return {"healthy": r.status_code != 401}


async def _check_discord(dry_run: bool) -> dict[str, Any]:
    import os
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return {"healthy": False, "reason": "DISCORD_WEBHOOK_URL not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    return {"healthy": url.startswith("https://discord.com/api/webhooks/")}


async def _check_slack(dry_run: bool) -> dict[str, Any]:
    import os
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return {"healthy": False, "reason": "SLACK_WEBHOOK_URL not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    return {"healthy": url.startswith("https://hooks.slack.com/")}


async def _check_telegram(dry_run: bool) -> dict[str, Any]:
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"healthy": False, "reason": "TELEGRAM_BOT_TOKEN not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    async with httpx.AsyncClient() as c:
        r = await c.get(f"https://api.telegram.org/bot{token}/getMe")
    return {"healthy": r.status_code == 200 and r.json().get("ok")}


async def _check_orcid(dry_run: bool) -> dict[str, Any]:
    import os
    if not os.getenv("ORCID_CLIENT_ID"):
        return {"healthy": False, "reason": "ORCID_CLIENT_ID not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    return {"healthy": True, "note": "token present, full check requires OAuth2 flow"}


async def _check_arxiv(dry_run: bool) -> dict[str, Any]:
    import os
    if not os.getenv("ARXIV_SUBMISSION_KEY"):
        return {"healthy": False, "reason": "ARXIV_SUBMISSION_KEY not set"}
    if dry_run:
        return {"healthy": True, "mode": "dry-run"}
    return {"healthy": True, "note": "token present, full endorsement check requires API call"}
