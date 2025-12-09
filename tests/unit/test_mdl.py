"""
tests/unit/test_mdl.py

ApproximateMDL testleri.
UEM v2 - Pattern degerlendirme ve MDL hesaplama testleri.

Test gruplari:
- MDLConfig testleri
- MDLScore testleri
- compute_compression_score testleri
- compute_pattern_length testleri
- compute_episode_length testleri
- evaluate_candidate testleri
- diversity bonus testleri
- risk penalty testleri
- compare_patterns testleri
- rank_patterns testleri
- filter_good_patterns testleri
- Integration testleri
"""

import pytest
from datetime import datetime
from typing import List

from core.learning.mdl import MDLConfig, MDLScore, ApproximateMDL
from core.learning.types import Pattern, PatternType
from core.learning.episode import Episode, EpisodeOutcome


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mdl():
    """Default ApproximateMDL instance."""
    return ApproximateMDL()


@pytest.fixture
def custom_config():
    """Custom MDLConfig."""
    return MDLConfig(
        compression_weight=0.6,
        diversity_weight=0.2,
        risk_weight=0.2,
        min_episodes_for_evaluation=3,
    )


@pytest.fixture
def sample_pattern():
    """Sample pattern for testing."""
    return Pattern(
        id="pattern_001",
        pattern_type=PatternType.RESPONSE,
        content="merhaba, size nasil yardimci olabilirim?",
        extra_data={"slots": ["greeting", "offer_help"]},
    )


@pytest.fixture
def simple_pattern():
    """Simple short pattern."""
    return Pattern(
        id="pattern_002",
        pattern_type=PatternType.RESPONSE,
        content="tamam",
        extra_data={},
    )


@pytest.fixture
def risky_pattern():
    """Pattern with risk keywords."""
    return Pattern(
        id="pattern_003",
        pattern_type=PatternType.RESPONSE,
        content="bu cok tehlikeli bir durum, zarar verebilir",
        extra_data={},
    )


@pytest.fixture
def ethical_concern_pattern():
    """Pattern with ethical concerns."""
    return Pattern(
        id="pattern_004",
        pattern_type=PatternType.RESPONSE,
        content="bu ayrimcilik iceren bir yaklasim olabilir",
        extra_data={},
    )


@pytest.fixture
def sample_episodes():
    """Sample episodes for testing."""
    return [
        Episode(
            id="ep_001",
            user_message="merhaba, nasil yardimci olabilirsin?",
            situation_summary={"topic": "greeting"},
            dialogue_acts=["GREET", "QUERY"],
            intent="greeting",
            emotion_label="neutral",
            constructions_used=["greeting_01"],
            outcome=EpisodeOutcome(success=True, explicit_feedback=0.8),
            trust_delta=0.1,
        ),
        Episode(
            id="ep_002",
            user_message="selam, bugün ne yapabiliriz?",
            situation_summary={"topic": "greeting"},
            dialogue_acts=["GREET", "SUGGEST"],
            intent="greeting",
            emotion_label="positive",
            constructions_used=["greeting_02"],
            outcome=EpisodeOutcome(success=True, explicit_feedback=0.7),
            trust_delta=0.05,
        ),
        Episode(
            id="ep_003",
            user_message="gunaydın, bir sorum var",
            situation_summary={"topic": "question"},
            dialogue_acts=["GREET", "QUERY"],
            intent="question",
            emotion_label="curious",
            constructions_used=["greeting_01", "question_01"],
            outcome=EpisodeOutcome(success=True, explicit_feedback=0.9),
            trust_delta=0.15,
        ),
    ]


