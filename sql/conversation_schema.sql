-- ============================================================================
-- UEM v2 - Conversation Memory PostgreSQL Schema
-- ============================================================================
--
-- Kurulum:
--   docker exec -i uem_v2_postgres psql -U uem -d uem_v2 < sql/conversation_schema.sql
--
-- Bu sema memory_schema.sql'den SONRA calistirilmalidir.
-- ============================================================================

-- ═══════════════════════════════════════════════════════════════════════════
-- CONVERSATIONS
-- Sohbet oturumu - DialogueTurn'lerin koleksiyonu
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS dialogue_turns CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Oturum bilgileri
    session_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    user_id TEXT,
    agent_id TEXT NOT NULL DEFAULT 'default',

    -- Zaman bilgisi
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Ozet bilgiler
    turn_count INT DEFAULT 0,
    summary TEXT,
    main_topics TEXT[] DEFAULT '{}',
    resolved_intents TEXT[] DEFAULT '{}',

    -- Duygusal akis
    emotional_arc FLOAT[] DEFAULT '{}',
    dominant_emotion TEXT,
    average_valence FLOAT DEFAULT 0,

    -- Iliskili episode
    episode_id UUID REFERENCES episodes(id) ON DELETE SET NULL,

    -- Sohbet kalitesi
    coherence_score FLOAT DEFAULT 1.0 CHECK (coherence_score >= 0 AND coherence_score <= 1),
    engagement_score FLOAT DEFAULT 0.5 CHECK (engagement_score >= 0 AND engagement_score <= 1),

    -- Memory metadata
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Meta
    tags TEXT[] DEFAULT '{}',
    context JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_started_at ON conversations(started_at DESC);
