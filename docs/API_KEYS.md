# API Keys & Service Registration Guide

**Updated:** 2026-07-11
**Mini guide (GitLab Pages):** `landing/docs/setup/api-keys.html`
**Env template:** `.env.example`

c4reqber is **BYOK** (bring your own key). The pipeline runs on CPU without GPU; most **Tier-1 knowledge sources need no registration**. This guide lists every key used in this repository, how to obtain it, and what to expect (email, approval, billing).

> **Security:** Never commit `.env`. Copy `.env.example` → `.env` locally. Rotate keys if exposed.

---

## Quick setup

```bash
cp .env.example .env
# Edit .env — minimum:
export OPENROUTER_API_KEY="<paste-from-openrouter-settings>"
# Recommended for literature search at scale:
export NCBI_API_KEY="..."
export NCBI_EMAIL="you@institution.edu"
```

Verify keys: `python3 tools/check_keys.py`

---

# English

## Tier 0 — Required (pipeline won't route LLM calls)

| Service | Env var | Sign up | Steps | Email / wait | Cost (Jul 2026) |
|---------|---------|---------|-------|--------------|-----------------|
| **OpenRouter** | `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) | Sign up (email / Google / GitLab) → [Keys](https://openrouter.ai/settings/keys) → **Create Key** → copy `sk-or-...` (shown once) | Confirm email | Free `:free` models; ~50 req/day without credits; top-up optional |

## Tier 1 — LLM providers (optional, multi-provider routing)

| Service | Env var | Sign up | Steps | Email / wait | Cost |
|---------|---------|---------|-------|--------------|------|
| **DeepSeek** | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) | Separate from chat.deepseek.com → **API Keys** → Create → `sk-...` → **Billing top-up** required before first response | Email + **phone SMS** | Pay-per-token after top-up |
| **xAI (Grok)** | `XAI_API_KEY` | [console.x.ai](https://console.x.ai) | API Keys → Create → `xai-...` (shown once) | Usually instant | ~$25 promo credits on new accounts |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | [build.nvidia.com](https://build.nvidia.com) | [Settings → API Keys](https://build.nvidia.com/settings/api-key) → Generate → `nvapi-...` | Instant | Free dev tier: ~1000 inference credits, 40 rpm, no card |
| Mistral | `MISTRAL_API_KEY` | [console.mistral.ai](https://console.mistral.ai) | Workspace → API keys | Email | Paid balance |
| Moonshot | `MOONSHOT_API_KEY` | [platform.moonshot.cn](https://platform.moonshot.cn) | Console → API keys | Phone common | Paid balance |
| Anthropic | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | API keys section | Email | Paid |
| OpenAI | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | API keys | Email | Paid |

Local LLM (no cloud key): `OLLAMA_URL`, `LM_STUDIO_URL` — run Ollama / LM Studio locally.

## Tier 2 — Web & AI search

| Service | Env var | Sign up | Steps | Email / wait | Cost |
|---------|---------|---------|-------|--------------|------|
| **Brave Search** | `BRAVE_API_KEY` | [brave.com/search/api](https://brave.com/search/api) | Subscribe → create key → header `X-Subscription-Token` | **Credit card required** (anti-fraud) | As of Feb 2026: **$5 monthly credits** (~1000 queries), then metered |
| **Tavily** | `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | Dashboard → API key `tvly-...` | Instant | **1000 credits/month**, no card |
| Exa | `EXA_API_KEY` | [exa.ai](https://exa.ai) | Dashboard → API keys | Email | Free tier available |

## Tier 3 — Scientific knowledge sources (keys in this repo)

| Service | Env var(s) | Sign up | Steps | Email / wait | Notes |
|---------|------------|---------|-------|--------------|-------|
| **NCBI E-utilities** | `NCBI_API_KEY`, `NCBI_EMAIL` | [account.ncbi.nlm.nih.gov](https://account.ncbi.nlm.nih.gov) | Account settings → **API Key Management** → Create | Instant | Raises limit 3→10 req/s. **Also** register tool name + email with NCBI: `eutilities@ncbi.nlm.nih.gov` |
| **CORE** | `CORE_API_KEY` | [core.ac.uk/services/api](https://core.ac.uk/services/api) | Enter email → key sent by email | Minutes–hours | 10M+ OA full texts |
| **Materials Project** | `MATERIALS_PROJECT_API_KEY` | [next-gen.materialsproject.org](https://next-gen.materialsproject.org) | Log in → **API** (top nav) → copy key | Instant | Academic materials DB |
| **Kaggle** | `KAGGLE_USERNAME`, `KAGGLE_KEY` | [kaggle.com](https://www.kaggle.com) | [Settings → API](https://www.kaggle.com/settings/api) → **Generate New Token** | Instant | Or legacy `~/.kaggle/kaggle.json` |
| **BibSonomy** | `BIBSONOMY_API_KEY`, `BIBSONOMY_USERNAME` | [bibsonomy.org](https://www.bibsonomy.org) | [Settings](https://www.bibsonomy.org/settings?selTab=1) → API block | Instant | Social bookmarking |
| **NOAA CDO** | `NOAA_API_KEY` | [ncei.noaa.gov/cdo-web/token](https://www.ncei.noaa.gov/cdo-web/token) | Submit email → token in email | Minutes | Header `token:`, not URL param |
| **openFDA** | `OPENFDA_API_KEY` | [api.data.gov/signup](https://api.data.gov/signup/) | Email → key from api.data.gov | Minutes | `?api_key=` on requests; 240 req/min |
| **OpenAlex** | `OPENALEX_API_KEY` | [openalex.org/api](https://openalex.org/api) | Optional premium key | Optional | **Works without key** (polite pool) |
| **STRING DB** | `STRING_DB_API_KEY` | [string-db.org](https://string-db.org) | Request via API or web form | Usually instant | PPI networks; optional for basic use |
| **Unpaywall** | `UNPAYWALL_EMAIL` | [unpaywall.org/products/api](https://unpaywall.org/products/api) | Use your email in `email=` param | Instant | Not a secret key — contact identity |
| **GBIF** | `GBIF_USER`, `GBIF_PASSWORD` | [gbif.org/user/register](https://www.gbif.org/user/register) | Account password auth | Instant | For bulk downloads |
| **NASA Earthdata** | `NASA_EARTHDATA_TOKEN` | [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov) | Register → profile → token | Instant | Satellite / CMR search |
| **ORCID** | `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET` | [orcid.org/developer-tools](https://orcid.org/developer-tools) | Register OAuth app | Sandbox fast; production review | Publishing module only |
| Harvard Dataverse | `HARVARD_DATAVERSE_API_KEY` | [dataverse.harvard.edu](https://dataverse.harvard.edu) | Account → API token | Instant | Datasets |
| Crossref Plus | `CROSSREF_PLUS_API_KEY` | [crossref.org/services/metadata-delivery-plus](https://www.crossref.org/services/metadata-delivery-plus/) | Membership / Plus | Manual | **Polite pool:** set `CROSSREF_MAILTO` only |

## Tier 4 — Manual approval (expect days)

| Service | Env var | How to apply | Typical wait |
|---------|---------|--------------|--------------|
| **Semantic Scholar** | `SEMANTIC_SCHOLAR_API_KEY` | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) → **Request an API Key** | 1–2 business days |
| **BASE (Bielefeld)** | `BASE_API_KEY` | [api.base-search.net](https://api.base-search.net/) → application form + use case | Few days |
| **DataCite** | `DATACITE_API_KEY` | [datacite.org](https://datacite.org) — member/API access | Manual |
| **OMIM** | `OMIM_API_KEY` | [omim.org/api](https://www.omim.org/api) | Manual approval |
| **DrugBank** | `DRUGBANK_API_KEY` | [go.drugbank.com](https://go.drugbank.com) | **Paid subscription** — stub when empty |

## Tier 5 — No API key required

These adapters work without registration (rate limits apply):

arXiv, PubMed (without NCBI key), Crossref (`CROSSREF_MAILTO` recommended), Europe PMC, DOAJ, DBLP, Zenodo, Figshare, Datacite (public), Inspire-HEP, PubChem, ChEMBL, ClinicalTrials.gov, Allen Brain Atlas, GBIF (read API), USGS, re3data, OpenReview, CyberLeninka, Math-Net.Ru, HuggingFace Datasets, and more — see `src/knowledge/config.py` → `SOURCE_REGISTRY`.

## Social publishing (optional)

| Platform | Env vars | Registration |
|----------|----------|--------------|
| Zenodo | `ZENODO_ACCESS_TOKEN` | [zenodo.org](https://zenodo.org) → Applications → personal access token |
| Twitter/X | `X_BEARER_TOKEN` | [developer.x.com](https://developer.x.com) |
| Mastodon | `MASTODON_ACCESS_TOKEN` | Instance → Preferences → Development |
| Bluesky | `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` | App password in Bluesky settings |
| Telegram | `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) |

---

# Русский

## Уровень 0 — Обязательно

| Сервис | Переменная | Регистрация | Шаги | Ожидание | Стоимость |
|--------|------------|-------------|------|----------|-----------|
| **OpenRouter** | `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) | Регистрация → [Ключи](https://openrouter.ai/settings/keys) → **Create Key** → `sk-or-...` | Подтвердить email | Бесплатные `:free` модели; ~50 запросов/день |

## Уровень 1 — LLM-провайдеры (опционально)

| Сервис | Переменная | Регистрация | Важно | Ожидание |
|--------|------------|-------------|-------|----------|
| **DeepSeek** | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) | **Отдельный** аккаунт от chat.deepseek.com; нужен **top-up** в Billing | Email + SMS |
| **xAI (Grok)** | `XAI_API_KEY` | [console.x.ai](https://console.x.ai) | Ключ `xai-...` показывается один раз | Сразу |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | [build.nvidia.com/settings/api-key](https://build.nvidia.com/settings/api-key) | `nvapi-...`, бесплатные dev-кредиты | Сразу |

Локально без облака: `OLLAMA_URL`, `LM_STUDIO_URL`.

## Уровень 2 — Поиск

| Сервис | Переменная | Регистрация | Ожидание | Стоимость (июль 2026) |
|--------|------------|-------------|----------|------------------------|
| **Brave** | `BRAVE_API_KEY` | [brave.com/search/api](https://brave.com/search/api) | Карта обязательна | $5 кредитов/мес (~1000 запросов) |
| **Tavily** | `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | Сразу | 1000 credits/мес, без карты |

## Уровень 3 — Научные базы (ключи из этого репозитория)

| Сервис | Переменные | Где регистрироваться | Письмо / ожидание |
|--------|------------|---------------------|-------------------|
| **NCBI** | `NCBI_API_KEY`, `NCBI_EMAIL` | [account.ncbi.nlm.nih.gov](https://account.ncbi.nlm.nih.gov) | Сразу; + письмо на `eutilities@ncbi.nlm.nih.gov` |
| **CORE** | `CORE_API_KEY` | [core.ac.uk/services/api](https://core.ac.uk/services/api) | Ключ **на email** |
| **Materials Project** | `MATERIALS_PROJECT_API_KEY` | [next-gen.materialsproject.org](https://next-gen.materialsproject.org) | Сразу |
| **Kaggle** | `KAGGLE_USERNAME`, `KAGGLE_KEY` | [kaggle.com/settings/api](https://www.kaggle.com/settings/api) | Сразу |
| **BibSonomy** | `BIBSONOMY_API_KEY`, `BIBSONOMY_USERNAME` | [bibsonomy.org/settings](https://www.bibsonomy.org/settings?selTab=1) | Сразу |
| **NOAA** | `NOAA_API_KEY` | [ncei.noaa.gov/cdo-web/token](https://www.ncei.noaa.gov/cdo-web/token) | Токен **на email** |
| **openFDA** | `OPENFDA_API_KEY` | [api.data.gov/signup](https://api.data.gov/signup/) | Письмо от api.data.gov |
| **OpenAlex** | `OPENALEX_API_KEY` | [openalex.org/api](https://openalex.org/api) | **Без ключа работает** |
| **STRING** | `STRING_DB_API_KEY` | [string-db.org](https://string-db.org) | Обычно сразу |
| **Unpaywall** | `UNPAYWALL_EMAIL` | [unpaywall.org/products/api](https://unpaywall.org/products/api) | Email в запросе |
| **GBIF** | `GBIF_USER`, `GBIF_PASSWORD` | [gbif.org/user/register](https://www.gbif.org/user/register) | Аккаунт |
| **NASA Earthdata** | `NASA_EARTHDATA_TOKEN` | [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov) | Сразу |
| **ORCID** | `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET` | [orcid.org/developer-tools](https://orcid.org/developer-tools) | 1–2 дня (sandbox быстрее) |

## Уровень 4 — Ручное одобрение

| Сервис | Переменная | Как | Срок |
|--------|------------|-----|------|
| **Semantic Scholar** | `SEMANTIC_SCHOLAR_API_KEY` | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) | 1–2 рабочих дня |
| **BASE** | `BASE_API_KEY` | [api.base-search.net](https://api.base-search.net/) + use case | Несколько дней |
| **DataCite** | `DATACITE_API_KEY` | datacite.org | Вручную |
| **OMIM** | `OMIM_API_KEY` | omim.org/api | Вручную |
| **DrugBank** | `DRUGBANK_API_KEY` | Подписка | Платно |

## Уровень 5 — Без ключа

arXiv, PubMed (медленнее без NCBI key), Crossref, Europe PMC, DOAJ, Zenodo, PubChem, ChEMBL, ClinicalTrials.gov и др. — см. `SOURCE_REGISTRY` в `src/knowledge/config.py`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401` from DeepSeek | Top up balance at platform.deepseek.com |
| `429` from NCBI | Add `NCBI_API_KEY`; respect 10 req/s |
| Brave bills unexpectedly | Monitor dashboard; $5 credits then per-query |
| BASE / Semantic Scholar empty | Key pending — use OpenAlex/arXiv meanwhile |
| Keys in git history | Rotate all keys; never commit `.env` |

## References

- Env template: `.env.example`
- Source registry: `src/knowledge/config.py`
- Key checker: `tools/check_keys.py`
- GitLab repo: `git@gitlab.com:cognitive-functors/turbo-cdi.git`
