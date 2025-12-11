"""
tests/unit/test_feedback_reranking.py

Feedback-driven construction re-ranking testleri.

UEM v2 - Faz 5 Feedback-Driven Learning.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.learning.feedback_stats import ConstructionStats
from core.learning.feedback_store import FeedbackStore
from core.learning.feedback_aggregator import FeedbackAggregator
from core.learning.feedback_scorer import (
    WIN_EXPLICIT,
    LOSS_EXPLICIT,
    WIN_IMPLICIT,
    LOSS_IMPLICIT,
    PRIOR_WINS,
    PRIOR_LOSSES,
    MIN_SAMPLES_FOR_FULL_INFLUENCE,
    compute_wins_losses,
    compute_feedback_mean,
    compute_influence,
    compute_adjustment,
    compute_final_score,
    explain_score,
    is_score_significant,
    get_feedback_summary,
)
from core.learning.episode_types import EpisodeLog, ImplicitFeedback
from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct


# ============================================================================
# ConstructionStats Tests
# ============================================================================

class TestConstructionStats:
    """ConstructionStats dataclass testleri."""

    def test_construction_stats_defaults(self):
        """Default değerler doğru mu?"""
        stats = ConstructionStats(construction_id="test_01")

        assert stats.construction_id == "test_01"
        assert stats.total_uses == 0
        assert stats.explicit_pos == 0
        assert stats.explicit_neg == 0
        assert stats.implicit_pos == 0
        assert stats.implicit_neg == 0
        assert stats.cached_score == 0.5
        assert stats.last_updated is None

    def test_construction_stats_to_dict(self):
        """to_dict() doğru çalışıyor mu?"""
        now = datetime.now()
        stats = ConstructionStats(
            construction_id="test_01",
            total_uses=10,
            explicit_pos=3,
            explicit_neg=1,
            implicit_pos=5,
            implicit_neg=2,
            cached_score=0.7,
            last_updated=now,
        )

        d = stats.to_dict()

        assert d["construction_id"] == "test_01"
        assert d["total_uses"] == 10
        assert d["explicit_pos"] == 3
        assert d["explicit_neg"] == 1
        assert d["implicit_pos"] == 5
        assert d["implicit_neg"] == 2
        assert d["cached_score"] == 0.7
        assert d["last_updated"] == now.isoformat()

    def test_construction_stats_from_dict(self):
        """from_dict() doğru çalışıyor mu?"""
        now = datetime.now()
        d = {
            "construction_id": "test_01",
            "total_uses": 10,
            "explicit_pos": 3,
            "explicit_neg": 1,
            "implicit_pos": 5,
            "implicit_neg": 2,
            "cached_score": 0.7,
            "last_updated": now.isoformat(),
        }

        stats = ConstructionStats.from_dict(d)

        assert stats.construction_id == "test_01"
        assert stats.total_uses == 10
        assert stats.explicit_pos == 3
        assert stats.explicit_neg == 1
        assert stats.implicit_pos == 5
        assert stats.implicit_neg == 2
        assert stats.cached_score == 0.7
        # Datetime comparison (ignoring microseconds)
        assert stats.last_updated.replace(microsecond=0) == now.replace(microsecond=0)

    def test_construction_stats_to_dict_from_dict_roundtrip(self):
        """to_dict() ve from_dict() roundtrip doğru mu?"""
        original = ConstructionStats(
            construction_id="test_roundtrip",
            total_uses=15,
            explicit_pos=5,
            explicit_neg=2,
            implicit_pos=8,
            implicit_neg=3,
            cached_score=0.65,
            last_updated=datetime.now(),
        )

        d = original.to_dict()
        restored = ConstructionStats.from_dict(d)

        assert restored.construction_id == original.construction_id
        assert restored.total_uses == original.total_uses
        assert restored.explicit_pos == original.explicit_pos
        assert restored.explicit_neg == original.explicit_neg
        assert restored.implicit_pos == original.implicit_pos
        assert restored.implicit_neg == original.implicit_neg
        assert restored.cached_score == original.cached_score

    def test_construction_stats_properties(self):
        """Property'ler doğru hesaplanıyor mu?"""
        stats = ConstructionStats(
            construction_id="test_01",
            total_uses=10,
            explicit_pos=3,
            explicit_neg=1,
            implicit_pos=5,
            implicit_neg=2,
        )

        assert stats.total_explicit == 4
        assert stats.total_implicit == 7
        assert stats.total_feedback == 11
        assert stats.explicit_ratio == 0.75  # 3/4
        assert stats.implicit_ratio == pytest.approx(5 / 7)

    def test_construction_stats_ratio_no_feedback(self):
        """Feedback yoksa ratio 0.5 dönmeli."""
        stats = ConstructionStats(construction_id="test_01")

        assert stats.explicit_ratio == 0.5
        assert stats.implicit_ratio == 0.5


