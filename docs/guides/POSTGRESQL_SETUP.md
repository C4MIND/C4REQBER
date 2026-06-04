# Reqber PostgreSQL Production Setup

This guide covers the complete PostgreSQL production setup for Reqber, including migration from SQLite, connection pooling configuration, and troubleshooting.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Migration from SQLite](#migration-from-sqlite)
3. [Connection Pooling](#connection-pooling)
4. [Configuration](#configuration)
5. [Docker Deployment](#docker-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Environment Setup

```bash
# Copy example environment
cp .env.example .env

# Edit .env with your PostgreSQL settings
# For local development with Docker:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=turbo_cdi
DB_USER=turbo_cdi
DB_PASSWORD=your_secure_password

# Or use DATABASE_URL directly:
DATABASE_URL=postgresql://turbo_cdi:your_secure_password@localhost:5432/turbo_cdi
```

### 2. Start PostgreSQL

```bash
# Using Docker Compose (production)
docker-compose -f docker-compose.prod.yml up -d postgres

# Or using local PostgreSQL
# macOS with Homebrew:
brew install postgresql@16
brew services start postgresql@16

# Ubuntu/Debian:
sudo apt-get install postgresql-16
sudo systemctl start postgresql
```

### 3. Initialize Database

```bash
# Run migrations
make db-migrate

# Or manually with Alembic
alembic upgrade head

# Seed initial data
make db-seed
```

---

## Migration from SQLite

### Why Migrate?

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Concurrency | Limited (file locks) | Excellent (MVCC) |
| Scalability | Single-node only | Horizontal scaling |
| Data types | Limited | Rich (JSONB, arrays, etc.) |
| Performance | Good for small datasets | Excellent for large datasets |
| Backups | File copy | Point-in-time recovery |

### Migration Steps

1. **Export SQLite data:**
```bash
# Export to SQL dump
sqlite3 data/turbo_cdi.db .dump > turbo_cdi_dump.sql

# Or use Python script
python scripts/export_sqlite.py
```

2. **Create PostgreSQL database:**
```bash
# Using psql
psql -U postgres -c "CREATE DATABASE turbo_cdi;"
psql -U postgres -c "CREATE USER turbo_cdi WITH PASSWORD 'your_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE turbo_cdi TO turbo_cdi;"
```

3. **Import to PostgreSQL:**
```bash
# Using pg_dump format (recommended)
pg_restore -U turbo_cdi -d turbo_cdi turbo_cdi_dump.sql

# Or using custom migration script
python scripts/migrate_sqlite_to_pg.py
```

4. **Verify migration:**
```bash
# Test connection
python -c "from src.data.database_pg import PostgreSQLDatabase; db = PostgreSQLDatabase(); print('OK')"

# Run health check
python scripts/db_health_check.py
```

### Migration Script Example

```python
# scripts/migrate_sqlite_to_pg.py
import asyncio
from src.data.database import Database
from src.data.database_pg import PostgreSQLDatabase

async def migrate():
    # Source: SQLite
    sqlite_db = Database("sqlite:///data/turbo_cdi.db")
    
    # Target: PostgreSQL
    pg_db = PostgreSQLDatabase()
    
    # Migration logic here
    # ...

if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## Connection Pooling

### Why Connection Pooling?

- **Performance**: Reuses connections instead of creating new ones
- **Resource management**: Limits concurrent connections
- **Stability**: Prevents connection exhaustion

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `POOL_SIZE` | 5 | Base pool size |
| `MAX_OVERFLOW` | 10 | Additional connections when pool exhausted |
| `POOL_TIMEOUT` | 30 | Seconds to wait for available connection |
| `POOL_RECYCLE` | 1800 | Seconds before connection is recycled |
| `POOL_PRE_PING` | true | Verify connection before use |

### Recommended Settings by Workload

```python
# Development (single user)
POOL_SIZE=2
MAX_OVERFLOW=3

# Small production (< 100 concurrent users)
POOL_SIZE=5
MAX_OVERFLOW=10

# Medium production (100-1000 users)
POOL_SIZE=10
MAX_OVERFLOW=20

# Large production (1000+ users)
POOL_SIZE=20
MAX_OVERFLOW=40
POOL_TIMEOUT=60
```

### Monitoring Pool Health

```python
from src.data.connection_pool import ConnectionPool
from src.config.database import get_database_config

config = get_database_config()
pool = ConnectionPool(
    url=config.get_effective_url(),
    pool_size=config.pool_size,
    max_overflow=config.max_overflow,
)

# Get pool status
status = pool.get_pool_status()
print(f"Pool size: {status['size']}")
print(f"Checked out: {status['checked_out']}")
print(f"Overflow: {status['overflow']}")

# Health check
health = pool.health_check()
print(f"Healthy: {health.is_healthy}")
print(f"Response time: {health.response_time_ms}ms")
```

---

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
# OR
DB_HOST=localhost
DB_PORT=5432
DB_NAME=turbo_cdi
DB_USER=turbo_cdi
DB_PASSWORD=secure_password

# Optional - Pooling
POOL_SIZE=5
MAX_OVERFLOW=10
POOL_TIMEOUT=30
POOL_RECYCLE=1800
POOL_PRE_PING=true
```

### Python Configuration

```python
from src.config.database import DatabaseConfig

# From environment
config = DatabaseConfig.from_env()

# Manual configuration
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="turbo_cdi",
    user="turbo_cdi",
    password="secure_password",
    pool_size=10,
    max_overflow=20,
)

# Get connection URL
url = config.get_effective_url()
# postgresql://turbo_cdi:secure_password@localhost:5432/turbo_cdi
```

---

## Docker Deployment

### Production Setup

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f postgres

# Scale API workers (if needed)
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

### Database Persistence

PostgreSQL data is persisted in a Docker volume:

```yaml
# docker-compose.prod.yml
volumes:
  postgres_data:
    driver: local
```

To backup:
```bash
# Create backup
docker exec turbo-cdi-postgres-1 pg_dump -U turbo_cdi turbo_cdi > backup.sql

# Restore from backup
cat backup.sql | docker exec -i turbo-cdi-postgres-1 psql -U turbo_cdi -d turbo_cdi
```

### Health Checks

PostgreSQL includes built-in health checks:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U turbo_cdi -d turbo_cdi"]
  interval: 10s
  timeout: 5s
  retries: 5
```

API waits for PostgreSQL to be healthy before starting:

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

```
Error: could not connect to server: Connection refused
```

**Solutions:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker-compose logs postgres

# Verify port is not blocked
lsof -i :5432

# Check pg_hba.conf for access rules
docker exec turbo-cdi-postgres-1 cat /var/lib/postgresql/data/pgdata/pg_hba.conf
```

#### 2. Pool Exhaustion

```
Error: QueuePool limit of size X overflow Y reached
```

**Solutions:**
```python
# Increase pool size
POOL_SIZE=20
MAX_OVERFLOW=40

# Check for connection leaks
# Ensure sessions are properly closed:
async with db.session() as session:
    # do work
    pass  # auto-closes

# Monitor pool usage
from src.data.connection_pool import ConnectionPool
pool = ConnectionPool(url)
print(pool.get_pool_status())
```

#### 3. SSL/TLS Issues

```
Error: sslmode value "require" invalid
```

**Solutions:**
```python
# For local development, disable SSL
DATABASE_URL=postgresql://user:pass@localhost/dbname?sslmode=disable

# For production, ensure certificates are valid
# Check server SSL:
psql "postgresql://user:pass@host/dbname?sslmode=require" -c "SHOW ssl;"
```

#### 4. Authentication Failed

```
Error: password authentication failed for user "turbo_cdi"
```

**Solutions:**
```bash
# Reset password
docker exec -it turbo-cdi-postgres-1 psql -U postgres -c "ALTER USER turbo_cdi WITH PASSWORD 'new_password';"

# Verify .env matches docker-compose
grep DB_ .env
grep DB_ docker-compose.prod.yml

# Check user exists
docker exec turbo-cdi-postgres-1 psql -U postgres -c "\du"
```

#### 5. Slow Queries

**Solutions:**
```sql
-- Enable query logging in postgresql.conf
log_min_duration_statement = 1000  -- log queries > 1s

-- Analyze slow queries
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM your_slow_query;

-- Check for missing indexes
SELECT schemaname, tablename, attname as column, n_tup_read, n_tup_fetch 
FROM pg_stats 
WHERE schemaname = 'public';
```

### Diagnostic Commands

```bash
# Check PostgreSQL version
docker exec turbo-cdi-postgres-1 psql -V

# List databases
docker exec turbo-cdi-postgres-1 psql -U turbo_cdi -c "\l"

# List tables
docker exec turbo-cdi-postgres-1 psql -U turbo_cdi -d turbo_cdi -c "\dt"

# Check active connections
docker exec turbo-cdi-postgres-1 psql -U turbo_cdi -c "SELECT * FROM pg_stat_activity;"

# Check table sizes
docker exec turbo-cdi-postgres-1 psql -U turbo_cdi -d turbo_cdi -c "
SELECT relname as table, pg_size_pretty(pg_total_relation_size(relid)) as size
FROM pg_catalog.pg_statio_user_tables 
ORDER BY pg_total_relation_size(relid) DESC;"
```

### Performance Tuning

```bash
# Edit postgresql.conf for production
# docker-compose.prod.yml volumes:
#   - ./config/postgresql.conf:/etc/postgresql/postgresql.conf

docker exec turbo-cdi-postgres-1 cat >> /var/lib/postgresql/data/pgdata/postgresql.conf <<EOF
# Memory settings (adjust based on available RAM)
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 16MB
maintenance_work_mem = 64MB

# Checkpoint settings
checkpoint_timeout = 10min
checkpoint_completion_target = 0.9
max_wal_size = 2GB

# Query planner
effective_io_concurrency = 200
random_page_cost = 1.1
EOF

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

---

## Security Best Practices

1. **Use strong passwords:** Minimum 16 characters, mixed case, numbers, symbols
2. **Enable SSL in production:** `sslmode=require` in DATABASE_URL
3. **Restrict network access:** Use Docker networks, firewall rules
4. **Regular backups:** Automate daily backups with `pg_dump`
5. **Update PostgreSQL:** Keep up with security patches
6. **Use dedicated user:** Don't use postgres superuser for application

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/index.html)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)
- [Reqber Architecture Docs](docs/ARCHITECTURE.md)