@pytest.fixture
def diverse_episodes():
    """Diverse episodes with different intents and emotions."""
    return [
        Episode(
            id="ep_d01",
            user_message="bunu anlat",
            situation_summary={},
            dialogue_acts=["EXPLAIN"],
            intent="explain",
            emotion_label="curious",
            constructions_used=[],
            outcome=EpisodeOutcome(success=True),
            trust_delta=0.1,
        ),
        Episode(
            id="ep_d02",
            user_message="beni destekle",
            situation_summary={},
            dialogue_acts=["SUPPORT"],
            intent="support",
            emotion_label="anxious",
            constructions_used=[],
            outcome=EpisodeOutcome(success=True),
            trust_delta=0.05,
        ),
        Episode(
            id="ep_d03",
            user_message="öneri ver",
            situation_summary={},
            dialogue_acts=["SUGGEST"],
            intent="suggest",
            emotion_label="neutral",
            constructions_used=[],
            outcome=EpisodeOutcome(success=True),
            trust_delta=0.0,
        ),
        Episode(
            id="ep_d04",
            user_message="şikayet ediyorum",
            situation_summary={},
            dialogue_acts=["COMPLAIN"],
            intent="complaint",
            emotion_label="angry",
            constructions_used=[],
            outcome=EpisodeOutcome(success=True),
            trust_delta=-0.1,
        ),
    ]


# ============================================================================
# MDLConfig Tests
# ============================================================================

class TestMDLConfig:
    """MDLConfig testleri."""

    def test_default_config(self):
        """Default konfigürasyon değerlerini test et."""
        config = MDLConfig()
        assert config.compression_weight == 0.5
        assert config.diversity_weight == 0.3
        assert config.risk_weight == 0.2
        assert config.min_episodes_for_evaluation == 2

    def test_custom_weights(self):
        """Custom ağırlıkları test et."""
        config = MDLConfig(
            compression_weight=0.7,
            diversity_weight=0.2,
            risk_weight=0.1,
        )
        assert config.compression_weight == 0.7
        assert config.diversity_weight == 0.2
        assert config.risk_weight == 0.1

    def test_default_risk_keywords(self):
        """Default risk keyword'leri test et."""
        config = MDLConfig()
        assert "zarar" in config.risk_keywords
        assert "tehlike" in config.risk_keywords
        assert "yasadisi" in config.risk_keywords

    def test_default_ethical_concerns(self):
        """Default etik endişe keyword'leri test et."""
        config = MDLConfig()
        assert "ayrimcilik" in config.ethical_concerns
        assert "nefret" in config.ethical_concerns
        assert "manipulasyon" in config.ethical_concerns

    def test_custom_risk_keywords(self):
        """Custom risk keyword'leri test et."""
        custom_keywords = {"riskli", "sorunlu"}
        config = MDLConfig(risk_keywords=custom_keywords)
        assert config.risk_keywords == custom_keywords

    def test_diversity_bonus_defaults(self):
        """Diversity bonus default değerlerini test et."""
        config = MDLConfig()
        assert config.intent_diversity_bonus == 0.1
        assert config.emotion_diversity_bonus == 0.1
        assert config.unique_pattern_bonus == 0.1


# ============================================================================
# MDLScore Tests
# ============================================================================

class TestMDLScore:
    """MDLScore testleri."""

    def test_basic_score_creation(self):
        """Temel skor oluşturmayı test et."""
        score = MDLScore(
            compression_score=100.0,
            normalized_score=0.7,
            episode_count=5,
            avg_episode_length=50.0,
            pattern_length=20,
        )
        assert score.compression_score == 100.0
        assert score.normalized_score == 0.7
        assert score.episode_count == 5

    def test_is_good_pattern(self):
        """is_good_pattern property test."""
        good_score = MDLScore(
            compression_score=100.0,
            normalized_score=0.6,
            episode_count=3,
            avg_episode_length=40.0,
            pattern_length=15,
            final_score=0.6,
        )
        bad_score = MDLScore(
            compression_score=10.0,
            normalized_score=0.3,
            episode_count=3,
            avg_episode_length=40.0,
            pattern_length=15,
            final_score=0.3,
        )
        assert good_score.is_good_pattern is True
        assert bad_score.is_good_pattern is False

    def test_is_risky(self):
        """is_risky property test."""
        risky_score = MDLScore(
            compression_score=100.0,
            normalized_score=0.6,
            episode_count=3,
            avg_episode_length=40.0,
            pattern_length=15,
            risk_penalty=0.2,
        )
        safe_score = MDLScore(
            compression_score=100.0,
            normalized_score=0.6,
            episode_count=3,
            avg_episode_length=40.0,
            pattern_length=15,
            risk_penalty=0.05,
        )
        assert risky_score.is_risky is True
        assert safe_score.is_risky is False

    def test_post_init_final_score_calculation(self):
        """Post-init final score hesaplamasını test et."""
        score = MDLScore(
            compression_score=100.0,
            normalized_score=0.8,
            episode_count=3,
            avg_episode_length=40.0,
            pattern_length=15,
        )
        # post_init should set final_score = normalized_score if final_score is 0
        assert score.final_score == 0.8


