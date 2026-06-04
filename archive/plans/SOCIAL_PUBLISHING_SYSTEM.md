# c4reqber: Social Publishing & Preprint Dissemination System
## Project Plan v1.0 — 2026-05-19

---

## 1. Vision

User runs `blast turbo "sleep as active maintenance"`. Pipeline generates a dissertation.
System embeds user profile metadata into the paper. User reviews it in TUI or via Telegram
messenger. Upon approval, system uploads to Zenodo (gets DOI), registers on ORCID, generates
social posts with the DOI link, and posts to Twitter, Mastodon, Reddit, Discord, and Slack —
all with BYOK (Bring Your Own Key) and PolicyEngine guardrails.

**Core principles:**
- **No mocks.** Every API call is real. Every integration is real.
- **Human-in-the-loop by default.** arXiv — never auto. Zenodo — review by default.
- **LLM-assisted editing.** Via Telegram/Slack/Discord: user describes changes → LLM applies them.
- **Draft-first.** Social mode `draft` generates everything locally. User publishes with `blast social publish`.
- **Terminal-first.** TUI review, CLI commands, `/config` in agent.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE (existing)                               │
│  hil_pipeline.py / universal_solve_pipeline.py                      │
│  Phase F: DissertationGenerator → dissertation.md                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ dissertation.md + metadata
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2: PROFILE EMBED                            │
│  profile.json → ФИО, ORCID, affiliation → вшито в LaTeX/frontmatter│
└──────────────────────────────┬──────────────────────────────────────┘
                               │ preprint draft (md + tex/pdf)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 3: HUMAN REVIEW                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │   TUI    │  │ Telegram │  │  Slack   │  │ Discord  │           │
│  │ /approve │  │ [Approve]│  │ [Approve]│  │ [Approve]│           │
│  │ /edit    │  │ [Changes]│  │ [Changes]│  │ [Changes]│           │
│  │ /reject  │  │ LLM-edit │  │ LLM-edit │  │ LLM-edit │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                     │
│  LLM-assisted editing: user types natural language change request   │
│  → pipeline LLM applies → shows result → user confirms             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ approved ✅
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 4: PREPRINT UPLOAD                          │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────┐                 │
│  │  Zenodo  │  │  ai-archive.io   │  │   arXiv   │                 │
│  │  (API)   │  │  (MCP server)    │  │ (human    │                 │
│  │  → DOI   │  │  → submission    │  │  only!)   │                 │
│  └──────────┘  └──────────────────┘  └───────────┘                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ DOI / URL
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 5: ORCID REGISTRATION                       │
│  POST /v3.0/{orcid}/work  →  adds metadata entry with DOI          │
│  (metadata only — not re-uploading PDF)                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ DOI + confirmation
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 6: SOCIAL POST GENERATION                   │
│  Template: "New preprint: {title} — {doi_url} #c4reqber"           │
│  Optional human review (configurable, default OFF)                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ approved posts
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 7: MULTI-PLATFORM POSTING                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Twitter  │ │ Mastodon │ │  Reddit  │ │ Discord  │ │  Slack   │  │
│  │ API v2   │ │   API    │ │ OAuth2   │ │ Webhook  │ │ Webhook  │  │
│  │ Post     │ │  Post    │ │ Submit   │ │  Send    │ │  Send    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                                     │
│  PolicyEngine checks (HARD_WRITE tier) on every post                │
│  All results logged to ~/.c4reqber/social_history.jsonl             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Configuration System

### 3.1 Settings Tabs (10 tabs)

| # | Tab | Content |
|---|-----|---------|
| **1** | **Model** | Provider (openrouter/xai/mistral/deepseek/ollama/mlx), model name, temperature, max_tokens, API base URL. Model-per-pipeline-stage assignment (A→claude, B→qwen, etc.) |
| **2** | **MCP** | List of connected MCP servers with status (●/○), add/remove/toggle. Pre-populated with c4reqber's 21 built-in tools. |
| **3** | **Skills** | Toggle individual c4reqber skills: c4.engine, c4.pipeline, c4.triz, c4.discovery, c4.verification, c4.knowledge, c4.wasm, c4.memory, c4.export, c4.security, c4.soul |
| **4** | **Social** | mode (off/draft/full), auto_approve_paper (bool), review_posts (bool), preprints (checkbox: zenodo, ai-archive), social_platforms (checkbox: twitter, mastodon, reddit, discord, slack), messengers (checkbox: telegram, slack) |
| **5** | **Profile** | full_name, orcid_id, orcid_client_id, orcid_client_secret, affiliation, academic_title, email. Used for preprint metadata embedding. |
| **6** | **Pipeline** | verify_backend (hybrid/z3/lean4/coq), competing=N, no_iterative, functors toggle, plugin_selection |
| **7** | **Soul** | identity name, communication_style tone, core_values toggles, refusal_rules toggles. Read/write from ~/.c4reqber/soul.json |
| **8** | **Notifications** | telegram_bot_token, telegram_chat_id, slack_webhook_url, discord_webhook_url. Where review requests and status updates go. |
| **9** | **Security** | policy_custom_rules (add/edit/remove risk tiers), audit_trail view, guardian_sensitivity (low/medium/high) |
| **10** | **Export** | default_output_format (md/json/bibtex/latex/html), output_directory, auto_compile_latex (bool), editor_command ($EDITOR or custom) |

### 3.2 Social Mode States

| Mode | Pipeline | Upload preprint | Post to social | Save locally |
|------|----------|-----------------|----------------|--------------|
| `off` | normal | ❌ | ❌ | ❌ |
| `draft` | normal + embed profile | ❌ | ❌ | ✅ all files |
| `full` | normal + embed profile | ✅ via API | ✅ via API | ✅ receipts |

