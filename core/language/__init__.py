"""
core/language/__init__.py

UEM v2 Language Module - LLM entegrasyonu ve Thought-to-Speech Pipeline.

Components:
- Context: Context building for LLM prompts
- LLM Adapter: LLM provider abstraction
- Chat Agent: Main conversation agent
- Dialogue: DialogueAct, MessagePlan, SituationModel (Faz 4)
- Risk: RiskLevel, RiskAssessment (Faz 4)
- Construction: Construction Grammar (Faz 4)

Kullanim:
    from core.language import UEMChatAgent, ChatConfig

    agent = UEMChatAgent()
    session_id = agent.start_session("user_123")
    response = agent.chat("Merhaba!")
    print(response.content)
    agent.end_session()

    # Faz 4 - Dialogue types
    from core.language.dialogue import DialogueAct, MessagePlan, SituationModel
    from core.language.risk import RiskLevel, RiskAssessment
    from core.language.construction import Construction, ConstructionLevel
"""

from .context import (
    ContextBuilder,
    ContextConfig,
    ContextSection,
    get_context_builder,
    create_context_builder,
    reset_context_builder,
)

from .llm_adapter import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMAdapter,
    MockLLMAdapter,
    AnthropicAdapter,
    OpenAIAdapter,
    create_adapter,
    get_llm_adapter,
    reset_llm_adapter,
)

from .chat_agent import (
    ChatConfig,
    ChatResponse,
    UEMChatAgent,
    get_chat_agent,
    create_chat_agent,
    reset_chat_agent,
)

# Faz 4 - Dialogue types
from .dialogue import (
    DialogueAct,
    ToneType,
    Actor,
    Intention,
    Risk,
    Relationship,
    TemporalContext,
    EmotionalState,
    SituationModel,
    MessagePlan,
    generate_situation_id,
    generate_message_plan_id,
)

# Faz 4 - Risk types
from .risk import (
    RiskLevel,
    RiskCategory,
    RiskFactor,
    RiskAssessment,
    generate_risk_assessment_id,
)

# Faz 4 - Construction types
from .construction import (
    ConstructionLevel,
    SlotType,
    Slot,
    MorphologyRule,
    ConstructionForm,
    ConstructionMeaning,
    Construction,
    generate_construction_id,
    generate_slot_id,
)

__all__ = [
    # Context
    "ContextBuilder",
    "ContextConfig",
    "ContextSection",
    "get_context_builder",
    "create_context_builder",
    "reset_context_builder",

    # LLM
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMAdapter",
    "MockLLMAdapter",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "create_adapter",
    "get_llm_adapter",
    "reset_llm_adapter",

    # Chat Agent
    "ChatConfig",
    "ChatResponse",
    "UEMChatAgent",
    "get_chat_agent",
    "create_chat_agent",
    "reset_chat_agent",

    # Faz 4 - Dialogue
    "DialogueAct",
    "ToneType",
    "Actor",
    "Intention",
    "Risk",
    "Relationship",
    "TemporalContext",
    "EmotionalState",
    "SituationModel",
    "MessagePlan",
    "generate_situation_id",
    "generate_message_plan_id",

    # Faz 4 - Risk
    "RiskLevel",
    "RiskCategory",
    "RiskFactor",
    "RiskAssessment",
    "generate_risk_assessment_id",

    # Faz 4 - Construction
    "ConstructionLevel",
    "SlotType",
    "Slot",
    "MorphologyRule",
    "ConstructionForm",
    "ConstructionMeaning",
    "Construction",
    "generate_construction_id",
    "generate_slot_id",
]
