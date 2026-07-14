"""Initial PostgreSQL schema (users, discoveries, hypotheses, api_logs).

Revision ID: 001_initial
Revises:
Create Date: 2026-06-21
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            tier VARCHAR(50) DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS discoveries (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            problem TEXT NOT NULL,
            top_hypothesis TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            duration_seconds FLOAT,
            estimated_cost FLOAT,
            validation_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS hypotheses (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            discovery_id UUID REFERENCES discoveries(id) ON DELETE CASCADE,
            hypothesis_text TEXT NOT NULL,
            confidence FLOAT,
            method VARCHAR(100),
            c4_path TEXT[],
            triz_principles INTEGER[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS api_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            endpoint VARCHAR(255),
            method VARCHAR(10),
            status_code INTEGER,
            response_time_ms FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_discoveries_user_id ON discoveries(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_discoveries_created_at ON discoveries(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_hypotheses_discovery_id ON hypotheses(discovery_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at'
            ) THEN
                CREATE TRIGGER update_users_updated_at
                BEFORE UPDATE ON users
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'update_discoveries_updated_at'
            ) THEN
                CREATE TRIGGER update_discoveries_updated_at
                BEFORE UPDATE ON discoveries
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END $$
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_discoveries_updated_at ON discoveries")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column")
    op.execute("DROP TABLE IF EXISTS api_logs")
    op.execute("DROP TABLE IF EXISTS hypotheses")
    op.execute("DROP TABLE IF EXISTS discoveries")
    op.execute("DROP TABLE IF EXISTS users")