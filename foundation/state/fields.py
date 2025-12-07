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
    VALENCE = "valence"        # Pozitif/negatif (-1 to 1, normalized 0-1)
    AROUSAL = "arousal"        # Uyarılmışlık (0-1)
    DOMINANCE = "dominance"    # Kontrol hissi (0-1)
    
    # Türetilen duygusal değerler
    EMOTIONAL_INTENSITY = "emotional_intensity"  # Duygu yoğunluğu (0-1)
    MOOD_STABILITY = "mood_stability"            # Ruh hali stabilitesi (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # EMPATHY FIELDS - 4 Kanal + Toplam
    # ══════════════════════════════════════════════════════════════════
    COGNITIVE_EMPATHY = "cognitive_empathy"      # Bilişsel anlama (0-1)
    AFFECTIVE_EMPATHY = "affective_empathy"      # Duygusal rezonans (0-1)
    SOMATIC_EMPATHY = "somatic_empathy"          # Bedensel his (0-1)
    PROJECTIVE_EMPATHY = "projective_empathy"    # "Ben olsam" simülasyonu (0-1)
    EMPATHY_TOTAL = "empathy_total"              # Toplam empati (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # SYMPATHY FIELDS
    # ══════════════════════════════════════════════════════════════════
    SYMPATHY_LEVEL = "sympathy_level"            # Sempati seviyesi (0-1)
    SYMPATHY_VALENCE = "sympathy_valence"        # Sempati yönü (-1 to 1, norm 0-1)
    # 1.0 = tamamen prosocial, 0.0 = tamamen antisocial
    
    # ══════════════════════════════════════════════════════════════════
    # TRUST FIELDS
    # ══════════════════════════════════════════════════════════════════
    TRUST_VALUE = "trust_value"                  # Güven değeri (0-1)
    TRUST_COMPETENCE = "trust_competence"        # Yetkinlik güveni (0-1)
    TRUST_BENEVOLENCE = "trust_benevolence"      # İyi niyet güveni (0-1)
    TRUST_INTEGRITY = "trust_integrity"          # Dürüstlük güveni (0-1)
    TRUST_PREDICTABILITY = "trust_predictability" # Öngörülebilirlik (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # SOCIAL CONTEXT FIELDS
    # ══════════════════════════════════════════════════════════════════
    SOCIAL_ENGAGEMENT = "social_engagement"      # Sosyal bağlılık (0-1)
    RELATIONSHIP_QUALITY = "relationship_quality" # İlişki kalitesi (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # COGNITIVE FIELDS
    # ══════════════════════════════════════════════════════════════════
    COGNITIVE_LOAD = "cognitive_load"            # Bilişsel yük (0-1)
    ATTENTION_FOCUS = "attention_focus"          # Dikkat odağı (0-1)
    CERTAINTY = "certainty"                      # Kesinlik (0-1)

    # ══════════════════════════════════════════════════════════════════
    # MEMORY FIELDS
    # ══════════════════════════════════════════════════════════════════
    MEMORY_LOAD = "memory_load"                  # Ne kadar bellek yuklu? (0-1)
    MEMORY_RELEVANCE = "memory_relevance"        # Getirilen bilgi ne kadar alakali? (0-1)
    KNOWN_AGENT = "known_agent"                  # Agent taniniyor mu? (0-1, bool-like)
    
    # ══════════════════════════════════════════════════════════════════
    # SELF FIELDS
    # ══════════════════════════════════════════════════════════════════
    INTEGRITY = "integrity"                      # Tutarlılık (0-1)
    ETHICAL_ALIGNMENT = "ethical_alignment"      # Etik uyum (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # META FIELDS
    # ══════════════════════════════════════════════════════════════════
    CONSCIOUSNESS_LEVEL = "consciousness_level"  # Bilinç seviyesi (0-1)
    
    # ══════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ══════════════════════════════════════════════════════════════════
    
    @classmethod
    def core_fields(cls) -> list["SVField"]:
        """Core alanları döndür."""
        return [cls.RESOURCE, cls.THREAT, cls.WELLBEING]
    
    @classmethod
    def emotion_fields(cls) -> list["SVField"]:
        """Emotion (PAD) alanlarını döndür."""
        return [cls.VALENCE, cls.AROUSAL, cls.DOMINANCE]
    
    @classmethod
    def empathy_fields(cls) -> list["SVField"]:
        """Empathy alanlarını döndür."""
        return [
            cls.COGNITIVE_EMPATHY,
            cls.AFFECTIVE_EMPATHY,
            cls.SOMATIC_EMPATHY,
            cls.PROJECTIVE_EMPATHY,
            cls.EMPATHY_TOTAL,
        ]
    
    @classmethod
    def sympathy_fields(cls) -> list["SVField"]:
        """Sympathy alanlarını döndür."""
        return [cls.SYMPATHY_LEVEL, cls.SYMPATHY_VALENCE]
    
    @classmethod
    def trust_fields(cls) -> list["SVField"]:
        """Trust alanlarını döndür."""
        return [
            cls.TRUST_VALUE,
            cls.TRUST_COMPETENCE,
            cls.TRUST_BENEVOLENCE,
            cls.TRUST_INTEGRITY,
            cls.TRUST_PREDICTABILITY,
        ]
    
    @classmethod
    def social_fields(cls) -> list["SVField"]:
        """Tüm sosyal alanları döndür (empathy + sympathy + trust)."""
        return cls.empathy_fields() + cls.sympathy_fields() + cls.trust_fields()
    
    @classmethod
    def affect_fields(cls) -> list["SVField"]:
        """Tüm affect alanlarını döndür."""
        return cls.emotion_fields() + cls.social_fields()

    @classmethod
    def memory_fields(cls) -> list["SVField"]:
        """Memory alanlarını döndür."""
        return [cls.MEMORY_LOAD, cls.MEMORY_RELEVANCE, cls.KNOWN_AGENT]

    @classmethod
    def cognitive_fields(cls) -> list["SVField"]:
        """Cognitive alanlarını döndür."""
        return [cls.COGNITIVE_LOAD, cls.ATTENTION_FOCUS, cls.CERTAINTY]
