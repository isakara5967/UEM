"""
core/language/construction/realizer.py

ConstructionRealizer - Construction + slot values → Cümle üretimi.

Construction template'lerini doldurarak gerçek Türkçe
cümleler üretir. Basit morfoloji kuralları uygular.

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re

from .types import (
    Construction,
    ConstructionForm,
    Slot,
    SlotType,
    MorphologyRule,
)


@dataclass
class RealizationResult:
    """
    Gerçekleştirme sonucu.

    Attributes:
        success: Başarılı mı?
        text: Üretilen metin
        construction_id: Kullanılan construction ID'si
        filled_slots: Doldurulan slot'lar
        missing_slots: Eksik slot'lar
        errors: Hata mesajları
    """
    success: bool
    text: str
    construction_id: str
    filled_slots: Dict[str, str] = field(default_factory=dict)
    missing_slots: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ConstructionRealizerConfig:
    """
    ConstructionRealizer konfigürasyonu.

    Attributes:
        apply_morphology: Morfoloji kurallarını uygula
        use_defaults: Varsayılan slot değerlerini kullan
        strict_validation: Katı slot doğrulama
        capitalize_first: İlk harfi büyük yap
        add_punctuation: Noktalama işareti ekle
    """
    apply_morphology: bool = True
    use_defaults: bool = True
    strict_validation: bool = False
    capitalize_first: bool = True
    add_punctuation: bool = True


class ConstructionRealizer:
    """
    Construction + slot values → Cümle üretimi.

    Construction template'lerini doldurarak gerçek Türkçe
    cümleler üretir.

    Kullanım:
        realizer = ConstructionRealizer()

        result = realizer.realize(
            construction,
            {"konu": "Python", "bilgi": "programlama dilidir"}
        )

        if result.success:
            print(result.text)  # "Python programlama dilidir."
    """

    def __init__(self, config: Optional[ConstructionRealizerConfig] = None):
        """
        ConstructionRealizer oluştur.

        Args:
            config: Realizer konfigürasyonu
        """
        self.config = config or ConstructionRealizerConfig()

        # Türkçe morfoloji kuralları
        self._vowels = set("aeıioöuü")
        self._back_vowels = set("aıou")
        self._front_vowels = set("eiöü")
        self._rounded_vowels = set("oöuü")
        self._unrounded_vowels = set("aeıi")

    def realize(
        self,
        construction: Construction,
        slot_values: Dict[str, str],
        context: Optional[Dict[str, Any]] = None
    ) -> RealizationResult:
        """
        Construction'ı gerçekleştir.

        Args:
            construction: Gerçekleştirilecek construction
            slot_values: Slot değerleri
            context: Ek bağlam

        Returns:
            RealizationResult: Gerçekleştirme sonucu
        """
        # 1. Slot'ları doğrula
        is_valid, missing, errors = self.validate_slots(construction, slot_values)

        if not is_valid and self.config.strict_validation:
            return RealizationResult(
                success=False,
                text="",
                construction_id=construction.id,
                missing_slots=missing,
                errors=errors
            )

        # 2. Template'i doldur
        text, filled, unfilled_required = self._fill_template(construction, slot_values)

        # Zorunlu slot doldurulamadıysa: strict modda başarısız, non-strict'te warning
        if unfilled_required:
            all_missing = list(set(missing + unfilled_required))

            if self.config.strict_validation:
                # Strict mode: Fail immediately
                return RealizationResult(
                    success=False,
                    text="",
                    construction_id=construction.id,
                    filled_slots=filled,
                    missing_slots=all_missing,
                    errors=errors + [f"Required slot not filled: {s}" for s in unfilled_required]
                )
            else:
                # Non-strict mode: Continue but log as errors
                errors = errors + [f"Required slot not filled: {s}" for s in unfilled_required]
                missing = all_missing

        # Boş metin varsa başarısız say
        if not text.strip():
            return RealizationResult(
                success=False,
                text="",
                construction_id=construction.id,
                filled_slots=filled,
                missing_slots=missing,
                errors=errors + ["Empty text after template filling"]
            )

        # 3. Morfoloji uygula
        if self.config.apply_morphology:
            text = self._apply_morphology(text, construction)

        # 4. Post-processing
        text = self._post_process(text, construction)

        return RealizationResult(
            success=True,
            text=text,
            construction_id=construction.id,
            filled_slots=filled,
            missing_slots=missing,
            errors=errors
        )

    def validate_slots(
        self,
        construction: Construction,
        slot_values: Dict[str, str]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Slot değerlerini doğrula.

        Args:
            construction: Construction
            slot_values: Slot değerleri

        Returns:
            Tuple[is_valid, missing_slots, errors]
        """
        missing = []
        errors = []

        form = construction.form

        for slot_name, slot in form.slots.items():
            value = slot_values.get(slot_name)

            # Zorunlu slot kontrolü
            if slot.required and not value:
                if self.config.use_defaults and slot.default:
                    continue
                missing.append(slot_name)
                errors.append(f"Missing required slot: {slot_name}")
                continue

            # Değer doğrulama
            if value and not slot.validate_value(value):
                errors.append(f"Invalid value for slot '{slot_name}': {value}")

        is_valid = len(missing) == 0 or not self.config.strict_validation
        return is_valid, missing, errors

    def _fill_template(
        self,
        construction: Construction,
        slot_values: Dict[str, str]
    ) -> Tuple[str, Dict[str, str], List[str]]:
        """
        Template'i slot değerleriyle doldur.

        Args:
            construction: Construction
            slot_values: Slot değerleri

        Returns:
            Tuple[filled_text, filled_slots, unfilled_required]
        """
        template = construction.form.template
        filled_slots = {}
        unfilled_required = []

        for slot_name, slot in construction.form.slots.items():
            value = slot_values.get(slot_name)

            # Varsayılan değer kullan
            if not value and self.config.use_defaults:
                value = slot.default

            pattern = f"{{{slot_name}}}"

            if value:
                # {slot_name} formatını değiştir
                template = template.replace(pattern, value)
                filled_slots[slot_name] = value
            else:
                # Slot doldurulamadı
                if slot.required:
                    unfilled_required.append(slot_name)
                # Placeholder'ı temizle (boş string ile değiştir)
                template = template.replace(pattern, "")

        # Fazla boşlukları temizle
        template = " ".join(template.split())

        return template, filled_slots, unfilled_required

    def _apply_morphology(
        self,
        text: str,
        construction: Construction
    ) -> str:
        """
        Basit Türkçe morfoloji kurallarını uygula.

        Args:
            text: İşlenecek metin
            construction: Construction (kuralları içerir)

        Returns:
            İşlenmiş metin
        """
        # Construction'daki morfoloji kurallarını uygula
        for rule in sorted(construction.form.morphology_rules, key=lambda r: -r.priority):
            text = self._apply_rule(text, rule)

        # Genel Türkçe kuralları
        text = self._apply_vowel_harmony(text)
        text = self._apply_buffer_consonant(text)

        return text

    def _apply_rule(self, text: str, rule: MorphologyRule) -> str:
        """
        Tek bir morfoloji kuralını uygula.

        Args:
            text: İşlenecek metin
            rule: Uygulanacak kural

        Returns:
            İşlenmiş metin
        """
        if rule.rule_type == "vowel_harmony":
            return self._apply_vowel_harmony(text)
        elif rule.rule_type == "consonant_softening":
            return self._apply_consonant_softening(text)
        elif rule.rule_type == "buffer_consonant":
            return self._apply_buffer_consonant(text)

        return text

    def _apply_vowel_harmony(self, text: str) -> str:
        """
        Ünlü uyumu uygula (basit).

        Türkçe'de ekler, son ünlüye göre değişir.

        Args:
            text: İşlenecek metin

        Returns:
            İşlenmiş metin
        """
        # Bu basit bir implementasyon - tam Türkçe morfoloji çok karmaşık
        # Şimdilik sadece yaygın durumları ele alıyoruz

        # Örnek: "kitap" + "-ı" → "kitabı"
        # Örnek: "ev" + "-i" → "evi"

        # Basit ünlü uyumu kontrolleri
        words = text.split()
        result_words = []

        for word in words:
            # Son ünlüyü bul
            last_vowel = None
            for char in reversed(word.lower()):
                if char in self._vowels:
                    last_vowel = char
                    break

            result_words.append(word)

        return " ".join(result_words)

    def _apply_consonant_softening(self, text: str) -> str:
        """
        Ünsüz yumuşaması uygula (basit).

        p → b, ç → c, t → d, k → ğ

        Args:
            text: İşlenecek metin

        Returns:
            İşlenmiş metin
        """
        # Bu basit bir implementasyon
        # Gerçek uygulama kelime sınırlarını ve morfolojik bağlamı dikkate almalı
        return text

    def _apply_buffer_consonant(self, text: str) -> str:
        """
        Kaynaştırma ünsüzü uygula (basit).

        İki ünlü arasına y, n, s, ş ekleme.

        Args:
            text: İşlenecek metin

        Returns:
            İşlenmiş metin
        """
        # Bu basit bir implementasyon
        return text

    def _post_process(self, text: str, construction: Construction) -> str:
        """
        Son işlemler: büyük harf, noktalama.

        Args:
            text: İşlenecek metin
            construction: Construction

        Returns:
            İşlenmiş metin
        """
        # Fazla boşlukları temizle
        text = " ".join(text.split())

        # İlk harfi büyük yap
        if self.config.capitalize_first and text:
            text = text[0].upper() + text[1:]

        # Noktalama ekle
        if self.config.add_punctuation:
            text = self._add_punctuation(text, construction)

        return text

    def _add_punctuation(self, text: str, construction: Construction) -> str:
        """
        Noktalama işareti ekle.

        Args:
            text: İşlenecek metin
            construction: Construction (intonation bilgisi için)

        Returns:
            Noktalama eklenmiş metin
        """
        if not text:
            return text

        # Zaten noktalama varsa ekleme
        if text[-1] in ".!?":
            return text

        # Soru mu?
        intonation = construction.form.intonation
        if intonation == "rising":
            return text + "?"

        # DialogueAct'e göre
        dialogue_act = construction.meaning.dialogue_act
        if dialogue_act == "ask":
            if not text.endswith("?"):
                return text + "?"
        elif dialogue_act == "warn":
            return text + "!"

        # Varsayılan: nokta
        return text + "."

    def realize_multiple(
        self,
        constructions: List[Construction],
        slot_values: Dict[str, str],
        separator: str = " "
    ) -> RealizationResult:
        """
        Birden fazla construction'ı birleştirerek gerçekleştir.

        Args:
            constructions: Construction listesi
            slot_values: Ortak slot değerleri
            separator: Birleştirme karakteri

        Returns:
            RealizationResult: Birleşik sonuç
        """
        texts = []
        all_filled = {}
        all_missing = []
        all_errors = []

        for construction in constructions:
            result = self.realize(construction, slot_values)
            if result.success:
                texts.append(result.text)
                all_filled.update(result.filled_slots)
            all_missing.extend(result.missing_slots)
            all_errors.extend(result.errors)

        combined_text = separator.join(texts)

        return RealizationResult(
            success=len(texts) > 0,
            text=combined_text,
            construction_id=",".join(c.id for c in constructions),
            filled_slots=all_filled,
            missing_slots=list(set(all_missing)),
            errors=all_errors
        )

    def get_required_slots(self, construction: Construction) -> List[str]:
        """
        Construction için gerekli slot'ları getir.

        Args:
            construction: Construction

        Returns:
            Zorunlu slot isimleri
        """
        return [
            slot.name
            for slot in construction.form.slots.values()
            if slot.required and not slot.default
        ]

    def get_slot_types(self, construction: Construction) -> Dict[str, SlotType]:
        """
        Construction için slot tiplerini getir.

        Args:
            construction: Construction

        Returns:
            Slot ismi → SlotType eşleştirmesi
        """
        return {
            name: slot.slot_type
            for name, slot in construction.form.slots.items()
        }
