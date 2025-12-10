"""
core/language/pipeline/thought_to_speech.py

ThoughtToSpeechPipeline - Tam pipeline orkestratoru.

Input -> SituationModel -> DialogueAct -> MessagePlan -> Risk -> Construction -> Output

Tum bilesenleri entegre eder:
- SituationBuilder
- DialogueActSelector
- MessagePlanner
- RiskScorer
- InternalApprover
- ConstructionSelector
- ConstructionRealizer
- SelfCritique

UEM v2 - Thought-to-Speech Pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from ..dialogue.types import (
    SituationModel,
    MessagePlan,
    DialogueAct,
)
from ..dialogue.situation_builder import SituationBuilder, SituationBuilderConfig
from ..dialogue.act_selector import (
    DialogueActSelector,
    ActSelectorConfig,
    ActSelectionResult,
)
from ..dialogue.message_planner import MessagePlanner, MessagePlannerConfig
from ..risk.types import RiskAssessment, RiskLevel
from ..risk.scorer import RiskScorer, RiskScorerConfig
from ..risk.approver import InternalApprover, InternalApproverConfig, ApprovalResult
from ..construction.types import Construction
from ..construction.grammar import ConstructionGrammar, ConstructionGrammarConfig
from ..construction.selector import ConstructionSelector, ConstructionSelectorConfig
from ..construction.realizer import (
    ConstructionRealizer,
    ConstructionRealizerConfig,
    RealizationResult,
)
from ..conversation import ContextManager
from .config import PipelineConfig
from .self_critique import SelfCritique, CritiqueResult


def generate_pipeline_result_id() -> str:
    """Generate unique pipeline result ID."""
    return f"pr_{uuid.uuid4().hex[:12]}"


@dataclass
class PipelineResult:
    """
    Pipeline sonucu.

    Attributes:
        success: Pipeline basarili mi?
        output: Uretilen cikti metni
        situation: Durum modeli
        act_selection: Act secim sonucu
        message_plan: Mesaj plani
        risk_assessment: Risk degerlendirmesi
        approval: Onay sonucu
        constructions_used: Kullanilan construction'lar
        critique_result: Self-critique sonucu (opsiyonel)
        metadata: Ek metadata
        error: Hata mesaji (basarisiz ise)
        created_at: Olusturulma zamani
    """
    success: bool
    output: str
    situation: Optional[SituationModel] = None
    act_selection: Optional[ActSelectionResult] = None
    message_plan: Optional[MessagePlan] = None
    risk_assessment: Optional[RiskAssessment] = None
    approval: Optional[ApprovalResult] = None
    constructions_used: List[Construction] = field(default_factory=list)
    critique_result: Optional[CritiqueResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def id(self) -> str:
        """Result ID."""
        return self.metadata.get("id", generate_pipeline_result_id())

    @property
    def is_approved(self) -> bool:
        """Onaylandi mi?"""
        return self.approval is not None and self.approval.is_approved

    @property
    def risk_level(self) -> Optional[RiskLevel]:
        """Risk seviyesi."""
        return self.risk_assessment.level if self.risk_assessment else None

    @property
    def was_revised(self) -> bool:
        """Revize edildi mi?"""
        return (
            self.critique_result is not None
            and self.critique_result.revised_output is not None
        )

    @classmethod
    def failure(
        cls,
        error: str,
        fallback_output: str = "Bir hata olustu."
    ) -> "PipelineResult":
        """Hata sonucu olustur."""
        return cls(
            success=False,
            output=fallback_output,
            error=error,
            metadata={"id": generate_pipeline_result_id()}
        )


class ThoughtToSpeechPipeline:
    """
    Tam pipeline: Input -> SituationModel -> DialogueAct -> MessagePlan -> Risk -> Construction -> Output

    Tum bilesenleri orkestre eder.

    Kullanim:
        pipeline = ThoughtToSpeechPipeline()
        result = pipeline.process("Merhaba, nasilsin?")

        if result.success:
            print(result.output)
        else:
            print(f"Hata: {result.error}")

        # Bagam ile
        context = [
            {"role": "user", "content": "Kendimi kotu hissediyorum"},
            {"role": "assistant", "content": "Anliyorum..."}
        ]
        result = pipeline.process("Cok uzgunum", context)
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        situation_builder: Optional[SituationBuilder] = None,
        act_selector: Optional[DialogueActSelector] = None,
        message_planner: Optional[MessagePlanner] = None,
        risk_scorer: Optional[RiskScorer] = None,
        approver: Optional[InternalApprover] = None,
        construction_grammar: Optional[ConstructionGrammar] = None,
        construction_selector: Optional[ConstructionSelector] = None,
        construction_realizer: Optional[ConstructionRealizer] = None,
        self_critique: Optional[SelfCritique] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """
        ThoughtToSpeechPipeline olustur.

        Args:
            config: Pipeline konfigurasyonu
            situation_builder: SituationBuilder (opsiyonel, otomatik olusturulur)
            act_selector: DialogueActSelector (opsiyonel)
            message_planner: MessagePlanner (opsiyonel)
            risk_scorer: RiskScorer (opsiyonel)
            approver: InternalApprover (opsiyonel)
            construction_grammar: ConstructionGrammar (opsiyonel)
            construction_selector: ConstructionSelector (opsiyonel)
            construction_realizer: ConstructionRealizer (opsiyonel)
            self_critique: SelfCritique (opsiyonel)
            context_manager: ContextManager (opsiyonel, multi-turn context için)
        """
        self.config = config or PipelineConfig()

        # Bilesenleri olustur veya kullan
        self.situation_builder = situation_builder or SituationBuilder()
        self.act_selector = act_selector or DialogueActSelector()
        self.message_planner = message_planner or MessagePlanner()
        self.risk_scorer = risk_scorer or RiskScorer()
        self.approver = approver or InternalApprover()

        # Construction bilesenleri
        if construction_grammar:
            self.construction_grammar = construction_grammar
        else:
            self.construction_grammar = ConstructionGrammar(
                ConstructionGrammarConfig(
                    load_defaults=self.config.use_default_constructions
                )
            )

        if construction_selector:
            self.construction_selector = construction_selector
        else:
            self.construction_selector = ConstructionSelector(
                self.construction_grammar
            )

        self.construction_realizer = (
            construction_realizer or ConstructionRealizer()
        )

        # Self critique
        if self_critique:
            self.self_critique = self_critique
        else:
            self.self_critique = SelfCritique(
                self.config.self_critique_config
            )

        # Context manager (opsiyonel - multi-turn için)
        self.context_manager = context_manager

    def process(
        self,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Ana islem metodu - kullanici mesajini isle.

        Args:
            user_message: Kullanici mesaji
            context: Konusma gecmisi [{"role": "user", "content": "..."}]
            metadata: Ek metadata

        Returns:
            PipelineResult: Pipeline sonucu
        """
        result_id = generate_pipeline_result_id()
        result_metadata = {"id": result_id, **(metadata or {})}

        try:
            # Context manager varsa, eski format'tan yükle
            if self.context_manager and context:
                self.context_manager.from_legacy_format(context)

            # 1. SituationModel olustur
            situation = self._build_situation(user_message, context)
            result_metadata["situation_id"] = situation.id

            # Context manager'a user message ekle
            if self.context_manager:
                primary_intent = situation.intentions[0].goal if situation.intentions else None
                from ..intent.types import IntentCategory
                try:
                    intent_enum = IntentCategory(primary_intent) if primary_intent else None
                except (ValueError, AttributeError):
                    intent_enum = None
                self.context_manager.add_user_message(user_message, intent_enum)

            # 2. DialogueAct sec
            act_selection = self._select_acts(situation)
            result_metadata["act_count"] = len(act_selection.primary_acts)

            # 3. MessagePlan olustur
            message_plan = self._plan_message(situation, act_selection)
            result_metadata["plan_id"] = message_plan.id

            # 4. Risk degerlendir (opsiyonel)
            risk_assessment = None
            if self.config.enable_risk_assessment:
                risk_assessment = self._assess_risk(message_plan, situation)
                result_metadata["risk_level"] = risk_assessment.level.value

            # 5. Onay al (opsiyonel)
            approval = None
            if self.config.enable_approval_check and risk_assessment:
                approval = self._approve(risk_assessment)
                result_metadata["approval"] = approval.decision.value

                # Reddedildi mi?
                if approval.is_rejected:
                    return PipelineResult(
                        success=False,
                        output=self.config.fallback_response,
                        situation=situation,
                        act_selection=act_selection,
                        message_plan=message_plan,
                        risk_assessment=risk_assessment,
                        approval=approval,
                        error="Mesaj onaylanmadi",
                        metadata=result_metadata
                    )

            # 6. Construction sec
            constructions = self._select_construction(message_plan, situation)
            result_metadata["construction_count"] = len(constructions)

            # 7. Cikti uret
            output = self._realize(constructions, message_plan)

            # Construction bulunamazsa fallback
            if not output:
                output = self._generate_fallback_output(message_plan, situation)

            # 8. Self critique (opsiyonel)
            critique_result = None
            if self.config.enable_self_critique:
                critique_result = self._critique(output, message_plan, situation)
                result_metadata["critique_score"] = critique_result.score

                # Revize edildi mi?
                if critique_result.revised_output:
                    output = critique_result.revised_output
                    result_metadata["was_revised"] = True

            # Uzunluk kontrolu
            if len(output) > self.config.max_output_length:
                output = output[: self.config.max_output_length - 3] + "..."

            # Context manager'a assistant message ekle
            if self.context_manager:
                primary_act = act_selection.primary_acts[0] if act_selection.primary_acts else None
                self.context_manager.add_assistant_message(output, primary_act)

            return PipelineResult(
                success=True,
                output=output,
                situation=situation,
                act_selection=act_selection,
                message_plan=message_plan,
                risk_assessment=risk_assessment,
                approval=approval,
                constructions_used=constructions,
                critique_result=critique_result,
                metadata=result_metadata
            )

        except Exception as e:
            return PipelineResult.failure(
                error=str(e),
                fallback_output=self.config.fallback_response
            )

    def _build_situation(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> SituationModel:
        """
        SituationModel olustur.

        Args:
            message: Kullanici mesaji
            context: Konusma gecmisi

        Returns:
            SituationModel
        """
        return self.situation_builder.build(message, context)

    def _select_acts(self, situation: SituationModel) -> ActSelectionResult:
        """
        DialogueAct sec.

        Args:
            situation: Durum modeli

        Returns:
            ActSelectionResult
        """
        return self.act_selector.select(situation)

    def _plan_message(
        self,
        situation: SituationModel,
        acts: ActSelectionResult
    ) -> MessagePlan:
        """
        MessagePlan olustur.

        Args:
            situation: Durum modeli
            acts: Act secim sonucu

        Returns:
            MessagePlan
        """
        return self.message_planner.plan(acts, situation)

    def _assess_risk(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> RiskAssessment:
        """
        Risk degerlendir.

        Args:
            plan: Mesaj plani
            situation: Durum modeli

        Returns:
            RiskAssessment
        """
        return self.risk_scorer.assess(plan, situation)

    def _approve(self, assessment: RiskAssessment) -> ApprovalResult:
        """
        Onay al.

        Args:
            assessment: Risk degerlendirmesi

        Returns:
            ApprovalResult
        """
        return self.approver.approve(assessment)

    def _select_construction(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> List[Construction]:
        """
        Construction sec.

        Args:
            plan: Mesaj plani
            situation: Durum modeli

        Returns:
            Construction listesi
        """
        # DialogueAct'leri string'e cevir
        act_strings = [act.value for act in plan.dialogue_acts]

        # Ton string'e cevir
        tone_string = plan.tone.value

        # Constraints
        constraints = plan.constraints

        # Sec
        result = self.construction_selector.select(
            dialogue_acts=act_strings,
            tone=tone_string,
            constraints=constraints
        )

        # Construction'lari cikar
        return [score.construction for score in result.selected]

    def _realize(
        self,
        constructions: List[Construction],
        plan: MessagePlan
    ) -> str:
        """
        Cikti uret.

        Args:
            constructions: Construction listesi
            plan: Mesaj plani

        Returns:
            Uretilen metin
        """
        if not constructions:
            return ""

        # SURFACE level construction'lari tercih et (dogrudan cikti icin)
        from ..construction.types import ConstructionLevel
        surface_constructions = [
            c for c in constructions
            if c.level == ConstructionLevel.SURFACE
        ]

        # SURFACE varsa onlari kullan, yoksa hepsini kullan
        target_constructions = surface_constructions if surface_constructions else constructions

        # Slot values hazirla
        slot_values = self._prepare_slot_values(plan)

        # Tek construction (en yuksek skorlu)
        if len(target_constructions) >= 1:
            # Sadece en uygun construction'i kullan
            result = self.construction_realizer.realize(
                target_constructions[0], slot_values
            )
            return result.text if result.success else ""

        return ""

    def _prepare_slot_values(self, plan: MessagePlan) -> Dict[str, str]:
        """
        Slot degerleri hazirla.

        Args:
            plan: Mesaj plani

        Returns:
            Slot ismi -> deger eslesmesi
        """
        slots = {}

        # Intent'ten konu cikar
        slots["konu"] = plan.primary_intent[:50] if plan.primary_intent else ""

        # Icerik noktalarindan bilgi cikar
        if plan.content_points:
            slots["bilgi"] = plan.content_points[0][:100]
            if len(plan.content_points) > 1:
                slots["ek_bilgi"] = plan.content_points[1][:100]

        # Varsayilan degerler
        slots.setdefault("mesaj", "Anliyorum")
        slots.setdefault("duygu", "anlayis")

        return slots

    def _critique(
        self,
        output: str,
        plan: MessagePlan,
        situation: SituationModel
    ) -> CritiqueResult:
        """
        Self critique uygula.

        Args:
            output: Cikti metni
            plan: Mesaj plani
            situation: Durum modeli

        Returns:
            CritiqueResult
        """
        return self.self_critique.critique(output, plan, situation)

    def _generate_fallback_output(
        self,
        plan: MessagePlan,
        situation: SituationModel
    ) -> str:
        """
        Construction bulunamazsa fallback cikti uret.

        Args:
            plan: Mesaj plani
            situation: Durum modeli

        Returns:
            Fallback metin
        """
        # Primary act'e gore fallback
        primary_act = plan.dialogue_acts[0] if plan.dialogue_acts else None

        fallbacks = {
            DialogueAct.INFORM: "Anliyorum, bilgi vereyim.",
            DialogueAct.EXPLAIN: "Size aciklamak isterim.",
            DialogueAct.CLARIFY: "Bunu netlestirelim.",
            DialogueAct.ASK: "Sormak istedigim bir sey var.",
            DialogueAct.CONFIRM: "Dogrulamak istiyorum.",
            DialogueAct.EMPATHIZE: "Sizi anliyorum, zor bir durum.",
            DialogueAct.ENCOURAGE: "Yapabilirsiniz, inaniyorum.",
            DialogueAct.COMFORT: "Buradayim, her sey duzelebilir.",
            DialogueAct.SUGGEST: "Bir onerim var.",
            DialogueAct.WARN: "Dikkat etmeniz gereken bir sey var.",
            DialogueAct.ADVISE: "Size tavsiyem su olacaktir.",
            DialogueAct.REFUSE: "Maalesef bu konuda yardimci olamiyorum.",
            DialogueAct.LIMIT: "Bu konuda sinirlarim var.",
            DialogueAct.DEFLECT: "Baska bir konuya bakalim mi?",
            DialogueAct.ACKNOWLEDGE: "Anliyorum.",
            DialogueAct.APOLOGIZE: "Ozur dilerim.",
            DialogueAct.THANK: "Tesekkur ederim.",
        }

        return fallbacks.get(primary_act, self.config.fallback_response)

    def process_with_retry(
        self,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
        max_retries: int = 2
    ) -> PipelineResult:
        """
        Retry ile islem yap.

        Args:
            user_message: Kullanici mesaji
            context: Konusma gecmisi
            max_retries: Maksimum deneme sayisi

        Returns:
            PipelineResult
        """
        last_result = None

        for attempt in range(max_retries + 1):
            result = self.process(user_message, context)

            if result.success:
                return result

            last_result = result

            # Revizyon gerekiyorsa tekrar dene
            if (
                result.critique_result
                and result.critique_result.needs_revision
                and attempt < max_retries
            ):
                continue

            break

        return last_result or PipelineResult.failure(
            error="Maksimum deneme sayisi asildi",
            fallback_output=self.config.fallback_response
        )

    def get_pipeline_info(self) -> Dict[str, Any]:
        """Pipeline bilgilerini dondur."""
        return {
            "config": {
                "self_critique_enabled": self.config.enable_self_critique,
                "risk_assessment_enabled": self.config.enable_risk_assessment,
                "approval_check_enabled": self.config.enable_approval_check,
                "max_revisions": self.config.max_revision_attempts,
                "min_approval_level": self.config.min_approval_level.value,
            },
            "components": {
                "situation_builder": type(self.situation_builder).__name__,
                "act_selector": type(self.act_selector).__name__,
                "message_planner": type(self.message_planner).__name__,
                "risk_scorer": type(self.risk_scorer).__name__,
                "approver": type(self.approver).__name__,
                "construction_grammar": type(self.construction_grammar).__name__,
                "construction_selector": type(self.construction_selector).__name__,
                "construction_realizer": type(self.construction_realizer).__name__,
                "self_critique": type(self.self_critique).__name__,
            },
            "construction_count": len(
                self.construction_grammar.get_all_constructions()
            ),
        }
