# UEM v2 Project Structure

_Auto-generated: 2025-12-11 06:11_

## Overview

| Metric | Count |
|--------|-------|
| Total Modules | 193 |
| Total Classes | 413 |
| Dataclasses | 212 |
| Enums | 85 |
| Functions | 185 |

## Directory Tree

```
core/
  __init__.py
    __init__.py
      __init__.py
        __init__.py
        dynamics.py
        emotions.py
        pad.py
        __init__.py
        __init__.py
        __init__.py
      __init__.py
        __init__.py
        channels.py
        empathy.py
        simulation.py
      orchestrator.py
        __init__.py
        calculator.py
        sympathy.py
        types.py
        __init__.py
        __init__.py
        manager.py
        trust.py
        types.py
    __init__.py
      __init__.py
      __init__.py
    planning.py
    processor.py
      __init__.py
      __init__.py
    types.py
    __init__.py
      __init__.py
      __init__.py
      __init__.py
      __init__.py
      __init__.py
    __init__.py
    chat_agent.py
      __init__.py
      grammar.py
      mvcs.py
      realizer.py
      selector.py
      types.py
    context.py
      __init__.py
      manager.py
      types.py
      __init__.py
      act_selector.py
      message_planner.py
      situation_builder.py
      types.py
      __init__.py
      patterns.py
      recognizer.py
      types.py
    llm_adapter.py
      __init__.py
      config.py
      self_critique.py
      thought_to_speech.py
      __init__.py
      approver.py
      scorer.py
      types.py
    __init__.py
    adaptation.py
    episode.py
    episode_logger.py
    episode_store.py
    episode_types.py
    feedback.py
    feedback_aggregator.py
    feedback_scorer.py
    feedback_stats.py
    feedback_store.py
    generalization.py
    mdl.py
    pattern_analyzer.py
    patterns.py
      __init__.py
      feedback_repo.py
      pattern_repo.py
    processor.py
    reinforcement.py
    similarity.py
    types.py
    __init__.py
      __init__.py
    conversation.py
    embeddings.py
      __init__.py
      __init__.py
      __init__.py
      conversation_repo.py
      models.py
      repository.py
    semantic.py
    store.py
    types.py
      __init__.py
    __init__.py
      __init__.py
    extractor.py
    filters.py
      __init__.py
    processor.py
      __init__.py
    types.py
      __init__.py
    __init__.py
      __init__.py
    goals.py
      __init__.py
      __init__.py
      __init__.py
    needs.py
    processor.py
    types.py
      __init__.py
    __init__.py
    text.py
engine/
  __init__.py
  cycle.py
    __init__.py
    bus.py
    __init__.py
    affect.py
    cognition.py
    executive.py
    memory.py
    perception.py
    __init__.py
    definitions.py
foundation/
  __init__.py
    __init__.py
    __init__.py
    __init__.py
    bridge.py
    fields.py
    vector.py
    __init__.py
    actions.py
    base.py
    results.py
infra/
  __init__.py
    __init__.py
    __init__.py
      __init__.py
    __init__.py
      __init__.py
      __init__.py
      __init__.py
interface/
  __init__.py
    __init__.py
    __init__.py
    cli.py
    __init__.py
    __init__.py
    app.py
meta/
  __init__.py
    __init__.py
    attention.py
    awareness.py
    integration.py
    processor.py
    types.py
      __init__.py
    __init__.py
    analyzers.py
    insights.py
    learning.py
    patterns.py
    processor.py
    types.py
    __init__.py
      __init__.py
      __init__.py
      collector.py
      cycle.py
    monitor.py
    persistence.py
      __init__.py
    reporter.py
scripts/
  aggregate_feedback.py
  analyze_episodes.py
  demo_dashboard.py
  demo_full_system.py
  generate_docs.py
```

## Module Details

### core/

#### `core/__init__.py`

#### `core/affect/__init__.py`

#### `core/affect/emotion/__init__.py`

#### `core/affect/emotion/core/__init__.py`

_UEM v2 - Emotion Core Module_

#### `core/affect/emotion/core/dynamics.py`

_UEM v2 - Emotion Dynamics_

**Classes:**
- `DecayModel` (enum)
- `RegulationStrategy` (enum)
- `EmotionConfig` (dataclass)
- `EmotionState` (dataclass)

**Functions:**
- `create_personality_baseline()`

#### `core/affect/emotion/core/emotions.py`

_UEM v2 - Basic Emotions_

**Classes:**
- `BasicEmotion` (enum)
- `SecondaryEmotion` (enum)
- `EmotionProfile` (dataclass)

**Functions:**
- `get_emotion_pad()`
- `get_secondary_emotion_pad()`
- `identify_emotion()`
- `identify_all_emotions()`
- `create_emotion_profile()`
- `blend_emotions()`
- `get_emotion_family()`

#### `core/affect/emotion/core/pad.py`

_UEM v2 - PAD Model_

**Classes:**
- `PADState` (dataclass)
- `PADOctant` (enum)

**Functions:**
- `get_octant()`
- `pad_from_appraisal()`
- `pad_from_stimulus()`

#### `core/affect/emotion/primitive/__init__.py`

#### `core/affect/emotion/regulation/__init__.py`

#### `core/affect/emotion/somatic/__init__.py`

