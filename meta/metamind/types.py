"""
UEM v2 - MetaMind Types

Meta-cognitive analysis tipleri.
Sistem performansini analiz eder, ogrenilenleri cikarir, kaliplari tespit eder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class InsightType(str, Enum):
    """Ogrenilen ders turleri."""
    PERFORMANCE = "performance"       # Performans ilgili
    BOTTLENECK = "bottleneck"         # Darbogazlar
    OPTIMIZATION = "optimization"     # Optimizasyon firsatlari
    ANOMALY = "anomaly"               # Anormallikler
    CORRELATION = "correlation"       # Iliskiler
    TREND = "trend"                   # Trendler
    WARNING = "warning"               # Uyarilar
    SUCCESS = "success"               # Basari paternleri


class PatternType(str, Enum):
    """Tespit edilen kalip turleri."""
    RECURRING = "recurring"           # Tekrarlayan
    CYCLIC = "cyclic"                 # Dongusal
    SPIKE = "spike"                   # Ani artis
    DEGRADATION = "degradation"       # Bozulma
    STABILITY = "stability"           # Kararlilik
    OSCILLATION = "oscillation"       # Salinti
    IMPROVEMENT = "improvement"       # Iyilesme
    ANOMALY = "anomaly"               # Anormallik


class LearningGoalType(str, Enum):
    """Ogrenme hedef turleri."""
    SPEED = "speed"                   # Hiz artirma
    ACCURACY = "accuracy"             # Dogruluk artirma
    EFFICIENCY = "efficiency"         # Verimlilik
    STABILITY = "stability"           # Kararlilik
    MEMORY = "memory"                 # Bellek kullanimi
    ADAPTABILITY = "adaptability"     # Uyum yetenegi


class MetaStateType(str, Enum):
    """Meta-bilissel durum turleri."""
    ANALYZING = "analyzing"           # Analiz ediliyor
    LEARNING = "learning"             # Ogreniyor
    ADAPTING = "adapting"             # Uyum sagliyor
    MONITORING = "monitoring"         # Izliyor
    OPTIMIZING = "optimizing"         # Optimize ediyor
    IDLE = "idle"                     # Bosta


class AnalysisScope(str, Enum):
    """Analiz kapsami."""
    SINGLE_CYCLE = "single_cycle"     # Tek cycle
    SHORT_TERM = "short_term"         # Kisa vadeli (son 10 cycle)
    MEDIUM_TERM = "medium_term"       # Orta vadeli (son 100 cycle)
    LONG_TERM = "long_term"           # Uzun vadeli (tum gecmis)


class SeverityLevel(str, Enum):
    """Ciddiyet seviyesi."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class CycleAnalysisResult:
    """Tek cycle analiz sonucu."""
    cycle_id: int
    timestamp: datetime = field(default_factory=datetime.now)

    # Performans metrikleri
    total_duration_ms: float = 0.0
    phase_durations: Dict[str, float] = field(default_factory=dict)
    slowest_phase: Optional[str] = None
    fastest_phase: Optional[str] = None

    # Basari metrikleri
    success: bool = True
    failed_phases: List[str] = field(default_factory=list)

    # Kaynak kullanimi
    memory_retrievals: int = 0
    memory_stores: int = 0
    events_processed: int = 0

    # Karsilastirma
    vs_average: Optional[float] = None  # Ortalamaya gore % fark
    vs_previous: Optional[float] = None  # Oncekine gore % fark

    # Anomali
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None

    def get_performance_score(self) -> float:
        """Performans skoru (0-1)."""
        if self.total_duration_ms == 0:
            return 1.0

        # Daha kisa sure = daha yuksek skor
        # 100ms optimal, 1000ms+ kotu
        score = max(0.0, 1.0 - (self.total_duration_ms / 1000.0))

        # Basarisiz phase'ler skoru dusurur
        if not self.success:
            score *= 0.5

        return min(1.0, score)

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye donustur."""
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "phase_durations": self.phase_durations,
            "slowest_phase": self.slowest_phase,
            "fastest_phase": self.fastest_phase,
            "success": self.success,
            "failed_phases": self.failed_phases,
            "performance_score": self.get_performance_score(),
            "is_anomaly": self.is_anomaly,
            "anomaly_reason": self.anomaly_reason,
        }


@dataclass
class Insight:
    """Ogrenilen bir ders/icigor."""
    id: str = ""
    insight_type: InsightType = InsightType.PERFORMANCE
    timestamp: datetime = field(default_factory=datetime.now)

    # Icerik
    title: str = ""
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Onem
    severity: SeverityLevel = SeverityLevel.MEDIUM
    confidence: float = 0.8  # Guvenilirlik (0-1)

    # Aksiyon
    actionable: bool = True
    recommended_action: Optional[str] = None

    # Kaynak
    source_cycles: List[int] = field(default_factory=list)
    scope: AnalysisScope = AnalysisScope.SHORT_TERM

    # Yasam suresi
    expires_at: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = f"insight_{datetime.now().timestamp()}"

    def get_priority(self) -> float:
        """Oncelik skoru (0-1)."""
        severity_weights = {
            SeverityLevel.LOW: 0.2,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.CRITICAL: 1.0,
        }
        return severity_weights[self.severity] * self.confidence

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye donustur."""
        return {
            "id": self.id,
            "type": self.insight_type.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "priority": self.get_priority(),
            "actionable": self.actionable,
            "recommended_action": self.recommended_action,
            "is_active": self.is_active,
        }


