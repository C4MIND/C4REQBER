"""c4reqber: i18n Social Post Templates — 7 languages."""
from __future__ import annotations


TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "preprint_post": "New preprint: {title} — {url} #c4reqber",
        "preprint_no_url": "New preprint: {title} #c4reqber",
        "published": "Published: {title} — DOI: {doi}",
        "review_request": "{title} ({words} words) — ready for review",
        "review_approved": "✅ Approved: {title}",
        "review_rejected": "❌ Rejected: {title}",
        "health_ok": "● {platform}: connected",
        "health_fail": "○ {platform}: {reason}",
    },
    "ru": {
        "preprint_post": "Новый препринт: {title} — {url} #c4reqber",
        "preprint_no_url": "Новый препринт: {title} #c4reqber",
        "published": "Опубликовано: {title} — DOI: {doi}",
        "review_request": "{title} ({words} слов) — готово к рецензии",
        "review_approved": "✅ Одобрено: {title}",
        "review_rejected": "❌ Отклонено: {title}",
        "health_ok": "● {platform}: подключено",
        "health_fail": "○ {platform}: {reason}",
    },
    "zh": {
        "preprint_post": "新预印本：{title} — {url} #c4reqber",
        "preprint_no_url": "新预印本：{title} #c4reqber",
        "published": "已发布：{title} — DOI：{doi}",
        "review_request": "{title}（{words}字）— 待审阅",
        "review_approved": "✅ 已批准：{title}",
        "review_rejected": "❌ 已拒绝：{title}",
        "health_ok": "● {platform}：已连接",
        "health_fail": "○ {platform}：{reason}",
    },
    "ja": {
        "preprint_post": "新しいプレプリント: {title} — {url} #c4reqber",
        "preprint_no_url": "新しいプレプリント: {title} #c4reqber",
        "published": "公開済み: {title} — DOI: {doi}",
        "review_request": "{title}（{words}語）— レビュー待ち",
        "review_approved": "✅ 承認済み: {title}",
        "review_rejected": "❌ 却下: {title}",
        "health_ok": "● {platform}: 接続済み",
        "health_fail": "○ {platform}: {reason}",
    },
    "de": {
        "preprint_post": "Neues Preprint: {title} — {url} #c4reqber",
        "preprint_no_url": "Neues Preprint: {title} #c4reqber",
        "published": "Veröffentlicht: {title} — DOI: {doi}",
        "review_request": "{title} ({words} Wörter) — bereit zur Prüfung",
        "review_approved": "✅ Genehmigt: {title}",
        "review_rejected": "❌ Abgelehnt: {title}",
        "health_ok": "● {platform}: verbunden",
        "health_fail": "○ {platform}: {reason}",
    },
    "ar": {
        "preprint_post": "نسخة أولية جديدة: {title} — {url} #c4reqber",
        "preprint_no_url": "نسخة أولية جديدة: {title} #c4reqber",
        "published": "تم النشر: {title} — DOI: {doi}",
        "review_request": "{title} ({words} كلمة) — جاهز للمراجعة",
        "review_approved": "✅ تمت الموافقة: {title}",
        "review_rejected": "❌ مرفوض: {title}",
        "health_ok": "● {platform}: متصل",
        "health_fail": "○ {platform}: {reason}",
    },
    "hi": {
        "preprint_post": "नया प्रीप्रिंट: {title} — {url} #c4reqber",
        "preprint_no_url": "नया प्रीप्रिंट: {title} #c4reqber",
        "published": "प्रकाशित: {title} — DOI: {doi}",
        "review_request": "{title} ({words} शब्द) — समीक्षा के लिए तैयार",
        "review_approved": "✅ स्वीकृत: {title}",
        "review_rejected": "❌ अस्वीकृत: {title}",
        "health_ok": "● {platform}: जुड़ा हुआ",
        "health_fail": "○ {platform}: {reason}",
    },
}


def get_template(lang: str, key: str) -> str:
    """Get a translated template string."""
    return TEMPLATES.get(lang, TEMPLATES["en"]).get(key, TEMPLATES["en"].get(key, key))


def detect_language() -> str:
    """Detect user language from environment."""
    import os
    lang_raw = os.environ.get("LANG", os.environ.get("LC_ALL", "en_US.UTF-8"))
    lang = lang_raw.split(".")[0].split("_")[0][:2]
    return lang if lang in TEMPLATES else "en"


def format_post(lang: str, key: str, **kwargs: str | int) -> str:
    """Format a translated template with variables."""
    template = get_template(lang, key)
    return template.format(**kwargs)
