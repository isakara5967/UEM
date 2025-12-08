"""
core/language/context.py

Context Builder - Memory ve State'i LLM context'ine donusturur.
UEM v2 - Token limitli, priority bazli context olusturma.

Ozellikler:
- Section bazli context building
- Token sayimi ve truncation
- Priority siralama (dusuk = onemli)
- Conversation, memory, state entegrasyonu
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """Context builder yapilandirmasi."""

    max_tokens: int = 4000                    # Maksimum token limiti
    recent_turns_count: int = 10              # Son N diyalog turu
    relevant_memories_count: int = 5          # Ilgili ani sayisi
    include_self_state: bool = True           # Self state dahil et
    include_relationship: bool = True         # Iliski bilgisi dahil et
    include_system_prompt: bool = True        # System prompt dahil et


@dataclass
class ContextSection:
    """Context bolumu."""

    name: str
    content: str
    priority: int       # Dusuk = daha onemli, once eklenir
    token_count: int


class ContextBuilder:
    """
    Context Builder - Memory + State -> LLM Context.

    Memory sistemi ve agent state'ini LLM icin context'e donusturur.
    Token limitlerine uyar, priority'ye gore sectionlari siralar.

    Kullanim:
        builder = ContextBuilder()

        context = builder.build(
            user_message="Merhaba, nasilsin?",
            conversation=conversation,
            relevant_memories=memories,
            self_state={"mood": "happy"},
            personality="Yardimci ve arkadas canli"
        )
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        """
        Initialize ContextBuilder.

        Args:
            config: Context yapilandirmasi
        """
        self.config = config or ContextConfig()

        # Stats
        self._stats = {
            "total_builds": 0,
            "total_sections": 0,
            "total_truncations": 0,
        }

        logger.info(
            f"ContextBuilder initialized (max_tokens={self.config.max_tokens})"
        )

    # ===================================================================
    # MAIN BUILD METHOD
    # ===================================================================

    def build(
        self,
        user_message: str,
        conversation: Optional[Any] = None,
        relevant_memories: Optional[List[Any]] = None,
        self_state: Optional[Dict[str, Any]] = None,
        relationship: Optional[Dict[str, Any]] = None,
        personality: Optional[str] = None,
    ) -> str:
        """
        Build full context for LLM.

        Args:
            user_message: Current user message
            conversation: Conversation object with turns
            relevant_memories: List of EmbeddingResult from semantic search
            self_state: Agent's internal state (mood, goals, etc.)
            relationship: Relationship info with current user
            personality: Personality description/system prompt

        Returns:
            Formatted context string ready for LLM
        """
        sections: List[ContextSection] = []

        # 1. System/Personality section (highest priority)
        if self.config.include_system_prompt and personality:
            section = self._build_system_section(personality)
            if section.content:
                sections.append(section)

        # 2. Self state section
        if self.config.include_self_state and self_state:
            section = self._build_self_section(self_state)
            if section.content:
                sections.append(section)

        # 3. Relationship section
        if self.config.include_relationship and relationship:
            section = self._build_relationship_section(relationship)
            if section.content:
                sections.append(section)

        # 4. Relevant memories section
        if relevant_memories:
            section = self._build_memory_section(relevant_memories)
            if section.content:
                sections.append(section)

        # 5. Conversation history section
        if conversation:
            section = self._build_conversation_section(
                conversation,
                max_turns=self.config.recent_turns_count,
            )
            if section.content:
                sections.append(section)

        # 6. Current user message (lowest priority number = highest importance)
        section = self._build_user_message_section(user_message)
        if section.content:
            sections.append(section)

        # Sort by priority and truncate to fit
        result = self.truncate_to_fit(sections, self.config.max_tokens)

        self._stats["total_builds"] += 1
        self._stats["total_sections"] += len(sections)

        return result

    # ===================================================================
    # SECTION BUILDERS
    # ===================================================================

    def _build_system_section(self, personality: str) -> ContextSection:
        """
        Build system/personality section.

        Args:
            personality: Personality description

        Returns:
            ContextSection with system prompt
        """
        content = f"[System]\n{personality}"
        return ContextSection(
            name="system",
            content=content,
            priority=1,  # Highest priority
            token_count=self.count_tokens(content),
        )

    def _build_self_section(self, self_state: Dict[str, Any]) -> ContextSection:
        """
        Build self state section.

        Args:
            self_state: Agent's internal state

        Returns:
            ContextSection with self state
        """
        lines = ["[Self State]"]

        # Mood / Emotional state
        if "mood" in self_state:
            lines.append(f"Mood: {self_state['mood']}")
        if "emotion" in self_state:
            lines.append(f"Emotion: {self_state['emotion']}")

        # Energy / Arousal
        if "energy" in self_state:
            lines.append(f"Energy: {self_state['energy']}")
        if "arousal" in self_state:
            lines.append(f"Arousal: {self_state['arousal']:.2f}")

        # Goals
        if "goals" in self_state:
            goals = self_state["goals"]
            if isinstance(goals, list):
                lines.append(f"Current Goals: {', '.join(goals)}")
            else:
                lines.append(f"Current Goal: {goals}")

        # Attention / Focus
        if "focus" in self_state:
            lines.append(f"Focus: {self_state['focus']}")

        # Other state values
        for key, value in self_state.items():
            if key not in ["mood", "emotion", "energy", "arousal", "goals", "focus"]:
                if isinstance(value, float):
                    lines.append(f"{key.title()}: {value:.2f}")
                else:
                    lines.append(f"{key.title()}: {value}")

        content = "\n".join(lines)
        return ContextSection(
            name="self_state",
            content=content,
            priority=2,
            token_count=self.count_tokens(content),
        )

    def _build_relationship_section(
        self,
        relationship: Dict[str, Any],
    ) -> ContextSection:
        """
        Build relationship section.

        Args:
            relationship: Relationship info with user

        Returns:
            ContextSection with relationship info
        """
        lines = ["[Relationship]"]

        # Name
        if "name" in relationship:
            lines.append(f"User: {relationship['name']}")

        # Relationship type
        if "type" in relationship:
            lines.append(f"Relationship: {relationship['type']}")

        # Trust
        if "trust_score" in relationship:
            trust = relationship["trust_score"]
            trust_level = self._trust_to_label(trust)
            lines.append(f"Trust: {trust_level} ({trust:.2f})")

        # Interaction history summary
        if "total_interactions" in relationship:
            lines.append(f"Total Interactions: {relationship['total_interactions']}")

        # Sentiment
        if "sentiment" in relationship:
            sentiment = relationship["sentiment"]
            sentiment_label = "positive" if sentiment > 0.2 else "negative" if sentiment < -0.2 else "neutral"
            lines.append(f"Overall Sentiment: {sentiment_label}")

        # Notes
        if "notes" in relationship and relationship["notes"]:
            notes = relationship["notes"]
            if isinstance(notes, list):
                lines.append(f"Notes: {'; '.join(notes[:3])}")  # Max 3 notes
            else:
                lines.append(f"Notes: {notes}")

        content = "\n".join(lines)
        return ContextSection(
            name="relationship",
            content=content,
            priority=3,
            token_count=self.count_tokens(content),
        )

    def _build_memory_section(
        self,
        memories: List[Any],
    ) -> ContextSection:
        """
        Build relevant memories section.

        Args:
            memories: List of EmbeddingResult or similar

        Returns:
            ContextSection with relevant memories
        """
        lines = ["[Relevant Memories]"]

        # Limit to configured count
        max_memories = min(len(memories), self.config.relevant_memories_count)

        for i, memory in enumerate(memories[:max_memories]):
            # Handle both EmbeddingResult and dict
            if hasattr(memory, "content"):
                content = memory.content
                similarity = getattr(memory, "similarity", 0)
                source_type = getattr(memory, "source_type", "unknown")
                if hasattr(source_type, "value"):
                    source_type = source_type.value
            elif isinstance(memory, dict):
                content = memory.get("content", "")
                similarity = memory.get("similarity", 0)
                source_type = memory.get("source_type", "unknown")
            else:
                continue

            # Truncate long memories
            if len(content) > 200:
                content = content[:197] + "..."

            lines.append(f"- [{source_type}] (relevance: {similarity:.2f}) {content}")

        content = "\n".join(lines)
        return ContextSection(
            name="memories",
            content=content,
            priority=4,
            token_count=self.count_tokens(content),
        )

    def _build_conversation_section(
        self,
        conversation: Any,
        max_turns: int,
    ) -> ContextSection:
        """
        Build conversation history section.

        Args:
            conversation: Conversation object
            max_turns: Maximum number of turns to include

        Returns:
            ContextSection with conversation history
        """
        lines = ["[Conversation History]"]

        # Get turns from conversation
        if hasattr(conversation, "turns"):
            turns = conversation.turns
        elif hasattr(conversation, "get_last_n_turns"):
            turns = conversation.get_last_n_turns(max_turns)
        elif isinstance(conversation, list):
            turns = conversation
        else:
            turns = []

        # Limit turns
        recent_turns = turns[-max_turns:] if len(turns) > max_turns else turns

        for turn in recent_turns:
            # Handle DialogueTurn or dict
            if hasattr(turn, "role"):
                role = turn.role
                content = turn.content if hasattr(turn, "content") else ""
            elif isinstance(turn, dict):
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
            else:
                continue

            role_label = "User" if role == "user" else "Agent" if role in ["agent", "assistant"] else role.title()
            lines.append(f"{role_label}: {content}")

        content = "\n".join(lines)
        return ContextSection(
            name="conversation",
            content=content,
            priority=5,
            token_count=self.count_tokens(content),
        )

    def _build_user_message_section(self, message: str) -> ContextSection:
        """
        Build current user message section.

        Args:
            message: User's current message

        Returns:
            ContextSection with user message
        """
        content = f"[Current Message]\nUser: {message}"
        return ContextSection(
            name="user_message",
            content=content,
            priority=0,  # Highest priority (always included)
            token_count=self.count_tokens(content),
        )

    # ===================================================================
    # TOKEN MANAGEMENT
    # ===================================================================

    def count_tokens(self, text: str) -> int:
        """
        Count approximate tokens in text.

        Simple estimation: words * 1.3
        For accurate counting, use tiktoken.

        Args:
            text: Input text

        Returns:
            Approximate token count
        """
        if not text:
            return 0

        # Simple word-based estimation
        words = len(text.split())
        # Turkish and special chars need more tokens
        char_factor = len(text) / max(words, 1) / 5  # Average 5 chars per word
        adjustment = max(1.0, char_factor)

        return int(words * 1.3 * adjustment)

    def truncate_to_fit(
        self,
        sections: List[ContextSection],
        max_tokens: int,
    ) -> str:
        """
        Truncate sections to fit within token limit.

        Lower priority number = higher importance (included first).

        Args:
            sections: List of context sections
            max_tokens: Maximum token limit

        Returns:
            Formatted context string within token limit
        """
        if not sections:
            return ""

        # Sort by priority (lower = more important)
        sorted_sections = sorted(sections, key=lambda s: s.priority)

        included_sections: List[ContextSection] = []
        total_tokens = 0

        for section in sorted_sections:
            if total_tokens + section.token_count <= max_tokens:
                included_sections.append(section)
                total_tokens += section.token_count
            else:
                # Try to include partial content
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 50:  # Minimum useful content
                    truncated = self._truncate_section(section, remaining_tokens)
                    if truncated.content:
                        included_sections.append(truncated)
                        self._stats["total_truncations"] += 1
                break

        return self.format_for_llm(included_sections)

    def _truncate_section(
        self,
        section: ContextSection,
        max_tokens: int,
    ) -> ContextSection:
        """
        Truncate a section to fit within token limit.

        Args:
            section: Section to truncate
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated section
        """
        lines = section.content.split("\n")
        truncated_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens <= max_tokens:
                truncated_lines.append(line)
                current_tokens += line_tokens
            else:
                # Add partial line if possible
                words = line.split()
                partial = []
                for word in words:
                    word_tokens = self.count_tokens(word)
                    if current_tokens + word_tokens <= max_tokens:
                        partial.append(word)
                        current_tokens += word_tokens
                    else:
                        break
                if partial:
                    truncated_lines.append(" ".join(partial) + "...")
                break

        content = "\n".join(truncated_lines)
        return ContextSection(
            name=section.name,
            content=content,
            priority=section.priority,
            token_count=self.count_tokens(content),
        )

    # ===================================================================
    # FORMATTING
    # ===================================================================

    def format_for_llm(self, sections: List[ContextSection]) -> str:
        """
        Format sections for LLM consumption.

        Args:
            sections: List of context sections

        Returns:
            Formatted context string
        """
        if not sections:
            return ""

        # Sort by priority for consistent output
        sorted_sections = sorted(sections, key=lambda s: s.priority)

        parts = []
        for section in sorted_sections:
            if section.content:
                parts.append(section.content)

        return "\n\n".join(parts)

    # ===================================================================
    # UTILITIES
    # ===================================================================

    def _trust_to_label(self, trust: float) -> str:
        """Convert trust score to human-readable label."""
        if trust >= 0.8:
            return "very high"
        elif trust >= 0.6:
            return "high"
        elif trust >= 0.4:
            return "moderate"
        elif trust >= 0.2:
            return "low"
        else:
            return "very low"

    @property
    def stats(self) -> Dict[str, Any]:
        """Get builder statistics."""
        return {
            **self._stats,
            "config_max_tokens": self.config.max_tokens,
            "config_recent_turns": self.config.recent_turns_count,
        }


# ========================================================================
# FACTORY & SINGLETON
# ========================================================================

_context_builder: Optional[ContextBuilder] = None


def get_context_builder(
    config: Optional[ContextConfig] = None,
) -> ContextBuilder:
    """Get context builder singleton."""
    global _context_builder

    if _context_builder is None:
        _context_builder = ContextBuilder(config)

    return _context_builder


def reset_context_builder() -> None:
    """Reset context builder singleton (test icin)."""
    global _context_builder
    _context_builder = None


def create_context_builder(
    config: Optional[ContextConfig] = None,
) -> ContextBuilder:
    """Create new context builder (test icin)."""
    return ContextBuilder(config)
