-- C4 COGNOS — Discovery Lab Database Schema
-- Extracted from discovery_lab.py Pydantic models

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

-- 1. knowledge_corpora: bounded knowledge corpus metadata
CREATE TABLE IF NOT EXISTS knowledge_corpora (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    epoch_end TEXT NOT NULL,
    subdomains TEXT NOT NULL DEFAULT '[]',
    constraints TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    user_id TEXT,
    project_id TEXT
);

-- 2. corpus_facts: individual facts belonging to a corpus
CREATE TABLE IF NOT EXISTS corpus_facts (
    id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    statement TEXT NOT NULL,
    source TEXT,
    year INTEGER,
    domain TEXT,
    c4_state TEXT,
    FOREIGN KEY (corpus_id) REFERENCES knowledge_corpora(id) ON DELETE CASCADE
);

-- 3. corpus_theories: theories with constraints belonging to a corpus
CREATE TABLE IF NOT EXISTS corpus_theories (
    id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    name TEXT NOT NULL,
    principles TEXT NOT NULL DEFAULT '[]',
    equations TEXT NOT NULL DEFAULT '[]',
    domain TEXT,
    FOREIGN KEY (corpus_id) REFERENCES knowledge_corpora(id) ON DELETE CASCADE
);

-- 4. anomalies: discovered contradictions or unexplained phenomena
CREATE TABLE IF NOT EXISTS anomalies (
    id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('empirical', 'theoretical', 'predictive')),
    fact_statement TEXT NOT NULL,
    theory_name TEXT NOT NULL,
    conflict_description TEXT NOT NULL,
    criticality TEXT NOT NULL CHECK(criticality IN ('low', 'medium', 'high', 'critical')),
    c4_state TEXT,
    resolved INTEGER DEFAULT 0 CHECK(resolved IN (0, 1)),
    FOREIGN KEY (corpus_id) REFERENCES knowledge_corpora(id) ON DELETE CASCADE
);

-- 5. presuppositions: extracted hidden assumptions from theories
CREATE TABLE IF NOT EXISTS presuppositions (
    id TEXT PRIMARY KEY,
    theory_id TEXT NOT NULL,
    theory_name TEXT NOT NULL,
    statement TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('ontological', 'epistemological', 'methodological', 'metaphysical')),
    status TEXT DEFAULT 'accepted' CHECK(status IN ('accepted', 'questioned', 'inverted')),
    inverted_statement TEXT,
    implications TEXT DEFAULT '[]',
    FOREIGN KEY (theory_id) REFERENCES corpus_theories(id) ON DELETE CASCADE
);

-- 6. trajectories: sequences of cognitive transformations
CREATE TABLE IF NOT EXISTS trajectories (
    id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    start_state TEXT NOT NULL,
    current_state TEXT NOT NULL,
    transformations TEXT NOT NULL DEFAULT '[]',
    goal_state TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (corpus_id) REFERENCES knowledge_corpora(id) ON DELETE CASCADE
);

-- 7. synthesized_theories: final synthesized theory outputs
CREATE TABLE IF NOT EXISTS synthesized_theories (
    id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    name TEXT NOT NULL,
    postulates TEXT NOT NULL DEFAULT '[]',
    consequences TEXT NOT NULL DEFAULT '[]',
    equations TEXT DEFAULT '[]',
    confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    corpus_compatibility REAL CHECK(corpus_compatibility >= 0.0 AND corpus_compatibility <= 1.0),
    predictions TEXT DEFAULT '[]',
    unresolved TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (corpus_id) REFERENCES knowledge_corpora(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_knowledge_corpora_user ON knowledge_corpora(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_corpora_project ON knowledge_corpora(project_id);

CREATE INDEX IF NOT EXISTS idx_corpus_facts_corpus ON corpus_facts(corpus_id);
CREATE INDEX IF NOT EXISTS idx_corpus_theories_corpus ON corpus_theories(corpus_id);

CREATE INDEX IF NOT EXISTS idx_anomalies_corpus ON anomalies(corpus_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_type ON anomalies(type);
CREATE INDEX IF NOT EXISTS idx_anomalies_criticality ON anomalies(criticality);

CREATE INDEX IF NOT EXISTS idx_presuppositions_theory ON presuppositions(theory_id);
CREATE INDEX IF NOT EXISTS idx_presuppositions_status ON presuppositions(status);

CREATE INDEX IF NOT EXISTS idx_trajectories_corpus ON trajectories(corpus_id);

CREATE INDEX IF NOT EXISTS idx_synthesized_theories_corpus ON synthesized_theories(corpus_id);
