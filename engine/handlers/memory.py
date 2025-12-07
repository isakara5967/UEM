"""
UEM v2 - Memory Phase Handlers

Cognitive Cycle'ın RETRIEVE fazı için handler.
Memory modülünden ilgili anıları, ilişkileri ve bilgileri getirir.

Kullanım:
    from engine.handlers.memory import create_retrieve_handler, RetrievePhaseConfig

    cycle = CognitiveCycle()
    cycle.register_handler(Phase.RETRIEVE, create_retrieve_handler())
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging
import time

import sys
sys.path.insert(0, '.')

from foundation.state import StateVector, SVField
from foundation.types import Context
from engine.phases import Phase, PhaseResult

from core.memory import (
    get_memory_store,
    MemoryStore,
    MemoryQuery,
    MemoryType,
    RetrievalResult,
    Episode,
    RelationshipRecord,
    WorkingMemoryItem,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievePhaseConfig:
    """RETRIEVE fazı yapılandırması."""

    # Hangi memory türlerini sorgula
    query_episodic: bool = True
    query_relationships: bool = True
    query_semantic: bool = True
    query_emotional: bool = True

    # Retrieval parametreleri
    max_results: int = 10
    min_importance: float = 0.1
    recency_weight: float = 0.3     # Güncel anılar daha önemli
    relevance_weight: float = 0.7   # Alakalı anılar daha önemli

    # Working memory
    load_to_working_memory: bool = True
    working_memory_limit: int = 5


@dataclass
class RetrieveHandlerState:
    """Handler durumu."""
    last_retrieval: Optional[RetrievalResult] = None
    retrieve_count: int = 0
    total_time_ms: float = 0.0


class RetrievePhaseHandler:
    """
    RETRIEVE fazı - bellek getirme.

    Context'teki bilgilere göre ilgili anıları, ilişkileri,
    ve bilgileri memory'den getirir.

    Akış:
    1. Context'ten algılanan agent'ları al
    2. Her agent için relationship bilgisi getir
    3. Mevcut duruma benzer episode'ları getir
    4. Agent'larla geçmiş etkileşimleri getir
    5. Sonuçları context ve StateVector'a yaz
    6. Working memory'ye yükle
    """

    def __init__(self, config: Optional[RetrievePhaseConfig] = None):
        self.config = config or RetrievePhaseConfig()
        self._memory = get_memory_store()
        self._state = RetrieveHandlerState()

    def __call__(
        self,
        phase: Phase,
        state: StateVector,
        context: Context,
    ) -> PhaseResult:
        """RETRIEVE fazını çalıştır."""
        start = time.perf_counter()

        try:
            # Context'ten bilgileri al
            agents = self._get_agents_from_context(context)
            current_situation = context.metadata.get("situation", "")

            retrieved_items: List[Dict[str, Any]] = []

            # 1. Algılanan agent'lar için relationship bilgisi getir
            if self.config.query_relationships and agents:
                relationship_items = self._retrieve_relationships(agents, context)
                retrieved_items.extend(relationship_items)

            # 2. Benzer durumları getir
            if self.config.query_episodic and current_situation:
                similar_items = self._retrieve_similar_episodes(current_situation)
                retrieved_items.extend(similar_items)

            # 3. Agent'larla geçmiş olayları getir
            if self.config.query_episodic and agents:
                past_items = self._retrieve_past_episodes(agents)
                retrieved_items.extend(past_items)

            # Context'e sonuçları ekle
            context.metadata["retrieved_memories"] = retrieved_items
            context.metadata["memory_retrieval_count"] = len(retrieved_items)

            # Working memory'ye yükle
            if self.config.load_to_working_memory and retrieved_items:
                self._load_to_working_memory(retrieved_items)

            # StateVector'a yaz
            self._update_state_vector(state, retrieved_items, agents)

            # İstatistikleri güncelle
            duration = (time.perf_counter() - start) * 1000
            self._state.retrieve_count += 1
            self._state.total_time_ms += duration

            return PhaseResult(
                phase=phase,
                success=True,
                duration_ms=duration,
                output={
                    "retrieved_count": len(retrieved_items),
                    "types": list(set(item["type"] for item in retrieved_items)),
                    "agents_processed": len(agents),
                },
            )

        except Exception as e:
            logger.error(f"RETRIEVE phase error: {e}")
            return PhaseResult(
                phase=phase,
                success=False,
                duration_ms=(time.perf_counter() - start) * 1000,
                error=str(e),
            )

    def _get_agents_from_context(self, context: Context) -> List[Dict[str, Any]]:
        """Context'ten agent listesi çıkar."""
        agents = []

        # "perceived_agents" listesi (PERCEIVE fazından)
        perceived = context.metadata.get("perceived_agents", [])
        for agent in perceived:
            if isinstance(agent, dict):
                agents.append(agent)
            elif hasattr(agent, "agent_id"):
                agents.append({"agent_id": agent.agent_id})

        # Stimulus'tan entity
        stimulus = context.metadata.get("stimulus")
        if stimulus and hasattr(stimulus, "source"):
            source = stimulus.source
            if hasattr(source, "entity_id"):
                agents.append({"agent_id": source.entity_id})

        return agents

    def _retrieve_relationships(
        self,
        agents: List[Dict[str, Any]],
        context: Context,
    ) -> List[Dict[str, Any]]:
        """Agent'lar için relationship bilgisi getir."""
        items = []

        for agent in agents:
            agent_id = agent.get("agent_id")
            if not agent_id:
                continue

            relationship = self._memory.get_relationship(agent_id)

            items.append({
                "type": "relationship",
                "agent_id": agent_id,
                "relationship_type": relationship.relationship_type.value,
                "trust_score": relationship.trust_score,
                "total_interactions": relationship.total_interactions,
                "sentiment": relationship.overall_sentiment,
                "is_known": relationship.total_interactions > 0,
                "positive_ratio": (
                    relationship.positive_interactions / relationship.total_interactions
                    if relationship.total_interactions > 0 else 0.5
                ),
                "betrayal_count": relationship.betrayal_count,
            })

            # Trust modülüne başlangıç bilgisi ver
            context.metadata[f"memory_trust_{agent_id}"] = relationship.get_trust_recommendation()

        return items

    def _retrieve_similar_episodes(self, situation: str) -> List[Dict[str, Any]]:
        """Benzer durumları getir."""
        items = []

        similar_episodes = self._memory.recall_similar_episodes(
            situation,
            limit=3,
        )

        for episode in similar_episodes:
            items.append({
                "type": "similar_episode",
                "episode_id": episode.id,
                "what": episode.what,
                "outcome": episode.outcome,
                "outcome_valence": episode.outcome_valence,
                "who": episode.who,
                "importance": episode.importance,
                "emotional_valence": episode.emotional_valence,
            })

        return items

    def _retrieve_past_episodes(
        self,
        agents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Agent'larla geçmiş olayları getir."""
        items = []
        seen_episodes = set()

        for agent in agents:
            agent_id = agent.get("agent_id")
            if not agent_id:
                continue

            past_episodes = self._memory.recall_episodes(
                agent_id=agent_id,
                limit=3,
            )

            for episode in past_episodes:
                # Duplicate kontrolü
                if episode.id in seen_episodes:
                    continue
                seen_episodes.add(episode.id)

                items.append({
                    "type": "past_episode",
                    "agent_id": agent_id,
                    "episode_id": episode.id,
                    "what": episode.what,
                    "outcome": episode.outcome,
                    "outcome_valence": episode.outcome_valence,
                    "importance": episode.importance,
                    "self_emotion": episode.self_emotion_during,
                })

        return items

    def _load_to_working_memory(self, items: List[Dict[str, Any]]) -> None:
        """Retrieved items'ı working memory'ye yükle."""
        # En önemli N tanesini al
        sorted_items = sorted(
            items,
            key=lambda x: (
                x.get("trust_score", 0) +
                abs(x.get("outcome_valence", 0)) +
                x.get("importance", 0)
            ),
            reverse=True,
        )[:self.config.working_memory_limit]

        for item in sorted_items:
            wm_item = WorkingMemoryItem(
                content=item,
                source="retrieval",
                priority=0.6,
                importance=item.get("importance", 0.5),
            )
            self._memory.hold_in_working(wm_item)

    def _update_state_vector(
        self,
        state: StateVector,
        items: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
    ) -> None:
        """StateVector'ı güncelle."""
        # Memory load (0-1)
        memory_load = min(1.0, len(items) / 10)
        state.set(SVField.MEMORY_LOAD, memory_load)

        # Known agent flag
        has_known_agent = any(
            item.get("is_known", False)
            for item in items
            if item.get("type") == "relationship"
        )
        state.set(SVField.KNOWN_AGENT, 1.0 if has_known_agent else 0.0)

        # Relationship quality (ortalama sentiment)
        relationship_items = [
            item for item in items
            if item.get("type") == "relationship"
        ]
        if relationship_items:
            avg_sentiment = sum(
                item.get("sentiment", 0) for item in relationship_items
            ) / len(relationship_items)
            # -1 to 1 -> 0 to 1
            relationship_quality = (avg_sentiment + 1) / 2
            state.set(SVField.RELATIONSHIP_QUALITY, relationship_quality)

        # Memory relevance (benzer episode varsa)
        similar_items = [
            item for item in items
            if item.get("type") == "similar_episode"
        ]
        if similar_items:
            state.set(SVField.MEMORY_RELEVANCE, min(1.0, len(similar_items) / 3))
        else:
            state.set(SVField.MEMORY_RELEVANCE, 0.0)

    @property
    def stats(self) -> Dict[str, Any]:
        """Handler istatistikleri."""
        return {
            "retrieve_count": self._state.retrieve_count,
            "total_time_ms": self._state.total_time_ms,
            "avg_time_ms": (
                self._state.total_time_ms / self._state.retrieve_count
                if self._state.retrieve_count > 0 else 0
            ),
        }


def create_retrieve_handler(
    config: Optional[RetrievePhaseConfig] = None,
) -> RetrievePhaseHandler:
    """RETRIEVE handler oluştur."""
    return RetrievePhaseHandler(config)
