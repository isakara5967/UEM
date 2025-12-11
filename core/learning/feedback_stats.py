"""
core/learning/feedback_stats.py

ConstructionStats - Feedback istatistikleri için veri yapısı.

Her construction için feedback sayaçları ve cache'lenmiş skor tutar.
Aggregator tarafından episode'lardan hesaplanır, FeedbackStore tarafından saklanır.

UEM v2 - Faz 5 Feedback-Driven Learning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ConstructionStats:
    """
    Bir construction için feedback istatistikleri.

    Attributes:
        construction_id: Construction'ın benzersiz ID'si
        total_uses: Toplam kullanım sayısı
        explicit_pos: /good feedback sayısı
        explicit_neg: /bad feedback sayısı
        implicit_pos: Pozitif implicit sinyal sayısı (user_thanked, conversation_continued)
        implicit_neg: Negatif implicit sinyal sayısı (user_rephrased, user_complained, session_ended_abruptly)
        cached_score: Aggregator tarafından hesaplanan feedback mean (0.0-1.0)
        last_updated: Son güncelleme zamanı
    """

    construction_id: str

    # Kullanım sayısı
    total_uses: int = 0

    # Explicit feedback sayıları
    explicit_pos: int = 0  # /good
    explicit_neg: int = 0  # /bad

    # Implicit feedback sayıları
    implicit_pos: int = 0  # user_thanked, conversation_continued
    implicit_neg: int = 0  # user_rephrased, user_complained, session_ended_abruptly

    # Cache (aggregator tarafından hesaplanır)
    cached_score: float = 0.5
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        """
        JSON serialization için dictionary'e çevir.

        Returns:
            dict: Stats alanları
        """
        return {
            "construction_id": self.construction_id,
            "total_uses": self.total_uses,
            "explicit_pos": self.explicit_pos,
            "explicit_neg": self.explicit_neg,
            "implicit_pos": self.implicit_pos,
            "implicit_neg": self.implicit_neg,
            "cached_score": self.cached_score,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConstructionStats":
        """
        Dictionary'den ConstructionStats oluştur.

        Args:
            data: JSON'dan yüklenen dict

        Returns:
            ConstructionStats: Yeni stats instance
        """
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])

        return cls(
            construction_id=data["construction_id"],
            total_uses=data.get("total_uses", 0),
            explicit_pos=data.get("explicit_pos", 0),
            explicit_neg=data.get("explicit_neg", 0),
            implicit_pos=data.get("implicit_pos", 0),
            implicit_neg=data.get("implicit_neg", 0),
            cached_score=data.get("cached_score", 0.5),
            last_updated=last_updated,
        )

    @property
    def total_explicit(self) -> int:
        """Toplam explicit feedback sayısı."""
        return self.explicit_pos + self.explicit_neg

    @property
    def total_implicit(self) -> int:
        """Toplam implicit feedback sayısı."""
        return self.implicit_pos + self.implicit_neg

    @property
    def total_feedback(self) -> int:
        """Toplam feedback sayısı (explicit + implicit)."""
        return self.total_explicit + self.total_implicit

    @property
    def explicit_ratio(self) -> float:
        """
        Explicit feedback oranı (pozitif / toplam).

        Returns:
            float: 0.0-1.0 arası, feedback yoksa 0.5
        """
        if self.total_explicit == 0:
            return 0.5
        return self.explicit_pos / self.total_explicit

    @property
    def implicit_ratio(self) -> float:
        """
        Implicit feedback oranı (pozitif / toplam).

        Returns:
            float: 0.0-1.0 arası, feedback yoksa 0.5
        """
        if self.total_implicit == 0:
            return 0.5
        return self.implicit_pos / self.total_implicit

    def __repr__(self) -> str:
        return (
            f"ConstructionStats(id={self.construction_id!r}, "
            f"uses={self.total_uses}, "
            f"+exp={self.explicit_pos}, -exp={self.explicit_neg}, "
            f"+imp={self.implicit_pos}, -imp={self.implicit_neg}, "
            f"score={self.cached_score:.3f})"
        )
