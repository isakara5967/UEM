"""
core/learning/feedback_aggregator.py

FeedbackAggregator - Episode loglarından construction stats hesaplar.

Episode'lardaki explicit ve implicit feedback'leri toplar,
her construction için istatistikler oluşturur.

UEM v2 - Faz 5 Feedback-Driven Learning.
"""

import logging
from datetime import datetime
from typing import Dict, List

from .episode_types import EpisodeLog, ImplicitFeedback
from .feedback_stats import ConstructionStats
from .feedback_scorer import compute_feedback_mean, compute_wins_losses

logger = logging.getLogger(__name__)


class FeedbackAggregator:
    """
    Episode loglarından construction stats hesaplar.

    Episode'lardaki feedback verilerini aggregate ederek
    her construction için istatistikler oluşturur.

    Kullanım:
        aggregator = FeedbackAggregator()
        stats = aggregator.aggregate(episodes)

        for cid, stat in stats.items():
            print(f"{cid}: uses={stat.total_uses}, score={stat.cached_score}")
    """

    def aggregate(self, episodes: List[EpisodeLog]) -> Dict[str, ConstructionStats]:
        """
        Tüm episode'lardan stats üret.

        Args:
            episodes: EpisodeLog listesi

        Returns:
            {construction_id: ConstructionStats} sözlüğü
        """
        stats_by_id: Dict[str, ConstructionStats] = {}

        for episode in episodes:
            cid = episode.construction_id

            # Construction ID yoksa atla
            if not cid:
                logger.debug(f"Episode {episode.id} has no construction_id, skipping")
                continue

            # Stats al veya oluştur
            if cid not in stats_by_id:
                stats_by_id[cid] = ConstructionStats(construction_id=cid)

            stats = stats_by_id[cid]
            stats.total_uses += 1

            # Explicit feedback
            self._process_explicit_feedback(stats, episode)

            # Implicit feedback
            self._process_implicit_feedback(stats, episode)

        # Cached score'ları hesapla
        for stats in stats_by_id.values():
            self._update_cached_score(stats)

        logger.info(
            f"FeedbackAggregator: Processed {len(episodes)} episodes, "
            f"generated stats for {len(stats_by_id)} constructions"
        )

        return stats_by_id

    def _process_explicit_feedback(self, stats: ConstructionStats, episode: EpisodeLog) -> None:
        """
        Explicit feedback'i işle.

        Args:
            stats: Güncellenecek stats
            episode: Episode log
        """
        if episode.feedback_explicit is not None:
            if episode.feedback_explicit > 0:
                stats.explicit_pos += 1
            elif episode.feedback_explicit < 0:
                stats.explicit_neg += 1
            # 0 ise nötr, sayılmaz

    def _process_implicit_feedback(self, stats: ConstructionStats, episode: EpisodeLog) -> None:
        """
        Implicit feedback'i işle.

        Args:
            stats: Güncellenecek stats
            episode: Episode log
        """
        fb = episode.feedback_implicit

        if not fb:
            return

        # Pozitif sinyaller
        if fb.user_thanked:
            stats.implicit_pos += 1

        if fb.conversation_continued:
            stats.implicit_pos += 1

        # Negatif sinyaller
        if fb.user_rephrased:
            stats.implicit_neg += 1

        if fb.user_complained:
            stats.implicit_neg += 1

        if fb.session_ended_abruptly:
            stats.implicit_neg += 1

    def _update_cached_score(self, stats: ConstructionStats) -> None:
        """
        Cached score'u güncelle.

        Args:
            stats: Güncellenecek stats
        """
        wins, losses = compute_wins_losses(stats)
        stats.cached_score = compute_feedback_mean(wins, losses)
        stats.last_updated = datetime.now()

    def aggregate_incremental(
        self,
        existing_stats: Dict[str, ConstructionStats],
        new_episodes: List[EpisodeLog]
    ) -> Dict[str, ConstructionStats]:
        """
        Mevcut stats'a yeni episode'ları ekle (incremental aggregation).

        Args:
            existing_stats: Mevcut stats sözlüğü
            new_episodes: Yeni episode'lar

        Returns:
            Güncellenmiş stats sözlüğü
        """
        # Mevcut stats'ları kopyala
        stats_by_id = {cid: ConstructionStats.from_dict(s.to_dict())
                       for cid, s in existing_stats.items()}

        for episode in new_episodes:
            cid = episode.construction_id

            if not cid:
                continue

            # Stats al veya oluştur
            if cid not in stats_by_id:
                stats_by_id[cid] = ConstructionStats(construction_id=cid)

            stats = stats_by_id[cid]
            stats.total_uses += 1

            self._process_explicit_feedback(stats, episode)
            self._process_implicit_feedback(stats, episode)

        # Cached score'ları güncelle
        for stats in stats_by_id.values():
            self._update_cached_score(stats)

        return stats_by_id

    def get_summary(self, stats: Dict[str, ConstructionStats]) -> dict:
        """
        Stats özeti oluştur.

        Args:
            stats: Stats sözlüğü

        Returns:
            Özet dict
        """
        if not stats:
            return {
                "total_constructions": 0,
                "total_uses": 0,
                "total_explicit_feedback": 0,
                "total_implicit_feedback": 0,
            }

        total_uses = sum(s.total_uses for s in stats.values())
        total_explicit_pos = sum(s.explicit_pos for s in stats.values())
        total_explicit_neg = sum(s.explicit_neg for s in stats.values())
        total_implicit_pos = sum(s.implicit_pos for s in stats.values())
        total_implicit_neg = sum(s.implicit_neg for s in stats.values())

        return {
            "total_constructions": len(stats),
            "total_uses": total_uses,
            "total_explicit_feedback": total_explicit_pos + total_explicit_neg,
            "explicit_positive": total_explicit_pos,
            "explicit_negative": total_explicit_neg,
            "total_implicit_feedback": total_implicit_pos + total_implicit_neg,
            "implicit_positive": total_implicit_pos,
            "implicit_negative": total_implicit_neg,
            "average_score": sum(s.cached_score for s in stats.values()) / len(stats) if stats else 0.5,
        }
