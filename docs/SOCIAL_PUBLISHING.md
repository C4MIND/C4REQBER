# Social Publishing Guide

c4reqber can publish discovery dissertations to Zenodo (DOI), register works in ORCID, and announce preprints on social platforms.

This guide covers setup, the draft workflow, and all entry points (CLI, MCP, TUI v9).

## Overview

```
Discovery pipeline → dissertation saved → ~/.c4reqber/drafts/<id>/
                                              ↓
                         blast social publish --id <id>
                                              ↓
                    Zenodo (DOI) → ORCID → social platforms
```

**What works end-to-end today:**

| Channel | Upload / post | Notes |
|---------|---------------|-------|
| Zenodo | Real API upload | Requires `ZENODO_ACCESS_TOKEN` |
| ORCID | Partial | Client credentials; full user OAuth may be needed for your account |
| Mastodon | Real post | `MASTODON_ACCESS_TOKEN` |
| Twitter/X | Real post | `X_*` env vars (see below) |
| Bluesky | Real post | `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` |
| Telegram | Real post | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| Reddit | Link post | OAuth credentials + `REDDIT_SUBREDDIT` (default: `science`); needs DOI URL |
| Discord | Webhook | `DISCORD_WEBHOOK_URL` |
| Slack | Webhook | `SLACK_WEBHOOK_URL` |
| arXiv | Package generation only | LaTeX bundle on disk; no auto-upload in publish flow |
| bioRxiv | Not implemented | Listed on landing for roadmap visibility |

Platforms without configured credentials are **skipped** (not failed). Use `blast social health` to see what is ready.

## Quick start

### 1. Configure credentials

**Primary store:** `~/.c4reqber/secrets.env` via `blast init` or `blast config keys --assign KEY=value` (TUI: `Ctrl+Shift+K`).

For Docker/dev you can also use project `.env` — process env always wins.

```bash
# Example (saved to secrets.env)
blast config keys --assign ZENODO_ACCESS_TOKEN=your_zenodo_token
blast config keys --assign MASTODON_ACCESS_TOKEN=your_token
# … set only channels you need — see docs/API_KEYS.md
```

Legacy `.env` copy still works for local development:

```bash
cp .env.example .env
# Archive
ZENODO_ACCESS_TOKEN=your_zenodo_token
ORCID_CLIENT_ID=
ORCID_CLIENT_SECRET=

# Social (set only what you need)
MASTODON_ACCESS_TOKEN=
MASTODON_INSTANCE_URL=https://mastodon.social
BLUESKY_HANDLE=
BLUESKY_APP_PASSWORD=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DISCORD_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
REDDIT_SUBREDDIT=science

# X/Twitter (SocialAutoPoster path)
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_SECRET=
X_BEARER_TOKEN=
```

Run `blast social setup` for a quick env-var checklist in the terminal.

### 2. Run a discovery

After `blast solve`, `blast turbo`, or TUI discovery, a draft is created automatically:

```
~/.c4reqber/drafts/2026-07-13_your_topic/
├── dissertation.md
├── metadata.json
└── draft_state.json
```

### 3. Check health

```bash
blast social health
blast social drafts
blast social preview --id 2026-07-13_your_topic
```

### 4. Publish

Full pipeline (Zenodo + ORCID + all configured social channels):

```bash
blast social publish --id 2026-07-13_your_topic
```

Simulate without API calls:

```bash
blast social publish --id 2026-07-13_your_topic --dry-run
```

### 5. Post to a single platform

Useful when you already have a DOI or want to re-announce:

```bash
blast social post --id 2026-07-13_your_topic --platform mastodon
blast social post --id 2026-07-13_your_topic --platform bluesky
blast social post --id 2026-07-13_your_topic --platform discord
```

Supported `--platform` values: `mastodon`, `bluesky`, `telegram`, `twitter` (alias: `x`), `reddit`, `discord`, `slack`.

## CLI reference

| Command | Description |
|---------|-------------|
| `blast social status` | Profile + draft count |
| `blast social health` | Check all platform credentials |
| `blast social drafts` | List pending drafts |
| `blast social preview --id X` | Preview dissertation markdown |
| `blast social publish --id X` | Zenodo + ORCID + social blast |
| `blast social post --id X --platform Y` | Post to one platform |
| `blast social clean --older-than 30` | Remove old drafts |
| `blast social setup` | Env var checklist |

## MCP (`c4_social`)

When `blast serve --mcp` is running:

```json
{"action": "health"}
{"action": "drafts"}
{"action": "publish", "draft_id": "2026-07-13_topic"}
{"action": "post", "draft_id": "2026-07-13_topic", "platform": "mastodon"}
```

## TUI v9

Open the social publishing menu:

- **Command palette** (`:`) → `Open social publishing`
- **Keyboard**: `Ctrl+Shift+S`

Actions in the menu:

1. Refresh draft list
2. Platform health check
3. Publish selected draft (runs `blast social publish`)
4. Post to Mastodon / Bluesky for selected draft

The TUI shells out to the `blast` CLI, so credentials in `~/.c4reqber/` or `.env` must be available to the same environment.

## API (optional)

If the FastAPI backend is running (`make backend`):

- `POST /v8/social/post` — Mastodon, Twitter, SciMatic
- `POST /v8/social/mastodon/post` — Mastodon only

Webhook platforms (Discord, Slack) and Reddit are CLI/MCP-only today.

## Audit trail

All publish and post events are logged to:

```
~/.c4reqber/social_history.jsonl
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Draft not found` | Run `blast social drafts`; check `~/.c4reqber/drafts/` |
| Zenodo skipped | Set `ZENODO_ACCESS_TOKEN` (sandbox: https://sandbox.zenodo.org) |
| Reddit skipped | Publish to Zenodo first (needs DOI URL), set OAuth vars |
| Twitter skipped | Use `X_*` vars for auto-poster; `TWITTER_*` for API router only |
| Platform `skipped` | Credential missing — run `blast social health` |
| TUI action fails | Ensure `blast` is on `PATH` (`pip install c4reqber`) |

## Where to get API keys

| Service | URL |
|---------|-----|
| Zenodo | https://zenodo.org/account/settings/applications/tokens/new |
| ORCID | https://orcid.org/developer-tools |
| Mastodon | Instance → Preferences → Development → New application |
| Bluesky | Settings → App passwords |
| Telegram | @BotFather → `/newbot` |
| Reddit | https://www.reddit.com/prefs/apps (script app) |
| Discord | Channel → Integrations → Webhooks |
| Slack | https://api.slack.com/apps → Incoming Webhooks |
| X/Twitter | https://developer.x.com |
