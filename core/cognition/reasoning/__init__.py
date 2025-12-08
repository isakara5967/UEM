"""
UEM v2 - Reasoning Engine

Akıl yürütme motoru - Deduction, Induction, Abduction.

Kullanım:
    from core.cognition.reasoning import ReasoningEngine

    engine = ReasoningEngine()
    result = engine.reason(beliefs, context)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime
import logging
import time

from ..types import (
    Belief, BeliefType, BeliefStrength,
    ReasoningType, ReasoningResult,
    CognitiveState,
)


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ReasoningConfig:
    """Reasoning engine yapılandırması."""

    # Minimum güven eşikleri
    min_belief_confidence: float = 0.3   # İnancın akıl yürütmede kullanılması için
    min_conclusion_confidence: float = 0.2  # Sonucun kabul edilmesi için

    # Reasoning ağırlıkları
    deduction_weight: float = 1.0
    induction_weight: float = 0.8
    abduction_weight: float = 0.6
    analogy_weight: float = 0.5

    # Performans
    max_inference_depth: int = 5         # Maksimum çıkarım derinliği
    max_conclusions_per_cycle: int = 10  # Cycle başına maksimum sonuç

    # Kalite
    require_multiple_evidence: bool = False  # İnduction için birden fazla örnek
    min_pattern_count: int = 2           # Pattern tanıma için minimum örnek


# ============================================================================
# INFERENCE RULES
# ============================================================================

@dataclass
class InferenceRule:
    """Çıkarım kuralı."""
    rule_id: str
    name: str
    pattern: str                         # Kural paterni (human-readable)
    reasoning_type: ReasoningType

    # Koşullar
    premises_required: int = 1
    premise_patterns: List[str] = field(default_factory=list)

    # Çıktı
    conclusion_template: str = ""

    # Kalite
    reliability: float = 0.8             # Kuralın güvenilirliği


# Önceden tanımlı çıkarım kuralları
BUILTIN_RULES: List[InferenceRule] = [
    # Deduction kuralları
    InferenceRule(
        rule_id="modus_ponens",
        name="Modus Ponens",
        pattern="If A then B, A → B",
        reasoning_type=ReasoningType.DEDUCTION,
        premises_required=2,
        premise_patterns=["if {X} then {Y}", "{X}"],
        conclusion_template="{Y}",
        reliability=1.0,
    ),
    InferenceRule(
        rule_id="threat_implies_danger",
        name="Threat Implies Danger",
        pattern="Threat detected → Danger present",
        reasoning_type=ReasoningType.DEDUCTION,
        premises_required=1,
        premise_patterns=["threat_detected"],
        conclusion_template="danger_present",
        reliability=0.9,
    ),

    # Induction kuralları
    InferenceRule(
        rule_id="pattern_to_rule",
        name="Pattern to Rule",
        pattern="Multiple instances of X → X is likely general",
        reasoning_type=ReasoningType.INDUCTION,
        premises_required=3,
        premise_patterns=["instance_{X}"],
        conclusion_template="general_rule_{X}",
        reliability=0.7,
    ),

    # Abduction kuralları
    InferenceRule(
        rule_id="best_explanation",
        name="Best Explanation",
        pattern="Observation B, A→B explains B → A is likely",
        reasoning_type=ReasoningType.ABDUCTION,
        premises_required=2,
        premise_patterns=["observation_{B}", "if_{A}_then_{B}"],
        conclusion_template="likely_{A}",
        reliability=0.6,
    ),
]


# ============================================================================
# REASONING ENGINE
# ============================================================================

class ReasoningEngine:
    """
    Ana akıl yürütme motoru.

    Üç temel akıl yürütme türünü destekler:
    1. Deduction (Tümdengelim): Kesin, garantili sonuçlar
    2. Induction (Tümevarım): Pattern'lerden genelleme
    3. Abduction (Abdüksiyon): En iyi açıklamayı çıkarım
    """

    def __init__(self, config: Optional[ReasoningConfig] = None):
        self.config = config or ReasoningConfig()
        self.rules = list(BUILTIN_RULES)
        self._inference_cache: Dict[str, ReasoningResult] = {}

    # ========================================================================
    # MAIN REASONING
    # ========================================================================

    def reason(
        self,
        cognitive_state: CognitiveState,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReasoningResult]:
        """
        Ana akıl yürütme fonksiyonu.

        Tüm reasoning türlerini uygular ve sonuçları döndürür.

        Args:
            cognitive_state: Mevcut biliş durumu
            context: Ek bağlam bilgisi

        Returns:
            Reasoning sonuçları listesi
        """
        start_time = time.time()
        context = context or {}
        results: List[ReasoningResult] = []

        # Kullanılabilir inançları al
        usable_beliefs = [
            b for b in cognitive_state.beliefs.values()
            if b.confidence >= self.config.min_belief_confidence and b.is_valid()
        ]

        logger.debug(f"Reasoning with {len(usable_beliefs)} usable beliefs")

        # 1. Deduction - En güvenilir sonuçlar
        deduction_results = self._apply_deduction(usable_beliefs, context)
        results.extend(deduction_results)

        # 2. Induction - Pattern'lerden genelleme
        induction_results = self._apply_induction(usable_beliefs, context)
        results.extend(induction_results)

        # 3. Abduction - En iyi açıklama
        abduction_results = self._apply_abduction(usable_beliefs, context)
        results.extend(abduction_results)

        # Süre hesapla
        elapsed_ms = (time.time() - start_time) * 1000
        for r in results:
            r.processing_time_ms = elapsed_ms / max(len(results), 1)

        # Sonuçları filtrele
        filtered = [
            r for r in results
            if r.confidence >= self.config.min_conclusion_confidence
        ]

        # Limit uygula
        if len(filtered) > self.config.max_conclusions_per_cycle:
            filtered.sort(key=lambda r: r.quality_score, reverse=True)
            filtered = filtered[:self.config.max_conclusions_per_cycle]

        logger.debug(
            f"Reasoning complete: {len(filtered)} conclusions in {elapsed_ms:.1f}ms"
        )

        return filtered

    # ========================================================================
    # DEDUCTION (Tümdengelim)
    # ========================================================================

    def deduce(
        self,
        premises: List[str],
        rule: Optional[InferenceRule] = None,
    ) -> ReasoningResult:
        """
        Tümdengelim: Kesin sonuç çıkar.

        A→B, A ∴ B (Modus Ponens)

        Örnek:
            "Tüm insanlar ölümlüdür" + "Sokrates insandır" → "Sokrates ölümlüdür"
        """
        result = ReasoningResult(
            reasoning_type=ReasoningType.DEDUCTION,
            premises=premises,
        )

        if len(premises) < 2:
            result.conclusion = "insufficient_premises"
            result.confidence = 0.0
            result.validity = 0.0
            return result

        # Basit Modus Ponens uygula
        # Premise 1: "if X then Y" formatında
        # Premise 2: "X" (antecedent)
        # Conclusion: "Y" (consequent)

        conditional = None
        antecedent = None

        for p in premises:
            p_lower = p.lower()
            if "implies" in p_lower or "then" in p_lower or "->" in p_lower:
                conditional = p
            else:
                antecedent = p

        if conditional and antecedent:
            # Basit çıkarım
            parts = conditional.replace("->", " implies ").split("implies")
            if len(parts) == 2:
                cond_antecedent = parts[0].strip().lower()
                consequent = parts[1].strip()

                if cond_antecedent in antecedent.lower():
                    result.conclusion = consequent
                    result.confidence = 0.95  # Deduction yüksek güven
                    result.validity = 1.0     # Mantıksal olarak geçerli
                    result.soundness = 0.9    # Premise'lere bağlı
                    result.reasoning_chain = [
                        f"Premise 1: {conditional}",
                        f"Premise 2: {antecedent}",
                        f"By Modus Ponens: {consequent}",
                    ]

        if not result.conclusion:
            result.conclusion = "no_valid_deduction"
            result.confidence = 0.0
            result.validity = 0.0

        return result

    def _apply_deduction(
        self,
        beliefs: List[Belief],
        context: Dict[str, Any],
    ) -> List[ReasoningResult]:
        """Tümdengelim kurallarını uygula."""
        results = []

        # Tehdit tespiti deduction'ı
        threat_beliefs = [b for b in beliefs if "threat" in b.subject.lower()]
        if threat_beliefs:
            high_threat = any(b.confidence > 0.7 for b in threat_beliefs)
            if high_threat:
                result = ReasoningResult(
                    reasoning_type=ReasoningType.DEDUCTION,
                    premises=[b.subject + ": " + b.predicate for b in threat_beliefs],
                    conclusion="danger_present_caution_required",
                    confidence=0.9,
                    validity=1.0,
                    soundness=0.85,
                    reasoning_chain=[
                        "High threat belief detected",
                        "Threat implies potential danger",
                        "Conclusion: Caution is required",
                    ],
                )
                results.append(result)

        # Agent ile ilgili deduction'lar
        agent_beliefs = [b for b in beliefs if b.subject.startswith("agent_")]
        for agent_belief in agent_beliefs:
            if "hostile" in agent_belief.predicate.lower():
                result = ReasoningResult(
                    reasoning_type=ReasoningType.DEDUCTION,
                    premises=[f"{agent_belief.subject}: {agent_belief.predicate}"],
                    conclusion=f"avoid_or_defend_against_{agent_belief.subject}",
                    confidence=agent_belief.confidence * 0.9,
                    validity=1.0,
                    soundness=agent_belief.confidence,
                    reasoning_chain=[
                        f"Agent {agent_belief.subject} shows hostile behavior",
                        "Hostile agents may cause harm",
                        "Conclusion: Avoidance or defense recommended",
                    ],
                )
                results.append(result)

        return results

    # ========================================================================
    # INDUCTION (Tümevarım)
    # ========================================================================

    def induce(
        self,
        observations: List[str],
        pattern_name: Optional[str] = None,
    ) -> ReasoningResult:
        """
        Tümevarım: Gözlemlerden genelleme çıkar.

        X₁, X₂, X₃... → Genel kural X

        Örnek:
            "Güneş bugün doğdu", "Güneş dün doğdu", ... → "Güneş her gün doğar"
        """
        result = ReasoningResult(
            reasoning_type=ReasoningType.INDUCTION,
            premises=observations,
        )

        if len(observations) < self.config.min_pattern_count:
            result.conclusion = "insufficient_observations"
            result.confidence = 0.0
            return result

        # Pattern analizi
        common_elements = self._find_common_pattern(observations)

        if common_elements:
            result.conclusion = f"pattern_identified: {common_elements}"
            # Confidence örnek sayısına bağlı
            base_confidence = 0.5
            bonus = min(0.4, len(observations) * 0.1)
            result.confidence = base_confidence + bonus
            result.validity = 0.8  # Induction kesin değil
            result.soundness = 0.7
            result.reasoning_chain = [
                f"Observed {len(observations)} instances",
                f"Common pattern: {common_elements}",
                "Generalized to likely rule",
            ]
        else:
            result.conclusion = "no_pattern_found"
            result.confidence = 0.1

        return result

    def _apply_induction(
        self,
        beliefs: List[Belief],
        context: Dict[str, Any],
    ) -> List[ReasoningResult]:
        """Tümevarım kurallarını uygula."""
        results = []

        # Benzer inançları grupla
        subject_groups: Dict[str, List[Belief]] = {}
        for belief in beliefs:
            # Ana konuyu çıkar
            base_subject = belief.subject.split("_")[0] if "_" in belief.subject else belief.subject
            if base_subject not in subject_groups:
                subject_groups[base_subject] = []
            subject_groups[base_subject].append(belief)

        # Yeterli örneği olan gruplar için genelleme yap
        for subject, group in subject_groups.items():
            if len(group) >= self.config.min_pattern_count:
                # Ortak predicate'leri bul
                predicates = [b.predicate for b in group]
                common_pred = self._find_common_pattern(predicates)

                if common_pred:
                    avg_confidence = sum(b.confidence for b in group) / len(group)
                    result = ReasoningResult(
                        reasoning_type=ReasoningType.INDUCTION,
                        premises=[f"{b.subject}: {b.predicate}" for b in group],
                        conclusion=f"general_pattern_{subject}: {common_pred}",
                        confidence=avg_confidence * 0.8,  # Induction discount
                        validity=0.75,
                        soundness=0.7,
                        reasoning_chain=[
                            f"Observed {len(group)} beliefs about {subject}",
                            f"Common pattern: {common_pred}",
                            "Induced general rule",
                        ],
                    )
                    results.append(result)

        return results

    def _find_common_pattern(self, items: List[str]) -> Optional[str]:
        """Ortak pattern bul."""
        if not items:
            return None

        # Basit kelime bazlı ortak pattern
        word_sets = [set(item.lower().split()) for item in items]
        if not word_sets:
            return None

        common_words = word_sets[0]
        for ws in word_sets[1:]:
            common_words = common_words.intersection(ws)

        if common_words:
            return " ".join(sorted(common_words))

        return None

    # ========================================================================
    # ABDUCTION (Abdüksiyon)
    # ========================================================================

    def abduce(
        self,
        observation: str,
        possible_explanations: List[str],
    ) -> ReasoningResult:
        """
        Abdüksiyon: En iyi açıklamayı çıkar.

        B gözlendi, A→B açıklar → A muhtemeldir

        Örnek:
            "Çim ıslak" + "Yağmur yağarsa çim ıslanır" → "Muhtemelen yağmur yağdı"
        """
        result = ReasoningResult(
            reasoning_type=ReasoningType.ABDUCTION,
            premises=[observation] + possible_explanations,
        )

        if not possible_explanations:
            result.conclusion = "no_explanation_available"
            result.confidence = 0.0
            return result

        # En iyi açıklamayı seç (basit heuristik: en kısa/basit)
        best_explanation = min(possible_explanations, key=len)

        result.conclusion = f"best_explanation: {best_explanation}"
        result.confidence = 0.6  # Abduction orta güven
        result.validity = 0.5   # Abduction kesin değil
        result.soundness = 0.5
        result.assumptions = [
            "Assuming most parsimonious explanation",
            "No alternative explanations considered fully",
        ]
        result.reasoning_chain = [
            f"Observation: {observation}",
            f"Possible explanations: {len(possible_explanations)}",
            f"Selected: {best_explanation} (parsimony)",
        ]

        return result

    def _apply_abduction(
        self,
        beliefs: List[Belief],
        context: Dict[str, Any],
    ) -> List[ReasoningResult]:
        """Abdüksiyon kurallarını uygula."""
        results = []

        # Gözlem inançlarını bul
        observations = [
            b for b in beliefs
            if b.belief_type in (BeliefType.FACTUAL, BeliefType.INFERRED)
        ]

        # Açıklama gerektiren gözlemler için
        for obs in observations:
            if obs.evidence:  # Zaten açıklanmış
                continue

            # Olası açıklamalar (diğer inançlardan)
            possible = [
                b.subject + " caused " + obs.subject
                for b in beliefs
                if b != obs and b.subject != obs.subject
            ]

            if possible and len(possible) <= 5:  # Çok fazla seçenek yoksa
                result = self.abduce(
                    f"{obs.subject}: {obs.predicate}",
                    possible[:3],  # İlk 3 açıklama
                )
                if result.confidence > 0.3:
                    results.append(result)

        return results

    # ========================================================================
    # ANALOGY (Benzetme)
    # ========================================================================

    def reason_by_analogy(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        shared_properties: List[str],
    ) -> ReasoningResult:
        """
        Analoji ile akıl yürütme.

        A~B, A has P → B likely has P

        Örnek:
            "Mars Dünya'ya benzer" + "Dünya'da su var" → "Mars'ta su olabilir"
        """
        result = ReasoningResult(
            reasoning_type=ReasoningType.ANALOGY,
            premises=[
                f"Source: {source}",
                f"Target: {target}",
                f"Shared: {shared_properties}",
            ],
        )

        # Benzerlik skoru
        similarity = len(shared_properties) / max(len(source), len(target), 1)

        # Source'daki fazladan özellikler
        source_only = set(source.keys()) - set(shared_properties) - set(target.keys())

        if source_only and similarity > 0.3:
            transferred = list(source_only)[0]
            result.conclusion = f"by_analogy_{target.get('name', 'target')}_may_have_{transferred}"
            result.confidence = similarity * 0.5  # Analoji düşük güven
            result.validity = 0.4
            result.soundness = 0.4
            result.reasoning_chain = [
                f"Similarity: {similarity:.2f}",
                f"Shared properties: {shared_properties}",
                f"Transferred: {transferred}",
            ]
        else:
            result.conclusion = "insufficient_similarity"
            result.confidence = 0.0

        return result

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def add_rule(self, rule: InferenceRule) -> None:
        """Yeni çıkarım kuralı ekle."""
        self.rules.append(rule)

    def clear_cache(self) -> None:
        """Inference cache'i temizle."""
        self._inference_cache.clear()

    def get_applicable_rules(
        self,
        beliefs: List[Belief],
    ) -> List[InferenceRule]:
        """Uygulanabilir kuralları bul."""
        applicable = []
        for rule in self.rules:
            if len(beliefs) >= rule.premises_required:
                applicable.append(rule)
        return applicable


# ============================================================================
# FACTORY & SINGLETON
# ============================================================================

_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine(config: Optional[ReasoningConfig] = None) -> ReasoningEngine:
    """Reasoning engine singleton'ı al veya oluştur."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine(config)
    return _reasoning_engine


def create_reasoning_engine(config: Optional[ReasoningConfig] = None) -> ReasoningEngine:
    """Yeni reasoning engine oluştur."""
    return ReasoningEngine(config)
