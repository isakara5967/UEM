"""
core/learning/pattern_analyzer.py

Faz 5 Pattern Analyzer - Episode verilerinden offline pattern analizi.

PatternAnalyzer, JSONL episode verilerinden istatistik ve korelasyonları
hesaplar. Otomatik değişiklik yapmaz, sadece rapor üretir.

Analizler:
- Intent frekansı
- Dialogue act frekansı
- Construction kullanımı
- Feedback korelasyonu (intent/act/construction başına)
- Fallback oranları
- Öneriler

UEM v2 - Faz 5 Pattern Evolution Analytics.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct
from .episode_store import EpisodeStore, JSONLEpisodeStore
from .episode_types import EpisodeLog


class PatternAnalyzer:
    """
    Episode verilerinden pattern analizi yapar.

    Sadece okuma yapar, hiçbir değişiklik yapmaz.
    Markdown formatında rapor üretir.

    Attributes:
        store: Episode verilerini sağlayan store
    """

    # Fallback response pattern'leri
    FALLBACK_RESPONSES = [
        "Anlıyorum.",
        "Anlıyorum",
        "Hmm, anlıyorum.",
        "Anladım.",
    ]

    def __init__(self, store: EpisodeStore):
        """
        Initialize PatternAnalyzer.

        Args:
            store: EpisodeStore instance (genelde JSONLEpisodeStore)
        """
        self.store = store
        self._episodes: Optional[List[EpisodeLog]] = None

    def _load_episodes(self) -> List[EpisodeLog]:
        """Episode'ları yükle (lazy loading)."""
        if self._episodes is None:
            self._episodes = self.store.get_all()
        return self._episodes

    def analyze_intent_frequency(self) -> Dict[str, int]:
        """
        Hangi intent kaç kez görüldü?

        Returns:
            Dict[str, int]: Intent adı -> görülme sayısı
        """
        episodes = self._load_episodes()
        frequency: Dict[str, int] = defaultdict(int)

        for episode in episodes:
            if episode.intent_primary:
                intent_name = episode.intent_primary.value
                frequency[intent_name] += 1

        # Sıralı dict olarak döndür (en sık görülenden az görülene)
        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))

    def analyze_act_frequency(self) -> Dict[str, int]:
        """
        Hangi dialogue act kaç kez seçildi?

        Returns:
            Dict[str, int]: Act adı -> seçilme sayısı
        """
        episodes = self._load_episodes()
        frequency: Dict[str, int] = defaultdict(int)

        for episode in episodes:
            if episode.dialogue_act_selected:
                act_name = episode.dialogue_act_selected.value
                frequency[act_name] += 1

        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))

    def analyze_construction_usage(self) -> Dict[str, int]:
        """
        Hangi construction kaç kez kullanıldı?

        Returns:
            Dict[str, int]: Construction ID/category -> kullanım sayısı
        """
        episodes = self._load_episodes()
        frequency: Dict[str, int] = defaultdict(int)

        for episode in episodes:
            # Construction category kullan (daha anlamlı)
            category = episode.construction_category or episode.construction_id
            if category:
                frequency[category] += 1

        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))

    def analyze_feedback_correlation(self) -> Dict[str, Dict[str, float]]:
        """
        Intent/Act/Construction başına ortalama feedback.

        Returns:
            Dict[str, Dict[str, float]]: Kategori adı -> {avg_feedback, count, positive_rate}

        Örnek:
            {
                "greeting": {"avg_feedback": 0.8, "count": 10, "positive_rate": 0.9},
                "unknown": {"avg_feedback": -0.3, "count": 5, "positive_rate": 0.2}
            }
        """
        episodes = self._load_episodes()

        # Intent bazlı feedback toplama
        intent_feedback: Dict[str, List[float]] = defaultdict(list)

        for episode in episodes:
            if episode.feedback_explicit is not None and episode.intent_primary:
                intent_name = episode.intent_primary.value
                intent_feedback[intent_name].append(episode.feedback_explicit)

        # İstatistikleri hesapla
        result: Dict[str, Dict[str, float]] = {}

        for intent_name, feedbacks in intent_feedback.items():
            if feedbacks:
                avg = sum(feedbacks) / len(feedbacks)
                positive_count = sum(1 for f in feedbacks if f > 0)
                positive_rate = positive_count / len(feedbacks)

                result[intent_name] = {
                    "avg_feedback": round(avg, 2),
                    "count": len(feedbacks),
                    "positive_rate": round(positive_rate, 2),
                }

        # Ortalama feedback'e göre sırala (en iyi performanstan en kötüye)
        return dict(sorted(result.items(), key=lambda x: x[1]["avg_feedback"], reverse=True))

    def analyze_act_feedback_correlation(self) -> Dict[str, Dict[str, float]]:
        """
        Dialogue act başına ortalama feedback.

        Returns:
            Dict[str, Dict[str, float]]: Act adı -> {avg_feedback, count, positive_rate}
        """
        episodes = self._load_episodes()

        act_feedback: Dict[str, List[float]] = defaultdict(list)

        for episode in episodes:
            if episode.feedback_explicit is not None and episode.dialogue_act_selected:
                act_name = episode.dialogue_act_selected.value
                act_feedback[act_name].append(episode.feedback_explicit)

        result: Dict[str, Dict[str, float]] = {}

        for act_name, feedbacks in act_feedback.items():
            if feedbacks:
                avg = sum(feedbacks) / len(feedbacks)
                positive_count = sum(1 for f in feedbacks if f > 0)
                positive_rate = positive_count / len(feedbacks)

                result[act_name] = {
                    "avg_feedback": round(avg, 2),
                    "count": len(feedbacks),
                    "positive_rate": round(positive_rate, 2),
                }

        return dict(sorted(result.items(), key=lambda x: x[1]["avg_feedback"], reverse=True))

    def analyze_fallback_rate(self) -> Dict[str, float]:
        """
        Fallback oranlarını hesapla.

        Returns:
            Dict[str, float]: Fallback türü -> oran

        Örnek:
            {
                "unknown_intent_rate": 0.15,
                "fallback_response_rate": 0.08,
                "total_episodes": 100
            }
        """
        episodes = self._load_episodes()
        total = len(episodes)

        if total == 0:
            return {
                "unknown_intent_rate": 0.0,
                "fallback_response_rate": 0.0,
                "unknown_count": 0,
                "fallback_response_count": 0,
                "total_episodes": 0,
            }

        # Unknown intent sayısı
        unknown_count = sum(
            1 for ep in episodes
            if ep.intent_primary == IntentCategory.UNKNOWN
        )

        # Fallback response sayısı
        fallback_response_count = sum(
            1 for ep in episodes
            if ep.response_text.strip() in self.FALLBACK_RESPONSES
        )

        return {
            "unknown_intent_rate": round(unknown_count / total, 2),
            "fallback_response_rate": round(fallback_response_count / total, 2),
            "unknown_count": unknown_count,
            "fallback_response_count": fallback_response_count,
            "total_episodes": total,
        }

    def analyze_session_stats(self) -> Dict[str, any]:
        """
        Session bazlı istatistikler.

        Returns:
            Dict: Session istatistikleri
        """
        episodes = self._load_episodes()

        if not episodes:
            return {
                "total_sessions": 0,
                "total_episodes": 0,
                "avg_turns_per_session": 0.0,
                "min_turns": 0,
                "max_turns": 0,
            }

        # Session'ları topla
        sessions: Dict[str, List[EpisodeLog]] = defaultdict(list)
        for episode in episodes:
            sessions[episode.session_id].append(episode)

        # Turn sayıları
        turn_counts = [len(eps) for eps in sessions.values()]
        avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0.0

        return {
            "total_sessions": len(sessions),
            "total_episodes": len(episodes),
            "avg_turns_per_session": round(avg_turns, 1),
            "min_turns": min(turn_counts) if turn_counts else 0,
            "max_turns": max(turn_counts) if turn_counts else 0,
        }

    def analyze_feedback_summary(self) -> Dict[str, any]:
        """
        Feedback özet istatistikleri.

        Returns:
            Dict: Feedback özeti
        """
        episodes = self._load_episodes()

        total = len(episodes)
        with_feedback = [ep for ep in episodes if ep.feedback_explicit is not None]

        if not with_feedback:
            return {
                "total_episodes": total,
                "episodes_with_feedback": 0,
                "feedback_coverage": 0.0,
                "avg_feedback": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            }

        feedbacks = [ep.feedback_explicit for ep in with_feedback]
        positive = sum(1 for f in feedbacks if f > 0)
        negative = sum(1 for f in feedbacks if f < 0)
        neutral = sum(1 for f in feedbacks if f == 0)

        return {
            "total_episodes": total,
            "episodes_with_feedback": len(with_feedback),
            "feedback_coverage": round(len(with_feedback) / total, 2) if total > 0 else 0.0,
            "avg_feedback": round(sum(feedbacks) / len(feedbacks), 2),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
        }

    def generate_recommendations(self) -> List[str]:
        """
        Analizlere dayanarak öneriler üret.

        Returns:
            List[str]: Öneri listesi
        """
        recommendations = []

        # Fallback analizi
        fallback = self.analyze_fallback_rate()
        if fallback["unknown_intent_rate"] > 0.1:
            unknown_pct = int(fallback["unknown_intent_rate"] * 100)
            recommendations.append(
                f"'unknown' intent oranı yüksek ({unknown_pct}%) - intent pattern'leri genişletilmeli"
            )

        if fallback["fallback_response_rate"] > 0.05:
            fallback_pct = int(fallback["fallback_response_rate"] * 100)
            recommendations.append(
                f"Fallback response oranı yüksek ({fallback_pct}%) - construction coverage artırılmalı"
            )

        # Feedback korelasyonu analizi
        feedback_corr = self.analyze_feedback_correlation()
        for intent_name, stats in feedback_corr.items():
            if stats["count"] >= 2 and stats["avg_feedback"] < -0.2:
                recommendations.append(
                    f"'{intent_name}' intent için negatif feedback ({stats['avg_feedback']:.2f}) - "
                    f"bu intent'in tanınması veya yanıtı iyileştirilmeli"
                )

        # Düşük kullanımlı intent'ler
        intent_freq = self.analyze_intent_frequency()
        total_intents = sum(intent_freq.values())
        if total_intents > 10:
            for intent_name, count in intent_freq.items():
                coverage = count / total_intents
                if coverage < 0.02 and intent_name != "unknown":
                    recommendations.append(
                        f"'{intent_name}' intent düşük coverage ({count} kez, %{int(coverage*100)}) - "
                        f"daha fazla pattern eklenebilir"
                    )

        # Feedback coverage
        feedback_summary = self.analyze_feedback_summary()
        if feedback_summary["feedback_coverage"] < 0.1 and feedback_summary["total_episodes"] > 20:
            recommendations.append(
                "Feedback coverage düşük - kullanıcılardan daha fazla feedback toplanmalı"
            )

        if not recommendations:
            recommendations.append("Şu an için özel bir öneri yok. Daha fazla veri toplanmalı.")

        return recommendations

    def generate_report(self) -> str:
        """
        Tüm analizleri markdown formatında döndür.

        Returns:
            str: Markdown formatında rapor
        """
        lines = []

        # Header
        lines.append("# Episode Analysis Report")
        lines.append("")
        lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        lines.append("")

        # Session Stats
        session_stats = self.analyze_session_stats()
        lines.append("## Overview")
        lines.append("")
        lines.append(f"- **Total Episodes:** {session_stats['total_episodes']}")
        lines.append(f"- **Total Sessions:** {session_stats['total_sessions']}")
        lines.append(f"- **Avg Turns/Session:** {session_stats['avg_turns_per_session']}")
        lines.append("")

        # Intent Frequency
        intent_freq = self.analyze_intent_frequency()
        total_intents = sum(intent_freq.values())

        lines.append("## Intent Frequency")
        lines.append("")
        if intent_freq:
            lines.append("| Intent | Count | % |")
            lines.append("|--------|-------|---|")
            for intent_name, count in intent_freq.items():
                pct = int((count / total_intents * 100)) if total_intents > 0 else 0
                lines.append(f"| {intent_name} | {count} | {pct}% |")
        else:
            lines.append("_No intent data available._")
        lines.append("")

        # Dialogue Act Frequency
        act_freq = self.analyze_act_frequency()
        total_acts = sum(act_freq.values())

        lines.append("## Dialogue Act Frequency")
        lines.append("")
        if act_freq:
            lines.append("| Act | Count | % |")
            lines.append("|-----|-------|---|")
            for act_name, count in act_freq.items():
                pct = int((count / total_acts * 100)) if total_acts > 0 else 0
                lines.append(f"| {act_name} | {count} | {pct}% |")
        else:
            lines.append("_No dialogue act data available._")
        lines.append("")

        # Construction Usage
        construction_usage = self.analyze_construction_usage()
        total_constructions = sum(construction_usage.values())

        lines.append("## Construction Usage")
        lines.append("")
        if construction_usage:
            lines.append("| Construction | Count | % |")
            lines.append("|--------------|-------|---|")
            for const_name, count in list(construction_usage.items())[:15]:  # Top 15
                pct = int((count / total_constructions * 100)) if total_constructions > 0 else 0
                lines.append(f"| {const_name} | {count} | {pct}% |")
            if len(construction_usage) > 15:
                lines.append(f"| _... and {len(construction_usage) - 15} more_ | | |")
        else:
            lines.append("_No construction data available._")
        lines.append("")

        # Feedback Summary
        feedback_summary = self.analyze_feedback_summary()
        lines.append("## Feedback Summary")
        lines.append("")
        lines.append(f"- **Episodes with Feedback:** {feedback_summary['episodes_with_feedback']} "
                    f"({int(feedback_summary['feedback_coverage'] * 100)}% coverage)")
        lines.append(f"- **Average Feedback Score:** {feedback_summary['avg_feedback']}")
        lines.append(f"- **Positive:** {feedback_summary['positive_count']}")
        lines.append(f"- **Negative:** {feedback_summary['negative_count']}")
        lines.append(f"- **Neutral:** {feedback_summary['neutral_count']}")
        lines.append("")

        # Feedback Correlation by Intent
        feedback_corr = self.analyze_feedback_correlation()
        lines.append("## Feedback Correlation (by Intent)")
        lines.append("")
        if feedback_corr:
            lines.append("| Intent | Avg Feedback | Sample Size | Positive Rate |")
            lines.append("|--------|--------------|-------------|---------------|")
            for intent_name, stats in feedback_corr.items():
                lines.append(
                    f"| {intent_name} | {stats['avg_feedback']} | {stats['count']} | "
                    f"{int(stats['positive_rate'] * 100)}% |"
                )
        else:
            lines.append("_No feedback correlation data available._")
        lines.append("")

        # Feedback Correlation by Act
        act_corr = self.analyze_act_feedback_correlation()
        lines.append("## Feedback Correlation (by Dialogue Act)")
        lines.append("")
        if act_corr:
            lines.append("| Act | Avg Feedback | Sample Size | Positive Rate |")
            lines.append("|-----|--------------|-------------|---------------|")
            for act_name, stats in act_corr.items():
                lines.append(
                    f"| {act_name} | {stats['avg_feedback']} | {stats['count']} | "
                    f"{int(stats['positive_rate'] * 100)}% |"
                )
        else:
            lines.append("_No feedback correlation data available for dialogue acts._")
        lines.append("")

        # Fallback Rate
        fallback = self.analyze_fallback_rate()
        lines.append("## Fallback Rate")
        lines.append("")
        lines.append(f"- **Unknown Intent:** {int(fallback['unknown_intent_rate'] * 100)}% "
                    f"({fallback['unknown_count']} episodes)")
        lines.append(f"- **Fallback Response:** {int(fallback['fallback_response_rate'] * 100)}% "
                    f"({fallback['fallback_response_count']} episodes)")
        lines.append("")

        # Recommendations
        recommendations = self.generate_recommendations()
        lines.append("## Recommendations")
        lines.append("")
        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("_Report generated by UEM Pattern Analyzer_")

        return "\n".join(lines)


def create_analyzer(filepath: str = "data/episodes.jsonl") -> PatternAnalyzer:
    """
    Helper function to create a PatternAnalyzer.

    Args:
        filepath: JSONL dosya yolu

    Returns:
        PatternAnalyzer: Hazır analyzer instance
    """
    store = JSONLEpisodeStore(filepath)
    return PatternAnalyzer(store)
