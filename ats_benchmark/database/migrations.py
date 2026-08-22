"""SQLite database schema and migrations for ATS Resume Benchmark."""
import sqlite3

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comparison_id TEXT NOT NULL,
    model TEXT NOT NULL,
    jd TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    
    -- AI Scores
    ai_status TEXT DEFAULT 'STRONG MATCH',
    ai_overall_reported REAL,
    ai_overall_calculated REAL,
    ai_keyword_match REAL,
    ai_skills_coverage REAL,
    ai_ats_formatting REAL,
    ai_role_alignment REAL,
    ai_impact_metrics REAL,
    
    -- Human Scores
    human_status TEXT DEFAULT 'MODERATE MATCH',
    human_overall_reported REAL,
    human_overall_calculated REAL,
    human_keyword_match REAL,
    human_skills_coverage REAL,
    human_ats_formatting REAL,
    human_role_alignment REAL,
    human_impact_metrics REAL,
    
    -- Comparison Metrics
    reported_ats_advantage REAL,
    calculated_ats_advantage REAL,
    relative_increase_percent REAL,
    winner TEXT NOT NULL DEFAULT 'UNKNOWN',
    
    -- Qualitative
    ai_strengths TEXT,
    ai_weaknesses TEXT,
    human_strengths TEXT,
    human_weaknesses TEXT,
    winner_reasons TEXT,
    
    -- Audit & Metadata
    claude_chat_url TEXT,
    raw_report_text TEXT,
    is_math_consistent INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    
    UNIQUE(model, jd, version)
);

CREATE INDEX IF NOT EXISTS idx_comparisons_active ON comparisons(is_active);
CREATE INDEX IF NOT EXISTS idx_comparisons_model ON comparisons(model);
CREATE INDEX IF NOT EXISTS idx_comparisons_jd ON comparisons(jd);
CREATE INDEX IF NOT EXISTS idx_comparisons_comp_id ON comparisons(comparison_id);
"""


def init_db(conn: sqlite3.Connection):
    """Initializes SQLite schema and ensures WAL mode is enabled."""
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(CREATE_TABLES_SQL)
    conn.commit()