# ============================================================================
# FeedbackStore Tests
# ============================================================================

class TestFeedbackStore:
    """FeedbackStore persistence testleri."""

    def test_feedback_store_save_load(self):
        """Save ve load doğru çalışıyor mu?"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            stats = ConstructionStats(
                construction_id="test_01",
                total_uses=5,
                explicit_pos=2,
                cached_score=0.7,
            )
            store.update_stats(stats)

            # Yeni store oluştur ve yükle
            store2 = FeedbackStore(path)
            loaded = store2.get_stats("test_01")

            assert loaded is not None
            assert loaded.construction_id == "test_01"
            assert loaded.total_uses == 5
            assert loaded.explicit_pos == 2
            assert loaded.cached_score == 0.7

    def test_feedback_store_get_nonexistent_returns_none(self):
        """Var olmayan ID için None dönmeli."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            result = store.get_stats("nonexistent_id")
            assert result is None

    def test_feedback_store_bulk_update(self):
        """bulk_update() doğru çalışıyor mu?"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            stats_dict = {
                "test_01": ConstructionStats(construction_id="test_01", total_uses=5),
                "test_02": ConstructionStats(construction_id="test_02", total_uses=10),
                "test_03": ConstructionStats(construction_id="test_03", total_uses=15),
            }
            store.bulk_update(stats_dict)

            assert store.count() == 3
            assert store.get_stats("test_01").total_uses == 5
            assert store.get_stats("test_02").total_uses == 10
            assert store.get_stats("test_03").total_uses == 15

    def test_feedback_store_get_all(self):
        """get_all() doğru çalışıyor mu?"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            stats_dict = {
                "test_01": ConstructionStats(construction_id="test_01"),
                "test_02": ConstructionStats(construction_id="test_02"),
            }
            store.bulk_update(stats_dict)

            all_stats = store.get_all()
            assert len(all_stats) == 2
            assert "test_01" in all_stats
            assert "test_02" in all_stats

    def test_feedback_store_clear(self):
        """clear() doğru çalışıyor mu?"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            store.update_stats(ConstructionStats(construction_id="test_01"))
            assert store.count() == 1

            store.clear()
            assert store.count() == 0

    def test_feedback_store_contains(self):
        """__contains__ doğru çalışıyor mu?"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            store.update_stats(ConstructionStats(construction_id="test_01"))

            assert "test_01" in store
            assert "test_02" not in store


# ============================================================================
# FeedbackAggregator Tests
# ============================================================================