#### `core/affect/social/__init__.py`

_UEM v2 - Social Affect Module_

#### `core/affect/social/empathy/__init__.py`

_UEM v2 - Empathy Module_

#### `core/affect/social/empathy/channels.py`

_UEM v2 - Empathy Channels_

**Classes:**
- `EmpathyChannel` (enum)
- `ChannelResult` (dataclass)
- `EmpathyChannels` (dataclass)

**Functions:**
- `get_context_weights()`

#### `core/affect/social/empathy/empathy.py`

_UEM v2 - Empathy Module_

**Classes:**
- `EmpathyConfig` (dataclass)
- `Empathy`

**Functions:**
- `compute_empathy_for_emotion()`
- `estimate_empathy_difficulty()`

#### `core/affect/social/empathy/simulation.py`

_UEM v2 - Empathy Simulation_

**Classes:**
- `AgentState` (dataclass)
- `SimulationConfig` (dataclass)
- `EmpathySimulator`
- `EmpathyResult` (dataclass)

#### `core/affect/social/orchestrator.py`

_UEM v2 - Social Affect Orchestrator (StateVector Integrated)_

**Classes:**
- `SocialAffectResult` (dataclass)
- `OrchestratorConfig` (dataclass)
- `SocialAffectOrchestrator`

**Functions:**
- `create_orchestrator()`
- `process_social_affect()`

#### `core/affect/social/sympathy/__init__.py`

_UEM v2 - Sympathy Module_

#### `core/affect/social/sympathy/calculator.py`

_UEM v2 - Sympathy Calculator_

**Classes:**
- `RelationshipContext` (dataclass)
- `SympathyConfig` (dataclass)
- `SympathyCalculator`
- `SympathyResult` (dataclass)

#### `core/affect/social/sympathy/sympathy.py`

_UEM v2 - Sympathy Module_

**Classes:**
- `SympathyModuleConfig` (dataclass)
- `Sympathy`

**Functions:**
- `predict_sympathy()`
- `get_sympathy_spectrum()`

#### `core/affect/social/sympathy/types.py`

_UEM v2 - Sympathy Types_

**Classes:**
- `SympathyType` (enum)
- `SympathyResponse` (dataclass)
- `SympathyTrigger` (dataclass)

**Functions:**
- `get_sympathy_pad()`
- `get_action_tendency()`
- `get_trigger()`

#### `core/affect/social/theory_of_mind/__init__.py`

#### `core/affect/social/trust/__init__.py`

_UEM v2 - Trust Module_

#### `core/affect/social/trust/manager.py`

_UEM v2 - Trust Manager_

**Classes:**
- `TrustProfile` (dataclass)
- `TrustConfig` (dataclass)
- `TrustManager`

#### `core/affect/social/trust/trust.py`

_UEM v2 - Trust Module_

**Classes:**
- `Trust`

**Functions:**
- `quick_trust_check()`
- `calculate_risk_threshold()`

#### `core/affect/social/trust/types.py`

_UEM v2 - Trust Types_

**Classes:**
- `TrustLevel` (enum)
- `TrustType` (enum)
- `TrustDimension` (enum)
- `TrustComponents` (dataclass)
- `TrustEvent` (dataclass)

**Functions:**
- `create_trust_event()`
- `determine_trust_type()`

#### `core/cognition/__init__.py`

_UEM v2 - Cognition Module_

#### `core/cognition/creativity/__init__.py`

#### `core/cognition/evaluation/__init__.py`

_UEM v2 - Evaluation Module_

**Classes:**
- `EvaluationConfig` (dataclass)
- `RiskItem` (dataclass)
- `OpportunityItem` (dataclass)
- `RiskAssessor`
- `OpportunityAssessor`
- `SituationEvaluator`

**Functions:**
- `get_situation_evaluator()`
- `create_situation_evaluator()`

#### `core/cognition/planning.py`

_UEM v2 - Planning Module_

**Classes:**
- `PlanningConfig` (dataclass)
- `ActionTemplate` (dataclass)
- `GoalManager`
- `ActionPlanner`

**Functions:**
- `get_goal_manager()`
- `get_action_planner()`
- `create_goal_manager()`
- `create_action_planner()`

#### `core/cognition/processor.py`

_UEM v2 - Cognition Processor_

**Classes:**
- `CognitionConfig` (dataclass)
- `CognitionOutput` (dataclass)
- `CognitionProcessor`

**Functions:**
- `get_cognition_processor()`
- `create_cognition_processor()`

#### `core/cognition/reasoning/__init__.py`

_UEM v2 - Reasoning Engine_

**Classes:**
- `ReasoningConfig` (dataclass)
- `InferenceRule` (dataclass)
- `ReasoningEngine`

**Functions:**
- `get_reasoning_engine()`
- `create_reasoning_engine()`

#### `core/cognition/simulation/__init__.py`

#### `core/cognition/types.py`

_UEM v2 - Cognition Types_

**Classes:**
- `BeliefType` (enum)
- `BeliefStrength` (enum)
- `GoalType` (enum)
- `GoalPriority` (enum)
- `GoalStatus` (enum)
- `IntentionStrength` (enum)
- `ReasoningType` (enum)
- `RiskLevel` (enum)
- `OpportunityLevel` (enum)
- `Belief` (dataclass)
- `Goal` (dataclass)
- `Intention` (dataclass)
- `PlanStep` (dataclass)
- `Plan` (dataclass)
- `ReasoningResult` (dataclass)
- `SituationAssessment` (dataclass)
- `CognitiveState` (dataclass)

