"""
core/perception/extractor.py

Feature Extractor - Ham duyusal veriden ozellik cikarma.

Gorevler:
- Gorsel ozellik cikarma (yuz, ifade, hareket)
- Isitsel ozellik cikarma (ses tonu, konusma)
- Hareket analizi
- Ajan algisi
- Tehdit ipuclari cikarma
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import math

from .types import (
    SensoryModality, SensoryData,
    VisualFeatures, AuditoryFeatures, MotionFeatures,
    PerceivedAgent, ThreatAssessment, ThreatLevel,
    EmotionalExpression, BodyLanguage, AgentDisposition,
    PerceptualInput,
)

logger = logging.getLogger(__name__)


# ========================================================================
# CONFIGURATION
# ========================================================================

@dataclass
class ExtractorConfig:
    """Feature extractor yapilandirmasi."""

    # Gorsel analiz
    enable_face_detection: bool = True
    enable_expression_analysis: bool = True
    enable_motion_tracking: bool = True

    # Isitsel analiz
    enable_speech_detection: bool = True
    enable_tone_analysis: bool = True

    # Tehdit analizi
    enable_threat_detection: bool = True
    threat_keywords: List[str] = field(default_factory=lambda: [
        "angry", "hostile", "aggressive", "threatening",
        "attack", "enemy", "danger", "warning"
    ])
    threat_expressions: List[EmotionalExpression] = field(default_factory=lambda: [
        EmotionalExpression.ANGRY,
        EmotionalExpression.THREATENING,
        EmotionalExpression.CONTEMPTUOUS,
    ])

    # Esik degerleri
    face_confidence_threshold: float = 0.5
    speech_confidence_threshold: float = 0.5
    threat_threshold: float = 0.3


# ========================================================================
# VISUAL FEATURE EXTRACTOR
# ========================================================================

class VisualFeatureExtractor:
    """Gorsel ozellik cikarici."""

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

    def extract(self, data: SensoryData) -> VisualFeatures:
        """Gorsel veriden ozellik cikar."""
        if data.modality != SensoryModality.VISUAL:
            return VisualFeatures()

        features = VisualFeatures()

        # Ham veriden cikar
        if data.raw_data:
            raw = data.raw_data

            # Temel ozellikler
            features.brightness = raw.get("brightness", 0.5)
            features.contrast = raw.get("contrast", 0.5)
            features.color_dominant = raw.get("color", None)

            # Hareket
            if self.config.enable_motion_tracking:
                features.motion_detected = raw.get("motion", False)
                features.motion_direction = raw.get("motion_direction", None)
                features.motion_speed = raw.get("motion_speed", 0.0)

            # Uzamsal
            features.distance_estimate = raw.get("distance", 1.0)
            features.size_estimate = raw.get("size", 1.0)
            if "position" in raw:
                features.position = tuple(raw["position"])

            # Yuz algilama
            if self.config.enable_face_detection:
                features.face_detected = raw.get("face_detected", False)
                if features.face_detected:
                    expr_str = raw.get("expression", "neutral")
                    features.expression = self._parse_expression(expr_str)
                    features.gaze_direction = raw.get("gaze", None)

            # Belirgin ozellikler
            if "salient" in raw:
                features.salient_features = raw["salient"]

        # Visual data'dan da cikar (eger varsa)
        if data.visual:
            # Mevcut degerleri koru, eksikleri doldur
            if not features.face_detected:
                features.face_detected = data.visual.face_detected
            if features.expression is None:
                features.expression = data.visual.expression

        return features

    def _parse_expression(self, expr_str: str) -> EmotionalExpression:
        """String ifadeyi enum'a cevir."""
        expr_lower = expr_str.lower()
        mapping = {
            "neutral": EmotionalExpression.NEUTRAL,
            "happy": EmotionalExpression.HAPPY,
            "sad": EmotionalExpression.SAD,
            "angry": EmotionalExpression.ANGRY,
            "fearful": EmotionalExpression.FEARFUL,
            "surprised": EmotionalExpression.SURPRISED,
            "disgusted": EmotionalExpression.DISGUSTED,
            "contempt": EmotionalExpression.CONTEMPTUOUS,
            "contemptuous": EmotionalExpression.CONTEMPTUOUS,
            "threatening": EmotionalExpression.THREATENING,
        }
        return mapping.get(expr_lower, EmotionalExpression.NEUTRAL)


