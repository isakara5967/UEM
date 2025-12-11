"""
core/learning/feedback_store.py

FeedbackStore - Construction feedback istatistiklerinin JSON persistence'ı.

ConstructionStats'ları JSON dosyasında saklar ve yükler.
Selector tarafından re-ranking için okunur.

UEM v2 - Faz 5 Feedback-Driven Learning.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .feedback_stats import ConstructionStats

logger = logging.getLogger(__name__)


class FeedbackStore:
    """
    Construction feedback istatistiklerini JSON'da saklar.

    Attributes:
        path: JSON dosya yolu
        _stats: Memory cache {construction_id: ConstructionStats}

    Kullanım:
        store = FeedbackStore()
        stats = store.get_stats("greet_basic_01")
        if stats:
            print(f"Uses: {stats.total_uses}")

        # Güncelleme
        new_stats = ConstructionStats(construction_id="greet_basic_01", ...)
        store.update_stats(new_stats)
    """

    DEFAULT_PATH = Path("data/construction_stats.json")

    def __init__(self, path: Optional[Path] = None):
        """
        FeedbackStore oluştur.

        Args:
            path: JSON dosya yolu (default: data/construction_stats.json)
        """
        self.path = path or self.DEFAULT_PATH
        self._stats: Dict[str, ConstructionStats] = {}
        self._load()

    def _ensure_directory_exists(self) -> None:
        """Dizin yoksa oluştur."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """JSON dosyasından yükle."""
        if not self.path.exists():
            logger.debug(f"FeedbackStore: No existing file at {self.path}")
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Data yapısı: {"stats": {construction_id: {...}, ...}, "metadata": {...}}
            stats_data = data.get("stats", {})
            for cid, stat_dict in stats_data.items():
                self._stats[cid] = ConstructionStats.from_dict(stat_dict)

            logger.info(f"FeedbackStore: Loaded {len(self._stats)} construction stats from {self.path}")

        except json.JSONDecodeError as e:
            logger.warning(f"FeedbackStore: JSON parse error in {self.path}: {e}")
        except Exception as e:
            logger.warning(f"FeedbackStore: Error loading {self.path}: {e}")

    def _save(self) -> None:
        """JSON dosyasına kaydet."""
        self._ensure_directory_exists()

        data = {
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "count": len(self._stats),
            },
            "stats": {cid: stats.to_dict() for cid, stats in self._stats.items()},
        }

        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"FeedbackStore: Saved {len(self._stats)} stats to {self.path}")

        except Exception as e:
            logger.error(f"FeedbackStore: Error saving to {self.path}: {e}")
            raise

    def get_stats(self, construction_id: str) -> Optional[ConstructionStats]:
        """
        Belirli construction için stats döndür.

        Args:
            construction_id: Construction ID

        Returns:
            ConstructionStats veya None (yoksa)
        """
        return self._stats.get(construction_id)

    def update_stats(self, stats: ConstructionStats) -> None:
        """
        Tek stats güncelle ve kaydet.

        Args:
            stats: Güncellenecek ConstructionStats
        """
        self._stats[stats.construction_id] = stats
        self._save()

    def bulk_update(self, stats_dict: Dict[str, ConstructionStats]) -> None:
        """
        Toplu güncelleme (aggregator için).

        Mevcut stats'ları günceller veya yeni ekler, sonra kaydeder.

        Args:
            stats_dict: {construction_id: ConstructionStats} sözlüğü
        """
        self._stats.update(stats_dict)
        self._save()
        logger.info(f"FeedbackStore: Bulk updated {len(stats_dict)} construction stats")

    def get_all(self) -> Dict[str, ConstructionStats]:
        """
        Tüm stats'ları döndür.

        Returns:
            {construction_id: ConstructionStats} sözlüğünün kopyası
        """
        return self._stats.copy()

    def clear(self) -> None:
        """Tüm stats'ları sil (testing için)."""
        self._stats.clear()
        self._save()
        logger.info("FeedbackStore: Cleared all stats")

    def count(self) -> int:
        """Stats sayısı."""
        return len(self._stats)

    def get_top_constructions(self, n: int = 10) -> list:
        """
        En yüksek skorlu construction'ları getir.

        Args:
            n: Kaç tane döndürülecek

        Returns:
            [(construction_id, stats), ...] listesi (cached_score'a göre sıralı)
        """
        sorted_stats = sorted(
            self._stats.items(),
            key=lambda x: x[1].cached_score,
            reverse=True
        )
        return sorted_stats[:n]

    def get_most_used(self, n: int = 10) -> list:
        """
        En çok kullanılan construction'ları getir.

        Args:
            n: Kaç tane döndürülecek

        Returns:
            [(construction_id, stats), ...] listesi (total_uses'a göre sıralı)
        """
        sorted_stats = sorted(
            self._stats.items(),
            key=lambda x: x[1].total_uses,
            reverse=True
        )
        return sorted_stats[:n]

    def __len__(self) -> int:
        return len(self._stats)

    def __contains__(self, construction_id: str) -> bool:
        return construction_id in self._stats

    def __repr__(self) -> str:
        return f"FeedbackStore(path={self.path!r}, count={len(self._stats)})"
