"""
core/language/construction/mvcs.py

Minimum Viable Construction Set (MVCS)
Cold start problemini cozmek icin cekirdek construction'lar.

UEM v2 - Thought-to-Speech Pipeline bileşeni.

7 Temel Construction (Alice onerisi):
1. GREET - Selamlama
2. SELF_INTRO - Kendini tanitma
3. ASK_WELLBEING - Hal hatir sorma cevabi
4. SIMPLE_INFORM - Basit bilgi verme
5. EMPATHIZE_BASIC - Temel empati
6. CLARIFY_REQUEST - Netlestirme isteme
7. SAFE_REFUSAL - Guvenli reddetme

Bu set, sistemin en temel iletisim ihtiyaclarini karsilar.
Yeni construction'lar ogrenildikce bu set genisler.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import logging

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

logger = logging.getLogger(__name__)


class MVCSCategory(str, Enum):
    """MVCS kategori tipleri."""
    GREET = "greet"
    SELF_INTRO = "self_intro"
    ASK_WELLBEING = "ask_wellbeing"
    SIMPLE_INFORM = "simple_inform"
    EMPATHIZE_BASIC = "empathize_basic"
    CLARIFY_REQUEST = "clarify_request"
    SAFE_REFUSAL = "safe_refusal"


@dataclass
class MVCSConfig:
    """
    MVCS yapilandirmasi.

    Attributes:
        include_variations: Her kategori icin varyasyonlari dahil et
        default_confidence: Varsayilan guven skoru
        source: Construction kaynagi (human, learned, generated)
    """
    include_variations: bool = True
    default_confidence: float = 0.8
    source: str = "human"  # Must be one of: human, learned, generated


class MVCSLoader:
    """
    Minimum Viable Construction Set yukleyici.

    Cold start icin gerekli temel construction'lari yukler.
    7 temel kategori, toplam ~20+ construction.

    Kullanim:
        loader = MVCSLoader()

        # Tum MVCS construction'larini yukle
        all_constructions = loader.load_all()

        # Kategoriye gore getir
        greetings = loader.get_greet_constructions()
        empathy = loader.get_empathy_constructions()

        # Isme gore getir
        greet = loader.get_by_category(MVCSCategory.GREET)
    """

    def __init__(self, config: Optional[MVCSConfig] = None):
        """
        MVCSLoader olustur.

        Args:
            config: MVCS yapilandirmasi
        """
        self.config = config or MVCSConfig()
        self._cache: Dict[MVCSCategory, List[Construction]] = {}
        self._all_constructions: Optional[List[Construction]] = None

    def load_all(self) -> List[Construction]:
        """
        Tum MVCS construction'larini yukle.

        Returns:
            List[Construction]: Tum MVCS construction'lari
        """
        if self._all_constructions is not None:
            return self._all_constructions

        constructions = []

        # 1. GREET - Selamlama
        constructions.extend(self._create_greet_constructions())

        # 2. SELF_INTRO - Kendini tanitma
        constructions.extend(self._create_self_intro_constructions())

        # 3. ASK_WELLBEING - Hal hatir cevabi
        constructions.extend(self._create_wellbeing_constructions())

        # 4. SIMPLE_INFORM - Basit bilgi verme
        constructions.extend(self._create_inform_constructions())

        # 5. EMPATHIZE_BASIC - Temel empati
        constructions.extend(self._create_empathy_constructions())

        # 6. CLARIFY_REQUEST - Netlestirme isteme
        constructions.extend(self._create_clarify_constructions())

        # 7. SAFE_REFUSAL - Guvenli reddetme
        constructions.extend(self._create_refusal_constructions())

        self._all_constructions = constructions
        logger.info(f"MVCS loaded: {len(constructions)} constructions")

        return constructions

    def get_by_category(self, category: MVCSCategory) -> List[Construction]:
        """
        Kategoriye gore construction'lari getir.

        Args:
            category: MVCS kategorisi

        Returns:
            O kategorideki construction'lar
        """
        if category in self._cache:
            return self._cache[category]

        # Lazy load
        if category == MVCSCategory.GREET:
            constructions = self._create_greet_constructions()
        elif category == MVCSCategory.SELF_INTRO:
            constructions = self._create_self_intro_constructions()
        elif category == MVCSCategory.ASK_WELLBEING:
            constructions = self._create_wellbeing_constructions()
        elif category == MVCSCategory.SIMPLE_INFORM:
            constructions = self._create_inform_constructions()
        elif category == MVCSCategory.EMPATHIZE_BASIC:
            constructions = self._create_empathy_constructions()
        elif category == MVCSCategory.CLARIFY_REQUEST:
            constructions = self._create_clarify_constructions()
        elif category == MVCSCategory.SAFE_REFUSAL:
            constructions = self._create_refusal_constructions()
        else:
            constructions = []

        self._cache[category] = constructions
        return constructions

    def get_by_name(self, name: str) -> Optional[Construction]:
        """
        Isme gore tek construction getir.

        Args:
            name: Construction extra_data["mvcs_name"]

        Returns:
            Bulunan construction veya None
        """
        all_constructions = self.load_all()

        for construction in all_constructions:
            if construction.extra_data.get("mvcs_name") == name:
                return construction

        return None

    def get_greet_constructions(self) -> List[Construction]:
        """Selamlama construction'larini getir."""
        return self.get_by_category(MVCSCategory.GREET)

    def get_self_intro_constructions(self) -> List[Construction]:
        """Kendini tanitma construction'larini getir."""
        return self.get_by_category(MVCSCategory.SELF_INTRO)

    def get_wellbeing_constructions(self) -> List[Construction]:
        """Hal hatir cevabi construction'larini getir."""
        return self.get_by_category(MVCSCategory.ASK_WELLBEING)

    def get_inform_constructions(self) -> List[Construction]:
        """Bilgi verme construction'larini getir."""
        return self.get_by_category(MVCSCategory.SIMPLE_INFORM)

    def get_empathy_constructions(self) -> List[Construction]:
        """Empati construction'larini getir."""
        return self.get_by_category(MVCSCategory.EMPATHIZE_BASIC)

    def get_clarify_constructions(self) -> List[Construction]:
        """Netlestirme construction'larini getir."""
        return self.get_by_category(MVCSCategory.CLARIFY_REQUEST)

    def get_refusal_constructions(self) -> List[Construction]:
        """Guvenli reddetme construction'larini getir."""
        return self.get_by_category(MVCSCategory.SAFE_REFUSAL)

    def get_category_count(self) -> Dict[MVCSCategory, int]:
        """
        Kategori basina construction sayisi.

        Returns:
            Sayim sozlugu
        """
        all_constructions = self.load_all()
        counts = {cat: 0 for cat in MVCSCategory}

        for construction in all_constructions:
            cat_name = construction.extra_data.get("mvcs_category")
            if cat_name:
                try:
                    cat = MVCSCategory(cat_name)
                    counts[cat] += 1
                except ValueError:
                    pass

        return counts

    def get_total_count(self) -> int:
        """Toplam MVCS construction sayisi."""
        return len(self.load_all())

    # =========================================================================
    # Construction Factory Methods
    # =========================================================================

    def _create_greet_constructions(self) -> List[Construction]:
        """GREET - Selamlama construction'lari olustur."""
        constructions = []

        # 1. Basit merhaba
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Merhaba!",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="greet",
                effects=["user_greeted"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.GREET.value,
                "mvcs_name": "greet_simple",
                "is_mvcs": True,
                "tone": "friendly",
                "formality": 0.5,
            }
        ))

        # 2. Samimi selam
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="Selam, nasilsin?",
                    slots={}
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="greet",
                    effects=["user_greeted", "wellbeing_asked"]
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.GREET.value,
                    "mvcs_name": "greet_casual",
                    "is_mvcs": True,
                    "tone": "casual",
                    "formality": 0.2,
                }
            ))

        # 3. Yardim teklifi ile selamlama
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Merhaba! Size nasil yardimci olabilirim?",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="greet",
                effects=["user_greeted", "help_offered"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.GREET.value,
                "mvcs_name": "greet_with_offer",
                "is_mvcs": True,
                "tone": "helpful",
                "formality": 0.6,
            }
        ))

        return constructions

    def _create_self_intro_constructions(self) -> List[Construction]:
        """SELF_INTRO - Kendini tanitma construction'lari olustur."""
        constructions = []

        # 1. Temel tanitim
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Ben UEM, yapay zeka asistanizim.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                effects=["self_introduced"],
                semantic_roles={"agent": "self", "identity": "ai_assistant"}
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SELF_INTRO.value,
                "mvcs_name": "self_intro_basic",
                "is_mvcs": True,
                "tone": "neutral",
                "formality": 0.5,
            }
        ))

        # 2. Yardim vurgulu tanitim
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Ben bir yapay zeka asistaniyim, size yardimci olmak icin buradayim.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                effects=["self_introduced", "purpose_stated"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SELF_INTRO.value,
                "mvcs_name": "self_intro_helpful",
                "is_mvcs": True,
                "tone": "helpful",
                "formality": 0.5,
            }
        ))

        # 3. Kisa tanitim
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="Ben UEM, yapay zeka destekli bir asistan.",
                    slots={}
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="inform",
                    effects=["self_introduced"]
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.SELF_INTRO.value,
                    "mvcs_name": "self_intro_short",
                    "is_mvcs": True,
                    "tone": "neutral",
                    "formality": 0.4,
                }
            ))

        return constructions

    def _create_wellbeing_constructions(self) -> List[Construction]:
        """ASK_WELLBEING - Hal hatir cevabi construction'lari olustur."""
        constructions = []

        # 1. Temel cevap
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Iyiyim, tesekkur ederim! Siz nasilsiniz?",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                effects=["wellbeing_answered", "wellbeing_asked"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.ASK_WELLBEING.value,
                "mvcs_name": "wellbeing_reciprocal",
                "is_mvcs": True,
                "tone": "friendly",
                "formality": 0.5,
            }
        ))

        # 2. Yardim yonlendirmeli
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Tesekkurler, iyiyim. Size nasil yardimci olabilirim?",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                effects=["wellbeing_answered", "help_offered"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.ASK_WELLBEING.value,
                "mvcs_name": "wellbeing_with_offer",
                "is_mvcs": True,
                "tone": "helpful",
                "formality": 0.5,
            }
        ))

        # 3. Samimi cevap
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="Gayet iyiyim, sordugun icin tesekkurler! Sen nasil hissediyorsun?",
                    slots={}
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="inform",
                    effects=["wellbeing_answered", "wellbeing_asked"]
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.ASK_WELLBEING.value,
                    "mvcs_name": "wellbeing_casual",
                    "is_mvcs": True,
                    "tone": "casual",
                    "formality": 0.3,
                }
            ))

        return constructions

    def _create_inform_constructions(self) -> List[Construction]:
        """SIMPLE_INFORM - Basit bilgi verme construction'lari olustur."""
        constructions = []

        # 1. Konu hakkinda bilgi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="{konu} hakkinda bilgi vereyim.",
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
                effects=["information_provided"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SIMPLE_INFORM.value,
                "mvcs_name": "inform_about_topic",
                "is_mvcs": True,
                "tone": "neutral",
                "formality": 0.5,
            }
        ))

        # 2. Direkt bilgi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="{bilgi}",
                slots={
                    "bilgi": Slot(
                        id=generate_slot_id(),
                        name="bilgi",
                        slot_type=SlotType.ENTITY,
                        required=True,
                        description="Verilecek bilgi"
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="inform",
                semantic_roles={"content": "bilgi"},
                effects=["information_provided"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SIMPLE_INFORM.value,
                "mvcs_name": "inform_direct",
                "is_mvcs": True,
                "tone": "neutral",
                "formality": 0.5,
            }
        ))

        # 3. Aciklama ile bilgi
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="{konu} su sekilde calisiyor: {aciklama}",
                    slots={
                        "konu": Slot(
                            id=generate_slot_id(),
                            name="konu",
                            slot_type=SlotType.ENTITY,
                            required=True
                        ),
                        "aciklama": Slot(
                            id=generate_slot_id(),
                            name="aciklama",
                            slot_type=SlotType.ENTITY,
                            required=True
                        )
                    }
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="explain",
                    semantic_roles={"theme": "konu", "content": "aciklama"},
                    effects=["information_provided", "explanation_given"]
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.SIMPLE_INFORM.value,
                    "mvcs_name": "inform_with_explanation",
                    "is_mvcs": True,
                    "tone": "educational",
                    "formality": 0.5,
                }
            ))

        return constructions

    def _create_empathy_constructions(self) -> List[Construction]:
        """EMPATHIZE_BASIC - Temel empati construction'lari olustur."""
        constructions = []

        # 1. Anlama ifadesi
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Sizi anliyorum, bu zor bir durum.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="empathize",
                effects=["empathy_expressed", "user_validated"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.EMPATHIZE_BASIC.value,
                "mvcs_name": "empathy_understand",
                "is_mvcs": True,
                "tone": "empathic",
                "formality": 0.5,
            }
        ))

        # 2. Duygu dogrulama
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Duygularinizi anliyorum.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="empathize",
                effects=["empathy_expressed"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.EMPATHIZE_BASIC.value,
                "mvcs_name": "empathy_feelings",
                "is_mvcs": True,
                "tone": "empathic",
                "formality": 0.5,
            }
        ))

        # 3. Normallestirme
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Bu durumda kendinizi boyle hissetmeniz normal.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="empathize",
                effects=["empathy_expressed", "feeling_normalized"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.EMPATHIZE_BASIC.value,
                "mvcs_name": "empathy_normalize",
                "is_mvcs": True,
                "tone": "supportive",
                "formality": 0.5,
            }
        ))

        # 4. Spesifik duygu empatisi
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="{duygu} hissetmen cok anlasilir.",
                    slots={
                        "duygu": Slot(
                            id=generate_slot_id(),
                            name="duygu",
                            slot_type=SlotType.ENTITY,
                            required=True,
                            description="Kullanicinin hissettigi duygu"
                        )
                    }
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="empathize",
                    semantic_roles={"experiencer": "user", "emotion": "duygu"},
                    effects=["empathy_expressed", "feeling_validated"]
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.EMPATHIZE_BASIC.value,
                    "mvcs_name": "empathy_specific",
                    "is_mvcs": True,
                    "tone": "empathic",
                    "formality": 0.4,
                }
            ))

        return constructions

    def _create_clarify_constructions(self) -> List[Construction]:
        """CLARIFY_REQUEST - Netlestirme isteme construction'lari olustur."""
        constructions = []

        # 1. Basit netlestirme
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Biraz daha aciklar misiniz?",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="ask",
                effects=["clarification_requested"],
                illocutionary_force="question"
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.CLARIFY_REQUEST.value,
                "mvcs_name": "clarify_simple",
                "is_mvcs": True,
                "tone": "polite",
                "formality": 0.6,
            }
        ))

        # 2. Detay isteme
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Ne demek istediginizi tam anlayamadim, detay verebilir misiniz?",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="ask",
                effects=["clarification_requested", "confusion_expressed"],
                illocutionary_force="question"
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.CLARIFY_REQUEST.value,
                "mvcs_name": "clarify_confused",
                "is_mvcs": True,
                "tone": "honest",
                "formality": 0.5,
            }
        ))

        # 3. Spesifik netlestirme
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="{konu} hakkinda daha fazla bilgi verebilir misiniz?",
                    slots={
                        "konu": Slot(
                            id=generate_slot_id(),
                            name="konu",
                            slot_type=SlotType.ENTITY,
                            required=True,
                            description="Netlestirme istenen konu"
                        )
                    }
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="ask",
                    semantic_roles={"theme": "konu"},
                    effects=["clarification_requested"],
                    illocutionary_force="question"
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.CLARIFY_REQUEST.value,
                    "mvcs_name": "clarify_specific",
                    "is_mvcs": True,
                    "tone": "polite",
                    "formality": 0.6,
                }
            ))

        return constructions

    def _create_refusal_constructions(self) -> List[Construction]:
        """SAFE_REFUSAL - Guvenli reddetme construction'lari olustur."""
        constructions = []

        # 1. Basit red
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Bu konuda size yardimci olamiyorum.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="refuse",
                effects=["request_declined"],
                preconditions=["request_is_harmful"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SAFE_REFUSAL.value,
                "mvcs_name": "refuse_simple",
                "is_mvcs": True,
                "tone": "polite",
                "formality": 0.6,
                "values_alignment": ["non_maleficence"],
            }
        ))

        # 2. Alternatif oneren red
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Bu isteginizi yerine getiremiyorum, ancak baska bir konuda yardimci olabilirim.",
                slots={}
            ),
            meaning=ConstructionMeaning(
                dialogue_act="refuse",
                effects=["request_declined", "alternative_offered"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SAFE_REFUSAL.value,
                "mvcs_name": "refuse_with_alternative",
                "is_mvcs": True,
                "tone": "helpful",
                "formality": 0.6,
                "values_alignment": ["non_maleficence", "autonomy_respect"],
            }
        ))

        # 3. Aciklamali red
        if self.config.include_variations:
            constructions.append(Construction(
                id=generate_construction_id(),
                level=ConstructionLevel.SURFACE,
                form=ConstructionForm(
                    template="Uzgunum, {neden} nedeniyle bu konuda yardimci olamam.",
                    slots={
                        "neden": Slot(
                            id=generate_slot_id(),
                            name="neden",
                            slot_type=SlotType.REASON,
                            required=True,
                            default="etik kurallarim geregi",
                            description="Reddetme nedeni"
                        )
                    }
                ),
                meaning=ConstructionMeaning(
                    dialogue_act="refuse",
                    semantic_roles={"reason": "neden"},
                    effects=["request_declined", "reason_explained"]
                ),
                confidence=self.config.default_confidence,
                source=self.config.source,
                extra_data={
                    "mvcs_category": MVCSCategory.SAFE_REFUSAL.value,
                    "mvcs_name": "refuse_with_reason",
                    "is_mvcs": True,
                    "tone": "apologetic",
                    "formality": 0.6,
                    "values_alignment": ["transparency", "non_maleficence"],
                }
            ))

        # 4. Sinir belirten red
        constructions.append(Construction(
            id=generate_construction_id(),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template="Bu benim yeteneklerimin disinda, ancak {alternatif} onerebilirim.",
                slots={
                    "alternatif": Slot(
                        id=generate_slot_id(),
                        name="alternatif",
                        slot_type=SlotType.ENTITY,
                        required=False,
                        default="baska konularda yardim",
                        description="Onerilebilecek alternatif"
                    )
                }
            ),
            meaning=ConstructionMeaning(
                dialogue_act="refuse",
                semantic_roles={"alternative": "alternatif"},
                effects=["limitation_expressed", "alternative_offered"]
            ),
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data={
                "mvcs_category": MVCSCategory.SAFE_REFUSAL.value,
                "mvcs_name": "refuse_limitation",
                "is_mvcs": True,
                "tone": "honest",
                "formality": 0.5,
                "values_alignment": ["transparency"],
            }
        ))

        return constructions

    def clear_cache(self) -> None:
        """Onbellegi temizle."""
        self._cache.clear()
        self._all_constructions = None

    def get_constructions_by_dialogue_act(self, dialogue_act: str) -> List[Construction]:
        """
        DialogueAct'e gore MVCS construction'larini getir.

        Args:
            dialogue_act: DialogueAct degeri

        Returns:
            Uygun construction'lar
        """
        all_constructions = self.load_all()
        return [
            c for c in all_constructions
            if c.meaning.dialogue_act == dialogue_act
        ]

    def get_constructions_by_tone(self, tone: str) -> List[Construction]:
        """
        Tona gore MVCS construction'larini getir.

        Args:
            tone: Ton degeri (friendly, empathic, etc.)

        Returns:
            Uygun construction'lar
        """
        all_constructions = self.load_all()
        return [
            c for c in all_constructions
            if c.extra_data.get("tone") == tone
        ]

    def get_constructions_by_formality(
        self,
        min_formality: float = 0.0,
        max_formality: float = 1.0
    ) -> List[Construction]:
        """
        Formalite araligina gore MVCS construction'larini getir.

        Args:
            min_formality: Minimum formalite (0.0-1.0)
            max_formality: Maximum formalite (0.0-1.0)

        Returns:
            Uygun construction'lar
        """
        all_constructions = self.load_all()
        return [
            c for c in all_constructions
            if min_formality <= c.extra_data.get("formality", 0.5) <= max_formality
        ]
