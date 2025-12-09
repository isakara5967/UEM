"""
core/language/risk/types.py

Risk Types - Risk değerlendirme veri yapıları.
UEM v2 - MessagePlan risk değerlendirmesi için.

Özellikler:
- RiskLevel: 4 seviyeli risk sınıflandırması
- RiskCategory: 6 risk kategorisi
- RiskFactor: Bireysel risk faktörü
- RiskAssessment: Kapsamlı değerlendirme

Risk Seviyeleri:
- LOW: Otomatik onay
- MEDIUM: İç değerlendirme (Self + Ethics)
- HIGH: Dikkatli değerlendirme (Metamind)
- CRITICAL: Varsayılan ret
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class RiskLevel(str, Enum):
    """
    Risk seviyeleri - Kontrol mekanizması tetikleyicisi.

    Seviyeler:
    - LOW: Güvenli, otomatik onay
    - MEDIUM: Orta risk, iç değerlendirme gerekli
    - HIGH: Yüksek risk, dikkatli değerlendirme
    - CRITICAL: Kritik risk, varsayılan ret
    """
    LOW = "low"                 # Otomatik onay
    MEDIUM = "medium"           # Self + Ethics değerlendirme
    HIGH = "high"               # Metamind + detaylı analiz
    CRITICAL = "critical"       # Varsayılan ret

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """
        Skor değerinden risk seviyesi belirle.

        Args:
            score: 0.0-1.0 arası risk skoru

        Returns:
            Uygun RiskLevel
        """
        if score < 0.25:
            return cls.LOW
        elif score < 0.50:
            return cls.MEDIUM
        elif score < 0.75:
            return cls.HIGH
        else:
            return cls.CRITICAL

    @property
    def requires_human_approval(self) -> bool:
        """Bu seviye insan onayı gerektiriyor mu? (Aşama 1)"""
        return self in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    @property
    def allows_auto_approval(self) -> bool:
        """Otomatik onay mümkün mü?"""
        return self == RiskLevel.LOW


class RiskCategory(str, Enum):
    """
    Risk kategorileri - Riskin türü/kaynağı.

    Kategoriler:
    - ETHICAL: Etik ihlal riski
    - EMOTIONAL: Duygusal zarar riski
    - FACTUAL: Yanlış bilgi riski
    - SAFETY: Güvenlik riski
    - PRIVACY: Gizlilik riski
    - BOUNDARY: Sınır ihlali riski
    """
    ETHICAL = "ethical"         # Etik değerlere aykırılık
    EMOTIONAL = "emotional"     # Duygusal zarar potansiyeli
    FACTUAL = "factual"         # Yanlış/yanıltıcı bilgi
    SAFETY = "safety"           # Fiziksel/dijital güvenlik
    PRIVACY = "privacy"         # Gizlilik ihlali
    BOUNDARY = "boundary"       # Kapsam/rol sınır ihlali


@dataclass
class RiskFactor:
    """
    Bireysel risk faktörü.

    Bir RiskAssessment birden fazla RiskFactor içerebilir.
    Her faktör, riskin bir boyutunu temsil eder.

    Attributes:
        id: Benzersiz faktör ID'si
        category: Risk kategorisi
        description: Faktör açıklaması
        score: Faktör skoru (0.0-1.0)
        source: Bu faktörü tespit eden kaynak
        evidence: Destekleyici kanıtlar
        mitigation: Azaltma önerisi
    """
    id: str
    category: RiskCategory
    description: str
    score: float                        # 0.0 (düşük) - 1.0 (yüksek)
    source: str = "unknown"             # "ethics", "affect", "metamind", "self", "pattern"
    evidence: List[str] = field(default_factory=list)
    mitigation: Optional[str] = None

    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"RiskFactor score must be between 0.0 and 1.0, got {self.score}")

    @property
    def is_high(self) -> bool:
        """Bu faktör yüksek riskli mi?"""
        return self.score >= 0.7

    @property
    def is_critical(self) -> bool:
        """Bu faktör kritik riskli mi?"""
        return self.score >= 0.85


@dataclass
class RiskAssessment:
    """
    Kapsamlı risk değerlendirmesi.

    MessagePlan için yapılan risk değerlendirmesinin sonucu.
    Ethics, Affect, Self ve Metamind modüllerinden gelen
    bilgileri birleştirir.

    Attributes:
        id: Benzersiz değerlendirme ID'si
        level: Genel risk seviyesi
        overall_score: Toplam risk skoru (0.0-1.0)
        ethical_score: Ethics modülünden (0.0-1.0, düşük=güvenli)
        trust_impact: Affect modülünden (-1.0 ile 1.0)
        structural_impact: Metamind'dan (0.0-1.0)
        factors: Bireysel risk faktörleri
        recommendation: Öneri (approve, review, reject)
        reasoning: Karar gerekçesi
        message_plan_id: Değerlendirilen plan ID'si
        context: Ek bağlam
        created_at: Oluşturulma zamanı
    """
    id: str
    level: RiskLevel
    overall_score: float = 0.0          # 0.0 (güvenli) - 1.0 (riskli)
    ethical_score: float = 0.0          # Ethics modülünden
    trust_impact: float = 0.0           # Affect modülünden (-1.0 to 1.0)
    structural_impact: float = 0.0      # Metamind'dan
    factors: List[RiskFactor] = field(default_factory=list)
    recommendation: str = "approve"     # "approve", "review", "modify", "reject"
    reasoning: str = ""
    message_plan_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate score ranges."""
        if not 0.0 <= self.overall_score <= 1.0:
            raise ValueError(
                f"overall_score must be between 0.0 and 1.0, got {self.overall_score}"
            )

        if not 0.0 <= self.ethical_score <= 1.0:
            raise ValueError(
                f"ethical_score must be between 0.0 and 1.0, got {self.ethical_score}"
            )

        if not -1.0 <= self.trust_impact <= 1.0:
            raise ValueError(
                f"trust_impact must be between -1.0 and 1.0, got {self.trust_impact}"
            )

        if not 0.0 <= self.structural_impact <= 1.0:
            raise ValueError(
                f"structural_impact must be between 0.0 and 1.0, got {self.structural_impact}"
            )

        valid_recommendations = {"approve", "review", "modify", "reject"}
        if self.recommendation not in valid_recommendations:
            raise ValueError(
                f"recommendation must be one of {valid_recommendations}, got {self.recommendation}"
            )

    @property
    def is_approved(self) -> bool:
        """Onaylandı mı?"""
        return self.recommendation == "approve"

    @property
    def is_rejected(self) -> bool:
        """Reddedildi mi?"""
        return self.recommendation == "reject"

    @property
    def needs_review(self) -> bool:
        """İnceleme gerekiyor mu?"""
        return self.recommendation in ("review", "modify")

    @property
    def highest_risk_factor(self) -> Optional[RiskFactor]:
        """En yüksek riskli faktör."""
        if not self.factors:
            return None
        return max(self.factors, key=lambda f: f.score)

    def get_factors_by_category(self, category: RiskCategory) -> List[RiskFactor]:
        """Belirli kategorideki faktörleri getir."""
        return [f for f in self.factors if f.category == category]

    def has_ethical_concern(self, threshold: float = 0.5) -> bool:
        """Etik endişe var mı?"""
        return self.ethical_score >= threshold

    def has_trust_damage(self, threshold: float = -0.3) -> bool:
        """Güven hasarı riski var mı?"""
        return self.trust_impact <= threshold

    def calculate_weighted_score(
        self,
        ethical_weight: float = 0.4,
        trust_weight: float = 0.3,
        structural_weight: float = 0.3
    ) -> float:
        """
        Ağırlıklı risk skoru hesapla.

        Args:
            ethical_weight: Etik skor ağırlığı
            trust_weight: Güven etkisi ağırlığı
            structural_weight: Yapısal etki ağırlığı

        Returns:
            Ağırlıklı toplam skor (0.0-1.0)
        """
        # Trust impact'i 0-1 aralığına normalize et (-1:1 -> 0:1, negatif kötü)
        normalized_trust = (1 - self.trust_impact) / 2

        weighted = (
            self.ethical_score * ethical_weight +
            normalized_trust * trust_weight +
            self.structural_impact * structural_weight
        )

        return min(max(weighted, 0.0), 1.0)

    @classmethod
    def create_low_risk(
        cls,
        message_plan_id: Optional[str] = None,
        reasoning: str = "No significant risks detected"
    ) -> "RiskAssessment":
        """Düşük riskli değerlendirme oluştur."""
        return cls(
            id=generate_risk_assessment_id(),
            level=RiskLevel.LOW,
            overall_score=0.1,
            recommendation="approve",
            reasoning=reasoning,
            message_plan_id=message_plan_id
        )

    @classmethod
    def create_critical_risk(
        cls,
        factors: List[RiskFactor],
        message_plan_id: Optional[str] = None,
        reasoning: str = "Critical risk factors detected"
    ) -> "RiskAssessment":
        """Kritik riskli değerlendirme oluştur."""
        return cls(
            id=generate_risk_assessment_id(),
            level=RiskLevel.CRITICAL,
            overall_score=0.9,
            factors=factors,
            recommendation="reject",
            reasoning=reasoning,
            message_plan_id=message_plan_id
        )


def generate_risk_assessment_id() -> str:
    """Generate unique risk assessment ID."""
    return f"risk_{uuid.uuid4().hex[:12]}"


def generate_risk_factor_id() -> str:
    """Generate unique risk factor ID."""
    return f"rf_{uuid.uuid4().hex[:12]}"
