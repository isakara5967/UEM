"""
UEM v2 - Global Workspace Integration

Global Workspace Theory (Baars) implementasyonu.
Tum modullerden gelen bilgiyi entegre eder ve yayinlar.

Workspace = Bilincin "sahnesi"
- Yarisma: Moduller sahneye cikmak icin yarisir
- Entegrasyon: Kazanan icerik diger bilgilerle birlesiir
- Yayin (Broadcast): Entegre bilgi tum modullere yayinlanir
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
import uuid

from .types import (
    WorkspaceContent,
    GlobalWorkspaceState,
    BroadcastType,
    AttentionPriority,
    IntegrationStatus,
    ConsciousnessLevel,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class GlobalWorkspaceConfig:
    """Global Workspace yapilandirmasi."""
    # Kapasite
    max_active_contents: int = 10         # Workspace'te max icerik
    max_broadcast_queue: int = 5          # Yayin kuyrugunun boyutu
    max_history: int = 100                # Yayin gecmisi

    # Yarisma parametreleri
    competition_threshold: float = 0.5    # Bu skorun ustu yarisabilir
    winner_boost: float = 0.2             # Kazanana bonus

    # Entegrasyon parametreleri
    integration_threshold: float = 0.6    # Entegrasyon icin min skor
    coherence_weight: float = 0.3         # Tutarlilik agirligi
    relevance_weight: float = 0.4         # Alakalilik agirligi
    novelty_weight: float = 0.3           # Yenilik agirligi

    # Yayin parametreleri
    broadcast_interval_ms: float = 500.0  # Yayinlar arasi min sure
    broadcast_decay: float = 0.1          # Her yayindan sonra azalma

    # Temizlik
    cleanup_interval: int = 10            # Her N cycle'da temizlik
    content_ttl_ms: float = 10000.0       # Icerik yasam suresi

    # Ozellikler
    enable_conflict_detection: bool = True
    track_broadcasts: bool = True


# ============================================================================
# BROADCAST LISTENER
# ============================================================================

@dataclass
class BroadcastListener:
    """
    Yayin dinleyicisi.

    Moduller bu interface ile workspace yayinlarini dinler.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    module_name: str = ""
    content_types: List[BroadcastType] = field(default_factory=list)  # Ilgilendigi turler
    callback: Optional[Callable[[WorkspaceContent], None]] = None
    priority: int = 0  # Yayin sirasi

    def accepts(self, content_type: BroadcastType) -> bool:
        """Bu turu kabul ediyor mu?"""
        if not self.content_types:
            return True  # Tum turler
        return content_type in self.content_types


# ============================================================================
# GLOBAL WORKSPACE
# ============================================================================

