"""
tests/unit/test_semantic_memory.py

SemanticMemory unit testleri.
Embedding bazli semantik arama testleri.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import MagicMock, patch
import numpy as np

from core.memory.types import (
    SourceType,
    EmbeddingResult,
    Episode,
    EpisodeType,
    DialogueTurn,
    Conversation,
)
from core.memory.semantic import (
    SemanticMemory,
    IndexEntry,
    get_semantic_memory,
    create_semantic_memory,
    reset_semantic_memory,
)


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def mock_encoder():
    """Mock embedding encoder for tests."""
    encoder = MagicMock()
    encoder.encode.return_value = np.random.randn(384).astype(np.float32)
    encoder.encode_batch.return_value = np.random.randn(3, 384).astype(np.float32)
    return encoder


@pytest.fixture
def semantic_memory(mock_encoder):
    """SemanticMemory instance with mock encoder."""
    return SemanticMemory(encoder=mock_encoder)


@pytest.fixture
def sample_episode():
    """Sample episode for testing."""
    return Episode(
        id="ep_001",
        what="Met Alice at the park",
        where="Central Park",
        who=["alice"],
        outcome="Had a nice conversation",
        episode_type=EpisodeType.ENCOUNTER,
        importance=0.8,
    )


@pytest.fixture
def sample_dialogue_turn():
    """Sample dialogue turn for testing."""
    return DialogueTurn(
        id="turn_001",
        role="user",
        content="What is the weather like today?",
        emotional_valence=0.5,
        intent="question",
        topics=["weather"],
    )


@pytest.fixture
def sample_conversation(sample_dialogue_turn):
    """Sample conversation for testing."""
    conv = Conversation(
        session_id="conv_001",
        user_id="user_001",
        agent_id="agent_001",
    )
    conv.add_turn(sample_dialogue_turn)
    conv.add_turn(DialogueTurn(
        id="turn_002",
        role="agent",
        content="The weather is sunny and warm today.",
        emotional_valence=0.6,
    ))
    return conv


# ========================================================================
# SOURCETYPE TESTS
# ========================================================================

class TestSourceType:
    """SourceType enum testleri."""

    def test_source_type_values(self):
        """Source type degerleri dogru olmali."""
        assert SourceType.EPISODE.value == "episode"
        assert SourceType.DIALOGUE.value == "dialogue"
        assert SourceType.FACT.value == "fact"
        assert SourceType.CONCEPT.value == "concept"

    def test_source_type_from_string(self):
        """String'den source type olusturulabilmeli."""
        assert SourceType("episode") == SourceType.EPISODE
        assert SourceType("dialogue") == SourceType.DIALOGUE

    def test_source_type_is_string(self):
        """SourceType str enum olmali."""
        assert isinstance(SourceType.EPISODE, str)
        assert SourceType.EPISODE == "episode"


# ========================================================================
# EMBEDDINGRESULT TESTS
# ========================================================================

class TestEmbeddingResult:
    """EmbeddingResult dataclass testleri."""

    def test_embedding_result_required_fields(self):
        """Zorunlu alanlar set edilmeli."""
        result = EmbeddingResult(
            id="test_001",
            content="Test content",
            similarity=0.85,
            source_type=SourceType.FACT,
        )
        assert result.id == "test_001"
        assert result.content == "Test content"
        assert result.similarity == 0.85
        assert result.source_type == SourceType.FACT

    def test_embedding_result_optional_fields(self):
        """Opsiyonel alanlar default olmali."""
        result = EmbeddingResult(
            id="test_001",
            content="Test",
            similarity=0.5,
            source_type=SourceType.EPISODE,
        )
        assert result.source_id is None
        assert result.timestamp is None
        assert result.extra_data == {}

    def test_embedding_result_with_all_fields(self):
        """Tum alanlar set edilebilmeli."""
        now = datetime.now()
        result = EmbeddingResult(
            id="test_001",
            content="Full content",
            similarity=0.95,
            source_type=SourceType.DIALOGUE,
            source_id="conv_001",
            timestamp=now,
            extra_data={"role": "user"},
        )
        assert result.source_id == "conv_001"
        assert result.timestamp == now
        assert result.extra_data["role"] == "user"


