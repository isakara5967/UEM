"""
UEM v2 - Phase Definitions

Cognitive cycle fazları - 10-phase model.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum, auto


class Phase(str, Enum):
    """
    10-Phase Cognitive Cycle.
    
    Her faz sırayla çalışır, önceki fazın çıktısı sonrakine girdi olur.
    """
    
    # Algı Fazları (Perception)
    SENSE = "1_sense"           # Ham duyusal girdi al
    ATTEND = "2_attend"         # Dikkat yönlendir
    PERCEIVE = "3_perceive"     # Anlam çıkar
    
    # Bellek Fazları (Memory)
    RETRIEVE = "4_retrieve"     # İlgili anıları getir
    
    # Biliş Fazları (Cognition)  
    REASON = "5_reason"         # Akıl yürüt
    EVALUATE = "6_evaluate"     # Değerlendir
    
    # Duygu Fazları (Affect)
    FEEL = "7_feel"             # Duygu hesapla
    
    # Yönetici Fazları (Executive)
    DECIDE = "8_decide"         # Karar ver
    PLAN = "9_plan"             # Plan yap
    ACT = "10_act"              # Eylemi gerçekleştir
    
    @classmethod
    def ordered(cls) -> List["Phase"]:
        """Fazları sıralı olarak döndür."""
        return [
            cls.SENSE,
            cls.ATTEND,
            cls.PERCEIVE,
            cls.RETRIEVE,
            cls.REASON,
            cls.EVALUATE,
            cls.FEEL,
            cls.DECIDE,
            cls.PLAN,
            cls.ACT,
        ]
    
    @classmethod
    def get_module(cls, phase: "Phase") -> str:
        """Fazın ait olduğu modülü döndür."""
        mapping = {
            cls.SENSE: "perception",
            cls.ATTEND: "perception",
            cls.PERCEIVE: "perception",
            cls.RETRIEVE: "memory",
            cls.REASON: "cognition",
            cls.EVALUATE: "cognition",
            cls.FEEL: "affect",
            cls.DECIDE: "executive",
            cls.PLAN: "executive",
            cls.ACT: "executive",
        }
        return mapping.get(phase, "unknown")


@dataclass
class PhaseConfig:
    """Faz yapılandırması."""
    phase: Phase
    enabled: bool = True
    timeout_ms: float = 1000.0  # Maksimum çalışma süresi
    required: bool = True       # Başarısız olursa cycle durur mu?
    retry_count: int = 0        # Başarısızlıkta kaç kez dene


@dataclass  
class PhaseResult:
    """Tek bir fazın sonucu."""
    phase: Phase
    success: bool
    duration_ms: float = 0.0
    output: Optional[dict] = None
    error: Optional[str] = None
    skipped: bool = False
    
    @property
    def status_str(self) -> str:
        if self.skipped:
            return "SKIPPED"
        return "OK" if self.success else "FAILED"


# Default faz yapılandırması
DEFAULT_PHASE_CONFIGS = [
    PhaseConfig(Phase.SENSE, timeout_ms=100),
    PhaseConfig(Phase.ATTEND, timeout_ms=50),
    PhaseConfig(Phase.PERCEIVE, timeout_ms=200),
    PhaseConfig(Phase.RETRIEVE, timeout_ms=300),
    PhaseConfig(Phase.REASON, timeout_ms=500),
    PhaseConfig(Phase.EVALUATE, timeout_ms=200),
    PhaseConfig(Phase.FEEL, timeout_ms=100),
    PhaseConfig(Phase.DECIDE, timeout_ms=200),
    PhaseConfig(Phase.PLAN, timeout_ms=300),
    PhaseConfig(Phase.ACT, timeout_ms=100),
]
