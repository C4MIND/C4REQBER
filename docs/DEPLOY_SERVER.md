# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Minimal server deployment — no GPU required.

Requirements:
- CPU: 2+ cores
- RAM: 4GB (embeddings ~500MB) + 8GB if running local autocomplete model
- Disk: 2GB (code + models)
- Python 3.11+
- No GPU needed — BYOK model routes to OpenRouter cloud

Install:
```bash
git clone https://gitlab.com/c4reqber/c4reqber.git
cd c4reqber
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-server.txt  # minimal deps, no torch/mlx
cp .env.example .env
# Edit .env: add OPENROUTER_API_KEY
blast serve --mcp  # MCP server on stdio
# OR
make backend      # FastAPI on :8000
```

Docker:
```bash
docker build -t c4reqber -f Dockerfile.minimal .
docker run -p 8000:8000 --env-file .env c4reqber
```

Minimal requirements (requirements-server.txt):
```
httpx>=0.27
pydantic>=2
fastapi>=0.115
uvicorn>=0.30
rich>=13
numpy>=1.26
sentence-transformers>=2.7  # embeddings only, ~500MB download once
typer>=0.12
```

Cost: $0 (BYOK) + ~$0.02/request (OpenRouter via your API key)
"""
