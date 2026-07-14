from __future__ import annotations


"""Auto-poster to social media platforms with real HTTP API integration."""

import asyncio
import os
from abc import ABC, abstractmethod
from datetime import UTC
from typing import Any

import httpx


class BasePlatformPoster(ABC):
    """Abstract base class for social media platform posters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name."""

    @property
    @abstractmethod
    def max_chars(self) -> int:
        """Maximum character limit for the platform."""

    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if required env vars are set for this platform."""

    def truncate(self, content: str) -> str:
        """Truncate content to platform's max character limit."""
        if len(content) <= self.max_chars:
            return content
        return content[: self.max_chars]

    @abstractmethod
    async def post(self, content: str) -> dict[str, Any]:
        """Post content to the platform. Return result dict."""

    def _error(self, message: str) -> dict[str, Any]:
        return {"status": "error", "platform": self.name, "message": message}

    def _success(self, url: str | None = None, extra: dict | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {"status": "posted", "platform": self.name}
        if url:
            result["url"] = url
        if extra:
            result.update(extra)
        return result

    def _preview(self, content: str, message: str) -> dict[str, Any]:
        return {
            "status": "preview",
            "platform": self.name,
            "message": message,
            "preview": self.truncate(content),
        }


class XTwitterPoster(BasePlatformPoster):
    """X/Twitter v2 API poster."""

    @property
    def name(self) -> str:
        return "x_twitter"

    @property
    def max_chars(self) -> int:
        return 280

    @property
    def available(self) -> bool:
        return bool(
            os.environ.get("X_API_KEY")
            and os.environ.get("X_API_SECRET")
            and os.environ.get("X_ACCESS_TOKEN")
            and os.environ.get("X_ACCESS_SECRET")
            and os.environ.get("X_BEARER_TOKEN")
        )

    async def post(self, content: str) -> dict[str, Any]:
        """Post."""
        if not self.available:
            return self._error("X API credentials not configured (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET, X_BEARER_TOKEN)")

        bearer = os.environ["X_BEARER_TOKEN"]
        text = self.truncate(content)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.com/2/tweets",
                    headers={
                        "Authorization": f"Bearer {bearer}",
                        "Content-Type": "application/json",
                    },
                    json={"text": text},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                tweet_id = data.get("data", {}).get("id")
                url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None
                return self._success(url=url, extra={"tweet_id": tweet_id, "text": text})
        except httpx.HTTPStatusError as e:
            return self._error(f"X API error: {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            return self._error(f"X network error: {e}")
        except Exception as e:
            return self._error(f"X unexpected error: {e}")


class MastodonPoster(BasePlatformPoster):
    """Mastodon API poster."""

    @property
    def name(self) -> str:
        return "mastodon"

    @property
    def max_chars(self) -> int:
        return 500

    @property
    def available(self) -> bool:
        return bool(os.environ.get("MASTODON_ACCESS_TOKEN"))

    @property
    def instance_url(self) -> str:
        return os.environ.get("MASTODON_INSTANCE_URL", "https://mastodon.social")

    async def post(self, content: str) -> dict[str, Any]:
        """Post."""
        if not self.available:
            return self._error("Mastodon access token not configured (MASTODON_ACCESS_TOKEN)")

        token = os.environ["MASTODON_ACCESS_TOKEN"]
        instance = self.instance_url.rstrip("/")
        text = self.truncate(content)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{instance}/api/v1/statuses",
                    headers={"Authorization": f"Bearer {token}"},
                    data={"status": text, "visibility": "public"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                status_id = data.get("id")
                url = data.get("url") or (f"{instance}/@{data.get('account', {}).get('acct')}/{status_id}" if status_id else None)
                return self._success(url=url, extra={"status_id": status_id, "text": text})
        except httpx.HTTPStatusError as e:
            return self._error(f"Mastodon API error: {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            return self._error(f"Mastodon network error: {e}")
        except Exception as e:
            return self._error(f"Mastodon unexpected error: {e}")


class TelegramPoster(BasePlatformPoster):
    """Telegram Bot API poster."""

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def max_chars(self) -> int:
        return 4096

    @property
    def available(self) -> bool:
        return bool(os.environ.get("TELEGRAM_BOT_TOKEN"))

    async def post(self, content: str) -> dict[str, Any]:
        """Post."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not token:
            return self._error("Telegram bot token not configured (TELEGRAM_BOT_TOKEN)")

        if not chat_id:
            return self._preview(
                content,
                "TELEGRAM_CHAT_ID not set — preview only. Set TELEGRAM_CHAT_ID to post for real.",
            )

        text = self.truncate(content)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                msg = data.get("result", {})
                return self._success(
                    url=f"https://t.me/c/{str(chat_id).replace('-100', '')}/{msg.get('message_id')}" if str(chat_id).startswith("-100") else None,
                    extra={"message_id": msg.get("message_id"), "chat_id": chat_id, "text": text},
                )
        except httpx.HTTPStatusError as e:
            return self._error(f"Telegram API error: {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            return self._error(f"Telegram network error: {e}")
        except Exception as e:
            return self._error(f"Telegram unexpected error: {e}")


class SciMaticPoster(BasePlatformPoster):
    """SciMatic API poster (beta/untested)."""

    @property
    def name(self) -> str:
        return "scimatic"

    @property
    def max_chars(self) -> int:
        return 5000

    @property
    def available(self) -> bool:
        return bool(os.environ.get("SCIMATIC_API_KEY"))

    async def post(self, content: str) -> dict[str, Any]:
        """Post."""
        if not self.available:
            return self._preview(content, "SciMatic not configured — set SCIMATIC_API_KEY to enable (beta, untested)")

        api_key = os.environ["SCIMATIC_API_KEY"]
        text = self.truncate(content)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://v2.scimatic.org/literature_survey_api",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"query": text},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return self._success(url=data.get("url"), extra={"response": data, "text": text, "note": "beta, untested"})
        except httpx.HTTPStatusError as e:
            return self._error(f"SciMatic API error: {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            return self._error(f"SciMatic network error: {e}")
        except Exception as e:
            return self._error(f"SciMatic unexpected error: {e}")


class BlueskyPoster(BasePlatformPoster):
    """Bluesky (AT Protocol) poster."""

    @property
    def name(self) -> str:
        return "bluesky"

    @property
    def max_chars(self) -> int:
        return 300

    @property
    def available(self) -> bool:
        return bool(
            os.environ.get("BLUESKY_HANDLE")
            and os.environ.get("BLUESKY_APP_PASSWORD")
        )

    async def post(self, content: str) -> dict[str, Any]:
        """Post."""
        if not self.available:
            return self._error(
                "Bluesky credentials not configured (BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)"
            )

        handle = os.environ["BLUESKY_HANDLE"]
        app_password = os.environ["BLUESKY_APP_PASSWORD"]
        text = self.truncate(content)

        try:
            async with httpx.AsyncClient() as client:
                # Authenticate
                session_resp = await client.post(
                    "https://bsky.social/xrpc/com.atproto.server.createSession",
                    json={"identifier": handle, "password": app_password},
                    timeout=30.0,
                )
                session_resp.raise_for_status()
                session_data = session_resp.json()
                access_jwt = session_data.get("accessJwt")
                did = session_data.get("did")

                if not access_jwt or not did:
                    return self._error("Bluesky auth failed: missing accessJwt or did")

                # Create post record
                from datetime import datetime

                record = {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }

                post_resp = await client.post(
                    "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                    headers={
                        "Authorization": f"Bearer {access_jwt}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "repo": did,
                        "collection": "app.bsky.feed.post",
                        "record": record,
                    },
                    timeout=30.0,
                )
                post_resp.raise_for_status()
                post_data = post_resp.json()
                uri = post_data.get("uri")
                cid = post_data.get("cid")
                url = f"https://bsky.app/profile/{handle}/post/{uri.split('/')[-1]}" if uri else None
                return self._success(
                    url=url,
                    extra={"uri": uri, "cid": cid, "text": text},
                )
        except httpx.HTTPStatusError as e:
            return self._error(
                f"Bluesky API error: {e.response.status_code} — {e.response.text}"
            )
        except httpx.RequestError as e:
            return self._error(f"Bluesky network error: {e}")
        except Exception as e:
            return self._error(f"Bluesky unexpected error: {e}")


class SocialAutoPoster:
    """Router for posting to multiple social media platforms."""

    def __init__(self) -> None:
        self.platforms: dict[str, BasePlatformPoster] = {
            "x_twitter": XTwitterPoster(),
            "mastodon": MastodonPoster(),
            "telegram": TelegramPoster(),
            "bluesky": BlueskyPoster(),
            "scimatic": SciMaticPoster(),
        }

    def post(self, platform: str, content: str, auto_approve: bool = False) -> dict[str, Any]:
        """Post to a single platform (sync wrapper).

        Args:
            platform: Platform name (e.g. "x_twitter", "mastodon").
            content: Content to post.
            auto_approve: If False, returns a pending-approval response instead of posting.
        """
        poster = self.platforms.get(platform)
        if not poster:
            return {"status": "error", "message": f"Unknown platform: {platform}"}
        if not auto_approve:
            return {
                "status": "pending_approval",
                "platform": platform,
                "preview": poster.truncate(content),
                "message": "Human approval required. Use auto_approve=True to skip.",
            }
        return asyncio.run(poster.post(content))

    async def post_all(
        self, content: str, platforms: list[str] | None = None, auto_approve: bool = False
    ) -> list[dict[str, Any]]:
        """Post to all configured platforms in parallel.

        If `platforms` is None, attempts all platforms.
        Only platforms with required env vars will actually post;
        others return preview/error gracefully.

        Args:
            content: Content to post.
            platforms: Optional list of platform names to target.
            auto_approve: If False, all platforms return pending-approval responses.
        """
        targets = platforms or list(self.platforms.keys())
        tasks = []
        for name in targets:
            poster = self.platforms.get(name)
            if poster:
                if not auto_approve:
                    tasks.append(
                        asyncio.sleep(
                            0,
                            result={
                                "status": "pending_approval",
                                "platform": name,
                                "preview": poster.truncate(content),
                                "message": "Human approval required. Use auto_approve=True to skip.",
                            },
                        )
                    )
                else:
                    tasks.append(poster.post(content))
            else:
                tasks.append(asyncio.sleep(0, result={"status": "error", "message": f"Unknown platform: {name}"}))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if isinstance(r, dict) else {"status": "error", "message": str(r)}
            for r in results
        ]


AUTHOR_PROFILES = {
    "selyutin_i": {
        "name": "Ilya Selyutin",
        "orcid": "0009-0009-8545-5875",
        "arxiv": "https://arxiv.org/a/selyutin_i",
        "researchgate": "https://researchgate.net/profile/Ilya-Selyutin",
        "gitlab": "https://gitlab.com/cognitive-functors",
        "github": "https://github.com/c4-meta",
        "reddit": "https://reddit.com/user/c44tcdi",
    },
    "kovalev_n": {
        "name": "Nikolay Kovalev",
        "orcid": "https://orcid.org/0000-0000-0000-0000",
        "arxiv": "https://arxiv.org/a/kovalev_n",
        "researchgate": "https://researchgate.net/profile/Nikolay-Kovalev",
        "gitlab": "",
        "github": "",
        "reddit": "",
    },
}


def get_citation_block(author_profiles: dict | None = None) -> str:
    """Generate citation block with author profiles."""
    profiles = author_profiles or AUTHOR_PROFILES
    s = profiles["selyutin_i"]
    k = profiles["kovalev_n"]
    citation = (
        "\\section*{Software Attribution}\n"
        "This discovery was made using \\textbf{c44tcdi v4.1.0} — C4-META Cognitive Architecture.\n\n"
        "\\textbf{Authors:}\n"
        f"Selyutin I. \\orcidlink{{{s['orcid']}}}"
        f" — primary developer\n"
        f"Kovalev N.I. \\orcidlink{{{k['orcid']}}}"
        f" — theoretical model\n\n"
        "\\textbf{Author Profiles:}\n"
    )
    for _key, profile in profiles.items():
        citation += f"\\textbf{{{profile['name']}}}: "
        links = []
        if profile.get("orcid"):
            links.append(f"ORCID: {profile['orcid']}")
        if profile.get("arxiv"):
            links.append(f"arXiv: {profile['arxiv']}")
        if profile.get("github"):
            links.append(f"GitHub: {profile['github']}")
        if profile.get("gitlab"):
            links.append(f"GitLab: {profile['gitlab']}")
        if profile.get("researchgate"):
            links.append(f"ResearchGate: {profile['researchgate']}")
        if profile.get("reddit"):
            links.append(f"Reddit: {profile['reddit']}")
        citation += " | ".join(links) + "\n"
    return citation
