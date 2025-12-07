"""
UEM v2 - StateVector Field Definitions

Merkezi alan tanımı - typo koruması sağlar.
Yeni alan eklemek için buraya SVField enum'una ekle.
"""

from enum import Enum


class SVField(str, Enum):
    """
    StateVector alanları.
    
    String enum kullanıyoruz ki:
    - Typo yapınca IDE uyarsın
    - Serialization kolay olsun
    - Dict key olarak kullanılabilsin
    """
    
    # ══════════════════════════════════════════════════════════════════
    # CORE FIELDS - Asla değişmez (3 alan)
    # ══════════════════════════════════════════════════════════════════
    RESOURCE = "resource"      # Kaynak durumu (0-1)
    THREAT = "threat"          # Tehdit seviyesi (0-1)
    WELLBEING = "wellbeing"    # Genel iyilik hali (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # EMOTION FIELDS - PAD Model
    # ══════════════════════════════════════════════════════════════════
    VALENCE = "valence"        # Pozitif/negatif (-1 to 1)
    AROUSAL = "arousal"        # Uyarılmışlık (0-1)
    DOMINANCE = "dominance"    # Kontrol hissi (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # SOCIAL FIELDS - Empathy/Sympathy/Trust
    # ══════════════════════════════════════════════════════════════════
    COGNITIVE_EMPATHY = "cognitive_empathy"    # Bilişsel anlama (0-1)
    AFFECTIVE_EMPATHY = "affective_empathy"    # Duygusal rezonans (0-1)
    SOMATIC_EMPATHY = "somatic_empathy"        # Bedensel his (0-1)
    PROJECTIVE_EMPATHY = "projective_empathy"  # "Ben olsam" simülasyonu (0-1)
    
    SYMPATHY_LEVEL = "sympathy_level"          # Sempati seviyesi (0-1)
    TRUST_VALUE = "trust_value"                # Güven değeri (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # COGNITIVE FIELDS
    # ══════════════════════════════════════════════════════════════════
    COGNITIVE_LOAD = "cognitive_load"          # Bilişsel yük (0-1)
    ATTENTION_FOCUS = "attention_focus"        # Dikkat odağı (0-1)
    CERTAINTY = "certainty"                    # Kesinlik (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # SELF FIELDS
    # ══════════════════════════════════════════════════════════════════
    INTEGRITY = "integrity"                    # Tutarlılık (0-1)
    ETHICAL_ALIGNMENT = "ethical_alignment"    # Etik uyum (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # META FIELDS
    # ══════════════════════════════════════════════════════════════════
    CONSCIOUSNESS_LEVEL = "consciousness_level"  # Bilinç seviyesi (0-1)
    
    @classmethod
    def core_fields(cls) -> list["SVField"]:
        """Core alanları döndür."""
        return [cls.RESOURCE, cls.THREAT, cls.WELLBEING]
    
    @classmethod
    def emotion_fields(cls) -> list["SVField"]:
        """Emotion alanlarını döndür."""
        return [cls.VALENCE, cls.AROUSAL, cls.DOMINANCE]
    
    @classmethod
    def social_fields(cls) -> list["SVField"]:
        """Social alanlarını döndür."""
        return [
            cls.COGNITIVE_EMPATHY,
            cls.AFFECTIVE_EMPATHY,
            cls.SOMATIC_EMPATHY,
            cls.PROJECTIVE_EMPATHY,
            cls.SYMPATHY_LEVEL,
            cls.TRUST_VALUE,
        ]