# ============================================================================
# compute_compression_score Tests
# ============================================================================

class TestComputeCompressionScore:
    """compute_compression_score testleri."""

    def test_empty_episodes(self, mdl, sample_pattern):
        """Boş episode listesi ile test."""
        score = mdl.compute_compression_score(sample_pattern, [])
        assert score == 0.0

    def test_single_episode(self, mdl, sample_pattern, sample_episodes):
        """Tek episode ile test."""
        score = mdl.compute_compression_score(sample_pattern, [sample_episodes[0]])
        assert isinstance(score, float)

    def test_multiple_episodes(self, mdl, sample_pattern, sample_episodes):
        """Birden fazla episode ile test."""
        score = mdl.compute_compression_score(sample_pattern, sample_episodes)
        assert isinstance(score, float)

    def test_compression_increases_with_more_episodes(self, mdl, simple_pattern, sample_episodes):
        """Daha fazla episode = daha iyi compression test."""
        score_2 = mdl.compute_compression_score(simple_pattern, sample_episodes[:2])
        score_3 = mdl.compute_compression_score(simple_pattern, sample_episodes)
        # More episodes should generally result in better compression
        assert score_3 > score_2

    def test_shorter_pattern_better_compression(self, mdl, sample_pattern, simple_pattern, sample_episodes):
        """Daha kısa pattern = daha iyi compression test."""
        score_long = mdl.compute_compression_score(sample_pattern, sample_episodes)
        score_short = mdl.compute_compression_score(simple_pattern, sample_episodes)
        # Shorter pattern should have better compression
        assert score_short > score_long


# ============================================================================
# compute_pattern_length Tests
# ============================================================================

class TestComputePatternLength:
    """compute_pattern_length testleri."""

    def test_empty_pattern_content(self, mdl):
        """Boş içerikli pattern test."""
        pattern = Pattern(
            id="empty",
            pattern_type=PatternType.RESPONSE,
            content="",
            extra_data={},
        )
        length = mdl.compute_pattern_length(pattern)
        assert length == 2  # Just type_cost

    def test_pattern_with_slots(self, mdl, sample_pattern):
        """Slot'lu pattern uzunluk testi."""
        length = mdl.compute_pattern_length(sample_pattern)
        # content_length + (2 slots * 5) + type_cost
        expected_min = len(sample_pattern.content) + 10 + 2
        assert length == expected_min

    def test_pattern_without_slots(self, mdl, simple_pattern):
        """Slot'suz pattern uzunluk testi."""
        length = mdl.compute_pattern_length(simple_pattern)
        expected = len(simple_pattern.content) + 0 + 2
        assert length == expected


# ============================================================================
# compute_episode_length Tests
# ============================================================================

