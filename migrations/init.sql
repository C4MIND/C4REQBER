-- Initialize database schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discoveries table
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
);

-- Hypotheses table
CREATE TABLE IF NOT EXISTS hypotheses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discovery_id UUID REFERENCES discoveries(id) ON DELETE CASCADE,
    hypothesis_text TEXT NOT NULL,
    confidence FLOAT,
    method VARCHAR(100),
    c4_path TEXT[],
    triz_principles INTEGER[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API logs for rate limiting
CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_discoveries_user_id ON discoveries(user_id);
CREATE INDEX idx_discoveries_created_at ON discoveries(created_at);
CREATE INDEX idx_hypotheses_discovery_id ON hypotheses(discovery_id);
CREATE INDEX idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at);

-- Update trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_discoveries_updated_at BEFORE UPDATE ON discoveries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
