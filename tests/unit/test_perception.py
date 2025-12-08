"""
tests/unit/test_perception.py

Perception modulu testleri.
"""

import pytest
from datetime import datetime

# Types
from core.perception.types import (
    SensoryModality, PerceptualCategory, ThreatLevel,
    AgentDisposition, EmotionalExpression, BodyLanguage,
    VisualFeatures, AuditoryFeatures, MotionFeatures,
    SensoryData, PerceptualInput,
    PerceivedAgent, ThreatAssessment, AttentionFocus,
    PerceptualFeatures, PerceptualOutput,
)

# Extractor
from core.perception.extractor import (
    FeatureExtractor, ExtractorConfig,
    VisualFeatureExtractor, AuditoryFeatureExtractor,
    MotionFeatureExtractor, AgentExtractor, ThreatExtractor,
)

# Filters
from core.perception.filters import (
    AttentionFilter, NoiseFilter, SalienceFilter,
    FilterConfig, PerceptionFilterPipeline,
)

# Processor
from core.perception.processor import (
    PerceptionProcessor, ProcessorConfig,
    get_perception_processor, reset_perception_processor,
)


# ========================================================================
# TYPES TESTS
# ========================================================================

class TestSensoryModality:
    """SensoryModality enum testleri."""

    def test_visual_modality(self):
        assert SensoryModality.VISUAL == "visual"

    def test_auditory_modality(self):
        assert SensoryModality.AUDITORY == "auditory"

    def test_all_modalities_exist(self):
        modalities = [
            SensoryModality.VISUAL,
            SensoryModality.AUDITORY,
            SensoryModality.TACTILE,
            SensoryModality.PROPRIOCEPTIVE,
            SensoryModality.INTEROCEPTIVE,
            SensoryModality.SOCIAL,
        ]
        assert len(modalities) == 6


class TestThreatLevel:
    """ThreatLevel enum testleri."""

    def test_threat_levels(self):
        assert ThreatLevel.NONE.value == "none"
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MODERATE.value == "moderate"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"


class TestVisualFeatures:
    """VisualFeatures dataclass testleri."""

    def test_default_values(self):
        features = VisualFeatures()
        assert features.brightness == 0.5
        assert features.contrast == 0.5
        assert features.motion_detected is False
        assert features.distance_estimate == 1.0
        assert features.face_detected is False

    def test_custom_values(self):
        features = VisualFeatures(
            brightness=0.8,
            motion_detected=True,
            motion_direction="approaching",
            face_detected=True,
            expression=EmotionalExpression.ANGRY,
        )
        assert features.brightness == 0.8
        assert features.motion_detected is True
        assert features.motion_direction == "approaching"
        assert features.face_detected is True
        assert features.expression == EmotionalExpression.ANGRY


class TestAuditoryFeatures:
    """AuditoryFeatures dataclass testleri."""

    def test_default_values(self):
        features = AuditoryFeatures()
        assert features.volume == 0.5
        assert features.pitch == 0.5
        assert features.sound_type == "ambient"
        assert features.speech_detected is False

    def test_speech_detection(self):
        features = AuditoryFeatures(
            speech_detected=True,
            speech_tone="angry",
            speech_content="Get out!",
        )
        assert features.speech_detected is True
        assert features.speech_tone == "angry"
        assert features.speech_content == "Get out!"


class TestPerceivedAgent:
    """PerceivedAgent dataclass testleri."""

    def test_default_values(self):
        agent = PerceivedAgent(agent_id="test_agent")
        assert agent.agent_id == "test_agent"
        assert agent.agent_type == "unknown"
        assert agent.expression == EmotionalExpression.NEUTRAL
        assert agent.disposition == AgentDisposition.UNKNOWN
        assert agent.threat_level == ThreatLevel.NONE
        assert agent.threat_score == 0.0

    def test_hostile_agent(self):
        agent = PerceivedAgent(
            agent_id="enemy_1",
            agent_type="human",
            expression=EmotionalExpression.ANGRY,
            disposition=AgentDisposition.HOSTILE,
            body_language=BodyLanguage.AGGRESSIVE,
            approaching=True,
            threat_level=ThreatLevel.HIGH,
            threat_score=0.8,
        )
        assert agent.disposition == AgentDisposition.HOSTILE
        assert agent.threat_level == ThreatLevel.HIGH
        assert agent.approaching is True