#### `core/executive/__init__.py`

#### `core/executive/action/__init__.py`

#### `core/executive/decision/__init__.py`

#### `core/executive/goal/__init__.py`

#### `core/executive/planning/__init__.py`

#### `core/executive/strategy/__init__.py`

#### `core/language/__init__.py`

_core/language/__init__.py_

#### `core/language/chat_agent.py`

_core/language/chat_agent.py_

**Classes:**
- `ChatConfig` (dataclass)
- `ChatResponse` (dataclass)
- `UEMChatAgent`

**Functions:**
- `get_chat_agent()`
- `reset_chat_agent()`
- `create_chat_agent()`

#### `core/language/construction/__init__.py`

_core/language/construction/__init__.py_

#### `core/language/construction/grammar.py`

_core/language/construction/grammar.py_

**Classes:**
- `ConstructionGrammarConfig` (dataclass)
- `ConstructionGrammar`

#### `core/language/construction/mvcs.py`

_core/language/construction/mvcs.py_

**Classes:**
- `MVCSCategory` (enum)
- `MVCSConfig` (dataclass)
- `MVCSLoader`

#### `core/language/construction/realizer.py`

_core/language/construction/realizer.py_

**Classes:**
- `RealizationResult` (dataclass)
- `ConstructionRealizerConfig` (dataclass)
- `ConstructionRealizer`

#### `core/language/construction/selector.py`

_core/language/construction/selector.py_

**Classes:**
- `ConstructionScore` (dataclass)
- `SelectionResult` (dataclass)
- `ConstructionSelectorConfig` (dataclass)
- `ConstructionSelector`

#### `core/language/construction/types.py`

_core/language/construction/types.py_

**Classes:**
- `ConstructionLevel` (enum)
- `SlotType` (enum)
- `Slot` (dataclass)
- `MorphologyRule` (dataclass)
- `ConstructionForm` (dataclass)
- `ConstructionMeaning` (dataclass)
- `Construction` (dataclass)

**Functions:**
- `generate_construction_id()`
- `generate_deterministic_construction_id()`
- `generate_slot_id()`
- `generate_morphology_rule_id()`

#### `core/language/context.py`

_core/language/context.py_

**Classes:**
- `ContextConfig` (dataclass)
- `ContextSection` (dataclass)
- `ContextBuilder`

**Functions:**
- `get_context_builder()`
- `reset_context_builder()`
- `create_context_builder()`

#### `core/language/conversation/__init__.py`

_core/language/conversation_

#### `core/language/conversation/manager.py`

_core/language/conversation/manager.py_

**Classes:**
- `ContextManager`

#### `core/language/conversation/types.py`

_core/language/conversation/types.py_

**Classes:**
- `Message` (dataclass)
- `ConversationContext` (dataclass)
- `ContextConfig` (dataclass)

#### `core/language/dialogue/__init__.py`

_core/language/dialogue/__init__.py_

#### `core/language/dialogue/act_selector.py`

_core/language/dialogue/act_selector.py_

**Classes:**
- `SelectionStrategy` (enum)
- `ActScore` (dataclass)
- `ActSelectionResult` (dataclass)
- `ActSelectorConfig` (dataclass)
- `DialogueActSelector`

#### `core/language/dialogue/message_planner.py`

_core/language/dialogue/message_planner.py_

**Classes:**
- `ConstraintSeverity` (enum)
- `ConstraintType` (enum)
- `ContentPoint` (dataclass)
- `MessageConstraint` (dataclass)
- `MessagePlannerConfig` (dataclass)
- `MessagePlanner`

#### `core/language/dialogue/situation_builder.py`

_core/language/dialogue/situation_builder.py_

**Classes:**
- `SituationBuilderConfig` (dataclass)
- `SituationBuilder`

#### `core/language/dialogue/types.py`

_core/language/dialogue/types.py_

**Classes:**
- `DialogueAct` (enum)
- `ToneType` (enum)
- `Actor` (dataclass)
- `Intention` (dataclass)
- `Risk` (dataclass)
- `Relationship` (dataclass)
- `TemporalContext` (dataclass)
- `EmotionalState` (dataclass)
- `SituationModel` (dataclass)
- `MessagePlan` (dataclass)

**Functions:**
- `generate_situation_id()`
- `generate_message_plan_id()`

#### `core/language/intent/__init__.py`

_core/language/intent_

#### `core/language/intent/patterns.py`

_core/language/intent/patterns.py_

**Functions:**
- `get_pattern_weight()`
- `get_all_patterns()`
- `get_pattern_count()`
- `get_patterns_for_category()`
- `get_pattern_id()`
- `get_pattern_ids_for_category()`

#### `core/language/intent/recognizer.py`

_core/language/intent/recognizer.py_

**Classes:**
- `IntentRecognizerConfig` (dataclass)
- `IntentRecognizer`

#### `core/language/intent/types.py`

_core/language/intent/types.py_

**Classes:**
- `IntentCategory` (enum)
- `IntentMatch` (dataclass)
- `IntentResult` (dataclass)

