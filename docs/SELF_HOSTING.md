# Self-Hosting TURBO-CDI

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional)
- PostgreSQL 15+ (optional, SQLite default)

## Methods

### Method 1: Docker (Recommended)
```bash
git clone https://github.com/c4reqber/turbo-cdi.git
cd turbo-cdi
cp .env.example .env
# Edit .env with your settings
docker-compose -f examples/hosting/docker-compose.vps-traefik.yml up -d
```

### Method 2: Manual
```bash
git clone https://github.com/c4reqber/turbo-cdi.git
cd turbo-cdi
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make db-migrate
make backend
```

### Method 3: Desktop App
Download latest release from GitHub Releases.

## Configuration
See `.env.example` for all environment variables.

## Production Checklist
- [ ] Set strong JWT_SECRET
- [ ] Configure PostgreSQL (not SQLite)
- [ ] Set up Redis for caching
- [ ] Configure rate limiting
- [ ] Set up HTTPS
- [ ] Enable Sentry DSN
- [ ] Review CORS origins
