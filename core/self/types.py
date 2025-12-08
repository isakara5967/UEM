"""
UEM v2 - Self Types

Benlik modulunun temel veri yapilari.
Identity, Value, Need, PersonalGoal ve SelfModel tanimlari.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class IdentityAspect(str, Enum):
    """Kimlik boyutlari."""
    CORE = "core"                    # Temel kimlik (degismez)
    SOCIAL = "social"                # Sosyal roller
    PROFESSIONAL = "professional"    # Mesleki/gorev kimligi
    RELATIONAL = "relational"        # Iliskisel kimlik
    ASPIRATIONAL = "aspirational"    # Olmak istedigim


class ValueCategory(str, Enum):
    """Deger kategorileri."""
    TERMINAL = "terminal"            # Ulas sonuc (mutluluk, bilgelik)
    INSTRUMENTAL = "instrumental"    # Arasal (durustluk, cesaret)
    MORAL = "moral"                  # Etik degerler
    AESTHETIC = "aesthetic"          # Estetik degerler
    EPISTEMIC = "epistemic"          # Bilgisel degerler (hakikat, bilgi)


class ValuePriority(str, Enum):
    """Deger onceligi."""
    SACRED = "sacred"                # Dokunulmaz, pazarlik edilemez
    CORE = "core"                    # Temel, cok onemli
    IMPORTANT = "important"          # Onemli
    PREFERRED = "preferred"          # Tercih edilen
    OPTIONAL = "optional"            # Opsiyonel


class NeedLevel(str, Enum):
    """Maslow ihtiyac seviyeleri."""
    PHYSIOLOGICAL = "physiological"  # Fizyolojik (enerji, kaynak)
    SAFETY = "safety"                # Guvenlik
    BELONGING = "belonging"          # Ait olma, sevgi
    ESTEEM = "esteem"                # Sayginlik
    SELF_ACTUALIZATION = "self_actualization"  # Kendini gerceklestirme


class NeedStatus(str, Enum):
    """Ihtiyac durumu."""
    SATISFIED = "satisfied"          # Karsilanmis
    PARTIAL = "partial"              # Kismen karsilanmis
    UNSATISFIED = "unsatisfied"      # Karsilanmamis
    CRITICAL = "critical"            # Kritik eksik


class GoalDomain(str, Enum):
    """Kisisel hedef alanlari."""
    GROWTH = "growth"                # Gelisim
    RELATIONSHIP = "relationship"    # Iliski
    CONTRIBUTION = "contribution"    # Katki
    MASTERY = "mastery"              # Ustalasma
    AUTONOMY = "autonomy"            # Ozerklik
    MEANING = "meaning"              # Anlam


class IntegrityStatus(str, Enum):
    """Tutarlilik durumu."""
    ALIGNED = "aligned"              # Tamamen uyumlu
    MINOR_CONFLICT = "minor_conflict"  # Kucuk catisma
    MAJOR_CONFLICT = "major_conflict"  # Buyuk catisma
    CRISIS = "crisis"                # Kimlik krizi


class NarrativeType(str, Enum):
    """Hikaye turleri."""
    ORIGIN = "origin"                # Koken hikayesi
    CHALLENGE = "challenge"          # Zorluk/basari hikayesi
    TRANSFORMATION = "transformation"  # Donusum
    LESSON = "lesson"                # Ders cikarilan deneyim
    RELATIONSHIP = "relationship"    # Iliski hikayesi


# ============================================================================
# VALUE (Deger)
# ============================================================================

@dataclass
class Value:
    """
    Bir deger temsili.

    Value = Agent'in onemli buldugu, davranilarini yonlendiren ilke
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tanim
    name: str = ""
    description: str = ""
    category: ValueCategory = ValueCategory.INSTRUMENTAL

    # Oncelik ve onem
    priority: ValuePriority = ValuePriority.IMPORTANT
    weight: float = 0.5              # 0.0-1.0 agirlik

    # Iliskili kavramlar
    related_values: List[str] = field(default_factory=list)
    conflicting_values: List[str] = field(default_factory=list)

    # Davranisal gostergeler
    behavioral_indicators: List[str] = field(default_factory=list)

    # Zaman
    acquired_at: datetime = field(default_factory=datetime.now)
    last_expressed: Optional[datetime] = None

    # Meta
    expression_count: int = 0        # Kac kez davranisa yansidi
    violation_count: int = 0         # Kac kez ihlal edildi

    @property
    def priority_weight(self) -> float:
        """Oncelik bazli agirlik."""
        weights = {
            ValuePriority.SACRED: 1.0,
            ValuePriority.CORE: 0.8,
            ValuePriority.IMPORTANT: 0.6,
            ValuePriority.PREFERRED: 0.4,
            ValuePriority.OPTIONAL: 0.2,
        }
        return weights.get(self.priority, 0.5) * self.weight

    @property
    def integrity_score(self) -> float:
        """Bu deger icin tutarlilik skoru."""
        total = self.expression_count + self.violation_count
        if total == 0:
            return 1.0
        return self.expression_count / total

    def express(self) -> None:
        """Degeri ifade et (davranisa yansit)."""
        self.expression_count += 1
        self.last_expressed = datetime.now()

    def violate(self) -> None:
        """Degeri ihlal et."""
        self.violation_count += 1


