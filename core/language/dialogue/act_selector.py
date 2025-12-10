"""
core/language/dialogue/act_selector.py

DialogueActSelector - SituationModel → DialogueAct seçimi

Self + Affect + Ethics değerlendirmesiyle
duruma uygun konuşma eylemlerini seçer.

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    DialogueAct,
    SituationModel,
    Intention,
    Risk,
    EmotionalState,
)


class SelectionStrategy(str, Enum):
    """
    Act seçim stratejisi.

    Strategies:
    - CONSERVATIVE: Güvenli, düşük risk, safe acts tercih
    - BALANCED: Dengeli yaklaşım
    - EXPRESSIVE: Duygusal, empatik acts tercih
    """
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    EXPRESSIVE = "expressive"


@dataclass
class ActScore:
    """
    Bir DialogueAct'in skoru.

    Attributes:
        act: Değerlendirilen DialogueAct
        score: Skor değeri (0.0-1.0)
        reasons: Skor gerekçeleri
    """
    act: DialogueAct
    score: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class ActSelectionResult:
    """
    Seçim sonucu.

    Attributes:
        primary_acts: Ana eylemler (sıralı, en yüksek skorlu)
        secondary_acts: Alternatif eylemler
        all_scores: Tüm skorlar
        strategy_used: Kullanılan strateji
        confidence: Seçim güveni (0.0-1.0)
    """
    primary_acts: List[DialogueAct]
    secondary_acts: List[DialogueAct]
    all_scores: List[ActScore]
    strategy_used: SelectionStrategy
    confidence: float


@dataclass
class ActSelectorConfig:
    """
    DialogueActSelector konfigürasyonu.

    Attributes:
        max_primary_acts: Maksimum ana act sayısı
        max_secondary_acts: Maksimum alternatif act sayısı
        min_score_threshold: Minimum skor eşiği
        strategy: Seçim stratejisi
        enable_ethics_check: Etik kontrolü aktif mi?
        enable_affect_influence: Affect etkisi aktif mi?
    """
    max_primary_acts: int = 3
    max_secondary_acts: int = 2
    min_score_threshold: float = 0.3
    strategy: SelectionStrategy = SelectionStrategy.BALANCED
    enable_ethics_check: bool = True
    enable_affect_influence: bool = True


class DialogueActSelector:
    """
    SituationModel → DialogueAct seçimi.

    Self + Affect + Ethics değerlendirmesiyle
    duruma uygun konuşma eylemlerini seçer.

    Kullanım:
        selector = DialogueActSelector()
        result = selector.select(situation)
        print(result.primary_acts)  # [DialogueAct.INFORM, DialogueAct.SUGGEST]

        # Strateji ile
        config = ActSelectorConfig(strategy=SelectionStrategy.EXPRESSIVE)
        selector = DialogueActSelector(config=config)
        result = selector.select(situation)
    """

    def __init__(
        self,
        config: Optional[ActSelectorConfig] = None,
        affect_processor: Optional[Any] = None,
        self_processor: Optional[Any] = None,
        ethics_checker: Optional[Any] = None
    ):
        """
        DialogueActSelector oluştur.

        Args:
            config: Selector konfigürasyonu
            affect_processor: Affect modülü (opsiyonel)
            self_processor: Self modülü (opsiyonel)
            ethics_checker: Ethics checker (opsiyonel)
        """
        self.config = config or ActSelectorConfig()
        self.affect = affect_processor
        self.self_proc = self_processor
        self.ethics = ethics_checker

        # Eşleştirme tabloları
        self._intent_act_map = self._build_intent_act_map()
        self._risk_act_map = self._build_risk_act_map()
        self._emotion_act_map = self._build_emotion_act_map()

    def select(
        self,
        situation: SituationModel,
        context: Optional[Dict[str, Any]] = None
    ) -> ActSelectionResult:
        """
        Ana seçim metodu - SituationModel'den DialogueAct'ler seç.

        Context-aware: Önceki act'leri ve konuşma durumunu dikkate alır.

        Args:
            situation: Durum modeli
            context: Ek bağlam (conversation history, last acts, etc.)

        Returns:
            ActSelectionResult: Seçim sonucu
        """
        # 1. Tüm act'ler için skor hesapla
        all_scores = self._score_all_acts(situation)

        # 2. Context-aware adjustments
        if context:
            all_scores = self._apply_context_adjustments(all_scores, context)

        # 3. Etik kontrolü uygula
        if self.config.enable_ethics_check:
            all_scores = self._apply_ethics_filter(all_scores, situation)

        # 4. Affect etkisini uygula
        if self.config.enable_affect_influence:
            all_scores = self._apply_affect_influence(all_scores, situation)

        # 5. Stratejiye göre ayarla
        all_scores = self._apply_strategy(all_scores)

        # 6. Sırala
        sorted_scores = sorted(all_scores, key=lambda x: x.score, reverse=True)

        # 7. Eşik üstündekileri al
        valid_scores = [
            s for s in sorted_scores
            if s.score >= self.config.min_score_threshold
        ]

        # 8. Primary ve secondary ayır
        primary = [
            s.act for s in valid_scores[:self.config.max_primary_acts]
        ]
        secondary = [
            s.act for s in valid_scores[
                self.config.max_primary_acts:
                self.config.max_primary_acts + self.config.max_secondary_acts
            ]
        ]

        # 9. Confidence hesapla
        confidence = self._calculate_confidence(valid_scores, situation)

        # Fallback: hiç act seçilmediyse
        if not primary:
            # Intent'e göre fallback
            has_greet_intent = any(
                i.goal == "greet" for i in situation.intentions
            )
            if has_greet_intent:
                primary = [DialogueAct.GREET]
            else:
                primary = [DialogueAct.ACKNOWLEDGE]
            confidence = 0.3

        return ActSelectionResult(
            primary_acts=primary,
            secondary_acts=secondary,
            all_scores=sorted_scores,
            strategy_used=self.config.strategy,
            confidence=confidence
        )

    def _score_all_acts(self, situation: SituationModel) -> List[ActScore]:
        """
        Tüm act'ler için skor hesapla.

        Args:
            situation: Durum modeli

        Returns:
            List[ActScore]: Tüm skorlar
        """
        scores = []

        for act in DialogueAct:
            score, reasons = self._calculate_act_score(act, situation)
            scores.append(ActScore(act=act, score=score, reasons=reasons))

        return scores

    def _calculate_act_score(
        self,
        act: DialogueAct,
        situation: SituationModel
    ) -> Tuple[float, List[str]]:
        """
        Tek bir act için skor hesapla.

        Args:
            act: Değerlendirilecek act
            situation: Durum modeli

        Returns:
            Tuple[score, reasons]
        """
        score = 0.0
        reasons = []

        # 1. Intent eşleşmesi (%40)
        intent_score, intent_reasons = self._score_by_intentions(
            act, situation.intentions
        )
        score += intent_score * 0.4
        reasons.extend(intent_reasons)

        # 2. Risk eşleşmesi (%30)
        risk_score, risk_reasons = self._score_by_risks(act, situation.risks)
        score += risk_score * 0.3
        reasons.extend(risk_reasons)

        # 3. Emotion eşleşmesi (%20)
        emotion_score, emotion_reasons = self._score_by_emotion(
            act, situation.emotional_state
        )
        score += emotion_score * 0.2
        reasons.extend(emotion_reasons)

        # 4. Understanding etkisi (%10)
        understanding_bonus = situation.understanding_score * 0.1
        score += understanding_bonus

        return min(1.0, score), reasons

    def _score_by_intentions(
        self,
        act: DialogueAct,
        intentions: List[Intention]
    ) -> Tuple[float, List[str]]:
        """
        Intent'lere göre skor hesapla.

        Args:
            act: Değerlendirilecek act
            intentions: Niyet listesi

        Returns:
            Tuple[score, reasons]
        """
        if not intentions:
            return 0.0, []

        score = 0.0
        reasons = []

        for intention in intentions:
            # Intention.goal alanını kullan
            goal = intention.goal
            if goal in self._intent_act_map:
                matching_acts = self._intent_act_map[goal]
                if act in matching_acts:
                    # Primary act (first in list) gets higher boost
                    # Hedefli B: Primary act için daha güçlü boost (0.9 → 1.1)
                    if matching_acts[0] == act:
                        boost = intention.confidence * 1.1
                    else:
                        boost = intention.confidence * 0.7
                    score += boost
                    reasons.append(f"Intent '{goal}' matches")

        return min(1.0, score), reasons

    def _score_by_risks(
        self,
        act: DialogueAct,
        risks: List[Risk]
    ) -> Tuple[float, List[str]]:
        """
        Risk'lere göre skor hesapla.

        Args:
            act: Değerlendirilecek act
            risks: Risk listesi

        Returns:
            Tuple[score, reasons]
        """
        if not risks:
            return 0.0, []

        score = 0.0
        reasons = []

        for risk in risks:
            # Risk.category ve Risk.level alanlarını kullan
            category = risk.category
            if category in self._risk_act_map:
                matching_acts = self._risk_act_map[category]
                if act in matching_acts:
                    boost = risk.level * 0.5
                    score += boost
                    reasons.append(f"Risk '{category}' suggests this act")

        return min(1.0, score), reasons

    def _score_by_emotion(
        self,
        act: DialogueAct,
        emotional_state: Optional[EmotionalState]
    ) -> Tuple[float, List[str]]:
        """
        Duygusal duruma göre skor hesapla.

        Args:
            act: Değerlendirilecek act
            emotional_state: Duygusal durum

        Returns:
            Tuple[score, reasons]
        """
        if not emotional_state:
            return 0.0, []

        score = 0.0
        reasons = []

        # Negative valence → Empathize, Comfort, Encourage
        if emotional_state.valence <= -0.2:
            empathy_acts = [
                DialogueAct.EMPATHIZE,
                DialogueAct.COMFORT,
                DialogueAct.ENCOURAGE
            ]
            if act in empathy_acts:
                # Stronger boost for empathy with negative emotions
                score += 0.7
                reasons.append("Negative emotion detected, empathy needed")

        # Positive valence → Acknowledge, Encourage
        elif emotional_state.valence > 0.3:
            positive_acts = [DialogueAct.ACKNOWLEDGE, DialogueAct.ENCOURAGE]
            if act in positive_acts:
                score += 0.3
                reasons.append("Positive emotion, acknowledge it")

        # High arousal → Comfort, Clarify
        if emotional_state.arousal > 0.5:
            calming_acts = [DialogueAct.COMFORT, DialogueAct.CLARIFY]
            if act in calming_acts:
                score += 0.3
                reasons.append("High arousal, calming response needed")

        return min(1.0, score), reasons

    def _apply_ethics_filter(
        self,
        scores: List[ActScore],
        situation: SituationModel
    ) -> List[ActScore]:
        """
        Etik kontrolü uygula.

        Yüksek riskli durumlarda bazı act'leri kısıtla,
        bazılarını teşvik et.

        Args:
            scores: Mevcut skorlar
            situation: Durum modeli

        Returns:
            Güncellenmiş skorlar
        """
        high_risks = [r for r in situation.risks if r.level > 0.7]

        if high_risks:
            # Yüksek riskli durumda REFUSE, DEFLECT skorunu düşür
            restricted_acts = [DialogueAct.REFUSE, DialogueAct.DEFLECT]
            for score in scores:
                if score.act in restricted_acts:
                    score.score *= 0.5
                    score.reasons.append(
                        "Ethics: reduced due to high risk situation"
                    )

            # WARN, EMPATHIZE, COMFORT skorunu artır
            encouraged_acts = [
                DialogueAct.WARN,
                DialogueAct.EMPATHIZE,
                DialogueAct.COMFORT
            ]
            for score in scores:
                if score.act in encouraged_acts:
                    score.score = min(1.0, score.score * 1.3)
                    score.reasons.append(
                        "Ethics: boosted for high risk situation"
                    )

        return scores

    def _apply_affect_influence(
        self,
        scores: List[ActScore],
        situation: SituationModel
    ) -> List[ActScore]:
        """
        Affect modülü etkisini uygula.

        Args:
            scores: Mevcut skorlar
            situation: Durum modeli

        Returns:
            Güncellenmiş skorlar
        """
        if not situation.emotional_state:
            return scores

        # Çok negatif durumda empati act'lerini güçlendir
        if situation.emotional_state.valence < -0.5:
            empathy_acts = [
                DialogueAct.EMPATHIZE,
                DialogueAct.COMFORT,
                DialogueAct.ENCOURAGE
            ]
            for score in scores:
                if score.act in empathy_acts:
                    score.score = min(1.0, score.score * 1.2)
                    score.reasons.append("Affect: strong negative emotion boost")

        return scores

    def _apply_strategy(self, scores: List[ActScore]) -> List[ActScore]:
        """
        Stratejiye göre skorları ayarla.

        Args:
            scores: Mevcut skorlar

        Returns:
            Güncellenmiş skorlar
        """
        strategy = self.config.strategy

        if strategy == SelectionStrategy.CONSERVATIVE:
            # Güvenli act'leri tercih et
            safe_acts = [
                DialogueAct.ACKNOWLEDGE,
                DialogueAct.CLARIFY,
                DialogueAct.INFORM
            ]
            for score in scores:
                if score.act in safe_acts:
                    score.score = min(1.0, score.score * 1.2)
                    score.reasons.append("Strategy: conservative boost")

        elif strategy == SelectionStrategy.EXPRESSIVE:
            # Duygusal act'leri tercih et
            expressive_acts = [
                DialogueAct.EMPATHIZE,
                DialogueAct.ENCOURAGE,
                DialogueAct.COMFORT
            ]
            for score in scores:
                if score.act in expressive_acts:
                    score.score = min(1.0, score.score * 1.2)
                    score.reasons.append("Strategy: expressive boost")

        # BALANCED: değişiklik yok

        return scores

    def _calculate_confidence(
        self,
        valid_scores: List[ActScore],
        situation: SituationModel
    ) -> float:
        """
        Seçim güvenilirliğini hesapla.

        Args:
            valid_scores: Geçerli skorlar
            situation: Durum modeli

        Returns:
            Güven skoru (0.0-1.0)
        """
        if not valid_scores:
            return 0.0

        # En yüksek skorun güvenilirliğe etkisi
        top_score = valid_scores[0].score if valid_scores else 0.0

        # Situation understanding etkisi
        understanding = situation.understanding_score

        # Skor farkı (çok yakınsa daha az güven)
        if len(valid_scores) >= 2:
            score_diff = valid_scores[0].score - valid_scores[1].score
            diff_factor = min(1.0, score_diff * 2)
        else:
            diff_factor = 0.5

        confidence = (
            top_score * 0.4 +
            understanding * 0.3 +
            diff_factor * 0.3
        )
        return min(1.0, max(0.0, confidence))

    def _apply_context_adjustments(
        self,
        scores: List[ActScore],
        context: Dict[str, Any]
    ) -> List[ActScore]:
        """
        Context bilgisine göre skorları ayarla.

        Args:
            scores: Mevcut skorlar
            context: Bağlam bilgisi

        Returns:
            Güncellenmiş skorlar
        """
        # Önceki assistant act varsa, tekrarlama önle
        last_act = context.get("last_assistant_act")
        if last_act:
            for score in scores:
                if score.act == last_act:
                    # Aynı act'i tekrar kullanmayı azalt
                    score.score *= 0.7
                    score.reasons.append("Context: avoiding repetition")

        # Sentiment trend'e göre ayarla
        sentiment_trend = context.get("sentiment_trend")
        if sentiment_trend == "negative":
            # Negatif trend varsa empati act'lerini güçlendir
            empathy_acts = [
                DialogueAct.EMPATHIZE,
                DialogueAct.COMFORT,
                DialogueAct.ENCOURAGE
            ]
            for score in scores:
                if score.act in empathy_acts:
                    score.score = min(1.0, score.score * 1.15)
                    score.reasons.append("Context: negative sentiment trend")

        # Followup sorusu ise CLARIFY/EXPLAIN'i güçlendir
        is_followup = context.get("is_followup", False)
        if is_followup:
            followup_acts = [DialogueAct.CLARIFY, DialogueAct.EXPLAIN, DialogueAct.INFORM]
            for score in scores:
                if score.act in followup_acts:
                    score.score = min(1.0, score.score * 1.1)
                    score.reasons.append("Context: followup question")

        return scores

    def _build_intent_act_map(self) -> Dict[str, List[DialogueAct]]:
        """
        Intent → Act eşleştirme tablosu.

        Yeni IntentCategory enum değerlerine göre güncellenmiş.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            # Yeni IntentCategory enum değerleri
            "greeting": [DialogueAct.GREET, DialogueAct.ACKNOWLEDGE],
            "farewell": [DialogueAct.CLOSE_CONVERSATION, DialogueAct.ACKNOWLEDGE],
            "ask_wellbeing": [DialogueAct.RESPOND_WELLBEING, DialogueAct.INFORM],  # Hedefli B: kullanıcı bize sorduğunda
            "ask_identity": [DialogueAct.INFORM],  # MVCS: SELF_INTRO
            "express_positive": [DialogueAct.ACKNOWLEDGE_POSITIVE, DialogueAct.ACKNOWLEDGE, DialogueAct.ENCOURAGE],  # Hedefli B
            "express_negative": [DialogueAct.EMPATHIZE, DialogueAct.COMFORT, DialogueAct.ENCOURAGE],
            "request_help": [DialogueAct.CLARIFY, DialogueAct.ADVISE, DialogueAct.SUGGEST],
            "request_info": [DialogueAct.INFORM, DialogueAct.EXPLAIN, DialogueAct.CLARIFY],
            "thank": [DialogueAct.RECEIVE_THANKS, DialogueAct.ACKNOWLEDGE],  # Hedefli B: teşekkür alındığında
            "apologize": [DialogueAct.ACKNOWLEDGE, DialogueAct.COMFORT],
            "agree": [DialogueAct.ACKNOWLEDGE, DialogueAct.CONFIRM],
            "disagree": [DialogueAct.ACKNOWLEDGE, DialogueAct.CLARIFY],
            "clarify": [DialogueAct.CLARIFY, DialogueAct.EXPLAIN],
            "complain": [DialogueAct.EMPATHIZE, DialogueAct.ACKNOWLEDGE, DialogueAct.APOLOGIZE],
            "meta_question": [DialogueAct.EXPLAIN, DialogueAct.INFORM],
            "smalltalk": [DialogueAct.LIGHT_CHITCHAT, DialogueAct.ACKNOWLEDGE, DialogueAct.INFORM],  # Hedefli B
            "unknown": [DialogueAct.ACKNOWLEDGE, DialogueAct.CLARIFY],

            # Backward compatibility (eski intent'ler)
            "ask_identity": [DialogueAct.INFORM],
            "express_negative_emotion": [DialogueAct.EMPATHIZE, DialogueAct.COMFORT, DialogueAct.ENCOURAGE],
            "express_positive_emotion": [DialogueAct.ACKNOWLEDGE, DialogueAct.ENCOURAGE],
            "help": [DialogueAct.ADVISE, DialogueAct.SUGGEST, DialogueAct.EXPLAIN],
            "inform": [DialogueAct.INFORM, DialogueAct.EXPLAIN, DialogueAct.CLARIFY],
            "ask": [DialogueAct.INFORM, DialogueAct.EXPLAIN, DialogueAct.CLARIFY],
            "request": [DialogueAct.ACKNOWLEDGE, DialogueAct.INFORM, DialogueAct.SUGGEST],
            "greet": [DialogueAct.GREET, DialogueAct.ACKNOWLEDGE],
            "express_emotion": [DialogueAct.EMPATHIZE, DialogueAct.COMFORT, DialogueAct.ENCOURAGE],
            "communicate": [DialogueAct.ACKNOWLEDGE, DialogueAct.INFORM]
        }

    def _build_risk_act_map(self) -> Dict[str, List[DialogueAct]]:
        """
        Risk → Act eşleştirme tablosu.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            "safety": [DialogueAct.WARN, DialogueAct.EMPATHIZE, DialogueAct.ADVISE],
            "emotional": [DialogueAct.EMPATHIZE, DialogueAct.COMFORT, DialogueAct.ENCOURAGE],
            "ethical": [DialogueAct.WARN, DialogueAct.REFUSE, DialogueAct.DEFLECT],
            "relational": [DialogueAct.EMPATHIZE, DialogueAct.CLARIFY, DialogueAct.ADVISE]
        }

    def _build_emotion_act_map(self) -> Dict[str, List[DialogueAct]]:
        """
        Emotion → Act eşleştirme tablosu.

        Returns:
            Eşleştirme sözlüğü
        """
        return {
            "positive": [DialogueAct.ACKNOWLEDGE, DialogueAct.ENCOURAGE],
            "negative": [DialogueAct.EMPATHIZE, DialogueAct.COMFORT, DialogueAct.ENCOURAGE],
            "neutral": [DialogueAct.INFORM, DialogueAct.ACKNOWLEDGE]
        }