#### `core/language/llm_adapter.py`

_core/language/llm_adapter.py_

**Classes:**
- `LLMProvider` (enum)
- `LLMConfig` (dataclass)
- `LLMResponse` (dataclass)
- `LLMAdapter`
- `MockLLMAdapter`
- `AnthropicAdapter`
- `OpenAIAdapter`

**Functions:**
- `create_adapter()`
- `get_llm_adapter()`
- `reset_llm_adapter()`

#### `core/language/pipeline/__init__.py`

_core/language/pipeline/__init__.py_

#### `core/language/pipeline/config.py`

_core/language/pipeline/config.py_

**Classes:**
- `SelfCritiqueConfig` (dataclass)
- `PipelineConfig` (dataclass)

#### `core/language/pipeline/self_critique.py`

_core/language/pipeline/self_critique.py_

**Classes:**
- `CritiqueResult` (dataclass)
- `SelfCritique`

#### `core/language/pipeline/thought_to_speech.py`

_core/language/pipeline/thought_to_speech.py_

**Classes:**
- `PipelineResult` (dataclass)
- `ThoughtToSpeechPipeline`

**Functions:**
- `generate_pipeline_result_id()`

#### `core/language/risk/__init__.py`

_core/language/risk/__init__.py_

#### `core/language/risk/approver.py`

_core/language/risk/approver.py_

**Classes:**
- `ApprovalDecision` (enum)
- `ApprovalResult` (dataclass)
- `InternalApproverConfig` (dataclass)
- `InternalApprover`

#### `core/language/risk/scorer.py`

_core/language/risk/scorer.py_

**Classes:**
- `RiskScorerConfig` (dataclass)
- `RiskScorer`

#### `core/language/risk/types.py`

_core/language/risk/types.py_

**Classes:**
- `RiskLevel` (enum)
- `RiskCategory` (enum)
- `RiskFactor` (dataclass)
- `RiskAssessment` (dataclass)

**Functions:**
- `generate_risk_assessment_id()`
- `generate_risk_factor_id()`

#### `core/learning/__init__.py`

_core/learning/__init__.py_

#### `core/learning/adaptation.py`

_core/learning/adaptation.py_

**Classes:**
- `AdaptationConfig` (dataclass)
- `AdaptationRecord` (dataclass)
- `BehaviorAdapter`

#### `core/learning/episode.py`

_core/learning/episode.py_

**Classes:**
- `EpisodeOutcome` (dataclass)
- `Episode` (dataclass)
- `EpisodeCollection` (dataclass)

**Functions:**
- `generate_episode_id()`

#### `core/learning/episode_logger.py`

_core/learning/episode_logger.py_

**Classes:**
- `EpisodeLogger`

#### `core/learning/episode_store.py`

_core/learning/episode_store.py_

**Classes:**
- `EpisodeStore`
- `JSONLEpisodeStore`

#### `core/learning/episode_types.py`

_core/learning/episode_types.py_

**Classes:**
- `ConstructionSource` (enum)
- `ConstructionLevel` (enum)
- `ApprovalStatus` (enum)
- `ImplicitFeedback` (dataclass)
- `EpisodeLog` (dataclass)

**Functions:**
- `generate_episode_log_id()`

#### `core/learning/feedback.py`

_core/learning/feedback.py_

**Classes:**
- `FeedbackCollector`
- `FeedbackWeighterConfig` (dataclass)
- `ImplicitSignals` (dataclass)
- `FeedbackWeighter`

#### `core/learning/feedback_aggregator.py`

_core/learning/feedback_aggregator.py_

**Classes:**
- `FeedbackAggregator`

#### `core/learning/feedback_scorer.py`

_core/learning/feedback_scorer.py_

**Functions:**
- `compute_wins_losses()`
- `compute_feedback_mean()`
- `compute_influence()`
- `compute_adjustment()`
- `compute_final_score()`
- `explain_score()`
- `is_score_significant()`
- `get_feedback_summary()`

#### `core/learning/feedback_stats.py`

_core/learning/feedback_stats.py_

**Classes:**
- `ConstructionStats` (dataclass)

#### `core/learning/feedback_store.py`

_core/learning/feedback_store.py_

**Classes:**
- `FeedbackStore`

#### `core/learning/generalization.py`

_core/learning/generalization.py_

**Classes:**
- `RuleExtractor`

#### `core/learning/mdl.py`

_core/learning/mdl.py_

**Classes:**
- `MDLConfig` (dataclass)
- `MDLScore` (dataclass)
- `ApproximateMDL`

#### `core/learning/pattern_analyzer.py`

_core/learning/pattern_analyzer.py_

**Classes:**
- `PatternAnalyzer`

**Functions:**
- `create_analyzer()`

#### `core/learning/patterns.py`

_core/learning/patterns.py_

**Classes:**
- `PatternStorage`

#### `core/learning/persistence/__init__.py`

_core/learning/persistence/__init__.py_

#### `core/learning/persistence/feedback_repo.py`

_core/learning/persistence/feedback_repo.py_

**Classes:**
- `FeedbackRepository`

#### `core/learning/persistence/pattern_repo.py`

_core/learning/persistence/pattern_repo.py_

**Classes:**
- `PatternRepository`

#### `core/learning/processor.py`

