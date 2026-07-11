# Optional VPS hosting (not for end-user local install)

Use this only if **you** operate a server with a domain and want `api.yourdomain.org` behind Traefik + Let's Encrypt.

Normal users should use:

- `pip install c4reqber` + `blast setup` — see [docs/INSTALL.md](../../docs/INSTALL.md)
- `docker-compose.release.yml` — API on localhost

## Files

| File | Purpose |
|------|---------|
| `docker-compose.vps-traefik.yml` | Postgres + API + web + Traefik reverse proxy |

```bash
cp .env.example .env
# Set JWT_SECRET, DB_PASSWORD, OPENROUTER_API_KEY, ACME_EMAIL, domain labels
docker compose -f examples/hosting/docker-compose.vps-traefik.yml --profile full up -d
```
