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
    generate_deterministic_construction_id,
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
    # Hedefli B - Yeni kategoriler
    RESPOND_WELLBEING = "respond_wellbeing"
    RECEIVE_THANKS = "receive_thanks"
    LIGHT_CHITCHAT = "light_chitchat"
    ACKNOWLEDGE_POSITIVE = "acknowledge_positive"
    CLOSE_CONVERSATION = "close_conversation"  # Vedalaşma, kapanış


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

        # Hedefli B - Yeni kategoriler
        # 8. RESPOND_WELLBEING - Nasılsın sorusuna yanıt
        constructions.extend(self._create_respond_wellbeing_constructions())

        # 9. RECEIVE_THANKS - Teşekkür alındığında
        constructions.extend(self._create_receive_thanks_constructions())

        # 10. LIGHT_CHITCHAT - Hafif sohbet
        constructions.extend(self._create_light_chitchat_constructions())

        # 11. ACKNOWLEDGE_POSITIVE - Pozitif duyguya yanıt
        constructions.extend(self._create_acknowledge_positive_constructions())

        # 12. CLOSE_CONVERSATION - Vedalaşma, kapanış
        constructions.extend(self._create_close_conversation_constructions())

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
        # Hedefli B - Yeni kategoriler
        elif category == MVCSCategory.RESPOND_WELLBEING:
            constructions = self._create_respond_wellbeing_constructions()
        elif category == MVCSCategory.RECEIVE_THANKS:
            constructions = self._create_receive_thanks_constructions()
        elif category == MVCSCategory.LIGHT_CHITCHAT:
            constructions = self._create_light_chitchat_constructions()
        elif category == MVCSCategory.ACKNOWLEDGE_POSITIVE:
            constructions = self._create_acknowledge_positive_constructions()
        elif category == MVCSCategory.CLOSE_CONVERSATION:
            constructions = self._create_close_conversation_constructions()
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

    def _create_mvcs_construction(
        self,
        mvcs_name: str,
        category: MVCSCategory,
        template: str,
        dialogue_act: str,
        slots: Dict = None,
        effects: List[str] = None,
        semantic_roles: Dict = None,
        tone: str = "neutral",
        formality: float = 0.5,
        preconditions: List[str] = None,
        illocutionary_force: str = None,
        values_alignment: List[str] = None,
    ) -> Construction:
        """
        Helper to create MVCS construction with deterministic ID.

        Uses mvcs_name to generate stable, reproducible construction IDs.
        This ensures the same construction has the same ID across runs.

        Args:
            mvcs_name: Unique name for this construction (e.g., "greet_simple")
            category: MVCSCategory enum
            template: Template string
            dialogue_act: DialogueAct value
            slots: Slot definitions (optional)
            effects: Effect list (optional)
            semantic_roles: Semantic role mappings (optional)
            tone: Tone value
            formality: Formality score 0.0-1.0
            preconditions: Precondition list (optional)
            illocutionary_force: Illocutionary force (optional)
            values_alignment: Value alignment list (optional)

        Returns:
            Construction with deterministic ID
        """
        extra_data = {
            "mvcs_category": category.value,
            "mvcs_name": mvcs_name,
            "is_mvcs": True,
            "tone": tone,
            "formality": formality,
        }
        if values_alignment:
            extra_data["values_alignment"] = values_alignment

        meaning = ConstructionMeaning(
            dialogue_act=dialogue_act,
            effects=effects or [],
            semantic_roles=semantic_roles or {},
            preconditions=preconditions or [],
        )
        if illocutionary_force:
            meaning.illocutionary_force = illocutionary_force

        return Construction(
            id=generate_deterministic_construction_id(mvcs_name),
            level=ConstructionLevel.SURFACE,
            form=ConstructionForm(
                template=template,
                slots=slots or {}
            ),
            meaning=meaning,
            confidence=self.config.default_confidence,
            source=self.config.source,
            extra_data=extra_data
        )

    def _create_greet_constructions(self) -> List[Construction]:
        """GREET - Selamlama construction'lari olustur."""
        constructions = []

        # 1. Basit merhaba
        constructions.append(self._create_mvcs_construction(
            mvcs_name="greet_simple",
            category=MVCSCategory.GREET,
            template="Merhaba!",
            dialogue_act="greet",
            effects=["user_greeted"],
            tone="friendly",
            formality=0.5,
        ))

        # 2. Samimi selam
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="greet_casual",
                category=MVCSCategory.GREET,
                template="Selam, nasilsin?",
                dialogue_act="greet",
                effects=["user_greeted", "wellbeing_asked"],
                tone="casual",
                formality=0.2,
            ))

        # 3. Yardim teklifi ile selamlama
        constructions.append(self._create_mvcs_construction(
            mvcs_name="greet_with_offer",
            category=MVCSCategory.GREET,
            template="Merhaba! Size nasil yardimci olabilirim?",
            dialogue_act="greet",
            effects=["user_greeted", "help_offered"],
            tone="helpful",
            formality=0.6,
        ))

        return constructions

    def _create_self_intro_constructions(self) -> List[Construction]:
        """SELF_INTRO - Kendini tanitma construction'lari olustur."""
        constructions = []

        # 1. Temel tanitim
        constructions.append(self._create_mvcs_construction(
            mvcs_name="self_intro_basic",
            category=MVCSCategory.SELF_INTRO,
            template="Ben UEM, yapay zeka asistanizim.",
            dialogue_act="inform",
            effects=["self_introduced"],
            semantic_roles={"agent": "self", "identity": "ai_assistant"},
            tone="neutral",
            formality=0.5,
        ))

        # 2. Yardim vurgulu tanitim
        constructions.append(self._create_mvcs_construction(
            mvcs_name="self_intro_helpful",
            category=MVCSCategory.SELF_INTRO,
            template="Ben bir yapay zeka asistaniyim, size yardimci olmak icin buradayim.",
            dialogue_act="inform",
            effects=["self_introduced", "purpose_stated"],
            tone="helpful",
            formality=0.5,
        ))

        # 3. Kisa tanitim
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="self_intro_short",
                category=MVCSCategory.SELF_INTRO,
                template="Ben UEM, yapay zeka destekli bir asistan.",
                dialogue_act="inform",
                effects=["self_introduced"],
                tone="neutral",
                formality=0.4,
            ))

        return constructions

    def _create_wellbeing_constructions(self) -> List[Construction]:
        """ASK_WELLBEING - Hal hatir cevabi construction'lari olustur."""
        constructions = []

        # 1. Temel cevap
        constructions.append(self._create_mvcs_construction(
            mvcs_name="wellbeing_reciprocal",
            category=MVCSCategory.ASK_WELLBEING,
            template="Iyiyim, tesekkur ederim! Siz nasilsiniz?",
            dialogue_act="inform",
            effects=["wellbeing_answered", "wellbeing_asked"],
            tone="friendly",
            formality=0.5,
        ))

        # 2. Yardim yonlendirmeli
        constructions.append(self._create_mvcs_construction(
            mvcs_name="wellbeing_with_offer",
            category=MVCSCategory.ASK_WELLBEING,
            template="Tesekkurler, iyiyim. Size nasil yardimci olabilirim?",
            dialogue_act="inform",
            effects=["wellbeing_answered", "help_offered"],
            tone="helpful",
            formality=0.5,
        ))

        # 3. Samimi cevap
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="wellbeing_casual",
                category=MVCSCategory.ASK_WELLBEING,
                template="Gayet iyiyim, sordugun icin tesekkurler! Sen nasil hissediyorsun?",
                dialogue_act="inform",
                effects=["wellbeing_answered", "wellbeing_asked"],
                tone="casual",
                formality=0.3,
            ))

        return constructions

    def _create_inform_constructions(self) -> List[Construction]:
        """SIMPLE_INFORM - Basit bilgi verme construction'lari olustur."""
        constructions = []

        # 1. Konu hakkinda bilgi
        constructions.append(self._create_mvcs_construction(
            mvcs_name="inform_about_topic",
            category=MVCSCategory.SIMPLE_INFORM,
            template="{konu} hakkinda bilgi vereyim.",
            dialogue_act="inform",
            slots={
                "konu": Slot(
                    id=generate_slot_id(),
                    name="konu",
                    slot_type=SlotType.ENTITY,
                    required=True,
                    description="Bilgi verilecek konu"
                )
            },
            semantic_roles={"theme": "konu"},
            effects=["information_provided"],
            tone="neutral",
            formality=0.5,
        ))

        # 2. Direkt bilgi
        constructions.append(self._create_mvcs_construction(
            mvcs_name="inform_direct",
            category=MVCSCategory.SIMPLE_INFORM,
            template="{bilgi}",
            dialogue_act="inform",
            slots={
                "bilgi": Slot(
                    id=generate_slot_id(),
                    name="bilgi",
                    slot_type=SlotType.ENTITY,
                    required=True,
                    description="Verilecek bilgi"
                )
            },
            semantic_roles={"content": "bilgi"},
            effects=["information_provided"],
            tone="neutral",
            formality=0.5,
        ))

        # 3. Aciklama ile bilgi
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="inform_with_explanation",
                category=MVCSCategory.SIMPLE_INFORM,
                template="{konu} su sekilde calisiyor: {aciklama}",
                dialogue_act="explain",
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
                },
                semantic_roles={"theme": "konu", "content": "aciklama"},
                effects=["information_provided", "explanation_given"],
                tone="educational",
                formality=0.5,
            ))

        return constructions

    def _create_empathy_constructions(self) -> List[Construction]:
        """EMPATHIZE_BASIC - Temel empati construction'lari olustur."""
        constructions = []

        # 1. Anlama ifadesi
        constructions.append(self._create_mvcs_construction(
            mvcs_name="empathy_understand",
            category=MVCSCategory.EMPATHIZE_BASIC,
            template="Sizi anliyorum, bu zor bir durum.",
            dialogue_act="empathize",
            effects=["empathy_expressed", "user_validated"],
            tone="empathic",
            formality=0.5,
        ))

        # 2. Duygu dogrulama
        constructions.append(self._create_mvcs_construction(
            mvcs_name="empathy_feelings",
            category=MVCSCategory.EMPATHIZE_BASIC,
            template="Duygularinizi anliyorum.",
            dialogue_act="empathize",
            effects=["empathy_expressed"],
            tone="empathic",
            formality=0.5,
        ))

        # 3. Normallestirme
        constructions.append(self._create_mvcs_construction(
            mvcs_name="empathy_normalize",
            category=MVCSCategory.EMPATHIZE_BASIC,
            template="Bu durumda kendinizi boyle hissetmeniz normal.",
            dialogue_act="empathize",
            effects=["empathy_expressed", "feeling_normalized"],
            tone="supportive",
            formality=0.5,
        ))

        # 4. Spesifik duygu empatisi
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="empathy_specific",
                category=MVCSCategory.EMPATHIZE_BASIC,
                template="{duygu} hissetmen cok anlasilir.",
                dialogue_act="empathize",
                slots={
                    "duygu": Slot(
                        id=generate_slot_id(),
                        name="duygu",
                        slot_type=SlotType.ENTITY,
                        required=True,
                        description="Kullanicinin hissettigi duygu"
                    )
                },
                semantic_roles={"experiencer": "user", "emotion": "duygu"},
                effects=["empathy_expressed", "feeling_validated"],
                tone="empathic",
                formality=0.4,
            ))

        return constructions

    def _create_clarify_constructions(self) -> List[Construction]:
        """CLARIFY_REQUEST - Netlestirme isteme construction'lari olustur."""
        constructions = []

        # 1. Basit netlestirme
        constructions.append(self._create_mvcs_construction(
            mvcs_name="clarify_simple",
            category=MVCSCategory.CLARIFY_REQUEST,
            template="Biraz daha aciklar misiniz?",
            dialogue_act="ask",
            effects=["clarification_requested"],
            illocutionary_force="question",
            tone="polite",
            formality=0.6,
        ))

        # 2. Detay isteme
        constructions.append(self._create_mvcs_construction(
            mvcs_name="clarify_confused",
            category=MVCSCategory.CLARIFY_REQUEST,
            template="Ne demek istediginizi tam anlayamadim, detay verebilir misiniz?",
            dialogue_act="ask",
            effects=["clarification_requested", "confusion_expressed"],
            illocutionary_force="question",
            tone="honest",
            formality=0.5,
        ))

        # 3. Spesifik netlestirme
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="clarify_specific",
                category=MVCSCategory.CLARIFY_REQUEST,
                template="{konu} hakkinda daha fazla bilgi verebilir misiniz?",
                dialogue_act="ask",
                slots={
                    "konu": Slot(
                        id=generate_slot_id(),
                        name="konu",
                        slot_type=SlotType.ENTITY,
                        required=True,
                        description="Netlestirme istenen konu"
                    )
                },
                semantic_roles={"theme": "konu"},
                effects=["clarification_requested"],
                illocutionary_force="question",
                tone="polite",
                formality=0.6,
            ))

        return constructions

    def _create_refusal_constructions(self) -> List[Construction]:
        """SAFE_REFUSAL - Guvenli reddetme construction'lari olustur."""
        constructions = []

        # 1. Basit red
        constructions.append(self._create_mvcs_construction(
            mvcs_name="refuse_simple",
            category=MVCSCategory.SAFE_REFUSAL,
            template="Bu konuda size yardimci olamiyorum.",
            dialogue_act="refuse",
            effects=["request_declined"],
            preconditions=["request_is_harmful"],
            tone="polite",
            formality=0.6,
            values_alignment=["non_maleficence"],
        ))

        # 2. Alternatif oneren red
        constructions.append(self._create_mvcs_construction(
            mvcs_name="refuse_with_alternative",
            category=MVCSCategory.SAFE_REFUSAL,
            template="Bu isteginizi yerine getiremiyorum, ancak baska bir konuda yardimci olabilirim.",
            dialogue_act="refuse",
            effects=["request_declined", "alternative_offered"],
            tone="helpful",
            formality=0.6,
            values_alignment=["non_maleficence", "autonomy_respect"],
        ))

        # 3. Aciklamali red
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="refuse_with_reason",
                category=MVCSCategory.SAFE_REFUSAL,
                template="Uzgunum, {neden} nedeniyle bu konuda yardimci olamam.",
                dialogue_act="refuse",
                slots={
                    "neden": Slot(
                        id=generate_slot_id(),
                        name="neden",
                        slot_type=SlotType.REASON,
                        required=True,
                        default="etik kurallarim geregi",
                        description="Reddetme nedeni"
                    )
                },
                semantic_roles={"reason": "neden"},
                effects=["request_declined", "reason_explained"],
                tone="apologetic",
                formality=0.6,
                values_alignment=["transparency", "non_maleficence"],
            ))

        # 4. Sinir belirten red
        constructions.append(self._create_mvcs_construction(
            mvcs_name="refuse_limitation",
            category=MVCSCategory.SAFE_REFUSAL,
            template="Bu benim yeteneklerimin disinda, ancak {alternatif} onerebilirim.",
            dialogue_act="refuse",
            slots={
                "alternatif": Slot(
                    id=generate_slot_id(),
                    name="alternatif",
                    slot_type=SlotType.ENTITY,
                    required=False,
                    default="baska konularda yardim",
                    description="Onerilebilecek alternatif"
                )
            },
            semantic_roles={"alternative": "alternatif"},
            effects=["limitation_expressed", "alternative_offered"],
            tone="honest",
            formality=0.5,
            values_alignment=["transparency"],
        ))

        return constructions

    def _create_respond_wellbeing_constructions(self) -> List[Construction]:
        """RESPOND_WELLBEING - Nasılsın sorusuna yanıt construction'ları oluştur."""
        constructions = []

        # 1. İyi + teşekkür + geri sorma
        constructions.append(self._create_mvcs_construction(
            mvcs_name="wellbeing_good_reciprocal",
            category=MVCSCategory.RESPOND_WELLBEING,
            template="Iyiyim, tesekkur ederim! Siz nasilsiniz?",
            dialogue_act="respond_wellbeing",
            effects=["wellbeing_shared", "reciprocal_interest_shown"],
            tone="friendly",
            formality=0.5,
        ))

        # 2. İyi + yardım teklifi
        constructions.append(self._create_mvcs_construction(
            mvcs_name="wellbeing_good_help",
            category=MVCSCategory.RESPOND_WELLBEING,
            template="Tesekkurler, ben de iyiyim. Size nasil yardimci olabilirim?",
            dialogue_act="respond_wellbeing",
            effects=["wellbeing_shared", "help_offered"],
            tone="helpful",
            formality=0.5,
        ))

        # 3. Fena değil + teşekkür
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="wellbeing_okay",
                category=MVCSCategory.RESPOND_WELLBEING,
                template="Fena degilim, sordugunuz icin tesekkurler.",
                dialogue_act="respond_wellbeing",
                effects=["wellbeing_shared"],
                tone="casual",
                formality=0.3,
            ))

        return constructions

    def _create_receive_thanks_constructions(self) -> List[Construction]:
        """RECEIVE_THANKS - Teşekkür alındığında construction'ları oluştur."""
        constructions = []

        # 1. Rica ederim (basit)
        constructions.append(self._create_mvcs_construction(
            mvcs_name="thanks_simple",
            category=MVCSCategory.RECEIVE_THANKS,
            template="Rica ederim!",
            dialogue_act="receive_thanks",
            effects=["thanks_acknowledged"],
            tone="friendly",
            formality=0.4,
        ))

        # 2. Memnun oldum
        constructions.append(self._create_mvcs_construction(
            mvcs_name="thanks_pleasure",
            category=MVCSCategory.RECEIVE_THANKS,
            template="Ne demek, memnun oldum.",
            dialogue_act="receive_thanks",
            effects=["thanks_acknowledged", "pleasure_expressed"],
            tone="warm",
            formality=0.5,
        ))

        # 3. Rica ederim + yardım teklifi
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="thanks_continue_help",
                category=MVCSCategory.RECEIVE_THANKS,
                template="Rica ederim, baska nasil yardimci olabilirim?",
                dialogue_act="receive_thanks",
                effects=["thanks_acknowledged", "continued_help_offered"],
                tone="helpful",
                formality=0.5,
            ))

        return constructions

    def _create_light_chitchat_constructions(self) -> List[Construction]:
        """LIGHT_CHITCHAT - Hafif sohbet construction'ları oluştur."""
        constructions = []

        # 1. Fena değilim + sen
        constructions.append(self._create_mvcs_construction(
            mvcs_name="chitchat_casual_reciprocal",
            category=MVCSCategory.LIGHT_CHITCHAT,
            template="Fena degilim, sen nasilsin?",
            dialogue_act="light_chitchat",
            effects=["chitchat_engaged", "reciprocal_question"],
            tone="casual",
            formality=0.2,
        ))

        # 2. İyidir + neler oluyor
        constructions.append(self._create_mvcs_construction(
            mvcs_name="chitchat_whats_up",
            category=MVCSCategory.LIGHT_CHITCHAT,
            template="Iyidir, neler oluyor?",
            dialogue_act="light_chitchat",
            effects=["chitchat_engaged", "interest_shown"],
            tone="casual",
            formality=0.2,
        ))

        # 3. Buradayım + yardım
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="chitchat_present_ready",
                category=MVCSCategory.LIGHT_CHITCHAT,
                template="Buradayim, hazirim. Nasil yardimci olabilirim?",
                dialogue_act="light_chitchat",
                effects=["presence_confirmed", "help_offered"],
                tone="friendly",
                formality=0.4,
            ))

        return constructions

    def _create_acknowledge_positive_constructions(self) -> List[Construction]:
        """ACKNOWLEDGE_POSITIVE - Pozitif duyguya yanıt construction'ları oluştur."""
        constructions = []

        # 1. İyi olmanıza sevindim
        constructions.append(self._create_mvcs_construction(
            mvcs_name="positive_glad",
            category=MVCSCategory.ACKNOWLEDGE_POSITIVE,
            template="Iyi olmaniza sevindim!",
            dialogue_act="acknowledge_positive",
            effects=["positive_acknowledged", "joy_shared"],
            tone="warm",
            formality=0.5,
        ))

        # 2. Güzel + duymak iyi geldi
        constructions.append(self._create_mvcs_construction(
            mvcs_name="positive_nice_to_hear",
            category=MVCSCategory.ACKNOWLEDGE_POSITIVE,
            template="Guzel, bunu duymak iyi geldi.",
            dialogue_act="acknowledge_positive",
            effects=["positive_acknowledged"],
            tone="friendly",
            formality=0.4,
        ))

        # 3. Ne güzel + mutlu oldum
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="positive_happy",
                category=MVCSCategory.ACKNOWLEDGE_POSITIVE,
                template="Ne guzel, mutlu oldum.",
                dialogue_act="acknowledge_positive",
                effects=["positive_acknowledged", "happiness_expressed"],
                tone="enthusiastic",
                formality=0.3,
            ))

        return constructions

    def _create_close_conversation_constructions(self) -> List[Construction]:
        """CLOSE_CONVERSATION - Vedalaşma, kapanış construction'ları oluştur."""
        constructions = []

        # 1. Görüşürüz, iyi günler
        constructions.append(self._create_mvcs_construction(
            mvcs_name="farewell_see_you",
            category=MVCSCategory.CLOSE_CONVERSATION,
            template="Gorusuruz, iyi gunler!",
            dialogue_act="farewell",
            effects=["farewell", "well_wishes"],
            tone="friendly",
            formality=0.5,
        ))

        # 2. Hoşça kal, tekrar beklerim
        constructions.append(self._create_mvcs_construction(
            mvcs_name="farewell_see_you_again",
            category=MVCSCategory.CLOSE_CONVERSATION,
            template="Hosca kal, tekrar beklerim.",
            dialogue_act="farewell",
            effects=["farewell", "invitation_to_return"],
            tone="warm",
            formality=0.4,
        ))

        # 3. Kendine iyi bak, görüşmek üzere
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="farewell_take_care",
                category=MVCSCategory.CLOSE_CONVERSATION,
                template="Kendine iyi bak, gorusmek uzere!",
                dialogue_act="farewell",
                effects=["farewell", "care_expressed"],
                tone="caring",
                formality=0.3,
            ))

        # 4. İyi günler, her zaman yazabilirsin
        if self.config.include_variations:
            constructions.append(self._create_mvcs_construction(
                mvcs_name="farewell_always_available",
                category=MVCSCategory.CLOSE_CONVERSATION,
                template="Iyi gunler, her zaman yazabilirsin.",
                dialogue_act="farewell",
                effects=["farewell", "availability_expressed"],
                tone="supportive",
                formality=0.4,
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