_core/learning/processor.py_

**Classes:**
- `LearningProcessor`

#### `core/learning/reinforcement.py`

_core/learning/reinforcement.py_

**Classes:**
- `RewardConfig` (dataclass)
- `RewardCalculator`
- `Reinforcer`

#### `core/learning/similarity.py`

_core/learning/similarity.py_

**Classes:**
- `SimilarityConfig` (dataclass)
- `SimilarityResult` (dataclass)
- `EpisodeSimilarity`

**Functions:**
- `jaccard_similarity()`
- `levenshtein_distance()`
- `levenshtein_similarity()`

#### `core/learning/types.py`

_core/learning/types.py_

**Classes:**
- `FeedbackType` (enum)
- `PatternType` (enum)
- `Feedback` (dataclass)
- `Pattern` (dataclass)
- `LearningOutcome` (dataclass)
- `Rule` (dataclass)

**Functions:**
- `generate_feedback_id()`
- `generate_pattern_id()`
- `generate_rule_id()`

#### `core/memory/__init__.py`

_core/memory/__init__.py_

#### `core/memory/consolidation/__init__.py`

#### `core/memory/conversation.py`

_core/memory/conversation.py_

**Classes:**
- `ConversationConfig` (dataclass)
- `ConversationMemory`

**Functions:**
- `get_conversation_memory()`
- `reset_conversation_memory()`
- `create_conversation_memory()`

#### `core/memory/embeddings.py`

_core/memory/embeddings.py_

**Classes:**
- `LRUCache`
- `EmbeddingEncoder`

**Functions:**
- `cosine_similarity()`
- `batch_cosine_similarity()`
- `top_k_indices()`
- `euclidean_distance()`
- `normalize_vector()`
- `get_embedding_encoder()`
- `reset_embedding_encoder()`
- `create_embedding_encoder()`

#### `core/memory/emotional/__init__.py`

#### `core/memory/episodic/__init__.py`

#### `core/memory/persistence/__init__.py`

_core/memory/persistence/__init__.py_

#### `core/memory/persistence/conversation_repo.py`

_core/memory/persistence/conversation_repo.py_

**Classes:**
- `ConversationRepository`

#### `core/memory/persistence/models.py`

_core/memory/persistence/models.py_

**Classes:**
- `MemoryTypeEnum` (enum)
- `RelationshipTypeEnum` (enum)
- `InteractionTypeEnum` (enum)
- `EpisodeTypeEnum` (enum)
- `EpisodeModel`
- `RelationshipModel`
- `InteractionModel`
- `SemanticFactModel`
- `EmotionalMemoryModel`
- `TrustHistoryModel`
- `CycleMetricModel`
- `ActivityLogModel`
- `ConversationModel`
- `PatternTypeEnum` (enum)
- `PatternModel`
- `FeedbackTypeEnum` (enum)
- `FeedbackModel`
- `DialogueTurnModel`

#### `core/memory/persistence/repository.py`

_core/memory/persistence/repository.py_

**Classes:**
- `MemoryRepository`

**Functions:**
- `get_database_url()`
- `get_engine()`
- `get_session()`
- `init_db()`

#### `core/memory/semantic.py`

_core/memory/semantic.py_

**Classes:**
- `IndexEntry` (dataclass)
- `SemanticMemory`

**Functions:**
- `get_semantic_memory()`
- `reset_semantic_memory()`
- `create_semantic_memory()`

#### `core/memory/store.py`

_core/memory/store.py_

**Classes:**
- `MemoryConfig` (dataclass)
- `MemoryStore`

**Functions:**
- `get_memory_store()`
- `reset_memory_store()`
- `create_memory_store()`

#### `core/memory/types.py`

_core/memory/types.py_

**Classes:**
- `MemoryType` (enum)
- `EmotionalValence` (enum)
- `RelationshipType` (enum)
- `InteractionType` (enum)
- `EpisodeType` (enum)
- `MemoryItem` (dataclass)
- `SensoryTrace` (dataclass)
- `WorkingMemoryItem` (dataclass)
- `Episode` (dataclass)
- `EpisodeSummary` (dataclass)
- `SemanticFact` (dataclass)
- `ConceptNode` (dataclass)
- `EmotionalMemory` (dataclass)
- `Interaction` (dataclass)
- `RelationshipRecord` (dataclass)
- `ConsolidationTask` (dataclass)
- `MemoryQuery` (dataclass)
- `RetrievalResult` (dataclass)
- `DialogueTurn` (dataclass)
- `Conversation` (dataclass)
- `EmbeddingModel` (enum)
- `SourceType` (enum)
- `EmbeddingConfig` (dataclass)
- `EmbeddingResult` (dataclass)

#### `core/memory/working/__init__.py`

#### `core/perception/__init__.py`

_core/perception/__init__.py_

#### `core/perception/attention/__init__.py`

#### `core/perception/extractor.py`

_core/perception/extractor.py_

**Classes:**
- `ExtractorConfig` (dataclass)
- `VisualFeatureExtractor`
- `AuditoryFeatureExtractor`
- `MotionFeatureExtractor`
- `AgentExtractor`
- `ThreatExtractor`
- `FeatureExtractor`

#### `core/perception/filters.py`

_core/perception/filters.py_