# ========================================================================
# SEMANTICMEMORY INIT TESTS
# ========================================================================

class TestSemanticMemoryInit:
    """SemanticMemory initialization testleri."""

    def test_init_with_encoder(self, mock_encoder):
        """Encoder ile initialize edilebilmeli."""
        sm = SemanticMemory(encoder=mock_encoder)
        assert sm._encoder is mock_encoder

    def test_init_empty_index(self, semantic_memory):
        """Index bos baslamali."""
        assert semantic_memory.count() == 0

    def test_init_stats(self, semantic_memory):
        """Stats initialize edilmeli."""
        stats = semantic_memory.stats
        assert stats["index_size"] == 0
        assert stats["total_adds"] == 0
        assert stats["total_searches"] == 0


# ========================================================================
# INDEX MANAGEMENT TESTS
# ========================================================================

class TestSemanticMemoryAdd:
    """SemanticMemory.add() testleri."""

    def test_add_single_item(self, semantic_memory):
        """Tek item eklenebilmeli."""
        semantic_memory.add(
            id="test_001",
            content="Test content",
            source_type=SourceType.FACT,
        )
        assert semantic_memory.count() == 1
        assert semantic_memory.contains("test_001")

    def test_add_with_source_id(self, semantic_memory):
        """Source ID ile eklenebilmeli."""
        semantic_memory.add(
            id="test_001",
            content="Test content",
            source_type=SourceType.EPISODE,
            source_id="ep_001",
        )
        assert semantic_memory.contains("test_001")

    def test_add_with_extra_data(self, semantic_memory):
        """Extra data ile eklenebilmeli."""
        semantic_memory.add(
            id="test_001",
            content="Test content",
            source_type=SourceType.DIALOGUE,
            extra_data={"role": "user", "intent": "question"},
        )
        assert semantic_memory.contains("test_001")

    def test_add_empty_content_skipped(self, semantic_memory):
        """Bos content atlanmali."""
        semantic_memory.add(
            id="test_001",
            content="",
            source_type=SourceType.FACT,
        )
        assert semantic_memory.count() == 0

    def test_add_whitespace_content_skipped(self, semantic_memory):
        """Sadece whitespace content atlanmali."""
        semantic_memory.add(
            id="test_001",
            content="   \n\t  ",
            source_type=SourceType.FACT,
        )
        assert semantic_memory.count() == 0

    def test_add_updates_stats(self, semantic_memory):
        """Add stats'i guncellemeli."""
        semantic_memory.add("id1", "content1", SourceType.FACT)
        semantic_memory.add("id2", "content2", SourceType.CONCEPT)
        assert semantic_memory.stats["total_adds"] == 2


class TestSemanticMemoryAddBatch:
    """SemanticMemory.add_batch() testleri."""

    def test_add_batch_multiple_items(self, semantic_memory, mock_encoder):
        """Birden fazla item toplu eklenebilmeli."""
        mock_encoder.encode_batch.return_value = np.random.randn(3, 384)

        items = [
            {"id": "id1", "content": "Content 1", "source_type": SourceType.FACT},
            {"id": "id2", "content": "Content 2", "source_type": SourceType.CONCEPT},
            {"id": "id3", "content": "Content 3", "source_type": SourceType.EPISODE},
        ]
        count = semantic_memory.add_batch(items)

        assert count == 3
        assert semantic_memory.count() == 3

    def test_add_batch_empty_list(self, semantic_memory):
        """Bos liste 0 donmeli."""
        count = semantic_memory.add_batch([])
        assert count == 0

    def test_add_batch_skips_empty_content(self, semantic_memory, mock_encoder):
        """Bos content'li itemlar atlanmali."""
        mock_encoder.encode_batch.return_value = np.random.randn(2, 384)

        items = [
            {"id": "id1", "content": "Content 1", "source_type": SourceType.FACT},
            {"id": "id2", "content": "", "source_type": SourceType.FACT},
            {"id": "id3", "content": "Content 3", "source_type": SourceType.FACT},
        ]
        count = semantic_memory.add_batch(items)

        assert count == 2

    def test_add_batch_string_source_type(self, semantic_memory, mock_encoder):
        """String source type kabul edilmeli."""
        mock_encoder.encode_batch.return_value = np.random.randn(1, 384)

        items = [
            {"id": "id1", "content": "Content 1", "source_type": "fact"},
        ]
        count = semantic_memory.add_batch(items)

        assert count == 1