class TestThreatAssessment:
    """ThreatAssessment dataclass testleri."""

    def test_default_no_threat(self):
        assessment = ThreatAssessment()
        assert assessment.overall_level == ThreatLevel.NONE
        assert assessment.overall_score == 0.0
        assert assessment.is_threatening() is False
        assert assessment.requires_immediate_action() is False

    def test_high_threat(self):
        assessment = ThreatAssessment(
            overall_level=ThreatLevel.HIGH,
            overall_score=0.75,
            threat_sources=["enemy_1"],
            primary_threat_id="enemy_1",
            suggested_response="flee",
        )
        assert assessment.is_threatening() is True
        assert assessment.requires_immediate_action() is True
        assert assessment.suggested_response == "flee"

    def test_moderate_threat(self):
        assessment = ThreatAssessment(
            overall_level=ThreatLevel.MODERATE,
            overall_score=0.5,
        )
        assert assessment.is_threatening() is True
        assert assessment.requires_immediate_action() is False


class TestPerceptualInput:
    """PerceptualInput dataclass testleri."""

    def test_default_values(self):
        input_data = PerceptualInput()
        assert input_data.source_type == "external"
        assert input_data.intensity == 0.5
        assert len(input_data.sensory_data) == 0

    def test_with_sensory_data(self):
        visual = SensoryData(
            modality=SensoryModality.VISUAL,
            raw_data={"brightness": 0.8},
        )
        input_data = PerceptualInput(
            sensory_data=[visual],
            intensity=0.7,
        )
        assert len(input_data.sensory_data) == 1
        assert input_data.has_modality(SensoryModality.VISUAL)
        assert not input_data.has_modality(SensoryModality.AUDITORY)

    def test_get_modality(self):
        visual = SensoryData(modality=SensoryModality.VISUAL)
        auditory = SensoryData(modality=SensoryModality.AUDITORY)
        input_data = PerceptualInput(sensory_data=[visual, auditory])

        assert input_data.get_modality(SensoryModality.VISUAL) == visual
        assert input_data.get_modality(SensoryModality.AUDITORY) == auditory
        assert input_data.get_modality(SensoryModality.TACTILE) is None


class TestPerceptualFeatures:
    """PerceptualFeatures dataclass testleri."""

    def test_default_values(self):
        features = PerceptualFeatures()
        assert len(features.agents) == 0
        assert features.salience_score == 0.5
        assert features.novelty_score == 0.0

    def test_get_primary_agent(self):
        agent1 = PerceivedAgent(agent_id="far", distance=10.0)
        agent2 = PerceivedAgent(agent_id="near", distance=2.0)
        features = PerceptualFeatures(agents=[agent1, agent2])

        primary = features.get_primary_agent()
        assert primary.agent_id == "near"

    def test_get_threatening_agents(self):
        safe = PerceivedAgent(agent_id="safe", threat_level=ThreatLevel.NONE)
        threat = PerceivedAgent(agent_id="threat", threat_level=ThreatLevel.HIGH)
        features = PerceptualFeatures(agents=[safe, threat])

        threatening = features.get_threatening_agents()
        assert len(threatening) == 1
        assert threatening[0].agent_id == "threat"


# ========================================================================
# EXTRACTOR TESTS
# ========================================================================

class TestVisualFeatureExtractor:
    """VisualFeatureExtractor testleri."""

    def test_extract_from_raw_data(self):
        extractor = VisualFeatureExtractor()
        data = SensoryData(
            modality=SensoryModality.VISUAL,
            raw_data={
                "brightness": 0.9,
                "motion": True,
                "motion_direction": "approaching",
                "face_detected": True,
                "expression": "angry",
            },
        )

        features = extractor.extract(data)
        assert features.brightness == 0.9
        assert features.motion_detected is True
        assert features.motion_direction == "approaching"
        assert features.face_detected is True
        assert features.expression == EmotionalExpression.ANGRY

    def test_extract_non_visual_returns_default(self):
        extractor = VisualFeatureExtractor()
        data = SensoryData(modality=SensoryModality.AUDITORY)

        features = extractor.extract(data)
        assert features.brightness == 0.5  # Default