class TestComputeEpisodeLength:
    """compute_episode_length testleri."""

    def test_basic_episode_length(self, mdl, sample_episodes):
        """Temel episode uzunluk testi."""
        episode = sample_episodes[0]
        length = mdl.compute_episode_length(episode)
        expected_min = (
            len(episode.user_message) +
            len(episode.intent) +
            len(episode.emotion_label) +
            sum(len(act) for act in episode.dialogue_acts) +
            10  # metadata_cost
        )
        assert length == expected_min

    def test_empty_dialogue_acts(self, mdl):
        """Boş dialogue acts ile test."""
        episode = Episode(
            id="empty_acts",
            user_message="test message",
            situation_summary={},
            dialogue_acts=[],
            intent="test",
            emotion_label="neutral",
            constructions_used=[],
            outcome=EpisodeOutcome(success=True),
            trust_delta=0.0,
        )
        length = mdl.compute_episode_length(episode)
        assert length > 0


# ============================================================================
# evaluate_candidate Tests
# ============================================================================

class TestEvaluateCandidate:
    """evaluate_candidate testleri."""

    def test_insufficient_episodes(self, mdl, sample_pattern):
        """Yetersiz episode sayısı ile test."""
        single_episode = Episode(
            id="single",
            user_message="test",
            situation_summary={},
            dialogue_acts=["TEST"],
            intent="test",
            emotion_label="neutral",
            constructions_used=[],
            outcome=EpisodeOutcome(success=True),
            trust_delta=0.0,
        )
        score = mdl.evaluate_candidate(sample_pattern, [single_episode])
        assert score.normalized_score == 0.0
        assert "error" in score.details

    def test_valid_evaluation(self, mdl, sample_pattern, sample_episodes):
        """Geçerli değerlendirme testi."""
        score = mdl.evaluate_candidate(sample_pattern, sample_episodes)
        assert isinstance(score, MDLScore)
        assert score.episode_count == 3
        assert 0.0 <= score.normalized_score <= 1.0
        assert 0.0 <= score.final_score <= 1.0

    def test_evaluation_with_existing_patterns(self, mdl, sample_pattern, simple_pattern, sample_episodes):
        """Mevcut pattern'lerle değerlendirme testi."""
        existing = [simple_pattern]
        score = mdl.evaluate_candidate(sample_pattern, sample_episodes, existing)
        assert isinstance(score, MDLScore)

    def test_final_score_formula(self, mdl, sample_pattern, sample_episodes):
        """Final score formülünü test et."""
        score = mdl.evaluate_candidate(sample_pattern, sample_episodes)
        expected = (
            score.normalized_score * mdl.config.compression_weight +
            score.diversity_bonus * mdl.config.diversity_weight -
            score.risk_penalty * mdl.config.risk_weight
        )
        expected = max(0.0, min(1.0, expected))
        assert score.final_score == pytest.approx(expected, abs=0.01)


# ============================================================================
# Diversity Bonus Tests
# ============================================================================

class TestDiversityBonus:
    """Diversity bonus testleri."""

    def test_no_diversity_bonus(self, mdl, sample_pattern):
        """Çeşitlilik olmadan bonus testi."""
        same_intent_episodes = [
            Episode(
                id=f"ep_{i}",
                user_message="merhaba",
                situation_summary={},
                dialogue_acts=["GREET"],
                intent="greeting",
                emotion_label="neutral",
                constructions_used=[],
                outcome=EpisodeOutcome(success=True),
                trust_delta=0.0,
            )
            for i in range(3)
        ]
        score = mdl.evaluate_candidate(sample_pattern, same_intent_episodes)
        # Same intent and emotion = low diversity bonus
        assert score.diversity_bonus < 0.1

    def test_high_diversity_bonus(self, mdl, sample_pattern, diverse_episodes):
        """Yüksek çeşitlilik bonusu testi."""
        score = mdl.evaluate_candidate(sample_pattern, diverse_episodes)
        # Different intents and emotions = higher diversity bonus
        assert score.diversity_bonus > 0.1

    def test_uniqueness_bonus(self, mdl, sample_pattern, sample_episodes):
        """Benzersizlik bonusu testi."""
        # Pattern is unique (no existing patterns)
        score_unique = mdl.evaluate_candidate(sample_pattern, sample_episodes, [])

        # Same pattern in existing list
        score_not_unique = mdl.evaluate_candidate(
            sample_pattern, sample_episodes, [sample_pattern]
        )
        # Unique pattern should have higher diversity bonus
        assert score_unique.diversity_bonus >= score_not_unique.diversity_bonus


