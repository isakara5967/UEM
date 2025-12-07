"""
tests/unit/test_memory.py

Memory modulu unit testleri.
Section 7 of MEMORY_MODULE_DESIGN.md implementation.
"""

import pytest
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from core.memory import (
    MemoryStore, MemoryConfig, create_memory_store,
    Episode, EpisodeType,
    RelationshipRecord, RelationshipType,
    Interaction, InteractionType,
    SemanticFact,
    EmotionalMemory,
    WorkingMemoryItem,
    MemoryQuery, MemoryType,
)


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def store():
    """Fresh memory store for each test."""
    return create_memory_store()


@pytest.fixture
def store_with_config():
    """Memory store with custom config."""
    config = MemoryConfig(
        working_memory_capacity=7,
        enable_decay=True,
        base_decay_rate=0.1,
    )
    return create_memory_store(config)


# ========================================================================
# WORKING MEMORY TESTS
# ========================================================================

class TestWorkingMemory:
    """Working memory (7+-2) testleri."""

    def test_capacity_limit(self, store):
        """Working memory 7+-2 limiti."""
        config = MemoryConfig(working_memory_capacity=7)
        store = create_memory_store(config)

        # 10 oge eklemeye calis
        for i in range(10):
            item = WorkingMemoryItem(
                content=f"item_{i}",
                priority=i / 10,  # 0.0 - 0.9
            )
            store.hold_in_working(item)

        wm = store.get_working_memory()
        assert len(wm) <= 7, f"WM should be <=7, got {len(wm)}"

        # En yuksek priority olanlar kalmali
        priorities = [item.priority for item in wm]
        assert min(priorities) >= 0.3, "Low priority items should be removed"

    def test_priority_based_removal(self, store):
        """Dusuk priority ogeler cikartilir."""
        config = MemoryConfig(working_memory_capacity=3)
        store = create_memory_store(config)

        # 3 oge ekle (dusuk priority)
        for i in range(3):
            item = WorkingMemoryItem(content=f"low_{i}", priority=0.1)
            store.hold_in_working(item)

        # Yuksek priority ekle
        high = WorkingMemoryItem(content="high", priority=0.9)
        result = store.hold_in_working(high)

        assert result is True
        wm = store.get_working_memory()
        assert any(item.content == "high" for item in wm)

    def test_clear_working_memory(self, store):
        """Working memory temizleme."""
        item = WorkingMemoryItem(content="test", priority=0.5)
        store.hold_in_working(item)

        cleared = store.clear_working_memory()
        assert len(cleared) == 1
        assert len(store.get_working_memory()) == 0


# ========================================================================
# RELATIONSHIP MEMORY TESTS
# ========================================================================

class TestRelationshipMemory:
    """Relationship memory ve trust entegrasyonu."""

    def test_new_agent_is_stranger(self, store):
        """Yeni agent stranger olarak baslar."""
        alice = store.get_relationship("alice")
        assert alice.relationship_type == RelationshipType.STRANGER
        assert alice.total_interactions == 0

    def test_interaction_recording(self, store):
        """Etkilesim kaydi."""
        interaction1 = Interaction(
            interaction_type=InteractionType.HELPED,
            outcome_valence=0.8,
            trust_impact=0.1,
        )
        store.record_interaction("alice", interaction1)

        interaction2 = Interaction(
            interaction_type=InteractionType.COOPERATED,
            outcome_valence=0.6,
            trust_impact=0.05,
        )
        store.record_interaction("alice", interaction2)

        alice = store.get_relationship("alice")
        assert alice.total_interactions == 2
        assert alice.positive_interactions == 2
        assert alice.overall_sentiment > 0.5

    def test_trust_recommendation(self, store):
        """Trust onerisi hesaplamalari."""
        # Pozitif etkilesimler
        for _ in range(3):
            store.record_interaction("friend", Interaction(
                interaction_type=InteractionType.HELPED,
                outcome_valence=0.8,
            ))

        friend = store.get_relationship("friend")
        assert friend.get_trust_recommendation() > 0.6

        # Negatif etkilesimler
        for _ in range(3):
            store.record_interaction("enemy", Interaction(
                interaction_type=InteractionType.ATTACKED,
                outcome_valence=-0.8,
            ))

        enemy = store.get_relationship("enemy")
        assert enemy.get_trust_recommendation() < 0.4

    def test_betrayal_tracking(self, store):
        """Betrayal izleme."""
        betrayal = Interaction(
            interaction_type=InteractionType.BETRAYED,
            outcome_valence=-0.9,
            trust_impact=-0.3,
        )
        store.record_interaction("traitor", betrayal)

        traitor = store.get_relationship("traitor")
        assert traitor.betrayal_count == 1
        assert traitor.last_betrayal is not None
        assert traitor.get_trust_recommendation() < 0.5

    def test_relationship_type_defaults(self, store):
        """RelationshipType'a gore varsayilan trust."""
        store.update_relationship("friend", relationship_type=RelationshipType.FRIEND)
        friend = store.get_relationship("friend")
        assert friend.get_trust_recommendation() == 0.7

        store.update_relationship("enemy", relationship_type=RelationshipType.ENEMY)
        enemy = store.get_relationship("enemy")
        assert enemy.get_trust_recommendation() == 0.15


