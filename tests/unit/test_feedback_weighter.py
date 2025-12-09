"""
tests/unit/test_feedback_weighter.py

FeedbackWeighter ve ilgili siniflarin testleri.
"""

import pytest
from datetime import datetime, timedelta

from core.learning.episode import Episode, EpisodeOutcome
from core.learning.feedback import (
    FeedbackWeighter,
    FeedbackWeighterConfig,
    ImplicitSignals,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def weighter():
    """Varsayilan FeedbackWeighter."""
    return FeedbackWeighter()


@pytest.fixture
def custom_config():
    """Ozel konfigurasyon."""
    return FeedbackWeighterConfig(
        explicit_weight=2.0,
        trust_delta_weight=1.5,
        implicit_weight=1.0,
    )


@pytest.fixture
def basic_outcome():
    """Basit outcome."""
    return EpisodeOutcome(success=True)


@pytest.fixture
def positive_outcome():
    """Pozitif outcome."""
    return EpisodeOutcome(
        success=True,
        explicit_feedback=0.8,
        trust_delta=0.2
    )


@pytest.fixture
def negative_outcome():
    """Negatif outcome."""
    return EpisodeOutcome(
        success=False,
        explicit_feedback=-0.7,
        trust_delta=-0.3
    )


@pytest.fixture
def implicit_positive_outcome():
    """Implicit pozitif sinyalli outcome."""
    return EpisodeOutcome(
        success=True,
        implicit_signals={
            "conversation_continued": True,
            "asked_followup": True,
            "response_acknowledged": True,
        }
    )


@pytest.fixture
def implicit_negative_outcome():
    """Implicit negatif sinyalli outcome."""
    return EpisodeOutcome(
        success=False,
        implicit_signals={
            "repeated_question": True,
            "session_ended_abruptly": True,
        }
    )


def create_episode(
    message: str = "Test mesaji",
    outcome: EpisodeOutcome = None,
    trust_delta: float = 0.0,
    feedback: str = None,
    created_at: datetime = None
) -> Episode:
    """Episode olusturma yardimcisi."""
    return Episode(
        id=f"ep_{hash(message) % 10000:04d}",
        user_message=message,
        situation_summary={},
        dialogue_acts=["inform"],
        intent="test",
        emotion_label="neutral",
        constructions_used=[],
        outcome=outcome or EpisodeOutcome(success=True),
        trust_delta=trust_delta,
        feedback=feedback,
        created_at=created_at or datetime.now(),
    )


# =============================================================================
# FeedbackWeighterConfig Tests
# =============================================================================

class TestFeedbackWeighterConfig:
    """FeedbackWeighterConfig testleri."""

    def test_default_weights(self):
        """Varsayilan agirliklar."""
        config = FeedbackWeighterConfig()
        assert config.explicit_weight == 3.0
        assert config.trust_delta_weight == 1.0
        assert config.implicit_weight == 0.5

    def test_custom_weights(self):
        """Ozel agirliklar."""
        config = FeedbackWeighterConfig(
            explicit_weight=2.0,
            trust_delta_weight=1.5,
            implicit_weight=0.8
        )
        assert config.explicit_weight == 2.0
        assert config.trust_delta_weight == 1.5
        assert config.implicit_weight == 0.8

    def test_default_patterns(self):
        """Varsayilan pattern'ler."""
        config = FeedbackWeighterConfig()
        assert "tesekkur" in config.positive_patterns
        assert "harika" in config.positive_patterns
        assert "yanlis" in config.negative_patterns
        assert "kotu" in config.negative_patterns

    def test_normalize_turkish_default(self):
        """Turkce normalizasyon varsayilani."""
        config = FeedbackWeighterConfig()
        assert config.normalize_turkish is True


# =============================================================================
# ImplicitSignals Tests
# =============================================================================

class TestImplicitSignals:
    """ImplicitSignals testleri."""

    def test_default_signals(self):
        """Varsayilan sinyaller."""
        signals = ImplicitSignals()
        assert signals.conversation_continued is False
        assert signals.asked_followup is False
        assert signals.repeated_question is False
        assert signals.session_ended_abruptly is False

    def test_custom_signals(self):
        """Ozel sinyaller."""
        signals = ImplicitSignals(
            conversation_continued=True,
            asked_followup=True
        )
        assert signals.conversation_continued is True
        assert signals.asked_followup is True

    def test_to_dict(self):
        """Dict'e donusum."""
        signals = ImplicitSignals(
            conversation_continued=True,
            repeated_question=True
        )
        d = signals.to_dict()
        assert d["conversation_continued"] is True
        assert d["repeated_question"] is True
        assert d["asked_followup"] is False

    def test_from_dict(self):
        """Dict'ten olusturma."""
        data = {
            "conversation_continued": True,
            "session_ended_abruptly": True,
        }
        signals = ImplicitSignals.from_dict(data)
        assert signals.conversation_continued is True
        assert signals.session_ended_abruptly is True
        assert signals.asked_followup is False


# =============================================================================
# Extract Explicit Feedback Tests
# =============================================================================

class TestExtractExplicitFeedback:
    """extract_explicit_feedback testleri."""

    def test_positive_tesekkur(self, weighter):
        """Tesekkur pozitif."""
        assert weighter.extract_explicit_feedback("Teşekkürler!") == 1.0
        assert weighter.extract_explicit_feedback("Çok teşekkür ederim") == 1.0

    def test_positive_harika(self, weighter):
        """Harika pozitif."""
        assert weighter.extract_explicit_feedback("Harika bir cevap!") == 1.0
        assert weighter.extract_explicit_feedback("Bu mükemmel oldu") == 1.0

    def test_positive_yardimci(self, weighter):
        """Yardimci oldu pozitif."""
        assert weighter.extract_explicit_feedback("Çok yardımcı oldun") == 1.0

    def test_negative_yanlis(self, weighter):
        """Yanlis negatif."""
        assert weighter.extract_explicit_feedback("Bu yanlış!") == -1.0
        assert weighter.extract_explicit_feedback("Hatalı bilgi verdin") == -1.0

    def test_negative_kotu(self, weighter):
        """Kotu negatif."""
        assert weighter.extract_explicit_feedback("Kötü bir cevap") == -1.0
        assert weighter.extract_explicit_feedback("Berbat!") == -1.0

    def test_negative_yardimci_olmadi(self, weighter):
        """Yardimci olmadi negatif."""
        assert weighter.extract_explicit_feedback("Yardımcı olmadın") == -1.0

    def test_neutral_message(self, weighter):
        """Notr mesaj."""
        assert weighter.extract_explicit_feedback("Merhaba") is None
        assert weighter.extract_explicit_feedback("Bir soru sormak istiyorum") is None

    def test_empty_message(self, weighter):
        """Bos mesaj."""
        assert weighter.extract_explicit_feedback("") is None
        assert weighter.extract_explicit_feedback(None) is None

    def test_case_insensitive(self, weighter):
        """Buyuk/kucuk harf duyarsiz."""
        assert weighter.extract_explicit_feedback("TEŞEKKÜRLER") == 1.0
        assert weighter.extract_explicit_feedback("YANLIŞ") == -1.0


# =============================================================================
# Extract Implicit Signals Tests
# =============================================================================

class TestExtractImplicitSignals:
    """extract_implicit_signals testleri."""

    def test_empty_context(self, weighter):
        """Bos context."""
        signals = weighter.extract_implicit_signals({})
        assert signals.conversation_continued is False
        assert signals.asked_followup is False

    def test_positive_signals(self, weighter):
        """Pozitif sinyaller."""
        context = {
            "conversation_continued": True,
            "asked_followup": True,
            "response_acknowledged": True,
        }
        signals = weighter.extract_implicit_signals(context)
        assert signals.conversation_continued is True
        assert signals.asked_followup is True
        assert signals.response_acknowledged is True

    def test_negative_signals(self, weighter):
        """Negatif sinyaller."""
        context = {
            "repeated_question": True,
            "session_ended_abruptly": True,
        }
        signals = weighter.extract_implicit_signals(context)
        assert signals.repeated_question is True
        assert signals.session_ended_abruptly is True


# =============================================================================
# Compute Implicit Value Tests
# =============================================================================

class TestComputeImplicitValue:
    """compute_implicit_value testleri."""

    def test_all_positive_signals(self, weighter):
        """Tum pozitif sinyaller."""
        signals = ImplicitSignals(
            conversation_continued=True,  # +0.3
            asked_followup=True,  # +0.2
            response_acknowledged=True,  # +0.4
        )
        score = weighter.compute_implicit_value(signals)
        assert score == pytest.approx(0.9)

    def test_all_negative_signals(self, weighter):
        """Tum negatif sinyaller."""
        signals = ImplicitSignals(
            repeated_question=True,  # -0.5
            session_ended_abruptly=True,  # -0.4
            topic_changed=True,  # -0.2
        )
        score = weighter.compute_implicit_value(signals)
        assert score == pytest.approx(-1.0)  # Clamped

    def test_mixed_signals(self, weighter):
        """Karisik sinyaller."""
        signals = ImplicitSignals(
            conversation_continued=True,  # +0.3
            repeated_question=True,  # -0.5
        )
        score = weighter.compute_implicit_value(signals)
        assert score == pytest.approx(-0.2)

    def test_no_signals(self, weighter):
        """Sinyal yok."""
        signals = ImplicitSignals()
        score = weighter.compute_implicit_value(signals)
        assert score == 0.0


# =============================================================================
# Compute Feedback Score Tests
# =============================================================================

class TestComputeFeedbackScore:
    """compute_feedback_score testleri."""

    def test_explicit_feedback_only(self, weighter, positive_outcome):
        """Sadece explicit feedback."""
        episode = create_episode(
            message="Test",
            outcome=positive_outcome
        )
        score = weighter.compute_feedback_score(episode)
        # explicit=0.8 * 3.0 + trust=0.2 * 1.0 = 2.6 / 4.0 = 0.65
        # Episode also gets trust_delta from outcome
        assert 0.5 < score <= 0.85

    def test_negative_explicit_feedback(self, weighter, negative_outcome):
        """Negatif explicit feedback."""
        episode = create_episode(
            message="Test",
            outcome=negative_outcome
        )
        score = weighter.compute_feedback_score(episode)
        assert score < -0.3

    def test_implicit_signals_only(self, weighter, implicit_positive_outcome):
        """Sadece implicit sinyaller."""
        episode = create_episode(
            message="Test",
            outcome=implicit_positive_outcome
        )
        score = weighter.compute_feedback_score(episode)
        assert score > 0.3

    def test_no_signals(self, weighter, basic_outcome):
        """Hic sinyal yok."""
        episode = create_episode(
            message="Merhaba",  # Notr mesaj
            outcome=basic_outcome
        )
        score = weighter.compute_feedback_score(episode)
        assert score == 0.0

    def test_message_based_feedback(self, weighter, basic_outcome):
        """Mesajdan cikarilan feedback."""
        episode = create_episode(
            message="Teşekkürler!",
            outcome=basic_outcome
        )
        score = weighter.compute_feedback_score(episode)
        assert score == 1.0  # Explicit from message

    def test_trust_delta_effect(self, weighter):
        """Trust delta etkisi."""
        outcome = EpisodeOutcome(success=True, trust_delta=0.5)
        episode = create_episode(
            message="Neutral",
            outcome=outcome,
            trust_delta=0.5
        )
        score = weighter.compute_feedback_score(episode)
        # trust_delta=0.5 * 1.0 / 1.0 = 0.5
        assert score == pytest.approx(0.5)


# =============================================================================
# Aggregate Episode Feedback Tests
# =============================================================================

class TestAggregateEpisodeFeedback:
    """aggregate_episode_feedback testleri."""

    def test_empty_list(self, weighter):
        """Bos liste."""
        score = weighter.aggregate_episode_feedback([])
        assert score == 0.0

    def test_single_episode(self, weighter, positive_outcome):
        """Tek episode."""
        episode = create_episode(outcome=positive_outcome)
        score = weighter.aggregate_episode_feedback([episode])
        individual_score = weighter.compute_feedback_score(episode)
        assert score == pytest.approx(individual_score)

    def test_multiple_episodes(self, weighter, positive_outcome, negative_outcome):
        """Birden fazla episode."""
        episodes = [
            create_episode(outcome=positive_outcome),
            create_episode(outcome=negative_outcome),
        ]
        score = weighter.aggregate_episode_feedback(episodes)
        # Ortalama civarinda olmali
        assert -0.5 < score < 0.5

    def test_recent_weight(self, weighter):
        """Son episode'a daha fazla agirlik."""
        base_time = datetime.now()

        # Eski negatif, yeni pozitif
        episodes = [
            create_episode(
                message="Kötü!",
                outcome=EpisodeOutcome(success=False, explicit_feedback=-1.0),
                created_at=base_time - timedelta(hours=2)
            ),
            create_episode(
                message="Harika!",
                outcome=EpisodeOutcome(success=True, explicit_feedback=1.0),
                created_at=base_time
            ),
        ]

        score = weighter.aggregate_episode_feedback(episodes, recent_weight=2.0)
        # Yeni episode daha agir, skor pozitif olmali
        assert score > 0


# =============================================================================
# Get Feedback Breakdown Tests
# =============================================================================

class TestGetFeedbackBreakdown:
    """get_feedback_breakdown testleri."""

    def test_breakdown_structure(self, weighter, positive_outcome):
        """Breakdown yapisi."""
        episode = create_episode(outcome=positive_outcome)
        breakdown = weighter.get_feedback_breakdown(episode)

        assert "total_score" in breakdown
        assert "explicit" in breakdown
        assert "trust_delta" in breakdown
        assert "implicit" in breakdown

    def test_breakdown_explicit_source(self, weighter):
        """Explicit kaynak tespiti."""
        # Outcome'dan
        episode1 = create_episode(
            outcome=EpisodeOutcome(success=True, explicit_feedback=0.5)
        )
        breakdown1 = weighter.get_feedback_breakdown(episode1)
        assert breakdown1["explicit"]["source"] == "outcome"

        # Mesajdan
        episode2 = create_episode(
            message="Teşekkürler!",
            outcome=EpisodeOutcome(success=True)
        )
        breakdown2 = weighter.get_feedback_breakdown(episode2)
        assert breakdown2["explicit"]["source"] == "message"

    def test_breakdown_weights(self, weighter, positive_outcome):
        """Breakdown agirliklari."""
        episode = create_episode(outcome=positive_outcome)
        breakdown = weighter.get_feedback_breakdown(episode)

        assert breakdown["explicit"]["weight"] == 3.0
        assert breakdown["trust_delta"]["weight"] == 1.0
        assert breakdown["implicit"]["weight"] == 0.5


# =============================================================================
# Is Positive/Negative Feedback Tests
# =============================================================================

class TestIsFeedback:
    """is_positive_feedback ve is_negative_feedback testleri."""

    def test_is_positive(self, weighter, positive_outcome):
        """Pozitif feedback tespiti."""
        episode = create_episode(outcome=positive_outcome)
        assert weighter.is_positive_feedback(episode) is True
        assert weighter.is_negative_feedback(episode) is False

    def test_is_negative(self, weighter, negative_outcome):
        """Negatif feedback tespiti."""
        episode = create_episode(outcome=negative_outcome)
        assert weighter.is_negative_feedback(episode) is True
        assert weighter.is_positive_feedback(episode) is False

    def test_neutral(self, weighter, basic_outcome):
        """Notr feedback."""
        episode = create_episode(
            message="Merhaba",
            outcome=basic_outcome
        )
        # Notr - ne pozitif ne negatif
        assert weighter.is_positive_feedback(episode) is False
        assert weighter.is_negative_feedback(episode) is False


# =============================================================================
# Custom Config Tests
# =============================================================================

class TestCustomConfig:
    """Ozel konfigurasyon testleri."""

    def test_custom_weights(self, custom_config):
        """Ozel agirliklar."""
        weighter = FeedbackWeighter(config=custom_config)
        assert weighter.config.explicit_weight == 2.0
        assert weighter.config.trust_delta_weight == 1.5
        assert weighter.config.implicit_weight == 1.0

    def test_custom_patterns(self):
        """Ozel pattern'ler."""
        config = FeedbackWeighterConfig(
            positive_patterns={"super", "mukemmel"},
            negative_patterns={"fena", "kotu"}
        )
        weighter = FeedbackWeighter(config=config)

        assert weighter.extract_explicit_feedback("Super!") == 1.0
        assert weighter.extract_explicit_feedback("Fena oldu") == -1.0
        # Varsayilan pattern'ler artik calismaz
        assert weighter.extract_explicit_feedback("Teşekkürler") is None


# =============================================================================
# Turkish Normalization Tests
# =============================================================================

class TestTurkishNormalization:
    """Turkce normalizasyon testleri."""

    def test_turkish_characters(self, weighter):
        """Turkce karakterler."""
        assert weighter.extract_explicit_feedback("Teşekkürler") == 1.0
        assert weighter.extract_explicit_feedback("Çok güzel") == 1.0
        assert weighter.extract_explicit_feedback("Yanlış!") == -1.0

    def test_uppercase_turkish(self, weighter):
        """Buyuk harf Turkce."""
        assert weighter.extract_explicit_feedback("TEŞEKKÜRLER") == 1.0
        assert weighter.extract_explicit_feedback("ÇOK GÜZEL") == 1.0

    def test_mixed_case(self, weighter):
        """Karisik buyuk/kucuk harf."""
        assert weighter.extract_explicit_feedback("TeŞeKküRLer") == 1.0
