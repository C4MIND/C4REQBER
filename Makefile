.PHONY: help install lint typecheck test test-backend test-frontend test-e2e coverage format security clean generate release db-migrate db-revision benchmark openapi

# ═══════════════════════════════════════════════════════════════════
# c4-cdi-turbo Makefile 2.0
# Professional CI/CD & DevEx automation
# ═══════════════════════════════════════════════════════════════════

## help — show all targets
help:
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║          c4-cdi-turbo — Development Commands (v2.0)             ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║  make help         — Show this help message                  ║"
	@echo "║  make install      — Install all dependencies + pre-commit   ║"
	@echo "║  make lint         — Run ruff + ESLint (fails on errors)     ║"
	@echo "║  make typecheck    — Run tsc + mypy                          ║"
	@echo "║  make typecheck-backend  — Run mypy on backend only          ║"
	@echo "║  make typecheck-frontend — Run tsc on frontend only          ║"
	@echo "║  make test         — Run pytest + vitest                     ║"
	@echo "║  make test-backend     — Run pytest only                     ║"
	@echo "║  make test-frontend    — Run vitest only                     ║"
	@echo "║  make test-e2e         — Run Playwright e2e tests            ║"
	@echo "║  make coverage     — Run pytest --cov + open HTML report     ║"
	@echo "║  make format       — Run black + prettier                    ║"
	@echo "║  make security     — Run trivy + npm audit + pip-audit       ║"
	@echo "║  make clean        — Remove build artifacts, caches          ║"
	@echo "║  make proto        — Generate proto code via buf             ║"
	@echo "║  make generate     — Proto code generation (stub)            ║"
	@echo "║  make benchmark    — Run scientific pattern benchmarks      ║"
	@echo "║  make docs         — Build documentation site               ║"
	@echo "║  make release           — Tag + changelog + build           ║"
	@echo "║  make db-migrate        — Run Alembic migrations            ║"
	@echo "║  make db-revision       — Create new Alembic migration      ║"
	@echo "║  make monitoring-up     — Start monitoring stack            ║"
	@echo "║  make monitoring-down   — Stop monitoring stack             ║"
	@echo "║  make pre-commit-install — Install pre-commit hooks         ║"
	@echo "║  make pre-commit-run    — Run all pre-commit checks         ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"

## install — pip install + pre-commit install
install:
	@echo "=== Installing backend dependencies ==="
	pip install -r requirements.txt
	pip install pytest pytest-cov mypy ruff black pip-audit pre-commit
	@echo "=== Installing pre-commit hooks ==="
	pre-commit install || true
	@echo "=== Frontend: TUI v9 (Go) — cd src/tui/v9 && go test ./... ==="
	@echo "=== Static site: landing/ (GitLab Pages) ==="

## install-verifiers — CVC5 + TLA+ + Alloy + Lean/Coq/Dafny/Agda/Z3 (macOS brew + jars)
install-verifiers:
	bash tools/install-verifiers.sh

## verify-backends — smoke-test CVC5/TLA+/Alloy on live binaries
verify-backends:
	python3 scripts/verify_backends_smoke.py

## lint — ruff (Python)
lint:
	@echo "=== Python lint (ruff) ==="
	cd . && ruff check src/

## typecheck — mypy backend + Go TUI compile check
typecheck: typecheck-backend typecheck-tui

## typecheck-tui — Go TUI v9 compile/test
typecheck-tui:
	@echo "=== Go TUI v9 typecheck ==="
	cd src/tui/v9 && go test ./... -count=1

## typecheck-backend — Python mypy type checking
typecheck-backend:
	@echo "=== Python mypy ==="
	python3 -m mypy src/

## test — pytest + Go TUI
test: test-backend test-tui

## test-backend — pytest
test-backend:
	@echo "=== Running backend tests (pytest + coverage) ==="
	PYTHONPATH=src python3 -m pytest tests/ --cov=src --cov-report=term --cov-report=html --cov-config=.coveragerc --cov-fail-under=60 -v

## test-e2e — verifier smoke + manual E2E script
test-e2e:
	@echo "=== Running verifier E2E smoke ==="
	python3 scripts/verify_backends_smoke.py
	bash scripts/manual_e2e_verifiers.sh

## test-tui — Go TUI v9 tests
test-tui:
	@echo "=== Running TUI v9 tests (go test) ==="
	cd src/tui/v9 && go test ./... -count=1

