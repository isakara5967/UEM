"""
core/learning/persistence/pattern_repo.py

Repository for Pattern PostgreSQL persistence.

Provides CRUD operations for learning patterns.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
import logging

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from core.memory.persistence.models import PatternModel
from core.learning.types import Pattern, PatternType

logger = logging.getLogger(__name__)


class PatternRepository:
    """
    Repository for pattern persistence operations.

    Usage:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)

        repo = PatternRepository(Session)

        # Save pattern
        pattern = Pattern(id="pat_123", ...)
        repo.save(pattern)

        # Get pattern
        pattern = repo.get("pat_123")

        # Get all patterns
        patterns = repo.get_all()
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize pattern repository.

        Args:
            session_factory: Callable that returns SQLAlchemy Session
        """
        self.session_factory = session_factory

    def save(self, pattern: Pattern) -> str:
        """
        Save or update pattern.

        Args:
            pattern: Pattern entity to save

        Returns:
            Pattern ID
        """
        session = self.session_factory()
        try:
            model = self._to_model(pattern)

            # Check if exists
            existing = session.query(PatternModel).filter(
                PatternModel.id == pattern.id
            ).first()

            if existing:
                # Update existing
                existing.pattern_type = model.pattern_type
                existing.content = model.content
                existing.embedding = model.embedding
                existing.success_count = model.success_count
                existing.failure_count = model.failure_count
                existing.total_reward = model.total_reward
                existing.last_used = model.last_used
                existing.extra_data = model.extra_data
            else:
                # Insert new
                session.add(model)

            session.commit()
            logger.debug(f"Pattern saved: {pattern.id}")
            return pattern.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving pattern: {e}")
            raise
        finally:
            session.close()

    def get(self, pattern_id: str) -> Optional[Pattern]:
        """
        Get pattern by ID.

        Args:
            pattern_id: Pattern ID

        Returns:
            Pattern entity or None
        """
        session = self.session_factory()
        try:
            model = session.query(PatternModel).filter(
                PatternModel.id == pattern_id
            ).first()

            if model:
                return self._to_entity(model)
            return None
        finally:
            session.close()

    def get_all(self) -> List[Pattern]:
        """
        Get all patterns.

        Returns:
            List of Pattern entities
        """
        session = self.session_factory()
        try:
            models = session.query(PatternModel).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def update(self, pattern: Pattern) -> bool:
        """
        Update existing pattern.

        Args:
            pattern: Pattern entity to update

        Returns:
            True if updated, False if not found
        """
        session = self.session_factory()
        try:
            existing = session.query(PatternModel).filter(
                PatternModel.id == pattern.id
            ).first()

            if not existing:
                return False

            existing.pattern_type = pattern.pattern_type.value
            existing.content = pattern.content
            existing.embedding = pattern.embedding
            existing.success_count = pattern.success_count
            existing.failure_count = pattern.failure_count
            existing.total_reward = pattern.total_reward
            existing.last_used = pattern.last_used
            existing.extra_data = pattern.extra_data

            session.commit()
            logger.debug(f"Pattern updated: {pattern.id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating pattern: {e}")
            raise
        finally:
            session.close()

    def delete(self, pattern_id: str) -> bool:
        """
        Delete pattern by ID.

        Args:
            pattern_id: Pattern ID

        Returns:
            True if deleted, False if not found
        """
        session = self.session_factory()
        try:
            result = session.query(PatternModel).filter(
                PatternModel.id == pattern_id
            ).delete()

            session.commit()

            if result > 0:
                logger.debug(f"Pattern deleted: {pattern_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting pattern: {e}")
            raise
        finally:
            session.close()

    def find_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """
        Find patterns by type.

        Args:
            pattern_type: Pattern type to filter

        Returns:
            List of Pattern entities
        """
        session = self.session_factory()
        try:
            models = session.query(PatternModel).filter(
                PatternModel.pattern_type == pattern_type.value
            ).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def get_top_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        k: int = 10
    ) -> List[Pattern]:
        """
        Get top patterns by success count.

        Args:
            pattern_type: Optional type filter
            k: Number of patterns to return

        Returns:
            List of Pattern entities sorted by success
        """
        session = self.session_factory()
        try:
            query = session.query(PatternModel)

            if pattern_type:
                query = query.filter(
                    PatternModel.pattern_type == pattern_type.value
                )

            models = query.order_by(
                desc(PatternModel.success_count)
            ).limit(k).all()

            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def count(self) -> int:
        """
        Get total pattern count.

        Returns:
            Number of patterns
        """
        session = self.session_factory()
        try:
            return session.query(PatternModel).count()
        finally:
            session.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pattern statistics.

        Returns:
            Statistics dict
        """
        session = self.session_factory()
        try:
            total = session.query(PatternModel).count()

            if total == 0:
                return {
                    "total_patterns": 0,
                    "by_type": {},
                    "total_uses": 0,
                    "average_success_rate": 0.0
                }

            # Count by type
            by_type = {}
            for ptype in PatternType:
                count = session.query(PatternModel).filter(
                    PatternModel.pattern_type == ptype.value
                ).count()
                if count > 0:
                    by_type[ptype.value] = count

            # Total uses
            total_uses = session.query(
                func.sum(PatternModel.success_count + PatternModel.failure_count)
            ).scalar() or 0

            # Average success rate (for patterns with uses)
            used_patterns = session.query(PatternModel).filter(
                (PatternModel.success_count + PatternModel.failure_count) > 0
            ).all()

            if used_patterns:
                rates = []
                for p in used_patterns:
                    total_p = p.success_count + p.failure_count
                    rates.append(p.success_count / total_p if total_p > 0 else 0)
                avg_success = sum(rates) / len(rates)
            else:
                avg_success = 0.0

            return {
                "total_patterns": total,
                "by_type": by_type,
                "total_uses": total_uses,
                "average_success_rate": avg_success
            }
        finally:
            session.close()

    def clear(self) -> int:
        """
        Delete all patterns.

        Returns:
            Number of deleted patterns
        """
        session = self.session_factory()
        try:
            count = session.query(PatternModel).delete()
            session.commit()
            logger.info(f"Cleared {count} patterns")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing patterns: {e}")
            raise
        finally:
            session.close()

    def _to_model(self, pattern: Pattern) -> PatternModel:
        """
        Convert Pattern entity to PatternModel.

        Args:
            pattern: Pattern entity

        Returns:
            PatternModel instance
        """
        return PatternModel(
            id=pattern.id,
            pattern_type=pattern.pattern_type.value,
            content=pattern.content,
            embedding=pattern.embedding,
            success_count=pattern.success_count,
            failure_count=pattern.failure_count,
            total_reward=pattern.total_reward,
            created_at=pattern.created_at,
            last_used=pattern.last_used,
            extra_data=pattern.extra_data or {}
        )

    def _to_entity(self, model: PatternModel) -> Pattern:
        """
        Convert PatternModel to Pattern entity.

        Args:
            model: PatternModel instance

        Returns:
            Pattern entity
        """
        return Pattern(
            id=model.id,
            pattern_type=PatternType(model.pattern_type),
            content=model.content,
            embedding=model.embedding,
            success_count=model.success_count,
            failure_count=model.failure_count,
            total_reward=model.total_reward,
            created_at=model.created_at or datetime.now(),
            last_used=model.last_used,
            extra_data=model.extra_data or {}
        )
