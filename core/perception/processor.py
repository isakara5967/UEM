"""
core/perception/processor.py

PerceptionProcessor - Ana koordinator.

Gorevler:
- Ham girdiyi al (SENSE)
- Filtreleme/dikkat yonlendirme (ATTEND)
- Ozellik cikarma (PERCEIVE)
- Ciktiyi diger modullere hazirla

Akis:
    Input -> Filter -> Extract -> Integrate -> Output
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import time

from .types import (
    SensoryModality, SensoryData,
    VisualFeatures, AuditoryFeatures, MotionFeatures,
    PerceptualInput, PerceptualFeatures, PerceptualOutput,
    PerceivedAgent, ThreatAssessment, ThreatLevel,
    AttentionFocus,
)
from .extractor import FeatureExtractor, ExtractorConfig
from .filters import AttentionFilter, NoiseFilter, FilterConfig

logger = logging.getLogger(__name__)


# ========================================================================
# CONFIGURATION
# ========================================================================

@dataclass
class ProcessorConfig:
    """PerceptionProcessor yapilandirmasi."""

    # Genel
    enable_logging: bool = True
    max_processing_time_ms: float = 200.0

    # Filtreleme
    enable_attention_filter: bool = True
    enable_noise_filter: bool = True

    # Ozellik cikarma
    extractor_config: Optional[ExtractorConfig] = None
    filter_config: Optional[FilterConfig] = None

    # Entegrasyon
    enable_threat_integration: bool = True
    enable_memory_integration: bool = False  # Memory modulu ile entegrasyon

    # Esikler
    min_confidence: float = 0.3
    attention_threshold: float = 0.4


# ========================================================================
# PERCEPTION PROCESSOR
# ========================================================================

class PerceptionProcessor:
    """
    Ana perception islemcisi.

    Tum algi akisini koordine eder:
    1. Ham girdiyi al
    2. Noise filtreleme
    3. Attention filtreleme
    4. Ozellik cikarma
    5. Entegrasyon
    6. Cikti hazirlama

    Kullanim:
        processor = PerceptionProcessor()

        # Tek girdi isle
        output = processor.process(perceptual_input)

        # Stimulus'tan isle (uyumluluk)
        output = processor.process_stimulus(stimulus)
    """

    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()

        # Bilesenler
        self.extractor = FeatureExtractor(
            self.config.extractor_config or ExtractorConfig()
        )
        self.attention_filter = AttentionFilter(
            self.config.filter_config or FilterConfig()
        )
        self.noise_filter = NoiseFilter(
            self.config.filter_config or FilterConfig()
        )

        # Istatistikler
        self._processed_count = 0
        self._total_processing_time = 0.0

    # ====================================================================
    # ANA ISLEM METOTLARI
    # ====================================================================

    def process(
        self,
        input_data: PerceptualInput,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerceptualOutput:
        """
        Ana islem metodu - tam algi pipeline'i.

        Args:
            input_data: Ham algi girdisi
            context: Ek baglamsal bilgi (cycle_id, vb.)

        Returns:
            PerceptualOutput: Islenmis algi ciktisi
        """
        start_time = time.perf_counter()
        context = context or {}

        output = PerceptualOutput(
            cycle_id=context.get("cycle_id"),
            input_count=len(input_data.sensory_data),
        )

        try:
            # 1. Noise filtreleme
            if self.config.enable_noise_filter:
                input_data = self._apply_noise_filter(input_data)

            # 2. Ozellik cikarma
            extracted = self.extractor.extract_all(input_data)

            # 3. Attention filtreleme
            attention_focus = None
            if self.config.enable_attention_filter:
                attention_focus = self._apply_attention_filter(
                    extracted,
                    input_data,
                    context,
                )

            # 4. Features olustur
            features = self._build_features(
                extracted,
                attention_focus,
                input_data,
            )

            output.features = features
            output.success = True

            # 5. Ozet olustur
            output.summary = self._create_summary(features)

        except Exception as e:
            logger.error(f"Perception processing error: {e}")
            output.success = False
            output.error = str(e)

        # Islem suresi
        processing_time = (time.perf_counter() - start_time) * 1000
        output.processing_time_ms = processing_time

        # Istatistik guncelle
        self._processed_count += 1
        self._total_processing_time += processing_time

        if self.config.enable_logging:
            logger.debug(
                f"Perception processed: agents={len(output.features.agents)}, "
                f"threat={output.features.threat.overall_level.value}, "
                f"time={processing_time:.1f}ms"
            )

        return output

    def process_stimulus(
        self,
        stimulus: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerceptualOutput:
        """
        Stimulus'tan isle (eski API uyumlulugu).

        Foundation.types.Stimulus veya dict kabul eder.
        """
        input_data = self._stimulus_to_input(stimulus)
        return self.process(input_data, context)

    # ====================================================================
    # FAZ-SPESIFIK METOTLAR
    # ====================================================================

    def sense(
        self,
        raw_input: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerceptualInput:
        """
        SENSE fazi - ham girdiyi PerceptualInput'a cevir.

        Args:
            raw_input: Stimulus, dict, veya PerceptualInput

        Returns:
            PerceptualInput
        """
        if isinstance(raw_input, PerceptualInput):
            return raw_input

        return self._stimulus_to_input(raw_input)

    def attend(
        self,
        input_data: PerceptualInput,
        current_attention: Optional[AttentionFocus] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[PerceptualInput, AttentionFocus]:
        """
        ATTEND fazi - dikkat yonlendirme ve filtreleme.

        Args:
            input_data: SENSE'den gelen girdi
            current_attention: Mevcut dikkat odagi
            context: Ek bilgi

        Returns:
            (filtrelenmis_input, yeni_attention_focus)
        """
        context = context or {}

        # Noise filtrele
        if self.config.enable_noise_filter:
            input_data = self._apply_noise_filter(input_data)

        # Hizli ozellik cikarimi (attention icin)
        quick_features = self._quick_extract(input_data)

        # Attention hesapla
        attention = self.attention_filter.calculate_attention(
            quick_features,
            current_attention,
            context,
        )

        # Dikkat esiginin altindaki verileri filtrele
        if self.config.enable_attention_filter:
            input_data = self._filter_by_attention(input_data, attention)

        return input_data, attention

    def perceive(
        self,
        input_data: PerceptualInput,
        attention: Optional[AttentionFocus] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerceptualFeatures:
        """
        PERCEIVE fazi - tam ozellik cikarma.

        Args:
            input_data: ATTEND'den gelen filtrelenmis girdi
            attention: Dikkat odagi
            context: Ek bilgi

        Returns:
            PerceptualFeatures
        """
        context = context or {}

        # Tam ozellik cikarma
        extracted = self.extractor.extract_all(input_data)

        # Features olustur
        features = self._build_features(
            extracted,
            attention,
            input_data,
        )

        return features

    # ====================================================================
    # YARDIMCI METOTLAR
    # ====================================================================

    def _stimulus_to_input(self, stimulus: Any) -> PerceptualInput:
        """Stimulus'u PerceptualInput'a cevir."""
        input_data = PerceptualInput()

        if stimulus is None:
            return input_data

        # Foundation Stimulus nesnesi
        if hasattr(stimulus, "stimulus_type"):
            input_data.raw_stimulus = {
                "stimulus_type": stimulus.stimulus_type,
                "content": getattr(stimulus, "content", {}),
                "intensity": getattr(stimulus, "intensity", 0.5),
                "source_entity": getattr(stimulus, "source_entity", None),
            }
            input_data.intensity = stimulus.intensity

            # Stimulus type'a gore SensoryData olustur
            modality = self._stimulus_type_to_modality(stimulus.stimulus_type)
            if modality:
                sensory = SensoryData(
                    modality=modality,
                    raw_data=stimulus.content,
                    confidence=1.0,
                )
                input_data.sensory_data.append(sensory)

        # Dict
        elif isinstance(stimulus, dict):
            input_data.raw_stimulus = stimulus
            input_data.intensity = stimulus.get("intensity", 0.5)

            # Content'i sensory data'ya cevir
            if "content" in stimulus:
                modality = self._stimulus_type_to_modality(
                    stimulus.get("stimulus_type", "visual")
                )
                if modality:
                    sensory = SensoryData(
                        modality=modality,
                        raw_data=stimulus["content"],
                    )
                    input_data.sensory_data.append(sensory)

        return input_data

    def _stimulus_type_to_modality(self, stype: str) -> Optional[SensoryModality]:
        """Stimulus type'i SensoryModality'ye cevir."""
        mapping = {
            "visual": SensoryModality.VISUAL,
            "auditory": SensoryModality.AUDITORY,
            "social": SensoryModality.SOCIAL,
            "tactile": SensoryModality.TACTILE,
        }
        return mapping.get(stype.lower())

    def _apply_noise_filter(self, input_data: PerceptualInput) -> PerceptualInput:
        """Noise filtreleme uygula."""
        for i, sensory in enumerate(input_data.sensory_data):
            filtered = self.noise_filter.filter(sensory)
            input_data.sensory_data[i] = filtered
        return input_data

    def _apply_attention_filter(
        self,
        extracted: Dict[str, Any],
        input_data: PerceptualInput,
        context: Dict[str, Any],
    ) -> AttentionFocus:
        """Attention filtreleme uygula ve odak hesapla."""
        return self.attention_filter.calculate_attention(
            extracted,
            current_attention=None,
            context=context,
        )

    def _filter_by_attention(
        self,
        input_data: PerceptualInput,
        attention: AttentionFocus,
    ) -> PerceptualInput:
        """Dikkat esiginin altindaki verileri filtrele."""
        if attention.attention_level < self.config.attention_threshold:
            # Dusuk dikkat - sadece yuksek oncelikli verileri koru
            filtered_data = []
            for sensory in input_data.sensory_data:
                if sensory.confidence >= self.config.min_confidence:
                    filtered_data.append(sensory)
            input_data.sensory_data = filtered_data

        return input_data

    def _quick_extract(self, input_data: PerceptualInput) -> Dict[str, Any]:
        """Hizli ozellik cikarimi (attention hesabi icin)."""
        result = {
            "has_visual": False,
            "has_auditory": False,
            "has_motion": False,
            "has_face": False,
            "intensity": input_data.intensity,
            "urgency": input_data.urgency,
        }

        for sensory in input_data.sensory_data:
            if sensory.modality == SensoryModality.VISUAL:
                result["has_visual"] = True
                if sensory.raw_data and sensory.raw_data.get("face_detected"):
                    result["has_face"] = True
                if sensory.raw_data and sensory.raw_data.get("motion"):
                    result["has_motion"] = True

            elif sensory.modality == SensoryModality.AUDITORY:
                result["has_auditory"] = True

        return result

    def _build_features(
        self,
        extracted: Dict[str, Any],
        attention: Optional[AttentionFocus],
        input_data: PerceptualInput,
    ) -> PerceptualFeatures:
        """PerceptualFeatures olustur."""
        features = PerceptualFeatures()

        # Ajanlar
        features.agents = extracted.get("agents", [])

        # Tehdit
        features.threat = extracted.get("threat", ThreatAssessment())

        # Dikkat
        if attention:
            features.attention = attention
        else:
            features.attention = AttentionFocus()

        # Salience ve novelty
        features.salience_score = self._calculate_salience(extracted, input_data)
        features.novelty_score = self._calculate_novelty(extracted)

        # Kaynak input ID'leri
        features.source_input_ids = [input_data.id]

        return features

    def _calculate_salience(
        self,
        extracted: Dict[str, Any],
        input_data: PerceptualInput,
    ) -> float:
        """Belirginlik skoru hesapla."""
        score = 0.3  # Base

        # Yuksek yogunluk
        score += input_data.intensity * 0.2

        # Tehdit belirginligi arttirir
        threat = extracted.get("threat")
        if threat and threat.overall_score > 0:
            score += threat.overall_score * 0.3

        # Ajan varligi
        agents = extracted.get("agents", [])
        if agents:
            score += 0.2

        # Hareket
        motion = extracted.get("motion")
        if motion and motion.observed_motion:
            score += 0.1

        return min(1.0, score)

    def _calculate_novelty(self, extracted: Dict[str, Any]) -> float:
        """Yenilik skoru hesapla."""
        # Basit implementasyon - memory entegrasyonu ile gelistirilebilir
        score = 0.0

        # Bilinmeyen ajanlar
        agents = extracted.get("agents", [])
        unknown_count = sum(1 for a in agents if not a.known)
        if agents:
            score += (unknown_count / len(agents)) * 0.5

        return score

    def _create_summary(self, features: PerceptualFeatures) -> Dict[str, Any]:
        """Ozet olustur."""
        return {
            "agents_count": len(features.agents),
            "threatening_agents": len(features.get_threatening_agents()),
            "threat_level": features.threat.overall_level.value,
            "threat_score": features.threat.overall_score,
            "attention_target": features.attention.target_type,
            "attention_level": features.attention.attention_level,
            "salience": features.salience_score,
            "novelty": features.novelty_score,
        }

    # ====================================================================
    # ISTATISTIKLER
    # ====================================================================

    @property
    def stats(self) -> Dict[str, Any]:
        """Islem istatistikleri."""
        avg_time = 0.0
        if self._processed_count > 0:
            avg_time = self._total_processing_time / self._processed_count

        return {
            "processed_count": self._processed_count,
            "total_processing_time_ms": self._total_processing_time,
            "average_processing_time_ms": avg_time,
        }

    def reset_stats(self) -> None:
        """Istatistikleri sifirla."""
        self._processed_count = 0
        self._total_processing_time = 0.0


# ========================================================================
# FACTORY FONKSIYONLAR
# ========================================================================

_default_processor: Optional[PerceptionProcessor] = None


def get_perception_processor(
    config: Optional[ProcessorConfig] = None,
) -> PerceptionProcessor:
    """Default perception processor'i getir veya olustur."""
    global _default_processor

    if _default_processor is None or config is not None:
        _default_processor = PerceptionProcessor(config)

    return _default_processor


def reset_perception_processor() -> None:
    """Default processor'i sifirla."""
    global _default_processor
    _default_processor = None