class TestFeedbackAggregator:
    """FeedbackAggregator testleri."""

    def _create_episode(
        self,
        construction_id: str,
        explicit: float = None,
        implicit: ImplicitFeedback = None
    ) -> EpisodeLog:
        """Test için EpisodeLog oluştur."""
        return EpisodeLog(
            id="test_ep",
            session_id="test_session",
            turn_number=1,
            user_message="test",
            user_message_normalized="test",
            intent_primary=IntentCategory.GREETING,
            construction_id=construction_id,
            feedback_explicit=explicit,
            feedback_implicit=implicit,
        )

    def test_aggregator_counts_uses(self):
        """Kullanım sayısı doğru sayılıyor mu?"""
        episodes = [
            self._create_episode("test_01"),
            self._create_episode("test_01"),
            self._create_episode("test_02"),
        ]

        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate(episodes)

        assert stats["test_01"].total_uses == 2
        assert stats["test_02"].total_uses == 1

    def test_aggregator_counts_explicit_feedback(self):
        """Explicit feedback doğru sayılıyor mu?"""
        episodes = [
            self._create_episode("test_01", explicit=1.0),  # pos
            self._create_episode("test_01", explicit=1.0),  # pos
            self._create_episode("test_01", explicit=-1.0),  # neg
            self._create_episode("test_01", explicit=0.0),  # neutral (ignored)
        ]

        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate(episodes)

        assert stats["test_01"].explicit_pos == 2
        assert stats["test_01"].explicit_neg == 1

    def test_aggregator_counts_implicit_feedback(self):
        """Implicit feedback doğru sayılıyor mu?"""
        episodes = [
            self._create_episode(
                "test_01",
                implicit=ImplicitFeedback(user_thanked=True)
            ),
            self._create_episode(
                "test_01",
                implicit=ImplicitFeedback(conversation_continued=True)
            ),
            self._create_episode(
                "test_01",
                implicit=ImplicitFeedback(user_rephrased=True)
            ),
            self._create_episode(
                "test_01",
                implicit=ImplicitFeedback(user_complained=True, session_ended_abruptly=True)
            ),
        ]

        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate(episodes)

        # Pozitif: user_thanked(1) + conversation_continued(1) = 2
        assert stats["test_01"].implicit_pos == 2
        # Negatif: user_rephrased(1) + user_complained(1) + session_ended_abruptly(1) = 3
        assert stats["test_01"].implicit_neg == 3

    def test_aggregator_empty_episodes(self):
        """Boş episode listesi için boş stats dönmeli."""
        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate([])

        assert len(stats) == 0

    def test_aggregator_skips_empty_construction_id(self):
        """Construction ID boşsa atlamalı."""
        episodes = [
            self._create_episode(""),
            self._create_episode("test_01"),
        ]

        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate(episodes)

        assert len(stats) == 1
        assert "test_01" in stats

    def test_aggregator_updates_cached_score(self):
        """Cached score hesaplanıyor mu?"""
        episodes = [
            self._create_episode("test_01", explicit=1.0),
            self._create_episode("test_01", explicit=1.0),
            self._create_episode("test_01", explicit=1.0),
        ]

        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate(episodes)

        # Tüm feedback pozitif, score yüksek olmalı
        assert stats["test_01"].cached_score > 0.5
        assert stats["test_01"].last_updated is not None

    def test_aggregator_get_summary(self):
        """get_summary() doğru çalışıyor mu?"""
        stats = {
            "test_01": ConstructionStats(
                construction_id="test_01",
                total_uses=5,
                explicit_pos=2,
                explicit_neg=1,
                implicit_pos=3,
                implicit_neg=1,
                cached_score=0.6,
            ),
            "test_02": ConstructionStats(
                construction_id="test_02",
                total_uses=10,
                explicit_pos=5,
                explicit_neg=2,
                implicit_pos=4,
                implicit_neg=2,
                cached_score=0.7,
            ),
        }

        aggregator = FeedbackAggregator()
        summary = aggregator.get_summary(stats)

        assert summary["total_constructions"] == 2
        assert summary["total_uses"] == 15
        assert summary["explicit_positive"] == 7
        assert summary["explicit_negative"] == 3
        assert summary["implicit_positive"] == 7
        assert summary["implicit_negative"] == 3


# ============================================================================
# FeedbackScorer Tests
# ============================================================================

