"""
UEM v2 - Attention Module

Dikkat yonetimi ve kontrolu.
Spotlight metaforu - bilincin "fener" gibi odaklanmasi.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid

from .types import (
    AttentionFocus,
    AttentionMode,
    AttentionPriority,
    WorkspaceContent,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AttentionConfig:
    """Dikkat modulu yapilandirmasi."""
    # Dikkat parametreleri
    default_duration_ms: float = 5000.0   # Varsayilan odak suresi
    max_duration_ms: float = 30000.0      # Maksimum odak suresi
    min_switch_interval_ms: float = 500.0 # Minimum degisim araligi

    # Oncelik esikleri
    critical_threshold: float = 0.9       # Otomatik dikkat cekme
    high_threshold: float = 0.7
    normal_threshold: float = 0.5

    # Kapasite
    max_divided_targets: int = 3          # Bolusmis dikkatte maks hedef
    max_history: int = 50                 # Dikkat gecmisi

    # Decay
    attention_decay_rate: float = 0.02    # Odak zaman icinde zayiflar
    stability_decay_rate: float = 0.01

    # Filtre
    enable_inhibition: bool = True        # Dikkat engellemesi
    inhibition_duration_ms: float = 2000.0  # Engelleme suresi


# ============================================================================
# ATTENTION FILTER
# ============================================================================

@dataclass
class AttentionFilter:
    """
    Dikkat filtresi.

    AttentionFilter = Nelere dikkat edilmeyecegi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Filtre kurallari
    blocked_types: List[str] = field(default_factory=list)    # Engelli turler
    blocked_sources: List[str] = field(default_factory=list)  # Engelli kaynaklar
    min_priority: AttentionPriority = AttentionPriority.LOW   # Minimum oncelik

    # Inhibisyon (gecici engelleme)
    inhibited_targets: Dict[str, datetime] = field(default_factory=dict)

    def is_blocked(self, target_type: str, source: str, priority: AttentionPriority) -> bool:
        """Hedef engelli mi?"""
        if target_type in self.blocked_types:
            return True
        if source in self.blocked_sources:
            return True
        # Oncelik kontrolu
        priority_order = [
            AttentionPriority.BACKGROUND,
            AttentionPriority.LOW,
            AttentionPriority.NORMAL,
            AttentionPriority.HIGH,
            AttentionPriority.CRITICAL,
        ]
        if priority_order.index(priority) < priority_order.index(self.min_priority):
            return True
        return False

    def is_inhibited(self, target_id: str) -> bool:
        """Hedef gecici olarak engelli mi?"""
        if target_id not in self.inhibited_targets:
            return False
        inhibit_time = self.inhibited_targets[target_id]
        # Suresi doldu mu?
        return True  # Basit kontrol, tam sureli kontrol asagida

    def add_inhibition(self, target_id: str) -> None:
        """Gecici engelleme ekle."""
        self.inhibited_targets[target_id] = datetime.now()

    def clear_expired_inhibitions(self, duration_ms: float) -> int:
        """Suresi dolmus engellemeleri temizle."""
        now = datetime.now()
        expired = []
        for target_id, inhibit_time in self.inhibited_targets.items():
            elapsed = (now - inhibit_time).total_seconds() * 1000
            if elapsed > duration_ms:
                expired.append(target_id)
        for target_id in expired:
            del self.inhibited_targets[target_id]
        return len(expired)


# ============================================================================
# ATTENTION CONTROLLER
# ============================================================================

