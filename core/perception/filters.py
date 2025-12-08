"""
core/perception/filters.py

Perception filtreleri - Dikkat ve gurultu azaltma.

Icerik:
- AttentionFilter: Dikkat yonlendirme ve filtreleme
- NoiseFilter: Gurultu azaltma
- SalienceFilter: Belirginlik filtreleme
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import math

from .types import (
    SensoryModality, SensoryData,
    PerceptualInput, AttentionFocus,
    ThreatLevel,
)

logger = logging.getLogger(__name__)


# ========================================================================
# CONFIGURATION
# ========================================================================

@dataclass
class FilterConfig:
    """Filtre yapilandirmasi."""

    # Attention ayarlari
    threat_attention_boost: float = 0.4      # Tehdit dikkat artisi
    social_attention_boost: float = 0.2      # Sosyal dikkat artisi
    motion_attention_boost: float = 0.15     # Hareket dikkat artisi
    novelty_attention_boost: float = 0.1     # Yenilik dikkat artisi

    # Attention decay (dikkat azalmasi)
    attention_decay_rate: float = 0.1        # Saniye basina azalma

    # Noise filter ayarlari
    noise_threshold: float = 0.2             # Bu altindaki veriler noise
    confidence_boost_clear: float = 0.1      # Net veriler icin guven artisi

    # Salience ayarlari
    min_salience_threshold: float = 0.1      # Minimum belirginlik esigi
    max_tracked_objects: int = 7             # 7±2 kurali (working memory)


# ========================================================================
# ATTENTION FILTER
# ========================================================================

class AttentionFilter:
    """
    Dikkat yonlendirme ve filtreleme.

    Dikkat kaynaklari:
    1. Reflexive (otomatik): Tehdit, ani hareket, yuksek ses
    2. Voluntary (isteyerek): Gorev odakli, hedef tarama
    3. Sustained (surdurulen): Uzun sureli izleme

    Dikkat azaltma:
    - Zaman gecince dikkat azalir
    - Yeni stimulus dikkat ceker
    - Tehdit her zaman oncelikli
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()
        self._last_attention: Optional[AttentionFocus] = None
        self._last_update: Optional[datetime] = None

    def calculate_attention(
        self,
        features: Dict[str, Any],
        current_attention: Optional[AttentionFocus] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AttentionFocus:
        """
        Dikkat odagi hesapla.

        Args:
            features: Cikarilmis ozellikler (quick_extract veya full)
            current_attention: Mevcut dikkat odagi
            context: Ek baglamsal bilgi

        Returns:
            AttentionFocus
        """
        context = context or {}
        now = datetime.now()

        # Yeni attention olustur
        attention = AttentionFocus(timestamp=now)

        # Base attention level
        base_level = 0.3

        # 1. Threat-based attention (reflexive)
        threat_boost = self._calculate_threat_attention(features)
        if threat_boost > 0:
            attention.attention_type = "reflexive"
            attention.reason = "threat"

        # 2. Social attention
        social_boost = self._calculate_social_attention(features)
        if social_boost > threat_boost:
            attention.reason = "social"

        # 3. Motion attention (reflexive)
        motion_boost = self._calculate_motion_attention(features)
        if motion_boost > max(threat_boost, social_boost):
            attention.attention_type = "reflexive"
            attention.reason = "novelty"

        # 4. Task-based attention (voluntary) - context'ten
        task_boost = 0.0
        if context.get("task_target"):
            task_boost = 0.3
            attention.attention_type = "voluntary"
            attention.reason = "task"
            attention.target_id = context.get("task_target")

        # Toplam attention level
        total_boost = max(threat_boost, social_boost, motion_boost, task_boost)
        attention.attention_level = min(1.0, base_level + total_boost)

        # 5. Attention decay (eger onceki attention varsa)
        if current_attention and self._last_update:
            elapsed = (now - self._last_update).total_seconds()
            decay = elapsed * self.config.attention_decay_rate

            # Ayni hedefe devam ediyorsak sustained attention
            if (current_attention.target_id and
                attention.target_id == current_attention.target_id):
                attention.attention_type = "sustained"
                attention.focus_duration = current_attention.focus_duration + elapsed

                # Sustained attention icin decay daha yavas
                decay *= 0.5

            attention.attention_level = max(
                0.2,
                attention.attention_level - decay
            )

        # 6. Hedef belirleme
        self._determine_target(attention, features)

        # 7. Peripheral awareness
        attention.peripheral_awareness = self._calculate_peripheral(
            attention.attention_level, features
        )

        # State guncelle
        self._last_attention = attention
        self._last_update = now

        return attention

    def _calculate_threat_attention(self, features: Dict[str, Any]) -> float:
        """Tehdit kaynaklı dikkat artisi."""
        boost = 0.0

        # Threat assessment'tan
        threat = features.get("threat")
        if threat:
            if hasattr(threat, "overall_score"):
                boost = threat.overall_score * self.config.threat_attention_boost
            elif isinstance(threat, dict):
                boost = threat.get("overall_score", 0) * self.config.threat_attention_boost

        # Tehdit ajanlarindan
        agents = features.get("agents", [])
        for agent in agents:
            if hasattr(agent, "threat_level"):
                if agent.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    boost = max(boost, self.config.threat_attention_boost)
            elif isinstance(agent, dict):
                if agent.get("threat_level") in ["high", "critical"]:
                    boost = max(boost, self.config.threat_attention_boost)

        return boost

    def _calculate_social_attention(self, features: Dict[str, Any]) -> float:
        """Sosyal kaynaklı dikkat artisi."""
        boost = 0.0

        # Ajan varligi
        agents = features.get("agents", [])
        if agents:
            boost = self.config.social_attention_boost

        # Yuz algilama
        if features.get("has_face"):
            boost = max(boost, self.config.social_attention_boost * 1.2)

        # Konusma
        auditory = features.get("auditory")
        if auditory:
            if hasattr(auditory, "speech_detected") and auditory.speech_detected:
                boost = max(boost, self.config.social_attention_boost)
            elif isinstance(auditory, dict) and auditory.get("speech_detected"):
                boost = max(boost, self.config.social_attention_boost)

        return boost

    def _calculate_motion_attention(self, features: Dict[str, Any]) -> float:
        """Hareket kaynaklı dikkat artisi."""
        boost = 0.0

        # Hareket algilama
        if features.get("has_motion"):
            boost = self.config.motion_attention_boost

        motion = features.get("motion")
        if motion:
            if hasattr(motion, "approach_detected") and motion.approach_detected:
                boost = max(boost, self.config.motion_attention_boost * 1.5)
            elif isinstance(motion, dict) and motion.get("approach_detected"):
                boost = max(boost, self.config.motion_attention_boost * 1.5)

        return boost

    def _determine_target(
        self,
        attention: AttentionFocus,
        features: Dict[str, Any],
    ) -> None:
        """Dikkat hedefini belirle."""
        # Oncelik sirasi: threat > social > motion > none

        # Tehdit ajanlarini kontrol et
        agents = features.get("agents", [])
        threatening_agents = []

        for agent in agents:
            threat_level = None
            if hasattr(agent, "threat_level"):
                threat_level = agent.threat_level
            elif isinstance(agent, dict):
                threat_level = agent.get("threat_level")

            if threat_level and threat_level != ThreatLevel.NONE:
                threatening_agents.append(agent)

        if threatening_agents:
            # En tehlikeli ajana odaklan
            primary = threatening_agents[0]
            attention.target_type = "agent"
            if hasattr(primary, "agent_id"):
                attention.target_id = primary.agent_id
            elif isinstance(primary, dict):
                attention.target_id = primary.get("agent_id", primary.get("id"))
            return

        # Herhangi bir ajan varsa
        if agents:
            primary = agents[0]
            attention.target_type = "agent"
            if hasattr(primary, "agent_id"):
                attention.target_id = primary.agent_id
            elif isinstance(primary, dict):
                attention.target_id = primary.get("agent_id", primary.get("id"))
            return

        # Hareket varsa
        if features.get("has_motion"):
            attention.target_type = "event"
            return

        # Hicbir sey yoksa
        attention.target_type = "none"

    def _calculate_peripheral(
        self,
        attention_level: float,
        features: Dict[str, Any],
    ) -> float:
        """Cevresel farkindalik hesapla."""
        # Yuksek odaklanma = dusuk cevresel farkindalik
        base = 1.0 - (attention_level * 0.5)

        # Tehdit varsa cevresel farkindalik artar (hypervigilance)
        threat = features.get("threat")
        if threat:
            if hasattr(threat, "overall_score") and threat.overall_score > 0.5:
                base = min(1.0, base + 0.2)
            elif isinstance(threat, dict) and threat.get("overall_score", 0) > 0.5:
                base = min(1.0, base + 0.2)

        return max(0.0, min(1.0, base))

    def filter_by_attention(
        self,
        input_data: PerceptualInput,
        attention: AttentionFocus,
        threshold: float = 0.4,
    ) -> PerceptualInput:
        """Dikkat esigine gore girdiyi filtrele."""
        if attention.attention_level < threshold:
            # Dusuk dikkat - yuksek oncelikli verileri koru
            filtered = []
            for sensory in input_data.sensory_data:
                # Yuksek guvenilirlik veya yuksek intensity
                if sensory.confidence >= 0.7:
                    filtered.append(sensory)
                elif input_data.intensity >= 0.7:
                    filtered.append(sensory)
            input_data.sensory_data = filtered

        return input_data


# ========================================================================
# NOISE FILTER
# ========================================================================

class NoiseFilter:
    """
    Gurultu azaltma filtresi.

    Dusuk kaliteli, belirsiz veya gurultulu verileri filtreler.
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()

    def filter(self, data: SensoryData) -> SensoryData:
        """
        Duyusal veriyi filtrele.

        - Dusuk guvenilirlik -> discard veya low-confidence mark
        - Yuksek noise -> azalt
        - Net veri -> confidence boost
        """
        # Noise seviyesi yuksekse
        if data.noise_level > self.config.noise_threshold:
            # Confidence azalt
            noise_penalty = data.noise_level * 0.3
            data.confidence = max(0.1, data.confidence - noise_penalty)

            # Cok yuksek noise - veriyi temizle
            if data.noise_level > 0.7:
                data = self._clean_noisy_data(data)

        # Net veri icin confidence artir
        elif data.noise_level < 0.1 and data.confidence >= 0.5:
            data.confidence = min(1.0, data.confidence + self.config.confidence_boost_clear)

        return data

    def _clean_noisy_data(self, data: SensoryData) -> SensoryData:
        """Cok gurultulu veriyi temizle."""
        # Raw data'yi basitlestir
        if data.raw_data:
            # Sadece yuksek guvenilirlikli alanlari koru
            cleaned = {}
            for key, value in data.raw_data.items():
                # Temel bilgileri koru
                if key in ["face_detected", "motion", "speech_detected", "distance"]:
                    cleaned[key] = value
            data.raw_data = cleaned

        # Noise seviyesini isaretli tut
        data.noise_level = data.noise_level  # Degistirme, sadece temizledik

        return data

    def filter_batch(self, data_list: List[SensoryData]) -> List[SensoryData]:
        """Birden fazla veriyi filtrele."""
        return [self.filter(d) for d in data_list]

    def calculate_signal_quality(self, data: SensoryData) -> float:
        """Sinyal kalitesi hesapla."""
        # Basit formul: confidence * (1 - noise)
        quality = data.confidence * (1.0 - data.noise_level)
        return max(0.0, min(1.0, quality))


# ========================================================================
# SALIENCE FILTER
# ========================================================================

class SalienceFilter:
    """
    Belirginlik filtresi.

    Dikkat cekmesi gereken (salient) ozellikleri belirler ve filtreler.
    7±2 kurali uygulanir - ayni anda en fazla 7 nesne takip edilir.
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()

    def filter_by_salience(
        self,
        items: List[Any],
        get_salience: callable,
    ) -> List[Any]:
        """
        Belirginlige gore filtrele.

        Args:
            items: Filtrelenecek liste
            get_salience: Item'dan salience skoru donduren fonksiyon

        Returns:
            Filtrelenmis liste (max 7 item)
        """
        # Salience hesapla ve sirala
        scored = [(item, get_salience(item)) for item in items]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Min threshold uygula
        filtered = [
            item for item, score in scored
            if score >= self.config.min_salience_threshold
        ]

        # 7±2 siniri
        max_items = self.config.max_tracked_objects
        return filtered[:max_items]

    def calculate_agent_salience(self, agent: Any) -> float:
        """Ajan icin belirginlik skoru hesapla."""
        score = 0.3  # Base

        # Tehdit belirginligi arttirir
        if hasattr(agent, "threat_score"):
            score += agent.threat_score * 0.4
        elif isinstance(agent, dict):
            score += agent.get("threat_score", 0) * 0.4

        # Yakinlik belirginligi arttirir
        distance = 10.0  # Default uzak
        if hasattr(agent, "distance"):
            distance = agent.distance
        elif isinstance(agent, dict):
            distance = agent.get("distance", 10.0)

        if distance < 5:
            score += (5 - distance) / 5 * 0.2

        # Hareket belirginligi arttirir
        is_moving = False
        if hasattr(agent, "is_moving"):
            is_moving = agent.is_moving
        elif isinstance(agent, dict):
            is_moving = agent.get("is_moving", False)

        if is_moving:
            score += 0.1

        return min(1.0, score)


# ========================================================================
# COMBINED FILTER PIPELINE
# ========================================================================

class PerceptionFilterPipeline:
    """
    Tum filtreleri birlestiren pipeline.

    Kullanim:
        pipeline = PerceptionFilterPipeline()
        filtered_input, attention = pipeline.apply(input_data)
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()

        self.noise_filter = NoiseFilter(self.config)
        self.attention_filter = AttentionFilter(self.config)
        self.salience_filter = SalienceFilter(self.config)

    def apply(
        self,
        input_data: PerceptualInput,
        features: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[PerceptualInput, AttentionFocus]:
        """
        Tam filtre pipeline'i uygula.

        Args:
            input_data: Ham girdi
            features: Cikarilmis ozellikler (opsiyonel)
            context: Baglamsal bilgi

        Returns:
            (filtrelenmis_input, attention_focus)
        """
        context = context or {}
        features = features or {}

        # 1. Noise filtreleme
        for i, sensory in enumerate(input_data.sensory_data):
            input_data.sensory_data[i] = self.noise_filter.filter(sensory)

        # 2. Attention hesapla
        attention = self.attention_filter.calculate_attention(
            features, context=context
        )

        # 3. Attention-based filtreleme
        input_data = self.attention_filter.filter_by_attention(
            input_data, attention
        )

        return input_data, attention