**Classes:**
- `FilterConfig` (dataclass)
- `AttentionFilter`
- `NoiseFilter`
- `SalienceFilter`
- `PerceptionFilterPipeline`

#### `core/perception/fusion/__init__.py`

#### `core/perception/processor.py`

_core/perception/processor.py_

**Classes:**
- `ProcessorConfig` (dataclass)
- `PerceptionProcessor`

**Functions:**
- `get_perception_processor()`
- `reset_perception_processor()`

#### `core/perception/sensory/__init__.py`

#### `core/perception/types.py`

_core/perception/types.py_

**Classes:**
- `SensoryModality` (enum)
- `PerceptualCategory` (enum)
- `ThreatLevel` (enum)
- `AgentDisposition` (enum)
- `EmotionalExpression` (enum)
- `BodyLanguage` (enum)
- `VisualFeatures` (dataclass)
- `AuditoryFeatures` (dataclass)
- `MotionFeatures` (dataclass)
- `SensoryData` (dataclass)
- `PerceptualInput` (dataclass)
- `PerceivedAgent` (dataclass)
- `ThreatAssessment` (dataclass)
- `AttentionFocus` (dataclass)
- `PerceptualFeatures` (dataclass)
- `PerceptualOutput` (dataclass)

#### `core/perception/world_model/__init__.py`

#### `core/self/__init__.py`

_UEM v2 - Self Module_

#### `core/self/ethics/__init__.py`

#### `core/self/goals.py`

_UEM v2 - Personal Goals Module_

**Classes:**
- `PersonalGoalConfig` (dataclass)
- `PersonalGoalManager`

**Functions:**
- `create_personal_goal_manager()`

#### `core/self/identity/__init__.py`

_UEM v2 - Identity Module_

**Classes:**
- `IdentityConfig` (dataclass)
- `IdentityManager`

**Functions:**
- `create_identity_manager()`
- `create_default_identity()`

#### `core/self/integrity/__init__.py`

#### `core/self/narrative/__init__.py`

#### `core/self/needs.py`

_UEM v2 - Needs Module_

**Classes:**
- `NeedConfig` (dataclass)
- `NeedManager`

**Functions:**
- `get_default_needs()`
- `create_need_manager()`

#### `core/self/processor.py`

_UEM v2 - Self Processor_

**Classes:**
- `SelfProcessorConfig` (dataclass)
- `SelfOutput` (dataclass)
- `SelfProcessor`

**Functions:**
- `create_self_processor()`
- `get_self_processor()`

#### `core/self/types.py`

_UEM v2 - Self Types_

**Classes:**
- `IdentityAspect` (enum)
- `ValueCategory` (enum)
- `ValuePriority` (enum)
- `NeedLevel` (enum)
- `NeedStatus` (enum)
- `GoalDomain` (enum)
- `IntegrityStatus` (enum)
- `NarrativeType` (enum)
- `Value` (dataclass)
- `Need` (dataclass)
- `PersonalGoal` (dataclass)
- `IdentityTrait` (dataclass)
- `Identity` (dataclass)
- `NarrativeElement` (dataclass)
- `SelfState` (dataclass)

#### `core/self/values/__init__.py`

_UEM v2 - Values Module_

**Classes:**
- `ValueSystemConfig` (dataclass)
- `ValueSystem`

**Functions:**
- `get_default_values()`
- `create_value_system()`

#### `core/utils/__init__.py`

_core/utils/__init__.py_

#### `core/utils/text.py`

_core/utils/text.py_

**Functions:**
- `normalize_turkish()`
- `normalize_for_matching()`

### engine/

#### `engine/__init__.py`

_UEM v2 - Engine Module_

#### `engine/cycle.py`

_UEM v2 - Cognitive Cycle_

**Classes:**
- `CycleConfig` (dataclass)
- `CycleState` (dataclass)
- `CognitiveCycle`

#### `engine/events/__init__.py`

_UEM v2 - Events Module_

#### `engine/events/bus.py`

_UEM v2 - Event Bus_

**Classes:**
- `EventType` (enum)
- `Event` (dataclass)
- `EventBus`

**Functions:**
- `get_event_bus()`
- `reset_event_bus()`

#### `engine/handlers/__init__.py`

_UEM v2 - Phase Handlers_

**Functions:**
- `register_all_handlers()`

#### `engine/handlers/affect.py`

_UEM v2 - Affect Phase Handlers_

**Classes:**
- `AffectPhaseConfig` (dataclass)
- `AffectPhaseState` (dataclass)
- `AffectPhaseHandler`

**Functions:**
- `create_feel_handler()`
- `simple_feel_handler()`

#### `engine/handlers/cognition.py`

_UEM v2 - Cognition Phase Handlers_

**Classes:**
- `CognitionHandlerConfig` (dataclass)
- `ReasonPhaseHandler`
- `EvaluatePhaseHandler`

**Functions:**
- `create_reason_handler()`
- `create_evaluate_handler()`
- `create_cognition_handlers()`

#### `engine/handlers/executive.py`

_UEM v2 - Executive Phase Handlers_

**Classes:**
- `ExecutiveConfig` (dataclass)
- `DecidePhaseHandler`
- `ActPhaseHandler`

**Functions:**
- `create_decide_handler()`
- `create_act_handler()`

#### `engine/handlers/memory.py`

