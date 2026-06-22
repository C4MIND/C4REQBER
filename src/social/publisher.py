"""c4reqber: Publishing Orchestrator — draft → review → upload → DOI → social posts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.social.profile_manager import UserProfile
from src.social.social_history import SocialHistory


class Publisher:
    """Orchestrates the full preprint publishing pipeline.

    Usage::

        pub = Publisher(dry_run=False)
        result = await pub.publish("2026-05-19_sleep_maintenance")
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.history = SocialHistory()

    async def publish(self, draft_id: str) -> dict[str, Any]:
        """Publish a draft: Zenodo upload → DOI → ORCID → social posts."""
        draft_dir = Path.home() / ".c4reqber" / "drafts" / draft_id
        if not draft_dir.exists():
            return {"error": f"Draft not found: {draft_id}"}

        result: dict[str, Any] = {"draft_id": draft_id, "steps": {}}

        # Step 1: Load draft metadata
        metadata = self._load_metadata(draft_dir)
        profile = UserProfile.load()

        # Step 2: Zenodo upload
        result["steps"]["zenodo"] = await self._publish_zenodo(draft_dir, metadata, profile, draft_id)

        # Step 3: ORCID (if configured)
        if profile.orcid_ids:
            result["steps"]["orcid"] = await self._register_orcid(
                result["steps"]["zenodo"], profile, draft_id
            )

        # Step 4: Generate social posts
        result["steps"]["social"] = await self._generate_posts(
            result["steps"]["zenodo"], draft_id
        )

        return result

    async def _publish_zenodo(self, draft_dir: Path, metadata: dict[str, Any], profile: UserProfile, draft_id: str) -> dict[str, Any]:
        from src.social.zenodo_client import ZenodoClient

        zc = ZenodoClient(dry_run=self.dry_run)

        title = metadata.get("title", draft_id.replace("_", " ").title())
        md_file = draft_dir / "dissertation.md"
        pdf_file = draft_dir / "dissertation.pdf"

        authors = [{"name": a.name, "orcid": a.orcid, "affiliation": a.affiliation} for a in profile.authors if a.name]

        if pdf_file.exists():
            upload_file = pdf_file
        elif md_file.exists():
            upload_file = md_file
        else:
            return {"error": "No dissertation.md or .pdf found in draft"}

        result = await zc.publish_preprint(
            title=title,
            filepath=upload_file,
            description=metadata.get("abstract", "")[:2000],
            creators=authors if authors else None,
        )
        status = "success" if "doi" in result else "failed"
        self.history.record("zenodo_publish", "zenodo", draft_id, status, doi=result.get("doi", ""))
        return result

    async def _register_orcid(self, zenodo_result: dict[str, Any], profile: UserProfile, draft_id: str) -> dict[str, Any]:
        doi = zenodo_result.get("doi", "")
        if not doi or self.dry_run:
            self.history.record("orcid_register", "orcid", draft_id, "skipped" if self.dry_run else "no_doi")
            return {"status": "skipped", "reason": "dry-run" if self.dry_run else "no DOI from Zenodo"}

        try:
            from src.social.orcid_client import ORCIDClient
            oc = ORCIDClient(dry_run=self.dry_run)
            result = await oc.add_work(profile.orcid_ids[0], {
                "title": zenodo_result.get("title", ""),
                "doi": doi,
                "type": "preprint",
            })
            status = "success" if result.get("status") == "ok" else "failed"
            self.history.record("orcid_register", "orcid", draft_id, status)
            return result
        except Exception as e:
            self.history.record("orcid_register", "orcid", draft_id, "failed", error=str(e))
            return {"error": str(e)}

    async def _generate_posts(self, zenodo_result: dict[str, Any], draft_id: str) -> dict[str, Any]:
        """Generate platform-specific posts using i18n templates."""
        from src.social.i18n_templates import detect_language, format_post
        lang = detect_language()
        doi = zenodo_result.get("doi", "")
        title = zenodo_result.get("title", draft_id.replace("_", " ").title())
        url = f"https://doi.org/{doi}" if doi else ""

        posts: dict[str, str] = {}
        if url:
            posts["twitter"] = format_post(lang, "preprint_post", title=title, url=url)[:280]
            posts["mastodon"] = format_post(lang, "preprint_post", title=title, url=url)[:500]
            posts["reddit"] = format_post(lang, "preprint_post", title=title[:300], url=url)
            posts["discord"] = format_post(lang, "preprint_post", title=title, url=url)[:2000]
            posts["slack"] = format_post(lang, "preprint_post", title=title, url=url)[:3000]
        else:
            posts["default"] = format_post(lang, "preprint_no_url", title=title)

        self.history.record("posts_generated", "all", draft_id, "success", post_count=len(posts))
        return {"posts": posts, "language": lang}

    @staticmethod
    def _load_metadata(draft_dir: Path) -> dict[str, Any]:
        meta_file = draft_dir / "metadata.json"
        if meta_file.exists():
            import json
            return json.loads(meta_file.read_text(encoding="utf-8"))
        return {}
