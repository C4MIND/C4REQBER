# TURBO-CDI Documentation

> **Primary remote:** [GitLab](https://gitlab.com/cognitive-functors/c4reqber) · **UI:** TUI v9 + static `landing/` (GitLab Pages). No `web-v2` SPA.

## 🚀 Quick Start

### Docker Compose (API only)

```bash
# Clone repository
git clone git@gitlab.com:cognitive-functors/c4reqber.git
cd c4reqber

# Start API (optional — most users use CLI/TUI locally)
docker compose -f docker-compose.release.yml up -d

# Access:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Static site: landing/ or GitLab Pages deploy
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."
export JWT_SECRET="your-secret"
export OPENROUTER_API_KEY="your-key"

# Run migrations
psql -f migrations/init.sql

# Start server
python -m src.api.server
```

## 📚 API Reference

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret", "name": "User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'
```

### Discovery

```bash
# Create discovery
curl -X POST http://localhost:8000/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem": "increase battery density", "max_hypotheses": 5}'
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        TURBO-CDI v4.5                       │
├─────────────────────────────────────────────────────────────┤
│  Web UI (React)    │    API (FastAPI)    │    Workers      │
│  Port: 3000        │    Port: 8000       │    Async        │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL        │    Redis            │    Monitoring   │
│  Data Storage      │    Cache/Queue      │    Prometheus   │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://localhost/turbo_cdi` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `JWT_SECRET` | JWT signing secret | `change-me` |
| `API_WORKERS` | Number of API workers | `4` |

## 📊 Features

- ✅ C4 Cognitive Geometry (27 operators)
- ✅ TRIZ 40 Principles
- ✅ Multi-Agent System (Analyst+Scientist+Critic+Synthesizer)
- ✅ Semantic Scholar Integration (200M papers)
- ✅ Explainability Engine
- ✅ Dashboard & Analytics
- ✅ WebSocket Real-time Updates

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Benchmarks
pytest tests/ -m benchmark
```

## 📄 License

Triple License: AGPL-3.0 / Apache-2.0-NC / Commercial