# ========================================================================
# EPISODIC MEMORY TESTS
# ========================================================================

class TestEpisodicMemory:
    """Episode kaydetme ve hatırlama."""

    def test_store_and_retrieve_episode(self, store):
        """Episode kaydet ve getir."""
        episode = Episode(
            what="Alice helped me when I was in trouble",
            where="forest",
            who=["alice"],
            episode_type=EpisodeType.COOPERATION,
            outcome="Successfully escaped danger",
            outcome_valence=0.8,
            importance=0.8,
        )

        episode_id = store.store_episode(episode)
        retrieved = store.get_episode(episode_id)

        assert retrieved is not None
        assert retrieved.what == episode.what
        assert retrieved.who == ["alice"]

    def test_recall_by_agent(self, store):
        """Agent'a gore hatirla."""
        store.store_episode(Episode(
            what="Met Alice",
            who=["alice"],
            episode_type=EpisodeType.ENCOUNTER,
        ))
        store.store_episode(Episode(
            what="Met Bob",
            who=["bob"],
            episode_type=EpisodeType.ENCOUNTER,
        ))

        alice_episodes = store.recall_episodes(agent_id="alice")
        assert len(alice_episodes) == 1
        assert alice_episodes[0].who == ["alice"]

    def test_recall_by_type(self, store):
        """Episode turune gore hatirla."""
        store.store_episode(Episode(
            what="Friendly meeting",
            episode_type=EpisodeType.COOPERATION,
        ))
        store.store_episode(Episode(
            what="Enemy encounter",
            episode_type=EpisodeType.CONFLICT,
        ))

        conflicts = store.recall_episodes(episode_type=EpisodeType.CONFLICT)
        assert len(conflicts) == 1
        assert conflicts[0].episode_type == EpisodeType.CONFLICT

    def test_recall_similar_episodes(self, store):
        """Benzer durumları hatirla."""
        store.store_episode(Episode(
            what="Alice helped me when I was in trouble",
            outcome="Escaped danger successfully",
            importance=0.8,
        ))

        similar = store.recall_similar_episodes("trouble danger")
        assert len(similar) >= 1

    def test_episode_creates_relationship_update(self, store):
        """Episode relationship'i otomatik gunceller."""
        episode = Episode(
            what="Alice helped me",
            who=["alice"],
            outcome_valence=0.8,
        )
        store.store_episode(episode)

        alice = store.get_relationship("alice")
        assert alice.total_interactions >= 1


# ========================================================================
# DECAY TESTS
# ========================================================================

class TestMemoryDecay:
    """Bellek zamanla zayiflama."""

    def test_decay_reduces_strength(self):
        """Decay strength azaltir."""
        config = MemoryConfig(enable_decay=True, base_decay_rate=0.1)
        store = create_memory_store(config)

        episode = Episode(
            what="Test event",
            importance=0.5,
            strength=1.0,
        )
        store.store_episode(episode)

        initial_strength = episode.strength

        # Decay uygula (birkac kez)
        for _ in range(5):
            store.apply_decay()

        assert episode.strength < initial_strength

    def test_importance_slows_decay(self):
        """Onemli anilar daha yavas unutulur."""
        config = MemoryConfig(enable_decay=True, base_decay_rate=0.1)
        store = create_memory_store(config)

        low_importance = Episode(what="Low", importance=0.1, strength=1.0)
        high_importance = Episode(what="High", importance=0.9, strength=1.0)

        store.store_episode(low_importance)
        store.store_episode(high_importance)

        for _ in range(5):
            store.apply_decay()

        # High importance daha az kayip yasamali
        assert high_importance.strength > low_importance.strength


# ========================================================================
# EMOTIONAL MEMORY TESTS
# ========================================================================