# ============================================================================
# NEED (Ihtiyac)
# ============================================================================

@dataclass
class Need:
    """
    Bir ihtiyac temsili (Maslow hiyerarsisi).

    Need = Agent'in karsilanmasi gereken temel ihtiyaci
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tanim
    name: str = ""
    description: str = ""
    level: NeedLevel = NeedLevel.SAFETY

    # Durum
    satisfaction: float = 0.5        # 0.0-1.0 karsilanma orani
    status: NeedStatus = NeedStatus.PARTIAL

    # Agirlik
    importance: float = 0.5          # Bu ihtiyacin onemi
    urgency: float = 0.3             # Aciliyet

    # Esik degerleri
    critical_threshold: float = 0.2  # Bu altinda kritik
    satisfied_threshold: float = 0.7 # Bu ustunde karsilanmis

    # Zaman
    last_satisfied: Optional[datetime] = None
    deprivation_duration: float = 0.0  # Saat cinsinden

    # Meta
    drive_strength: float = 0.5      # Motivasyon gucu

    @property
    def priority_score(self) -> float:
        """Oncelik skoru = (1 - satisfaction) * importance * level_weight."""
        level_weights = {
            NeedLevel.PHYSIOLOGICAL: 1.0,
            NeedLevel.SAFETY: 0.9,
            NeedLevel.BELONGING: 0.7,
            NeedLevel.ESTEEM: 0.5,
            NeedLevel.SELF_ACTUALIZATION: 0.3,
        }
        weight = level_weights.get(self.level, 0.5)
        deficit = 1.0 - self.satisfaction
        return deficit * self.importance * weight * (1 + self.urgency)

    def update_satisfaction(self, delta: float) -> None:
        """Karsilanma oranini guncelle."""
        self.satisfaction = max(0.0, min(1.0, self.satisfaction + delta))
        self._update_status()

    def _update_status(self) -> None:
        """Durumu guncelle."""
        if self.satisfaction < self.critical_threshold:
            self.status = NeedStatus.CRITICAL
        elif self.satisfaction < 0.5:
            self.status = NeedStatus.UNSATISFIED
        elif self.satisfaction < self.satisfied_threshold:
            self.status = NeedStatus.PARTIAL
        else:
            self.status = NeedStatus.SATISFIED
            self.last_satisfied = datetime.now()

    def deprive(self, hours: float = 1.0) -> None:
        """Ihtiyaci mahrum birak (zaman gecti)."""
        self.deprivation_duration += hours
        # Deprivasyon ile tatmin azalir
        decay = 0.01 * hours * (1.0 - self.importance)
        self.update_satisfaction(-decay)

    def satisfy(self, amount: float = 0.3) -> None:
        """Ihtiyaci karila."""
        self.update_satisfaction(amount)
        self.deprivation_duration = 0.0


# ============================================================================
# PERSONAL GOAL (Kisisel Hedef)
# ============================================================================

@dataclass
class PersonalGoal:
    """
    Kisisel bir hedef temsili.

    PersonalGoal = Agent'in bireysel gelisim/anlam hedefi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tanim
    name: str = ""
    description: str = ""
    domain: GoalDomain = GoalDomain.GROWTH

    # Iliskiler
    related_values: List[str] = field(default_factory=list)
    related_needs: List[str] = field(default_factory=list)

    # Ilerleme
    progress: float = 0.0            # 0.0-1.0
    milestones: List[str] = field(default_factory=list)
    achieved_milestones: List[str] = field(default_factory=list)

    # Motivasyon
    intrinsic_motivation: float = 0.7  # Icsel motivasyon
    extrinsic_motivation: float = 0.3  # Disal motivasyon
    commitment: float = 0.5          # Baglilik

    # Zaman
    created_at: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    last_progress: Optional[datetime] = None

    # Durum
    is_active: bool = True

    @property
    def total_motivation(self) -> float:
        """Toplam motivasyon."""
        # Icsel motivasyon daha degerli
        return (self.intrinsic_motivation * 0.7 +
                self.extrinsic_motivation * 0.3) * self.commitment

    @property
    def milestone_progress(self) -> float:
        """Milestone bazli ilerleme."""
        if not self.milestones:
            return self.progress
        return len(self.achieved_milestones) / len(self.milestones)

    def achieve_milestone(self, milestone: str) -> None:
        """Milestone tamamla."""
        if milestone in self.milestones and milestone not in self.achieved_milestones:
            self.achieved_milestones.append(milestone)
            self.progress = self.milestone_progress
            self.last_progress = datetime.now()

    def update_progress(self, new_progress: float) -> None:
        """Ilerlemeyi guncelle."""
        self.progress = max(0.0, min(1.0, new_progress))
        self.last_progress = datetime.now()


