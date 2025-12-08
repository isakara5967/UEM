"""
UEM v2 - Cognition Types

Biliş modülünün temel veri yapıları.
Belief, Goal, Plan, Intention ve CognitiveState tanımları.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class BeliefType(str, Enum):
    """İnanç türleri."""
    FACTUAL = "factual"           # Gözleme dayalı
    INFERRED = "inferred"         # Çıkarıma dayalı
    ASSUMED = "assumed"           # Varsayım
    HYPOTHETICAL = "hypothetical" # Hipotez


class BeliefStrength(str, Enum):
    """İnanç gücü seviyeleri."""
    CERTAIN = "certain"           # Kesin (0.9-1.0)
    STRONG = "strong"             # Güçlü (0.7-0.9)
    MODERATE = "moderate"         # Orta (0.5-0.7)
    WEAK = "weak"                 # Zayıf (0.3-0.5)
    UNCERTAIN = "uncertain"       # Belirsiz (0.0-0.3)


class GoalType(str, Enum):
    """Hedef türleri."""
    SURVIVAL = "survival"         # Hayatta kalma
    MAINTENANCE = "maintenance"   # Durum koruma
    ACHIEVEMENT = "achievement"   # Başarı
    AVOIDANCE = "avoidance"       # Kaçınma
    SOCIAL = "social"             # Sosyal
    EXPLORATION = "exploration"   # Keşif


class GoalPriority(str, Enum):
    """Hedef önceliği."""
    CRITICAL = "critical"         # Kritik (acil)
    HIGH = "high"                 # Yüksek
    NORMAL = "normal"             # Normal
    LOW = "low"                   # Düşük
    BACKGROUND = "background"     # Arka plan


class GoalStatus(str, Enum):
    """Hedef durumu."""
    ACTIVE = "active"             # Aktif, üzerinde çalışılıyor
    PENDING = "pending"           # Beklemede
    ACHIEVED = "achieved"         # Başarıldı
    FAILED = "failed"             # Başarısız
    SUSPENDED = "suspended"       # Askıya alındı
    ABANDONED = "abandoned"       # Terk edildi


class IntentionStrength(str, Enum):
    """Niyet gücü."""
    COMMITTED = "committed"       # Kararlı
    INTENDED = "intended"         # Niyetli
    CONSIDERING = "considering"   # Düşünüyor
    POSSIBLE = "possible"         # Mümkün


class ReasoningType(str, Enum):
    """Akıl yürütme türleri."""
    DEDUCTION = "deduction"       # Tümdengelim: A→B, A ∴ B
    INDUCTION = "induction"       # Tümevarım: pattern → general rule
    ABDUCTION = "abduction"       # Abdüksiyon: B, A→B ∴ A (en iyi açıklama)
    ANALOGY = "analogy"           # Benzetme: A~B, A has P ∴ B has P


class RiskLevel(str, Enum):
    """Risk seviyesi."""
    CRITICAL = "critical"         # Kritik risk
    HIGH = "high"                 # Yüksek risk
    MODERATE = "moderate"         # Orta risk
    LOW = "low"                   # Düşük risk
    MINIMAL = "minimal"           # Minimal risk


class OpportunityLevel(str, Enum):
    """Fırsat seviyesi."""
    EXCELLENT = "excellent"       # Mükemmel fırsat
    GOOD = "good"                 # İyi fırsat
    MODERATE = "moderate"         # Orta fırsat
    LIMITED = "limited"           # Sınırlı fırsat
    NONE = "none"                 # Fırsat yok


# ============================================================================
# BELIEF (İnanç)
# ============================================================================

@dataclass
class Belief:
    """
    Bir inanç/bilgi temsili.

    Belief = Agent'ın dünya hakkındaki bir kanısı
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # İçerik
    subject: str = ""                    # Ne hakkında
    predicate: str = ""                  # Ne iddia ediyor
    content: Dict[str, Any] = field(default_factory=dict)  # Detaylı içerik

    # Tip ve güç
    belief_type: BeliefType = BeliefType.ASSUMED
    confidence: float = 0.5              # 0.0-1.0 güven skoru

    # Kaynak ve geçerlilik
    source: str = ""                     # Nereden geldi (perception, inference, memory)
    evidence: List[str] = field(default_factory=list)  # Destekleyen kanıtlar
    contradictions: List[str] = field(default_factory=list)  # Çelişen inançlar

    # Zaman
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None  # Geçerlilik süresi

    # Meta
    cycle_created: int = 0
    revision_count: int = 0

    @property
    def strength(self) -> BeliefStrength:
        """Confidence'a göre güç seviyesi."""
        if self.confidence >= 0.9:
            return BeliefStrength.CERTAIN
        elif self.confidence >= 0.7:
            return BeliefStrength.STRONG
        elif self.confidence >= 0.5:
            return BeliefStrength.MODERATE
        elif self.confidence >= 0.3:
            return BeliefStrength.WEAK
        return BeliefStrength.UNCERTAIN

    def update_confidence(self, delta: float) -> None:
        """Güveni güncelle."""
        self.confidence = max(0.0, min(1.0, self.confidence + delta))
        self.updated_at = datetime.now()
        self.revision_count += 1

    def add_evidence(self, evidence_id: str) -> None:
        """Kanıt ekle, güveni artır."""
        if evidence_id not in self.evidence:
            self.evidence.append(evidence_id)
            self.update_confidence(0.1)

    def add_contradiction(self, belief_id: str) -> None:
        """Çelişki ekle, güveni azalt."""
        if belief_id not in self.contradictions:
            self.contradictions.append(belief_id)
            self.update_confidence(-0.15)

    def is_valid(self) -> bool:
        """İnanç hala geçerli mi?"""
        if self.valid_until and datetime.now() > self.valid_until:
            return False
        return self.confidence > 0.1


