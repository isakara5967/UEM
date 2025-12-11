"""
core/language/construction/selector.py

ConstructionSelector - MessagePlan → Uygun Construction seçimi.

MessagePlan'daki DialogueAct'lere, tona ve kısıtlara göre
en uygun Construction'ları seçer.

Faz 5: Feedback-driven re-ranking desteği eklendi.
FeedbackStore varsa, construction seçiminde feedback skorlarını kullanır.

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .types import (
    Construction,
    ConstructionLevel,
)
from .grammar import ConstructionGrammar

if TYPE_CHECKING:
    from core.learning.feedback_store import FeedbackStore

logger = logging.getLogger(__name__)


@dataclass
class ConstructionScore:
    """
    Construction skorlaması.

    Attributes:
        construction: Skorlanan construction
        total_score: Toplam skor (0.0-1.0)
        dialogue_act_score: DialogueAct eşleşme skoru
        tone_score: Ton uyum skoru
        constraint_score: Kısıt uyum skoru
        confidence_score: Construction güven skoru
        reasons: Skor gerekçeleri
        feedback_metadata: Feedback re-ranking metadata (Faz 5)
    """
    construction: Construction
    total_score: float
    dialogue_act_score: float = 0.0
    tone_score: float = 0.0
    constraint_score: float = 0.0
    confidence_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    feedback_metadata: Optional[Dict[str, Any]] = None


@dataclass
class SelectionResult:
    """
    Seçim sonucu.

    Attributes:
        selected: Seçilen construction'lar (skorlanmış)
        all_scores: Tüm skorlar
        level_counts: Katman başına seçilen sayı
    """
    selected: List[ConstructionScore]
    all_scores: List[ConstructionScore]
    level_counts: Dict[ConstructionLevel, int] = field(default_factory=dict)


@dataclass
class ConstructionSelectorConfig:
    """
    ConstructionSelector konfigürasyonu.

    Attributes:
        dialogue_act_weight: DialogueAct eşleşme ağırlığı
        tone_weight: Ton uyum ağırlığı
        constraint_weight: Kısıt uyum ağırlığı
        confidence_weight: Güven skoru ağırlığı
        min_score_threshold: Minimum skor eşiği
        max_selections_per_act: Act başına maksimum seçim
        prefer_high_confidence: Yüksek güvenli construction'ları tercih et
        mvcs_boost: MVCS construction'ları için bonus skor
        prefer_mvcs: MVCS construction'ları önceliklendir
    """
    dialogue_act_weight: float = 0.40
    tone_weight: float = 0.25
    constraint_weight: float = 0.15
    confidence_weight: float = 0.20
    min_score_threshold: float = 0.3
    max_selections_per_act: int = 3
    prefer_high_confidence: bool = True
    mvcs_boost: float = 0.15
    prefer_mvcs: bool = True


class ConstructionSelector:
    """
    MessagePlan → Uygun Construction seçimi.

    MessagePlan'daki DialogueAct'lere, tona ve kısıtlara göre
    en uygun Construction'ları seçer.

    Kullanım:
        grammar = ConstructionGrammar()
        selector = ConstructionSelector(grammar)

        result = selector.select(
            dialogue_acts=["inform", "suggest"],
            tone="supportive",
            constraints=["be_empathic"]
        )

        for score in result.selected:
            print(f"{score.construction.form.template}: {score.total_score}")
    """

    def __init__(
        self,
        grammar: ConstructionGrammar,
        config: Optional[ConstructionSelectorConfig] = None,
        feedback_store: Optional["FeedbackStore"] = None
    ):
        """
        ConstructionSelector oluştur.

        Args:
            grammar: Construction grammar
            config: Selector konfigürasyonu
            feedback_store: FeedbackStore for re-ranking (Faz 5, opsiyonel)
        """
        self.grammar = grammar
        self.config = config or ConstructionSelectorConfig()
        self.feedback_store = feedback_store

        # Tone mapping
        self._tone_map = self._build_tone_map()

        # Intent → MVCS Category mapping
        self._intent_mvcs_map = self._build_intent_mvcs_map()

        if feedback_store:
            logger.info(f"ConstructionSelector: Feedback re-ranking enabled with {len(feedback_store)} construction stats")

    def select(
        self,
        dialogue_acts: List[str],
        tone: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SelectionResult:
        """
        MessagePlan kriterlerine göre construction seç.

        Args:
            dialogue_acts: DialogueAct listesi
            tone: İstenen ton (opsiyonel)
            constraints: Kısıtlar (opsiyonel)
            context: Ek bağlam (opsiyonel)

        Returns:
            SelectionResult: Seçim sonucu
        """
        all_scores = []
        selected = []

        # Her dialogue act için construction'ları skorla
        for act in dialogue_acts:
            constructions = self.grammar.get_by_dialogue_act(act)

            act_scores = []
            for construction in constructions:
                score = self.score_construction(
                    construction, act, tone, constraints, context
                )
                act_scores.append(score)
                all_scores.append(score)

            # Bu act için en iyi construction'ları seç
            act_scores.sort(key=lambda s: s.total_score, reverse=True)
            top_selections = [
                s for s in act_scores[:self.config.max_selections_per_act]
                if s.total_score >= self.config.min_score_threshold
            ]
            selected.extend(top_selections)

        # Tekrarları kaldır ve sırala
        seen_ids = set()
        unique_selected = []
        for score in selected:
            if score.construction.id not in seen_ids:
                seen_ids.add(score.construction.id)
                unique_selected.append(score)

        unique_selected.sort(key=lambda s: s.total_score, reverse=True)

        # Faz 5: Feedback re-ranking uygula
        unique_selected = self._apply_feedback_rerank(unique_selected)

        # Level counts
        level_counts = {}
        for level in ConstructionLevel:
            level_counts[level] = sum(
                1 for s in unique_selected if s.construction.level == level
            )

        return SelectionResult(
            selected=unique_selected,
            all_scores=all_scores,
            level_counts=level_counts
        )

    def score_construction(
        self,
        construction: Construction,
        dialogue_act: str,
        tone: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConstructionScore:
        """
        Tek bir construction için skor hesapla.

        Args:
            construction: Skorlanacak construction
            dialogue_act: Hedef dialogue act
            tone: İstenen ton
            constraints: Kısıtlar
            context: Ek bağlam

        Returns:
            ConstructionScore: Skor sonucu
        """
        reasons = []

        # 1. DialogueAct eşleşmesi
        act_score = self._match_dialogue_act(construction, dialogue_act)
        if act_score > 0:
            reasons.append(f"DialogueAct match: {dialogue_act}")

        # 2. Ton uyumu
        tone_score = self._match_tone(construction, tone) if tone else 0.5
        if tone and tone_score > 0.5:
            reasons.append(f"Tone match: {tone}")

        # 3. Kısıt uyumu
        constraint_score = self._match_constraints(construction, constraints) if constraints else 0.5
        if constraints and constraint_score > 0.5:
            reasons.append("Constraint match")

        # 4. Güven skoru
        confidence_score = construction.confidence
        if self.config.prefer_high_confidence and confidence_score > 0.7:
            reasons.append("High confidence")

        # 5. MVCS bonus
        mvcs_bonus = 0.0
        if self.config.prefer_mvcs and construction.extra_data.get("is_mvcs"):
            mvcs_bonus = self.config.mvcs_boost
            reasons.append("MVCS construction (priority)")

            # Intent context'e göre ekstra bonus (context'ten gelen intent)
            if context:
                intent = context.get("intent")
                if intent:
                    mvcs_category = construction.extra_data.get("mvcs_category")
                    category_match = self._match_intent_to_mvcs_category(intent, mvcs_category)
                    if category_match:
                        mvcs_bonus += 0.1
                        reasons.append(f"MVCS category match: {mvcs_category}")

        # Toplam skor hesapla
        total_score = (
            act_score * self.config.dialogue_act_weight +
            tone_score * self.config.tone_weight +
            constraint_score * self.config.constraint_weight +
            confidence_score * self.config.confidence_weight +
            mvcs_bonus
        )

        return ConstructionScore(
            construction=construction,
            total_score=min(1.0, total_score),
            dialogue_act_score=act_score,
            tone_score=tone_score,
            constraint_score=constraint_score,
            confidence_score=confidence_score,
            reasons=reasons
        )

    def _match_dialogue_act(
        self,
        construction: Construction,
        dialogue_act: str
    ) -> float:
        """
        DialogueAct eşleşme skoru.

        Args:
            construction: Construction
            dialogue_act: Hedef act

        Returns:
            Eşleşme skoru (0.0-1.0)
        """
        if construction.meaning.dialogue_act == dialogue_act:
            return 1.0

        # Yakın act'ler için kısmi skor
        similar_acts = {
            "inform": ["explain", "clarify"],
            "explain": ["inform", "clarify"],
            "empathize": ["comfort", "encourage"],
            "comfort": ["empathize", "encourage"],
            "suggest": ["advise"],
            "advise": ["suggest"],
            "warn": ["advise"],
        }

        if dialogue_act in similar_acts:
            if construction.meaning.dialogue_act in similar_acts[dialogue_act]:
                return 0.6

        return 0.0

    def _match_tone(
        self,
        construction: Construction,
        tone: str
    ) -> float:
        """
        Ton uyum skoru.

        Args:
            construction: Construction
            tone: İstenen ton

        Returns:
            Uyum skoru (0.0-1.0)
        """
        construction_tone = construction.extra_data.get("tone")

        if not construction_tone:
            # Ton belirtilmemişse nötr kabul et
            return 0.5

        if construction_tone == tone:
            return 1.0

        # Benzer tonlar için kısmi skor
        if tone in self._tone_map and construction_tone in self._tone_map[tone]:
            return 0.7

        return 0.3

    def _match_constraints(
        self,
        construction: Construction,
        constraints: List[str]
    ) -> float:
        """
        Kısıt uyum skoru.

        Args:
            construction: Construction
            constraints: Kısıtlar

        Returns:
            Uyum skoru (0.0-1.0)
        """
        if not constraints:
            return 0.5

        construction_constraints = construction.extra_data.get("constraints", [])

        # Kısıt eşleşme sayısı
        matches = sum(1 for c in constraints if c in construction_constraints)

        # İlgili ton/effect kontrolü
        tone = construction.extra_data.get("tone")
        effects = construction.meaning.effects

        # Kısıtlara göre bonus
        bonus = 0.0
        for constraint in constraints:
            if "empathic" in constraint.lower() and tone == "empathic":
                bonus += 0.2
            if "supportive" in constraint.lower() and tone == "supportive":
                bonus += 0.2
            if "formal" in constraint.lower() and tone == "formal":
                bonus += 0.2
            if "serious" in constraint.lower() and tone == "serious":
                bonus += 0.2

        if matches > 0:
            return min(1.0, (matches / len(constraints)) + bonus)

        return min(1.0, 0.3 + bonus)

    def _build_tone_map(self) -> Dict[str, List[str]]:
        """
        Benzer tonlar eşleştirmesi.

        Returns:
            Ton eşleştirme sözlüğü
        """
        return {
            "neutral": ["formal", "casual"],
            "empathic": ["supportive", "casual"],
            "supportive": ["empathic", "casual"],
            "formal": ["neutral", "serious"],
            "serious": ["formal", "cautious"],
            "cautious": ["serious", "formal"],
            "casual": ["neutral", "supportive"],
            "enthusiastic": ["supportive", "casual"],
        }

    def select_by_level(
        self,
        dialogue_acts: List[str],
        level: ConstructionLevel,
        tone: Optional[str] = None
    ) -> List[ConstructionScore]:
        """
        Belirli bir katmandan construction seç.

        Args:
            dialogue_acts: DialogueAct listesi
            level: Katman seviyesi
            tone: İstenen ton

        Returns:
            Skorlanmış construction listesi
        """
        result = self.select(dialogue_acts, tone)

        level_selections = [
            s for s in result.selected
            if s.construction.level == level
        ]

        return level_selections

    def get_best_for_act(
        self,
        dialogue_act: str,
        tone: Optional[str] = None
    ) -> Optional[ConstructionScore]:
        """
        Belirli bir act için en iyi construction'ı getir.

        Args:
            dialogue_act: DialogueAct
            tone: İstenen ton

        Returns:
            En iyi skor veya None
        """
        result = self.select([dialogue_act], tone)

        if result.selected:
            return result.selected[0]

        return None

    def _build_intent_mvcs_map(self) -> Dict[str, str]:
        """
        Intent → MVCS Category eşleştirmesi.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            # Direkt eşleşmeler
            "greet": "greet",
            "ask_wellbeing": "ask_wellbeing",
            "ask_identity": "self_intro",
            "express_negative_emotion": "empathize_basic",
            "express_positive_emotion": "ask_wellbeing",  # Positive response
            "request_help": "clarify_request",
            # Yakın eşleşmeler
            "help": "simple_inform",
            "inform": "simple_inform",
            "ask": "clarify_request",
            "complain": "empathize_basic",
            "express_emotion": "empathize_basic",
            "communicate": "simple_inform",
        }

    def _match_intent_to_mvcs_category(
        self,
        intent: str,
        mvcs_category: Optional[str]
    ) -> bool:
        """
        Intent'in MVCS kategorisiyle eşleşip eşleşmediğini kontrol et.

        Args:
            intent: Kullanıcı intent'i
            mvcs_category: MVCS kategorisi

        Returns:
            Eşleşme varsa True
        """
        if not intent or not mvcs_category:
            return False

        expected_category = self._intent_mvcs_map.get(intent)
        if expected_category and expected_category == mvcs_category:
            return True

        return False

    def _apply_feedback_rerank(
        self,
        candidates: List[ConstructionScore]
    ) -> List[ConstructionScore]:
        """
        Feedback skorlarına göre yeniden sırala.

        Faz 5: Construction seçiminde feedback-driven learning.
        Her construction için feedback stats varsa, base score'u adjust eder.

        Args:
            candidates: Sıralı ConstructionScore listesi

        Returns:
            Feedback-adjusted ve yeniden sıralanmış liste
        """
        if not self.feedback_store:
            return candidates

        if not candidates:
            return candidates

        # Lazy import to avoid circular dependency
        from core.learning.feedback_scorer import compute_final_score

        for candidate in candidates:
            stats = self.feedback_store.get_stats(candidate.construction.id)

            if stats:
                base_score = candidate.total_score
                final_score, metadata = compute_final_score(base_score, stats)

                # Score'u güncelle
                candidate.total_score = final_score

                # Metadata'yı kaydet (açıklanabilirlik için)
                candidate.feedback_metadata = metadata

                # Reason ekle
                adjustment = metadata.get("adjustment", 1.0)
                if adjustment > 1.05:
                    candidate.reasons.append(
                        f"Feedback boost: {adjustment:.2f}x (mean={metadata['feedback_mean']:.2f})"
                    )
                elif adjustment < 0.95:
                    candidate.reasons.append(
                        f"Feedback penalty: {adjustment:.2f}x (mean={metadata['feedback_mean']:.2f})"
                    )

                logger.debug(
                    f"Feedback rerank: {candidate.construction.id} "
                    f"base={base_score:.3f} → final={final_score:.3f} "
                    f"(adj={adjustment:.3f})"
                )
            else:
                # Stats yoksa base_score kalsın
                candidate.feedback_metadata = {
                    "feedback_mean": 0.5,
                    "adjustment": 1.0,
                    "base_score": candidate.total_score,
                    "final_score": candidate.total_score,
                    "total_uses": 0,
                }

        # Yeniden sırala
        candidates.sort(key=lambda x: x.total_score, reverse=True)

        return candidates

    def set_feedback_store(self, feedback_store: "FeedbackStore") -> None:
        """
        FeedbackStore'u dinamik olarak ayarla.

        Args:
            feedback_store: FeedbackStore instance
        """
        self.feedback_store = feedback_store
        logger.info(f"ConstructionSelector: Feedback store updated ({len(feedback_store)} stats)")