# ============================================================================
# Risk Penalty Tests
# ============================================================================

class TestRiskPenalty:
    """Risk penalty testleri."""

    def test_no_risk_penalty(self, mdl, sample_pattern, sample_episodes):
        """Risk içermeyen pattern testi."""
        score = mdl.evaluate_candidate(sample_pattern, sample_episodes)
        assert score.risk_penalty == 0.0

    def test_risk_keyword_penalty(self, mdl, risky_pattern, sample_episodes):
        """Risk keyword'ü cezası testi."""
        score = mdl.evaluate_candidate(risky_pattern, sample_episodes)
        assert score.risk_penalty > 0.0
        assert score.is_risky is True

    def test_ethical_concern_penalty(self, mdl, ethical_concern_pattern, sample_episodes):
        """Etik endişe cezası testi."""
        score = mdl.evaluate_candidate(ethical_concern_pattern, sample_episodes)
        assert score.risk_penalty > 0.0

    def test_combined_risk_and_ethical(self, mdl, sample_episodes):
        """Hem risk hem etik endişe içeren pattern testi."""
        combined_pattern = Pattern(
            id="combined_risk",
            pattern_type=PatternType.RESPONSE,
            content="tehlikeli durumlar ayrimcilik yaratabilir",
            extra_data={},
        )
        score = mdl.evaluate_candidate(combined_pattern, sample_episodes)
        assert score.risk_penalty > 0.2

    def test_risk_penalty_capped_at_one(self, mdl, sample_episodes):
        """Risk cezasının 1.0'da sınırlandırılması testi."""
        very_risky_pattern = Pattern(
            id="very_risky",
            pattern_type=PatternType.RESPONSE,
            content="zarar tehlike yasadisi suç hacklemek olum siddet ayrimcilik nefret manipulasyon",
            extra_data={},
        )
        score = mdl.evaluate_candidate(very_risky_pattern, sample_episodes)
        assert score.risk_penalty <= 1.0


# ============================================================================
# compare_patterns Tests
# ============================================================================

class TestComparePatterns:
    """compare_patterns testleri."""

    def test_compare_better_pattern_wins(self, mdl, sample_pattern, risky_pattern, sample_episodes):
        """Daha iyi pattern'in seçilmesi testi."""
        better = mdl.compare_patterns(sample_pattern, risky_pattern, sample_episodes)
        # Non-risky pattern should win
        assert better.id == sample_pattern.id

    def test_compare_same_patterns(self, mdl, sample_pattern, sample_episodes):
        """Aynı pattern'lerin karşılaştırılması testi."""
        result = mdl.compare_patterns(sample_pattern, sample_pattern, sample_episodes)
        assert result.id == sample_pattern.id

    def test_compare_with_existing_patterns(self, mdl, sample_pattern, simple_pattern, sample_episodes):
        """Mevcut pattern'lerle karşılaştırma testi."""
        existing = [simple_pattern]
        result = mdl.compare_patterns(
            sample_pattern, simple_pattern, sample_episodes, existing
        )
        assert result.id in [sample_pattern.id, simple_pattern.id]


# ============================================================================
# rank_patterns Tests
# ============================================================================

class TestRankPatterns:
    """rank_patterns testleri."""

    def test_empty_patterns_list(self, mdl, sample_episodes):
        """Boş pattern listesi testi."""
        result = mdl.rank_patterns([], sample_episodes)
        assert result == []

    def test_single_pattern_ranking(self, mdl, sample_pattern, sample_episodes):
        """Tek pattern sıralama testi."""
        result = mdl.rank_patterns([sample_pattern], sample_episodes)
        assert len(result) == 1
        assert result[0][0].id == sample_pattern.id

    def test_multiple_patterns_ranking(self, mdl, sample_pattern, simple_pattern, risky_pattern, sample_episodes):
        """Birden fazla pattern sıralama testi."""
        patterns = [risky_pattern, sample_pattern, simple_pattern]
        result = mdl.rank_patterns(patterns, sample_episodes)
        assert len(result) == 3
        # Risky pattern should be last (lowest score)
        assert result[-1][0].id == risky_pattern.id

    def test_ranking_order_by_final_score(self, mdl, sample_pattern, simple_pattern, sample_episodes):
        """Final score'a göre sıralama testi."""
        patterns = [sample_pattern, simple_pattern]
        result = mdl.rank_patterns(patterns, sample_episodes)
        # Should be sorted by final_score descending
        scores = [r[1].final_score for r in result]
        assert scores == sorted(scores, reverse=True)