class TestFeedbackScorer:
    """Feedback scorer formül testleri."""

    def test_compute_feedback_mean_no_feedback_returns_half(self):
        """Feedback yoksa 0.5 dönmeli."""
        stats = ConstructionStats(construction_id="test")
        wins, losses = compute_wins_losses(stats)
        mean = compute_feedback_mean(wins, losses)

        # Prior: (1 + 1) / (0 + 0 + 1 + 1) = 0.5
        assert mean == pytest.approx(0.5)

    def test_compute_feedback_mean_all_positive(self):
        """Tüm feedback pozitif ise yüksek skor."""
        stats = ConstructionStats(
            construction_id="test",
            explicit_pos=10,
            explicit_neg=0,
        )
        wins, losses = compute_wins_losses(stats)
        mean = compute_feedback_mean(wins, losses)

        # (10 + 1) / (10 + 0 + 1 + 1) = 11/12 ≈ 0.917
        assert mean > 0.9

    def test_compute_feedback_mean_all_negative(self):
        """Tüm feedback negatif ise düşük skor."""
        stats = ConstructionStats(
            construction_id="test",
            explicit_pos=0,
            explicit_neg=10,
        )
        wins, losses = compute_wins_losses(stats)
        mean = compute_feedback_mean(wins, losses)

        # (0 + 1) / (0 + 10 + 1 + 1) = 1/12 ≈ 0.083
        assert mean < 0.1

    def test_compute_influence_zero_uses(self):
        """0 kullanım için etki 0 olmalı."""
        influence = compute_influence(0)
        assert influence == 0.0

    def test_compute_influence_full_at_threshold(self):
        """MIN_SAMPLES_FOR_FULL_INFLUENCE kullanımda tam etki."""
        influence = compute_influence(MIN_SAMPLES_FOR_FULL_INFLUENCE)
        assert influence == 1.0

    def test_compute_influence_half_at_half_threshold(self):
        """Eşiğin yarısında yarı etki."""
        influence = compute_influence(MIN_SAMPLES_FOR_FULL_INFLUENCE // 2)
        assert influence == pytest.approx(0.5, abs=0.1)

    def test_compute_influence_capped_at_one(self):
        """Etki 1.0'ı geçmemeli."""
        influence = compute_influence(1000)
        assert influence == 1.0

    def test_compute_adjustment_neutral(self):
        """Nötr feedback için adjustment 1.0 olmalı."""
        stats = ConstructionStats(construction_id="test")
        adjustment = compute_adjustment(stats)

        # total_uses=0 → influence=0 → adjustment=1.0
        assert adjustment == 1.0

    def test_compute_adjustment_positive_boost(self):
        """Pozitif feedback için adjustment > 1.0 olmalı."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=20,  # Full influence
            explicit_pos=10,
            explicit_neg=0,
        )
        adjustment = compute_adjustment(stats)

        assert adjustment > 1.0

    def test_compute_adjustment_negative_penalty(self):
        """Negatif feedback için adjustment < 1.0 olmalı."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=20,  # Full influence
            explicit_pos=0,
            explicit_neg=10,
        )
        adjustment = compute_adjustment(stats)

        assert adjustment < 1.0

    def test_compute_final_score_returns_metadata(self):
        """compute_final_score() metadata döndürmeli."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=10,
            explicit_pos=5,
            explicit_neg=1,
        )
        final_score, metadata = compute_final_score(0.8, stats)

        assert "base_score" in metadata
        assert "feedback_mean" in metadata
        assert "influence" in metadata
        assert "adjustment" in metadata
        assert "final_score" in metadata
        assert "total_uses" in metadata
        assert "explicit_pos" in metadata
        assert "explicit_neg" in metadata

        assert metadata["base_score"] == pytest.approx(0.8)
        assert metadata["final_score"] == pytest.approx(final_score)

    def test_compute_final_score_applies_adjustment(self):
        """Final skor = base_score * adjustment."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=20,
            explicit_pos=10,
            explicit_neg=0,
        )
        base_score = 0.6
        final_score, metadata = compute_final_score(base_score, stats)

        expected = base_score * metadata["adjustment"]
        assert final_score == pytest.approx(expected, abs=0.001)

    def test_explain_score_returns_string(self):
        """explain_score() string döndürmeli."""
        stats = ConstructionStats(
            construction_id="test_explain",
            total_uses=5,
            explicit_pos=2,
        )
        explanation = explain_score(0.7, stats)

        assert isinstance(explanation, str)
        assert "test_explain" in explanation
        assert "Base score" in explanation

    def test_is_score_significant_with_enough_data(self):
        """Yeterli veri ve sapma varsa significant olmalı."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=10,
            explicit_pos=10,
            explicit_neg=0,
        )
        assert is_score_significant(stats)

    def test_is_score_significant_not_enough_data(self):
        """Yeterli veri yoksa significant olmamalı."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=1,
            explicit_pos=1,
            explicit_neg=0,
        )
        assert not is_score_significant(stats)

    def test_get_feedback_summary(self):
        """get_feedback_summary() özet döndürmeli."""
        stats = ConstructionStats(
            construction_id="test",
            total_uses=10,
            explicit_pos=8,
            explicit_neg=1,
        )
        summary = get_feedback_summary(stats)

        assert "sentiment" in summary
        assert "score" in summary
        assert "uses" in summary
        assert summary["sentiment"] == "positive"
        assert summary["uses"] == 10


# ============================================================================
# Selector Re-ranking Tests
# ============================================================================

