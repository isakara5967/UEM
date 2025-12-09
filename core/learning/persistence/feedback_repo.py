"""
core/learning/persistence/feedback_repo.py

Repository for Feedback PostgreSQL persistence.

Provides CRUD operations for learning feedbacks.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
import logging

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from core.memory.persistence.models import FeedbackModel
from core.learning.types import Feedback, FeedbackType

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """
    Repository for feedback persistence operations.

    Usage:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)

        repo = FeedbackRepository(Session)

        # Save feedback
        feedback = Feedback(id="fb_123", ...)
        repo.save(feedback)

        # Get by interaction
        feedbacks = repo.get_by_interaction("int_123")
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize feedback repository.

        Args:
            session_factory: Callable that returns SQLAlchemy Session
        """
        self.session_factory = session_factory

    def save(self, feedback: Feedback) -> str:
        """
        Save feedback.

        Args:
            feedback: Feedback entity to save

        Returns:
            Feedback ID
        """
        session = self.session_factory()
        try:
            model = self._to_model(feedback)
            session.add(model)
            session.commit()
            logger.debug(f"Feedback saved: {feedback.id}")
            return feedback.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving feedback: {e}")
            raise
        finally:
            session.close()

    def get(self, feedback_id: str) -> Optional[Feedback]:
        """
        Get feedback by ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            Feedback entity or None
        """
        session = self.session_factory()
        try:
            model = session.query(FeedbackModel).filter(
                FeedbackModel.id == feedback_id
            ).first()

            if model:
                return self._to_entity(model)
            return None
        finally:
            session.close()

    def get_by_interaction(self, interaction_id: str) -> List[Feedback]:
        """
        Get feedbacks by interaction ID.

        Args:
            interaction_id: Interaction ID

        Returns:
            List of Feedback entities
        """
        session = self.session_factory()
        try:
            models = session.query(FeedbackModel).filter(
                FeedbackModel.interaction_id == interaction_id
            ).order_by(
                desc(FeedbackModel.timestamp)
            ).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def get_by_user(self, user_id: str) -> List[Feedback]:
        """
        Get feedbacks by user ID.

        Args:
            user_id: User ID

        Returns:
            List of Feedback entities
        """
        session = self.session_factory()
        try:
            models = session.query(FeedbackModel).filter(
                FeedbackModel.user_id == user_id
            ).order_by(
                desc(FeedbackModel.timestamp)
            ).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def get_recent(self, limit: int = 100) -> List[Feedback]:
        """
        Get recent feedbacks.

        Args:
            limit: Maximum number of feedbacks

        Returns:
            List of Feedback entities
        """
        session = self.session_factory()
        try:
            models = session.query(FeedbackModel).order_by(
                desc(FeedbackModel.timestamp)
            ).limit(limit).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def get_all(self) -> List[Feedback]:
        """
        Get all feedbacks.

        Returns:
            List of Feedback entities
        """
        session = self.session_factory()
        try:
            models = session.query(FeedbackModel).order_by(
                desc(FeedbackModel.timestamp)
            ).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def delete(self, feedback_id: str) -> bool:
        """
        Delete feedback by ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            True if deleted, False if not found
        """
        session = self.session_factory()
        try:
            result = session.query(FeedbackModel).filter(
                FeedbackModel.id == feedback_id
            ).delete()

            session.commit()

            if result > 0:
                logger.debug(f"Feedback deleted: {feedback_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting feedback: {e}")
            raise
        finally:
            session.close()

    def count(self) -> int:
        """
        Get total feedback count.

        Returns:
            Number of feedbacks
        """
        session = self.session_factory()
        try:
            return session.query(FeedbackModel).count()
        finally:
            session.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Returns:
            Statistics dict
        """
        session = self.session_factory()
        try:
            total = session.query(FeedbackModel).count()

            if total == 0:
                return {
                    "total_feedback": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "explicit_count": 0,
                    "implicit_count": 0,
                    "average_score": 0.0,
                    "unique_users": 0,
                    "unique_interactions": 0
                }

            # Count by value
            positive = session.query(FeedbackModel).filter(
                FeedbackModel.value > 0.3
            ).count()
            negative = session.query(FeedbackModel).filter(
                FeedbackModel.value < -0.3
            ).count()
            neutral = total - positive - negative

            # Count by type
            explicit = session.query(FeedbackModel).filter(
                FeedbackModel.feedback_type == FeedbackType.EXPLICIT.value
            ).count()
            implicit = session.query(FeedbackModel).filter(
                FeedbackModel.feedback_type == FeedbackType.IMPLICIT.value
            ).count()

            # Average score
            avg_score = session.query(func.avg(FeedbackModel.value)).scalar() or 0.0

            # Unique users
            unique_users = session.query(
                func.count(func.distinct(FeedbackModel.user_id))
            ).filter(
                FeedbackModel.user_id.isnot(None)
            ).scalar() or 0

            # Unique interactions
            unique_interactions = session.query(
                func.count(func.distinct(FeedbackModel.interaction_id))
            ).scalar() or 0

            return {
                "total_feedback": total,
                "positive_count": positive,
                "negative_count": negative,
                "neutral_count": neutral,
                "explicit_count": explicit,
                "implicit_count": implicit,
                "average_score": float(avg_score),
                "unique_users": unique_users,
                "unique_interactions": unique_interactions
            }
        finally:
            session.close()

    def get_average_score(self, user_id: Optional[str] = None) -> float:
        """
        Get average feedback score.

        Args:
            user_id: Optional user ID filter

        Returns:
            Average score
        """
        session = self.session_factory()
        try:
            query = session.query(func.avg(FeedbackModel.value))

            if user_id:
                query = query.filter(FeedbackModel.user_id == user_id)

            result = query.scalar()
            return float(result) if result else 0.0
        finally:
            session.close()

    def clear(self) -> int:
        """
        Delete all feedbacks.

        Returns:
            Number of deleted feedbacks
        """
        session = self.session_factory()
        try:
            count = session.query(FeedbackModel).delete()
            session.commit()
            logger.info(f"Cleared {count} feedbacks")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing feedbacks: {e}")
            raise
        finally:
            session.close()

    def _to_model(self, feedback: Feedback) -> FeedbackModel:
        """
        Convert Feedback entity to FeedbackModel.

        Args:
            feedback: Feedback entity

        Returns:
            FeedbackModel instance
        """
        return FeedbackModel(
            id=feedback.id,
            interaction_id=feedback.interaction_id,
            feedback_type=feedback.feedback_type.value,
            value=feedback.value,
            timestamp=feedback.timestamp,
            user_id=feedback.user_id,
            context=feedback.context,
            reason=feedback.reason
        )

    def _to_entity(self, model: FeedbackModel) -> Feedback:
        """
        Convert FeedbackModel to Feedback entity.

        Args:
            model: FeedbackModel instance

        Returns:
            Feedback entity
        """
        return Feedback(
            id=model.id,
            interaction_id=model.interaction_id,
            feedback_type=FeedbackType(model.feedback_type),
            value=model.value,
            timestamp=model.timestamp or datetime.now(),
            user_id=model.user_id,
            context=model.context,
            reason=model.reason
        )
