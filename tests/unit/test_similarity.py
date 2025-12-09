"""
tests/unit/test_similarity.py

EpisodeSimilarity ve Episode testleri.
"""

import pytest
from datetime import datetime

from core.learning.episode import (
    Episode,
    EpisodeOutcome,
    EpisodeCollection,
    generate_episode_id,
)
from core.learning.similarity import (
    SimilarityConfig,
    SimilarityResult,
    EpisodeSimilarity,
    jaccard_similarity,
    levenshtein_distance,
    levenshtein_similarity,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def default_outcome():
    """Varsayilan episode outcome."""
    return EpisodeOutcome(success=True)


@pytest.fixture
def sample_episode(default_outcome):
    """Ornek episode."""
    return Episode(
        id="ep_test001",
        user_message="Merhaba, nasılsın?",
        situation_summary={"topic": "greeting"},
        dialogue_acts=["greet", "ask"],
        intent="greet",
        emotion_label="neutral",
        constructions_used=["c_greet1"],
        outcome=default_outcome,
    )


@pytest.fixture
def similar_episode(default_outcome):
    """Benzer episode."""
    return Episode(
        id="ep_test002",
        user_message="Selam, nasılsın?",
        situation_summary={"topic": "greeting"},
        dialogue_acts=["greet"],
        intent="greet",
        emotion_label="neutral",
        constructions_used=["c_greet2"],
        outcome=default_outcome,
    )


@pytest.fixture
def different_episode(default_outcome):
    """Farkli episode."""
    return Episode(
        id="ep_test003",
        user_message="Bir sorunum var, yardım edebilir misin?",
        situation_summary={"topic": "help"},
        dialogue_acts=["request", "inform"],
        intent="help",
        emotion_label="anxious",
        constructions_used=["c_help1"],
        outcome=default_outcome,
    )


@pytest.fixture
def similarity():
    """EpisodeSimilarity instance."""
    return EpisodeSimilarity()


# =============================================================================
# EpisodeOutcome Tests
# =============================================================================

class TestEpisodeOutcome:
    """EpisodeOutcome testleri."""

    def test_create_basic_outcome(self):
        """Basit outcome olusturma."""
        outcome = EpisodeOutcome(success=True)
        assert outcome.success is True
        assert outcome.explicit_feedback is None
        assert outcome.trust_delta == 0.0

    def test_create_outcome_with_feedback(self):
        """Feedback ile outcome olusturma."""
        outcome = EpisodeOutcome(
            success=True,
            explicit_feedback=0.8,
            trust_delta=0.1
        )
        assert outcome.explicit_feedback == 0.8
        assert outcome.trust_delta == 0.1

    def test_feedback_range_validation(self):
        """Feedback aralık doğrulaması."""
        with pytest.raises(ValueError):
            EpisodeOutcome(success=True, explicit_feedback=1.5)

        with pytest.raises(ValueError):
            EpisodeOutcome(success=True, explicit_feedback=-1.5)

    def test_overall_score_with_feedback(self):
        """Feedback ile genel skor."""
        outcome = EpisodeOutcome(success=True, explicit_feedback=0.8)
        assert outcome.overall_score == 0.8

    def test_overall_score_without_feedback_success(self):
        """Feedback olmadan basarili sonuc."""
        outcome = EpisodeOutcome(success=True)
        assert outcome.overall_score == 0.5

    def test_overall_score_without_feedback_failure(self):
        """Feedback olmadan basarisiz sonuc."""
        outcome = EpisodeOutcome(success=False)
        assert outcome.overall_score == -0.3

    def test_overall_score_with_trust_delta(self):
        """Trust delta etkisi."""
        outcome = EpisodeOutcome(
            success=True,
            explicit_feedback=0.5,
            trust_delta=0.5
        )
        # 0.5 + (0.5 * 0.3) = 0.65
        assert outcome.overall_score == pytest.approx(0.65)

    def test_has_positive_outcome(self):
        """Pozitif sonuc kontrolu."""
        pos = EpisodeOutcome(success=True, explicit_feedback=0.5)
        neg = EpisodeOutcome(success=False, explicit_feedback=-0.5)

        assert pos.has_positive_outcome is True
        assert neg.has_positive_outcome is False


# =============================================================================
# Episode Tests
# =============================================================================

class TestEpisode:
    """Episode testleri."""

    def test_create_episode(self, default_outcome):
        """Episode olusturma."""
        episode = Episode(
            id="ep_123",
            user_message="Test message",
            situation_summary={},
            dialogue_acts=["inform"],
            intent="test",
            emotion_label="neutral",
            constructions_used=[],
            outcome=default_outcome,
        )
        assert episode.id == "ep_123"
        assert episode.user_message == "Test message"

    def test_auto_generate_id(self, default_outcome):
        """Otomatik ID olusturma."""
        episode = Episode(
            id="",
            user_message="Test",
            situation_summary={},
            dialogue_acts=[],
            intent="",
            emotion_label="",
            constructions_used=[],
            outcome=default_outcome,
        )
        assert episode.id.startswith("ep_")

    def test_word_count(self, default_outcome):
        """Kelime sayisi."""
        episode = Episode(
            id="ep_1",
            user_message="Bu bir test mesajidir",
            situation_summary={},
            dialogue_acts=[],
            intent="",
            emotion_label="",
            constructions_used=[],
            outcome=default_outcome,
        )
        assert episode.word_count == 4

    def test_has_emotion(self, default_outcome):
        """Duygu varlik kontrolu."""
        neutral = Episode(
            id="ep_1", user_message="", situation_summary={},
            dialogue_acts=[], intent="", emotion_label="neutral",
            constructions_used=[], outcome=default_outcome,
        )
        happy = Episode(
            id="ep_2", user_message="", situation_summary={},
            dialogue_acts=[], intent="", emotion_label="happy",
            constructions_used=[], outcome=default_outcome,
        )

        assert neutral.has_emotion is False
        assert happy.has_emotion is True

    def test_to_dict(self, sample_episode):
        """Dictionary donusumu."""
        data = sample_episode.to_dict()

        assert data["id"] == "ep_test001"
        assert data["user_message"] == "Merhaba, nasılsın?"
        assert data["dialogue_acts"] == ["greet", "ask"]

    def test_from_dict(self):
        """Dictionary'den olusturma."""
        data = {
            "id": "ep_dict",
            "user_message": "Test",
            "situation_summary": {"key": "value"},
            "dialogue_acts": ["inform"],
            "intent": "test",
            "emotion_label": "happy",
            "constructions_used": ["c1"],
            "outcome": {"success": True, "trust_delta": 0.1},
        }

        episode = Episode.from_dict(data)

        assert episode.id == "ep_dict"
        assert episode.intent == "test"
        assert episode.outcome.success is True


# =============================================================================
# EpisodeCollection Tests
# =============================================================================

class TestEpisodeCollection:
    """EpisodeCollection testleri."""

    def test_create_empty_collection(self):
        """Bos koleksiyon."""
        collection = EpisodeCollection()
        assert len(collection) == 0

    def test_add_episode(self, sample_episode):
        """Episode ekleme."""
        collection = EpisodeCollection()
        collection.add(sample_episode)
        assert len(collection) == 1

    def test_get_successful(self, default_outcome):
        """Basarili episode'lari getir."""
        success = Episode(
            id="ep_s", user_message="", situation_summary={},
            dialogue_acts=[], intent="", emotion_label="",
            constructions_used=[], outcome=EpisodeOutcome(success=True),
        )
        failure = Episode(
            id="ep_f", user_message="", situation_summary={},
            dialogue_acts=[], intent="", emotion_label="",
            constructions_used=[], outcome=EpisodeOutcome(success=False),
        )

        collection = EpisodeCollection(episodes=[success, failure])
        successful = collection.get_successful()

        assert len(successful) == 1
        assert successful[0].id == "ep_s"

    def test_success_rate(self, default_outcome):
        """Basari orani."""
        episodes = [
            Episode(
                id=f"ep_{i}", user_message="", situation_summary={},
                dialogue_acts=[], intent="", emotion_label="",
                constructions_used=[],
                outcome=EpisodeOutcome(success=(i % 2 == 0)),
            )
            for i in range(10)
        ]
        collection = EpisodeCollection(episodes=episodes)

        assert collection.success_rate == 0.5


# =============================================================================
# SimilarityConfig Tests
# =============================================================================

class TestSimilarityConfig:
    """SimilarityConfig testleri."""

    def test_default_config(self):
        """Varsayilan konfigurasyon."""
        config = SimilarityConfig()
        assert config.text_weight == 0.30
        assert config.intent_weight == 0.25
        assert config.emotion_weight == 0.20
        assert config.dialogue_act_weight == 0.25

    def test_weights_must_sum_to_one(self):
        """Agirliklar toplami 1.0 olmali."""
        with pytest.raises(ValueError):
            SimilarityConfig(
                text_weight=0.5,
                intent_weight=0.5,
                emotion_weight=0.5,
                dialogue_act_weight=0.5
            )

    def test_custom_thresholds(self):
        """Ozel esik degerleri."""
        config = SimilarityConfig(
            similar_threshold=0.9,
            cluster_threshold=0.8
        )
        assert config.similar_threshold == 0.9
        assert config.cluster_threshold == 0.8


# =============================================================================
# EpisodeSimilarity - Text Similarity Tests
# =============================================================================

class TestTextSimilarity:
    """Metin benzerligi testleri."""

    def test_identical_text(self, similarity):
        """Ayni metin."""
        score = similarity._text_similarity(
            "Merhaba nasılsın",
            "Merhaba nasılsın"
        )
        assert score == 1.0

    def test_similar_text(self, similarity):
        """Benzer metin."""
        score = similarity._text_similarity(
            "Merhaba nasılsın",
            "Selam nasılsın"
        )
        # "nasilsin" ortak, "merhaba" vs "selam" farkli
        assert 0.3 <= score <= 0.7

    def test_different_text(self, similarity):
        """Farkli metin."""
        score = similarity._text_similarity(
            "Merhaba nasılsın",
            "Yardım edebilir misiniz"
        )
        assert score < 0.5

    def test_empty_text(self, similarity):
        """Bos metin."""
        assert similarity._text_similarity("", "") == 1.0
        assert similarity._text_similarity("test", "") == 0.0
        assert similarity._text_similarity("", "test") == 0.0

    def test_case_insensitive(self, similarity):
        """Buyuk/kucuk harf duyarsiz."""
        score = similarity._text_similarity(
            "MERHABA",
            "merhaba"
        )
        assert score == 1.0


# =============================================================================
# EpisodeSimilarity - Intent Similarity Tests
# =============================================================================

class TestIntentSimilarity:
    """Intent benzerligi testleri."""

    def test_identical_intent(self, similarity):
        """Ayni intent."""
        score = similarity._intent_similarity("greet", "greet")
        assert score == 1.0

    def test_same_category_intent(self, similarity):
        """Ayni kategorideki intent."""
        score = similarity._intent_similarity("ask", "inform")
        assert score == 0.7  # Ayni kategori (information)

    def test_different_category_intent(self, similarity):
        """Farkli kategorideki intent."""
        score = similarity._intent_similarity("greet", "help")
        assert score == 0.0

    def test_empty_intent(self, similarity):
        """Bos intent."""
        assert similarity._intent_similarity("", "") == 1.0
        assert similarity._intent_similarity("greet", "") == 0.0


# =============================================================================
# EpisodeSimilarity - Emotion Similarity Tests
# =============================================================================

class TestEmotionSimilarity:
    """Duygu benzerligi testleri."""

    def test_identical_emotion(self, similarity):
        """Ayni duygu."""
        score = similarity._emotion_similarity("happy", "happy")
        assert score == 1.0

    def test_same_category_emotion(self, similarity):
        """Ayni kategorideki duygu."""
        score = similarity._emotion_similarity("happy", "excited")
        assert score == 1.0  # Ikisi de "positive"

    def test_opposite_emotion(self, similarity):
        """Zit duygu."""
        score = similarity._emotion_similarity("happy", "sad")
        assert score == pytest.approx(0.2)  # positive vs negative = 0.8 mesafe

    def test_neutral_emotion(self, similarity):
        """Notr duygu."""
        score = similarity._emotion_similarity("neutral", "happy")
        assert score == 0.7  # neutral vs positive = 0.3 mesafe

    def test_empty_emotion(self, similarity):
        """Bos duygu."""
        assert similarity._emotion_similarity("", "") == 1.0


# =============================================================================
# EpisodeSimilarity - DialogueAct Similarity Tests
# =============================================================================

class TestDialogueActSimilarity:
    """DialogueAct benzerligi testleri."""

    def test_identical_acts(self, similarity):
        """Ayni act'ler."""
        score = similarity._dialogue_act_similarity(
            ["greet", "ask"],
            ["greet", "ask"]
        )
        assert score == 1.0

    def test_partial_overlap(self, similarity):
        """Kismi ortusen act'ler."""
        score = similarity._dialogue_act_similarity(
            ["greet", "ask"],
            ["greet", "inform"]
        )
        # 1 ortak (greet), 3 unique
        assert score == pytest.approx(1/3)

    def test_no_overlap(self, similarity):
        """Ortusmeyen act'ler."""
        score = similarity._dialogue_act_similarity(
            ["greet", "ask"],
            ["warn", "inform"]
        )
        assert score == 0.0

    def test_empty_acts(self, similarity):
        """Bos act listesi."""
        assert similarity._dialogue_act_similarity([], []) == 1.0
        assert similarity._dialogue_act_similarity(["greet"], []) == 0.0


# =============================================================================
# EpisodeSimilarity - Full Similarity Tests
# =============================================================================

class TestFullSimilarity:
    """Tam benzerlik hesaplama testleri."""

    def test_identical_episodes(self, similarity, sample_episode):
        """Ayni episode."""
        score = similarity.compute(sample_episode, sample_episode)
        # Kendisiyle karsilastirma 1.0 olmali
        assert score == pytest.approx(1.0)

    def test_similar_episodes(self, similarity, sample_episode, similar_episode):
        """Benzer episode'lar."""
        score = similarity.compute(sample_episode, similar_episode)
        # Benzer episode'lar yuksek skor almali
        assert score > 0.6

    def test_different_episodes(self, similarity, sample_episode, different_episode):
        """Farkli episode'lar."""
        score = similarity.compute(sample_episode, different_episode)
        # Farkli episode'lar dusuk skor almali
        assert score < 0.5

    def test_compute_detailed(self, similarity, sample_episode, similar_episode):
        """Detayli benzerlik hesaplama."""
        result = similarity.compute_detailed(sample_episode, similar_episode)

        assert isinstance(result, SimilarityResult)
        assert 0.0 <= result.total_score <= 1.0
        assert 0.0 <= result.text_score <= 1.0
        assert 0.0 <= result.intent_score <= 1.0


# =============================================================================
# EpisodeSimilarity - Batch Operations Tests
# =============================================================================

class TestBatchOperations:
    """Batch islem testleri."""

    def test_compute_batch(self, similarity, sample_episode, similar_episode, different_episode):
        """Batch benzerlik hesaplama."""
        candidates = [similar_episode, different_episode]
        results = similarity.compute_batch(sample_episode, candidates)

        assert len(results) == 2
        # Sonuclar skora gore sirali
        assert results[0][1] >= results[1][1]

    def test_compute_batch_with_threshold(self, similarity, sample_episode, similar_episode, different_episode):
        """Esik ile batch hesaplama."""
        candidates = [similar_episode, different_episode]
        results = similarity.compute_batch(
            sample_episode,
            candidates,
            min_threshold=0.5
        )

        # Sadece esik ustu sonuclar
        for _, score in results:
            assert score >= 0.5

    def test_compute_batch_excludes_self(self, similarity, sample_episode):
        """Kendisiyle karsilastirmayi haric tut."""
        candidates = [sample_episode]
        results = similarity.compute_batch(sample_episode, candidates)

        assert len(results) == 0

    def test_find_similar(self, similarity, sample_episode, similar_episode, different_episode):
        """Benzer episode'lari bul."""
        candidates = [similar_episode, different_episode]
        results = similarity.find_similar(sample_episode, candidates)

        # Sadece similar_threshold ustu
        for _, score in results:
            assert score >= similarity.config.similar_threshold


# =============================================================================
# Utility Functions Tests
# =============================================================================

class TestUtilityFunctions:
    """Yardimci fonksiyon testleri."""

    def test_jaccard_similarity(self):
        """Jaccard benzerligi."""
        assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
        assert jaccard_similarity({"a", "b"}, {"a", "c"}) == pytest.approx(1/3)
        assert jaccard_similarity({"a"}, {"b"}) == 0.0

    def test_jaccard_empty_sets(self):
        """Bos set'ler."""
        assert jaccard_similarity(set(), set()) == 1.0
        assert jaccard_similarity({"a"}, set()) == 0.0

    def test_levenshtein_distance(self):
        """Levenshtein mesafesi."""
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("abc", "") == 3
        assert levenshtein_distance("abc", "abc") == 0
        assert levenshtein_distance("abc", "abd") == 1
        assert levenshtein_distance("abc", "xyz") == 3

    def test_levenshtein_similarity(self):
        """Levenshtein benzerligi."""
        assert levenshtein_similarity("abc", "abc") == 1.0
        assert levenshtein_similarity("abc", "abd") == pytest.approx(2/3)
        assert levenshtein_similarity("", "") == 1.0

    def test_generate_episode_id(self):
        """Episode ID uretimi."""
        id1 = generate_episode_id()
        id2 = generate_episode_id()

        assert id1.startswith("ep_")
        assert id2.startswith("ep_")
        assert id1 != id2


# =============================================================================
# SimilarityResult Tests
# =============================================================================

class TestSimilarityResult:
    """SimilarityResult testleri."""

    def test_create_result(self):
        """Sonuc olusturma."""
        result = SimilarityResult(
            total_score=0.85,
            text_score=0.9,
            intent_score=0.8,
            emotion_score=0.7,
            dialogue_act_score=0.9,
            is_similar=True,
            is_cluster_candidate=True
        )

        assert result.total_score == 0.85
        assert result.is_similar is True

    def test_breakdown_report(self, similarity, sample_episode, similar_episode):
        """Detayli rapor."""
        breakdown = similarity.get_similarity_breakdown(
            sample_episode,
            similar_episode
        )

        assert "total_score" in breakdown
        assert "components" in breakdown
        assert "text" in breakdown["components"]
        assert "intent" in breakdown["components"]