# ============================================================================
# IDENTITY TRAIT (Kimlik Ozelligi)
# ============================================================================

@dataclass
class IdentityTrait:
    """
    Bir kimlik ozelligi.

    IdentityTrait = Agent'in kendini tanimlayan bir ozelligi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tanim
    name: str = ""                   # Ornegin: "Yardimci", "Merakli"
    description: str = ""
    aspect: IdentityAspect = IdentityAspect.CORE

    # Guc ve kararlilik
    strength: float = 0.5            # 0.0-1.0 ozelligin gucu
    stability: float = 0.7           # 0.0-1.0 zaman icinde kararlilik

    # Iliskili degerler
    supporting_values: List[str] = field(default_factory=list)

    # Davranisal etki
    behavioral_impact: Dict[str, float] = field(default_factory=dict)

    # Zaman
    formed_at: datetime = field(default_factory=datetime.now)
    last_reinforced: Optional[datetime] = None

    # Meta
    reinforcement_count: int = 0
    challenge_count: int = 0

    @property
    def resilience(self) -> float:
        """Dayaniklilik = strength * stability."""
        return self.strength * self.stability

    def reinforce(self, amount: float = 0.1) -> None:
        """Ozelligi guclendir."""
        self.strength = min(1.0, self.strength + amount)
        self.stability = min(1.0, self.stability + amount * 0.5)
        self.reinforcement_count += 1
        self.last_reinforced = datetime.now()

    def challenge(self, amount: float = 0.1) -> None:
        """Ozelligi sorgula."""
        self.challenge_count += 1
        # Stabilite yuksekse etki az
        impact = amount * (1.0 - self.stability * 0.5)
        self.strength = max(0.0, self.strength - impact)


# ============================================================================
# IDENTITY (Kimlik)
# ============================================================================

@dataclass
class Identity:
    """
    Kimlik temsili.

    Identity = Agent'in "Ben kimim?" sorusunun cevabi
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Temel tanim
    name: str = ""                   # Agent'in ismi/tanimlayicisi
    description: str = ""            # Kisa tanim

    # Kimlik ozellikleri
    traits: Dict[str, IdentityTrait] = field(default_factory=dict)
    core_traits: List[str] = field(default_factory=list)  # Trait ID'leri

    # Roller
    roles: List[str] = field(default_factory=list)  # "Yardimci", "Ogretmen" vb.
    primary_role: Optional[str] = None

    # Sinirlar ve yetenekler
    capabilities: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # Meta
    formation_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_trait(self, trait: IdentityTrait) -> None:
        """Kimlik ozelligi ekle."""
        self.traits[trait.id] = trait
        if trait.aspect == IdentityAspect.CORE:
            self.core_traits.append(trait.id)
        self.last_updated = datetime.now()

    def get_trait(self, trait_id: str) -> Optional[IdentityTrait]:
        """Ozelligi getir."""
        return self.traits.get(trait_id)

    def get_traits_by_aspect(self, aspect: IdentityAspect) -> List[IdentityTrait]:
        """Belirli bir boyuttaki ozellikleri getir."""
        return [t for t in self.traits.values() if t.aspect == aspect]

    def get_core_identity(self) -> List[IdentityTrait]:
        """Temel kimlik ozelliklerini getir."""
        return [self.traits[tid] for tid in self.core_traits if tid in self.traits]

    def add_role(self, role: str) -> None:
        """Rol ekle."""
        if role not in self.roles:
            self.roles.append(role)
            if not self.primary_role:
                self.primary_role = role
            self.last_updated = datetime.now()

    @property
    def identity_strength(self) -> float:
        """Kimlik gucu = core trait'lerin ortalama strength'i."""
        core = self.get_core_identity()
        if not core:
            return 0.5
        return sum(t.strength for t in core) / len(core)

    @property
    def identity_stability(self) -> float:
        """Kimlik kararliligi = core trait'lerin ortalama stability'si."""
        core = self.get_core_identity()
        if not core:
            return 0.5
        return sum(t.stability for t in core) / len(core)