### 3.3 Key Files

```
~/.c4reqber/
├── agent.json              # existing — agent config
├── soul.json               # existing — persona
├── profile.json            # NEW — user academic profile
├── agent_history.jsonl     # existing — conversation memory
├── social_history.jsonl    # NEW — publish/post receipts
├── policy.toml             # NEW — custom PolicyEngine rules
├── drafts/                 # NEW — preprint drafts before publish
│   └── 2026-05-19_sleep_maintenance/
│       ├── dissertation.md
│       ├── dissertation.tex
│       ├── posts/
│       │   ├── twitter.md
│       │   ├── mastodon.md
│       │   └── reddit.md
│       └── receipt.jsonl
└── exports/                # existing — final published outputs
```

---

## 4. Platform Integrations

### 4.1 Preprint Servers

#### 4.1.1 Zenodo (primary)

| Item | Detail |
|------|--------|
| File | `src/social/zenodo_client.py` |
| Auth | `ZENODO_ACCESS_TOKEN` from `https://zenodo.org/account/settings/applications/` |
| API base | `https://zenodo.org/api` |
| Flow | `POST /deposit/depositions` → `PUT .../:id` (metadata) → `POST .../files` (upload PDF) → `POST .../actions/publish` |
| Result | `{doi, id, links.html, conceptdoi}` |
| Status | ✅ REST API, free, production-ready |

#### 4.1.2 arXiv (human-only)

| Item | Detail |
|------|--------|
| File | `src/social/arxiv_client.py` |
| Auth | `ARXIV_SUBMISSION_KEY` from endorsement |
| API base | `https://arxiv-submission-api.org` (see arxiv.github.io/arxiv-submission-core) |
| Constraint | **Human review MANDATORY, NOT disablable.** System checks endorsement status before offering arXiv. |
| Flow | `POST /submissions` → attach TeX source → poll status → moderation queue |
| Note | TeX compilation required. Endorsement required per category. arXiv BANS AI-only content. Human-in-the-loop is a REQUIREMENT, not a feature. |

#### 4.1.3 ai-archive.io (AI-friendly)

| Item | Detail |
|------|--------|
| Integration | Via MCP server (`AI-Archive-io/MCP-server` on GitHub) |
| Auth | API key from ai-archive.io account |
| Flow | MCP tools: `submit_paper(metadata, pdf)`, `search_papers(query)` |
| Status | MCP-native — compatible with c4reqber's 21 MCP tools. Human review recommended but not enforced. |

#### 4.1.4 GitHub/GitLab (manual)

| Item | Detail |
|------|--------|
| Approach | System generates `git push` to user's preprint repo (LaTeX + PDF + README) |
| Auth | Git SSH keys or `GITHUB_TOKEN` |
| Benefit | Auto-triggers Zenodo webhook for DOI. Version-controlled preprint. |
| Note | NOT a preprint server — a companion to Zenodo. Zenodo auto-archives from GitHub. |

### 4.2 Social Platforms

#### 4.2.1 Twitter/X

| Item | Detail |
|------|--------|
| File | `src/social/twitter_client.py` (exists, needs completion) |
| Auth | `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` |
| API | `POST /2/tweets` (OAuth 1.0a User Context) |
| Methods | `post_tweet(text)`, `search_tweets(query)`, `get_user_tweets(username)` |

#### 4.2.2 Mastodon

| Item | Detail |
|------|--------|
| File | `src/social/mastodon_client.py` (exists, needs completion) |
| Auth | `MASTODON_TOKEN`, `MASTODON_INSTANCE_URL`, `MASTODON_ACCESS_TOKEN` |
| Methods | `post_discovery(content, confidence)`, `get_timeline(limit)`, `get_status(status_id)` |

#### 4.2.3 Reddit

| Item | Detail |
|------|--------|
| File | `src/social/reddit_client.py` (NEW) |
| Auth | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD` |
| API | `POST /api/submit` (OAuth2, `kind=link`, `sr=subreddit`, `title=...`, `url=...`) |
| Free tier | 100 requests/minute. Non-commercial use. OAuth2 required. |

#### 4.2.4 Discord

| Item | Detail |
|------|--------|
| File | `src/social/discord_webhook.py` (NEW) |
| Auth | `DISCORD_WEBHOOK_URL` |
| API | `POST https://discord.com/api/webhooks/{id}/{token}` |
| Payload | `{content: "text", embeds: [{title, description, url, color}]}` |
| Complexity | Simplest of all — single POST, no OAuth. |

#### 4.2.5 Slack

| Item | Detail |
|------|--------|
| File | `src/social/slack_webhook.py` (NEW) |
| Auth | `SLACK_WEBHOOK_URL` |
| API | `POST https://hooks.slack.com/services/{token}` |
| Payload | `{text: "markdown", blocks: [...]}` |
| Complexity | Simple webhook POST. Also supports Incoming Webhooks for rich blocks. |

### 4.3 Academic Registries

#### 4.3.1 ORCID

| Item | Detail |
|------|--------|
| File | `src/social/orcid_client.py` (NEW) |
| Auth | `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET`, user's ORCID iD |
| Flow | OAuth2 authorization → `POST /v3.0/{orcid}/work` |
| Data | title, type ("preprint"), DOI/URL, publication-date, citation |
| Note | NOT a PDF upload. Metadata only. ORCID requires member API credentials (free for non-profits). |

### 4.4 Messengers (Notifications + LLM Editing)

#### 4.4.1 Telegram

