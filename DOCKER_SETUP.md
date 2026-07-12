# DOCKER_SETUP.md

## Optimized Setup for Live Development

1. Clean cache: `docker builder prune -a -f`
2. Update docker-compose.yml with volumes:
   - api: `./src:/app/src`
   - web: `./landing:/usr/share/nginx/html:ro` (static site; web-v2 removed)
3. Optimized Dockerfile.simple with multi-stage pip cache, split requirements-simple.txt.
4. Run: `docker compose down && docker compose up -d --no-build`

Volumes enable live code reload without full rebuild. API and web now use latest changes instantly.

All commands tested. Containers healthy.