-- ============================================================================
-- UEM v2 - Memory Module PostgreSQL Schema
-- ============================================================================
--
-- Kurulum:
--   docker exec -i uem_v2_postgres psql -U uem -d uem_v2 < sql/memory_schema.sql
--
-- Temizlik (dikkatli kullan!):
--   DROP SCHEMA public CASCADE; CREATE SCHEMA public;
-- ============================================================================

-- ═══════════════════════════════════════════════════════════════════════════
-- ENUMS
-- ═══════════════════════════════════════════════════════════════════════════

-- Drop if exists (for re-running)
DROP TYPE IF EXISTS memory_type CASCADE;
DROP TYPE IF EXISTS relationship_type CASCADE;
DROP TYPE IF EXISTS interaction_type CASCADE;
DROP TYPE IF EXISTS episode_type CASCADE;

CREATE TYPE memory_type AS ENUM (
    'sensory', 'working', 'episodic', 'semantic', 'emotional', 'relationship'
);

CREATE TYPE relationship_type AS ENUM (
    'unknown', 'stranger', 'acquaintance', 'colleague',
    'friend', 'close_friend', 'family', 'rival', 'enemy', 'neutral'
);

CREATE TYPE interaction_type AS ENUM (
    'helped', 'cooperated', 'shared', 'protected', 'celebrated', 'comforted',
    'observed', 'conversed', 'traded',
    'competed', 'conflicted', 'harmed', 'betrayed', 'threatened', 'attacked'
);

CREATE TYPE episode_type AS ENUM (
    'encounter', 'interaction', 'observation', 'conflict',
    'cooperation', 'emotional', 'significant'
);

-- ═══════════════════════════════════════════════════════════════════════════
-- EPISODES
-- Olay hafızası - ne, nerede, ne zaman, kim
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS episodes CASCADE;

CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 5W1H
    what TEXT NOT NULL,
    location TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    participants TEXT[] DEFAULT '{}',  -- agent_id array
    why TEXT,
    how TEXT,

    -- Olay detayları
    episode_type episode_type NOT NULL DEFAULT 'encounter',
    duration_seconds FLOAT DEFAULT 0,

    -- Sonuç
    outcome TEXT,
    outcome_valence FLOAT DEFAULT 0 CHECK (outcome_valence >= -1 AND outcome_valence <= 1),

    -- Duygusal iz
    self_emotion_during TEXT,
    self_emotion_after TEXT,
    pleasure FLOAT,
    arousal FLOAT,
    dominance FLOAT,

    -- Memory metadata
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    emotional_valence FLOAT DEFAULT 0 CHECK (emotional_valence >= -1 AND emotional_valence <= 1),
    emotional_arousal FLOAT DEFAULT 0 CHECK (emotional_arousal >= 0 AND emotional_arousal <= 1),

    access_count INT DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Meta
    tags TEXT[] DEFAULT '{}',
    context JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_episodes_occurred_at ON episodes(occurred_at DESC);