| Item | Detail |
|------|--------|
| File | `src/social/telegram_bot.py` (NEW) |
| Auth | `TELEGRAM_BOT_TOKEN` (from @BotFather) |
| API | `POST https://api.telegram.org/bot{token}/sendMessage` |
| Features | Send preprint preview + inline buttons [✅Approve] [📝Changes] [❌Reject]; receive user text → LLM applies edits → resend updated |
| Dependencies | `python-telegram-bot` or raw `httpx` (prefer httpx for consistency) |

#### 4.4.2 Slack (messenger mode)

| Item | Detail |
|------|--------|
| File | Reuses `src/social/slack_webhook.py` |
| Auth | `SLACK_BOT_TOKEN` for interactive messages |
| Features | Same as Telegram — buttons + LLM-edit via incoming webhooks |

#### 4.4.3 Discord (messenger mode)

| Item | Detail |
|------|--------|
| File | `src/social/discord_bot.py` (NEW, separate from webhook) |
| Auth | `DISCORD_BOT_TOKEN` |
| Features | Same as Telegram — slash commands `/approve`, buttons via Discord Interactions API |

### 4.5 LLM-Assisted Editing Flow (all messengers)

```
0. System sends: "Preprint: 'Neural homeostasis during sleep' (4,200 words)"
   Buttons: [✅ Approve] [📝 Request Changes] [❌ Reject] [📄 Show Full]

1. User: 📝 Request Changes
   Bot: "Describe changes:"

2. User: "Shorten abstract to 150 words. Add keyword 'glymphatic system'."

3. System (LLM via ProviderRouter):
   - Parses user intent
   - Applies changes to dissertation markdown
   - Regenerates affected sections
   - Saves updated file

4. Bot: "Updated. Abstract: 147 words. Added 'glymphatic system'.
          [✅ Approve] [🔄 More Changes] [📄 Show Full]"
```

---

## 5. Human-in-the-Loop Guardrails

### 5.1 Per-Platform Enforcement

| Platform | Human Review | Can Disable? | Policy Tier |
|----------|-------------|--------------|-------------|
| **arXiv** | **MANDATORY** | ❌ Frozen to `true` | DANGEROUS |
| **Zenodo** | Default ON | ✅ `auto_approve_paper: true` | HARD_WRITE |
| **ORCID** | Default ON | ✅ `auto_approve_paper: true` | HARD_WRITE |
| **ai-archive.io** | Default OFF | ✅ | HARD_WRITE |
| **Twitter/Mastodon/Reddit** | Default OFF | ✅ `review_posts: true` | HARD_WRITE |
| **Discord/Slack** | Default OFF | ✅ `review_posts: true` | SOFT_WRITE |

### 5.2 Review Interface (TUI)

```
┌─────────────────────────────────────────────────────────────────┐
│  PREPRINT REVIEW — "Neural homeostasis during sleep"            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Title: Neural Homeostasis During Sleep: A Maintenance Hypothesis │
│  Authors: Ivan Selyutin (ORCID: 0000-0001-2345-6789)             │
│  Affiliation: Independent Researcher                              │
│                                                                  │
│  Abstract (147 words):                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ We propose that sleep serves as an active maintenance       │ │
│  │ process for neural homeostasis. Through systematic review   │ │
│  │ of glymphatic clearance mechanisms and synaptic scaling     │ │
│  │ evidence, we demonstrate that sleep-dependent processes     │ │
│  │ are necessary for maintaining optimal neural function...    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Stats: 4,200 words · 12 pages · 34 references · 3 figures       │
│  Targets: Zenodo (api key ✓) · ORCID (0000-0001-2345-6789)       │
│                                                                  │
│  [/approve] [/edit] [/reject] [/view-full] [/stats]               │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Review Interface (Telegram)

```
Bot: 📄 *Neural Homeostasis During Sleep: A Maintenance Hypothesis*
     Authors: Ivan Selyutin  
     Words: 4,200 · Refs: 34 · Figures: 3
     Target: Zenodo (DOI will be assigned)
     
     *Abstract:* We propose that sleep serves as an active maintenance
     process for neural homeostasis. Through systematic review of
     glymphatic clearance mechanisms and synaptic scaling evidence,
     we demonstrate that sleep-dependent processes are necessary...
     
     [✅ Approve] [📝 Request Changes] [❌ Reject] [📄 Full Text]
```

---

## 6. CLI & TUI Commands

### 6.1 New CLI Commands

| Command | Action |
|---------|--------|
| `blast config` | Interactive settings menu (10 tabs) |
| `blast config --edit` | Open `~/.c4reqber/agent.json` in `$EDITOR` |
| `blast config --show` | Print current config as JSON |
| `blast social publish <draft_id>` | Publish a draft preprint + posts |
| `blast social drafts` | List pending drafts |
| `blast social history` | Show publish/post history |
| `blast social preview <draft_id>` | Show draft in TUI for review |
| `blast profile` | Show/edit profile |
| `blast telegram start` | Start Telegram bot for background notifications |

### 6.2 Agent Slash Commands

| Command | Action |
|---------|--------|
| `/config` | Settings menu |
| `/profile` | Show/edit profile |
| `/drafts` | List saved preprint drafts |
| `/publish <draft_id>` | Publish a draft |
| `/social status` | Show social module status (mode, connected platforms) |

### 6.3 TUI Key Bindings

| Key | Action |
|-----|--------|
| `C` | Config screen (was: cube navigator — merge or replace) |
| `P` | Profile screen |
| `R` | Review current preprint draft |

---

## 7. File Creation Plan

### 7.1 New Files

```
src/social/
├── zenodo_client.py          # Zenodo REST API: create deposit, upload, publish, get DOI
├── reddit_client.py          # Reddit OAuth2: submit link post, search
├── discord_webhook.py        # Discord webhook: send message with embeds
├── discord_bot.py            # Discord bot: interactive messages for review
├── slack_webhook.py          # Slack webhook: send message with blocks
├── telegram_bot.py           # Telegram bot: notifications + LLM-edit review
├── orcid_client.py           # ORCID API: add work entry with DOI
├── arxiv_client.py           # arXiv submission API (human-only)
├── publisher.py              # Orchestrator: full publish pipeline
└── profile_manager.py        # Read/write ~/.c4reqber/profile.json

