"""
core/learning/episode_logger.py

Faz 5 Episode Logger - EpisodeLog yaşam döngüsü yönetimi.

EpisodeLogger bir conversation turn sırasında EpisodeLog'u adım adım oluşturur:
1. start_episode() - User mesajı ile başlat
2. update_intent() - Intent recognition sonucu
3. update_context() - Context snapshot
4. update_decision() - Act selection sonucu
5. update_construction() - Construction details
6. update_output() - Response text
7. update_risk() - Risk & approval
8. finalize_episode() - Tamamla ve kaydet

Feedback daha sonra eklenebilir (add_feedback).

UEM v2 - Faz 5 Pattern Evolution Logger.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from core.language.intent.types import IntentCategory
from core.language.dialogue.types import DialogueAct
from core.language.risk.types import RiskLevel
from core.language.conversation import ContextManager

from .episode_types import (
    EpisodeLog,
    ImplicitFeedback,
    ConstructionSource,
    ConstructionLevel,
    ApprovalStatus,
    generate_episode_log_id,
)
from .episode_store import EpisodeStore


class EpisodeLogger:
    """
    Episode Logger - Progressive episode log building.

    Bir conversation turn sırasında EpisodeLog'u adım adım oluşturur.
    Finalize edildiğinde store'a kaydeder.

    Attributes:
        store: EpisodeStore implementation
        session_id: Current session ID
        current_episode: Şu an oluşturulmakta olan episode
        turn_number: Current turn number (session içinde)
    """

    def __init__(self, store: EpisodeStore, session_id: str):
        """
        Initialize Episode Logger.

        Args:
            store: EpisodeStore implementation
            session_id: Session ID
        """
        self.store = store
        self.session_id = session_id
        self.current_episode: Optional[EpisodeLog] = None
        self.turn_number = 0

    def start_episode(
        self,
        user_message: str,
        user_message_normalized: str,
    ) -> str:
        """
        Yeni bir episode başlat.

        Args:
            user_message: Raw user message
            user_message_normalized: Normalized user message

        Returns:
            str: Episode ID
        """
        self.turn_number += 1
        episode_id = generate_episode_log_id()

        # Minimal episode oluştur (diğer alanlar adım adım doldurulacak)
        self.current_episode = EpisodeLog(
            id=episode_id,
            session_id=self.session_id,
            turn_number=self.turn_number,
            timestamp=datetime.now(),
            user_message=user_message,
            user_message_normalized=user_message_normalized,
            intent_primary=IntentCategory.UNKNOWN,  # Placeholder
        )

        return episode_id

    def update_intent(
        self,
        primary: IntentCategory,
        secondary: Optional[IntentCategory] = None,
        confidence: float = 0.0,
        pattern_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Intent recognition sonucunu ekle.

        Args:
            primary: Primary intent
            secondary: Secondary intent (compound)
            confidence: Intent confidence score
            pattern_ids: Matched pattern IDs
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        self.current_episode.intent_primary = primary
        self.current_episode.intent_secondary = secondary
        self.current_episode.intent_confidence = confidence
        self.current_episode.intent_matched_pattern_ids = pattern_ids or []

    def update_context(self, context_manager: Optional[ContextManager]) -> None:
        """
        Context snapshot'ı al ve ekle.

        Args:
            context_manager: ContextManager instance (None ise skip)
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        if not context_manager:
            return

        context = context_manager.get_context()

        self.current_episode.context_turn_count = context.turn_count
        self.current_episode.context_last_user_intent = context.last_user_intent
        self.current_episode.context_last_assistant_act = context.last_assistant_act
        self.current_episode.context_sentiment = context.user_sentiment
        # Use numeric sentiment_trend from context (not string from get_sentiment_trend())
        self.current_episode.context_sentiment_trend = context.sentiment_trend
        self.current_episode.context_topic = context.current_topic
        self.current_episode.context_is_followup = context.is_followup

    def update_decision(
        self,
        act_selected: DialogueAct,
        act_score: float = 0.0,
        alternatives: Optional[List[Tuple[str, float]]] = None,
    ) -> None:
        """
        Act selection sonucunu ekle.

        Args:
            act_selected: Selected dialogue act
            act_score: Selection score
            alternatives: Alternative acts with scores [(act, score)]
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        self.current_episode.dialogue_act_selected = act_selected
        self.current_episode.dialogue_act_score = act_score
        self.current_episode.dialogue_act_alternatives = alternatives or []

    def update_construction(
        self,
        construction_id: str,
        category: str,
        source: ConstructionSource = ConstructionSource.HUMAN_DEFAULT,
        level: ConstructionLevel = ConstructionLevel.SURFACE,
    ) -> None:
        """
        Construction bilgisini ekle.

        Args:
            construction_id: Construction ID
            category: Construction category (MVCSCategory value)
            source: Construction source (HUMAN_DEFAULT, LEARNED, ADAPTED)
            level: Construction level (SURFACE, MIDDLE, DEEP)
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        self.current_episode.construction_id = construction_id
        self.current_episode.construction_category = category
        self.current_episode.construction_source = source
        self.current_episode.construction_level = level

    def update_output(self, response_text: str) -> None:
        """
        Output bilgisini ekle.

        Args:
            response_text: Generated response
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        self.current_episode.response_text = response_text
        self.current_episode.response_length_chars = len(response_text)
        self.current_episode.response_length_words = len(response_text.split())

    def update_risk(
        self,
        risk_level: RiskLevel = RiskLevel.LOW,
        risk_score: float = 0.0,
        approval_status: ApprovalStatus = ApprovalStatus.NOT_CHECKED,
        approval_reasons: Optional[List[str]] = None,
    ) -> None:
        """
        Risk & approval bilgisini ekle.

        Args:
            risk_level: Risk level
            risk_score: Risk score
            approval_status: Approval status
            approval_reasons: Approval/rejection reasons
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        self.current_episode.risk_level = risk_level
        self.current_episode.risk_score = risk_score
        self.current_episode.approval_status = approval_status
        self.current_episode.approval_reasons = approval_reasons or []

    def finalize_episode(self, processing_time_ms: int = 0) -> EpisodeLog:
        """
        Episode'u tamamla ve store'a kaydet.

        Args:
            processing_time_ms: Total processing time in milliseconds

        Returns:
            EpisodeLog: Finalized episode

        Raises:
            ValueError: If no current episode
        """
        if not self.current_episode:
            raise ValueError("No current episode. Call start_episode() first.")

        self.current_episode.processing_time_ms = processing_time_ms

        # Store'a kaydet
        self.store.save(self.current_episode)

        # Reference'ı sakla ve temizle
        finalized = self.current_episode
        self.current_episode = None

        return finalized

    def add_feedback(
        self,
        episode_id: str,
        explicit: Optional[float] = None,
        implicit: Optional[ImplicitFeedback] = None,
        trust_before: Optional[float] = None,
        trust_after: Optional[float] = None,
    ) -> bool:
        """
        Sonradan episode'a feedback ekle.

        NOT: Bu Faz 5'te kullanılmayacak, Faz 6+ için hazırlık.
        Şimdilik episode'u store'dan oku, güncelle, tekrar kaydet yöntemi yok.
        Future: Update operation eklenecek.

        Args:
            episode_id: Episode ID
            explicit: Explicit feedback score (-1.0 to 1.0)
            implicit: Implicit feedback signals
            trust_before: Trust level before
            trust_after: Trust level after

        Returns:
            bool: Success status
        """
        # Future work için placeholder
        # Store'a update metodları eklendiğinde implement edilecek
        return False

    def get_session_episodes(self) -> List[EpisodeLog]:
        """
        Current session'ın tüm episode'larını getir.

        Returns:
            List[EpisodeLog]: Session episodes (zamana göre sıralı)
        """
        return self.store.get_by_session(self.session_id)

    def reset_turn_number(self) -> None:
        """Turn number'ı sıfırla (yeni session için)."""
        self.turn_number = 0