class TestSemanticMemoryRemove:
    """SemanticMemory.remove() testleri."""

    def test_remove_existing_item(self, semantic_memory):
        """Varolan item silinebilmeli."""
        semantic_memory.add("test_001", "content", SourceType.FACT)
        assert semantic_memory.remove("test_001") is True
        assert semantic_memory.count() == 0

    def test_remove_nonexistent_item(self, semantic_memory):
        """Olmayan item False donmeli."""
        assert semantic_memory.remove("nonexistent") is False

    def test_remove_updates_stats(self, semantic_memory):
        """Remove stats'i guncellemeli."""
        semantic_memory.add("test_001", "content", SourceType.FACT)
        semantic_memory.remove("test_001")
        assert semantic_memory.stats["total_removes"] == 1


class TestSemanticMemoryClear:
    """SemanticMemory.clear() testleri."""

    def test_clear_all_items(self, semantic_memory):
        """Tum itemlar silinmeli."""
        semantic_memory.add("id1", "content1", SourceType.FACT)
        semantic_memory.add("id2", "content2", SourceType.CONCEPT)
        semantic_memory.clear()
        assert semantic_memory.count() == 0


class TestSemanticMemoryContains:
    """SemanticMemory.contains() testleri."""

    def test_contains_existing(self, semantic_memory):
        """Varolan ID icin True donmeli."""
        semantic_memory.add("test_001", "content", SourceType.FACT)
        assert semantic_memory.contains("test_001") is True

    def test_contains_nonexistent(self, semantic_memory):
        """Olmayan ID icin False donmeli."""
        assert semantic_memory.contains("nonexistent") is False


# ========================================================================
# SEARCH TESTS
# ========================================================================

class TestSemanticMemorySearch:
    """SemanticMemory.search() testleri."""

    def test_search_empty_index(self, semantic_memory):
        """Bos index'te arama bos liste donmeli."""
        results = semantic_memory.search("test query")
        assert results == []

    def test_search_empty_query(self, semantic_memory):
        """Bos query bos liste donmeli."""
        semantic_memory.add("id1", "content", SourceType.FACT)
        results = semantic_memory.search("")
        assert results == []

    def test_search_returns_results(self, semantic_memory, mock_encoder):
        """Arama sonuc dondurmeli."""
        # Setup - add items with different embeddings
        semantic_memory.add("id1", "content1", SourceType.FACT)
        semantic_memory.add("id2", "content2", SourceType.CONCEPT)

        # Mock search to return predictable similarities
        with patch('core.memory.semantic.batch_cosine_similarity') as mock_sim:
            mock_sim.return_value = np.array([0.9, 0.7])
            with patch('core.memory.semantic.top_k_indices') as mock_top:
                mock_top.return_value = [(0, 0.9), (1, 0.7)]

                results = semantic_memory.search("query", k=2)

                assert len(results) == 2
                assert results[0].similarity == 0.9
                assert results[1].similarity == 0.7

    def test_search_respects_k(self, semantic_memory, mock_encoder):
        """K parametresi sonuc sayisini sınırlamalı."""
        for i in range(10):
            semantic_memory.add(f"id{i}", f"content{i}", SourceType.FACT)

        with patch('core.memory.semantic.batch_cosine_similarity') as mock_sim:
            mock_sim.return_value = np.array([0.9] * 10)
            with patch('core.memory.semantic.top_k_indices') as mock_top:
                mock_top.return_value = [(i, 0.9) for i in range(3)]

                results = semantic_memory.search("query", k=3)
                assert len(results) == 3

    def test_search_updates_stats(self, semantic_memory):
        """Arama stats'i guncellemeli."""
        semantic_memory.add("id1", "content", SourceType.FACT)

        with patch('core.memory.semantic.batch_cosine_similarity') as mock_sim:
            mock_sim.return_value = np.array([0.5])
            with patch('core.memory.semantic.top_k_indices') as mock_top:
                mock_top.return_value = [(0, 0.5)]

                semantic_memory.search("query")
                assert semantic_memory.stats["total_searches"] == 1