@dataclass
class Pattern:
    """Tespit edilen bir kalip."""
    id: str = ""
    pattern_type: PatternType = PatternType.RECURRING
    timestamp: datetime = field(default_factory=datetime.now)

    # Kalip detaylari
    name: str = ""
    description: str = ""

    # Istatistikler
    occurrence_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    frequency: float = 0.0  # Cycle basina gorunme orani

    # Etki
    affected_metric: Optional[str] = None
    average_impact: float = 0.0  # Ortalama etki

    # Guvenilirlik
    confidence: float = 0.8
    stability: float = 0.5  # Kalip ne kadar kararli

    # Veri
    sample_cycles: List[int] = field(default_factory=list)
    data_points: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = f"pattern_{datetime.now().timestamp()}"
        if not self.first_seen:
            self.first_seen = datetime.now()

    def update_occurrence(self, cycle_id: int, impact: float = 0.0) -> None:
        """Kalip gorulmesini guncelle."""
        self.occurrence_count += 1
        self.last_seen = datetime.now()
        if cycle_id not in self.sample_cycles:
            self.sample_cycles.append(cycle_id)
            if len(self.sample_cycles) > 100:
                self.sample_cycles.pop(0)

        if impact != 0.0:
            self.data_points.append(impact)
            if len(self.data_points) > 100:
                self.data_points.pop(0)
            self.average_impact = sum(self.data_points) / len(self.data_points)

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye donustur."""
        return {
            "id": self.id,
            "type": self.pattern_type.value,
            "name": self.name,
            "description": self.description,
            "occurrence_count": self.occurrence_count,
            "frequency": self.frequency,
            "affected_metric": self.affected_metric,
            "average_impact": self.average_impact,
            "confidence": self.confidence,
            "stability": self.stability,
        }


@dataclass
class LearningGoal:
    """Ogrenme hedefi."""
    id: str = ""
    goal_type: LearningGoalType = LearningGoalType.EFFICIENCY
    created_at: datetime = field(default_factory=datetime.now)

    # Hedef detaylari
    name: str = ""
    description: str = ""
    target_metric: str = ""

    # Mevcut ve hedef degerler
    current_value: float = 0.0
    target_value: float = 0.0
    baseline_value: float = 0.0  # Baslangic degeri

    # Ilerleme
    progress: float = 0.0  # 0-1 arasi
    improvements: List[Dict[str, Any]] = field(default_factory=list)

    # Strateji
    strategy: Optional[str] = None
    tactics: List[str] = field(default_factory=list)

    # Durum
    is_active: bool = True
    achieved: bool = False
    achieved_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"goal_{datetime.now().timestamp()}"

    def update_progress(self, new_value: float) -> None:
        """Ilerlemeyi guncelle."""
        self.current_value = new_value

        # Ilerleme hesapla
        if self.target_value != self.baseline_value:
            self.progress = (new_value - self.baseline_value) / (self.target_value - self.baseline_value)
            self.progress = max(0.0, min(1.0, self.progress))

        # Hedefe ulasildi mi?
        if self.goal_type in (LearningGoalType.SPEED, LearningGoalType.MEMORY):
            # Dusuk deger iyi
            if new_value <= self.target_value:
                self.achieved = True
                self.achieved_at = datetime.now()
        else:
            # Yuksek deger iyi
            if new_value >= self.target_value:
                self.achieved = True
                self.achieved_at = datetime.now()

        # Iyilestirme kaydi
        self.improvements.append({
            "value": new_value,
            "progress": self.progress,
            "timestamp": datetime.now().isoformat(),
        })

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye donustur."""
        return {
            "id": self.id,
            "type": self.goal_type.value,
            "name": self.name,
            "target_metric": self.target_metric,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "progress": self.progress,
            "is_active": self.is_active,
            "achieved": self.achieved,
        }


@dataclass
class MetaState:
    """MetaMind durumu."""
    state_type: MetaStateType = MetaStateType.IDLE
    timestamp: datetime = field(default_factory=datetime.now)

    # Analiz durumu
    cycles_analyzed: int = 0
    last_analysis_cycle: Optional[int] = None

    # Insight durumu
    active_insights_count: int = 0
    total_insights_generated: int = 0

    # Pattern durumu
    patterns_detected: int = 0
    active_patterns_count: int = 0

    # Learning durumu
    active_goals_count: int = 0
    achieved_goals_count: int = 0

    # Genel saglik
    system_health: float = 1.0  # 0-1
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye donustur."""
        return {
            "state": self.state_type.value,
            "cycles_analyzed": self.cycles_analyzed,
            "active_insights": self.active_insights_count,
            "patterns_detected": self.patterns_detected,
            "active_goals": self.active_goals_count,
            "achieved_goals": self.achieved_goals_count,
            "system_health": self.system_health,
            "confidence": self.confidence,
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "InsightType",
    "PatternType",
    "LearningGoalType",
    "MetaStateType",
    "AnalysisScope",
    "SeverityLevel",
    # Dataclasses
    "CycleAnalysisResult",
    "Insight",
    "Pattern",
    "LearningGoal",
    "MetaState",
]