src/tui/
├── config_screen.py          # UPDATE: 10-tab settings screen
├── settings_widgets.py       # NEW: reusable settings widgets (toggle, dropdown, list, key-value)
├── review_screen.py          # NEW: preprint review screen
└── profile_screen.py         # NEW: profile editing screen

src/agent/
├── telegram.py               # NEW: Telegram bot integration with agent
└── (core.py — update: /config, /profile, /drafts, /publish commands)
```

### 7.2 Modified Files

```
src/cli/blast_app.py          # ADD: config, social, profile commands
src/agent/core.py             # ADD: /config, /profile, /drafts, /publish slash commands
src/tui/app.py                # UPDATE: C key → config screen
src/api/v8_routers/social_v8.py # REFACTOR: use new clients
src/verification/hoare_verifier.py # no changes needed (already professional)
~/.c4reqber/agent.json        # NEW fields: social, profile, notifications sections
```

---

## 8. Dependencies

| Package | Purpose | License |
|---------|---------|---------|
| `httpx` | Async HTTP for ALL API clients | BSD |
| `python-dotenv` | Env vars (existing) | BSD |
| `requests-oauthlib` | OAuth1.0a for Twitter | ISC |
| `z3-solver` | Hoare verifier (existing) | MIT |
| `prometheus-client` | Metrics (existing) | Apache 2.0 |
| *(no new heavy dependencies — all API via httpx)* | | |

**NOT adding:** `python-telegram-bot` (heavy, ~200 deps). Use raw `httpx` POST to `api.telegram.org`. Same for Slack/Discord — raw webhook POSTs.

---

## 9. Data Flow — Detailed Step-by-Step

### 9.1 From Pipeline to Draft

```
Pipeline Phase F → dissertation.md (markdown with frontmatter)
     │
     ├─ Read profile.json → extract: ФИО, ORCID, affiliation, title
     ├─ Embed into dissertation frontmatter:
     │  ---
     │  title: "Neural Homeostasis During Sleep"
     │  authors:
     │    - name: "Ivan Selyutin"
     │      orcid: "0000-0001-2345-6789"  
     │      affiliation: "Independent Researcher"
     │  date: "2026-05-19"
     │  ---
     ├─ Save to ~/.c4reqber/drafts/{date}_{slug}/
     │  ├── dissertation.md
     │  ├── metadata.json
     │  └── bibliography.bib (if available)
     └─ If social.mode == 'draft' or 'full':
        ├─ Generate social posts → posts/*.md
        └─ If mode == 'full': proceed to review
```

### 9.2 Human Review → Decision

```
Review (TUI or messenger)
     │
     ├─ [/approve]   → status = "approved" → continue to step 4 (upload)
     ├─ [/edit]      → open $EDITOR or LLM-edit → re-save → re-review
     └─ [/reject]    → status = "rejected" → save to drafts, notify user
```

### 9.3 Upload → Post (full mode)

```
For each preprint in config.social.preprints:
  ├─ Zenodo:  create_deposit → upload_file → add_metadata → publish → get DOI
  └─ write receipt to social_history.jsonl

If config.social.orcid.enabled:
  └─ ORCID: POST work with DOI → write receipt

For each platform in config.social.social_platforms:
  ├─ Generate post text from template
  ├─ If config.social.review_posts: show review → wait approval
  ├─ PolicyEngine.evaluate(post_action) → check DANGEROUS tier
  ├─ Post via platform API
  └─ Write receipt to social_history.jsonl
```

### 9.4 Draft Mode (manual publish later)

```
Pipeline → save drafts → EXIT (no API calls)
     
User later:
  blast social drafts              # list all drafts
  blast social preview <id>        # review
  blast social publish <id>        # manual publish via API
```

---

## 10. Security & PolicyEngine Integration

### 10.1 Risk Classification

| Action | Risk Tier | Requires |
|--------|-----------|----------|
| Generate preprint (local) | READ | — |
| Upload to Zenodo | HARD_WRITE | User approval |
| Upload to arXiv | DANGEROUS | Multi-factor (human review MANDATORY) |
| Register on ORCID | HARD_WRITE | User approval |
| Post to Twitter | HARD_WRITE | If review_posts=on |
| Post to Mastodon | HARD_WRITE | If review_posts=on |
| Post to Reddit | HARD_WRITE | If review_posts=on |
| Post to Discord/Slack | SOFT_WRITE | Logged |
| Send Telegram message | SOFT_WRITE | Logged |

### 10.2 Audit Trail

Every publish and post action recorded in `~/.c4reqber/social_history.jsonl`:
```json
{"timestamp": 1716098400.0, "action": "zenodo_publish", "doi": "10.5281/...", "status": "success", "draft_id": "2026-05-19_sleep"}
{"timestamp": 1716098410.0, "action": "twitter_post", "tweet_id": "123456", "status": "success", "draft_id": "2026-05-19_sleep"}
```

---

## 11. Error Handling & Edge Cases

| Scenario | Resolution |
|----------|------------|
| Zenodo API down | Retry 3x with exponential backoff. Save to drafts. Notify user via configured messengers. |
| Twitter rate limited | Queue and retry. Log to social_history. |
| User closes TUI during review | Review state persisted in json. Resume on next `blast social preview`. |
| LaTeX not installed | Skip PDF generation. Upload markdown + .tex to Zenodo (they accept both). |
| ORCID token expired | Re-auth flow via CLI. Prompt user. |
| arXiv endorsement revoked | Log warning. Show in settings. Offer Zenodo as fallback. |
| Multiple parallel publishes | Semaphore lock on draft directory. One publish per draft at a time. |
| Disk full during draft save | Check disk space before save. Report error. |
| Messenger bot not started | Send notification to TUI/CLI instead. Future: queue in memory for bot pickup. |

---

## 12. Implementation Phases

### Phase 1: Foundation (estimated: session)
- [ ] `profile.json` schema + `ProfileManager`
- [ ] `social_history.jsonl` schema + audit trail
- [ ] Settings: `blast config` CLI + `/config` agent command
- [ ] TUI: config_screen refactor (C key)

### Phase 2: Preprint Pipeline (estimated: session)
- [ ] `ZenodoClient` — full REST API (deposit, upload, publish, DOI)
- [ ] `publisher.py` — orchestrator: draft → review → upload → DOI
- [ ] TUI: review screen (`/approve`, `/edit`, `/reject`)
- [ ] Draft storage + `blast social preview` command

### Phase 3: Social Posting (estimated: session)
- [ ] `RedditClient` — OAuth2 submit
- [ ] `DiscordWebhook` — send message
- [ ] `SlackWebhook` — send message
- [ ] `blast social publish` — manual draft publishing
- [ ] Post generation + review flow

### Phase 4: Messengers (estimated: session)
- [ ] `TelegramBot` — notifications + LLM-edit review
- [ ] `DiscordBot` — interactive messages
- [ ] Slack bot mode — interactive messages
- [ ] LLM-assisted editing via all messengers

### Phase 5: Academic (estimated: session)
- [ ] `ORCIDClient` — work registration
- [ ] `arXivClient` — human-only submission
- [ ] `ai-archive.io` MCP bridge

### Phase 6: Polish (estimated: session)
- [ ] Full integration tests
- [ ] Error handling + retry logic
- [ ] Documentation updates
- [ ] CHANGELOG

---

## 13. Post-Implementation Verification

| Check | Criteria |
|-------|----------|
| Lint | `ruff check src/social/ src/tui/ src/agent/ src/cli/` → 0 errors |
| Typecheck | `mypy src/social/ src/tui/ src/agent/` → 0 errors in new files |
| Import | `python -c "from src.social.zenodo_client import ZenodoClient"` → OK |
| Integration | `blast turbo "test"` → dissertation → draft saved with profile metadata |
| Review | Open draft in TUI → approve → Zenodo deposit created |
| Social | Post generated with DOI link → manual publish to Twitter test account |
| Audit | `social_history.jsonl` contains receipt entries |
| Messenger | Telegram bot receives notification → user can Approve/Changes/Reject |

---

---

## 14. Missing Pieces — Added After Review

### 14.1 LaTeX Compilation for arXiv

arXiv requires `.tex` source + compiled `.pdf`. System must:
- Convert `dissertation.md` → `.tex` (existing: `src/export/manager.py` LaTeX export)
- Compile with `pdflatex` (or `latexmk`) → check for errors
- Re-try with auto-fix: missing `\usepackage` → inject; undefined refs → remove `\ref{}`
- Pre-flight check before arXiv submission
- Abort with clear error if LaTeX not installed (offer `brew install texlive` / `apt install texlive`)

**File:** `src/publishing/latex_compiler.py` (NEW)
**Dependency:** `pdflatex` on system PATH. Not a Python dep.

### 14.2 Messenger Setup Wizard

User should not manually google how to create a Telegram bot. System walks through:

```
$ blast telegram setup

  Step 1: Open @BotFather on Telegram
  Step 2: Send /newbot, name: "c4reqber", username: "c4reqber_bot"
  Step 3: BotFather gives you a token. Paste it here:
  > 8123456789:AAHq...

  Token saved.
  Step 4: Open your bot on Telegram, send /start
  Step 5: System auto-detects your chat_id from /start message
  Bot connected. Chat ID: 123456789
```

Same pattern for Slack (`blast slack setup`) and Discord (`blast discord setup`).

**File:** `src/social/setup_wizard.py` (NEW) — interactive CLI wizard for all platforms.

### 14.3 TUI Key Conflict Resolution

**Current:** `C` = Cube Navigator (3×3×3 cube).
**Plan:** `C` = Config screen (10 tabs).

**Resolution:** Move Cube Navigator to `K` (Kube). Config → `C`. Both documented in AGENTS.md TUI shortcuts table.

### 14.4 Co-Author Support (Schema-Ready)

`profile.json` → `authors` as array (not single name). Version 1: single author. Schema ready for >1:

```json
{
  "authors": [
    {
      "name": "Ivan Selyutin",
      "orcid": "0000-0001-2345-6789",
      "affiliation": "Independent Researcher",
      "title": "",
      "corresponding": true,
      "email": "ivan@example.com"
    }
  ]
}
```

All preprint metadata generators read from `authors[0]` for v1. v2: iterate all authors for multi-author preprints.

### 14.5 Turbofactory Batch Mode

`blast turbofactory` spawns 5-100 parallel pipelines. Social module in `full` mode would fire 100 review requests simultaneously → spam.

**Solution:** Batch aggregation.
1. All N dissertations saved to drafts.
2. One summary notification: "Turbofactory complete: 47/100 dissertations generated. 12 passed quality gates. Review batch?"
3. `blast social batch-review` → list with checkboxes, bulk [Approve All] [Reject All] or per-item.
4. Publish approved batch sequentially.
5. Single Telegram/Slack notification with summary.

**File:** `src/social/batch_publisher.py` (NEW)

### 14.6 Preprint Discovery Auto-Bridge (CRITICAL)

Pipeline Phase F completes → dissertation saved to `discovery/batch_N/`. Social module operates on `~/.c4reqber/drafts/`. Need automatic handoff:

**Hook in `hil_pipeline.py`:** after Phase G (quality gate passes):
```python
if config.social_mode != "off":
    await SocialBridge.transfer_to_drafts(record, social_config)
```
`SocialBridge.transfer_to_drafts()`:
1. Copies dissertation.md to `~/.c4reqber/drafts/{date}_{slug}/`
2. Embeds profile metadata (authors, ORCID, affiliation)
3. Generates social post templates
4. Saves `draft_state.json` with status "pending_review"

**File:** `src/social/social_bridge.py` (NEW)

### 14.7 Platform Health Check

`blast social health` — validates all configured credentials with lightweight API call.

| Platform | Check |
|----------|-------|
| Zenodo | `GET /api/deposit/depositions?access_token=X` → 200 |
| Twitter | `GET /2/users/me` → 200 |
| Mastodon | `GET /api/v1/accounts/verify_credentials` → 200 |
| Reddit | `GET /api/v1/me` → 200 |
| Discord | `POST webhook {"content":"health check"}` → 204 |
| Slack | `POST webhook {"text":"health check"}` → 200 |
| Telegram | `GET /bot{token}/getMe` → 200 |
| ORCID | `GET /v3.0/{orcid}` → 200 |
| arXiv | Check endorsement status via submission API |

TUI: green ● / red ● indicators. CLI: `blast social health --json` for machine output.

**File:** `src/social/health_checker.py` (NEW)

### 14.8 DOI Collision Prevention

Before creating a new Zenodo deposit, check if one with the same title already exists:

```python
existing = await self.list_deposits(query=f"title:\"{title}\"")
if existing:
    return {"status": "exists", "doi": existing[0]["doi"],
            "message": "Deposit already exists. Use update instead of create."}
```

User gets choice: update existing deposit (new version) or skip (keep old).

### 14.9 Review State Persistence

Every draft directory contains `draft_state.json`:

```json
{
  "id": "2026-05-19_sleep_maintenance",
  "status": "pending_review",
  "created_at": 1716098400.0,
  "review_started_at": 1716098500.0,
  "platforms": {
    "zenodo": "pending",
    "twitter": "pending"
  },
  "edit_history": [
    {"at": 1716098550, "by": "telegram", "change": "shortened abstract to 147 words"}
  ],
  "last_reviewer": "telegram"
}
```

On `blast social preview <id>` → loads `draft_state.json` → resumes from last state. Survives terminal close.

### 14.10 Post-Publication Analytics (v2)

Not in v1 scope, but schema-ready. After publishing:
- `social_history.jsonl` records `{platform, post_id, url}`
- `blast social analytics <id>` → polls Zenodo views/downloads, Twitter impressions, Mastodon boosts
- Future: TUI dashboard widget with real-time stats

---

## 15. Critical Risk & Edge Case Audit

### 15.1 Network Failures

| Scenario | Handling |
|----------|----------|
| Zenodo down during upload | Retry 3× with exponential backoff. Save draft. Notify. |
| All platforms down | Save all to drafts. Queue for `blast social publish` later. |
| Partial upload (Zenodo OK, Twitter fails) | Do NOT rollback Zenodo. Keep it. Record partial success. Offer retry for failed platforms. |
| Intermittent Wi-Fi during upload | Chunked uploads for large files. Resume from last chunk. |

### 15.2 Content Limits

| Platform | Limit | Handling |
|----------|-------|----------|
| Twitter | 280 chars | Truncate title + DOI link fits. Full abstract → thread (X thread support). |
| Mastodon | 500 chars | Standard post fits. Longer → content_warning dropdown. |
| Reddit | 40,000 chars | Self-post with full abstract. Link post with summary. |
| Discord | 2,000 chars | Embed with title + description + link. |
| Slack | 3,000 chars | Blocks with expandable sections. |
| Telegram | 4,096 chars | Full abstract fits. Use `telegramify-markdown` converter. |
| Zenodo | 50GB file limit | Preprints are KB-MB. Never an issue. |

### 15.3 Title/Content Sanitization

| Issue | Handling |
|-------|----------|
| Unicode in title (中文, العربية) | Encode properly for all APIs. Test with CJK, Arabic, Cyrillic. |
| Markdown in title | Strip for Twitter (plain text). Keep for Mastodon (native MD). Preserve for Telegram/Slack/Discord. |
| Newlines in post text | Platform-specific: Twitter strips extra. Mastodon keeps. |
| URL length | DOI URLs always short (~30 chars). |

### 15.4 Credential Rotation

| Scenario | Handling |
|----------|----------|
| Token expired (401) | Catch. Log. Offer `blast social health` to re-validate. |
| User changed platform password | Same → 401 → re-auth prompt. |
| Revoked OAuth token (403) | Detect. Prompt user to re-authorize platform. |

### 15.5 Multi-Platform Posting Order (CRITICAL)

Order enforcement: **preprint first → DOI → social posts.**

If social posts fire before Zenodo DOI → posts have NO link → useless.

**Enforcement:** `publisher.py` → `await` Zenodo DOI confirmation → only THEN generate and post to social. Sequential blocking step. Not parallel.

### 15.6 LaTeX Compilation Failures

| Error | Auto-Fix |
|-------|----------|
| Missing `\usepackage{...}` | Inject common: amsmath, graphicx, hyperref, geometry. |
| Undefined `\ref{...}` | Replace with `[reference]` placeholder. |
| Missing bibliography | Generate placeholder BibTeX from pipeline paper data. |
| File too large (>50 pages) | Compile without images. Warning: "Images excluded." |
| TeX not installed at all | Abort arXiv. Fallback: Zenodo accepts markdown + raw .tex. |

### 15.7 State Conflicts

| Scenario | Handling |
|----------|----------|
| Two `blast social publish` on same draft | File lock (`fcntl.flock`) on draft directory. Second process: "Draft locked. Try `blast social status`." |
| User edits draft locally while Telegram review active | Telegram review is the source of truth (was user-initiated). Local edits detected via mtime → warning. |
| Pipeline writes same draft ID twice | Append version suffix: `sleep_maintenance_v2`. Previous draft preserved. |

### 15.8 Privacy & Security

| Concern | Handling |
|---------|----------|
| ORCID `client_secret` | Stored in `~/.c4reqber/agent.json`. `chmod 600`. |
| Telegram bot token leak | Same. Never logged. Masked: `8123456***` in debug output. |
| Preprint drafts on shared machine | `~/.c4reqber/drafts/`. User's home dir = their responsibility. `chmod 700` on directory. |
| API keys in process memory | Short-lived Python strings. Loaded from env/config on each call. GC'd after. |

### 15.9 Large Preprints & Batches

| Scenario | Handling |
|----------|----------|
| Dissertation >10MB (many figures) | Zenodo: chunked upload (REST API supports). arXiv: compress images via `convert`. |
| Dissertation >50 pages | Telegram notification: first 500 words + "Open full text" link. |
| Batch of 100 preprints | Process sequentially. Show: "[23/100] Published sleep_maintenance to Zenodo. DOI: 10.5281/..." |

### 15.10 Platform-Specific Edge Cases

| Platform | Edge Case | Handling |
|----------|-----------|----------|
| Reddit | Subreddit doesn't exist | Pre-flight: `GET /r/{subreddit}/about` → 404 → "Subreddit r/... does not exist" |
| Reddit | Karma too low to post | Reddit returns error. Relay to user. |
| Mastodon | Instance blocked/defederated | Detect 403. "Instance unreachable. Try another?" |
| Telegram | Bot blocked by user | `getMe` ok, `sendMessage` 403 → disable Telegram notifications. |
| Slack | Webhook URL revoked | 404 → "Slack webhook invalid. Run `blast slack setup` to recreate." |
| Discord | Webhook deleted | 404 → same as Slack. |
| arXiv | Endorsement revoked mid-submission | Submission rejected. "Endorsement check failed. Submit via Zenodo instead?" |
| Zenodo | Duplicate DOI (versioning) | Zenodo creates version DOI automatically (new suffix). Accept and use it. |

### 15.11 Internationalization (i18n)

System supports 7 languages. Social posts match user's language.

| Lang | Template |
|------|----------|
| en | "New preprint: {title} — {url} #c4reqber" |
| ru | "Новый препринт: {title} — {url} #c4reqber" |
| zh | "新预印本：{title} — {url} #c4reqber" |
| ja | "新しいプレプリント: {title} — {url} #c4reqber" |
| de | "Neues Preprint: {title} — {url} #c4reqber" |
| ar | "نسخة أولية جديدة: {title} — {url} #c4reqber" |
| hi | "नया प्रीप्रिंट: {title} — {url} #c4reqber" |

Language auto-detected from `agent.json` locale or `$LANG` env variable.

### 15.12 Versioning & Republishing

| Scenario | Handling |
|----------|----------|
| Publish → edit → update | `blast social update <id>` → creates new Zenodo version (same concept DOI, new version suffix) |
| Withdraw preprint | Zenodo: `POST /deposit/:id/actions/discard`. arXiv: withdrawal request through submission API. |
| Cross-platform version tracking | All versions share same `draft_id`. Full history in `social_history.jsonl`. |

---

## 16. Implementation Status Board

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Foundation | `profile.json` schema + ProfileManager | ⬜ |
| 2 | Foundation | `social_history.jsonl` schema + audit trail | ⬜ |
| 3 | Foundation | `blast config` CLI + `/config` agent command | ⬜ |
| 4 | Foundation | TUI config_screen refactor (C→config, K→cube) | ⬜ |
| 5 | Foundation | `setup_wizard.py` — Telegram/Slack/Discord wizards | ⬜ |
| 6 | Preprint | `ZenodoClient` — create deposit, upload, publish, DOI | ⬜ |
| 7 | Preprint | `publisher.py` — orchestrator: draft→review→upload→DOI | ⬜ |
| 8 | Preprint | `SocialBridge` — pipeline handoff hook | ⬜ |
| 9 | Preprint | `review_screen.py` — TUI review (`/approve` `/edit` `/reject`) | ⬜ |
| 10 | Preprint | Draft storage + `blast social preview/drafts` | ⬜ |
| 11 | Social | `RedditClient` — OAuth2 submit link post | ⬜ |
| 12 | Social | `DiscordWebhook` + `DiscordBot` — post + interactive review | ⬜ |
| 13 | Social | `SlackWebhook` — post + interactive review | ⬜ |
| 14 | Social | `blast social publish` — manual draft publishing | ⬜ |
| 15 | Social | Post generation + review flow | ⬜ |
| 16 | Social | `batch_publisher.py` — turbofactory batch mode | ⬜ |
| 17 | Messengers | `TelegramBot` — notifications + LLM-edit review | ⬜ |
| 18 | Messengers | LLM-assisted editing via all messengers | ⬜ |
| 19 | Academic | `ORCIDClient` — work registration | ⬜ |
| 20 | Academic | `arXivClient` — human-only submission | ⬜ |
| 21 | Academic | ai-archive.io MCP bridge | ⬜ |
| 22 | Academic | `LatexCompiler` — pdflatex with auto-fix | ⬜ |
| 23 | Polish | `health_checker.py` — platform credential validation | ⬜ |
| 24 | Polish | Error handling + retry logic + sanitization | ⬜ |
| 25 | Polish | i18n templates for all social posts | ⬜ |
| 26 | Polish | Integration tests (full publish flow) | ⬜ |
| 27 | Polish | Documentation: AGENTS.md, README.md, CHANGELOG.md | ⬜ |

**Total: 27 implementation tasks across 6 phases.**

---

*Plan v2.0. 27 tasks. 15 risk categories audited. 10 missing gaps filled. 11 platform edge cases documented. 7 i18n templates. Zero mocks — every integration is a real API call. Ready for implementation upon user signal.*


---

## 17. Final Gap Fill — Second Audit

### 17.1 API Key Encryption at Rest (SECURITY)

`~/.c4reqber/agent.json` stores secrets in plaintext → any process reads them.

**Solution:** `cryptography.fernet.Fernet` (already in `src/security/secrets.py`). Master key from: `C4REQBER_KEYRING_TOKEN` env → macOS Keychain → Linux `secret-tool` → plaintext with warning. Model: decrypt on load → use → never write plaintext to disk.

### 17.2 Dry-Run Mode

`blast social publish --dry-run` simulates entire pipeline: "Zenodo: would create deposit → simulated DOI → Twitter: would post 234 chars". Every client gets `._dry_run` flag.

### 17.3 Agent /preprint Command

`/preprint "topic"` → pipeline → auto-bridge → draft → offer review. Separates from `/turbo`.

### 17.4 Multi-Messenger Routing

`notifications.primary: "telegram"`. Review requests → primary only. Status updates → all. LLM-edit → session-scoped.

### 17.5 Offline Bot State Conflict

Bot checks `draft_state.json` before processing clicks. If already reviewed via TUI → "Already reviewed at {time}."

### 17.6 Draft Cleanup

`blast social clean --older-than 30d` + `--dry-run` + `--force`.

### 17.7 ORCID Dedup

GET existing works → match by concept DOI → PUT (update) if exists, POST (create) if new.

### 17.8 PDF Attachment (v2)

Schema placeholder. v1: link-only. v2: auto-extract Figure 1 from PDF.


## 18. Final Task Board — 29 Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Foundation | `profile.json` schema + ProfileManager | ⬜ |
| 2 | Foundation | `social_history.jsonl` schema + audit trail | ⬜ |
| 3 | Foundation | Key encryption (Fernet) for agent.json secrets | ⬜ |
| 4 | Foundation | `blast config` CLI + `/config` agent command | ⬜ |
| 5 | Foundation | TUI config_screen (10 tabs, C=config, K=cube) | ⬜ |
| 6 | Foundation | `setup_wizard.py` — Telegram/Slack/Discord | ⬜ |
| 7 | Preprint | `ZenodoClient` — deposit, upload, publish, DOI | ⬜ |
| 8 | Preprint | `publisher.py` — orchestrator (dry-run support) | ⬜ |
| 9 | Preprint | `SocialBridge` — pipeline handoff hook | ⬜ |
| 10 | Preprint | `review_screen.py` — TUI /approve /edit /reject | ⬜ |
| 11 | Preprint | Draft storage + `blast social preview/drafts` | ⬜ |
| 12 | Preprint | `blast social clean` — draft cleanup | ⬜ |
| 13 | Preprint | Agent `/preprint` command | ⬜ |
| 14 | Social | `RedditClient` — OAuth2 submit link | ⬜ |
| 15 | Social | `DiscordWebhook` + `DiscordBot` | ⬜ |
| 16 | Social | `SlackWebhook` + Slack bot | ⬜ |
| 17 | Social | `blast social publish` (+ --dry-run, --confirm) | ⬜ |
| 18 | Social | Post generation + templates (i18n) | ⬜ |
| 19 | Social | `batch_publisher.py` — turbofactory batch | ⬜ |
| 20 | Messengers | `TelegramBot` — notifications + LLM-edit | ⬜ |
| 21 | Messengers | LLM-assisted editing via all messengers | ⬜ |
| 22 | Messengers | Multi-messenger routing (primary vs all) | ⬜ |
| 23 | Academic | `ORCIDClient` — work registration + dedup | ⬜ |
| 24 | Academic | `arXivClient` — human-only submission | ⬜ |
| 25 | Academic | ai-archive.io MCP bridge | ⬜ |
| 26 | Academic | `LatexCompiler` — pdflatex with auto-fix | ⬜ |
| 27 | Polish | `health_checker.py` — credential validation | ⬜ |
| 28 | Polish | Integration tests + error handling + retry | ⬜ |
| 29 | Polish | Documentation: AGENTS.md, README.md, CHANGELOG.md | ⬜ |

---

*Plan v3.0. 29 tasks. 15 risk categories. 18 gap fixes. Zero mocks — every integration is a real API call.*