class TestSemanticMemorySearchBySource:
    """SemanticMemory.search_by_source() testleri."""

    def test_search_by_source_filters(self, semantic_memory, mock_encoder):
        """Source type'a gore filtrelemeli."""
        semantic_memory.add("id1", "fact content", SourceType.FACT)
        semantic_memory.add("id2", "concept content", SourceType.CONCEPT)

        # Only FACT entries should be searched
        with patch('core.memory.semantic.batch_cosine_similarity') as mock_sim:
            mock_sim.return_value = np.array([0.8])
            with patch('core.memory.semantic.top_k_indices') as mock_top:
                mock_top.return_value = [(0, 0.8)]

                results = semantic_memory.search_by_source(
                    "query", SourceType.FACT, k=5
                )

                # Should only return FACT items
                for result in results:
                    assert result.source_type == SourceType.FACT

    def test_search_by_source_empty_source_type(self, semantic_memory):
        """Source type olmayan arama bos donmeli."""
        semantic_memory.add("id1", "content", SourceType.FACT)
        results = semantic_memory.search_by_source("query", SourceType.DIALOGUE)
        assert results == []


class TestSemanticMemorySearchSimilarToId:
    """SemanticMemory.search_similar_to_id() testleri."""

    def test_search_similar_to_nonexistent_id(self, semantic_memory):
        """Olmayan ID icin bos liste donmeli."""
        results = semantic_memory.search_similar_to_id("nonexistent")
        assert results == []

    def test_search_similar_excludes_self(self, semantic_memory, mock_encoder):
        """Kendisini sonuclardan haric tutmali."""
        semantic_memory.add("id1", "content1", SourceType.FACT)
        semantic_memory.add("id2", "content2", SourceType.FACT)

        with patch('core.memory.semantic.batch_cosine_similarity') as mock_sim:
            mock_sim.return_value = np.array([0.8])
            with patch('core.memory.semantic.top_k_indices') as mock_top:
                mock_top.return_value = [(0, 0.8)]

                results = semantic_memory.search_similar_to_id("id1", k=5)

                # id1 should not be in results
                for result in results:
                    assert result.id != "id1"


# ========================================================================
# MEMORY INTEGRATION TESTS
# ========================================================================

class TestSemanticMemoryIndexEpisode:
    """SemanticMemory.index_episode() testleri."""

    def test_index_episode(self, semantic_memory, sample_episode):
        """Episode index'lenmeli."""
        semantic_memory.index_episode(sample_episode)
        assert semantic_memory.contains(sample_episode.id)

    def test_index_episode_source_type(self, semantic_memory, sample_episode):
        """Episode source type EPISODE olmali."""
        semantic_memory.index_episode(sample_episode)
        entry = semantic_memory._index[sample_episode.id]
        assert entry.source_type == SourceType.EPISODE

    def test_index_episode_extra_data(self, semantic_memory, sample_episode):
        """Episode extra_data dogru olmali."""
        semantic_memory.index_episode(sample_episode)
        entry = semantic_memory._index[sample_episode.id]
        assert entry.extra_data["importance"] == 0.8
        assert "alice" in entry.extra_data["who"]


class TestSemanticMemoryIndexDialogueTurn:
    """SemanticMemory.index_dialogue_turn() testleri."""

    def test_index_dialogue_turn(self, semantic_memory, sample_dialogue_turn):
        """DialogueTurn index'lenmeli."""
        semantic_memory.index_dialogue_turn(sample_dialogue_turn, "conv_001")
        assert semantic_memory.contains(sample_dialogue_turn.id)

    def test_index_dialogue_turn_source_type(self, semantic_memory, sample_dialogue_turn):
        """DialogueTurn source type DIALOGUE olmali."""
        semantic_memory.index_dialogue_turn(sample_dialogue_turn, "conv_001")
        entry = semantic_memory._index[sample_dialogue_turn.id]
        assert entry.source_type == SourceType.DIALOGUE

    def test_index_empty_turn_skipped(self, semantic_memory):
        """Bos turn atlanmali."""
        turn = DialogueTurn(id="turn_empty", content="")
        semantic_memory.index_dialogue_turn(turn, "conv_001")
        assert not semantic_memory.contains("turn_empty")


