"""
core/learning/feedback_scorer.py

Feedback skor hesaplama formülleri.

Bayesian Beta dağılımı kullanarak feedback mean hesaplar.
Cold start problemi için prior kullanır.
Açıklanabilir (explainable) skor hesaplama sağlar.

UEM v2 - Faz 5 Feedback-Driven Learning.
"""

from typing import Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .feedback_stats import ConstructionStats


# ============================================================================
# AĞIRLIK SABİTLERİ
# ============================================================================

# Explicit feedback ağırlıkları
WIN_EXPLICIT = 1.0   # /good
LOSS_EXPLICIT = 1.0  # /bad

# Implicit feedback ağırlıkları (daha zayıf ama negatif biraz daha ağır)
WIN_IMPLICIT = 0.3   # user_thanked, conversation_continued
LOSS_IMPLICIT = 0.5  # user_rephrased, user_complained, session_ended_abruptly

# Bayesian prior (cold start için - varsayılan nötr)
PRIOR_WINS = 1.0
PRIOR_LOSSES = 1.0

# Minimum sample threshold (tam etki için gereken kullanım sayısı)
MIN_SAMPLES_FOR_FULL_INFLUENCE = 10


# ============================================================================
# TEMEL HESAPLAMA FONKSİYONLARI
# ============================================================================

def compute_wins_losses(stats: "ConstructionStats") -> Tuple[float, float]:
    """
    Ağırlıklı win/loss hesapla.

    Explicit feedback daha güçlü, implicit daha zayıf.

    Args:
        stats: ConstructionStats instance

    Returns:
        (wins, losses) tuple
    """
    wins = (
        stats.explicit_pos * WIN_EXPLICIT +
        stats.implicit_pos * WIN_IMPLICIT
    )
    losses = (
        stats.explicit_neg * LOSS_EXPLICIT +
        stats.implicit_neg * LOSS_IMPLICIT
    )
    return wins, losses


def compute_feedback_mean(wins: float, losses: float) -> float:
    """
    Bayesian Beta ortalaması hesapla.

    Beta(α, β) dağılımının ortalaması: α / (α + β)
    Prior ekleyerek cold start'ı önler.

    Args:
        wins: Ağırlıklı pozitif feedback
        losses: Ağırlıklı negatif feedback

    Returns:
        float: 0.0 - 1.0 arası skor
            - 0.5 = nötr (hiç feedback yok veya eşit)
            - 1.0 = çok pozitif
            - 0.0 = çok negatif
    """
    alpha = wins + PRIOR_WINS
    beta = losses + PRIOR_LOSSES
    return alpha / (alpha + beta)


def compute_influence(total_uses: int) -> float:
    """
    Az veri varken feedback etkisini azalt.

    Smooth ramp-up: 0'dan MIN_SAMPLES_FOR_FULL_INFLUENCE'a kadar
    lineer artış, sonra 1.0'da sabit.

    Args:
        total_uses: Toplam kullanım sayısı

    Returns:
        float: 0.0 - 1.0 arası etki çarpanı
            - 0 kullanım = 0.0 (feedback etkisiz)
            - MIN_SAMPLES_FOR_FULL_INFLUENCE kullanım = 1.0 (tam etki)
    """
    if total_uses <= 0:
        return 0.0
    return min(1.0, total_uses / MIN_SAMPLES_FOR_FULL_INFLUENCE)


def compute_adjustment(stats: "ConstructionStats") -> float:
    """
    Base score için çarpan hesapla.

    Feedback mean'i adjustment çarpanına dönüştürür.
    Influence ile ağırlıklandırılır (az veri = az etki).

    Args:
        stats: ConstructionStats instance

    Returns:
        float: 0.5 - 1.5 arası çarpan
            - 1.0 = değişiklik yok (nötr veya az veri)
            - 1.5 = çok beğenilen (base_score * 1.5)
            - 0.5 = sevilmeyen (base_score * 0.5)
    """
    wins, losses = compute_wins_losses(stats)
    feedback_mean = compute_feedback_mean(wins, losses)
    influence = compute_influence(stats.total_uses)

    # feedback_mean: 0.0 → 0.5, 0.5 → 1.0, 1.0 → 1.5
    # (lineer dönüşüm: feedback_factor = 0.5 + feedback_mean)
    feedback_factor = 0.5 + feedback_mean

    # Influence ile karışım: adjustment = 1.0 + influence * (feedback_factor - 1.0)
    # influence=0: adjustment = 1.0 (değişiklik yok)
    # influence=1: adjustment = feedback_factor
    adjustment = 1.0 + influence * (feedback_factor - 1.0)

    return adjustment


