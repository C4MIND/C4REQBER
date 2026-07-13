#!/usr/bin/env python3
"""Sync landing i18n keys for Wave A–C docs consistency (all 7 langs)."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "landing" / "i18n"

# Keys updated/added for docs + landing honesty (Jul 2026).
PATCHES: dict[str, dict[str, str]] = {
    "en": {
        "keys_h2_setup": "User secrets store",
        "keys_setup_note": "<code>blast init</code> or <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>. TUI: <code>Ctrl+Shift+K</code>. Override: <code>C4REQBER_CONFIG</code>. Never commit secrets.",
        "keys_intro": "c4reqber is free (AGPL-3.0) — you only pay upstream APIs. Minimum: <code>OPENROUTER_API_KEY</code> in <code>secrets.env</code> or env. TUI Setup Hub: <code>Ctrl+Shift+K</code>.",
        "gs_setup": "Packages vs API keys (different commands):",
        "gs_setup_packages": "<code>blast setup</code> — scientific packages (GROMACS, OpenMM, …)",
        "gs_setup_keys": "<code>blast init</code> or <code>blast config keys</code> — API keys → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub (<code>Ctrl+Shift+K</code>), <code>secrets.env</code>, OpenRouter + 20+ science APIs. Full guide on GitLab.",
        "home_tui_tag_setup": "Ctrl+Shift+K: Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S: Social publish",
        "home_tui_tag_agenda": "Shift+A: Research agenda",
        "home_tui_tag_models": "Ctrl+Shift+M: Models & council",
        "home_social_tui_hint": "TUI: <code>Ctrl+Shift+S</code> — drafts, health check, publish",
        "home_social_post_hint": "CLI: <code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": 'Full guide: <a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a> on GitLab',
        "home_social_platform_note": "Zenodo = real DOI upload. arXiv = LaTeX package only (no auto-submit). bioRxiv = not wired yet. Each social channel skipped without API key.",
        "doc_card_social_title": "Social Publishing",
        "doc_card_social_desc": "Zenodo, ORCID, Mastodon, Bluesky, Telegram, Reddit, Discord, Slack — setup + blast social post. Honest limits documented.",
        "gs_cmd_config_keys": "<code>blast config keys</code> — manage ~/.c4reqber/secrets.env",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">Social publishing guide</a> — Zenodo, ORCID, Mastodon, Bluesky, …',
        "foot_tests": "9,924 tests collected · regression-gated mypy",
        "arch_layer_tui_desc": "Go TUI v9 feed cockpit (<code>blast tui</code>) — command palette, sim surface, agenda, models, API keys, social overlays.",
        "gs_h2_tui": "TUI v9 overlays",
        "gs_tui_intro": "Launch <code>blast tui</code>. Key overlays (also in <code>:</code> palette):",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — API Keys Setup Hub</li><li><code>Ctrl+Shift+S</code> — Social publishing</li><li><code>Shift+A</code> — Research agenda</li><li><code>Ctrl+Shift+M</code> — Models &amp; council</li><li><code>Ctrl+Shift+C</code> — Sim capabilities</li><li><code>:</code> — Command palette</li></ul>",
    },
    "ru": {
        "keys_h2_setup": "Хранилище секретов",
        "keys_setup_note": "<code>blast init</code> или <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>. TUI: <code>Ctrl+Shift+K</code>. Переопределение: <code>C4REQBER_CONFIG</code>. Не коммитьте секреты.",
        "keys_intro": "c4reqber бесплатен (AGPL-3.0) — платите только за API. Минимум: <code>OPENROUTER_API_KEY</code> в <code>secrets.env</code> или env. Setup Hub в TUI: <code>Ctrl+Shift+K</code>.",
        "gs_setup": "Пакеты и API-ключи (разные команды):",
        "gs_setup_packages": "<code>blast setup</code> — научные пакеты (GROMACS, OpenMM, …)",
        "gs_setup_keys": "<code>blast init</code> или <code>blast config keys</code> — ключи → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub (<code>Ctrl+Shift+K</code>), <code>secrets.env</code>, OpenRouter + 20+ научных API. Полный гайд на GitLab.",
        "home_tui_tag_setup": "Ctrl+Shift+K: Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S: Соцпубликация",
        "home_tui_tag_agenda": "Shift+A: Повестка исследования",
        "home_tui_tag_models": "Ctrl+Shift+M: Модели и council",
        "home_social_tui_hint": "TUI: <code>Ctrl+Shift+S</code> — черновики, health, публикация",
        "home_social_post_hint": "CLI: <code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": 'Гайд: <a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a> на GitLab',
        "home_social_platform_note": "Zenodo = реальная загрузка DOI. arXiv = только LaTeX-пакет (без авто-submit). bioRxiv = пока не подключён. Канал без ключа пропускается.",
        "doc_card_social_title": "Социальная публикация",
        "doc_card_social_desc": "Zenodo, ORCID, Mastodon, Bluesky, Telegram, Reddit, Discord, Slack — настройка + blast social post. Честные ограничения в доке.",
        "gs_cmd_config_keys": "<code>blast config keys</code> — ~/.c4reqber/secrets.env",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">Гайд по соцпубликации</a> — Zenodo, ORCID, Mastodon, Bluesky, …',
        "foot_tests": "9 924 теста · mypy с регрессионным гейтом",
        "arch_layer_tui_desc": "Go TUI v9 (<code>blast tui</code>) — лента, palette, sim, agenda, модели, ключи, соцпубликация.",
        "gs_h2_tui": "Оверлеи TUI v9",
        "gs_tui_intro": "Запуск <code>blast tui</code>. Горячие клавиши (и в palette <code>:</code>):",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — Setup Hub (API-ключи)</li><li><code>Ctrl+Shift+S</code> — Соцпубликация</li><li><code>Shift+A</code> — Повестка исследования</li><li><code>Ctrl+Shift+M</code> — Модели и council</li><li><code>Ctrl+Shift+C</code> — Sim capabilities</li><li><code>:</code> — Command palette</li></ul>",
    },
    "zh": {
        "keys_h2_setup": "用户密钥存储",
        "keys_setup_note": "<code>blast init</code> 或 <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>。TUI：<code>Ctrl+Shift+K</code>。覆盖目录：<code>C4REQBER_CONFIG</code>。切勿提交密钥。",
        "keys_intro": "c4reqber 免费（AGPL-3.0）— 仅向上游 API 付费。最低要求：<code>secrets.env</code> 或环境中的 <code>OPENROUTER_API_KEY</code>。TUI Setup Hub：<code>Ctrl+Shift+K</code>。",
        "gs_setup": "软件包与 API 密钥（不同命令）：",
        "gs_setup_packages": "<code>blast setup</code> — 科学计算包（GROMACS、OpenMM 等）",
        "gs_setup_keys": "<code>blast init</code> 或 <code>blast config keys</code> — 密钥 → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub（<code>Ctrl+Shift+K</code>）、<code>secrets.env</code>、OpenRouter 及 20+ 科学 API。完整指南见 GitLab。",
        "home_tui_tag_setup": "Ctrl+Shift+K：Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S：社交发布",
        "home_tui_tag_agenda": "Shift+A：研究议程",
        "home_tui_tag_models": "Ctrl+Shift+M：模型与 council",
        "home_social_tui_hint": "TUI：<code>Ctrl+Shift+S</code> — 草稿、健康检查、发布",
        "home_social_post_hint": "CLI：<code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": '完整指南：<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a>（GitLab）',
        "home_social_platform_note": "Zenodo = 真实 DOI 上传。arXiv = 仅 LaTeX 包（无自动提交）。bioRxiv = 尚未接入。无 API 密钥的频道会跳过。",
        "doc_card_social_title": "社交发布",
        "doc_card_social_desc": "Zenodo、ORCID、Mastodon、Bluesky、Telegram、Reddit、Discord、Slack — 配置 + blast social post。限制见文档。",
        "gs_cmd_config_keys": "<code>blast config keys</code> — 管理 ~/.c4reqber/secrets.env",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">社交发布指南</a> — Zenodo、ORCID、Mastodon、Bluesky…',
        "foot_tests": "9,924 个测试 · 回归门控 mypy",
        "arch_layer_tui_desc": "Go TUI v9 信息流驾驶舱（<code>blast tui</code>）— 命令面板、仿真、议程、模型、密钥、社交叠加层。",
        "gs_h2_tui": "TUI v9 叠加层",
        "gs_tui_intro": "运行 <code>blast tui</code>。快捷键（亦可通过 <code>:</code> 面板）：",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — API 密钥 Setup Hub</li><li><code>Ctrl+Shift+S</code> — 社交发布</li><li><code>Shift+A</code> — 研究议程</li><li><code>Ctrl+Shift+M</code> — 模型与 council</li><li><code>Ctrl+Shift+C</code> — 仿真能力</li><li><code>:</code> — 命令面板</li></ul>",
    },
    "ja": {
        "keys_h2_setup": "ユーザーシークレット保存",
        "keys_setup_note": "<code>blast init</code> または <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>。TUI: <code>Ctrl+Shift+K</code>。上書き: <code>C4REQBER_CONFIG</code>。シークレットをコミットしないでください。",
        "keys_intro": "c4reqber は無料（AGPL-3.0）— 支払いは上流 API のみ。最低限: <code>secrets.env</code> または環境変数の <code>OPENROUTER_API_KEY</code>。TUI Setup Hub: <code>Ctrl+Shift+K</code>。",
        "gs_setup": "パッケージと API キー（別コマンド）:",
        "gs_setup_packages": "<code>blast setup</code> — 科学パッケージ（GROMACS、OpenMM など）",
        "gs_setup_keys": "<code>blast init</code> または <code>blast config keys</code> — キー → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub（<code>Ctrl+Shift+K</code>）、<code>secrets.env</code>、OpenRouter + 20+ 科学 API。完全ガイドは GitLab。",
        "home_tui_tag_setup": "Ctrl+Shift+K: Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S: ソーシャル投稿",
        "home_tui_tag_agenda": "Shift+A: 研究アジェンダ",
        "home_tui_tag_models": "Ctrl+Shift+M: モデル & council",
        "home_social_tui_hint": "TUI: <code>Ctrl+Shift+S</code> — ドラフト、ヘルスチェック、公開",
        "home_social_post_hint": "CLI: <code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": '完全ガイド: <a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a>（GitLab）',
        "home_social_platform_note": "Zenodo = 実 DOI アップロード。arXiv = LaTeX パッケージのみ（自動投稿なし）。bioRxiv = 未接続。API キーなしのチャネルはスキップ。",
        "doc_card_social_title": "ソーシャル公開",
        "doc_card_social_desc": "Zenodo、ORCID、Mastodon、Bluesky、Telegram、Reddit、Discord、Slack — 設定 + blast social post。制限はドキュメント参照。",
        "gs_cmd_config_keys": "<code>blast config keys</code> — ~/.c4reqber/secrets.env を管理",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">ソーシャル公開ガイド</a> — Zenodo、ORCID、Mastodon、Bluesky…',
        "foot_tests": "9,924 テスト収集 · 回帰ゲート mypy",
        "arch_layer_tui_desc": "Go TUI v9 フィードコックピット（<code>blast tui</code>）— パレット、シム、アジェンダ、モデル、キー、ソーシャル。",
        "gs_h2_tui": "TUI v9 オーバーレイ",
        "gs_tui_intro": "<code>blast tui</code> を起動。ショートカット（<code>:</code> パレットにもあり）:",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — API キー Setup Hub</li><li><code>Ctrl+Shift+S</code> — ソーシャル公開</li><li><code>Shift+A</code> — 研究アジェンダ</li><li><code>Ctrl+Shift+M</code> — モデル &amp; council</li><li><code>Ctrl+Shift+C</code> — シム機能</li><li><code>:</code> — コマンドパレット</li></ul>",
    },
    "de": {
        "keys_h2_setup": "Benutzer-Secrets",
        "keys_setup_note": "<code>blast init</code> oder <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>. TUI: <code>Ctrl+Shift+K</code>. Override: <code>C4REQBER_CONFIG</code>. Keine Secrets committen.",
        "keys_intro": "c4reqber ist kostenlos (AGPL-3.0) — Sie zahlen nur Upstream-APIs. Minimum: <code>OPENROUTER_API_KEY</code> in <code>secrets.env</code> oder env. TUI Setup Hub: <code>Ctrl+Shift+K</code>.",
        "gs_setup": "Pakete vs. API-Keys (verschiedene Befehle):",
        "gs_setup_packages": "<code>blast setup</code> — Wissenschaftspakete (GROMACS, OpenMM, …)",
        "gs_setup_keys": "<code>blast init</code> oder <code>blast config keys</code> — Keys → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub (<code>Ctrl+Shift+K</code>), <code>secrets.env</code>, OpenRouter + 20+ Wissenschafts-APIs. Vollständiger Guide auf GitLab.",
        "home_tui_tag_setup": "Ctrl+Shift+K: Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S: Social Publish",
        "home_tui_tag_agenda": "Shift+A: Forschungsagenda",
        "home_tui_tag_models": "Ctrl+Shift+M: Modelle & Council",
        "home_social_tui_hint": "TUI: <code>Ctrl+Shift+S</code> — Entwürfe, Health-Check, Publish",
        "home_social_post_hint": "CLI: <code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": 'Vollständiger Guide: <a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a> auf GitLab',
        "home_social_platform_note": "Zenodo = echter DOI-Upload. arXiv = nur LaTeX-Paket (kein Auto-Submit). bioRxiv = noch nicht angebunden. Kanal ohne API-Key wird übersprungen.",
        "doc_card_social_title": "Social Publishing",
        "doc_card_social_desc": "Zenodo, ORCID, Mastodon, Bluesky, Telegram, Reddit, Discord, Slack — Setup + blast social post. Ehrliche Limits dokumentiert.",
        "gs_cmd_config_keys": "<code>blast config keys</code> — ~/.c4reqber/secrets.env verwalten",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">Social-Publishing-Guide</a> — Zenodo, ORCID, Mastodon, Bluesky, …',
        "foot_tests": "9.924 Tests gesammelt · regression-gated mypy",
        "arch_layer_tui_desc": "Go TUI v9 Feed-Cockpit (<code>blast tui</code>) — Palette, Sim, Agenda, Modelle, Keys, Social-Overlays.",
        "gs_h2_tui": "TUI v9 Overlays",
        "gs_tui_intro": "<code>blast tui</code> starten. Shortcuts (auch in <code>:</code>-Palette):",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — API-Keys Setup Hub</li><li><code>Ctrl+Shift+S</code> — Social Publishing</li><li><code>Shift+A</code> — Forschungsagenda</li><li><code>Ctrl+Shift+M</code> — Modelle &amp; Council</li><li><code>Ctrl+Shift+C</code> — Sim-Fähigkeiten</li><li><code>:</code> — Command Palette</li></ul>",
    },
    "ar": {
        "keys_h2_setup": "مخزن الأسرار",
        "keys_setup_note": "<code>blast init</code> أو <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>. TUI: <code>Ctrl+Shift+K</code>. التجاوز: <code>C4REQBER_CONFIG</code>. لا تُرسل الأسرار إلى git.",
        "keys_intro": "c4reqber مجاني (AGPL-3.0) — تدفع فقط لـ APIs. الحد الأدنى: <code>OPENROUTER_API_KEY</code> في <code>secrets.env</code> أو البيئة. Setup Hub في TUI: <code>Ctrl+Shift+K</code>.",
        "gs_setup": "الحزم مقابل مفاتيح API (أوامر مختلفة):",
        "gs_setup_packages": "<code>blast setup</code> — حزم علمية (GROMACS، OpenMM، …)",
        "gs_setup_keys": "<code>blast init</code> أو <code>blast config keys</code> — المفاتيح → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub (<code>Ctrl+Shift+K</code>)، <code>secrets.env</code>، OpenRouter + 20+ API علمية. الدليل الكامل على GitLab.",
        "home_tui_tag_setup": "Ctrl+Shift+K: Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S: نشر اجتماعي",
        "home_tui_tag_agenda": "Shift+A: أجندة البحث",
        "home_tui_tag_models": "Ctrl+Shift+M: النماذج والمجلس",
        "home_social_tui_hint": "TUI: <code>Ctrl+Shift+S</code> — مسودات، فحص صحة، نشر",
        "home_social_post_hint": "CLI: <code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": 'الدليل الكامل: <a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a> على GitLab',
        "home_social_platform_note": "Zenodo = رفع DOI حقيقي. arXiv = حزمة LaTeX فقط (بدون إرسال تلقائي). bioRxiv = غير موصول بعد. كل قناة بدون مفتاح تُتخطى.",
        "doc_card_social_title": "النشر الاجتماعي",
        "doc_card_social_desc": "Zenodo، ORCID، Mastodon، Bluesky، Telegram، Reddit، Discord، Slack — إعداد + blast social post. القيود موثقة بصدق.",
        "gs_cmd_config_keys": "<code>blast config keys</code> — إدارة ~/.c4reqber/secrets.env",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">دليل النشر الاجتماعي</a> — Zenodo، ORCID، Mastodon، Bluesky، …',
        "foot_tests": "9,924 اختبارًا · mypy ببوابة انحدار",
        "arch_layer_tui_desc": "Go TUI v9 (<code>blast tui</code>) — لوحة أوامر، محاكاة، أجندة، نماذج، مفاتيح، نشر اجتماعي.",
        "gs_h2_tui": "طبقات TUI v9",
        "gs_tui_intro": "شغّل <code>blast tui</code>. الاختصارات (وفي palette <code>:</code>):",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — Setup Hub للمفاتيح</li><li><code>Ctrl+Shift+S</code> — النشر الاجتماعي</li><li><code>Shift+A</code> — أجندة البحث</li><li><code>Ctrl+Shift+M</code> — النماذج والمجلس</li><li><code>Ctrl+Shift+C</code> — قدرات المحاكاة</li><li><code>:</code> — لوحة الأوامر</li></ul>",
    },
    "hi": {
        "keys_h2_setup": "उपयोगकर्ता सीक्रेट स्टोर",
        "keys_setup_note": "<code>blast init</code> या <code>blast config keys --assign KEY=value</code> → <code>~/.c4reqber/secrets.env</code>। TUI: <code>Ctrl+Shift+K</code>। ओवरराइड: <code>C4REQBER_CONFIG</code>। सीक्रेट commit न करें।",
        "keys_intro": "c4reqber मुफ्त (AGPL-3.0) — केवल upstream API के लिए भुगतान। न्यूनतम: <code>secrets.env</code> या env में <code>OPENROUTER_API_KEY</code>। TUI Setup Hub: <code>Ctrl+Shift+K</code>।",
        "gs_setup": "पैकेज बनाम API कुंजी (अलग कमांड):",
        "gs_setup_packages": "<code>blast setup</code> — वैज्ञानिक पैकेज (GROMACS, OpenMM, …)",
        "gs_setup_keys": "<code>blast init</code> या <code>blast config keys</code> — कुंजियाँ → <code>~/.c4reqber/secrets.env</code>",
        "doc_card_keys_desc": "Setup Hub (<code>Ctrl+Shift+K</code>), <code>secrets.env</code>, OpenRouter + 20+ विज्ञान API। पूर्ण गाइड GitLab पर।",
        "home_tui_tag_setup": "Ctrl+Shift+K: Setup Hub",
        "home_tui_tag_social": "Ctrl+Shift+S: सोशल प्रकाशन",
        "home_tui_tag_agenda": "Shift+A: शोध एजेंडा",
        "home_tui_tag_models": "Ctrl+Shift+M: मॉडल और council",
        "home_social_tui_hint": "TUI: <code>Ctrl+Shift+S</code> — ड्राफ्ट, health, प्रकाशन",
        "home_social_post_hint": "CLI: <code>blast social publish</code> · <code>blast social post --id … --platform mastodon</code>",
        "home_social_doc": 'पूर्ण गाइड: <a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" target="_blank" rel="noopener">docs/SOCIAL_PUBLISHING.md</a> GitLab पर',
        "home_social_platform_note": "Zenodo = वास्तविक DOI अपलोड। arXiv = केवल LaTeX पैकेज (ऑटो-सबमिट नहीं)। bioRxiv = अभी जुड़ा नहीं। बिना API कुंजी चैनल छोड़ दिया जाता है।",
        "doc_card_social_title": "सोशल प्रकाशन",
        "doc_card_social_desc": "Zenodo, ORCID, Mastodon, Bluesky, Telegram, Reddit, Discord, Slack — सेटअप + blast social post। सीमाएँ दस्तावेज़ में।",
        "gs_cmd_config_keys": "<code>blast config keys</code> — ~/.c4reqber/secrets.env प्रबंधित करें",
        "gs_cmd_social": "<code>blast social publish</code> / <code>blast social post</code>",
        "gs_next_social": '<a href="https://gitlab.com/cognitive-functors/turbo-cdi/-/blob/main/docs/SOCIAL_PUBLISHING.md" rel="noopener noreferrer" target="_blank">सोशल प्रकाशन गाइड</a> — Zenodo, ORCID, Mastodon, Bluesky, …',
        "foot_tests": "9,924 परीक्षण · regression-gated mypy",
        "arch_layer_tui_desc": "Go TUI v9 फीड कॉकपिट (<code>blast tui</code>) — palette, sim, agenda, models, keys, social overlays।",
        "gs_h2_tui": "TUI v9 ओवरले",
        "gs_tui_intro": "<code>blast tui</code> चलाएँ। शॉर्टकट (<code>:</code> palette में भी):",
        "gs_tui_keys_html": "<ul><li><code>Ctrl+Shift+K</code> — API Keys Setup Hub</li><li><code>Ctrl+Shift+S</code> — सोशल प्रकाशन</li><li><code>Shift+A</code> — शोध एजेंडा</li><li><code>Ctrl+Shift+M</code> — मॉडल और council</li><li><code>Ctrl+Shift+C</code> — Sim capabilities</li><li><code>:</code> — Command palette</li></ul>",
    },
}


def main() -> None:
    en_path = I18N / "en.json"
    en_data: dict[str, str] = json.loads(en_path.read_text(encoding="utf-8"))
    en_data.update(PATCHES["en"])
    en_path.write_text(json.dumps(en_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for lang, patch in PATCHES.items():
        if lang == "en":
            continue
        path = I18N / f"{lang}.json"
        data: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
        data.update(patch)
        # Ensure any new en-only keys fall back to English text
        for key, val in PATCHES["en"].items():
            data.setdefault(key, val)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {path.name} (+{len(patch)} keys)")


if __name__ == "__main__":
    main()
