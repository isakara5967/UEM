"""
core/language/construction/types.py

Construction Grammar Types - 3 katmanlı dil yapısı tipleri.
UEM v2 - Goldberg Construction Grammar'dan esinlenilmiş.

Özellikler:
- ConstructionLevel: DEEP, MIDDLE, SURFACE katmanları
- SlotType: 10 farklı slot türü
- Slot: Template'deki değişken yeri
- ConstructionForm: Yüzey yapı (template + slots + rules)
- ConstructionMeaning: Anlam (dialogue_act + conditions + effects)
- Construction: Tam yapı (form + meaning + metadata)

Construction Grammar Katmanları:
- DEEP (Derin):
    - Konuşma eylemleri (DialogueAct)
    - Argüman yapıları
    - Semantik roller
    - Soyut niyet temsili

- MIDDLE (Orta):
    - Cümle iskeletleri
    - Bağlaç yapıları
    - Slot tanımları
    - Sözdizimsel pattern'ler

- SURFACE (Yüzey):
    - Türkçe morfoloji
    - Ünlü/ünsüz uyumu
    - Ek sıraları
    - Somut kelime formu
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class ConstructionLevel(str, Enum):
    """
    Construction katman seviyeleri.

    Katmanlar:
    - DEEP: Anlam ve niyet katmanı (en soyut)
    - MIDDLE: Sözdizimsel yapı katmanı
    - SURFACE: Morfolojik gerçekleşme (en somut)
    """
    DEEP = "deep"               # Semantic/pragmatic level
    MIDDLE = "middle"           # Syntactic level
    SURFACE = "surface"         # Morphological level


class SlotType(str, Enum):
    """
    Slot türleri - Template'deki değişken tipleri.

    Türler:
    - ENTITY: İsim, varlık (Ali, kitap, ev)
    - VERB: Fiil (gel, git, yap)
    - ADJECTIVE: Sıfat (güzel, hızlı, büyük)
    - ADVERB: Zarf (hızlıca, sessizce)
    - NUMBER: Sayı (bir, iki, on)
    - TIME: Zaman ifadesi (yarın, dün, şimdi)
    - PLACE: Yer ifadesi (burada, orada, evde)
    - REASON: Sebep ifadesi (çünkü..., için...)
    - CONNECTOR: Bağlaç (ve, ama, çünkü)
    - FILLER: Dolgu kelime (yani, işte, şey)
    """
    ENTITY = "entity"           # İsim, varlık
    VERB = "verb"               # Fiil
    ADJECTIVE = "adjective"     # Sıfat
    ADVERB = "adverb"           # Zarf
    NUMBER = "number"           # Sayı
    TIME = "time"               # Zaman ifadesi
    PLACE = "place"             # Yer ifadesi
    REASON = "reason"           # Sebep ifadesi
    CONNECTOR = "connector"     # Bağlaç
    FILLER = "filler"           # Dolgu kelime


@dataclass
class Slot:
    """
    Template slot tanımı.

    Template'deki {placeholder} karşılığı.
    Her slot bir tip ve kısıtlamalara sahip.

    Attributes:
        id: Benzersiz slot ID'si
        name: Slot adı (template'deki isim)
        slot_type: Slot türü
        required: Zorunlu mu?
        default: Varsayılan değer
        constraints: Ek kısıtlamalar
        description: Slot açıklaması
    """
    id: str
    name: str                           # "subject", "object", "verb"
    slot_type: SlotType
    required: bool = True
    default: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

    def validate_value(self, value: str) -> bool:
        """
        Değerin bu slot için geçerli olup olmadığını kontrol et.

        Args:
            value: Kontrol edilecek değer

        Returns:
            Geçerli ise True
        """
        if not value and self.required and not self.default:
            return False

        # Check constraints
        if "min_length" in self.constraints:
            if len(value) < self.constraints["min_length"]:
                return False

        if "max_length" in self.constraints:
            if len(value) > self.constraints["max_length"]:
                return False

        if "allowed_values" in self.constraints:
            if value not in self.constraints["allowed_values"]:
                return False

        return True

    def get_value(self, provided: Optional[str]) -> Optional[str]:
        """
        Slot değerini getir (varsayılanı uygula).

        Args:
            provided: Sağlanan değer

        Returns:
            Kullanılacak değer
        """
        if provided:
            return provided
        return self.default


@dataclass
class MorphologyRule:
    """
    Morfoloji kuralı - Yüzey katmanı ek kuralları.

    Türkçe için önemli:
    - Ünlü uyumu (büyük ünlü, küçük ünlü)
    - Ünsüz yumuşaması
    - Ek sırası

    Attributes:
        id: Benzersiz kural ID'si
        name: Kural adı
        rule_type: Kural türü
        condition: Uygulama koşulu
        transformation: Dönüşüm kuralı
        priority: Uygulama önceliği (yüksek=önce)
        examples: Örnek dönüşümler
    """
    id: str
    name: str
    rule_type: str                      # "vowel_harmony", "consonant_softening", "suffix_order"
    condition: str                      # Ne zaman uygulanır
    transformation: str                 # Nasıl dönüştürülür
    priority: int = 0                   # Uygulama sırası
    examples: List[str] = field(default_factory=list)


@dataclass
class ConstructionForm:
    """
    Construction'ın yüzey formu.

    Template + slotlar + morfoloji kuralları.

    Attributes:
        template: Template string ("{subject} {verb}")
        slots: Slot tanımları
        morphology_rules: Morfoloji kuralları
        word_order: Kelime sırası bilgisi
        intonation: Tonlama bilgisi
    """
    template: str
    slots: Dict[str, Slot] = field(default_factory=dict)
    morphology_rules: List[MorphologyRule] = field(default_factory=list)
    word_order: Optional[str] = None    # "SOV", "SVO", "free"
    intonation: Optional[str] = None    # "rising", "falling", "neutral"

    def get_slot_names(self) -> List[str]:
        """Template'deki slot isimlerini getir."""
        return list(self.slots.keys())

    def has_slot(self, name: str) -> bool:
        """Belirtilen slot var mı?"""
        return name in self.slots

    def get_required_slots(self) -> List[Slot]:
        """Zorunlu slotları getir."""
        return [s for s in self.slots.values() if s.required]

    def validate_slots(self, values: Dict[str, str]) -> List[str]:
        """
        Slot değerlerini doğrula.

        Args:
            values: Slot değerleri

        Returns:
            Hata mesajları listesi (boş=geçerli)
        """
        errors = []

        for name, slot in self.slots.items():
            value = values.get(name)

            if slot.required and not value and not slot.default:
                errors.append(f"Missing required slot: {name}")
            elif value and not slot.validate_value(value):
                errors.append(f"Invalid value for slot {name}: {value}")

        return errors


@dataclass
class ConstructionMeaning:
    """
    Construction'ın anlamı.

    DialogueAct + koşullar + etkiler.

    Attributes:
        dialogue_act: Bu construction hangi dialogue act'i ifade eder
        semantic_roles: Semantik roller
        preconditions: Ön koşullar
        effects: Etkiler
        illocutionary_force: İllocutionary güç
        context_requirements: Bağlam gereksinimleri
    """
    dialogue_act: str                   # DialogueAct.value
    semantic_roles: Dict[str, str] = field(default_factory=dict)  # "agent": "subject", "patient": "object"
    preconditions: List[str] = field(default_factory=list)        # ["user_asked_question", "topic_is_clear"]
    effects: List[str] = field(default_factory=list)              # ["user_informed", "question_answered"]
    illocutionary_force: Optional[str] = None                     # "assertion", "question", "command", "promise"
    context_requirements: Dict[str, Any] = field(default_factory=dict)

    def matches_context(self, context: Dict[str, Any]) -> bool:
        """
        Bu meaning mevcut bağlamla uyumlu mu?

        Args:
            context: Mevcut bağlam

        Returns:
            Uyumlu ise True
        """
        for key, required_value in self.context_requirements.items():
            if key not in context:
                return False
            if context[key] != required_value:
                return False
        return True


@dataclass
class Construction:
    """
    3 katmanlı Construction Grammar yapısı.

    Form + Meaning + Metadata.
    Her construction, belirli bir dil yapısını temsil eder.

    Örnekler:
    - DEEP: "INFORM about X" → soyut bilgi verme niyeti
    - MIDDLE: "{subject} {object}'ı {verb}" → cümle iskeleti
    - SURFACE: "Ali kitabı okudu" → gerçek cümle

    Attributes:
        id: Benzersiz construction ID'si
        level: Katman seviyesi
        form: Yüzey formu
        meaning: Anlam
        success_count: Başarılı kullanım sayısı
        failure_count: Başarısız kullanım sayısı
        confidence: Güven skoru (0.0-1.0)
        source: Kaynak ("human", "learned", "generated")
        parent_id: Üst katman construction ID'si
        children_ids: Alt katman construction ID'leri
        created_at: Oluşturulma zamanı
        last_used: Son kullanım zamanı
        extra_data: Ek veriler
    """
    id: str
    level: ConstructionLevel
    form: ConstructionForm
    meaning: ConstructionMeaning
    success_count: int = 0
    failure_count: int = 0
    confidence: float = 0.5
    source: str = "human"               # "human", "learned", "generated"
    parent_id: Optional[str] = None     # Üst katman bağlantısı
    children_ids: List[str] = field(default_factory=list)  # Alt katman bağlantıları
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        valid_sources = {"human", "learned", "generated"}
        if self.source not in valid_sources:
            raise ValueError(f"source must be one of {valid_sources}, got {self.source}")

    @property
    def success_rate(self) -> float:
        """Başarı oranı hesapla."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5

    @property
    def total_uses(self) -> int:
        """Toplam kullanım sayısı."""
        return self.success_count + self.failure_count

    @property
    def is_reliable(self) -> bool:
        """Güvenilir mi? (Yeterli kullanım + yüksek başarı)"""
        return self.total_uses >= 3 and self.success_rate >= 0.7

    def record_success(self) -> None:
        """Başarılı kullanım kaydet."""
        self.success_count += 1
        self.last_used = datetime.now()
        # Güveni artır
        self.confidence = min(1.0, self.confidence + 0.05)

    def record_failure(self) -> None:
        """Başarısız kullanım kaydet."""
        self.failure_count += 1
        self.last_used = datetime.now()
        # Güveni azalt
        self.confidence = max(0.0, self.confidence - 0.1)

    def realize(self, slot_values: Dict[str, str]) -> Optional[str]:
        """
        Construction'ı gerçekleştir (template'i doldur).

        Args:
            slot_values: Slot değerleri

        Returns:
            Gerçekleştirilmiş string veya None (hata varsa)
        """
        # Validate slots
        errors = self.form.validate_slots(slot_values)
        if errors:
            return None

        # Fill template
        result = self.form.template

        for name, slot in self.form.slots.items():
            value = slot.get_value(slot_values.get(name))
            if value:
                result = result.replace(f"{{{name}}}", value)

        # Apply morphology rules (simplified)
        # Full implementation would handle Turkish morphology
        for rule in sorted(self.form.morphology_rules, key=lambda r: -r.priority):
            # Placeholder for morphology rule application
            pass

        return result

    def matches_dialogue_act(self, dialogue_act: str) -> bool:
        """Bu construction belirtilen dialogue act için uygun mu?"""
        return self.meaning.dialogue_act == dialogue_act

    def to_dict(self) -> Dict[str, Any]:
        """Sözlük temsiline dönüştür."""
        return {
            "id": self.id,
            "level": self.level.value,
            "template": self.form.template,
            "dialogue_act": self.meaning.dialogue_act,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


def generate_construction_id() -> str:
    """Generate unique construction ID."""
    return f"cons_{uuid.uuid4().hex[:12]}"


def generate_slot_id() -> str:
    """Generate unique slot ID."""
    return f"slot_{uuid.uuid4().hex[:12]}"


def generate_morphology_rule_id() -> str:
    """Generate unique morphology rule ID."""
    return f"morph_{uuid.uuid4().hex[:12]}"