# ============================================================================
# NARRATIVE ELEMENT (Hikaye Ogesi)
# ============================================================================

@dataclass
class NarrativeElement:
    """
    Kisisel hikayedeki bir oge.

    NarrativeElement = Agent'in gecmisindeki anlamli bir deneyim
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tanim
    title: str = ""
    narrative_type: NarrativeType = NarrativeType.LESSON
    summary: str = ""

    # Icerik
    key_events: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)  # Iliskili agent ID'leri

    # Anlam
    meaning: str = ""                # Bu deneyimin anlami
    lessons_learned: List[str] = field(default_factory=list)

    # Duygusal boyut
    emotional_valence: float = 0.0   # -1 negatif, +1 pozitif
    emotional_intensity: float = 0.5 # 0-1 yoaunluk

    # Etki
    identity_impact: Dict[str, float] = field(default_factory=dict)  # trait_id -> impact
    value_reinforcement: List[str] = field(default_factory=list)  # value ID'leri

    # Zaman
    occurred_at: datetime = field(default_factory=datetime.now)
    remembered_count: int = 0

    @property
    def significance(self) -> float:
        """Bu hikaenin onemi."""
        emotional_factor = abs(self.emotional_valence) * self.emotional_intensity
        impact_factor = sum(abs(v) for v in self.identity_impact.values()) / max(1, len(self.identity_impact))
        return (emotional_factor + impact_factor) / 2


# ============================================================================
# SELF STATE (Benlik Durumu)
# ============================================================================

@dataclass
class SelfState:
    """
    Agent'in benlik durumu - tum benlik bilgilerinin butunu.
    """
    # Kimlik
    identity: Identity = field(default_factory=Identity)

    # Degerler
    values: Dict[str, Value] = field(default_factory=dict)
    core_values: List[str] = field(default_factory=list)  # En onemli deger ID'leri

    # Ihtiyaclar
    needs: Dict[str, Need] = field(default_factory=dict)

    # Kisisel hedefler
    personal_goals: Dict[str, PersonalGoal] = field(default_factory=dict)

    # Hikaye/Narratif
    narrative: List[NarrativeElement] = field(default_factory=list)

    # Tutarlilik
    integrity_status: IntegrityStatus = IntegrityStatus.ALIGNED
    integrity_score: float = 1.0     # 0.0-1.0 genel tutarlilik

    # Etik uyum
    ethical_alignment: float = 1.0   # 0.0-1.0 etik kurallara uyum

    # Meta
    last_update: datetime = field(default_factory=datetime.now)

    # ====================================================================
    # VALUE OPERATIONS
    # ====================================================================

    def add_value(self, value: Value) -> None:
        """Deger ekle."""
        self.values[value.id] = value
        if value.priority in (ValuePriority.SACRED, ValuePriority.CORE):
            self.core_values.append(value.id)
        self.last_update = datetime.now()

    def get_value(self, value_id: str) -> Optional[Value]:
        """Degeri getir."""
        return self.values.get(value_id)

    def get_core_values(self) -> List[Value]:
        """Temel degerleri getir."""
        return [self.values[vid] for vid in self.core_values if vid in self.values]

    def get_values_by_category(self, category: ValueCategory) -> List[Value]:
        """Kategoriye gore degerleri getir."""
        return [v for v in self.values.values() if v.category == category]

    # ====================================================================
    # NEED OPERATIONS
    # ====================================================================

    def add_need(self, need: Need) -> None:
        """Ihtiyac ekle."""
        self.needs[need.id] = need
        self.last_update = datetime.now()

    def get_need(self, need_id: str) -> Optional[Need]:
        """Ihtiyaci getir."""
        return self.needs.get(need_id)

    def get_needs_by_level(self, level: NeedLevel) -> List[Need]:
        """Seviyeye gore ihtiyaclari getir."""
        return [n for n in self.needs.values() if n.level == level]

    def get_unsatisfied_needs(self) -> List[Need]:
        """Karsilanmamis ihtiyaclari getir."""
        return [n for n in self.needs.values()
                if n.status in (NeedStatus.UNSATISFIED, NeedStatus.CRITICAL)]

    def get_critical_needs(self) -> List[Need]:
        """Kritik ihtiyaclari getir."""
        return [n for n in self.needs.values() if n.status == NeedStatus.CRITICAL]

    def get_most_pressing_need(self) -> Optional[Need]:
        """En acil ihtiyaci getir."""
        if not self.needs:
            return None
        return max(self.needs.values(), key=lambda n: n.priority_score)

    # ====================================================================
    # PERSONAL GOAL OPERATIONS
    # ====================================================================

    def add_personal_goal(self, goal: PersonalGoal) -> None:
        """Kisisel hedef ekle."""
        self.personal_goals[goal.id] = goal
        self.last_update = datetime.now()

    def get_personal_goal(self, goal_id: str) -> Optional[PersonalGoal]:
        """Kisisel hedefi getir."""
        return self.personal_goals.get(goal_id)

    def get_active_personal_goals(self) -> List[PersonalGoal]:
        """Aktif kisisel hedefleri getir."""
        return [g for g in self.personal_goals.values() if g.is_active]

    # ====================================================================
    # NARRATIVE OPERATIONS
    # ====================================================================

    def add_narrative_element(self, element: NarrativeElement) -> None:
        """Hikaye ogesi ekle."""
        self.narrative.append(element)
        element.remembered_count += 1
        self.last_update = datetime.now()

    def get_significant_narratives(self, min_significance: float = 0.5) -> List[NarrativeElement]:
        """Onemli hikayeleri getir."""
        return [n for n in self.narrative if n.significance >= min_significance]

    # ====================================================================
    # INTEGRITY OPERATIONS
    # ====================================================================

    def check_integrity(self) -> IntegrityStatus:
        """Tutarliligi kontrol et."""
        # Deger tutarliligi
        value_scores = [v.integrity_score for v in self.values.values()]
        avg_value_integrity = sum(value_scores) / len(value_scores) if value_scores else 1.0

        # Kimlik tutarliligi
        identity_stability = self.identity.identity_stability

        # Genel skor
        self.integrity_score = (avg_value_integrity + identity_stability) / 2

        if self.integrity_score >= 0.8:
            self.integrity_status = IntegrityStatus.ALIGNED
        elif self.integrity_score >= 0.6:
            self.integrity_status = IntegrityStatus.MINOR_CONFLICT
        elif self.integrity_score >= 0.4:
            self.integrity_status = IntegrityStatus.MAJOR_CONFLICT
        else:
            self.integrity_status = IntegrityStatus.CRISIS

        return self.integrity_status

    # ====================================================================
    # SUMMARY
    # ====================================================================

    def summary(self) -> Dict[str, Any]:
        """Benlik durumu ozeti."""
        return {
            "identity_name": self.identity.name,
            "identity_strength": self.identity.identity_strength,
            "identity_stability": self.identity.identity_stability,
            "roles": self.identity.roles,
            "values_count": len(self.values),
            "core_values_count": len(self.core_values),
            "needs_count": len(self.needs),
            "unsatisfied_needs": len(self.get_unsatisfied_needs()),
            "critical_needs": len(self.get_critical_needs()),
            "personal_goals_count": len(self.personal_goals),
            "active_goals": len(self.get_active_personal_goals()),
            "narrative_elements": len(self.narrative),
            "integrity_status": self.integrity_status.value,
            "integrity_score": self.integrity_score,
            "ethical_alignment": self.ethical_alignment,
            "last_update": self.last_update.isoformat(),
        }