class TestAuditoryFeatureExtractor:
    """AuditoryFeatureExtractor testleri."""

    def test_extract_speech(self):
        extractor = AuditoryFeatureExtractor()
        data = SensoryData(
            modality=SensoryModality.AUDITORY,
            raw_data={
                "volume": 0.8,
                "speech_detected": True,
                "speech_tone": "angry",
                "speech_content": "Stay away!",
            },
        )

        features = extractor.extract(data)
        assert features.volume == 0.8
        assert features.speech_detected is True
        assert features.speech_tone == "angry"
        assert features.speech_content == "Stay away!"


class TestAgentExtractor:
    """AgentExtractor testleri."""

    def test_extract_from_raw_stimulus(self):
        extractor = AgentExtractor()
        input_data = PerceptualInput(
            raw_stimulus={
                "detected_agents": [
                    {
                        "id": "alice",
                        "type": "human",
                        "expression": "happy",
                        "distance": 3.0,
                    }
                ]
            }
        )

        agents = extractor.extract_from_input(input_data)
        assert len(agents) == 1
        assert agents[0].agent_id == "alice"
        assert agents[0].expression == EmotionalExpression.HAPPY

    def test_extract_hostile_agent(self):
        extractor = AgentExtractor()
        input_data = PerceptualInput(
            raw_stimulus={
                "detected_agents": [
                    {
                        "id": "enemy",
                        "hostile": True,
                        "expression": "angry",
                        "body_language": "aggressive",
                    }
                ]
            }
        )

        agents = extractor.extract_from_input(input_data)
        assert len(agents) == 1
        assert agents[0].disposition == AgentDisposition.HOSTILE
        assert agents[0].expression == EmotionalExpression.ANGRY
        assert agents[0].body_language == BodyLanguage.AGGRESSIVE


