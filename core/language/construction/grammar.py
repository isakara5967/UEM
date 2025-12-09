"""
core/language/construction/grammar.py

ConstructionGrammar - 3 katmanlı Construction yönetimi.

Construction Grammar'ı yönetir:
- DEEP: Konuşma eylemleri, semantik yapılar
- MIDDLE: Cümle iskeletleri, sözdizimi
- SURFACE: Morfoloji, somut form

UEM v2 - Thought-to-Speech Pipeline bileşeni.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import (
    Construction,
    ConstructionLevel,
    ConstructionForm,
    ConstructionMeaning,
    Slot,
    SlotType,
    generate_construction_id,
    generate_slot_id,
)


@dataclass
class ConstructionGrammarConfig:
    """
    ConstructionGrammar konfigürasyonu.

    Attributes:
        load_defaults: Varsayılan construction'ları yükle
        max_constructions_per_level: Katman başına maksimum construction
        auto_create_connections: Katmanlar arası bağlantıları otomatik oluştur
    """
    load_defaults: bool = True
    max_constructions_per_level: int = 100
    auto_create_connections: bool = True


class ConstructionGrammar:
    """
    3 katmanlı Construction Grammar yöneticisi.

    Goldberg Construction Grammar'dan esinlenilmiş 3 katmanlı
    dil yapısı yönetimi sağlar.

    Kullanım:
        grammar = ConstructionGrammar()
        grammar.load_defaults()  # Varsayılan Türkçe construction'ları yükle

        # Katmana göre getir
        deep_constructions = grammar.get_by_level(ConstructionLevel.DEEP)

        # DialogueAct'e göre getir
        inform_constructions = grammar.get_by_dialogue_act("inform")

        # MessagePlan'a uygun olanları bul
        matching = grammar.find_matching(message_plan)
    """

    def __init__(self, config: Optional[ConstructionGrammarConfig] = None):
        """
        ConstructionGrammar oluştur.

        Args:
            config: Grammar konfigürasyonu
        """
        self.config = config or ConstructionGrammarConfig()

        # Construction storage by level
        self._constructions: Dict[ConstructionLevel, Dict[str, Construction]] = {
            ConstructionLevel.DEEP: {},
            ConstructionLevel.MIDDLE: {},
            ConstructionLevel.SURFACE: {},
        }

        # Index by dialogue_act for fast lookup
        self._by_dialogue_act: Dict[str, List[str]] = {}

        # Load defaults if configured
        if self.config.load_defaults:
            self.load_defaults()

    def add_construction(self, construction: Construction) -> bool:
        """
        Construction ekle.

        Args:
            construction: Eklenecek construction

        Returns:
            bool: Başarılı ise True
        """
        level = construction.level

        # Check max limit
        if len(self._constructions[level]) >= self.config.max_constructions_per_level:
            return False

        # Add to level storage
        self._constructions[level][construction.id] = construction

        # Add to dialogue_act index
        dialogue_act = construction.meaning.dialogue_act
        if dialogue_act not in self._by_dialogue_act:
            self._by_dialogue_act[dialogue_act] = []
        if construction.id not in self._by_dialogue_act[dialogue_act]:
            self._by_dialogue_act[dialogue_act].append(construction.id)

        return True

    def remove_construction(self, construction_id: str) -> bool:
        """
        Construction kaldır.

        Args:
            construction_id: Kaldırılacak construction ID'si

        Returns:
            bool: Başarılı ise True
        """
        for level in ConstructionLevel:
            if construction_id in self._constructions[level]:
                construction = self._constructions[level][construction_id]

                # Remove from dialogue_act index
                dialogue_act = construction.meaning.dialogue_act
                if dialogue_act in self._by_dialogue_act:
                    if construction_id in self._by_dialogue_act[dialogue_act]:
                        self._by_dialogue_act[dialogue_act].remove(construction_id)

                # Remove from level storage
                del self._constructions[level][construction_id]
                return True

        return False

    def get_construction(self, construction_id: str) -> Optional[Construction]:
        """
        ID ile construction getir.

        Args:
            construction_id: Construction ID'si

        Returns:
            Construction veya None
        """
        for level in ConstructionLevel:
            if construction_id in self._constructions[level]:
                return self._constructions[level][construction_id]
        return None

    def get_by_level(self, level: ConstructionLevel) -> List[Construction]:
        """
        Katmana göre construction'ları getir.

        Args:
            level: Katman seviyesi

        Returns:
            O katmandaki construction'lar
        """
        return list(self._constructions[level].values())

    def get_by_dialogue_act(self, dialogue_act: str) -> List[Construction]:
        """
        DialogueAct'e göre construction'ları getir.

        Args:
            dialogue_act: DialogueAct değeri (örn: "inform", "warn")

        Returns:
            Uygun construction'lar
        """
        if dialogue_act not in self._by_dialogue_act:
            return []

        construction_ids = self._by_dialogue_act[dialogue_act]
        constructions = []

        for cid in construction_ids:
            construction = self.get_construction(cid)
            if construction:
                constructions.append(construction)

        return constructions

    def find_matching(
        self,
        dialogue_acts: List[str],
        tone: Optional[str] = None,
        constraints: Optional[List[str]] = None
    ) -> List[Construction]:
        """
        Verilen kriterlere uyan construction'ları bul.

        Args:
            dialogue_acts: DialogueAct listesi
            tone: İstenen ton (opsiyonel)
            constraints: Kısıtlar (opsiyonel)

        Returns:
            Eşleşen construction'lar (skorlanmış)
        """
        matching = []

        # Get constructions for each dialogue act
        for act in dialogue_acts:
            constructions = self.get_by_dialogue_act(act)
            for construction in constructions:
                # Skip if already added
                if construction in matching:
                    continue

                # Check tone match if specified
                if tone:
                    tone_match = construction.extra_data.get("tone")
                    if tone_match and tone_match != tone:
                        continue

                # Check constraints if specified
                if constraints:
                    cons_match = construction.extra_data.get("constraints", [])
                    if not any(c in cons_match for c in constraints):
                        # No constraint match, but still add with lower priority
                        pass

                matching.append(construction)

        # Sort by confidence and success rate
        matching.sort(key=lambda c: (c.confidence, c.success_rate), reverse=True)

        return matching

    def get_all_constructions(self) -> List[Construction]:
        """
        Tüm construction'ları getir.

        Returns:
            Tüm construction'lar
        """
        all_constructions = []
        for level in ConstructionLevel:
            all_constructions.extend(self._constructions[level].values())
        return all_constructions

    def count_by_level(self) -> Dict[ConstructionLevel, int]:
        """
        Katman başına construction sayısı.

        Returns:
            Sayım sözlüğü
        """
        return {
            level: len(constructions)
            for level, constructions in self._constructions.items()
        }

    def count_total(self) -> int:
        """
        Toplam construction sayısı.

        Returns:
            Toplam sayı
        """
        return sum(len(c) for c in self._constructions.values())

    def load_defaults(self) -> int:
        """
        Varsayılan Türkçe construction'ları yükle.

        Returns:
            int: Yüklenen construction sayısı
        """
        count = 0

        # DEEP Level Constructions
        deep_constructions = self._create_deep_constructions()
        for construction in deep_constructions:
            if self.add_construction(construction):
                count += 1

        # MIDDLE Level Constructions
        middle_constructions = self._create_middle_constructions()
        for construction in middle_constructions:
            if self.add_construction(construction):
                count += 1

        # SURFACE Level Constructions
        surface_constructions = self._create_surface_constructions()
        for construction in surface_constructions:
            if self.add_construction(construction):
                count += 1

        return count

    def _create_deep_constructions(self) -> List[Construction]:
        """DEEP katman construction'larını oluştur."""
        constructions = []

        # INFORM - Bilgi verme
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="{konu} hakkında bilgi ver",
                slots={
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True,
                        description="Bilgi verilecek konu"
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                semantic_roles={"theme": "konu"},
                effects=["user_informed"]
            ),
            source="human",
            extra_data={"tone": "neutral"}
        ))

        # EXPLAIN - Açıklama
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="{konu}'ı açıkla",
                slots={
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="explain",
                semantic_roles={"theme": "konu"},
                effects=["user_understands"]
            ),
            source="human",
            extra_data={"tone": "neutral"}
        ))

        # WARN - Uyarı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="{tehlike} konusunda uyar",
                slots={
                    "tehlike": Slot(
                        id=generate_slot_id(),
                        name="tehlike",
                        slot_type=SlotType.ENTITY,
                        required=True,
                        description="Uyarılacak tehlike"
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="warn",
                semantic_roles={"theme": "tehlike"},
                effects=["user_warned"],
                illocutionary_force="directive"
            ),
            source="human",
            extra_data={"tone": "serious"}
        ))

        # EMPATHIZE - Empati
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="{duygu} duygusunu anla ve paylaş",
                slots={
                    "duygu": Slot(
                        id=generate_slot_id(),
                        name="duygu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="empathize",
                semantic_roles={"experiencer": "user", "theme": "duygu"},
                effects=["user_feels_understood"]
            ),
            source="human",
            extra_data={"tone": "empathic"}
        ))

        # ASK - Soru sorma
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="{konu} hakkında sor",
                slots={
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="ask",
                semantic_roles={"theme": "konu"},
                effects=["information_requested"],
                illocutionary_force="question"
            ),
            source="human",
            extra_data={"tone": "neutral"}
        ))

        # SUGGEST - Öneri
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="{oneri}'yı öner",
                slots={
                    "oneri": Slot(
                        id=generate_slot_id(),
                        name="oneri",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="suggest",
                semantic_roles={"theme": "oneri"},
                effects=["suggestion_made"]
            ),
            source="human",
            extra_data={"tone": "supportive"}
        ))

        # ACKNOWLEDGE - Kabul etme
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.DEEP,
            form=ConstructionForm(
                template="anladığını göster",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="acknowledge",
                effects=["user_acknowledged"]
            ),
            source="human",
            extra_data={"tone": "neutral"}
        ))

        return constructions

    def _create_middle_constructions(self) -> List[Construction]:
        """MIDDLE katman construction'larını oluştur."""
        constructions = []

        # Özne-Yüklem yapısı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="{ozne} {yuklem}",
                slots={
                    "ozne": Slot(
                        id=generate_slot_id(),
                        name="ozne",
                        slot_type=SlotType.ENTITY,
                        required=True,
                        description="Cümlenin öznesi"
                    ),
                    "yuklem": Slot(
                        id=generate_slot_id(),
                        name="yuklem",
                        slot_type=SlotType.VERB,
                        required=True,
                        description="Cümlenin yüklemi"
                    )
                },
                word_order="SOV"
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                semantic_roles={"agent": "ozne", "action": "yuklem"}
            ),
            source="human"
        ))

        # Özne-Nesne-Yüklem yapısı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="{ozne} {nesne} {yuklem}",
                slots={
                    "ozne": Slot(
                        id=generate_slot_id(),
                        name="ozne",
                        slot_type=SlotType.ENTITY,
                        required=True
                    ),
                    "nesne": Slot(
                        id=generate_slot_id(),
                        name="nesne",
                        slot_type=SlotType.ENTITY,
                        required=True
                    ),
                    "yuklem": Slot(
                        id=generate_slot_id(),
                        name="yuklem",
                        slot_type=SlotType.VERB,
                        required=True
                    )
                },
                word_order="SOV"
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                semantic_roles={"agent": "ozne", "patient": "nesne", "action": "yuklem"}
            ),
            source="human"
        ))

        # Neden-Sonuç yapısı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="{neden} için {sonuc}",
                slots={
                    "neden": Slot(
                        id=generate_slot_id(),
                        name="neden",
                        slot_type=SlotType.REASON,
                        required=True
                    ),
                    "sonuc": Slot(
                        id=generate_slot_id(),
                        name="sonuc",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="explain",
                semantic_roles={"cause": "neden", "effect": "sonuc"}
            ),
            source="human"
        ))

        # Çünkü bağlacı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="{sonuc}, çünkü {neden}",
                slots={
                    "sonuc": Slot(
                        id=generate_slot_id(),
                        name="sonuc",
                        slot_type=SlotType.ENTITY,
                        required=True
                    ),
                    "neden": Slot(
                        id=generate_slot_id(),
                        name="neden",
                        slot_type=SlotType.REASON,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="explain",
                semantic_roles={"effect": "sonuc", "cause": "neden"}
            ),
            source="human"
        ))

        # Soru yapısı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="{soru_kelimesi} {konu}?",
                slots={
                    "soru_kelimesi": Slot(
                        id=generate_slot_id(),
                        name="soru_kelimesi",
                        slot_type=SlotType.FILLER,
                        required=True,
                        constraints={"allowed_values": ["ne", "nasıl", "neden", "nerede", "ne zaman", "kim"]}
                    ),
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                },
                intonation="rising"
            ),
            meaning=ConstructionMeaning(
                dialogue_act="ask",
                illocutionary_force="question"
            ),
            source="human"
        ))

        # Öneri yapısı
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="{oneri} yapabilirsin",
                slots={
                    "oneri": Slot(
                        id=generate_slot_id(),
                        name="oneri",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="suggest"
            ),
            source="human"
        ))

        # Belki ile öneri
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.MIDDLE,
            form=ConstructionForm(
                template="Belki {oneri}",
                slots={
                    "oneri": Slot(
                        id=generate_slot_id(),
                        name="oneri",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="suggest"
            ),
            source="human",
            extra_data={"tone": "cautious"}
        ))

        return constructions

    def _create_surface_constructions(self) -> List[Construction]:
        """SURFACE katman construction'larını oluştur."""
        constructions = []

        # Basit bilgi cümlesi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="{konu} {bilgi}.",
                slots={
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    ),
                    "bilgi": Slot(
                        id=generate_slot_id(),
                        name="bilgi",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform"
            ),
            source="human"
        ))

        # Uyarı cümlesi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Dikkat! {uyari}.",
                slots={
                    "uyari": Slot(
                        id=generate_slot_id(),
                        name="uyari",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="warn"
            ),
            source="human",
            extra_data={"tone": "serious"}
        ))

        # Empati cümlesi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Seni anlıyorum, {duygu} hissetmen normal.",
                slots={
                    "duygu": Slot(
                        id=generate_slot_id(),
                        name="duygu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="empathize"
            ),
            source="human",
            extra_data={"tone": "empathic"}
        ))

        # Alternatif empati
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Bu durumda {duygu} hissetmen çok doğal.",
                slots={
                    "duygu": Slot(
                        id=generate_slot_id(),
                        name="duygu",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="empathize"
            ),
            source="human",
            extra_data={"tone": "supportive"}
        ))

        # Kabul cümlesi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Anlıyorum.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="acknowledge"
            ),
            source="human"
        ))

        # Alternatif kabul
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Evet, {onay}.",
                slots={
                    "onay": Slot(
                        id=generate_slot_id(),
                        name="onay",
                        slot_type=SlotType.ENTITY,
                        required=False,
                        default="anladım"
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="acknowledge"
            ),
            source="human"
        ))

        # Öneri cümlesi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="{oneri} deneyebilirsin.",
                slots={
                    "oneri": Slot(
                        id=generate_slot_id(),
                        name="oneri",
                        slot_type=SlotType.ENTITY,
                        required=True
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="suggest"
            ),
            source="human",
            extra_data={"tone": "supportive"}
        ))

        return constructions

    def clear(self) -> None:
        """Tüm construction'ları temizle."""
        for level in ConstructionLevel:
            self._constructions[level].clear()
        self._by_dialogue_act.clear()
