"""c4reqber: Social post dispatcher — routes content to all platform clients."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.config.paths import CONFIG_DIR
from src.social.i18n_templates import detect_language, format_post
from src.social.social_history import SocialHistory


PLATFORM_ALIASES: dict[str, str] = {
    "twitter": "x_twitter",
    "x": "x_twitter",
    "x_twitter": "x_twitter",
    "mastodon": "mastodon",
    "telegram": "telegram",
    "bluesky": "bluesky",
    "reddit": "reddit",
    "discord": "discord",
    "slack": "slack",
    "scimatic": "scimatic",
}

ALL_SOCIAL_PLATFORMS: list[str] = [
    "x_twitter",
    "mastodon",
    "telegram",
    "bluesky",
    "reddit",
    "discord",
    "slack",
]

DRAFTS_DIR = CONFIG_DIR / "drafts"


def normalize_platform(name: str) -> str:
    """Map CLI/MCP aliases to canonical platform ids."""
    key = name.strip().lower().replace("-", "_")
    if key not in PLATFORM_ALIASES:
        raise ValueError(
            f"Unknown platform: {name}. "
            f"Use one of: {', '.join(sorted(set(PLATFORM_ALIASES.values())))}"
        )
    return PLATFORM_ALIASES[key]


def build_post_content(title: str, url: str = "", lang: str | None = None) -> str:
    """Build localized announcement text for social platforms."""
    language = lang or detect_language()
    if url:
        return format_post(language, "preprint_post", title=title, url=url)
    return format_post(language, "preprint_no_url", title=title)


def _load_draft_context(draft_id: str) -> tuple[dict[str, Any], str, str]:
    """Return metadata dict, title, and optional DOI URL for a draft."""
    draft_dir = DRAFTS_DIR / draft_id
    if not draft_dir.exists():
        raise FileNotFoundError(f"Draft not found: {draft_id}")

    metadata: dict[str, Any] = {}
    meta_file = draft_dir / "metadata.json"
    if meta_file.exists():
        metadata = json.loads(meta_file.read_text(encoding="utf-8"))

    title = str(metadata.get("title") or draft_id.replace("_", " ").title())
    doi = str(metadata.get("doi") or "")
    url = f"https://doi.org/{doi}" if doi else ""

    state_file = draft_dir / "draft_state.json"
    if state_file.exists() and not url:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        platforms = state.get("platforms", {})
        zenodo = platforms.get("zenodo", {}) if isinstance(platforms, dict) else {}
        stored_doi = zenodo.get("doi", "") if isinstance(zenodo, dict) else ""
        if stored_doi:
            url = f"https://doi.org/{stored_doi}"

    return metadata, title, url


async def post_to_platform(
    platform: str,
    content: str,
    *,
    dry_run: bool = False,
    title: str = "",
    url: str = "",
    draft_id: str = "",
) -> dict[str, Any]:
    """Post content to a single platform."""
    canonical = normalize_platform(platform)
    history = SocialHistory()

    if dry_run:
        result = {
            "status": "dry_run",
            "platform": canonical,
            "preview": content[:500],
            "message": "Dry run — no API call made",
        }
        history.record("social_post", canonical, draft_id, "dry_run", preview=content[:280])
        return result

    if canonical in {"x_twitter", "mastodon", "telegram", "bluesky", "scimatic"}:
        from src.social.auto_poster import SocialAutoPoster

        poster = SocialAutoPoster().platforms.get(canonical)
        if poster is None:
            result = {"status": "error", "platform": canonical, "message": "Poster not found"}
        elif not poster.available:
            result = {
                "status": "skipped",
                "platform": canonical,
                "message": f"{canonical} credentials not configured",
            }
        else:
            result = await poster.post(content)
    elif canonical == "reddit":
        from src.social.reddit_client import RedditClient

        if not url:
            result = {
                "status": "skipped",
                "platform": canonical,
                "message": "Reddit link posts require a DOI/URL (publish to Zenodo first)",
            }
        else:
            subreddit = os.getenv("REDDIT_SUBREDDIT", "science")
            result = await RedditClient(dry_run=dry_run).submit_link(
                subreddit, title or content[:300], url
            )
    elif canonical == "discord":
        from src.social.discord_webhook import DiscordWebhook

        discord = DiscordWebhook(dry_run=dry_run)
        if url:
            result = await discord.send_preprint(title or content[:256], url, content)
        else:
            result = await discord.send(content)
    elif canonical == "slack":
        from src.social.slack_webhook import SlackWebhook

        slack = SlackWebhook(dry_run=dry_run)
        if url:
            result = await slack.send_preprint(title or content[:256], url, content)
        else:
            result = await slack.send(content)
    else:
        result = {"status": "error", "platform": canonical, "message": "Unsupported platform"}

    status = str(result.get("status", result.get("error", "failed")))
    if status in {"posted", "sent", "ok", "success"}:
        history_status = "success"
    elif status in {"skipped", "preview", "dry_run", "pending_approval"}:
        history_status = status
    elif "error" in result:
        history_status = "failed"
    else:
        history_status = "failed" if result.get("error") else status

    history.record(
        "social_post",
        canonical,
        draft_id,
        history_status,
        url=result.get("url", url),
        message=result.get("message", result.get("error", "")),
    )
    if canonical not in result:
        result["platform"] = canonical
    return result


async def dispatch_social_posts(
    *,
    draft_id: str,
    zenodo_result: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    dry_run: bool = False,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """Post announcement to all configured social platforms after Zenodo upload."""
    meta = metadata or {}
    title = str(
        zenodo_result.get("title") or meta.get("title") or draft_id.replace("_", " ").title()
    )
    doi = str(zenodo_result.get("doi") or meta.get("doi") or "")
    url = f"https://doi.org/{doi}" if doi else ""
    lang = detect_language()
    content = build_post_content(title, url, lang)

    targets = [normalize_platform(p) for p in platforms] if platforms else ALL_SOCIAL_PLATFORMS
    results: dict[str, Any] = {}
    for platform in targets:
        results[platform] = await post_to_platform(
            platform,
            content,
            dry_run=dry_run,
            title=title,
            url=url,
            draft_id=draft_id,
        )

    SocialHistory().record(
        "posts_dispatched",
        "all",
        draft_id,
        "success",
        post_count=len(results),
        language=lang,
    )
    return {"posts": results, "language": lang, "content": content}


async def post_draft(
    draft_id: str,
    *,
    platform: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Post a draft announcement to one or all social platforms."""
    _, title, url = _load_draft_context(draft_id)
    lang = detect_language()
    content = build_post_content(title, url, lang)

    if platform:
        targets = [normalize_platform(platform)]
    else:
        targets = ALL_SOCIAL_PLATFORMS

    results: dict[str, Any] = {}
    for name in targets:
        results[name] = await post_to_platform(
            name,
            content,
            dry_run=dry_run,
            title=title,
            url=url,
            draft_id=draft_id,
        )

    return {
        "draft_id": draft_id,
        "content": content,
        "language": lang,
        "results": results,
    }
