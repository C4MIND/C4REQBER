# Install c4reqber (end user)

**Product model:** you run everything **on your machine**. No hosted SaaS required.

## 1. Recommended — CLI + TUI (most users)

```bash
pip install c4reqber
# or from source: git clone + pip install -e ".[science]"
blast setup          # scientific packages only (GROMACS, OpenMM, …)
blast init           # interactive API key wizard → ~/.c4reqber/secrets.env
# or: blast config keys --assign OPENROUTER_API_KEY=sk-or-...
blast solve "your problem"
blast tui            # TUI v9 cockpit (Go)
blast serve --mcp    # MCP server for AI agents
```

Minimum: Python 3.11+, `OPENROUTER_API_KEY` in `secrets.env` or env (see [docs/API_KEYS.md](docs/API_KEYS.md)).

## 2. Optional — Docker API only

For a **local API server** without full Python dev install:

```bash
git clone git@gitlab.com:cognitive-functors/c4reqber.git
cd c4reqber
cp .env.example .env
# Edit .env: JWT_SECRET (32+ chars), OPENROUTER_API_KEY

# If the container registry is private:
docker login registry.gitlab.com

docker compose -f docker-compose.release.yml up -d
curl http://localhost:8000/api/v1/health
```

Image: `registry.gitlab.com/cognitive-functors/c4reqber/api:latest` (built on every green `main` pipeline).

## 3. Advanced — self-hosted VPS (optional)

If you want a **public domain + SSL** on your own server, see:

`examples/hosting/docker-compose.vps-traefik.yml`

This is **not** required for normal use.

## What CI `deploy-production` does

On GitLab `main`, after `build-api` succeeds, `deploy-production` **verifies** the registry image (pull + import smoke). It does **not** deploy to the maintainer's laptop or any shared host.

## Keys

Full registration guide: [docs/API_KEYS.md](docs/API_KEYS.md) · [mini Pages version](https://turbo-cdi-86c583.gitlab.io/docs/setup/api-keys.html)