class TestSelectorReranking:
    """ConstructionSelector feedback re-ranking testleri."""

    def test_selector_without_feedback_store_unchanged(self):
        """FeedbackStore olmadan skor değişmemeli."""
        from core.language.construction.selector import (
            ConstructionSelector,
            ConstructionScore,
        )
        from core.language.construction.grammar import ConstructionGrammar

        grammar = ConstructionGrammar()
        selector = ConstructionSelector(grammar, feedback_store=None)

        # Mock candidates
        mock_construction = MagicMock()
        mock_construction.id = "test_01"

        candidates = [
            ConstructionScore(
                construction=mock_construction,
                total_score=0.8,
            )
        ]

        result = selector._apply_feedback_rerank(candidates)

        assert len(result) == 1
        assert result[0].total_score == 0.8

    def test_selector_reranks_by_feedback(self):
        """Feedback'e göre yeniden sıralama yapılmalı."""
        from core.language.construction.selector import (
            ConstructionSelector,
            ConstructionScore,
        )
        from core.language.construction.grammar import ConstructionGrammar

        # FeedbackStore mock
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)

            # test_02 daha iyi feedback'e sahip
            store.update_stats(ConstructionStats(
                construction_id="test_01",
                total_uses=20,
                explicit_pos=2,
                explicit_neg=8,  # Çoğunlukla negatif
            ))
            store.update_stats(ConstructionStats(
                construction_id="test_02",
                total_uses=20,
                explicit_pos=8,
                explicit_neg=2,  # Çoğunlukla pozitif
            ))

            grammar = ConstructionGrammar()
            selector = ConstructionSelector(grammar, feedback_store=store)

            # İki candidate, başlangıçta test_01 önde
            mock_c1 = MagicMock()
            mock_c1.id = "test_01"
            mock_c2 = MagicMock()
            mock_c2.id = "test_02"

            candidates = [
                ConstructionScore(construction=mock_c1, total_score=0.8),
                ConstructionScore(construction=mock_c2, total_score=0.75),
            ]

            result = selector._apply_feedback_rerank(candidates)

            # test_02 pozitif feedback sayesinde öne geçmeli
            assert result[0].construction.id == "test_02"

    def test_selector_adds_feedback_metadata(self):
        """Feedback metadata eklenmeli."""
        from core.language.construction.selector import (
            ConstructionSelector,
            ConstructionScore,
        )
        from core.language.construction.grammar import ConstructionGrammar

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)
            store.update_stats(ConstructionStats(
                construction_id="test_01",
                total_uses=10,
                explicit_pos=5,
            ))

            grammar = ConstructionGrammar()
            selector = ConstructionSelector(grammar, feedback_store=store)

            mock_c = MagicMock()
            mock_c.id = "test_01"

            candidates = [ConstructionScore(construction=mock_c, total_score=0.7)]
            result = selector._apply_feedback_rerank(candidates)

            assert result[0].feedback_metadata is not None
            assert "feedback_mean" in result[0].feedback_metadata
            assert "adjustment" in result[0].feedback_metadata

    def test_selector_no_stats_uses_default_metadata(self):
        """Stats olmayan construction için default metadata kullanılmalı."""
        from core.language.construction.selector import (
            ConstructionSelector,
            ConstructionScore,
        )
        from core.language.construction.grammar import ConstructionGrammar

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)
            # Store'a bir şey ekle ki boş olmasın
            store.update_stats(ConstructionStats(construction_id="other_construction"))

            grammar = ConstructionGrammar()
            selector = ConstructionSelector(grammar, feedback_store=store)

            mock_c = MagicMock()
            mock_c.id = "unknown_construction"  # Store'da olmayan construction

            candidates = [ConstructionScore(construction=mock_c, total_score=0.7)]
            result = selector._apply_feedback_rerank(candidates)

            assert result[0].feedback_metadata is not None
            assert result[0].feedback_metadata["adjustment"] == 1.0
            assert result[0].feedback_metadata["total_uses"] == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestFeedbackRerankingIntegration:
    """Entegrasyon testleri."""

    def test_full_aggregation_to_reranking_flow(self):
        """Tam akış: episode → aggregate → store → selector."""
        from core.language.construction.selector import (
            ConstructionSelector,
            ConstructionScore,
        )
        from core.language.construction.grammar import ConstructionGrammar

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Episode'lar oluştur
            episodes = [
                EpisodeLog(
                    id=f"ep_{i}",
                    session_id="test",
                    turn_number=i,
                    user_message="test",
                    user_message_normalized="test",
                    intent_primary=IntentCategory.GREETING,
                    construction_id="good_construction",
                    feedback_explicit=1.0,
                )
                for i in range(10)
            ] + [
                EpisodeLog(
                    id=f"ep_{i+10}",
                    session_id="test",
                    turn_number=i + 10,
                    user_message="test",
                    user_message_normalized="test",
                    intent_primary=IntentCategory.GREETING,
                    construction_id="bad_construction",
                    feedback_explicit=-1.0,
                )
                for i in range(10)
            ]

            # 2. Aggregate
            aggregator = FeedbackAggregator()
            stats = aggregator.aggregate(episodes)

            # 3. Store'a kaydet
            path = Path(tmpdir) / "stats.json"
            store = FeedbackStore(path)
            store.bulk_update(stats)

            # 4. Selector ile re-rank
            grammar = ConstructionGrammar()
            selector = ConstructionSelector(grammar, feedback_store=store)

            mock_good = MagicMock()
            mock_good.id = "good_construction"
            mock_bad = MagicMock()
            mock_bad.id = "bad_construction"

            # Başlangıçta bad_construction önde
            candidates = [
                ConstructionScore(construction=mock_bad, total_score=0.9),
                ConstructionScore(construction=mock_good, total_score=0.8),
            ]

            result = selector._apply_feedback_rerank(candidates)

            # Re-rank sonrası good_construction önde olmalı
            assert result[0].construction.id == "good_construction"