# ============================================================================
# filter_good_patterns Tests
# ============================================================================

class TestFilterGoodPatterns:
    """filter_good_patterns testleri."""

    def test_filter_removes_risky(self, mdl, sample_pattern, risky_pattern, sample_episodes):
        """Riskli pattern'lerin filtrelenmesi testi."""
        patterns = [sample_pattern, risky_pattern]
        good = mdl.filter_good_patterns(patterns, sample_episodes)
        # Risky pattern should be filtered out
        assert risky_pattern not in good

    def test_filter_with_custom_threshold(self, mdl, sample_pattern, sample_episodes):
        """Custom eşik değeri ile filtreleme testi."""
        good_low = mdl.filter_good_patterns([sample_pattern], sample_episodes, min_score=0.1)
        good_high = mdl.filter_good_patterns([sample_pattern], sample_episodes, min_score=0.9)
        # Low threshold should include more patterns
        assert len(good_low) >= len(good_high)

    def test_filter_empty_input(self, mdl, sample_episodes):
        """Boş girdi ile filtreleme testi."""
        result = mdl.filter_good_patterns([], sample_episodes)
        assert result == []


# ============================================================================
# get_score_breakdown Tests
# ============================================================================

class TestGetScoreBreakdown:
    """get_score_breakdown testleri."""

    def test_breakdown_structure(self, mdl, sample_pattern, sample_episodes):
        """Breakdown yapısı testi."""
        breakdown = mdl.get_score_breakdown(sample_pattern, sample_episodes)

        assert "pattern_id" in breakdown
        assert "final_score" in breakdown
        assert "is_good" in breakdown
        assert "is_risky" in breakdown
        assert "components" in breakdown

    def test_breakdown_components(self, mdl, sample_pattern, sample_episodes):
        """Breakdown bileşenleri testi."""
        breakdown = mdl.get_score_breakdown(sample_pattern, sample_episodes)

        components = breakdown["components"]
        assert "compression" in components
        assert "diversity" in components
        assert "risk" in components

    def test_breakdown_episode_stats(self, mdl, sample_pattern, sample_episodes):
        """Breakdown episode istatistikleri testi."""
        breakdown = mdl.get_score_breakdown(sample_pattern, sample_episodes)

        assert breakdown["episode_stats"]["count"] == 3


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Entegrasyon testleri."""

    def test_full_workflow(self, mdl, sample_episodes):
        """Tam iş akışı testi."""
        # Create patterns
        patterns = [
            Pattern(
                id=f"pattern_{i}",
                pattern_type=PatternType.RESPONSE,
                content=f"cevap {i} icerigi burada",
                extra_data={},
            )
            for i in range(5)
        ]

        # Rank patterns
        ranked = mdl.rank_patterns(patterns, sample_episodes)
        assert len(ranked) == 5

        # Filter good patterns
        good = mdl.filter_good_patterns(patterns, sample_episodes, min_score=0.3)
        assert isinstance(good, list)

        # Get best pattern
        if ranked:
            best_pattern, best_score = ranked[0]
            breakdown = mdl.get_score_breakdown(best_pattern, sample_episodes)
            assert breakdown["pattern_id"] == best_pattern.id

    def test_custom_config_workflow(self, custom_config, sample_pattern, sample_episodes):
        """Custom config ile iş akışı testi."""
        mdl = ApproximateMDL(config=custom_config)

        score = mdl.evaluate_candidate(sample_pattern, sample_episodes)
        assert isinstance(score, MDLScore)

        # Verify custom weights are used
        expected = (
            score.normalized_score * custom_config.compression_weight +
            score.diversity_bonus * custom_config.diversity_weight -
            score.risk_penalty * custom_config.risk_weight
        )
        expected = max(0.0, min(1.0, expected))
        assert score.final_score == pytest.approx(expected, abs=0.01)

    def test_pattern_selection_scenario(self, mdl, sample_episodes):
        """Pattern seçim senaryosu testi."""
        # Simulate pattern candidates
        safe_short = Pattern(
            id="safe_short",
            pattern_type=PatternType.RESPONSE,
            content="merhaba",
            extra_data={},
        )
        safe_long = Pattern(
            id="safe_long",
            pattern_type=PatternType.RESPONSE,
            content="merhaba, size bugun nasil yardimci olabilirim acaba?",
            extra_data={"slots": ["greeting", "offer"]},
        )
        risky = Pattern(
            id="risky",
            pattern_type=PatternType.RESPONSE,
            content="bu tehlikeli bir durum olabilir",
            extra_data={},
        )

        # Rank and select
        patterns = [safe_short, safe_long, risky]
        ranked = mdl.rank_patterns(patterns, sample_episodes)

        # Best should not be risky
        best_pattern, best_score = ranked[0]
        assert best_pattern.id != "risky"

    def test_incremental_evaluation(self, mdl, sample_pattern, sample_episodes):
        """Artımlı değerlendirme testi."""
        # Evaluate with increasing episodes
        scores = []
        for i in range(2, len(sample_episodes) + 1):
            score = mdl.evaluate_candidate(sample_pattern, sample_episodes[:i])
            scores.append(score)

        # All should be valid scores
        assert all(isinstance(s, MDLScore) for s in scores)
        assert all(0.0 <= s.final_score <= 1.0 for s in scores)


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge case testleri."""

    def test_pattern_with_none_content(self, mdl, sample_episodes):
        """None içerikli pattern testi."""
        pattern = Pattern(
            id="none_content",
            pattern_type=PatternType.RESPONSE,
            content=None,
            extra_data={},
        )
        # Should not raise, but return valid score
        score = mdl.evaluate_candidate(pattern, sample_episodes)
        assert isinstance(score, MDLScore)

    def test_episode_with_empty_fields(self, mdl, sample_pattern):
        """Boş alanlarla episode testi."""
        episodes = [
            Episode(
                id="empty_fields",
                user_message="",
                situation_summary={},
                dialogue_acts=[],
                intent="",
                emotion_label="",
                constructions_used=[],
                outcome=EpisodeOutcome(success=True),
                trust_delta=0.0,
            )
            for _ in range(3)
        ]
        score = mdl.evaluate_candidate(sample_pattern, episodes)
        assert isinstance(score, MDLScore)

    def test_very_long_pattern(self, mdl, sample_episodes):
        """Çok uzun pattern testi."""
        long_content = "bu cok uzun bir pattern icerigi " * 100
        pattern = Pattern(
            id="long_pattern",
            pattern_type=PatternType.RESPONSE,
            content=long_content,
            extra_data={"slots": [f"slot_{i}" for i in range(20)]},
        )
        score = mdl.evaluate_candidate(pattern, sample_episodes)
        assert isinstance(score, MDLScore)
        # Long pattern should have lower compression score
        assert score.normalized_score < 0.8

    def test_jaccard_similarity_edge_cases(self, mdl):
        """Jaccard similarity edge case'leri."""
        # Empty strings
        assert mdl._jaccard_similarity("", "") == 0.0
        assert mdl._jaccard_similarity("test", "") == 0.0
        assert mdl._jaccard_similarity("", "test") == 0.0

        # Identical strings
        assert mdl._jaccard_similarity("test", "test") == 1.0