# ============================================================================
# GOAL (Hedef)
# ============================================================================

@dataclass
class Goal:
    """
    Bir hedef temsili.

    Goal = Agent'ın ulaşmak istediği durum
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tanım
    name: str = ""
    description: str = ""
    goal_type: GoalType = GoalType.ACHIEVEMENT

    # Öncelik ve durum
    priority: GoalPriority = GoalPriority.NORMAL
    status: GoalStatus = GoalStatus.PENDING

    # Koşullar
    preconditions: List[str] = field(default_factory=list)  # Başlamak için
    success_conditions: List[str] = field(default_factory=list)  # Başarı kriterleri
    failure_conditions: List[str] = field(default_factory=list)  # Başarısızlık kriterleri

    # İlerleme
    progress: float = 0.0               # 0.0-1.0
    estimated_completion: float = 0.0   # Tahmini tamamlanma oranı

    # İlişkiler
    parent_goal: Optional[str] = None   # Üst hedef
    sub_goals: List[str] = field(default_factory=list)  # Alt hedefler
    depends_on: List[str] = field(default_factory=list)  # Bağımlılıklar

    # Değer
    utility: float = 0.5                # Başarının değeri
    urgency: float = 0.5                # Aciliyet

    # Zaman
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None

    # Meta
    attempts: int = 0
    max_attempts: int = 3

    @property
    def importance(self) -> float:
        """Önem skoru = utility * urgency * priority_weight."""
        priority_weights = {
            GoalPriority.CRITICAL: 2.0,
            GoalPriority.HIGH: 1.5,
            GoalPriority.NORMAL: 1.0,
            GoalPriority.LOW: 0.5,
            GoalPriority.BACKGROUND: 0.2,
        }
        weight = priority_weights.get(self.priority, 1.0)
        return self.utility * self.urgency * weight

    def can_start(self, satisfied_conditions: Set[str]) -> bool:
        """Hedef başlayabilir mi?"""
        return all(pc in satisfied_conditions for pc in self.preconditions)

    def is_achieved(self, satisfied_conditions: Set[str]) -> bool:
        """Hedef başarıldı mı?"""
        return all(sc in satisfied_conditions for sc in self.success_conditions)

    def is_failed(self, satisfied_conditions: Set[str]) -> bool:
        """Hedef başarısız mı?"""
        if self.attempts >= self.max_attempts:
            return True
        return any(fc in satisfied_conditions for fc in self.failure_conditions)

    def update_progress(self, new_progress: float) -> None:
        """İlerlemeyi güncelle."""
        self.progress = max(0.0, min(1.0, new_progress))
        if self.progress >= 1.0:
            self.status = GoalStatus.ACHIEVED


# ============================================================================
# INTENTION (Niyet)
# ============================================================================

@dataclass
class Intention:
    """
    Bir niyet temsili.

    Intention = Belirli bir eylemi yapma kararı
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Bağlantı
    goal_id: str = ""                   # İlişkili hedef
    action_type: str = ""               # Yapılacak eylem türü

    # Detay
    target: Optional[str] = None        # Hedef varlık/nesne
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Güç ve olasılık
    strength: IntentionStrength = IntentionStrength.CONSIDERING
    commitment: float = 0.5             # 0.0-1.0 kararlılık

    # Beklentiler
    expected_outcome: str = ""
    expected_utility: float = 0.5
    expected_risk: float = 0.2

    # Zaman
    formed_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None

    @property
    def priority_score(self) -> float:
        """Öncelik skoru."""
        strength_weights = {
            IntentionStrength.COMMITTED: 1.0,
            IntentionStrength.INTENDED: 0.7,
            IntentionStrength.CONSIDERING: 0.4,
            IntentionStrength.POSSIBLE: 0.2,
        }
        weight = strength_weights.get(self.strength, 0.5)
        risk_factor = 1.0 - (self.expected_risk * 0.5)
        return self.commitment * weight * self.expected_utility * risk_factor

    def strengthen(self) -> None:
        """Niyeti güçlendir."""
        self.commitment = min(1.0, self.commitment + 0.2)
        if self.commitment > 0.8:
            self.strength = IntentionStrength.COMMITTED
        elif self.commitment > 0.5:
            self.strength = IntentionStrength.INTENDED

    def weaken(self) -> None:
        """Niyeti zayıflat."""
        self.commitment = max(0.0, self.commitment - 0.2)
        if self.commitment < 0.3:
            self.strength = IntentionStrength.POSSIBLE
        elif self.commitment < 0.5:
            self.strength = IntentionStrength.CONSIDERING


