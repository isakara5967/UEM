"""
core/language/dialogue/message_planner.py

MessagePlanner - ActSelectionResult + SituationModel → MessagePlan

Seçilen act'lerden ve durumdan tam mesaj planı oluşturur:
- Content points (ne söylenecek)
- Constraints (kısıtlar)
- Tone (üslup)
- Risk level (risk seviyesi)

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .types import (
    DialogueAct,
    ToneType,
    SituationModel,
    MessagePlan,
    Risk,
    EmotionalState,
    generate_message_plan_id,
)
from .act_selector import ActSelectionResult


class ConstraintSeverity(str, Enum):
    """
    Kısıt ciddiyeti.

    Levels:
    - LOW: Düşük, tercih edilen
    - MEDIUM: Orta, önemli
    - HIGH: Yüksek, zorunlu
    - CRITICAL: Kritik, kesinlikle uyulmalı
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConstraintType(str, Enum):
    """
    Kısıt türleri.

    Types:
    - ETHICAL: Etik kısıtlar
    - STYLE: Üslup kısıtları
    - CONTENT: İçerik kısıtları
    - SAFETY: Güvenlik kısıtları
    - TONE: Ton kısıtları
    """
    ETHICAL = "ethical"
    STYLE = "style"
    CONTENT = "content"
    SAFETY = "safety"
    TONE = "tone"


@dataclass
class ContentPoint:
    """
    İçerik noktası - MessagePlan'da ne söylenecek.

    Attributes:
        key: İçerik anahtarı (örn: "main_response", "empathy", "suggestion")
        value: İçerik değeri / açıklaması
        priority: Öncelik sırası (1 en yüksek)
        required: Zorunlu mu?
    """
    key: str
    value: str
    priority: int = 1
    required: bool = True

    def __post_init__(self):
        """Validate priority."""
        if self.priority < 1:
            raise ValueError(f"Priority must be >= 1, got {self.priority}")


@dataclass
class MessageConstraint:
    """
    Mesaj kısıtı - MessagePlan'da neye dikkat edilmeli.

    Attributes:
        constraint_type: Kısıt türü
        description: Kısıt açıklaması
        severity: Kısıt ciddiyeti
    """
    constraint_type: ConstraintType
    description: str
    severity: ConstraintSeverity = ConstraintSeverity.MEDIUM


@dataclass
class MessagePlannerConfig:
    """
    MessagePlanner konfigürasyonu.

    Attributes:
        max_content_points: Maksimum içerik noktası sayısı
        max_constraints: Maksimum kısıt sayısı
        default_tone: Varsayılan ton
        enable_self_values: Self modülü değerlerini kullan
        enable_constraints: Kısıt üretimini aktif et
        risk_threshold_for_caution: Dikkatli ton için risk eşiği
    """
    max_content_points: int = 10
    max_constraints: int = 5
    default_tone: ToneType = ToneType.NEUTRAL
    enable_self_values: bool = True
    enable_constraints: bool = True
    risk_threshold_for_caution: float = 0.5