_UEM v2 - Memory Phase Handlers_

**Classes:**
- `RetrievePhaseConfig` (dataclass)
- `RetrieveHandlerState` (dataclass)
- `RetrievePhaseHandler`

**Functions:**
- `create_retrieve_handler()`

#### `engine/handlers/perception.py`

_UEM v2 - Perception Phase Handlers_

**Classes:**
- `PerceptionHandlerConfig` (dataclass)
- `SensePhaseHandler`
- `AttendPhaseHandler`
- `PerceivePhaseHandler`
- `LegacyPerceivePhaseHandler`

**Functions:**
- `create_sense_handler()`
- `create_attend_handler()`
- `create_perceive_handler()`
- `create_legacy_perceive_handler()`

#### `engine/phases/__init__.py`

_UEM v2 - Phases Module_

#### `engine/phases/definitions.py`

_UEM v2 - Phase Definitions_

**Classes:**
- `Phase` (enum)
- `PhaseConfig` (dataclass)
- `PhaseResult` (dataclass)

### foundation/

#### `foundation/__init__.py`

_UEM v2 - Foundation Module_

#### `foundation/ontology/__init__.py`

#### `foundation/schemas/__init__.py`

#### `foundation/state/__init__.py`

_UEM v2 - State Module_

#### `foundation/state/bridge.py`

_UEM v2 - StateVector Bridge_

**Classes:**
- `SocialContext` (dataclass)
- `StateVectorBridge`

**Functions:**
- `get_state_bridge()`

#### `foundation/state/fields.py`

_UEM v2 - StateVector Field Definitions_

**Classes:**
- `SVField` (enum)

#### `foundation/state/vector.py`

_UEM v2 - StateVector_

**Classes:**
- `StateVector` (dataclass)

#### `foundation/types/__init__.py`

_UEM v2 - Types Module_

#### `foundation/types/actions.py`

_UEM v2 - Action Types_

**Classes:**
- `ActionCategory` (enum)
- `ActionStatus` (enum)
- `Action` (dataclass)
- `ActionOutcome` (dataclass)

**Functions:**
- `create_wait_action()`
- `create_observe_action()`

#### `foundation/types/base.py`

_UEM v2 - Base Types_

**Classes:**
- `Priority` (enum)
- `ModuleType` (enum)
- `Context` (dataclass)
- `Entity` (dataclass)
- `Stimulus` (dataclass)

#### `foundation/types/results.py`

_UEM v2 - Result Types_

**Classes:**
- `ResultStatus` (enum)
- `ModuleResult` (dataclass)
- `PerceptionResult` (dataclass)
- `CognitionResult` (dataclass)
- `MemoryResult` (dataclass)
- `AffectResult` (dataclass)
- `ExecutiveResult` (dataclass)
- `CycleResult` (dataclass)

### infra/

#### `infra/__init__.py`

#### `infra/config/__init__.py`

#### `infra/logging/__init__.py`

#### `infra/logging/handlers/__init__.py`

#### `infra/storage/__init__.py`

#### `infra/storage/file/__init__.py`

#### `infra/storage/memory/__init__.py`

#### `infra/storage/postgres/__init__.py`

### interface/

#### `interface/__init__.py`

_interface/__init__.py_

#### `interface/api/__init__.py`

#### `interface/chat/__init__.py`

_interface/chat/__init__.py_

#### `interface/chat/cli.py`

_interface/chat/cli.py_

**Classes:**
- `CLIChat`

**Functions:**
- `main()`

#### `interface/cli/__init__.py`

#### `interface/dashboard/__init__.py`

#### `interface/dashboard/app.py`

_UEM v2 - Streamlit Dashboard_

**Functions:**
- `get_data_provider()`
- `get_dashboard_data()`
- `render_cycle_metrics()`
- `render_phase_chart()`
- `render_memory_stats()`
- `render_trust_chart()`
- `render_activity_log()`
- `render_system_stats()`
- `main()`

### meta/

#### `meta/__init__.py`

#### `meta/consciousness/__init__.py`

_UEM v2 - Consciousness Module_

#### `meta/consciousness/attention.py`

_UEM v2 - Attention Module_

**Classes:**
- `AttentionConfig` (dataclass)
- `AttentionFilter` (dataclass)
- `AttentionController`

**Functions:**
- `create_attention_controller()`

#### `meta/consciousness/awareness.py`

_UEM v2 - Awareness Module_

**Classes:**
- `AwarenessConfig` (dataclass)
- `AwarenessManager`

**Functions:**
- `create_awareness_manager()`

#### `meta/consciousness/integration.py`

_UEM v2 - Global Workspace Integration_

**Classes:**
- `GlobalWorkspaceConfig` (dataclass)
- `BroadcastListener` (dataclass)
- `GlobalWorkspace`

**Functions:**
- `create_global_workspace()`

#### `meta/consciousness/processor.py`

_UEM v2 - Consciousness Processor_

**Classes:**
- `ConsciousnessConfig` (dataclass)
- `ConsciousnessOutput` (dataclass)
- `ConsciousnessProcessor`

**Functions:**
- `create_consciousness_processor()`
- `get_consciousness_processor()`

#### `meta/consciousness/types.py`

_UEM v2 - Consciousness Types_