# ============================================================================
# ANA SKOR FONKSİYONU
# ============================================================================

def compute_final_score(
    base_score: float,
    stats: "ConstructionStats"
) -> Tuple[float, Dict]:
    """
    Final skor hesapla ve açıklama metadata'sı döndür.

    Açıklanabilirlik için tüm ara hesapları metadata'da döndürür.

    Args:
        base_score: Selector'ın hesapladığı temel skor (0.0-1.0)
        stats: ConstructionStats instance

    Returns:
        (final_score, metadata_dict) tuple
            - final_score: base_score * adjustment
            - metadata: Hesaplama detayları
    """
    wins, losses = compute_wins_losses(stats)
    feedback_mean = compute_feedback_mean(wins, losses)
    influence = compute_influence(stats.total_uses)
    adjustment = compute_adjustment(stats)

    final_score = base_score * adjustment

    metadata = {
        "base_score": round(base_score, 4),
        "wins": round(wins, 2),
        "losses": round(losses, 2),
        "feedback_mean": round(feedback_mean, 4),
        "influence": round(influence, 4),
        "adjustment": round(adjustment, 4),
        "final_score": round(final_score, 4),
        "total_uses": stats.total_uses,
        "explicit_pos": stats.explicit_pos,
        "explicit_neg": stats.explicit_neg,
        "implicit_pos": stats.implicit_pos,
        "implicit_neg": stats.implicit_neg,
    }

    return final_score, metadata


# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def explain_score(
    base_score: float,
    stats: "ConstructionStats"
) -> str:
    """
    Skor hesaplamasını açıkla (debugging/logging için).

    Args:
        base_score: Temel skor
        stats: ConstructionStats

    Returns:
        str: İnsan okunabilir açıklama
    """
    final_score, metadata = compute_final_score(base_score, stats)

    lines = [
        f"Construction: {stats.construction_id}",
        f"  Base score: {metadata['base_score']}",
        f"  Feedback mean: {metadata['feedback_mean']} (prior + {metadata['wins']:.1f}W - {metadata['losses']:.1f}L)",
        f"  Influence: {metadata['influence']} (uses: {metadata['total_uses']})",
        f"  Adjustment: {metadata['adjustment']}",
        f"  Final score: {metadata['final_score']}",
    ]

    if metadata['explicit_pos'] > 0 or metadata['explicit_neg'] > 0:
        lines.append(f"  Explicit: +{metadata['explicit_pos']} / -{metadata['explicit_neg']}")

    if metadata['implicit_pos'] > 0 or metadata['implicit_neg'] > 0:
        lines.append(f"  Implicit: +{metadata['implicit_pos']} / -{metadata['implicit_neg']}")

    return "\n".join(lines)


def is_score_significant(stats: "ConstructionStats", threshold: float = 0.1) -> bool:
    """
    Feedback skoru anlamlı mı? (Nötrden yeterince farklı mı?)

    Args:
        stats: ConstructionStats
        threshold: Nötr'den (0.5) sapma eşiği

    Returns:
        bool: Feedback anlamlı ise True
    """
    wins, losses = compute_wins_losses(stats)
    feedback_mean = compute_feedback_mean(wins, losses)
    influence = compute_influence(stats.total_uses)

    # Hem feedback mean nötrden sapmalı, hem de yeterli veri olmalı
    deviation = abs(feedback_mean - 0.5)
    return deviation >= threshold and influence >= 0.3


def get_feedback_summary(stats: "ConstructionStats") -> Dict:
    """
    Kısa feedback özeti (UI için).

    Args:
        stats: ConstructionStats

    Returns:
        dict: Özet bilgiler
    """
    wins, losses = compute_wins_losses(stats)
    feedback_mean = compute_feedback_mean(wins, losses)

    # Sentiment kategorisi
    if feedback_mean >= 0.7:
        sentiment = "positive"
    elif feedback_mean <= 0.3:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "score": round(feedback_mean, 2),
        "uses": stats.total_uses,
        "has_feedback": stats.total_feedback > 0,
    }