class MessagePlanner:
    """
    ActSelectionResult + SituationModel → MessagePlan

    Seçilen act'lerden ve durumdan tam mesaj planı oluşturur.

    Kullanım:
        planner = MessagePlanner()
        plan = planner.plan(act_result, situation)
        print(plan.primary_intent)  # "Kullanıcıya bilgi ver"
        print(plan.tone)  # ToneType.EMPATHIC
        print(plan.content_points)  # ["Empati kur", "Bilgi ver", "Öneri sun"]

        # Güncelleme ile
        updated_plan = planner.update_plan(plan, new_tone=ToneType.FORMAL)
    """

    def __init__(
        self,
        config: Optional[MessagePlannerConfig] = None,
        self_processor: Optional[Any] = None,
        affect_processor: Optional[Any] = None
    ):
        """
        MessagePlanner oluştur.

        Args:
            config: Planner konfigürasyonu
            self_processor: Self modülü (opsiyonel)
            affect_processor: Affect modülü (opsiyonel)
        """
        self.config = config or MessagePlannerConfig()
        self.self_proc = self_processor
        self.affect = affect_processor

        # Act → Content point eşleştirmesi
        self._act_content_map = self._build_act_content_map()
        # Act → Intent açıklaması
        self._act_intent_map = self._build_act_intent_map()
        # Risk → Constraint eşleştirmesi
        self._risk_constraint_map = self._build_risk_constraint_map()

    def plan(
        self,
        act_result: ActSelectionResult,
        situation: SituationModel,
        context: Optional[Dict[str, Any]] = None
    ) -> MessagePlan:
        """
        Ana plan metodu - MessagePlan oluştur.

        Args:
            act_result: Act seçim sonucu
            situation: Durum modeli
            context: Ek bağlam

        Returns:
            MessagePlan: Mesaj planı
        """
        plan_id = generate_message_plan_id()

        # 1. Primary intent belirle
        primary_intent = self._determine_primary_intent(act_result, situation)

        # 2. Tone belirle
        tone = self._determine_tone(act_result, situation)

        # 3. Content points oluştur
        content_points_objs = self._generate_content_points(act_result, situation)
        content_points = [cp.value for cp in content_points_objs]

        # 4. Constraints oluştur
        constraints_objs: List[MessageConstraint] = []
        if self.config.enable_constraints:
            constraints_objs = self._generate_constraints(act_result, situation)
        constraints = [c.description for c in constraints_objs]

        # 5. Risk level hesapla
        risk_level = self._calculate_risk_level(situation)

        # 6. Confidence hesapla
        confidence = self._calculate_confidence(act_result, situation)

        # 7. Dialogue acts listesi
        dialogue_acts = list(act_result.primary_acts)
        if not dialogue_acts:
            dialogue_acts = [DialogueAct.ACKNOWLEDGE]

        return MessagePlan(
            id=plan_id,
            dialogue_acts=dialogue_acts,
            primary_intent=primary_intent,
            tone=tone,
            content_points=content_points[:self.config.max_content_points],
            constraints=constraints[:self.config.max_constraints],
            risk_level=risk_level,
            confidence=confidence,
            situation_id=situation.id,
            context={
                "act_selection_confidence": act_result.confidence,
                "strategy_used": act_result.strategy_used.value,
                **(context or {})
            }
        )

    def update_plan(
        self,
        original_plan: MessagePlan,
        new_tone: Optional[ToneType] = None,
        additional_content_points: Optional[List[str]] = None,
        additional_constraints: Optional[List[str]] = None,
        new_context: Optional[Dict[str, Any]] = None
    ) -> MessagePlan:
        """
        Mevcut planı güncelle (immutable).

        Args:
            original_plan: Orijinal plan
            new_tone: Yeni ton (opsiyonel)
            additional_content_points: Ek içerik noktaları (opsiyonel)
            additional_constraints: Ek kısıtlar (opsiyonel)
            new_context: Ek bağlam (opsiyonel)

        Returns:
            MessagePlan: Güncellenmiş yeni plan
        """
        # Yeni plan ID'si
        new_id = generate_message_plan_id()

        # Tone
        tone = new_tone if new_tone is not None else original_plan.tone

        # Content points
        content_points = list(original_plan.content_points)
        if additional_content_points:
            content_points.extend(additional_content_points)

        # Constraints
        constraints = list(original_plan.constraints)
        if additional_constraints:
            constraints.extend(additional_constraints)

        # Context
        context = dict(original_plan.context)
        context["original_plan_id"] = original_plan.id
        if new_context:
            context.update(new_context)

        return MessagePlan(
            id=new_id,
            dialogue_acts=list(original_plan.dialogue_acts),
            primary_intent=original_plan.primary_intent,
            tone=tone,
            content_points=content_points[:self.config.max_content_points],
            constraints=constraints[:self.config.max_constraints],
            risk_level=original_plan.risk_level,
            confidence=original_plan.confidence,
            situation_id=original_plan.situation_id,
            context=context
        )

    def _determine_primary_intent(
        self,
        act_result: ActSelectionResult,
        situation: SituationModel
    ) -> str:
        """
        Primary intent açıklamasını belirle.

        Args:
            act_result: Act seçim sonucu
            situation: Durum modeli

        Returns:
            str: Intent açıklaması
        """
        if not act_result.primary_acts:
            return "Kullanıcı mesajını kabul et"

        primary_act = act_result.primary_acts[0]

        # Act'e göre intent açıklaması
        intent_desc = self._act_intent_map.get(
            primary_act,
            "Kullanıcıyla etkileşim kur"
        )

        # Situation'dan ek bağlam
        if situation.intentions:
            user_goal = situation.intentions[0].goal
            intent_desc = f"{intent_desc} ({user_goal} isteği için)"

        return intent_desc

    def _determine_tone(
        self,
        act_result: ActSelectionResult,
        situation: SituationModel
    ) -> ToneType:
        """
        Mesaj tonunu belirle.

        Args:
            act_result: Act seçim sonucu
            situation: Durum modeli

        Returns:
            ToneType: Belirlenen ton
        """
        # Risk yüksekse dikkatli ton
        if situation.has_high_risk(self.config.risk_threshold_for_caution):
            return ToneType.CAUTIOUS

        # Emotional state'e göre
        if situation.emotional_state:
            valence = situation.emotional_state.valence

            # Çok negatif → Empatik/Destekleyici
            if valence < -0.5:
                return ToneType.SUPPORTIVE
            elif valence < -0.2:
                return ToneType.EMPATHIC

            # Pozitif → Coşkulu (hafif) veya casual
            if valence > 0.5:
                return ToneType.ENTHUSIASTIC
            elif valence > 0.2:
                return ToneType.CASUAL

        # Act'e göre ton
        if act_result.primary_acts:
            primary_act = act_result.primary_acts[0]

            # Duygusal act'ler → Empatik
            emotional_acts = {
                DialogueAct.EMPATHIZE,
                DialogueAct.COMFORT,
                DialogueAct.ENCOURAGE
            }
            if primary_act in emotional_acts:
                return ToneType.EMPATHIC

            # Uyarı act'leri → Ciddi
            if primary_act == DialogueAct.WARN:
                return ToneType.SERIOUS

            # Sınır act'leri → Resmi
            boundary_acts = {
                DialogueAct.REFUSE,
                DialogueAct.LIMIT,
                DialogueAct.DEFLECT
            }
            if primary_act in boundary_acts:
                return ToneType.FORMAL

        # Topic'e göre
        formal_topics = {"work", "health", "education"}
        if situation.topic_domain in formal_topics:
            return ToneType.FORMAL

        return self.config.default_tone

    def _generate_content_points(
        self,
        act_result: ActSelectionResult,
        situation: SituationModel
    ) -> List[ContentPoint]:
        """
        İçerik noktaları oluştur.

        Args:
            act_result: Act seçim sonucu
            situation: Durum modeli

        Returns:
            List[ContentPoint]: İçerik noktaları
        """
        content_points = []
        priority = 1

        # Primary act'ler için içerik noktaları
        for act in act_result.primary_acts:
            if act in self._act_content_map:
                content_info = self._act_content_map[act]
                content_points.append(ContentPoint(
                    key=content_info["key"],
                    value=content_info["value"],
                    priority=priority,
                    required=True
                ))
                priority += 1

        # Secondary act'ler için (required=False)
        for act in act_result.secondary_acts:
            if act in self._act_content_map:
                content_info = self._act_content_map[act]
                content_points.append(ContentPoint(
                    key=content_info["key"],
                    value=content_info["value"],
                    priority=priority,
                    required=False
                ))
                priority += 1

        # Risk varsa uyarı içeriği ekle
        if situation.risks:
            highest_risk = situation.get_highest_risk()
            if highest_risk and highest_risk.level > 0.5:
                content_points.append(ContentPoint(
                    key="risk_awareness",
                    value=f"Risk konusunda dikkatli ol: {highest_risk.category}",
                    priority=priority,
                    required=True
                ))
                priority += 1

        # Duygusal durum varsa empati içeriği ekle
        if situation.emotional_state and situation.emotional_state.valence < -0.3:
            # Zaten empati act'i yoksa ekle
            has_empathy = any(
                cp.key == "empathy" for cp in content_points
            )
            if not has_empathy:
                content_points.append(ContentPoint(
                    key="emotional_support",
                    value="Kullanıcının duygusal durumunu kabul et",
                    priority=1,  # Yüksek öncelik
                    required=True
                ))

        # Sırala
        content_points.sort(key=lambda x: x.priority)

        return content_points[:self.config.max_content_points]

    def _generate_constraints(
        self,
        act_result: ActSelectionResult,
        situation: SituationModel
    ) -> List[MessageConstraint]:
        """
        Kısıtları oluştur.

        Args:
            act_result: Act seçim sonucu
            situation: Durum modeli

        Returns:
            List[MessageConstraint]: Kısıtlar
        """
        constraints = []

        # Risk'lere göre kısıtlar
        for risk in situation.risks:
            if risk.category in self._risk_constraint_map:
                constraint_info = self._risk_constraint_map[risk.category]

                # Risk level'a göre severity
                if risk.level > 0.8:
                    severity = ConstraintSeverity.CRITICAL
                elif risk.level > 0.5:
                    severity = ConstraintSeverity.HIGH
                elif risk.level > 0.3:
                    severity = ConstraintSeverity.MEDIUM
                else:
                    severity = ConstraintSeverity.LOW

                constraints.append(MessageConstraint(
                    constraint_type=constraint_info["type"],
                    description=constraint_info["description"],
                    severity=severity
                ))

        # Act'lere göre kısıtlar
        if DialogueAct.REFUSE in act_result.primary_acts:
            constraints.append(MessageConstraint(
                constraint_type=ConstraintType.STYLE,
                description="Nazik ve açıklayıcı bir şekilde reddet",
                severity=ConstraintSeverity.HIGH
            ))

        if DialogueAct.WARN in act_result.primary_acts:
            constraints.append(MessageConstraint(
                constraint_type=ConstraintType.SAFETY,
                description="Uyarıyı net ve anlaşılır yap",
                severity=ConstraintSeverity.HIGH
            ))

        if DialogueAct.EMPATHIZE in act_result.primary_acts:
            constraints.append(MessageConstraint(
                constraint_type=ConstraintType.TONE,
                description="Samimi ve anlayışlı ol",
                severity=ConstraintSeverity.MEDIUM
            ))

        # Etik kısıtlar (her zaman)
        constraints.append(MessageConstraint(
            constraint_type=ConstraintType.ETHICAL,
            description="Dürüst ve şeffaf ol",
            severity=ConstraintSeverity.HIGH
        ))

        # Self values (eğer aktifse)
        if self.config.enable_self_values:
            constraints.append(MessageConstraint(
                constraint_type=ConstraintType.ETHICAL,
                description="UEM değerlerine uygun davran",
                severity=ConstraintSeverity.MEDIUM
            ))

        return constraints[:self.config.max_constraints]

    def _calculate_risk_level(self, situation: SituationModel) -> float:
        """
        Plan risk seviyesini hesapla.

        Args:
            situation: Durum modeli

        Returns:
            float: Risk seviyesi (0.0-1.0)
        """
        if not situation.risks:
            return 0.0

        # En yüksek riski al
        highest = situation.get_highest_risk()
        if highest:
            return highest.level

        return 0.0

    def _calculate_confidence(
        self,
        act_result: ActSelectionResult,
        situation: SituationModel
    ) -> float:
        """
        Plan güvenilirliğini hesapla.

        Args:
            act_result: Act seçim sonucu
            situation: Durum modeli

        Returns:
            float: Güven skoru (0.0-1.0)
        """
        # Act selection confidence (%40)
        act_confidence = act_result.confidence * 0.4

        # Understanding score (%30)
        understanding = situation.understanding_score * 0.3

        # Risk inverse bonus (%20) - düşük risk = yüksek güven
        risk_level = self._calculate_risk_level(situation)
        risk_bonus = (1.0 - risk_level) * 0.2

        # Content point coverage (%10)
        has_content = len(act_result.primary_acts) > 0
        content_bonus = 0.1 if has_content else 0.0

        confidence = act_confidence + understanding + risk_bonus + content_bonus
        return min(1.0, max(0.0, confidence))

    def _build_act_content_map(self) -> Dict[DialogueAct, Dict[str, str]]:
        """
        Act → Content point eşleştirmesi.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            DialogueAct.INFORM: {
                "key": "information",
                "value": "İstenen bilgiyi ver"
            },
            DialogueAct.EXPLAIN: {
                "key": "explanation",
                "value": "Konuyu detaylı açıkla"
            },
            DialogueAct.CLARIFY: {
                "key": "clarification",
                "value": "Belirsiz noktaları netleştir"
            },
            DialogueAct.ASK: {
                "key": "question",
                "value": "Gerekli soruyu sor"
            },
            DialogueAct.CONFIRM: {
                "key": "confirmation",
                "value": "Doğrulama iste"
            },
            DialogueAct.EMPATHIZE: {
                "key": "empathy",
                "value": "Duygularını anladığını göster"
            },
            DialogueAct.ENCOURAGE: {
                "key": "encouragement",
                "value": "Cesaretlendirici mesaj ver"
            },
            DialogueAct.COMFORT: {
                "key": "comfort",
                "value": "Teselli et ve rahatlat"
            },
            DialogueAct.SUGGEST: {
                "key": "suggestion",
                "value": "Öneri sun"
            },
            DialogueAct.WARN: {
                "key": "warning",
                "value": "Risk/tehlike konusunda uyar"
            },
            DialogueAct.ADVISE: {
                "key": "advice",
                "value": "Tavsiye ver"
            },
            DialogueAct.REFUSE: {
                "key": "refusal",
                "value": "Nazikçe reddet ve nedenini açıkla"
            },
            DialogueAct.LIMIT: {
                "key": "limitation",
                "value": "Kapsamı/sınırları belirt"
            },
            DialogueAct.DEFLECT: {
                "key": "deflection",
                "value": "Konuyu uygun şekilde yönlendir"
            },
            DialogueAct.ACKNOWLEDGE: {
                "key": "acknowledgment",
                "value": "Mesajı anladığını göster"
            },
            DialogueAct.APOLOGIZE: {
                "key": "apology",
                "value": "Uygun durumda özür dile"
            },
            DialogueAct.THANK: {
                "key": "thanks",
                "value": "Teşekkür et"
            }
        }

    def _build_act_intent_map(self) -> Dict[DialogueAct, str]:
        """
        Act → Intent açıklaması eşleştirmesi.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            DialogueAct.INFORM: "Kullanıcıyı bilgilendir",
            DialogueAct.EXPLAIN: "Kullanıcıya açıkla",
            DialogueAct.CLARIFY: "Belirsizliği gider",
            DialogueAct.ASK: "Kullanıcıya soru sor",
            DialogueAct.CONFIRM: "Doğrulama al",
            DialogueAct.EMPATHIZE: "Empati kur",
            DialogueAct.ENCOURAGE: "Kullanıcıyı cesaretlendir",
            DialogueAct.COMFORT: "Kullanıcıyı teselli et",
            DialogueAct.SUGGEST: "Öneri sun",
            DialogueAct.WARN: "Kullanıcıyı uyar",
            DialogueAct.ADVISE: "Tavsiye ver",
            DialogueAct.REFUSE: "İsteği reddet",
            DialogueAct.LIMIT: "Kapsamı sınırla",
            DialogueAct.DEFLECT: "Konuyu yönlendir",
            DialogueAct.ACKNOWLEDGE: "Kullanıcı mesajını kabul et",
            DialogueAct.APOLOGIZE: "Özür dile",
            DialogueAct.THANK: "Teşekkür et"
        }

    def _build_risk_constraint_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Risk → Constraint eşleştirmesi.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            "safety": {
                "type": ConstraintType.SAFETY,
                "description": "Güvenlik öncelikli, profesyonel yardım yönlendir"
            },
            "emotional": {
                "type": ConstraintType.TONE,
                "description": "Duygusal hassasiyet ile yaklaş"
            },
            "ethical": {
                "type": ConstraintType.ETHICAL,
                "description": "Etik sınırları aşma, alternatif öner"
            },
            "relational": {
                "type": ConstraintType.STYLE,
                "description": "Tarafsız ve dengeli ol"
            }
        }
