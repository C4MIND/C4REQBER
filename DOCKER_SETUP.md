# DOCKER_SETUP.md

## Optimized Setup for Live Development

1. Clean cache: `docker builder prune -a -f`
2. Update docker-compose.yml with volumes:
   - api: `./src:/app/src`
   - web: `./web-v2/dist:/usr/share/nginx/html:ro` (or dev mode)
3. Optimized Dockerfile.simple with multi-stage pip cache, split requirements-simple.txt.
4. Run: `docker compose down && docker compose up -d --no-build`

Volumes enable live code reload without full rebuild. API and web now use latest changes instantly.

All commands tested. Containers healthy.