# ========================================================================
# AUDITORY FEATURE EXTRACTOR
# ========================================================================

class AuditoryFeatureExtractor:
    """Isitsel ozellik cikarici."""

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

    def extract(self, data: SensoryData) -> AuditoryFeatures:
        """Isitsel veriden ozellik cikar."""
        if data.modality != SensoryModality.AUDITORY:
            return AuditoryFeatures()

        features = AuditoryFeatures()

        if data.raw_data:
            raw = data.raw_data

            # Temel ses ozellikleri
            features.volume = raw.get("volume", 0.5)
            features.pitch = raw.get("pitch", 0.5)
            features.tempo = raw.get("tempo", 0.5)

            # Ses turu
            features.sound_type = raw.get("sound_type", "ambient")

            # Konusma algilama
            if self.config.enable_speech_detection:
                features.speech_detected = raw.get("speech_detected", False)
                if features.speech_detected:
                    features.speech_content = raw.get("speech_content", None)

                    if self.config.enable_tone_analysis:
                        features.speech_tone = raw.get("speech_tone", None)

            # Mekansal
            features.direction = raw.get("direction", None)
            features.distance_estimate = raw.get("distance", 1.0)

            # Alarm
            features.is_alarm = raw.get("is_alarm", False)
            features.urgency_level = raw.get("urgency", 0.0)

        # Auditory data'dan da cikar
        if data.auditory:
            if not features.speech_detected:
                features.speech_detected = data.auditory.speech_detected
            if features.speech_tone is None:
                features.speech_tone = data.auditory.speech_tone

        return features


# ========================================================================
# MOTION FEATURE EXTRACTOR
# ========================================================================