class TestEmotionalMemory:
    """Duygusal anilar."""

    def test_store_and_recall_by_emotion(self, store):
        """Duyguya gore hatirla."""
        memory = EmotionalMemory(
            primary_emotion="fear",
            emotion_intensity=0.9,
            pleasure=-0.8,
            arousal=0.9,
            triggers=["enemy", "loud_noise"],
            is_flashbulb=True,
        )

        store.store_emotional_memory(memory)

        fear_memories = store.recall_by_emotion("fear", min_intensity=0.5)
        assert len(fear_memories) == 1
        assert fear_memories[0].primary_emotion == "fear"

    def test_recall_by_trigger(self, store):
        """Tetikleyiciye gore hatirla."""
        memory = EmotionalMemory(
            primary_emotion="fear",
            emotion_intensity=0.8,
            triggers=["enemy", "darkness"],
        )
        store.store_emotional_memory(memory)

        triggered = store.recall_by_trigger("enemy")
        assert len(triggered) == 1

        not_triggered = store.recall_by_trigger("sunshine")
        assert len(not_triggered) == 0

    def test_high_emotion_episode_creates_emotional_memory(self, store):
        """Yuksek duygusal yogunluklu episode emotional memory olusturur."""
        episode = Episode(
            what="Terrifying encounter",
            emotional_valence=-0.8,
            emotional_arousal=0.9,
            self_emotion_during="fear",
            importance=0.9,
        )
        store.store_episode(episode)

        # Emotional memory otomatik olusturulmali
        fear_memories = store.recall_by_emotion("fear")
        assert len(fear_memories) >= 1


# ========================================================================
# UNIFIED RETRIEVAL TESTS
# ========================================================================

class TestUnifiedRetrieval:
    """Unified memory retrieval."""

    def test_retrieve_multiple_types(self, store):
        """Birden fazla memory turunu sorgula."""
        store.store_episode(Episode(
            what="Met Bob at the park",
            who=["bob"],
            importance=0.7,
        ))

        store.record_interaction("bob", Interaction(
            interaction_type=InteractionType.CONVERSED,
            outcome_valence=0.5,
        ))

        query = MemoryQuery(
            memory_types=[MemoryType.EPISODIC, MemoryType.RELATIONSHIP],
            agent_ids=["bob"],
            max_results=10,
        )

        result = store.retrieve(query)

        assert result.total_matches >= 2  # Episode + Relationship
        assert result.query_time_ms >= 0


# ========================================================================
# AGENT RECOGNITION TESTS
# ========================================================================

class TestAgentRecognition:
    """Agent tanima."""

    def test_unknown_agent(self, store):
        """Bilinmeyen agent."""
        assert not store.is_known_agent("stranger_1")

    def test_known_after_interaction(self, store):
        """Etkilesim sonrasi taniniyor."""
        store.record_interaction("stranger_1", Interaction(
            interaction_type=InteractionType.OBSERVED,
        ))

        assert store.is_known_agent("stranger_1")


# ========================================================================
# SEMANTIC MEMORY TESTS
# ========================================================================

class TestSemanticMemory:
    """Semantic fact testleri."""

    def test_store_and_query_fact(self, store):
        """Fact kaydet ve sorgula."""
        fact = SemanticFact(
            subject="alice",
            predicate="is_a",
            object="friend",
            confidence=0.9,
        )
        store.store_fact(fact)

        results = store.query_facts(subject="alice")
        assert len(results) == 1
        assert results[0].object == "friend"

    def test_query_by_predicate(self, store):
        """Predicate ile sorgula."""
        store.store_fact(SemanticFact(
            subject="alice", predicate="is_a", object="friend"
        ))
        store.store_fact(SemanticFact(
            subject="bob", predicate="is_a", object="colleague"
        ))
        store.store_fact(SemanticFact(
            subject="enemy", predicate="implies", object="danger"
        ))

        is_a_facts = store.query_facts(predicate="is_a")
        assert len(is_a_facts) == 2


# ========================================================================
# STATS TESTS
# ========================================================================

class TestStats:
    """Statistics ve debug."""

    def test_stats_tracking(self, store):
        """Istatistik izleme."""
        store.store_episode(Episode(what="Test"))
        store.record_interaction("agent", Interaction())

        stats = store.stats
        assert stats["total_episodes"] >= 1
        assert stats["episodes_count"] >= 1
        assert stats["relationships_count"] >= 1

    def test_debug_dump(self, store):
        """Debug dump."""
        store.store_episode(Episode(what="Test"))
        dump = store.debug_dump()

        assert "config" in dump
        assert "stats" in dump
        assert "working_memory" in dump
        assert "relationships" in dump


# ========================================================================
# RUN ALL TESTS
# ========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
