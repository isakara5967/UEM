-- ============================================================================
-- UEM Learning Module - PostgreSQL Schema
-- ============================================================================
--
-- Tables for learning patterns and feedback persistence.
-- Run this after memory_schema.sql
--
-- Usage:
--   psql -U uem_user -d uem_db -f learning_schema.sql
-- ============================================================================

-- ============================================================================
-- PATTERNS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS patterns (
    id VARCHAR(255) PRIMARY KEY,

    -- Pattern data
    pattern_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,

    -- Embedding for similarity search (384 dimensions for all-MiniLM-L6-v2)
    embedding FLOAT[] DEFAULT NULL,

    -- Statistics
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    total_reward FLOAT DEFAULT 0.0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NULL,

    -- Extra data (JSON)
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT chk_pattern_type CHECK (
        pattern_type IN ('response', 'behavior', 'emotion', 'language')
    ),
    CONSTRAINT chk_success_count CHECK (success_count >= 0),
    CONSTRAINT chk_failure_count CHECK (failure_count >= 0)
);

-- Indexes for patterns
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_created_at ON patterns(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_success_count ON patterns(success_count DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_last_used ON patterns(last_used DESC);

-- Comment
COMMENT ON TABLE patterns IS 'Learning patterns - ogrenilen davranis patternleri';


-- ============================================================================
-- FEEDBACKS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS feedbacks (
    id VARCHAR(255) PRIMARY KEY,

    -- Feedback data
    interaction_id VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Optional fields
    user_id VARCHAR(255) DEFAULT NULL,
    context TEXT DEFAULT NULL,
    reason TEXT DEFAULT NULL,

    -- Constraints
    CONSTRAINT chk_feedback_type CHECK (
        feedback_type IN ('positive', 'negative', 'neutral', 'explicit', 'implicit')
    ),
    CONSTRAINT chk_feedback_value CHECK (value >= -1 AND value <= 1)
);

-- Indexes for feedbacks
CREATE INDEX IF NOT EXISTS idx_feedbacks_interaction ON feedbacks(interaction_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_user ON feedbacks(user_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_timestamp ON feedbacks(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_feedbacks_type ON feedbacks(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedbacks_value ON feedbacks(value);

-- Comment
COMMENT ON TABLE feedbacks IS 'Learning feedbacks - geri bildirim kayitlari';


-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate pattern success rate
CREATE OR REPLACE FUNCTION pattern_success_rate(p_id VARCHAR)
RETURNS FLOAT AS $$
DECLARE
    p patterns%ROWTYPE;
    total INTEGER;
BEGIN
    SELECT * INTO p FROM patterns WHERE id = p_id;
    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;

    total := p.success_count + p.failure_count;
    IF total = 0 THEN
        RETURN 0.5;  -- Default for no uses
    END IF;

    RETURN p.success_count::FLOAT / total::FLOAT;
END;
$$ LANGUAGE plpgsql;

-- Function to get average feedback value for an interaction
CREATE OR REPLACE FUNCTION interaction_avg_feedback(i_id VARCHAR)
RETURNS FLOAT AS $$
BEGIN
    RETURN (
        SELECT AVG(value)
        FROM feedbacks
        WHERE interaction_id = i_id
    );
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for pattern statistics
CREATE OR REPLACE VIEW v_pattern_stats AS
SELECT
    pattern_type,
    COUNT(*) as total_patterns,
    SUM(success_count) as total_successes,
    SUM(failure_count) as total_failures,
    AVG(CASE
        WHEN success_count + failure_count > 0
        THEN success_count::FLOAT / (success_count + failure_count)::FLOAT
        ELSE 0.5
    END) as avg_success_rate,
    AVG(total_reward) as avg_reward
FROM patterns
GROUP BY pattern_type;

-- View for feedback statistics
CREATE OR REPLACE VIEW v_feedback_stats AS
SELECT
    feedback_type,
    COUNT(*) as total_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT interaction_id) as unique_interactions
FROM feedbacks
GROUP BY feedback_type;


-- ============================================================================
-- CLEANUP
-- ============================================================================

-- Function to prune weak patterns
CREATE OR REPLACE FUNCTION prune_weak_patterns(
    min_uses INTEGER DEFAULT 5,
    max_failure_rate FLOAT DEFAULT 0.7
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM patterns
    WHERE (success_count + failure_count) >= min_uses
      AND (failure_count::FLOAT / (success_count + failure_count)::FLOAT) >= max_failure_rate;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old feedbacks
CREATE OR REPLACE FUNCTION clean_old_feedbacks(days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM feedbacks
    WHERE timestamp < NOW() - (days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
