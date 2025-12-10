"""
core/language/dialogue/situation_builder.py

SituationBuilder - Perception + Memory + Cognition → SituationModel

Kullanıcı mesajından durum modeli çıkarır:
- Aktörler kim?
- Niyetler ne?
- Riskler ne?
- Duygusal durum ne?
- Ne kadar anladık?

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from core.utils.text import normalize_turkish
from core.language.intent import IntentRecognizer, IntentCategory

from .types import (
    SituationModel,
    Actor,
    Intention,
    Risk,
    EmotionalState,
    generate_situation_id,
)


def _generate_intention_id() -> str:
    """Generate unique intention ID."""
    return f"int_{uuid.uuid4().hex[:12]}"


@dataclass
class SituationBuilderConfig:
    """
    SituationBuilder konfigürasyonu.

    Attributes:
        max_actors: Maksimum aktör sayısı
        max_intentions: Maksimum niyet sayısı
        max_risks: Maksimum risk sayısı
        min_understanding_threshold: Minimum anlama eşiği
        enable_emotion_detection: Duygu algılama aktif mi?
        enable_risk_detection: Risk algılama aktif mi?
    """
    max_actors: int = 10
    max_intentions: int = 20
    max_risks: int = 10
    min_understanding_threshold: float = 0.3
    enable_emotion_detection: bool = True
    enable_risk_detection: bool = True


class SituationBuilder:
    """
    Perception + Memory + Cognition → SituationModel

    Kullanıcı mesajından durum modeli çıkarır:
    - Aktörler kim?
    - Niyetler ne?
    - Riskler ne?
    - Duygusal durum ne?
    - Ne kadar anladık?

    Kullanım:
        builder = SituationBuilder()
        situation = builder.build("Merhaba, nasılsın?")
        print(situation.topic_domain)  # "general"
        print(situation.understanding_score)  # 0.5

        # Bağlam ile
        context = [
            {"role": "user", "content": "Bir sorunum var"},
            {"role": "assistant", "content": "Dinliyorum"}
        ]
        situation = builder.build("Çok üzgünüm", context)
    """

    def __init__(
        self,
        config: Optional[SituationBuilderConfig] = None,
        perception_processor: Optional[Any] = None,
        memory_search: Optional[Any] = None,
        cognition_processor: Optional[Any] = None
    ):
        """
        SituationBuilder oluştur.

        Args:
            config: Builder konfigürasyonu
            perception_processor: Perception modülü (opsiyonel)
            memory_search: Memory search modülü (opsiyonel)
            cognition_processor: Cognition modülü (opsiyonel)
        """
        self.config = config or SituationBuilderConfig()
        self.perception = perception_processor
        self.memory = memory_search
        self.cognition = cognition_processor

        # Intent recognizer
        self.intent_recognizer = IntentRecognizer()

    def build(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SituationModel:
        """
        Ana build metodu - SituationModel oluştur.

        Args:
            user_message: Kullanıcı mesajı
            conversation_context: Konuşma geçmişi [{"role": "user", "content": "..."}]
            metadata: Ek metadata

        Returns:
            SituationModel: Durum modeli
        """
        situation_id = generate_situation_id()

        # 1. Aktörleri çıkar
        actors = self._extract_actors(user_message, conversation_context)

        # 2. Niyetleri çıkar (context-aware)
        intentions = self._extract_intentions(user_message, actors, conversation_context)

        # 3. Riskleri değerlendir
        risks: List[Risk] = []
        if self.config.enable_risk_detection:
            risks = self._detect_risks(user_message, intentions)

        # 4. Duygusal durumu algıla
        emotional_state: Optional[EmotionalState] = None
        if self.config.enable_emotion_detection:
            emotional_state = self._detect_emotion(user_message)

        # 5. Konu alanını belirle
        topic_domain = self._determine_topic(user_message)

        # 6. Bağlam özeti oluştur
        context_summary = self._summarize_context(user_message, conversation_context)

        # 7. Anlama skorunu hesapla
        understanding_score = self._calculate_understanding(
            actors, intentions, risks, emotional_state
        )

        return SituationModel(
            id=situation_id,
            actors=actors,
            intentions=intentions,
            risks=risks,
            emotional_state=emotional_state,
            topic_domain=topic_domain,
            understanding_score=understanding_score,
            context={"summary": context_summary, **(metadata or {})}
        )

    def _extract_actors(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> List[Actor]:
        """
        Mesajdan aktörleri çıkar.

        Her zaman user ve assistant (UEM) var.
        Ek olarak mesajda 3. kişiler varsa onları da ekle.

        Args:
            message: Kullanıcı mesajı
            context: Konuşma geçmişi

        Returns:
            List[Actor]: Aktör listesi
        """
        actors = []

        # Her zaman user ve assistant var
        actors.append(Actor(
            id="user",
            role="user",
            name=None,
            traits={},
            context={}
        ))
        actors.append(Actor(
            id="assistant",
            role="assistant",
            name="UEM",
            traits={},
            context={}
        ))

        # Mesajda 3. kişiler var mı?
        # Basit heuristik: isim, "o", "onlar", "arkadaşım" vs.
        third_party_indicators = [
            "arkadasim", "annem", "babam", "kardesim", "esim",
            "mudurum", "ogretmenim", "doktorum", "komsum",
            "o ", "onlar", "onun", "ona"
        ]

        message_normalized = normalize_turkish(message)
        found_count = 0
        for i, indicator in enumerate(third_party_indicators):
            if indicator in message_normalized:
                actors.append(Actor(
                    id=f"third_party_{i}",
                    role="third_party",
                    name=indicator.strip(),
                    traits={"mentioned_as": indicator},
                    context={}
                ))
                found_count += 1
                if len(actors) >= self.config.max_actors:
                    break

        return actors[:self.config.max_actors]

    def _extract_intentions(
        self,
        message: str,
        actors: List[Actor],
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> List[Intention]:
        """
        Mesajdan niyetleri çıkar.

        Yeni intent recognition sistemi kullanır (IntentRecognizer).
        Context-aware: Önceki mesajlardan yararlanır.

        Args:
            message: Kullanıcı mesajı
            actors: Aktör listesi
            conversation_context: Konuşma geçmişi (context-aware için)

        Returns:
            List[Intention]: Niyet listesi
        """
        intentions = []

        # User actor'ü bul
        user_actor = next((a for a in actors if a.role == "user"), None)
        if not user_actor:
            return intentions

        # IntentRecognizer ile intent tanıma
        intent_result = self.intent_recognizer.recognize(message)

        # Context-aware confidence boost
        # Eğer önceki mesajlarla ilişkiliyse confidence artır
        if conversation_context and len(conversation_context) >= 2:
            # Basit followup detection
            from core.utils.text import normalize_turkish
            msg_normalized = normalize_turkish(message)
            followup_indicators = ["peki", "ya", "o zaman", "ee", "bunun", "onun"]
            is_followup = any(ind in msg_normalized for ind in followup_indicators)

            if is_followup:
                # Followup ise confidence'ı hafifçe artır
                intent_result.confidence = min(1.0, intent_result.confidence * 1.1)

        # Primary intent
        if intent_result.primary != IntentCategory.UNKNOWN:
            intentions.append(Intention(
                id=_generate_intention_id(),
                actor_id=user_actor.id,
                goal=intent_result.primary.value,
                sub_goals=[],
                confidence=intent_result.confidence,
                evidence=[f"IntentRecognizer matched: {intent_result.primary.value}"]
            ))

        # Secondary intent (compound intent varsa)
        if intent_result.secondary:
            # Secondary için confidence biraz daha düşük
            secondary_confidence = intent_result.confidence * 0.8
            intentions.append(Intention(
                id=_generate_intention_id(),
                actor_id=user_actor.id,
                goal=intent_result.secondary.value,
                sub_goals=[],
                confidence=secondary_confidence,
                evidence=[f"IntentRecognizer matched (secondary): {intent_result.secondary.value}"]
            ))

        # Diğer eşleşmeler (eğer yer varsa)
        remaining_slots = self.config.max_intentions - len(intentions)
        if remaining_slots > 0 and intent_result.all_matches:
            # İlk 2'yi zaten ekledik, kalanları ekle
            for match in intent_result.all_matches[2:2+remaining_slots]:
                if match.category not in [IntentCategory.UNKNOWN]:
                    intentions.append(Intention(
                        id=_generate_intention_id(),
                        actor_id=user_actor.id,
                        goal=match.category.value,
                        sub_goals=[],
                        confidence=match.confidence * 0.7,  # Daha düşük confidence
                        evidence=[f"IntentRecognizer matched: {match.matched_pattern}"]
                    ))

        # Eğer hiç niyet bulunamadıysa, genel bir niyet ekle
        if not intentions:
            intentions.append(Intention(
                id=_generate_intention_id(),
                actor_id=user_actor.id,
                goal="communicate",
                sub_goals=[],
                confidence=0.5,
                evidence=["Default intention - no specific intent recognized"]
            ))

        return intentions[:self.config.max_intentions]

    def _detect_risks(
        self,
        message: str,
        intentions: List[Intention]
    ) -> List[Risk]:
        """
        Mesajdan riskleri algıla.

        Args:
            message: Kullanıcı mesajı
            intentions: Niyet listesi

        Returns:
            List[Risk]: Risk listesi
        """
        risks = []
        message_normalized = normalize_turkish(message)

        # Risk pattern'leri - normalized keywords
        risk_patterns = {
            "safety": {
                "keywords": ["intihar", "kendine zarar", "olmek", "yaralanma", "kaza"],
                "level": 0.9
            },
            "emotional": {
                "keywords": ["depresyon", "anksiyete", "panik", "cok kotu", "dayanamiyorum"],
                "level": 0.7
            },
            "ethical": {
                "keywords": ["yasadisi", "hile", "dolandir", "cal", "hackle"],
                "level": 0.8
            },
            "relational": {
                "keywords": ["ayrilik", "bosanma", "kavga", "terk"],
                "level": 0.5
            }
        }

        for risk_type, config in risk_patterns.items():
            for keyword in config["keywords"]:
                if keyword in message_normalized:
                    mitigations = self._get_risk_mitigations(risk_type)
                    risks.append(Risk(
                        category=risk_type,
                        level=config["level"],
                        description=f"'{keyword}' ifadesi algılandı",
                        mitigation=mitigations[0] if mitigations else None
                    ))
                    break

        return risks[:self.config.max_risks]

    def _get_risk_mitigations(self, risk_type: str) -> List[str]:
        """
        Risk tipine göre önerilen aksiyonlar.

        Args:
            risk_type: Risk kategorisi

        Returns:
            List[str]: Azaltma önerileri
        """
        mitigations = {
            "safety": ["Profesyonel yardım öner", "Acil durum bilgisi ver"],
            "emotional": ["Empati kur", "Destek kaynakları öner"],
            "ethical": ["Etik sınırları belirt", "Alternatif öner"],
            "relational": ["Dinle", "Tarafsız kal"]
        }
        return mitigations.get(risk_type, ["Dikkatli ol"])

    def _detect_emotion(self, message: str) -> EmotionalState:
        """
        Mesajdan duygusal durumu algıla.

        PAD (Pleasure-Arousal-Dominance) modeli kullanır.

        Args:
            message: Kullanıcı mesajı

        Returns:
            EmotionalState: Duygusal durum
        """
        message_normalized = normalize_turkish(message)

        # Basit duygu pattern'leri - normalized words
        valence = 0.0
        arousal = 0.0
        primary_emotion: Optional[str] = None

        positive_words = ["mutlu", "harika", "guzel", "tesekkur", "seviyorum", "super"]
        negative_words = ["uzgun", "kotu", "sinirli", "kizgin", "nefret", "berbat"]
        high_arousal_words = ["heyecan", "panik", "acil", "cok", "asiri"]
        low_arousal_words = ["sakin", "huzur", "rahat", "yavas"]

        for word in positive_words:
            if word in message_normalized:
                valence += 0.3
                primary_emotion = primary_emotion or "positive"

        for word in negative_words:
            if word in message_normalized:
                valence -= 0.3
                primary_emotion = primary_emotion or "negative"

        for word in high_arousal_words:
            if word in message_normalized:
                arousal += 0.2

        for word in low_arousal_words:
            if word in message_normalized:
                arousal -= 0.2

        # Sınırla
        valence = max(-1.0, min(1.0, valence))
        arousal = max(-1.0, min(1.0, arousal))

        return EmotionalState(
            valence=valence,
            arousal=arousal,
            dominance=0.0,
            primary_emotion=primary_emotion,
            secondary_emotions=[],
            confidence=0.5
        )

    def _determine_topic(self, message: str) -> str:
        """
        Mesajın konu alanını belirle.

        Args:
            message: Kullanıcı mesajı

        Returns:
            str: Konu alanı
        """
        message_normalized = normalize_turkish(message)

        topic_patterns = {
            "technology": ["bilgisayar", "yazilim", "kod", "program", "internet"],
            "health": ["saglik", "hastalik", "doktor", "ilac", "agri"],
            "relationships": ["iliski", "aile", "arkadas", "sevgili"],
            "education": ["okul", "ders", "sinav", "ogren", "egitim"],  # Before work to prioritize
            "work": ["is", "kariyer", "maas", "patron", "calisma"],
            "emotions": ["hissediyorum", "duygu", "mutlu", "uzgun"],
            "help": ["yardim", "nasil", "ne yapmali"]
        }

        for topic, patterns in topic_patterns.items():
            for pattern in patterns:
                if pattern in message_normalized:
                    return topic

        return "general"

    def _summarize_context(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Bağlam özeti oluştur.

        Args:
            message: Kullanıcı mesajı
            context: Konuşma geçmişi

        Returns:
            str: Bağlam özeti
        """
        if not context:
            truncated = message[:100] + "..." if len(message) > 100 else message
            return f"Kullanıcı mesajı: {truncated}"

        summary_parts = []
        for turn in context[-3:]:  # Son 3 tur
            role = turn.get("role", "unknown")
            content = turn.get("content", "")[:50]
            summary_parts.append(f"{role}: {content}...")

        return " | ".join(summary_parts)

    def _calculate_understanding(
        self,
        actors: List[Actor],
        intentions: List[Intention],
        risks: List[Risk],
        emotional_state: Optional[EmotionalState]
    ) -> float:
        """
        Durumu ne kadar anladığımızı hesapla.

        Args:
            actors: Aktör listesi
            intentions: Niyet listesi
            risks: Risk listesi
            emotional_state: Duygusal durum

        Returns:
            float: Anlama skoru (0.0-1.0)
        """
        score = 0.3  # Base score

        # Aktör bulundu (user + assistant + en az bir 3. kişi)
        if len(actors) > 2:
            score += 0.1

        # Niyet bulundu
        if intentions:
            avg_confidence = sum(i.confidence for i in intentions) / len(intentions)
            score += 0.2 * avg_confidence

        # Risk değerlendirildi
        if risks:
            score += 0.1

        # Duygu algılandı
        if emotional_state and emotional_state.primary_emotion:
            score += 0.1

        # Yüksek güvenli niyet
        high_confidence_intents = [i for i in intentions if i.confidence > 0.7]
        if high_confidence_intents:
            score += 0.1

        return min(1.0, score)