CREATE INDEX idx_episodes_participants ON episodes USING GIN(participants);
CREATE INDEX idx_episodes_type ON episodes(episode_type);
CREATE INDEX idx_episodes_importance ON episodes(importance DESC);
CREATE INDEX idx_episodes_strength ON episodes(strength DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- RELATIONSHIPS
-- İlişki hafızası - bir agent ile tüm geçmiş
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS relationships CASCADE;

CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    agent_id TEXT NOT NULL UNIQUE,
    agent_name TEXT,

    relationship_type relationship_type NOT NULL DEFAULT 'stranger',
    relationship_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- İstatistikler
    total_interactions INT DEFAULT 0,
    positive_interactions INT DEFAULT 0,
    negative_interactions INT DEFAULT 0,
    neutral_interactions INT DEFAULT 0,

    -- Trust
    trust_score FLOAT DEFAULT 0.5 CHECK (trust_score >= 0 AND trust_score <= 1),

    -- Betrayal
    betrayal_count INT DEFAULT 0,
    last_betrayal TIMESTAMP WITH TIME ZONE,

    -- Duygusal özet
    overall_sentiment FLOAT DEFAULT 0 CHECK (overall_sentiment >= -1 AND overall_sentiment <= 1),
    dominant_emotion TEXT,

    -- Son etkileşim
    last_interaction TIMESTAMP WITH TIME ZONE,
    last_interaction_type interaction_type,

    -- Memory metadata
    strength FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,

    -- Meta
    notes TEXT[] DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_relationships_agent_id ON relationships(agent_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_relationships_trust ON relationships(trust_score);
CREATE INDEX idx_relationships_sentiment ON relationships(overall_sentiment);

-- ═══════════════════════════════════════════════════════════════════════════
-- INTERACTIONS
-- Tek bir etkileşim kaydı
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS interactions CASCADE;

CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    relationship_id UUID NOT NULL REFERENCES relationships(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE SET NULL,

    interaction_type interaction_type NOT NULL,
    context TEXT,

    -- Sonuç
    outcome TEXT,
    outcome_valence FLOAT DEFAULT 0 CHECK (outcome_valence >= -1 AND outcome_valence <= 1),

    -- Etki
    emotional_impact FLOAT DEFAULT 0,
    trust_impact FLOAT DEFAULT 0,

    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_relationship ON interactions(relationship_id);
CREATE INDEX idx_interactions_occurred_at ON interactions(occurred_at DESC);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);

-- ═══════════════════════════════════════════════════════════════════════════
-- SEMANTIC FACTS
-- Anlamsal bilgi - genel bilgi, kavramlar (subject-predicate-object)
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS semantic_facts CASCADE;

CREATE TABLE semantic_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,

    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    source TEXT,

    -- Memory metadata
    strength FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(subject, predicate, object)
);

CREATE INDEX idx_semantic_subject ON semantic_facts(subject);
CREATE INDEX idx_semantic_predicate ON semantic_facts(predicate);
CREATE INDEX idx_semantic_object ON semantic_facts(object);

-- ═══════════════════════════════════════════════════════════════════════════
-- EMOTIONAL MEMORIES
-- Duygusal anı - affect-tagged memory
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS emotional_memories CASCADE;

CREATE TABLE emotional_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    episode_id UUID REFERENCES episodes(id) ON DELETE SET NULL,

    primary_emotion TEXT NOT NULL,
    emotion_intensity FLOAT DEFAULT 0.5 CHECK (emotion_intensity >= 0 AND emotion_intensity <= 1),

    pleasure FLOAT DEFAULT 0,
    arousal FLOAT DEFAULT 0.5,
    dominance FLOAT DEFAULT 0.5,

    triggers TEXT[] DEFAULT '{}',
    is_flashbulb BOOLEAN DEFAULT FALSE,
    somatic_marker TEXT,

    -- Memory metadata
    strength FLOAT DEFAULT 1.0,
    importance FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_emotional_emotion ON emotional_memories(primary_emotion);
CREATE INDEX idx_emotional_intensity ON emotional_memories(emotion_intensity DESC);
CREATE INDEX idx_emotional_flashbulb ON emotional_memories(is_flashbulb) WHERE is_flashbulb = TRUE;

-- ═══════════════════════════════════════════════════════════════════════════
-- TRUST HISTORY
-- Trust modülü ile senkronizasyon için tarihçe
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS trust_history CASCADE;

CREATE TABLE trust_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    relationship_id UUID NOT NULL REFERENCES relationships(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,

    trust_value FLOAT NOT NULL CHECK (trust_value >= 0 AND trust_value <= 1),
    previous_value FLOAT,
    delta FLOAT,

    event_type TEXT,  -- Trust modülündeki event (helped_me, betrayal, etc.)
    event_context TEXT,

    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trust_history_agent ON trust_history(agent_id);
CREATE INDEX idx_trust_history_recorded ON trust_history(recorded_at DESC);
CREATE INDEX idx_trust_history_relationship ON trust_history(relationship_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- CYCLE METRICS
-- Monitoring dashboard için cycle metrikleri
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS cycle_metrics CASCADE;

CREATE TABLE cycle_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cycle_id INT NOT NULL,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_ms FLOAT,

    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Phase durations (JSONB for flexibility)
    phase_durations JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cycle_metrics_started ON cycle_metrics(started_at DESC);
CREATE INDEX idx_cycle_metrics_cycle_id ON cycle_metrics(cycle_id);
CREATE INDEX idx_cycle_metrics_success ON cycle_metrics(success);

-- ═══════════════════════════════════════════════════════════════════════════
-- ACTIVITY LOG
-- Dashboard için aktivite logları
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS activity_log CASCADE;

CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    event_type TEXT NOT NULL,
    source TEXT,
    cycle_id INT,

    data JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_log_created ON activity_log(created_at DESC);
CREATE INDEX idx_activity_log_event_type ON activity_log(event_type);

-- ═══════════════════════════════════════════════════════════════════════════
-- FUNCTIONS & TRIGGERS
-- ═══════════════════════════════════════════════════════════════════════════

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all relevant tables
DROP TRIGGER IF EXISTS episodes_updated_at ON episodes;
CREATE TRIGGER episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS relationships_updated_at ON relationships;
CREATE TRIGGER relationships_updated_at
    BEFORE UPDATE ON relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS semantic_facts_updated_at ON semantic_facts;
CREATE TRIGGER semantic_facts_updated_at
    BEFORE UPDATE ON semantic_facts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS emotional_memories_updated_at ON emotional_memories;
CREATE TRIGGER emotional_memories_updated_at
    BEFORE UPDATE ON emotional_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════
-- DECAY FUNCTION
-- Bellek zayıflama - cron job ile periyodik çağrılabilir
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION apply_memory_decay(decay_rate FLOAT DEFAULT 0.01)
RETURNS TABLE(
    episodes_affected INT,
    relationships_affected INT,
    semantic_affected INT,
    emotional_affected INT
) AS $$
DECLARE
    ep_count INT;
    rel_count INT;
    sem_count INT;
    emo_count INT;
BEGIN
    -- Episodes
    UPDATE episodes
    SET strength = GREATEST(0, strength - decay_rate * (1 - importance * 0.5))
    WHERE strength > 0;
    GET DIAGNOSTICS ep_count = ROW_COUNT;

    -- Relationships - daha yavaş decay
    UPDATE relationships
    SET strength = GREATEST(0, strength - decay_rate * 0.5 * (1 - importance * 0.5))
    WHERE strength > 0;
    GET DIAGNOSTICS rel_count = ROW_COUNT;

    -- Semantic facts - en yavaş decay
    UPDATE semantic_facts
    SET strength = GREATEST(0, strength - decay_rate * 0.2 * (1 - importance * 0.5))
    WHERE strength > 0;
    GET DIAGNOSTICS sem_count = ROW_COUNT;

    -- Emotional memories - importance yüksekse çok yavaş
    UPDATE emotional_memories
    SET strength = GREATEST(0, strength - decay_rate * 0.3 * (1 - importance * 0.7))
    WHERE strength > 0;
    GET DIAGNOSTICS emo_count = ROW_COUNT;

    RETURN QUERY SELECT ep_count, rel_count, sem_count, emo_count;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
-- UTILITY FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- Touch (access) an episode
CREATE OR REPLACE FUNCTION touch_episode(episode_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE episodes
    SET
        last_accessed = NOW(),
        access_count = access_count + 1,
        strength = LEAST(1.0, strength + 0.05)
    WHERE id = episode_id;
END;
$$ LANGUAGE plpgsql;

-- Get memory stats
CREATE OR REPLACE FUNCTION get_memory_stats()
RETURNS TABLE(
    total_episodes BIGINT,
    total_relationships BIGINT,
    total_interactions BIGINT,
    total_semantic_facts BIGINT,
    total_emotional_memories BIGINT,
    avg_episode_strength FLOAT,
    avg_relationship_trust FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM episodes),
        (SELECT COUNT(*) FROM relationships),
        (SELECT COUNT(*) FROM interactions),
        (SELECT COUNT(*) FROM semantic_facts),
        (SELECT COUNT(*) FROM emotional_memories),
        (SELECT COALESCE(AVG(strength), 0) FROM episodes),
        (SELECT COALESCE(AVG(trust_score), 0.5) FROM relationships);
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
-- CLEANUP: Remove weak memories
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION cleanup_weak_memories(strength_threshold FLOAT DEFAULT 0.1)
RETURNS TABLE(
    episodes_deleted INT,
    semantic_deleted INT,
    emotional_deleted INT
) AS $$
DECLARE
    ep_count INT;
    sem_count INT;
    emo_count INT;
BEGIN
    -- Episodes (keep important ones)
    DELETE FROM episodes
    WHERE strength < strength_threshold AND importance < 0.5;
    GET DIAGNOSTICS ep_count = ROW_COUNT;

    -- Semantic facts
    DELETE FROM semantic_facts
    WHERE strength < strength_threshold * 0.5;
    GET DIAGNOSTICS sem_count = ROW_COUNT;

    -- Emotional memories (keep flashbulb)
    DELETE FROM emotional_memories
    WHERE strength < strength_threshold * 0.3 AND NOT is_flashbulb;
    GET DIAGNOSTICS emo_count = ROW_COUNT;

    -- Note: Relationships are never deleted, only marked inactive

    RETURN QUERY SELECT ep_count, sem_count, emo_count;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
-- GRANT PERMISSIONS (if needed)
-- ═══════════════════════════════════════════════════════════════════════════

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO uem;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uem;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO uem;