class AttentionController:
    """
    Dikkat kontrolcusu.

    "Spotlight" metaforu ile calisan dikkat yonetimi:
    - Odaklanma (focus)
    - Degistirme (switch)
    - Dagitma (divide)
    - Filtreleme (filter)
    """

    def __init__(self, config: Optional[AttentionConfig] = None):
        """
        AttentionController baslat.

        Args:
            config: Yapilandirma
        """
        self.config = config or AttentionConfig()

        # Mevcut dikkat
        self.current_focus: Optional[AttentionFocus] = None
        self.divided_focuses: List[AttentionFocus] = []  # Bolusmis dikkat

        # Mod
        self.mode: AttentionMode = AttentionMode.AUTOMATIC

        # Filtre
        self.filter = AttentionFilter()

        # Gecmis
        self._history: List[AttentionFocus] = []

        # Son degisim zamani
        self._last_switch_time: Optional[datetime] = None

        # Istatistikler
        self._stats = {
            "focus_count": 0,
            "switch_count": 0,
            "interrupted_count": 0,
            "filtered_count": 0,
            "critical_captures": 0,
        }

    # ========================================================================
    # FOCUS OPERATIONS
    # ========================================================================

    def focus_on(
        self,
        target_type: str,
        target_id: Optional[str] = None,
        target_description: str = "",
        priority: AttentionPriority = AttentionPriority.NORMAL,
        source_module: str = "",
        trigger_reason: str = "",
        duration_ms: Optional[float] = None,
        force: bool = False,
    ) -> Optional[AttentionFocus]:
        """
        Bir hedefe odaklan.

        Args:
            target_type: Hedef turu (entity, stimulus, thought, etc.)
            target_id: Hedef ID
            target_description: Hedef aciklamasi
            priority: Oncelik
            source_module: Kaynak modul
            trigger_reason: Neden dikkat cekti
            duration_ms: Odak suresi
            force: Zorla degistir

        Returns:
            Olusturulan odak veya None
        """
        # Filtre kontrolu
        if not force and self.filter.is_blocked(target_type, source_module, priority):
            self._stats["filtered_count"] += 1
            return None

        # Inhibisyon kontrolu
        if target_id and self.filter.is_inhibited(target_id):
            self._stats["filtered_count"] += 1
            return None

        # Switch interval kontrolu
        if not force and self._last_switch_time:
            elapsed = (datetime.now() - self._last_switch_time).total_seconds() * 1000
            if elapsed < self.config.min_switch_interval_ms:
                # Cok hizli degisim, sadece kritik icin izin ver
                if priority != AttentionPriority.CRITICAL:
                    return None

        # Mevcut odak kontrolu
        if self.current_focus and not force:
            # Mevcut odak daha mi onemli?
            if self.current_focus.priority_score > self._calculate_priority_score(priority, 0.5, 0.5):
                if priority != AttentionPriority.CRITICAL:
                    return None

        # Eski odagi gecmise ekle
        if self.current_focus:
            self._add_to_history(self.current_focus)
            if self.config.enable_inhibition:
                # Eski hedefe gecici inhibisyon
                if self.current_focus.target_id:
                    self.filter.add_inhibition(self.current_focus.target_id)

        # Yeni odak olustur
        focus = AttentionFocus(
            target_type=target_type,
            target_id=target_id,
            target_description=target_description,
            mode=self.mode if self.mode != AttentionMode.DIVIDED else AttentionMode.FOCUSED,
            priority=priority,
            intensity=0.7 if priority == AttentionPriority.CRITICAL else 0.5,
            stability=0.5,
            source_module=source_module,
            trigger_reason=trigger_reason,
            expected_duration_ms=duration_ms or self.config.default_duration_ms,
        )

        self.current_focus = focus
        self.mode = AttentionMode.FOCUSED
        self._last_switch_time = datetime.now()
        self._stats["focus_count"] += 1
        self._stats["switch_count"] += 1

        if priority == AttentionPriority.CRITICAL:
            self._stats["critical_captures"] += 1

        return focus

    def _calculate_priority_score(
        self,
        priority: AttentionPriority,
        intensity: float,
        stability: float,
    ) -> float:
        """Oncelik skoru hesapla."""
        priority_weights = {
            AttentionPriority.CRITICAL: 1.0,
            AttentionPriority.HIGH: 0.8,
            AttentionPriority.NORMAL: 0.5,
            AttentionPriority.LOW: 0.3,
            AttentionPriority.BACKGROUND: 0.1,
        }
        weight = priority_weights.get(priority, 0.5)
        return weight * intensity * stability

    # ========================================================================
    # ATTENTION CAPTURE
    # ========================================================================

    def capture_attention(
        self,
        content: WorkspaceContent,
        force: bool = False,
    ) -> bool:
        """
        Workspace iceriginin dikkati yakalamasi.

        Args:
            content: Icerik
            force: Zorla yakala

        Returns:
            Basarili mi
        """
        # Kritik icerik otomatik yakalar
        if content.priority == AttentionPriority.CRITICAL or content.urgency >= self.config.critical_threshold:
            force = True
            self._stats["interrupted_count"] += 1

        focus = self.focus_on(
            target_type=content.content_type.value,
            target_id=content.id,
            target_description=content.summary,
            priority=content.priority,
            source_module=content.source_module,
            trigger_reason=f"Competition score: {content.competition_score:.2f}",
            force=force,
        )

        return focus is not None

    # ========================================================================
    # DIVIDED ATTENTION
    # ========================================================================

    def divide_attention(
        self,
        targets: List[Dict[str, Any]],
    ) -> List[AttentionFocus]:
        """
        Dikkati bol.

        Args:
            targets: Hedef listesi [{"type": ..., "id": ..., ...}]

        Returns:
            Olusturulan odaklar
        """
        if len(targets) > self.config.max_divided_targets:
            targets = targets[:self.config.max_divided_targets]

        self.divided_focuses = []
        intensity_per_target = 0.8 / len(targets)

        for target in targets:
            focus = AttentionFocus(
                target_type=target.get("type", "unknown"),
                target_id=target.get("id"),
                target_description=target.get("description", ""),
                mode=AttentionMode.DIVIDED,
                priority=target.get("priority", AttentionPriority.NORMAL),
                intensity=intensity_per_target,
                stability=0.3,  # Bolusmis dikkat daha az stabil
                source_module=target.get("source", ""),
            )
            self.divided_focuses.append(focus)

        self.mode = AttentionMode.DIVIDED
        self.current_focus = None  # Ana odak yok

        return self.divided_focuses

    def consolidate_attention(self, target_index: int = 0) -> Optional[AttentionFocus]:
        """
        Bolusmis dikkati tek hedefe konsantre et.

        Args:
            target_index: Odaklanilacak hedef indeksi

        Returns:
            Yeni odak
        """
        if not self.divided_focuses:
            return self.current_focus

        if 0 <= target_index < len(self.divided_focuses):
            selected = self.divided_focuses[target_index]
            self.current_focus = AttentionFocus(
                target_type=selected.target_type,
                target_id=selected.target_id,
                target_description=selected.target_description,
                mode=AttentionMode.FOCUSED,
                priority=selected.priority,
                intensity=0.7,
                stability=0.5,
                source_module=selected.source_module,
            )

        self.divided_focuses = []
        self.mode = AttentionMode.FOCUSED

        return self.current_focus

    # ========================================================================
    # ATTENTION STATE
    # ========================================================================

    def get_current_focus(self) -> Optional[AttentionFocus]:
        """Mevcut odagi getir."""
        return self.current_focus

    def get_divided_focuses(self) -> List[AttentionFocus]:
        """Bolusmis odaklari getir."""
        return self.divided_focuses.copy()

    def get_mode(self) -> AttentionMode:
        """Dikkat modunu getir."""
        return self.mode

    def is_focused(self) -> bool:
        """Odaklanmis mi?"""
        return self.current_focus is not None and self.mode == AttentionMode.FOCUSED

    def is_divided(self) -> bool:
        """Dikkat bolunmus mu?"""
        return self.mode == AttentionMode.DIVIDED and len(self.divided_focuses) > 0

    # ========================================================================
    # ATTENTION MAINTENANCE
    # ========================================================================

    def sustain_focus(self, boost: float = 0.1) -> None:
        """
        Odagi surdurmek icin guclendir.
        """
        if self.current_focus:
            self.current_focus.stability = min(1.0, self.current_focus.stability + boost)
            self.mode = AttentionMode.SUSTAINED

    def release_focus(self) -> Optional[AttentionFocus]:
        """
        Odagi serbest birak.

        Returns:
            Serbest birakilan odak
        """
        released = self.current_focus
        if released:
            self._add_to_history(released)
        self.current_focus = None
        self.mode = AttentionMode.AUTOMATIC
        return released

    def apply_decay(self, duration_ms: float = 1000.0) -> None:
        """
        Dikkat zayiflamasi uygula.

        Args:
            duration_ms: Gecen sure
        """
        decay_factor = duration_ms / 1000.0  # Saniye cinsinden

        if self.current_focus:
            self.current_focus.intensity = max(
                0.0,
                self.current_focus.intensity - self.config.attention_decay_rate * decay_factor,
            )
            self.current_focus.stability = max(
                0.0,
                self.current_focus.stability - self.config.stability_decay_rate * decay_factor,
            )
            self.current_focus.duration_ms += duration_ms

            # Cok zayifladiysa serbest birak
            if self.current_focus.intensity < 0.1:
                self.release_focus()

        # Inhibisyonlari temizle
        self.filter.clear_expired_inhibitions(self.config.inhibition_duration_ms)

    def check_timeout(self) -> bool:
        """
        Odak suresi doldu mu?

        Returns:
            Timeout oldu mu
        """
        if self.current_focus and self.current_focus.is_expired:
            self._add_to_history(self.current_focus)
            self.current_focus = None
            self.mode = AttentionMode.AUTOMATIC
            return True
        return False

    # ========================================================================
    # FILTER MANAGEMENT
    # ========================================================================

    def block_type(self, target_type: str) -> None:
        """Tur engelle."""
        if target_type not in self.filter.blocked_types:
            self.filter.blocked_types.append(target_type)

    def unblock_type(self, target_type: str) -> None:
        """Tur engelini kaldir."""
        if target_type in self.filter.blocked_types:
            self.filter.blocked_types.remove(target_type)

    def set_min_priority(self, priority: AttentionPriority) -> None:
        """Minimum oncelik ayarla."""
        self.filter.min_priority = priority

    # ========================================================================
    # HISTORY
    # ========================================================================

    def _add_to_history(self, focus: AttentionFocus) -> None:
        """Gecmise ekle."""
        self._history.append(focus)
        if len(self._history) > self.config.max_history:
            self._history.pop(0)

    def get_history(self, limit: int = 10) -> List[AttentionFocus]:
        """Son odaklari getir."""
        return self._history[-limit:]

    def get_recent_targets(self, limit: int = 5) -> List[str]:
        """Son hedefleri getir."""
        recent = self._history[-limit:]
        return [f.target_description for f in recent if f.target_description]

    # ========================================================================
    # STATISTICS & STATE
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Istatistikleri getir."""
        return self._stats.copy()

    def summary(self) -> Dict[str, Any]:
        """Dikkat durumu ozeti."""
        return {
            "mode": self.mode.value,
            "is_focused": self.is_focused(),
            "is_divided": self.is_divided(),
            "current_focus": {
                "target": self.current_focus.target_description,
                "priority": self.current_focus.priority.value,
                "intensity": self.current_focus.intensity,
                "stability": self.current_focus.stability,
            } if self.current_focus else None,
            "divided_count": len(self.divided_focuses),
            "history_count": len(self._history),
            "blocked_types": self.filter.blocked_types,
            "inhibited_count": len(self.filter.inhibited_targets),
            "stats": self._stats,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_attention_controller(
    config: Optional[AttentionConfig] = None,
) -> AttentionController:
    """AttentionController factory."""
    return AttentionController(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "AttentionConfig",
    "AttentionFilter",
    "AttentionController",
    "create_attention_controller",
]
