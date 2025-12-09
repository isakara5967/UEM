"""
core/learning/types.py

Learning Module Types - Feedback ve Pattern tipleri.
UEM v2 - Ogrenme sistemi icin temel veri yapilari.

Ozellikler:
- FeedbackType: Geri bildirim turleri (explicit/implicit)
- PatternType: Davranis pattern turleri
- Feedback: Geri bildirim kaydi
- Pattern: Ogrenilen davranis patterni
- LearningOutcome: Ogrenme sonucu
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class FeedbackType(str, Enum):
    """Geri bildirim turleri."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    EXPLICIT = "explicit"      # Kullanici direkt soyledi
    IMPLICIT = "implicit"      # Davranistan cikarildi


class PatternType(str, Enum):
    """Davranis pattern turleri."""
    RESPONSE = "response"      # Cevap pattern'i
    BEHAVIOR = "behavior"      # Davranis pattern'i
    EMOTION = "emotion"        # Duygu pattern'i
    LANGUAGE = "language"      # Dil pattern'i


@dataclass
class Feedback:
    """Geri bildirim kaydi."""
    id: str
    interaction_id: str
    feedback_type: FeedbackType
    value: float              # -1.0 to 1.0
    timestamp: datetime
    user_id: Optional[str] = None
    context: Optional[str] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Validate value range."""
        if not -1.0 <= self.value <= 1.0:
            raise ValueError(f"Feedback value must be between -1.0 and 1.0, got {self.value}")


@dataclass
class Pattern:
    """Ogrenilen davranis patterni."""
    id: str
    pattern_type: PatternType
    content: str              # Pattern icerigi
    embedding: Optional[List[float]] = None
    success_count: int = 0
    failure_count: int = 0
    total_reward: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Basari orani hesapla."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5

    @property
    def average_reward(self) -> float:
        """Ortalama odul hesapla."""
        total = self.success_count + self.failure_count
        return self.total_reward / total if total > 0 else 0.0

    @property
    def total_uses(self) -> int:
        """Toplam kullanim sayisi."""
        return self.success_count + self.failure_count


@dataclass
class LearningOutcome:
    """Ogrenme sonucu."""
    pattern_id: str
    feedback: Feedback
    reward: float
    pattern_updated: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Rule:
    """
    Genellestirilmis kural - pattern'lerden cikarilmis template.

    Ornek:
        template: "Merhaba {name}, nasilsin?"
        slots: ["name"]
        source_patterns: ["pat_abc123", "pat_def456"]
    """
    id: str
    pattern_type: PatternType
    template: str                    # "Merhaba {name}" gibi
    slots: List[str]                 # ["name"]
    source_patterns: List[str]       # Bu kural hangi pattern'lerden cikti
    confidence: float                # 0.0 - 1.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


def generate_feedback_id() -> str:
    """Generate unique feedback ID."""
    return f"fb_{uuid.uuid4().hex[:12]}"


def generate_pattern_id() -> str:
    """Generate unique pattern ID."""
    return f"pat_{uuid.uuid4().hex[:12]}"


def generate_rule_id() -> str:
    """Generate unique rule ID."""
    return f"rule_{uuid.uuid4().hex[:12]}"
