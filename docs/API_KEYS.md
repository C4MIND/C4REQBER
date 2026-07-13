# API Keys & Environment Variables

Complete guide for configuring c4reqber credentials and optional integrations.

**Canonical list:** `.env.example` in the repository root (~100 variables).
**Machine registry:** `src/config/key_registry.py` (parsed from `.env.example`).
**Social publishing:** [SOCIAL_PUBLISHING.md](SOCIAL_PUBLISHING.md).

---

## Where keys are stored

| Location | Purpose |
|----------|---------|
| `~/.c4reqber/secrets.env` | **Primary user store** — managed by `blast config keys --assign` and TUI Setup Hub (`Ctrl+Shift+K`) |
| `~/.c4reqber/config.toml` | Core preferences + legacy `[keys]` section (OpenRouter, Brave, etc.) |
| Project `.env` | Developer / Docker deployments |
| Process environment | Always wins over file-based values |

Override the config directory (tests, containers):

```bash
export C4REQBER_CONFIG=/custom/path   # same as Python CONFIG_DIR and Go persist.UserConfigDir()
```

Load order at startup: `~/.kilo/.env` (if present) → `secrets.env` → `config.toml` → existing `os.environ`.

---

## Quick start

```bash
# Interactive wizard (essential keys)
blast init

# List all keys by category
blast config keys

# Set one secret (saved to ~/.c4reqber/secrets.env)
blast config keys --assign OPENROUTER_API_KEY=sk-or-...

# JSON export (for TUI / automation)
blast config keys --json

# Filter by category
blast config keys --category social

# Essential health check
blast config keys --health

# Model/council JSON (TUI Ctrl+Shift+M)
blast config --show --json
blast models --json

# Full social platform connectivity
blast social health
```

**TUI v9:** `Ctrl+Shift+K` — Setup Hub (browse categories, set keys, health check).
**TUI v9:** `Ctrl+Shift+S` — Social publishing menu.

---

## Required vs optional

| Variable | Status | Notes |
|----------|--------|-------|
| `OPENROUTER_API_KEY` | **Strongly recommended** | Default cloud LLM router; most pipelines need it |
| `BRAVE_API_KEY` or `TAVILY_API_KEY` | Recommended | Web/knowledge search enrichment |
| `LEAN4_PATH`, `COQ_PATH`, `DAFNY_PATH` | Optional | Formal verification backends (install tools separately) |
| Social keys (`ZENODO_*`, `MASTODON_*`, …) | Optional | Each platform skipped if unset — see [SOCIAL_PUBLISHING.md](SOCIAL_PUBLISHING.md) |
| Scientific source keys | Optional | Sources degrade gracefully or use polite pools |

`blast setup` installs **scientific packages only** (GROMACS, OpenMM, etc.) — not API keys. Use `blast init` or Setup Hub for keys.

---

## Categories

### LLM providers (`llm`)

| Variable | Service | Signup |
|----------|---------|--------|
| `OPENROUTER_API_KEY` | OpenRouter (multi-model) | https://openrouter.ai/keys |
| `DEEPSEEK_API_KEY` | DeepSeek | https://platform.deepseek.com |
| `MISTRAL_API_KEY` | Mistral AI | https://console.mistral.ai |
| `MOONSHOT_API_KEY` | Moonshot / Kimi | https://platform.moonshot.cn |
| `XAI_API_KEY` | xAI Grok | https://console.x.ai |
| `NVIDIA_API_KEY` | NVIDIA NIM | https://build.nvidia.com |
| `ANTHROPIC_API_KEY` | Anthropic | https://console.anthropic.com |
| `GOOGLE_API_KEY` | Google AI | https://aistudio.google.com/apikey |

### Local LLM (`local_llm`)

| Variable | Default | Notes |
|----------|---------|-------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama local server |
| `LM_STUDIO_URL` | `http://localhost:1234/v1` | LM Studio OpenAI-compatible API |
| `LM_STUDIO_API_KEY` | — | Usually empty for local |

Apple Silicon: MLX-LM auto-detects via `blast setup` — no API key.

### Search & web (`search`)

| Variable | Service | Signup |
|----------|---------|--------|
| `BRAVE_API_KEY` | Brave Search API | https://brave.com/search/api |
| `TAVILY_API_KEY` | Tavily (1000 free credits/mo) | https://app.tavily.com |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar | Optional — higher rate limits |
| `EXA_API_KEY` | Exa search | https://exa.ai |

### Scientific sources (`science`)

| Variable | Source | Notes |
|----------|--------|-------|
| `NCBI_API_KEY` + `NCBI_EMAIL` | PubMed / NCBI | Optional — raises rate limits |
| `MATERIALS_PROJECT_API_KEY` | Materials Project | Free academic key |
| `KAGGLE_USERNAME` + `KAGGLE_KEY` | Kaggle datasets | Required for Kaggle downloads |
| `OPENFDA_API_KEY` | OpenFDA | Free via api.data.gov |

Many sources (arXiv, Crossref, Europe PMC, OpenAlex) work **without** keys.

### Social & publishing (`social`)

See [SOCIAL_PUBLISHING.md](SOCIAL_PUBLISHING.md) for full workflow.

| Variable | Platform |
|----------|----------|
| `ZENODO_ACCESS_TOKEN` | Zenodo DOI upload |
| `MASTODON_ACCESS_TOKEN` | Mastodon |
| `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` | Bluesky |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Telegram |
| `DISCORD_WEBHOOK_URL` | Discord |
| `SLACK_WEBHOOK_URL` | Slack |
| `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` + `REDDIT_USERNAME` + `REDDIT_PASSWORD` | Reddit |
| `ORCID_CLIENT_ID` + `ORCID_CLIENT_SECRET` | ORCID |
| `X_BEARER_TOKEN` / `X_API_KEY` | X (Twitter) |

**arXiv / bioRxiv:** LaTeX package generation only — no automated upload API in c4reqber.

### Verification tools (`verification`)

| Variable | Tool |
|----------|------|
| `LEAN4_PATH` | Lean 4 (`elan` toolchain) |
| `COQ_PATH` | Coq (`coqc`) |
| `DAFNY_PATH` | Dafny verifier |

Install provers separately; paths point to binaries.

### Security (`security`)

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` / `C4REQBER_JWT_SECRET` | API auth (self-hosted) |
| `CSRF_SECRET` | CSRF protection |

Use `openssl rand -hex 32` for production secrets. Never commit real values.

---

## Simulation engines

c4reqber ships **38 engine bridges** — not all binaries are bundled. Engines are selected at runtime; missing engines show install hints and honest fallbacks.

```bash
blast packages list          # Scientific package installer
blast tui                    # Ctrl+Shift+C — capabilities overlay
```

See [INSTALL.md](INSTALL.md) and `docs/VERIFICATION_BACKENDS.md` for engine-specific setup.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `OPENROUTER_API_KEY not set` | `blast init` or `blast config keys --assign OPENROUTER_API_KEY=...` |
| Social publish skips platforms | Expected — only configured channels post. Run `blast social health` |
| Key set but not picked up | Process env overrides files; restart CLI/TUI after changes |
| `blast config keys --health` fails | Set at least `OPENROUTER_API_KEY` |

---

## Related docs

- [INSTALL.md](INSTALL.md) — full install from source
- [SOCIAL_PUBLISHING.md](SOCIAL_PUBLISHING.md) — multi-channel publishing
- `.env.example` — every variable with inline comments