class TestThreatExtractor:
    """ThreatExtractor testleri."""

    def test_no_threat(self):
        extractor = ThreatExtractor()
        agents = [
            PerceivedAgent(
                agent_id="friend",
                disposition=AgentDisposition.FRIENDLY,
                expression=EmotionalExpression.HAPPY,
            )
        ]

        assessment = extractor.extract(agents)
        assert assessment.overall_level == ThreatLevel.NONE
        assert assessment.overall_score < 0.2

    def test_hostile_agent_threat(self):
        extractor = ThreatExtractor()
        agents = [
            PerceivedAgent(
                agent_id="enemy",
                disposition=AgentDisposition.HOSTILE,
                expression=EmotionalExpression.ANGRY,
                body_language=BodyLanguage.AGGRESSIVE,
                approaching=True,
                distance=2.0,
            )
        ]

        assessment = extractor.extract(agents)
        # Hostile + angry + aggressive + approaching = very high threat
        assert assessment.overall_level in [ThreatLevel.MODERATE, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        assert assessment.overall_score > 0.3
        assert "enemy" in assessment.threat_sources

    def test_approaching_motion_threat(self):
        extractor = ThreatExtractor()
        motion = MotionFeatures(
            approach_detected=True,
            approach_speed=0.8,
            time_to_contact=3.0,
        )

        assessment = extractor.extract([], motion=motion)
        assert assessment.overall_score > 0


class TestFeatureExtractor:
    """FeatureExtractor (main) testleri."""

    def test_extract_all(self):
        extractor = FeatureExtractor()
        input_data = PerceptualInput(
            sensory_data=[
                SensoryData(
                    modality=SensoryModality.VISUAL,
                    raw_data={
                        "brightness": 0.7,
                        "face_detected": True,
                        "expression": "neutral",
                    },
                )
            ],
            raw_stimulus={
                "detected_agents": [
                    {"id": "person_1", "distance": 5.0}
                ]
            },
        )

        result = extractor.extract_all(input_data)

        assert result["visual"] is not None
        assert result["visual"].brightness == 0.7
        assert len(result["agents"]) >= 1
        assert result["threat"] is not None


# ========================================================================
# FILTER TESTS
# ========================================================================

class TestAttentionFilter:
    """AttentionFilter testleri."""

    def test_calculate_base_attention(self):
        filter = AttentionFilter()
        features = {"has_visual": True}

        attention = filter.calculate_attention(features)
        assert attention.attention_level >= 0.3
        assert attention.attention_type in ["voluntary", "reflexive", "sustained"]

    def test_threat_increases_attention(self):
        filter = AttentionFilter()

        # No threat
        features_safe = {"threat": ThreatAssessment()}
        attention_safe = filter.calculate_attention(features_safe)

        # With threat
        features_threat = {
            "threat": ThreatAssessment(
                overall_level=ThreatLevel.HIGH,
                overall_score=0.8,
            )
        }
        attention_threat = filter.calculate_attention(features_threat)

        assert attention_threat.attention_level > attention_safe.attention_level
        assert attention_threat.reason == "threat"

    def test_social_attention(self):
        filter = AttentionFilter()
        features = {
            "agents": [PerceivedAgent(agent_id="person")],
            "has_face": True,
        }

        attention = filter.calculate_attention(features)
        assert attention.attention_level > 0.3
        assert attention.target_type == "agent"


class TestNoiseFilter:
    """NoiseFilter testleri."""

    def test_filter_low_noise(self):
        filter = NoiseFilter()
        data = SensoryData(
            modality=SensoryModality.VISUAL,
            confidence=0.8,
            noise_level=0.05,
        )

        filtered = filter.filter(data)
        # Low noise should boost confidence
        assert filtered.confidence >= 0.8

    def test_filter_high_noise(self):
        filter = NoiseFilter()
        data = SensoryData(
            modality=SensoryModality.VISUAL,
            confidence=0.8,
            noise_level=0.5,
        )

        filtered = filter.filter(data)
        # High noise should reduce confidence
        assert filtered.confidence < 0.8

    def test_signal_quality(self):
        filter = NoiseFilter()

        good_data = SensoryData(
            modality=SensoryModality.VISUAL,
            confidence=0.9,
            noise_level=0.1,
        )
        bad_data = SensoryData(
            modality=SensoryModality.VISUAL,
            confidence=0.5,
            noise_level=0.5,
        )

        good_quality = filter.calculate_signal_quality(good_data)
        bad_quality = filter.calculate_signal_quality(bad_data)

        assert good_quality > bad_quality


class TestSalienceFilter:
    """SalienceFilter testleri."""

    def test_filter_by_salience(self):
        filter = SalienceFilter()
        items = [
            {"id": "a", "score": 0.3},
            {"id": "b", "score": 0.8},
            {"id": "c", "score": 0.5},
        ]

        filtered = filter.filter_by_salience(
            items, lambda x: x["score"]
        )

        # Should be sorted by salience, highest first
        assert filtered[0]["id"] == "b"

    def test_max_tracked_objects(self):
        filter = SalienceFilter(FilterConfig(max_tracked_objects=3))
        items = [{"id": str(i), "score": 0.5} for i in range(10)]

        filtered = filter.filter_by_salience(
            items, lambda x: float(x["score"])
        )

        assert len(filtered) <= 3


# ========================================================================
# PROCESSOR TESTS
# ========================================================================

class TestPerceptionProcessor:
    """PerceptionProcessor testleri."""

    def setup_method(self):
        reset_perception_processor()

    def test_process_empty_input(self):
        processor = PerceptionProcessor()
        input_data = PerceptualInput()

        output = processor.process(input_data)
        assert output.success is True
        assert len(output.features.agents) == 0

    def test_process_with_agent(self):
        processor = PerceptionProcessor()
        input_data = PerceptualInput(
            raw_stimulus={
                "detected_agents": [
                    {
                        "id": "test_agent",
                        "expression": "neutral",
                        "distance": 5.0,
                    }
                ]
            }
        )

        output = processor.process(input_data)
        assert output.success is True
        assert len(output.features.agents) >= 1

    def test_process_threat_detection(self):
        processor = PerceptionProcessor()
        input_data = PerceptualInput(
            raw_stimulus={
                "detected_agents": [
                    {
                        "id": "enemy",
                        "hostile": True,
                        "expression": "threatening",
                        "body_language": "aggressive",
                        "approaching": True,
                        "distance": 2.0,
                    }
                ]
            }
        )

        output = processor.process(input_data)
        assert output.success is True
        assert output.features.threat.overall_score > 0

    def test_sense_phase(self):
        processor = PerceptionProcessor()
        raw_stimulus = {
            "stimulus_type": "visual",
            "content": {"brightness": 0.8},
            "intensity": 0.7,
        }

        input_data = processor.sense(raw_stimulus)
        assert isinstance(input_data, PerceptualInput)
        assert input_data.intensity == 0.7

    def test_attend_phase(self):
        processor = PerceptionProcessor()
        input_data = PerceptualInput(
            sensory_data=[
                SensoryData(
                    modality=SensoryModality.VISUAL,
                    raw_data={"face_detected": True},
                )
            ]
        )

        filtered, attention = processor.attend(input_data)
        assert isinstance(attention, AttentionFocus)
        assert attention.attention_level > 0

    def test_perceive_phase(self):
        processor = PerceptionProcessor()
        input_data = PerceptualInput(
            raw_stimulus={
                "detected_agents": [{"id": "person"}]
            }
        )

        features = processor.perceive(input_data)
        assert isinstance(features, PerceptualFeatures)

    def test_stats(self):
        processor = PerceptionProcessor()
        input_data = PerceptualInput()

        processor.process(input_data)
        processor.process(input_data)

        stats = processor.stats
        assert stats["processed_count"] == 2
        assert stats["total_processing_time_ms"] > 0


class TestGetPerceptionProcessor:
    """get_perception_processor factory testleri."""

    def setup_method(self):
        reset_perception_processor()

    def test_returns_same_instance(self):
        p1 = get_perception_processor()
        p2 = get_perception_processor()
        assert p1 is p2

    def test_config_creates_new(self):
        p1 = get_perception_processor()
        p2 = get_perception_processor(ProcessorConfig(enable_logging=False))
        assert p1 is not p2


# ========================================================================
# INTEGRATION TESTS
# ========================================================================

class TestPerceptionIntegration:
    """Tam perception pipeline entegrasyon testleri."""

    def setup_method(self):
        reset_perception_processor()

    def test_full_pipeline_friendly_agent(self):
        """Dost ajan senaryosu."""
        processor = get_perception_processor()

        input_data = PerceptualInput(
            sensory_data=[
                SensoryData(
                    modality=SensoryModality.VISUAL,
                    raw_data={
                        "brightness": 0.7,
                        "face_detected": True,
                        "expression": "happy",
                    },
                ),
                SensoryData(
                    modality=SensoryModality.AUDITORY,
                    raw_data={
                        "speech_detected": True,
                        "speech_tone": "friendly",
                    },
                ),
            ],
            raw_stimulus={
                "detected_agents": [
                    {
                        "id": "alice",
                        "friendly": True,
                        "expression": "happy",
                        "distance": 3.0,
                    }
                ]
            },
            intensity=0.6,
        )

        output = processor.process(input_data)

        assert output.success is True
        assert len(output.features.agents) >= 1
        assert output.features.threat.overall_level in [ThreatLevel.NONE, ThreatLevel.LOW]
        assert output.summary["threat_level"] in ["none", "low"]

    def test_full_pipeline_hostile_agent(self):
        """Dusman ajan senaryosu."""
        processor = get_perception_processor()

        input_data = PerceptualInput(
            sensory_data=[
                SensoryData(
                    modality=SensoryModality.VISUAL,
                    raw_data={
                        "face_detected": True,
                        "expression": "angry",
                        "motion": True,
                        "motion_direction": "approaching",
                        "motion_speed": 0.8,
                    },
                ),
            ],
            raw_stimulus={
                "detected_agents": [
                    {
                        "id": "enemy",
                        "hostile": True,
                        "expression": "threatening",
                        "body_language": "aggressive",
                        "approaching": True,
                        "distance": 2.0,
                    }
                ]
            },
            intensity=0.9,
            urgency=0.8,
        )

        output = processor.process(input_data)

        assert output.success is True
        assert len(output.features.agents) >= 1
        assert output.features.threat.overall_score > 0.3
        assert output.features.threat.is_threatening() is True

    def test_full_pipeline_no_stimulus(self):
        """Stimulus olmadan calistirma."""
        processor = get_perception_processor()
        input_data = PerceptualInput()

        output = processor.process(input_data)

        assert output.success is True
        assert len(output.features.agents) == 0
        assert output.features.threat.overall_level == ThreatLevel.NONE

    def test_phase_by_phase(self):
        """Faz faz islem."""
        processor = get_perception_processor()

        # Raw stimulus
        raw = {
            "stimulus_type": "visual",
            "content": {"face_detected": True},
            "intensity": 0.7,
            "source_entity": {
                "id": "person",
                "entity_type": "agent",
            },
        }

        # SENSE
        sensed = processor.sense(raw)
        assert isinstance(sensed, PerceptualInput)

        # ATTEND
        attended, attention = processor.attend(sensed)
        assert isinstance(attention, AttentionFocus)

        # PERCEIVE
        features = processor.perceive(attended, attention)
        assert isinstance(features, PerceptualFeatures)
