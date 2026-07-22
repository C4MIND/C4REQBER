# Optional VPS hosting (not for end-user local install)

Use this only if **you** operate a server with a domain and want `api.yourdomain.org` behind Traefik + Let's Encrypt.

**Normal users should use:**

- `pip install c4reqber` + `blast setup` — see [docs/INSTALL.md](../../docs/INSTALL.md)
- `docker-compose.release.yml` — API on localhost (no Traefik)

## Files

| File | Purpose |
|------|---------|
| `docker-compose.vps-traefik.yml` | Postgres + API + web + Traefik reverse proxy |

## Required secrets (`.env` at repo root)

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | API auth (32+ chars; `openssl rand -hex 32`) |
| `DB_PASSWORD` | Postgres password |
| `OPENROUTER_API_KEY` | LLM provider (optional if using local LLM only) |
| `ACME_EMAIL` | Let's Encrypt registration email |
| `VPS_DOMAIN` | Public hostname (Traefik router rules) |

Optional: `CSRF_SECRET`, `CORS_ORIGINS`, `API_IMAGE_TAG`, `CI_REGISTRY_IMAGE`.

## Validate before deploy

From repository root:

```bash
cp .env.example .env
# Edit .env — set JWT_SECRET, DB_PASSWORD, ACME_EMAIL, VPS_DOMAIN

docker compose -f examples/hosting/docker-compose.vps-traefik.yml config
sh scripts/ci/validate_vps_compose.sh
```

## Deploy (full stack with Traefik)

```bash
docker compose -f examples/hosting/docker-compose.vps-traefik.yml --profile full up -d
curl -k https://api.${VPS_DOMAIN}/api/v1/health
```

API-only (no Traefik / landing): omit `--profile full` — starts Postgres + API on port 8000.

## Corporate SSL / proxy note

If `pip install` fails behind a corporate MITM proxy, configure `PIP_CERT` / system trust store —
see [INSTALL.md](../../docs/INSTALL.md); this is an environment tip, not a product feature.