CREATE INDEX idx_conversations_is_active ON conversations(is_active);
CREATE INDEX idx_conversations_topics ON conversations USING GIN(main_topics);
CREATE INDEX idx_conversations_importance ON conversations(importance DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- DIALOGUE TURNS
-- Tek bir diyalog turu - user/agent mesaji
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE dialogue_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Mesaj bilgileri
    role TEXT NOT NULL CHECK (role IN ('user', 'agent', 'system')),
    content TEXT NOT NULL,

    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Duygusal analiz
    emotional_valence FLOAT DEFAULT 0 CHECK (emotional_valence >= -1 AND emotional_valence <= 1),
    emotional_arousal FLOAT DEFAULT 0 CHECK (emotional_arousal >= 0 AND emotional_arousal <= 1),
    detected_emotion TEXT,

    -- Intent ve topic
    intent TEXT,
    topics TEXT[] DEFAULT '{}',

    -- Embedding (semantic search icin)
    embedding FLOAT[],

    -- Meta
    extra_data JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_dialogue_turns_conversation ON dialogue_turns(conversation_id);
CREATE INDEX idx_dialogue_turns_timestamp ON dialogue_turns(timestamp DESC);
CREATE INDEX idx_dialogue_turns_role ON dialogue_turns(role);
CREATE INDEX idx_dialogue_turns_emotion ON dialogue_turns(detected_emotion);
CREATE INDEX idx_dialogue_turns_topics ON dialogue_turns USING GIN(topics);

-- Full-text search index for content
CREATE INDEX idx_dialogue_turns_content_fts ON dialogue_turns
    USING GIN(to_tsvector('english', content));

-- ═══════════════════════════════════════════════════════════════════════════
-- CONVERSATION KEYWORDS
-- Hizli arama icin keyword index
-- ═══════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS conversation_keywords CASCADE;

CREATE TABLE conversation_keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    keyword TEXT NOT NULL,
    turn_id UUID NOT NULL REFERENCES dialogue_turns(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    frequency INT DEFAULT 1,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversation_keywords_keyword ON conversation_keywords(keyword);
CREATE INDEX idx_conversation_keywords_turn ON conversation_keywords(turn_id);
CREATE INDEX idx_conversation_keywords_conversation ON conversation_keywords(conversation_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGERS
-- ═══════════════════════════════════════════════════════════════════════════

-- Updated_at trigger for conversations
DROP TRIGGER IF EXISTS conversations_updated_at ON conversations;
CREATE TRIGGER conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-update turn_count when turn is added
CREATE OR REPLACE FUNCTION update_conversation_turn_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET
        turn_count = turn_count + 1,
        last_accessed = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS dialogue_turns_update_count ON dialogue_turns;
CREATE TRIGGER dialogue_turns_update_count
    AFTER INSERT ON dialogue_turns
    FOR EACH ROW EXECUTE FUNCTION update_conversation_turn_count();

-- Update emotional arc when turn is added
CREATE OR REPLACE FUNCTION update_conversation_emotional_arc()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET
        emotional_arc = array_append(emotional_arc, NEW.emotional_valence),
        average_valence = (
            SELECT COALESCE(AVG(emotional_valence), 0)
            FROM dialogue_turns
            WHERE conversation_id = NEW.conversation_id
        )
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS dialogue_turns_emotional_arc ON dialogue_turns;
CREATE TRIGGER dialogue_turns_emotional_arc
    AFTER INSERT ON dialogue_turns
    FOR EACH ROW EXECUTE FUNCTION update_conversation_emotional_arc();

-- ═══════════════════════════════════════════════════════════════════════════
-- UTILITY FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- Touch (access) a conversation
CREATE OR REPLACE FUNCTION touch_conversation(conv_session_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE conversations
    SET
        last_accessed = NOW(),
        access_count = access_count + 1,
        strength = LEAST(1.0, strength + 0.05)
    WHERE session_id = conv_session_id;
END;
$$ LANGUAGE plpgsql;

-- End a conversation
CREATE OR REPLACE FUNCTION end_conversation(
    conv_session_id UUID,
    conv_summary TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE conversations
    SET
        is_active = FALSE,
        ended_at = NOW(),
        summary = COALESCE(conv_summary, summary)
    WHERE session_id = conv_session_id;
END;
$$ LANGUAGE plpgsql;

-- Get user's active session
CREATE OR REPLACE FUNCTION get_active_session(p_user_id TEXT)
RETURNS UUID AS $$
DECLARE
    active_session UUID;
BEGIN
    SELECT session_id INTO active_session
    FROM conversations
    WHERE user_id = p_user_id AND is_active = TRUE
    ORDER BY started_at DESC
    LIMIT 1;

    RETURN active_session;
END;
$$ LANGUAGE plpgsql;

-- Search conversations by keyword
CREATE OR REPLACE FUNCTION search_conversation_history(
    p_query TEXT,
    p_user_id TEXT DEFAULT NULL,
    p_limit INT DEFAULT 20
)
RETURNS TABLE(
    turn_id UUID,
    conversation_id UUID,
    role TEXT,
    content TEXT,
    relevance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dt.id as turn_id,
        dt.conversation_id,
        dt.role,
        dt.content,
        ts_rank(to_tsvector('english', dt.content), plainto_tsquery('english', p_query)) as relevance
    FROM dialogue_turns dt
    JOIN conversations c ON c.id = dt.conversation_id
    WHERE
        to_tsvector('english', dt.content) @@ plainto_tsquery('english', p_query)
        AND (p_user_id IS NULL OR c.user_id = p_user_id)
    ORDER BY relevance DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Get context window for a conversation
CREATE OR REPLACE FUNCTION get_context_window(
    conv_session_id UUID,
    p_max_turns INT DEFAULT 10
)
RETURNS TABLE(
    role TEXT,
    content TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    emotional_valence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dt.role,
        dt.content,
        dt.timestamp,
        dt.emotional_valence
    FROM dialogue_turns dt
    JOIN conversations c ON c.id = dt.conversation_id
    WHERE c.session_id = conv_session_id
    ORDER BY dt.timestamp DESC
    LIMIT p_max_turns;
END;
$$ LANGUAGE plpgsql;

-- Cleanup inactive sessions
CREATE OR REPLACE FUNCTION cleanup_inactive_conversations(
    timeout_minutes INT DEFAULT 30
)
RETURNS INT AS $$
DECLARE
    closed_count INT;
BEGIN
    UPDATE conversations
    SET
        is_active = FALSE,
        ended_at = NOW(),
        summary = 'Session timed out'
    WHERE
        is_active = TRUE
        AND last_accessed < NOW() - (timeout_minutes || ' minutes')::INTERVAL;

    GET DIAGNOSTICS closed_count = ROW_COUNT;
    RETURN closed_count;
END;
$$ LANGUAGE plpgsql;

-- Get conversation stats
CREATE OR REPLACE FUNCTION get_conversation_stats()
RETURNS TABLE(
    total_conversations BIGINT,
    active_sessions BIGINT,
    total_turns BIGINT,
    avg_turns_per_conversation FLOAT,
    avg_conversation_duration_minutes FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM conversations),
        (SELECT COUNT(*) FROM conversations WHERE is_active = TRUE),
        (SELECT COUNT(*) FROM dialogue_turns),
        (SELECT COALESCE(AVG(turn_count), 0) FROM conversations),
        (
            SELECT COALESCE(
                AVG(EXTRACT(EPOCH FROM (COALESCE(ended_at, NOW()) - started_at)) / 60),
                0
            )
            FROM conversations
        );
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
-- DECAY FUNCTION FOR CONVERSATIONS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION apply_conversation_decay(decay_rate FLOAT DEFAULT 0.01)
RETURNS INT AS $$
DECLARE
    affected_count INT;
BEGIN
    -- Decay eski conversations (aktif olmayanlar)
    UPDATE conversations
    SET strength = GREATEST(0, strength - decay_rate * (1 - importance * 0.5))
    WHERE
        is_active = FALSE
        AND strength > 0;

    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN affected_count;
END;
$$ LANGUAGE plpgsql;