# ============================================================================
# PLAN (Plan)
# ============================================================================

@dataclass
class PlanStep:
    """Plan adımı."""
    step_id: int
    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    expected_effects: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, executing, completed, failed, skipped


@dataclass
class Plan:
    """
    Bir plan temsili.

    Plan = Hedefe ulaşmak için sıralı eylem dizisi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Bağlantı
    goal_id: str = ""                   # İlişkili hedef
    name: str = ""

    # Adımlar
    steps: List[PlanStep] = field(default_factory=list)
    current_step: int = 0

    # Kalite
    feasibility: float = 0.5            # Uygulanabilirlik
    expected_success: float = 0.5       # Beklenen başarı olasılığı
    estimated_cost: float = 0.3         # Tahmini maliyet

    # Durum
    status: str = "draft"               # draft, ready, executing, completed, failed

    # Zaman
    created_at: datetime = field(default_factory=datetime.now)

    # Alternatifler
    contingency_plans: List[str] = field(default_factory=list)  # Yedek plan ID'leri

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return completed / len(self.steps)

    @property
    def next_step(self) -> Optional[PlanStep]:
        """Sıradaki adım."""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def add_step(
        self,
        action: str,
        target: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        preconditions: Optional[List[str]] = None,
        expected_effects: Optional[List[str]] = None,
    ) -> PlanStep:
        """Plan adımı ekle."""
        step = PlanStep(
            step_id=len(self.steps),
            action=action,
            target=target,
            parameters=parameters or {},
            preconditions=preconditions or [],
            expected_effects=expected_effects or [],
        )
        self.steps.append(step)
        return step

    def advance(self) -> Optional[PlanStep]:
        """Bir sonraki adıma geç."""
        if self.current_step < len(self.steps):
            self.steps[self.current_step].status = "completed"
            self.current_step += 1
        return self.next_step

    def fail_current(self) -> None:
        """Mevcut adımı başarısız yap."""
        if self.current_step < len(self.steps):
            self.steps[self.current_step].status = "failed"
            self.status = "failed"


# ============================================================================
# REASONING RESULT (Akıl Yürütme Sonucu)
# ============================================================================

@dataclass
class ReasoningResult:
    """
    Akıl yürütme sonucu.
    """
    reasoning_type: ReasoningType

    # Girdi ve çıktı
    premises: List[str] = field(default_factory=list)
    conclusion: str = ""

    # Kalite
    confidence: float = 0.5             # Sonuç güveni
    validity: float = 0.5               # Mantıksal geçerlilik
    soundness: float = 0.5              # Sağlamlık

    # Detay
    reasoning_chain: List[str] = field(default_factory=list)  # Ara adımlar
    assumptions: List[str] = field(default_factory=list)

    # Meta
    processing_time_ms: float = 0.0

    @property
    def quality_score(self) -> float:
        """Toplam kalite skoru."""
        return (self.confidence + self.validity + self.soundness) / 3


# ============================================================================
# SITUATION ASSESSMENT (Durum Değerlendirmesi)
# ============================================================================

@dataclass
class SituationAssessment:
    """
    Mevcut durumun değerlendirmesi.
    """
    # Temel değerlendirme
    safety_level: float = 0.5           # Güvenlik seviyesi (0=tehlikeli, 1=güvenli)
    opportunity_level: float = 0.5      # Fırsat seviyesi
    urgency_level: float = 0.3          # Aciliyet

    # Risk ve fırsat
    risk_level: RiskLevel = RiskLevel.LOW
    opportunity: OpportunityLevel = OpportunityLevel.MODERATE

    # Detaylı faktörler
    identified_risks: List[str] = field(default_factory=list)
    identified_opportunities: List[str] = field(default_factory=list)

    # Önerilen eylemler
    recommended_actions: List[str] = field(default_factory=list)
    actions_to_avoid: List[str] = field(default_factory=list)

    # Beklentiler
    predicted_developments: List[str] = field(default_factory=list)

    # Meta
    assessment_time: datetime = field(default_factory=datetime.now)
    confidence: float = 0.5


# ============================================================================
# COGNITIVE STATE (Biliş Durumu)
# ============================================================================

@dataclass
class CognitiveState:
    """
    Agent'ın biliş durumu - tüm biliş bilgilerinin bütünü.
    """
    # İnançlar
    beliefs: Dict[str, Belief] = field(default_factory=dict)

    # Hedefler
    goals: Dict[str, Goal] = field(default_factory=dict)
    active_goal: Optional[str] = None   # Aktif hedef ID

    # Niyetler
    intentions: Dict[str, Intention] = field(default_factory=dict)
    current_intention: Optional[str] = None

    # Planlar
    plans: Dict[str, Plan] = field(default_factory=dict)
    active_plan: Optional[str] = None

    # Durum değerlendirmesi
    current_assessment: Optional[SituationAssessment] = None

    # Son akıl yürütme
    last_reasoning: Optional[ReasoningResult] = None

    # Meta
    cycle_id: int = 0
    last_update: datetime = field(default_factory=datetime.now)

    # ====================================================================
    # BELIEF OPERATIONS
    # ====================================================================

    def add_belief(self, belief: Belief) -> None:
        """İnanç ekle."""
        self.beliefs[belief.id] = belief
        self.last_update = datetime.now()

    def get_belief(self, belief_id: str) -> Optional[Belief]:
        """İnancı getir."""
        return self.beliefs.get(belief_id)

    def get_beliefs_about(self, subject: str) -> List[Belief]:
        """Belirli bir konu hakkındaki inançları getir."""
        return [b for b in self.beliefs.values() if b.subject == subject]

    def get_strong_beliefs(self, min_confidence: float = 0.7) -> List[Belief]:
        """Güçlü inançları getir."""
        return [b for b in self.beliefs.values() if b.confidence >= min_confidence]

    def remove_weak_beliefs(self, threshold: float = 0.2) -> int:
        """Zayıf inançları temizle."""
        to_remove = [b.id for b in self.beliefs.values() if b.confidence < threshold]
        for bid in to_remove:
            del self.beliefs[bid]
        return len(to_remove)

    # ====================================================================
    # GOAL OPERATIONS
    # ====================================================================

    def add_goal(self, goal: Goal) -> None:
        """Hedef ekle."""
        self.goals[goal.id] = goal
        if goal.status == GoalStatus.ACTIVE and not self.active_goal:
            self.active_goal = goal.id
        self.last_update = datetime.now()

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Hedefi getir."""
        return self.goals.get(goal_id)

    def get_active_goals(self) -> List[Goal]:
        """Aktif hedefleri getir."""
        return [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]

    def get_highest_priority_goal(self) -> Optional[Goal]:
        """En yüksek öncelikli hedefi getir."""
        active = self.get_active_goals()
        if not active:
            return None
        return max(active, key=lambda g: g.importance)

    # ====================================================================
    # INTENTION OPERATIONS
    # ====================================================================

    def add_intention(self, intention: Intention) -> None:
        """Niyet ekle."""
        self.intentions[intention.id] = intention
        self.last_update = datetime.now()

    def get_strongest_intention(self) -> Optional[Intention]:
        """En güçlü niyeti getir."""
        if not self.intentions:
            return None
        return max(self.intentions.values(), key=lambda i: i.priority_score)

    # ====================================================================
    # PLAN OPERATIONS
    # ====================================================================

    def add_plan(self, plan: Plan) -> None:
        """Plan ekle."""
        self.plans[plan.id] = plan
        self.last_update = datetime.now()

    def get_active_plan(self) -> Optional[Plan]:
        """Aktif planı getir."""
        if self.active_plan:
            return self.plans.get(self.active_plan)
        return None

    def activate_plan(self, plan_id: str) -> bool:
        """Planı aktifleştir."""
        if plan_id in self.plans:
            self.active_plan = plan_id
            self.plans[plan_id].status = "executing"
            return True
        return False

    # ====================================================================
    # SUMMARY
    # ====================================================================

    def summary(self) -> Dict[str, Any]:
        """Biliş durumu özeti."""
        return {
            "beliefs_count": len(self.beliefs),
            "strong_beliefs": len(self.get_strong_beliefs()),
            "goals_count": len(self.goals),
            "active_goals": len(self.get_active_goals()),
            "active_goal_id": self.active_goal,
            "intentions_count": len(self.intentions),
            "current_intention": self.current_intention,
            "plans_count": len(self.plans),
            "active_plan": self.active_plan,
            "has_assessment": self.current_assessment is not None,
            "last_update": self.last_update.isoformat(),
        }