**Classes:**
- `ConsciousnessLevel` (enum)
- `AwarenessType` (enum)
- `AttentionMode` (enum)
- `AttentionPriority` (enum)
- `BroadcastType` (enum)
- `IntegrationStatus` (enum)
- `AttentionFocus` (dataclass)
- `Qualia` (dataclass)
- `WorkspaceContent` (dataclass)
- `AwarenessState` (dataclass)
- `GlobalWorkspaceState` (dataclass)
- `ConsciousExperience` (dataclass)

#### `meta/consciousness/workspace/__init__.py`

#### `meta/metamind/__init__.py`

_UEM v2 - MetaMind Module_

#### `meta/metamind/analyzers.py`

_UEM v2 - MetaMind Analyzers_

**Classes:**
- `AnalyzerConfig` (dataclass)
- `CycleAnalyzer`

**Functions:**
- `create_cycle_analyzer()`
- `get_cycle_analyzer()`

#### `meta/metamind/insights.py`

_UEM v2 - MetaMind Insights_

**Classes:**
- `InsightGeneratorConfig` (dataclass)
- `InsightGenerator`

**Functions:**
- `create_insight_generator()`
- `get_insight_generator()`

#### `meta/metamind/learning.py`

_UEM v2 - MetaMind Learning_

**Classes:**
- `LearningManagerConfig` (dataclass)
- `AdaptationStrategy` (dataclass)
- `LearningManager`

**Functions:**
- `create_learning_manager()`
- `get_learning_manager()`

#### `meta/metamind/patterns.py`

_UEM v2 - MetaMind Patterns_

**Classes:**
- `PatternDetectorConfig` (dataclass)
- `PatternDetector`

**Functions:**
- `create_pattern_detector()`
- `get_pattern_detector()`

#### `meta/metamind/processor.py`

_UEM v2 - MetaMind Processor_

**Classes:**
- `MetaMindConfig` (dataclass)
- `MetaMindOutput` (dataclass)
- `MetaMindProcessor`

**Functions:**
- `create_metamind_processor()`
- `get_metamind_processor()`

#### `meta/metamind/types.py`

_UEM v2 - MetaMind Types_

**Classes:**
- `InsightType` (enum)
- `PatternType` (enum)
- `LearningGoalType` (enum)
- `MetaStateType` (enum)
- `AnalysisScope` (enum)
- `SeverityLevel` (enum)
- `CycleAnalysisResult` (dataclass)
- `Insight` (dataclass)
- `Pattern` (dataclass)
- `LearningGoal` (dataclass)
- `MetaState` (dataclass)

#### `meta/monitoring/__init__.py`

_UEM v2 - Monitoring Module_

#### `meta/monitoring/alerts/__init__.py`

#### `meta/monitoring/metrics/__init__.py`

_UEM v2 - Metrics Module_

#### `meta/monitoring/metrics/collector.py`

_UEM v2 - Metrics Collector_

**Classes:**
- `Metric` (dataclass)
- `MetricSummary` (dataclass)
- `MetricsCollector`

**Functions:**
- `get_metrics_collector()`

#### `meta/monitoring/metrics/cycle.py`

_UEM v2 - Cycle Metrics_

**Classes:**
- `MetricType` (enum)
- `PhaseMetrics` (dataclass)
- `CycleMetrics` (dataclass)
- `CycleMetricsHistory`

#### `meta/monitoring/monitor.py`

_UEM v2 - System Monitor_

**Classes:**
- `MonitorConfig` (dataclass)
- `SystemMonitor`

**Functions:**
- `get_system_monitor()`

#### `meta/monitoring/persistence.py`

_UEM v2 - Monitoring Persistence_

**Classes:**
- `MonitoringPersistence`
- `DashboardDataProvider`

**Functions:**
- `get_monitoring_persistence()`
- `get_dashboard_data_provider()`

#### `meta/monitoring/predata/__init__.py`

#### `meta/monitoring/reporter.py`

_UEM v2 - Monitoring Reporter_

**Classes:**
- `ReporterConfig` (dataclass)
- `MonitoringReporter`

**Functions:**
- `get_reporter()`

### scripts/

#### `scripts/aggregate_feedback.py`

_scripts/aggregate_feedback.py_

**Functions:**
- `main()`

#### `scripts/analyze_episodes.py`

_scripts/analyze_episodes.py_

**Functions:**
- `main()`

#### `scripts/demo_dashboard.py`

_UEM Dashboard Demo - 20 Farklı Senaryo_

**Functions:**
- `create_memory()`
- `create_cycle()`
- `run_scenarios()`
- `verify_db()`
- `main()`

#### `scripts/demo_full_system.py`

_UEM Full System Demo - Tum Modullerin Entegre Calismasi_

**Classes:**
- `Colors`

**Functions:**
- `print_header()`
- `print_step()`
- `print_result()`
- `print_warning()`
- `print_success()`
- `print_info()`
- `run_full_system_demo()`

#### `scripts/generate_docs.py`

_scripts/generate_docs.py_

**Classes:**
- `ClassInfo` (dataclass)
- `FunctionInfo` (dataclass)
- `ModuleInfo` (dataclass)

**Functions:**
- `analyze_module()`
- `analyze_project()`
- `generate_project_structure_md()`
- `generate_data_types_md()`
- `generate_api_reference_md()`
- `main()`
