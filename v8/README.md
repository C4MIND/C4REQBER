# TURBO-CDI v8.4 - Cognitive Discovery Intelligence Platform

![TURBO-CDI Logo](https://img.shields.io/badge/TURBO--CDI-v8.4-blue?logo=rocket&logoColor=white)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-green.svg)
![Clean Architecture](https://img.shields.io/badge/architecture-clean--hexagonal-red.svg)
![CQRS](https://img.shields.io/badge/pattern-CQRS-orange.svg)

> **Enterprise-Grade Cognitive Operating System for Transformational Knowledge Discovery**

TURBO-CDI is a revolutionary Clean Architecture enterprise system that revolutionizes how humans discover, process, and transform knowledge. Built with domain-driven design principles, CQRS pattern, and advanced cognitive algorithms, it provides automated knowledge discovery, anomaly detection, and intelligent transformation capabilities.

## 🎯 Key Features

### 🧠 Cognitive Intelligence
- **QZRF Operators**: Cognitive transformation algorithms for knowledge restructuring
- **Automated Discovery**: Machine-driven anomaly detection and pattern recognition
- **Presupposition Analysis**: Identify hidden assumptions in theoretical frameworks
- **Multi-Modal Reasoning**: Support for diverse knowledge representations

### 🏛️ Enterprise Architecture
- **Clean Architecture**: Hexagonal design with strict layer separation
- **CQRS Pattern**: Command/Query Responsibility Segregation for optimized operations
- **Domain-Driven Design**: Pure domain logic with rich business rules
- **Event Sourcing**: Complete auditability and temporal consistency

### 🚀 Production Ready
- **REST API**: FastAPI-powered REST endpoints with OpenAPI documentation
- **WebSocket Support**: Real-time discovery streams and system monitoring
- **Health Monitoring**: Multi-level system health checks and metrics
- **CLI Interface**: Rich command-line interface with progress tracking
- **Async Architecture**: Full async/await support for high concurrency

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  FastAPI REST API  │   WebSockets    │    CLI       │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                 APPLICATION LAYER                        │
│  ┌─────────────────────────────────────────────────────┐ │
│  │    Use Cases     │     App Services    │   Events    │ │
│  │      DTOs        │     CQRS Commands   │  Monitoring │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                  DOMAIN LAYER                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │   Entities    │   Domain Services │ Event Publisher │ │
│  │  Aggregates   │    Business Rules │   Factories     │ │
│  │   ValueObjects│  Repositories     │   Invariants    │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                INFRASTRUCTURE LAYER                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │   SQLAlchemy   │    External APIs    │   Health      │ │
│  │  Redis Cache   │  ChromaDB Vectors   │   Monitoring  │ │
│  │  PostgreSQL    │    LLM Services     │  Observability│ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.9+
PostgreSQL (recommended) or SQLite
Redis (optional, for caching)
```

### Installation

```bash
# Clone repository
git clone https://github.com/turbo-cdi/turbo-cdi.git
cd turbo-cdi

# Install dependencies
pip install -e ".[dev,gpu]"
```

### Configuration

Create `.env` file:
```bash
# Database
DATABASE_URL="postgresql+asyncpg://user:pass@localhost/turbo_cdi"

# External Services
OPENAI_API_KEY="your-openai-key"
CHROMADB_URL="http://localhost:8000"
REDIS_URL="redis://localhost:6379"

# System Settings
DEBUG_MODE=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### Usage

#### CLI Interface
```bash
# Check system status
turbo-cdi status

# Create a knowledge corpus
turbo-cdi corpus create physics_corpus --name "Quantum Physics" --domain physics

# Run knowledge discovery
turbo-cdi discovery analyze physics_corpus

# Start API server
turbo-cdi serve --host 0.0.0.0 --port 8000
```

#### REST API
```bash
# Start server
turbo-cdi serve

# Health check
curl http://localhost:8000/api/v1/health

# Create corpus
curl -X POST "http://localhost:8000/api/v1/corpora/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "quantum_physics",
    "name": "Quantum Physics Corpus",
    "domain": "physics"
  }'

# List corpora
curl "http://localhost:8000/api/v1/corpora/"
```

#### WebSocket Real-time
```javascript
// Connect to discovery stream
const ws = new WebSocket('ws://localhost:8000/discovery/my-client-123');

// Start real-time discovery
ws.send(JSON.stringify({
  command: 'start_discovery',
  corpus_id: 'quantum_physics'
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Discovery update:', data);
};
```

## 📚 Core Concepts

### 🔍 Knowledge Discovery
- **Agent-Driven Analysis**: Autonomous anomaly detection in knowledge structures
- **Pattern Recognition**: Identification of contradictions and gaps
- **Insight Generation**: Automated hypothesis formation and validation

### 🔄 Cognitive Transformations
- **QZRF Operators**: Quantum-inspired transformation algorithms
- **Multi-Level Processing**: Abstract/concrete representation shifts
- **Bridge Building**: Interdisciplinary knowledge integration

### 🧪 Presupposition Analysis
- **Hidden Assumptions**: Detection of implicit beliefs in theories
- **Contradiction Resolution**: Automated consistency checking
- **Validation Frameworks**: Theory verification against empirical data

## 🎨 APIs & Interfaces

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/corpora` | GET | List knowledge corpora |
| `/api/v1/corpora/{id}` | POST | Create new corpus |
| `/api/v1/corpora/{id}` | GET | Get corpus details |
| `/api/v1/corpora/{id}` | PUT | Update corpus |
| `/api/v1/corpora/{id}` | DELETE | Delete corpus |
| `/api/v1/discovery/analyze` | POST | Run knowledge discovery |
| `/api/v1/discovery/transformations` | POST | Apply cognitive transformations |
| `/api/v1/health` | GET | System health check |
| `/api/v1/health/database` | GET | Database health |
| `/api/v1/health/metrics` | GET | System metrics |

### CLI Commands

```bash
turbo-cdi --help                 # Show available commands
turbo-cdi corpus --help          # Corpus management
turbo-cdi discovery --help       # Knowledge discovery
turbo-cdi system --help          # System operations

# Example workflow
turbo-cdi corpus create my_corpus --name "My Research" --domain biology
turbo-cdi corpus list
turbo-cdi discovery analyze my_corpus
turbo-cdi corpus show my_corpus
turbo-cdi system health
```

### WebSocket Events

```javascript
// Discovery Stream
ws://host:port/discovery/{client_id}
// Events: progress, anomaly_found, transformation_applied, completed

// System Monitoring
ws://host:port/system/{client_id}
// Events: metrics_update, health_alert, system_event
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///:memory:` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `CHROMADB_URL` | ChromaDB vector database URL | `http://localhost:8000` |
| `OPENAI_API_KEY` | OpenAI API key | Required for LLM features |
| `API_HOST` | API server host | `127.0.0.1` |
| `API_PORT` | API server port | `8000` |
| `DEBUG_MODE` | Enable debug features | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Database Setup

```bash
# PostgreSQL setup
createdb turbo_cdi
psql turbo_cdi -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Run migrations
turbo-cdi system migrate
```

## 🧪 Testing & Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=turbo_cdi --cov-report=html

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
pytest -m "e2e"

# Development server with reload
turbo-cdi serve --reload
```

## 📊 Monitoring & Health

### Health Checks
- **Database connectivity**: Connection pool status and response times
- **External services**: LLM APIs, vector databases, cache systems
- **System resources**: CPU, memory, disk usage monitoring
- **Application metrics**: Request rates, error rates, performance stats

### Metrics Collection
- **Prometheus integration**: Standard metrics export
- **Application events**: Business operation tracking
- **Performance monitoring**: Response times and throughput
- **Error tracking**: Exception rates and failure patterns

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t turbo-cdi:v8.4 .

# Run with PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e REDIS_URL="redis://..." \
  -v /data:/app/data \
  turbo-cdi:v8.4
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: turbo-cdi
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: turbo-cdi:v8.4
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
        - name: REDIS_URL
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
```

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone
git clone https://github.com/your-username/turbo-cdi.git
cd turbo-cdi

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Code Quality
```bash
# Type checking
mypy turbo_cdi

# Code formatting
black turbo_cdi
isort turbo_cdi

# Linting
ruff turbo_cdi

# Security scanning
bandit -r turbo_cdi
```

### Domain-First Development
1. **Domain Modeling**: Define entities, value objects, and business rules
2. **Use Cases**: Describe application workflows and commands
3. **Infrastructure**: Implement adapters and external integrations
4. **Testing**: Write tests before implementation
5. **Documentation**: Update docs for new features

## 📝 License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with **Clean Architecture** principles
- Powered by **FastAPI**, **SQLAlchemy**, and **Pydantic**
- Inspired by Domain-Driven Design and CQRS patterns
- Cognitive algorithms based on advanced research paradigms

---

**TURBO-CDI v8.4** - *Transforming Knowledge Discovery Through Cognitive Intelligence* 🚀🧠