class TestSemanticMemoryIndexConversation:
    """SemanticMemory.index_conversation() testleri."""

    def test_index_conversation(self, semantic_memory, sample_conversation, mock_encoder):
        """Conversation tum turn'leri index'lemeli."""
        mock_encoder.encode.return_value = np.random.randn(384)
        count = semantic_memory.index_conversation(sample_conversation)
        assert count == 2

    def test_index_empty_conversation(self, semantic_memory):
        """Bos conversation 0 donmeli."""
        conv = Conversation(session_id="empty_conv")
        count = semantic_memory.index_conversation(conv)
        assert count == 0


# ========================================================================
# PERSISTENCE TESTS
# ========================================================================

class TestSemanticMemoryPersistence:
    """SemanticMemory save/load testleri."""

    def test_save_and_load(self, semantic_memory, mock_encoder):
        """Save ve load dogru calismalı."""
        # Add items
        semantic_memory.add("id1", "content1", SourceType.FACT, extra_data={"key": "value"})
        semantic_memory.add("id2", "content2", SourceType.CONCEPT)

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            semantic_memory.save(path)

            # Create new instance and load
            new_sm = SemanticMemory(encoder=mock_encoder)
            new_sm.load(path)

            assert new_sm.count() == 2
            assert new_sm.contains("id1")
            assert new_sm.contains("id2")

            # Check extra_data preserved
            entry = new_sm._index["id1"]
            assert entry.extra_data["key"] == "value"
        finally:
            os.unlink(path)

    def test_load_preserves_source_type(self, semantic_memory, mock_encoder):
        """Load source type'i preserve etmeli."""
        semantic_memory.add("id1", "content", SourceType.DIALOGUE)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            semantic_memory.save(path)

            new_sm = SemanticMemory(encoder=mock_encoder)
            new_sm.load(path)

            entry = new_sm._index["id1"]
            assert entry.source_type == SourceType.DIALOGUE
        finally:
            os.unlink(path)


# ========================================================================
# STATS TESTS
# ========================================================================

class TestSemanticMemoryStats:
    """SemanticMemory.stats testleri."""

    def test_stats_source_counts(self, semantic_memory):
        """Source counts dogru hesaplanmali."""
        semantic_memory.add("id1", "content1", SourceType.FACT)
        semantic_memory.add("id2", "content2", SourceType.FACT)
        semantic_memory.add("id3", "content3", SourceType.CONCEPT)

        stats = semantic_memory.stats
        assert stats["source_counts"]["fact"] == 2
        assert stats["source_counts"]["concept"] == 1

    def test_stats_comprehensive(self, semantic_memory):
        """Stats tum metrikleri icermeli."""
        semantic_memory.add("id1", "content", SourceType.FACT)
        semantic_memory.remove("id1")

        stats = semantic_memory.stats
        assert "index_size" in stats
        assert "source_counts" in stats
        assert "total_adds" in stats
        assert "total_searches" in stats
        assert "total_removes" in stats


# ========================================================================
# FACTORY TESTS
# ========================================================================

class TestSemanticMemoryFactory:
    """Factory function testleri."""

    def test_get_semantic_memory_singleton(self):
        """get_semantic_memory singleton dondurmeli."""
        reset_semantic_memory()

        with patch('core.memory.semantic.get_embedding_encoder') as mock_get:
            mock_get.return_value = MagicMock()

            sm1 = get_semantic_memory()
            sm2 = get_semantic_memory()

            assert sm1 is sm2

    def test_create_semantic_memory_new_instance(self):
        """create_semantic_memory yeni instance olusturmali."""
        with patch('core.memory.semantic.get_embedding_encoder') as mock_get:
            mock_get.return_value = MagicMock()

            sm1 = create_semantic_memory()
            sm2 = create_semantic_memory()

            assert sm1 is not sm2

    def test_reset_semantic_memory(self):
        """reset_semantic_memory singleton'i temizlemeli."""
        reset_semantic_memory()

        with patch('core.memory.semantic.get_embedding_encoder') as mock_get:
            mock_get.return_value = MagicMock()

            sm1 = get_semantic_memory()
            reset_semantic_memory()
            sm2 = get_semantic_memory()

            assert sm1 is not sm2