## coverage — pytest --cov + open HTML report
coverage:
	@echo "=== Running coverage analysis ==="
	PYTHONPATH=src pytest --cov=src --cov-report=html --cov-report=term
	@echo "=== Opening HTML coverage report ==="
	@open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html manually"

## format — black
format:
	@echo "=== Formatting Python (black) ==="
	cd . && black src/ tests/

## security — trivy + pip-audit
security:
	@echo "=== Trivy filesystem scan ==="
	trivy filesystem --scanners vuln,secret,misconfig . || true
	@echo "=== pip-audit ==="
	pip-audit --desc || true

## clean — rm build artifacts, __pycache__, .ruff_cache
clean:
	@echo "=== Cleaning build artifacts ==="
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info
	@echo "Clean complete."

## proto — generate code from proto files via buf
proto:
	@echo "=== Generating proto code ==="
	buf generate

## openapi — regenerate TUI v9 Go types from openapi/tui-v9.yaml
openapi:
	@echo "=== OpenAPI codegen (TUI v9) ==="
	cd src/tui/v9 && $(MAKE) openapi-gen

## openapi-export — regenerate openapi/fastapi.json from the live FastAPI app
openapi-export:
	@echo "=== Export FastAPI OpenAPI schema ==="
	python3 scripts/export_openapi.py

## openapi-check — validate TUI contract against FastAPI spec (REWORK_PLAN P3-1)
openapi-check:
	@echo "=== OpenAPI contract check (TUI v9) ==="
	python3 scripts/check_openapi_contract.py

## generate — proto code generation (stub)
generate:
	@echo "=== Proto code generation ==="
	@echo "Stub: add protoc commands here when .proto files are ready"
	@# protoc --python_out=src/api/proto proto/*.proto

## db-migrate — Run Alembic migrations

db-migrate:
	@echo "=== Running Alembic migrations ==="
	PYTHONPATH=src python3 -m alembic upgrade head

## db-revision — Create new Alembic migration (use: make db-revision msg="description")
db-revision:
	@echo "=== Creating Alembic migration (autogenerate from src/data/orm.py) ==="
	PYTHONPATH=src python3 -m alembic revision --autogenerate -m "$(msg)"

## benchmark — Run scientific pattern benchmarks
benchmark:
	@echo "=== Running scientific benchmarks ==="
	PYTHONPATH=src python3 -m pytest tests/benchmarks/ -v --tb=short --timeout=60 -p no:warnings

## docs — Build documentation site
docs:
	cd docs-site && npm install && npm run build

## release — tag + changelog + build
release:
	@echo "=== Creating release ==="
	@VERSION=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" 2>/dev/null || echo "6.1.0"); \
	echo "Version: $$VERSION"; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION" 2>/dev/null || echo "Tag already exists"; \
	git push origin "v$$VERSION" 2>/dev/null || echo "Push tag manually: git push origin v$$VERSION"
	@echo "=== Building artifacts ==="
	@make build-backend-artifact build-frontend-artifact 2>/dev/null || echo "Build artifacts skipped"

# ── Internal helpers ──

build-backend-artifact:
	@mkdir -p dist
	@tar czf dist/backend-$$(git describe --tags --always 2>/dev/null || echo "dev").tar.gz src/ requirements.txt pyproject.toml

build-frontend-artifact:
	@mkdir -p dist
	@tar czf dist/landing-$$(git describe --tags --always 2>/dev/null || echo "dev").tar.gz landing/

# ── Legacy aliases ──
dev:
	@echo "Starting c4-cdi-turbo..."
	@make backend & make frontend

backend:
	@echo "Starting FastAPI backend..."
	@PYTHONPATH=src python3 -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Static site: open landing/index.html or deploy via GitLab Pages (make pages)"

monitoring-up:  ## Start monitoring stack (Prometheus + Grafana + Alertmanager)
	docker-compose -f monitoring/docker-compose.yml up -d

monitoring-down:  ## Stop monitoring stack
	docker-compose -f monitoring/docker-compose.yml down

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install --install-hooks

pre-commit-run:  ## Run all pre-commit checks
	pre-commit run --all-files

docker-up:
	@docker-compose up -d

docker-down:
	@docker-compose down
docker-build:
	@docker-compose build