class MotionFeatureExtractor:
    """Hareket ozellik cikarici."""

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

    def extract(
        self,
        visual: Optional[VisualFeatures] = None,
        auditory: Optional[AuditoryFeatures] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> MotionFeatures:
        """Hareket ozellikleri cikar."""
        features = MotionFeatures()

        # Gorsel hareketten cikar
        if visual and visual.motion_detected:
            features.observed_motion = True

            # Yaklasma tespiti
            if visual.motion_direction == "approaching":
                features.approach_detected = True
                features.approach_speed = visual.motion_speed

                # Temas zamani tahmini
                if visual.distance_estimate > 0 and visual.motion_speed > 0:
                    # Basit tahmin: mesafe / hiz
                    speed_mps = visual.motion_speed * 5  # Normalize (0-1 -> 0-5 m/s)
                    if speed_mps > 0:
                        features.time_to_contact = visual.distance_estimate / speed_mps

            # Hareket paterni
            if visual.motion_speed > 0.7:
                features.motion_pattern = "running"
            elif visual.motion_speed > 0.3:
                features.motion_pattern = "walking"
            else:
                features.motion_pattern = "stationary"

        # Raw data'dan ek bilgi
        if raw_data:
            if "self_velocity" in raw_data:
                features.self_velocity = tuple(raw_data["self_velocity"])
            if "self_acceleration" in raw_data:
                features.self_acceleration = tuple(raw_data["self_acceleration"])

        return features


# ========================================================================
# AGENT EXTRACTOR
# ========================================================================

class AgentExtractor:
    """Ajan algilama ve ozellik cikarma."""

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

    def extract_from_input(
        self,
        input_data: PerceptualInput,
        visual: Optional[VisualFeatures] = None,
        auditory: Optional[AuditoryFeatures] = None,
        motion: Optional[MotionFeatures] = None,
    ) -> List[PerceivedAgent]:
        """Girdi verisinden ajan bilgisi cikar."""
        agents: List[PerceivedAgent] = []

        # Raw stimulus'tan ajan cikar
        if input_data.raw_stimulus:
            stimulus = input_data.raw_stimulus

            # Source entity varsa
            if "source_entity" in stimulus:
                entity = stimulus["source_entity"]
                agent = self._extract_from_entity(entity, visual, auditory, motion)
                if agent:
                    agents.append(agent)

            # Detected agents listesi
            if "detected_agents" in stimulus:
                for agent_data in stimulus["detected_agents"]:
                    agent = self._extract_from_dict(agent_data, visual, auditory, motion)
                    if agent:
                        agents.append(agent)

        # Gorsel veriden yuz algilandi ise
        if visual and visual.face_detected and not agents:
            # Anonim ajan olustur
            agent = PerceivedAgent(
                agent_id=f"unknown_{datetime.now().timestamp()}",
                expression=visual.expression or EmotionalExpression.NEUTRAL,
                distance=visual.distance_estimate,
                position=visual.position,
            )
            agents.append(agent)

        return agents

    def _extract_from_entity(
        self,
        entity: Any,
        visual: Optional[VisualFeatures],
        auditory: Optional[AuditoryFeatures],
        motion: Optional[MotionFeatures],
    ) -> Optional[PerceivedAgent]:
        """Entity nesnesinden ajan cikar."""
        if entity is None:
            return None

        # Entity dict veya object olabilir
        if hasattr(entity, "id"):
            agent_id = entity.id
            entity_type = getattr(entity, "entity_type", "unknown")
            attrs = getattr(entity, "attributes", {})
        elif isinstance(entity, dict):
            agent_id = entity.get("id", f"entity_{datetime.now().timestamp()}")
            entity_type = entity.get("entity_type", "unknown")
            attrs = entity.get("attributes", entity)
        else:
            return None

        # Agent degilse atla
        if entity_type not in ["agent", "human", "unknown"]:
            return None

        agent = PerceivedAgent(
            agent_id=agent_id,
            agent_type=entity_type,
        )

        # Attribute'lardan doldur
        self._fill_from_attributes(agent, attrs, visual, auditory, motion)

        return agent

    def _extract_from_dict(
        self,
        data: Dict[str, Any],
        visual: Optional[VisualFeatures],
        auditory: Optional[AuditoryFeatures],
        motion: Optional[MotionFeatures],
    ) -> Optional[PerceivedAgent]:
        """Dict'ten ajan cikar."""
        agent_id = data.get("id", f"agent_{datetime.now().timestamp()}")

        agent = PerceivedAgent(
            agent_id=agent_id,
            agent_type=data.get("type", "unknown"),
            name=data.get("name"),
        )

        self._fill_from_attributes(agent, data, visual, auditory, motion)

        return agent

    def _fill_from_attributes(
        self,
        agent: PerceivedAgent,
        attrs: Dict[str, Any],
        visual: Optional[VisualFeatures],
        auditory: Optional[AuditoryFeatures],
        motion: Optional[MotionFeatures],
    ) -> None:
        """Attribute'lardan ajan bilgilerini doldur."""

        # Duygusal ipuclari
        if "expression" in attrs:
            agent.expression = self._parse_expression(attrs["expression"])
        elif visual and visual.expression:
            agent.expression = visual.expression

        if "body_language" in attrs:
            agent.body_language = self._parse_body_language(attrs["body_language"])

        # Disposition
        if "hostile" in attrs and attrs["hostile"]:
            agent.disposition = AgentDisposition.HOSTILE
        elif "friendly" in attrs and attrs["friendly"]:
            agent.disposition = AgentDisposition.FRIENDLY
        elif "disposition" in attrs:
            agent.disposition = self._parse_disposition(attrs["disposition"])

        # PAD tahmini
        agent.estimated_valence = attrs.get("valence", 0.0)
        agent.estimated_arousal = attrs.get("arousal", 0.5)
        agent.estimated_dominance = attrs.get("dominance", 0.5)

        # Pozisyon ve mesafe
        if "position" in attrs:
            agent.position = tuple(attrs["position"])
        elif visual and visual.position:
            agent.position = visual.position

        if "distance" in attrs:
            agent.distance = attrs["distance"]
        elif visual:
            agent.distance = visual.distance_estimate

        # Hareket
        if motion:
            agent.is_moving = motion.observed_motion
            agent.approaching = motion.approach_detected
        if "approaching" in attrs:
            agent.approaching = attrs["approaching"]

        # Konusma
        if auditory:
            agent.speaking = auditory.speech_detected
            agent.voice_tone = auditory.speech_tone
            agent.verbal_content = auditory.speech_content

        # Iliski bilgisi
        agent.known = attrs.get("known", False)
        agent.relationship_type = attrs.get("relationship", None)
        agent.trust_level = attrs.get("trust_level", None)

        # Tehdit (ilk deger, sonra ThreatExtractor detaylandirir)
        if attrs.get("threatening", False) or attrs.get("hostile", False):
            agent.threat_level = ThreatLevel.MODERATE
            agent.threat_score = 0.5

    def _parse_expression(self, expr: str) -> EmotionalExpression:
        """String ifadeyi enum'a cevir."""
        expr_lower = expr.lower()
        mapping = {
            "neutral": EmotionalExpression.NEUTRAL,
            "happy": EmotionalExpression.HAPPY,
            "sad": EmotionalExpression.SAD,
            "angry": EmotionalExpression.ANGRY,
            "fearful": EmotionalExpression.FEARFUL,
            "surprised": EmotionalExpression.SURPRISED,
            "disgusted": EmotionalExpression.DISGUSTED,
            "contempt": EmotionalExpression.CONTEMPTUOUS,
            "contemptuous": EmotionalExpression.CONTEMPTUOUS,
            "threatening": EmotionalExpression.THREATENING,
        }
        return mapping.get(expr_lower, EmotionalExpression.NEUTRAL)

    def _parse_body_language(self, bl: str) -> BodyLanguage:
        """String body language'i enum'a cevir."""
        bl_lower = bl.lower()
        mapping = {
            "open": BodyLanguage.OPEN,
            "closed": BodyLanguage.CLOSED,
            "aggressive": BodyLanguage.AGGRESSIVE,
            "submissive": BodyLanguage.SUBMISSIVE,
            "relaxed": BodyLanguage.RELAXED,
            "tense": BodyLanguage.TENSE,
            "neutral": BodyLanguage.NEUTRAL,
        }
        return mapping.get(bl_lower, BodyLanguage.NEUTRAL)

    def _parse_disposition(self, disp: str) -> AgentDisposition:
        """String disposition'i enum'a cevir."""
        disp_lower = disp.lower()
        mapping = {
            "friendly": AgentDisposition.FRIENDLY,
            "neutral": AgentDisposition.NEUTRAL,
            "unfriendly": AgentDisposition.UNFRIENDLY,
            "hostile": AgentDisposition.HOSTILE,
            "unknown": AgentDisposition.UNKNOWN,
        }
        return mapping.get(disp_lower, AgentDisposition.UNKNOWN)


# ========================================================================
# THREAT EXTRACTOR
# ========================================================================

class ThreatExtractor:
    """Tehdit degerlendirmesi cikarici."""

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

    def extract(
        self,
        agents: List[PerceivedAgent],
        visual: Optional[VisualFeatures] = None,
        auditory: Optional[AuditoryFeatures] = None,
        motion: Optional[MotionFeatures] = None,
        input_data: Optional[PerceptualInput] = None,
    ) -> ThreatAssessment:
        """Tehdit degerlendirmesi yap."""
        assessment = ThreatAssessment()

        threat_scores: List[Tuple[str, float]] = []
        indicators: List[str] = []

        # 1. Ajan bazli tehdit
        for agent in agents:
            agent_threat = self._assess_agent_threat(agent)
            if agent_threat > 0:
                threat_scores.append((agent.agent_id, agent_threat))
                agent.threat_score = agent_threat
                agent.threat_level = self._score_to_level(agent_threat)

                if agent_threat > self.config.threat_threshold:
                    assessment.threat_sources.append(agent.agent_id)
                    indicators.append(f"Agent {agent.agent_id}: {agent.threat_level.value}")

        # 2. Hareket bazli tehdit
        if motion and motion.approach_detected:
            approach_threat = motion.approach_speed * 0.4
            if motion.time_to_contact and motion.time_to_contact < 5:
                approach_threat += 0.3  # 5 saniyeden az
            threat_scores.append(("approach", approach_threat))
            indicators.append(f"Rapid approach detected (speed={motion.approach_speed:.2f})")

        # 3. Ses bazli tehdit
        if auditory:
            if auditory.is_alarm:
                threat_scores.append(("alarm", auditory.urgency_level))
                indicators.append("Alarm sound detected")
            if auditory.speech_tone in ["angry", "threatening"]:
                threat_scores.append(("voice", 0.4))
                indicators.append(f"Threatening voice tone: {auditory.speech_tone}")

        # 4. Gorsel tehdit ipuclari
        if visual:
            if visual.motion_detected and visual.motion_direction == "approaching":
                if visual.motion_speed > 0.7:
                    threat_scores.append(("fast_approach", 0.5))
                    indicators.append("Fast approaching motion")

        # 5. Keyword bazli tehdit (stimulus content'ten)
        if input_data and input_data.raw_stimulus:
            content = str(input_data.raw_stimulus).lower()
            for keyword in self.config.threat_keywords:
                if keyword in content:
                    threat_scores.append(("keyword", 0.3))
                    indicators.append(f"Threat keyword: {keyword}")
                    break

        # Toplam tehdit hesapla
        if threat_scores:
            max_threat = max(score for _, score in threat_scores)
            avg_threat = sum(score for _, score in threat_scores) / len(threat_scores)

            # Max ve ortalama arasinda agirlikli ortalama
            assessment.overall_score = max_threat * 0.7 + avg_threat * 0.3
            assessment.overall_level = self._score_to_level(assessment.overall_score)

            # En buyuk tehdit kaynagi
            if threat_scores:
                max_source = max(threat_scores, key=lambda x: x[1])
                if max_source[0] not in ["approach", "alarm", "voice", "fast_approach", "keyword"]:
                    assessment.primary_threat_id = max_source[0]

        # Tehdit turleri
        assessment.physical_threat = self._calc_physical_threat(agents, motion)
        assessment.social_threat = self._calc_social_threat(agents, auditory)

        # Indicators
        assessment.indicators = indicators

        # Onerilen tepki
        assessment.suggested_response = self._suggest_response(assessment)
        assessment.urgency = min(1.0, assessment.overall_score * 1.5)

        return assessment

    def _assess_agent_threat(self, agent: PerceivedAgent) -> float:
        """Tek bir ajanin tehdit skorunu hesapla."""
        score = 0.0

        # Disposition
        if agent.disposition == AgentDisposition.HOSTILE:
            score += 0.5
        elif agent.disposition == AgentDisposition.UNFRIENDLY:
            score += 0.2

        # Expression
        if agent.expression in self.config.threat_expressions:
            score += 0.3

        # Body language
        if agent.body_language == BodyLanguage.AGGRESSIVE:
            score += 0.3
        elif agent.body_language == BodyLanguage.TENSE:
            score += 0.1

        # Yaklasma
        if agent.approaching:
            score += 0.2

        # Mesafe (yakin = daha tehdit edici)
        if agent.distance < 2.0:
            score += 0.2 * (1 - agent.distance / 2.0)

        # Mevcut tehdit seviyesi
        if agent.threat_level != ThreatLevel.NONE:
            score += agent.threat_score * 0.3

        return min(1.0, score)

    def _score_to_level(self, score: float) -> ThreatLevel:
        """Skoru tehdit seviyesine cevir."""
        if score >= 0.8:
            return ThreatLevel.CRITICAL
        elif score >= 0.6:
            return ThreatLevel.HIGH
        elif score >= 0.4:
            return ThreatLevel.MODERATE
        elif score >= 0.2:
            return ThreatLevel.LOW
        return ThreatLevel.NONE

    def _calc_physical_threat(
        self,
        agents: List[PerceivedAgent],
        motion: Optional[MotionFeatures],
    ) -> float:
        """Fiziksel tehdit hesapla."""
        score = 0.0

        for agent in agents:
            if agent.body_language == BodyLanguage.AGGRESSIVE:
                score = max(score, 0.5)
            if agent.approaching and agent.distance < 3:
                score = max(score, 0.4)

        if motion and motion.approach_detected:
            score = max(score, motion.approach_speed * 0.5)

        return min(1.0, score)

    def _calc_social_threat(
        self,
        agents: List[PerceivedAgent],
        auditory: Optional[AuditoryFeatures],
    ) -> float:
        """Sosyal tehdit hesapla."""
        score = 0.0

        for agent in agents:
            if agent.expression in [EmotionalExpression.CONTEMPTUOUS, EmotionalExpression.DISGUSTED]:
                score = max(score, 0.4)

        if auditory and auditory.speech_tone in ["contemptuous", "mocking"]:
            score = max(score, 0.3)

        return min(1.0, score)

    def _suggest_response(self, assessment: ThreatAssessment) -> str:
        """Onerilen tepkiyi belirle."""
        if assessment.overall_level == ThreatLevel.CRITICAL:
            if assessment.physical_threat > assessment.social_threat:
                return "flee"
            return "confront"

        if assessment.overall_level == ThreatLevel.HIGH:
            return "avoid"

        if assessment.overall_level == ThreatLevel.MODERATE:
            return "observe"

        if assessment.overall_level == ThreatLevel.LOW:
            return "observe"

        return "approach"


# ========================================================================
# MAIN FEATURE EXTRACTOR
# ========================================================================

class FeatureExtractor:
    """
    Ana ozellik cikarici - tum alt cikaricilari koordine eder.

    Kullanim:
        extractor = FeatureExtractor()
        features = extractor.extract(perceptual_input)
    """

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()

        # Alt cikaricilar
        self.visual_extractor = VisualFeatureExtractor(self.config)
        self.auditory_extractor = AuditoryFeatureExtractor(self.config)
        self.motion_extractor = MotionFeatureExtractor(self.config)
        self.agent_extractor = AgentExtractor(self.config)
        self.threat_extractor = ThreatExtractor(self.config)

    def extract_all(
        self,
        input_data: PerceptualInput,
    ) -> Dict[str, Any]:
        """
        Tum ozellikleri cikar.

        Returns:
            {
                "visual": VisualFeatures,
                "auditory": AuditoryFeatures,
                "motion": MotionFeatures,
                "agents": List[PerceivedAgent],
                "threat": ThreatAssessment,
            }
        """
        result: Dict[str, Any] = {
            "visual": None,
            "auditory": None,
            "motion": None,
            "agents": [],
            "threat": ThreatAssessment(),
        }

        # 1. Modality-spesifik cikarma
        for sensory_data in input_data.sensory_data:
            if sensory_data.modality == SensoryModality.VISUAL:
                result["visual"] = self.visual_extractor.extract(sensory_data)

            elif sensory_data.modality == SensoryModality.AUDITORY:
                result["auditory"] = self.auditory_extractor.extract(sensory_data)

        # 2. Hareket cikarma
        result["motion"] = self.motion_extractor.extract(
            visual=result["visual"],
            auditory=result["auditory"],
            raw_data=input_data.raw_stimulus,
        )

        # 3. Ajan cikarma
        result["agents"] = self.agent_extractor.extract_from_input(
            input_data,
            visual=result["visual"],
            auditory=result["auditory"],
            motion=result["motion"],
        )

        # 4. Tehdit degerlendirmesi
        if self.config.enable_threat_detection:
            result["threat"] = self.threat_extractor.extract(
                agents=result["agents"],
                visual=result["visual"],
                auditory=result["auditory"],
                motion=result["motion"],
                input_data=input_data,
            )

        return result

    def extract_visual(self, data: SensoryData) -> VisualFeatures:
        """Sadece gorsel ozellik cikar."""
        return self.visual_extractor.extract(data)

    def extract_auditory(self, data: SensoryData) -> AuditoryFeatures:
        """Sadece isitsel ozellik cikar."""
        return self.auditory_extractor.extract(data)

    def extract_threat(
        self,
        agents: List[PerceivedAgent],
        **kwargs,
    ) -> ThreatAssessment:
        """Tehdit degerlendirmesi yap."""
        return self.threat_extractor.extract(agents, **kwargs)