class GlobalWorkspace:
    """
    Global Workspace - Bilinc entegrasyon merkezi.

    Baars'in Global Workspace Theory'sine gore:
    1. Yarisma: Moduller icerikleri gonderir
    2. Secim: En alakali/acil icerik secilir
    3. Entegrasyon: Secilen icerik diger bilgilerle birlesiir
    4. Yayin: Entegre icerik tum modullere yayinlanir

    Bu yayinla "bilinc" ortaya cikar.
    """

    def __init__(self, config: Optional[GlobalWorkspaceConfig] = None):
        """
        GlobalWorkspace baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or GlobalWorkspaceConfig()

        # Workspace durumu
        self.state = GlobalWorkspaceState()

        # Dinleyiciler
        self._listeners: Dict[str, BroadcastListener] = {}

        # Son yayin zamani
        self._last_broadcast_time: Optional[datetime] = None

        # Cycle sayaci
        self._cycle_count = 0

        # Istatistikler
        self._stats = {
            "contents_submitted": 0,
            "contents_integrated": 0,
            "broadcasts_sent": 0,
            "conflicts_detected": 0,
            "contents_expired": 0,
        }

    # ========================================================================
    # CONTENT SUBMISSION
    # ========================================================================

    def submit_content(
        self,
        content_type: BroadcastType,
        source_module: str,
        payload: Dict[str, Any],
        summary: str = "",
        priority: AttentionPriority = AttentionPriority.NORMAL,
        relevance: float = 0.5,
        urgency: float = 0.3,
        novelty: float = 0.5,
        ttl_ms: Optional[float] = None,
    ) -> WorkspaceContent:
        """
        Workspace'e icerik gonder.

        Args:
            content_type: Icerik turu
            source_module: Kaynak modul
            payload: Icerik verisi
            summary: Kisa ozet
            priority: Oncelik
            relevance: Alakalilik (0-1)
            urgency: Aciliyet (0-1)
            novelty: Yenilik (0-1)
            ttl_ms: Yasam suresi

        Returns:
            Olusturulan icerik
        """
        content = WorkspaceContent(
            content_type=content_type,
            source_module=source_module,
            payload=payload,
            summary=summary,
            priority=priority,
            relevance=relevance,
            urgency=urgency,
            novelty=novelty,
            ttl_ms=ttl_ms or self.config.content_ttl_ms,
        )

        # Kapasite kontrolu
        if len(self.state.active_contents) >= self.config.max_active_contents:
            # En dusuk skorlu icerigi kaldir
            self._remove_lowest_content()

        self.state.add_content(content)
        self._stats["contents_submitted"] += 1

        # Catisma kontrolu
        if self.config.enable_conflict_detection:
            self._detect_conflicts(content)

        return content

    def _remove_lowest_content(self) -> Optional[str]:
        """En dusuk skorlu icerigi kaldir."""
        if not self.state.active_contents:
            return None

        lowest = min(
            self.state.active_contents.values(),
            key=lambda c: c.competition_score,
        )
        self.state.remove_content(lowest.id)
        return lowest.id

    # ========================================================================
    # COMPETITION
    # ========================================================================

    def run_competition(self) -> Optional[WorkspaceContent]:
        """
        Yarisma calistir - en yuksek skorlu icerik kazanir.

        Returns:
            Kazanan icerik veya None
        """
        # Henuz entegre olmamis icerikleri al
        candidates = [
            c for c in self.state.active_contents.values()
            if c.status == IntegrationStatus.PENDING
            and c.competition_score >= self.config.competition_threshold
        ]

        if not candidates:
            return None

        # En yuksek skorlu icerik
        winner = max(candidates, key=lambda c: c.competition_score)

        # Kazanana bonus
        winner.relevance = min(1.0, winner.relevance + self.config.winner_boost)

        return winner

    def get_top_competitors(self, n: int = 5) -> List[WorkspaceContent]:
        """En yuksek skorlu adaylari getir."""
        return self.state.get_top_contents(n)

    # ========================================================================
    # INTEGRATION
    # ========================================================================

    def integrate_content(self, content_id: str) -> bool:
        """
        Icerigi entegre et.

        Args:
            content_id: Icerik ID

        Returns:
            Basarili mi
        """
        content = self.state.get_content(content_id)
        if not content:
            return False

        if content.status != IntegrationStatus.PENDING:
            return False

        # Entegrasyon skoru hesapla
        integration_score = self._calculate_integration_score(content)

        if integration_score < self.config.integration_threshold:
            return False

        # Entegre olarak isaretle
        content.status = IntegrationStatus.PROCESSING
        content.integration_score = integration_score

        # Ilgili icerikleri bul ve bagla
        self._link_related_contents(content)

        content.mark_integrated(integration_score)
        self._stats["contents_integrated"] += 1

        # Yayin kuyuguna ekle
        if content.id not in self.state.broadcast_queue:
            self.state.broadcast_queue.append(content.id)
            if len(self.state.broadcast_queue) > self.config.max_broadcast_queue:
                self.state.broadcast_queue.pop(0)

        self.state.integration_count += 1

        return True

    def _calculate_integration_score(self, content: WorkspaceContent) -> float:
        """
        Entegrasyon skoru hesapla.

        Skor = coherence * w1 + relevance * w2 + novelty * w3
        """
        # Tutarlilik - diger iceriklerle uyum
        coherence = self._calculate_coherence(content)

        score = (
            coherence * self.config.coherence_weight +
            content.relevance * self.config.relevance_weight +
            content.novelty * self.config.novelty_weight
        )

        return score

    def _calculate_coherence(self, content: WorkspaceContent) -> float:
        """
        Tutarlilik hesapla - diger iceriklerle uyum.

        Args:
            content: Icerik

        Returns:
            Tutarlilik skoru (0-1)
        """
        if not self.state.active_contents:
            return 0.5

        # Catisma kontrolu
        conflict_count = len(content.conflicts_with)
        if conflict_count > 0:
            # Her catisma tutarliligi azaltir
            return max(0.0, 1.0 - conflict_count * 0.2)

        # Ilgili icerik kontrolu
        related_count = len(content.related_contents)
        if related_count > 0:
            # Ilgili icerikler tutarliligi arttirir
            return min(1.0, 0.5 + related_count * 0.1)

        return 0.5

    def _link_related_contents(self, content: WorkspaceContent) -> None:
        """Ilgili icerikleri bagla."""
        for other_id, other in self.state.active_contents.items():
            if other_id == content.id:
                continue

            # Ayni modulden veya iliskili turden
            if other.source_module == content.source_module:
                if other_id not in content.related_contents:
                    content.related_contents.append(other_id)

    # ========================================================================
    # BROADCAST
    # ========================================================================

    def broadcast(self, content_id: Optional[str] = None) -> bool:
        """
        Entegre icerigi tum modullere yayin yap.

        Args:
            content_id: Yayinlanacak icerik (None = kuyruktan al)

        Returns:
            Basarili mi
        """
        # Yayin araligi kontrolu
        if self._last_broadcast_time:
            elapsed = (datetime.now() - self._last_broadcast_time).total_seconds() * 1000
            if elapsed < self.config.broadcast_interval_ms:
                return False

        # Icerik secimi
        if content_id:
            content = self.state.get_content(content_id)
        elif self.state.broadcast_queue:
            content_id = self.state.broadcast_queue.pop(0)
            content = self.state.get_content(content_id)
        else:
            return False

        if not content:
            return False

        if content.status not in (IntegrationStatus.INTEGRATED, IntegrationStatus.PROCESSING):
            return False

        # Yayini yap
        content.mark_broadcast()
        self._last_broadcast_time = datetime.now()
        self._stats["broadcasts_sent"] += 1
        self.state.broadcast_count += 1

        # Dinleyicilere bildir
        self._notify_listeners(content)

        # Gecmise ekle
        if self.config.track_broadcasts:
            self.state.broadcast_history.append(content.id)
            if len(self.state.broadcast_history) > self.config.max_history:
                self.state.broadcast_history.pop(0)

        # Yayin sonrasi decay
        content.relevance = max(0.0, content.relevance - self.config.broadcast_decay)

        self.state.last_broadcast = datetime.now()

        return True

    def broadcast_all_pending(self) -> int:
        """Tum bekleyen yayinlari yap."""
        count = 0
        while self.state.broadcast_queue and self.broadcast():
            count += 1
        return count

    # ========================================================================
    # LISTENERS
    # ========================================================================

    def register_listener(
        self,
        module_name: str,
        callback: Callable[[WorkspaceContent], None],
        content_types: Optional[List[BroadcastType]] = None,
        priority: int = 0,
    ) -> str:
        """
        Yayin dinleyicisi kaydet.

        Args:
            module_name: Modul adi
            callback: Geri cagri fonksiyonu
            content_types: Ilgilenilen turler (None = hepsi)
            priority: Yayin sirasi

        Returns:
            Listener ID
        """
        listener = BroadcastListener(
            module_name=module_name,
            callback=callback,
            content_types=content_types or [],
            priority=priority,
        )
        self._listeners[listener.id] = listener
        return listener.id

    def unregister_listener(self, listener_id: str) -> bool:
        """Dinleyiciyi kaldir."""
        if listener_id in self._listeners:
            del self._listeners[listener_id]
            return True
        return False

    def _notify_listeners(self, content: WorkspaceContent) -> int:
        """
        Dinleyicileri bilgilendir.

        Args:
            content: Yayinlanan icerik

        Returns:
            Bildirilen dinleyici sayisi
        """
        notified = 0
        # Oncelik sirasina gore sirala
        sorted_listeners = sorted(
            self._listeners.values(),
            key=lambda l: l.priority,
            reverse=True,
        )

        for listener in sorted_listeners:
            if listener.accepts(content.content_type) and listener.callback:
                try:
                    listener.callback(content)
                    notified += 1
                except Exception:
                    pass  # Hata olsa bile devam et

        return notified

    # ========================================================================
    # CONFLICT DETECTION
    # ========================================================================

    def _detect_conflicts(self, new_content: WorkspaceContent) -> List[str]:
        """
        Catisma tespit et.

        Args:
            new_content: Yeni icerik

        Returns:
            Catisma olan icerik ID'leri
        """
        conflicts = []

        for other_id, other in self.state.active_contents.items():
            if other_id == new_content.id:
                continue

            # Ayni turde, farkli kaynak, zit bilgi
            if other.content_type == new_content.content_type:
                if other.source_module != new_content.source_module:
                    # Basit catisma dedektoru - gercek uygulamada daha sofistike olur
                    if self._is_conflicting_payload(new_content.payload, other.payload):
                        conflicts.append(other_id)
                        new_content.conflicts_with.append(other_id)
                        other.conflicts_with.append(new_content.id)
                        self._stats["conflicts_detected"] += 1
                        self.state.conflict_count += 1

        return conflicts

    def _is_conflicting_payload(self, payload1: Dict, payload2: Dict) -> bool:
        """
        Iki payload catisiyor mu?

        Basit heuristik - gercek uygulamada daha sofistike.
        """
        # Ayni anahtarlar, farkli degerler
        common_keys = set(payload1.keys()) & set(payload2.keys())
        for key in common_keys:
            if payload1[key] != payload2[key]:
                return True
        return False

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def cleanup(self) -> Dict[str, int]:
        """
        Temizlik yap - suresi dolmus icerikleri kaldir.

        Returns:
            Temizlik raporu
        """
        expired = self.state.cleanup_expired()
        self._stats["contents_expired"] += expired

        return {
            "expired_removed": expired,
            "active_count": len(self.state.active_contents),
            "queue_length": len(self.state.broadcast_queue),
        }

    # ========================================================================
    # CYCLE MANAGEMENT
    # ========================================================================

    def process_cycle(self) -> Dict[str, Any]:
        """
        Bir workspace cycle'i calistir.

        Returns:
            Cycle sonucu
        """
        self._cycle_count += 1
        self.state.cycle_id = self._cycle_count

        result = {
            "cycle_id": self._cycle_count,
            "winner": None,
            "integrated": False,
            "broadcast": False,
        }

        # 1. Yarisma
        winner = self.run_competition()
        if winner:
            result["winner"] = winner.summary

            # 2. Entegrasyon
            if self.integrate_content(winner.id):
                result["integrated"] = True

                # 3. Yayin
                if self.broadcast(winner.id):
                    result["broadcast"] = True

        # Periyodik temizlik
        if self._cycle_count % self.config.cleanup_interval == 0:
            result["cleanup"] = self.cleanup()

        return result

    # ========================================================================
    # STATE ACCESS
    # ========================================================================

    def get_state(self) -> GlobalWorkspaceState:
        """Workspace durumunu getir."""
        return self.state

    def get_active_contents(self) -> List[WorkspaceContent]:
        """Aktif icerikleri getir."""
        return list(self.state.active_contents.values())

    def get_contents_by_type(self, content_type: BroadcastType) -> List[WorkspaceContent]:
        """Ture gore icerikleri getir."""
        return self.state.get_contents_by_type(content_type)

    def get_broadcast_history(self, limit: int = 10) -> List[WorkspaceContent]:
        """Son yayinlari getir."""
        history_ids = self.state.broadcast_history[-limit:]
        return [
            self.state.get_content(cid)
            for cid in history_ids
            if self.state.get_content(cid)
        ]

    # ========================================================================
    # STATISTICS & SUMMARY
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Istatistikleri getir."""
        return self._stats.copy()

    def summary(self) -> Dict[str, Any]:
        """Workspace ozeti."""
        return {
            "cycle_id": self._cycle_count,
            "active_contents": len(self.state.active_contents),
            "broadcast_queue": len(self.state.broadcast_queue),
            "listeners": len(self._listeners),
            "integration_count": self.state.integration_count,
            "broadcast_count": self.state.broadcast_count,
            "conflict_count": self.state.conflict_count,
            "last_broadcast": self.state.last_broadcast.isoformat() if self.state.last_broadcast else None,
            "stats": self._stats,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_global_workspace(
    config: Optional[GlobalWorkspaceConfig] = None,
) -> GlobalWorkspace:
    """GlobalWorkspace factory."""
    return GlobalWorkspace(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "GlobalWorkspaceConfig",
    "BroadcastListener",
    "GlobalWorkspace",
    "create_global_workspace",
]
