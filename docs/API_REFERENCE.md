# UEM v2 API Reference

_Auto-generated: 2025-12-11 06:11_

Function and class API reference for UEM v2.

## Core Modules

### `core/affect/emotion/core/dynamics.py`

#### class `DecayModel` `(Enum)`

_Duygu sönümlenme modelleri._

#### class `RegulationStrategy` `(Enum)`

_Duygu düzenleme stratejileri (Gross, 2015)._

#### class `EmotionConfig` `@dataclass`

_Duygu dinamiği yapılandırması._

#### class `EmotionState` `@dataclass`

_Dinamik duygu durumu._

Methods:
- `update()`
- `trigger()`
- `trigger_emotion()`
- `trigger_from_event()`
- `regulate()`
- `social_contagion()`
- `set_baseline()`
- `reset_to_baseline()`
- `get_dominant_emotion()`
- `get_emotional_trajectory()`
- `is_positive()`
- `is_negative()`
- `is_neutral()`
- `is_high_arousal()`
- `is_low_arousal()`

#### `create_personality_baseline(extraversion, neuroticism, agreeableness) -> PADState`

_Big Five kişilik özelliklerinden baseline PAD oluştur._

### `core/affect/emotion/core/emotions.py`

#### class `BasicEmotion` `(Enum)`

_Temel duygular (Ekman + Plutchik bazlı)._

#### class `SecondaryEmotion` `(Enum)`

_İkincil duygular - temel duyguların kombinasyonları._

#### class `EmotionProfile` `@dataclass`

_Bir duygunun tam profili._

#### `get_emotion_pad(emotion) -> PADState`

_Temel duygunun PAD koordinatlarını döndür._

#### `get_secondary_emotion_pad(emotion) -> PADState`

_İkincil duygunun PAD koordinatlarını döndür._

#### `identify_emotion(pad, threshold) -> Optional[...]`

_PAD durumuna en yakın temel duyguyu bul._

#### `identify_all_emotions(pad, max_results, threshold) -> List[...]`

_PAD durumuna yakın tüm duyguları bul (sıralı)._

#### `create_emotion_profile(emotion) -> EmotionProfile`

_Temel duygu için tam profil oluştur._

#### `blend_emotions(emotion1, emotion2, weight) -> PADState`

_İki duyguyu karıştır._

#### `get_emotion_family(pad) -> List[...]`

_PAD durumunun ait olduğu duygu ailesini döndür._

### `core/affect/emotion/core/pad.py`

#### class `PADState` `@dataclass`

_PAD duygu durumu._

Methods:
- `__post_init__()`
- `valence()`
- `valence()`
- `distance()`
- `blend()`
- `amplify()`
- `decay()`
- `to_dict()`
- `from_dict()`
- `to_tuple()`
- `copy()`
- `from_tuple()`
- `neutral()`

#### class `PADOctant` `(Enum)`

_PAD uzayının 8 oktantı - temel duygu bölgeleri._

#### `get_octant(pad) -> PADOctant`

_PAD durumunun hangi oktantta olduğunu bul._

#### `pad_from_appraisal(goal_relevance, goal_congruence, coping_potential, ...) -> PADState`

_Appraisal teorisinden PAD hesapla._

#### `pad_from_stimulus(threat_level, reward_level, uncertainty, ...) -> PADState`

_Stimulus özelliklerinden PAD hesapla._

### `core/affect/social/empathy/channels.py`

#### class `EmpathyChannel` `(Enum)`

_Empati kanalları._

#### class `ChannelResult` `@dataclass`

_Tek bir kanalın sonucu._

#### class `EmpathyChannels` `@dataclass`

_4 kanalın birleşik sonucu._

Methods:
- `__post_init__()`
- `get()`
- `weighted_average()`
- `to_dict()`
- `dominant_channel()`

#### `get_context_weights(context) -> Dict[...]`

_Bağlama uygun ağırlıkları getir._

### `core/affect/social/empathy/empathy.py`

#### class `EmpathyConfig` `@dataclass`

_Empati modülü yapılandırması._

#### class `Empathy`

_Empati hesaplama facade sınıfı._

Methods:
- `__init__()`
- `compute()`
- `compute_batch()`
- `quick_empathy()`
- `update_self_state()`
- `clear_cache()`

#### `compute_empathy_for_emotion(self_state, target_emotion) -> float`

_Belirli bir duygu için empati hesapla._

#### `estimate_empathy_difficulty(agent) -> float`

_Empati kurmanın zorluğunu tahmin et._

### `core/affect/social/empathy/simulation.py`

#### class `AgentState` `@dataclass`

_Gözlemlenen ajanın durumu._

Methods:
- `has_emotional_cues()`

#### class `SimulationConfig` `@dataclass`

_Simülasyon yapılandırması._

#### class `EmpathySimulator`

_Simulation Theory bazlı empati hesaplayıcı._

Methods:
- `__init__()`
- `simulate()`

#### class `EmpathyResult` `@dataclass`

_Empati hesaplama sonucu._

Methods:
- `get_dominant_channel()`
- `get_inferred_emotion()`
- `to_dict()`

### `core/affect/social/orchestrator.py`

#### class `SocialAffectResult` `@dataclass`

_Social affect işleminin entegre sonucu._

Methods:
- `to_dict()`
- `summary()`

#### class `OrchestratorConfig` `@dataclass`

_Orkestratör yapılandırması._

#### class `SocialAffectOrchestrator`

_Social affect modüllerini koordine eden orkestratör._

Methods:
- `__init__()`
- `from_state_vector()`
- `process()`
- `process_batch()`
- `quick_process()`
- `bind_state_vector()`
- `update_self_state()`
- `get_trust_profile()`
- `reset_trust()`
- `get_state_vector_summary()`
- `stats()`

#### `create_orchestrator(self_pad, state_vector, config) -> SocialAffectOrchestrator`

_Orkestratör oluştur._

#### `process_social_affect(agent, state_vector, relationship) -> SocialAffectResult`

_Tek seferlik social affect işlemi._

### `core/affect/social/sympathy/calculator.py`

#### class `RelationshipContext` `@dataclass`

_İlişki bağlamı - sempati hesaplamada kullanılır._

Methods:
- `stranger()`
- `friend()`
- `rival()`
- `from_relationship_type()`

#### class `SympathyConfig` `@dataclass`

_Sempati hesaplama yapılandırması._

#### class `SympathyCalculator`

_Sempati hesaplayıcı._

Methods:
- `__init__()`
- `calculate()`

#### class `SympathyResult` `@dataclass`

_Sempati hesaplama sonucu._

Methods:
- `has_sympathy()`
- `get_action_tendency()`
- `is_prosocial()`
- `is_antisocial()`
- `to_dict()`

### `core/affect/social/sympathy/sympathy.py`

#### class `SympathyModuleConfig` `@dataclass`

_Sempati modülü yapılandırması._

#### class `Sympathy`

_Sempati hesaplama facade sınıfı._

Methods:
- `__init__()`
- `compute()`
- `compute_from_agent()`
- `quick_sympathy()`
- `update_self_state()`
- `get_self_state()`

#### `predict_sympathy(target_valence, relationship_valence) -> SympathyType`

_Basit sempati tahmini._

#### `get_sympathy_spectrum(empathy_result) -> Dict[...]`

_Olası tüm sempatilerin spektrumunu döndür._

### `core/affect/social/sympathy/types.py`

#### class `SympathyType` `(Enum)`

_Sempati türleri._

Methods:
- `prosocial()`
- `antisocial()`

#### class `SympathyResponse` `@dataclass`

_Tek bir sempati tepkisi._

Methods:
- `is_prosocial()`
- `is_antisocial()`

#### class `SympathyTrigger` `@dataclass`

_Sempati tetikleme koşulu._

Methods:
- `matches()`

#### `get_sympathy_pad(sympathy_type) -> PADState`

_Sempati türünün PAD etkisini getir._

#### `get_action_tendency(sympathy_type) -> str`

_Sempati türünün davranış eğilimini getir._

#### `get_trigger(sympathy_type) -> SympathyTrigger`

_Sempati türünün tetikleme koşulunu getir._

### `core/affect/social/trust/manager.py`

#### class `TrustProfile` `@dataclass`

_Bir ajan için güven profili._

Methods:
- `__post_init__()`
- `overall_trust()`
- `trust_level()`
- `interaction_count()`
- `trust_ratio()`
- `to_dict()`

#### class `TrustConfig` `@dataclass`

_Güven yönetimi yapılandırması._

#### class `TrustManager`

_Güven yöneticisi._

Methods:
- `__init__()`
- `get_profile()`
- `get_trust()`
- `get_trust_level()`
- `record_event()`
- `apply_decay()`
- `set_initial_trust()`
- `compare_trust()`
- `get_most_trusted()`
- `get_least_trusted()`
- `reset_trust()`
- `all_profiles()`
- `stats()`

### `core/affect/social/trust/trust.py`

#### class `Trust`

_Güven hesaplama facade sınıfı._

Methods:
- `__init__()`
- `get()`
- `get_level()`
- `get_profile()`
- `record()`
- `set_initial()`
- `should_trust()`
- `trust_for_action()`
- `compare()`
- `rank()`
- `analyze()`
- `explain_trust()`
- `reset()`
- `apply_time_decay()`
- `most_trusted()`
- `least_trusted()`
- `stats()`

#### `quick_trust_check(interaction_count, positive_ratio, had_betrayal) -> TrustLevel`

_Hızlı güven tahmini._

#### `calculate_risk_threshold(trust_level) -> float`

_Güven seviyesine göre kabul edilebilir risk eşiği._

### `core/affect/social/trust/types.py`

#### class `TrustLevel` `(Enum)`

_Güven seviyeleri._

Methods:
- `from_value()`

#### class `TrustType` `(Enum)`

_Güven türleri - nasıl oluştuğuna göre._

#### class `TrustDimension` `(Enum)`

_Güven boyutları (Mayer et al., 1995)._

#### class `TrustComponents` `@dataclass`

_Güven bileşenleri - 4 boyutlu model._

Methods:
- `__post_init__()`
- `overall()`
- `weakest_dimension()`
- `strongest_dimension()`
- `to_dict()`
- `copy()`
- `default()`
- `high()`
- `low()`

#### class `TrustEvent` `@dataclass`

_Güveni etkileyen olay._

Methods:
- `weighted_impact()`

#### `create_trust_event(event_type, context) -> TrustEvent`

_Olay tipinden TrustEvent oluştur._

#### `determine_trust_type(components, history_length, had_betrayal) -> TrustType`

_Güven bileşenlerinden güven tipini belirle._

### `core/cognition/evaluation/__init__.py`

#### class `EvaluationConfig` `@dataclass`

_Değerlendirme yapılandırması._

#### class `RiskItem` `@dataclass`

_Tanımlanan bir risk._

Methods:
- `severity()`

#### class `OpportunityItem` `@dataclass`

_Tanımlanan bir fırsat._

Methods:
- `expected_value()`

#### class `RiskAssessor`

_Risk değerlendirici._

Methods:
- `__init__()`
- `assess_risks()`
- `get_overall_risk_level()`

#### class `OpportunityAssessor`

_Fırsat değerlendirici._

Methods:
- `__init__()`
- `assess_opportunities()`
- `get_overall_opportunity_level()`

#### class `SituationEvaluator`

_Ana durum değerlendirici._

Methods:
- `__init__()`
- `evaluate()`

#### `get_situation_evaluator(config) -> SituationEvaluator`

_Situation evaluator singleton'ı al veya oluştur._

#### `create_situation_evaluator(config) -> SituationEvaluator`

_Yeni situation evaluator oluştur._

### `core/cognition/planning.py`

#### class `PlanningConfig` `@dataclass`

_Planlama yapılandırması._

#### class `ActionTemplate` `@dataclass`

_Eylem şablonu._

#### class `GoalManager`

_Hedef yöneticisi._

Methods:
- `__init__()`
- `add_goal()`
- `get_goal()`
- `remove_goal()`
- `update_goal_status()`
- `get_active_goals()`
- `get_pending_goals()`
- `get_prioritized_goals()`
- `get_highest_priority_goal()`
- `activate_goal()`
- `suspend_goal()`
- `complete_goal()`
- `fail_goal()`
- `create_survival_goal()`
- `create_resource_goal()`
- `create_social_goal()`

#### class `ActionPlanner`

_Eylem planlayıcı._

Methods:
- `__init__()`
- `create_plan()`
- `add_action_template()`
- `get_available_actions()`

#### `get_goal_manager(config) -> GoalManager`

_Goal manager singleton'ı al veya oluştur._

#### `get_action_planner(config) -> ActionPlanner`

_Action planner singleton'ı al veya oluştur._

#### `create_goal_manager(config) -> GoalManager`

_Yeni goal manager oluştur._

#### `create_action_planner(config) -> ActionPlanner`

_Yeni action planner oluştur._

### `core/cognition/processor.py`

#### class `CognitionConfig` `@dataclass`

_Biliş işlemci yapılandırması._

#### class `CognitionOutput` `@dataclass`

_Biliş işleme çıktısı._

Methods:
- `to_dict()`

#### class `CognitionProcessor`

_Ana biliş işlemcisi._

Methods:
- `__init__()`
- `process()`
- `reason()`
- `evaluate()`
- `cognitive_state()`
- `get_beliefs()`
- `get_goals()`
- `get_active_plan()`
- `add_belief()`
- `add_goal()`
- `complete_current_goal()`
- `get_metrics()`
- `reset()`

#### `get_cognition_processor(config) -> CognitionProcessor`

_Cognition processor singleton'ı al veya oluştur._

#### `create_cognition_processor(config) -> CognitionProcessor`

_Yeni cognition processor oluştur._

### `core/cognition/reasoning/__init__.py`

#### class `ReasoningConfig` `@dataclass`

_Reasoning engine yapılandırması._

#### class `InferenceRule` `@dataclass`

_Çıkarım kuralı._

#### class `ReasoningEngine`

_Ana akıl yürütme motoru._

Methods:
- `__init__()`
- `reason()`
- `deduce()`
- `induce()`
- `abduce()`
- `reason_by_analogy()`
- `add_rule()`
- `clear_cache()`
- `get_applicable_rules()`

#### `get_reasoning_engine(config) -> ReasoningEngine`

_Reasoning engine singleton'ı al veya oluştur._

#### `create_reasoning_engine(config) -> ReasoningEngine`

_Yeni reasoning engine oluştur._

### `core/cognition/types.py`

#### class `BeliefType` `(Enum)`

_İnanç türleri._

#### class `BeliefStrength` `(Enum)`

_İnanç gücü seviyeleri._

#### class `GoalType` `(Enum)`

_Hedef türleri._

#### class `GoalPriority` `(Enum)`

_Hedef önceliği._

#### class `GoalStatus` `(Enum)`

_Hedef durumu._

#### class `IntentionStrength` `(Enum)`

_Niyet gücü._

#### class `ReasoningType` `(Enum)`

_Akıl yürütme türleri._

#### class `RiskLevel` `(Enum)`

_Risk seviyesi._

#### class `OpportunityLevel` `(Enum)`

_Fırsat seviyesi._

#### class `Belief` `@dataclass`

_Bir inanç/bilgi temsili._

Methods:
- `strength()`
- `update_confidence()`
- `add_evidence()`
- `add_contradiction()`
- `is_valid()`

#### class `Goal` `@dataclass`

_Bir hedef temsili._

Methods:
- `importance()`
- `can_start()`
- `is_achieved()`
- `is_failed()`
- `update_progress()`

#### class `Intention` `@dataclass`

_Bir niyet temsili._

Methods:
- `priority_score()`
- `strengthen()`
- `weaken()`

#### class `PlanStep` `@dataclass`

_Plan adımı._

#### class `Plan` `@dataclass`

_Bir plan temsili._

Methods:
- `total_steps()`
- `progress()`
- `next_step()`
- `add_step()`
- `advance()`
- `fail_current()`

#### class `ReasoningResult` `@dataclass`

_Akıl yürütme sonucu._

Methods:
- `quality_score()`

#### class `SituationAssessment` `@dataclass`

_Mevcut durumun değerlendirmesi._

#### class `CognitiveState` `@dataclass`

_Agent'ın biliş durumu - tüm biliş bilgilerinin bütünü._

Methods:
- `add_belief()`
- `get_belief()`
- `get_beliefs_about()`
- `get_strong_beliefs()`
- `remove_weak_beliefs()`
- `add_goal()`
- `get_goal()`
- `get_active_goals()`
- `get_highest_priority_goal()`
- `add_intention()`
- `get_strongest_intention()`
- `add_plan()`
- `get_active_plan()`
- `activate_plan()`
- `summary()`

### `core/language/chat_agent.py`

#### class `ChatConfig` `@dataclass`

_Chat agent yapilandirmasi._

#### class `ChatResponse` `@dataclass`

_Chat yanit yapisi._

#### class `UEMChatAgent`

_UEM Chat Agent - Memory + LLM entegre chat._

Methods:
- `__init__()`
- `start_session()`
- `end_session()`
- `chat()`
- `recall()`
- `get_conversation_history()`
- `feedback()`
- `get_learned_count()`
- `get_learning_stats()`
- `get_current_emotion()`
- `get_trust_level()`
- `get_session_stats()`
- `set_pipeline_mode()`
- `get_pipeline_mode()`
- `get_pipeline_status()`
- `get_last_pipeline_result()`
- `get_pipeline_debug_info()`

#### `get_chat_agent(config, memory, llm) -> UEMChatAgent`

_Get chat agent singleton._

#### `reset_chat_agent() -> None`

_Reset chat agent singleton (test icin)._

#### `create_chat_agent(config, memory, llm) -> UEMChatAgent`

_Create new chat agent (test icin)._

### `core/language/construction/grammar.py`

#### class `ConstructionGrammarConfig` `@dataclass`

_ConstructionGrammar konfigürasyonu._

#### class `ConstructionGrammar`

_3 katmanlı Construction Grammar yöneticisi._

Methods:
- `__init__()`
- `add_construction()`
- `remove_construction()`
- `get_construction()`
- `get_by_level()`
- `get_by_dialogue_act()`
- `find_matching()`
- `get_all_constructions()`
- `count_by_level()`
- `count_total()`
- `load_defaults()`
- `clear()`

### `core/language/construction/mvcs.py`

#### class `MVCSCategory` `(Enum)`

_MVCS kategori tipleri._

#### class `MVCSConfig` `@dataclass`

_MVCS yapilandirmasi._

#### class `MVCSLoader`

_Minimum Viable Construction Set yukleyici._

Methods:
- `__init__()`
- `load_all()`
- `get_by_category()`
- `get_by_name()`
- `get_greet_constructions()`
- `get_self_intro_constructions()`
- `get_wellbeing_constructions()`
- `get_inform_constructions()`
- `get_empathy_constructions()`
- `get_clarify_constructions()`
- `get_refusal_constructions()`
- `get_category_count()`
- `get_total_count()`
- `clear_cache()`
- `get_constructions_by_dialogue_act()`
- `get_constructions_by_tone()`
- `get_constructions_by_formality()`

### `core/language/construction/realizer.py`

#### class `RealizationResult` `@dataclass`

_Gerçekleştirme sonucu._

#### class `ConstructionRealizerConfig` `@dataclass`

_ConstructionRealizer konfigürasyonu._

#### class `ConstructionRealizer`

_Construction + slot values → Cümle üretimi._

Methods:
- `__init__()`
- `realize()`
- `validate_slots()`
- `realize_multiple()`
- `get_required_slots()`
- `get_slot_types()`

### `core/language/construction/selector.py`

#### class `ConstructionScore` `@dataclass`

_Construction skorlaması._

#### class `SelectionResult` `@dataclass`

_Seçim sonucu._

#### class `ConstructionSelectorConfig` `@dataclass`

_ConstructionSelector konfigürasyonu._

#### class `ConstructionSelector`

_MessagePlan → Uygun Construction seçimi._

Methods:
- `__init__()`
- `select()`
- `score_construction()`
- `select_by_level()`
- `get_best_for_act()`
- `set_feedback_store()`

### `core/language/construction/types.py`

#### class `ConstructionLevel` `(Enum)`

_Construction katman seviyeleri._

#### class `SlotType` `(Enum)`

_Slot türleri - Template'deki değişken tipleri._

#### class `Slot` `@dataclass`

_Template slot tanımı._

Methods:
- `validate_value()`
- `get_value()`

#### class `MorphologyRule` `@dataclass`

_Morfoloji kuralı - Yüzey katmanı ek kuralları._

#### class `ConstructionForm` `@dataclass`

_Construction'ın yüzey formu._

Methods:
- `get_slot_names()`
- `has_slot()`
- `get_required_slots()`
- `validate_slots()`

#### class `ConstructionMeaning` `@dataclass`

_Construction'ın anlamı._

Methods:
- `matches_context()`

#### class `Construction` `@dataclass`

_3 katmanlı Construction Grammar yapısı._

Methods:
- `__post_init__()`
- `success_rate()`
- `total_uses()`
- `is_reliable()`
- `record_success()`
- `record_failure()`
- `realize()`
- `matches_dialogue_act()`
- `to_dict()`

#### `generate_construction_id() -> str`

_Generate unique construction ID (random UUID-based)._

#### `generate_deterministic_construction_id(name) -> str`

_Generate deterministic construction ID from a stable name._

#### `generate_slot_id() -> str`

_Generate unique slot ID._

#### `generate_morphology_rule_id() -> str`

_Generate unique morphology rule ID._

### `core/language/context.py`

#### class `ContextConfig` `@dataclass`

_Context builder yapilandirmasi._

#### class `ContextSection` `@dataclass`

_Context bolumu._

#### class `ContextBuilder`

_Context Builder - Memory + State -> LLM Context._

Methods:
- `__init__()`
- `build()`
- `count_tokens()`
- `truncate_to_fit()`
- `format_for_llm()`
- `stats()`

#### `get_context_builder(config) -> ContextBuilder`

_Get context builder singleton._

#### `reset_context_builder() -> None`

_Reset context builder singleton (test icin)._

#### `create_context_builder(config) -> ContextBuilder`

_Create new context builder (test icin)._

### `core/language/conversation/manager.py`

#### class `ContextManager`

_Multi-turn konuşma bağlamı yöneticisi._

Methods:
- `__init__()`
- `add_user_message()`
- `add_assistant_message()`
- `get_context()`
- `to_legacy_format()`
- `from_legacy_format()`
- `is_followup_question()`
- `is_topic_change()`
- `get_sentiment_trend()`
- `reset()`
- `get_recent_intents()`
- `get_recent_acts()`
- `get_context_summary()`

### `core/language/conversation/types.py`

#### class `Message` `@dataclass`

_Tek bir konuşma mesajı._

Methods:
- `is_user()`
- `is_assistant()`

#### class `ConversationContext` `@dataclass`

_Multi-turn konuşma bağlamı._

Methods:
- `get_recent_messages()`
- `get_user_messages()`
- `get_assistant_messages()`
- `get_last_user_message()`
- `get_last_assistant_message()`
- `message_count()`
- `is_empty()`
- `session_duration_seconds()`

#### class `ContextConfig` `@dataclass`

_ContextManager konfigürasyonu._

### `core/language/dialogue/act_selector.py`

#### class `SelectionStrategy` `(Enum)`

_Act seçim stratejisi._

#### class `ActScore` `@dataclass`

_Bir DialogueAct'in skoru._

#### class `ActSelectionResult` `@dataclass`

_Seçim sonucu._

#### class `ActSelectorConfig` `@dataclass`

_DialogueActSelector konfigürasyonu._

#### class `DialogueActSelector`

_SituationModel → DialogueAct seçimi._

Methods:
- `__init__()`
- `select()`

### `core/language/dialogue/message_planner.py`

#### class `ConstraintSeverity` `(Enum)`

_Kısıt ciddiyeti._

#### class `ConstraintType` `(Enum)`

_Kısıt türleri._

#### class `ContentPoint` `@dataclass`

_İçerik noktası - MessagePlan'da ne söylenecek._

Methods:
- `__post_init__()`

#### class `MessageConstraint` `@dataclass`

_Mesaj kısıtı - MessagePlan'da neye dikkat edilmeli._

#### class `MessagePlannerConfig` `@dataclass`

_MessagePlanner konfigürasyonu._

#### class `MessagePlanner`

_ActSelectionResult + SituationModel → MessagePlan_

Methods:
- `__init__()`
- `plan()`
- `update_plan()`

### `core/language/dialogue/situation_builder.py`

#### class `SituationBuilderConfig` `@dataclass`

_SituationBuilder konfigürasyonu._

#### class `SituationBuilder`

_Perception + Memory + Cognition → SituationModel_

Methods:
- `__init__()`
- `build()`

### `core/language/dialogue/types.py`

#### class `DialogueAct` `(Enum)`

_Konuşma eylemleri - Speech Act Theory'den esinlenilmiş._

#### class `ToneType` `(Enum)`

_Ton türleri - Mesajın üslup ve atmosferi._

#### class `Actor` `@dataclass`

_Konuşmadaki aktör - Kim konuşuyor/dinliyor?_

Methods:
- `__post_init__()`

#### class `Intention` `@dataclass`

_Niyet temsili - Aktör ne yapmak istiyor?_

Methods:
- `__post_init__()`

#### class `Risk` `@dataclass`

_Risk bilgisi - SituationModel'deki risk temsili._

Methods:
- `__post_init__()`

#### class `Relationship` `@dataclass`

_İlişki bilgisi - Aktörler arası ilişki._

Methods:
- `__post_init__()`

#### class `TemporalContext` `@dataclass`

_Zaman bağlamı - Konuşmanın zamansal özellikleri._

Methods:
- `conversation_duration()`

#### class `EmotionalState` `@dataclass`

_Duygusal durum - Affect modülünden gelen PAD değerleri._

Methods:
- `__post_init__()`

#### class `SituationModel` `@dataclass`

_Durum Modeli - Perception + Memory + Cognition çıktısı._

Methods:
- `__post_init__()`
- `get_primary_actor()`
- `get_highest_risk()`
- `has_high_risk()`

#### class `MessagePlan` `@dataclass`

_Mesaj Planı - Executive karar çıktısı._

Methods:
- `__post_init__()`
- `primary_act()`
- `has_emotional_act()`
- `has_boundary_act()`
- `has_warning_act()`

#### `generate_situation_id() -> str`

_Generate unique situation model ID._

#### `generate_message_plan_id() -> str`

_Generate unique message plan ID._

### `core/language/intent/patterns.py`

#### `get_pattern_weight(pattern) -> float`

_Pattern için güven ağırlığı döndür._

#### `get_all_patterns() -> List[...]`

_Tüm pattern'leri döndür (중복 olmadan)._

#### `get_pattern_count() -> int`

_Toplam pattern sayısı._

#### `get_patterns_for_category(category) -> List[...]`

_Belirli bir kategori için pattern'leri döndür._

#### `get_pattern_id(pattern) -> Optional[...]`

_Pattern text'ten pattern ID'yi getir._

#### `get_pattern_ids_for_category(category) -> List[...]`

_Belirli bir kategorinin tüm pattern ID'lerini döndür._

### `core/language/intent/recognizer.py`

#### class `IntentRecognizerConfig` `@dataclass`

_IntentRecognizer konfigürasyonu._

#### class `IntentRecognizer`

_Kullanıcı mesajından intent çıkarır._

Methods:
- `__init__()`
- `recognize()`
- `get_all_matches()`
- `has_intent()`
- `get_confidence_for_category()`
- `get_top_intents()`
- `batch_recognize()`
- `get_stats()`

### `core/language/intent/types.py`

#### class `IntentCategory` `(Enum)`

_Kullanıcı niyeti kategorileri._

#### class `IntentMatch` `@dataclass`

_Bir intent eşleşmesi._

#### class `IntentResult` `@dataclass`

_Intent tanıma sonucu._

Methods:
- `has_intent()`
- `get_all_categories()`

### `core/language/llm_adapter.py`

#### class `LLMProvider` `(Enum)`

_Desteklenen LLM provider'lar._

#### class `LLMConfig` `@dataclass`

_LLM yapilandirmasi._

Methods:
- `__post_init__()`

#### class `LLMResponse` `@dataclass`

_LLM yanit yapisi._

#### class `LLMAdapter`

_LLM Adapter base class._

Methods:
- `__init__()`
- `generate()`
- `generate_async()`
- `is_available()`
- `get_provider()`
- `stats()`

#### class `MockLLMAdapter`

_Mock LLM Adapter - Test icin._

Methods:
- `__init__()`
- `generate()`
- `generate_async()`
- `is_available()`
- `get_call_count()`
- `get_last_prompt()`
- `get_last_system_prompt()`
- `get_all_prompts()`
- `get_all_system_prompts()`
- `reset()`
- `set_responses()`

#### class `AnthropicAdapter`

_Anthropic Claude Adapter._

Methods:
- `__init__()`
- `generate()`
- `is_available()`

#### class `OpenAIAdapter`

_OpenAI Adapter._

Methods:
- `__init__()`
- `generate()`
- `is_available()`

#### `create_adapter(config) -> LLMAdapter`

_Create LLM adapter based on config._

#### `get_llm_adapter(config) -> LLMAdapter`

_Get LLM adapter singleton._

#### `reset_llm_adapter() -> None`

_Reset LLM adapter singleton (test icin)._

### `core/language/pipeline/config.py`

#### class `SelfCritiqueConfig` `@dataclass`

_SelfCritique konfigurasyonu._

#### class `PipelineConfig` `@dataclass`

_ThoughtToSpeechPipeline ana konfigurasyonu._

Methods:
- `__post_init__()`
- `minimal()`
- `strict()`
- `balanced()`
- `with_self_critique()`
- `with_risk_level()`

### `core/language/pipeline/self_critique.py`

#### class `CritiqueResult` `@dataclass`

_Self critique sonucu._

Methods:
- `__post_init__()`
- `needs_revision()`
- `violation_count()`
- `has_critical_violation()`

#### class `SelfCritique`

_Uretilen cevabi degerlendir ve gerekirse duzelt._

Methods:
- `__init__()`
- `critique()`
- `revise()`
- `get_critique_summary()`

### `core/language/pipeline/thought_to_speech.py`

#### class `PipelineResult` `@dataclass`

_Pipeline sonucu._

Methods:
- `id()`
- `is_approved()`
- `risk_level()`
- `was_revised()`
- `failure()`

#### class `ThoughtToSpeechPipeline`

_Tam pipeline: Input -> SituationModel -> DialogueAct -> MessagePlan -> Risk -> Construction -> Output_

Methods:
- `__init__()`
- `process()`
- `process_with_retry()`
- `get_pipeline_info()`

#### `generate_pipeline_result_id() -> str`

_Generate unique pipeline result ID._

### `core/language/risk/approver.py`

#### class `ApprovalDecision` `(Enum)`

_Onay kararı türleri._

#### class `ApprovalResult` `@dataclass`

_Onay sonucu._

Methods:
- `is_approved()`
- `needs_modifications()`
- `is_rejected()`

#### class `InternalApproverConfig` `@dataclass`

_InternalApprover konfigürasyonu._

#### class `InternalApprover`

_RiskAssessment → ApprovalResult_

Methods:
- `__init__()`
- `approve()`
- `override_approval()`
- `get_approval_flow()`

### `core/language/risk/scorer.py`

#### class `RiskScorerConfig` `@dataclass`

_RiskScorer konfigürasyonu._

#### class `RiskScorer`

_MessagePlan + SituationModel → RiskAssessment_

Methods:
- `__init__()`
- `assess()`
- `get_risk_patterns()`

### `core/language/risk/types.py`

#### class `RiskLevel` `(Enum)`

_Risk seviyeleri - Kontrol mekanizması tetikleyicisi._

Methods:
- `from_score()`
- `requires_human_approval()`
- `allows_auto_approval()`

#### class `RiskCategory` `(Enum)`

_Risk kategorileri - Riskin türü/kaynağı._

#### class `RiskFactor` `@dataclass`

_Bireysel risk faktörü._

Methods:
- `__post_init__()`
- `is_high()`
- `is_critical()`

#### class `RiskAssessment` `@dataclass`

_Kapsamlı risk değerlendirmesi._

Methods:
- `__post_init__()`
- `is_approved()`
- `is_rejected()`
- `needs_review()`
- `highest_risk_factor()`
- `get_factors_by_category()`
- `has_ethical_concern()`
- `has_trust_damage()`
- `calculate_weighted_score()`
- `create_low_risk()`
- `create_critical_risk()`

#### `generate_risk_assessment_id() -> str`

_Generate unique risk assessment ID._

#### `generate_risk_factor_id() -> str`

_Generate unique risk factor ID._

### `core/learning/adaptation.py`

#### class `AdaptationConfig` `@dataclass`

_Adaptasyon konfigurasyonu._

#### class `AdaptationRecord` `@dataclass`

_Adaptasyon kaydi._

#### class `BehaviorAdapter`

_Davranis adaptasyonu sinifi._

Methods:
- `__init__()`
- `suggest_pattern()`
- `should_explore()`
- `adapt_from_feedback()`
- `get_confidence()`
- `get_adaptations()`
- `stats()`
- `clear()`

### `core/learning/episode.py`

#### class `EpisodeOutcome` `@dataclass`

_Episode sonucu - Etkilesimin nasil sonuclandigini kaydeder._

Methods:
- `__post_init__()`
- `overall_score()`
- `has_positive_outcome()`

#### class `Episode` `@dataclass`

_Episode - Tek bir etkilesimin tam kaydi._

Methods:
- `__post_init__()`
- `success()`
- `word_count()`
- `has_emotion()`
- `dialogue_act_count()`
- `construction_count()`
- `to_dict()`
- `from_dict()`

#### class `EpisodeCollection` `@dataclass`

_Episode kolleksiyonu - Birden fazla episode'u gruplar._

Methods:
- `add()`
- `get_successful()`
- `get_by_intent()`
- `get_by_emotion()`
- `get_recent()`
- `success_rate()`
- `average_trust_delta()`

#### `generate_episode_id() -> str`

_Generate unique episode ID._

### `core/learning/episode_logger.py`

#### class `EpisodeLogger`

_Episode Logger - Progressive episode log building._

Methods:
- `__init__()`
- `start_episode()`
- `update_intent()`
- `update_context()`
- `update_decision()`
- `update_construction()`
- `update_output()`
- `update_risk()`
- `finalize_episode()`
- `add_feedback()`
- `add_feedback_to_last()`
- `get_session_episodes()`
- `reset_turn_number()`

### `core/learning/episode_store.py`

#### class `EpisodeStore`

_Episode Store Protocol - Storage interface for EpisodeLogs._

Methods:
- `save()`
- `get_by_id()`
- `get_recent()`
- `get_by_session()`
- `get_by_intent()`
- `get_by_act()`

#### class `JSONLEpisodeStore`

_JSONL-based Episode Store - Her satır bir JSON episode._

Methods:
- `__init__()`
- `save()`
- `get_by_id()`
- `get_recent()`
- `get_by_session()`
- `get_by_intent()`
- `get_by_act()`
- `get_all()`
- `count()`
- `clear()`
- `update_episode()`

### `core/learning/episode_types.py`

#### class `ConstructionSource` `(Enum)`

_Construction kaynağı - nereden geldi?_

#### class `ConstructionLevel` `(Enum)`

_Construction seviyesi - Construction Grammar teorisinden._

#### class `ApprovalStatus` `(Enum)`

_Approval durumu._

#### class `ImplicitFeedback` `@dataclass`

_Dolaylı geri bildirim sinyalleri._

Methods:
- `get_signal_score()`
- `to_dict()`

#### class `EpisodeLog` `@dataclass`

_Episode Log - Tek bir conversation turn'ünün kapsamlı kaydı._

Methods:
- `__post_init__()`
- `has_explicit_feedback()`
- `has_implicit_feedback()`
- `overall_feedback_score()`
- `is_successful()`
- `has_compound_intent()`
- `trust_delta()`
- `to_dict()`
- `from_dict()`

#### `generate_episode_log_id() -> str`

_Generate unique episode log ID._

### `core/learning/feedback.py`

#### class `FeedbackCollector`

_Kullanici geri bildirimi toplama ve yonetim sinifi._

Methods:
- `__init__()`
- `record()`
- `record_explicit()`
- `record_implicit()`
- `get_feedback()`
- `get_history()`
- `get_by_user()`
- `get_average_score()`
- `get_stats()`
- `clear()`

#### class `FeedbackWeighterConfig` `@dataclass`

_FeedbackWeighter konfigurasyonu._

#### class `ImplicitSignals` `@dataclass`

_Implicit (davranistan cikarilan) sinyaller._

Methods:
- `to_dict()`
- `from_dict()`

#### class `FeedbackWeighter`

_Feedback agirliklama sistemi (Alice uzlasisi)._

Methods:
- `__init__()`
- `compute_feedback_score()`
- `extract_explicit_feedback()`
- `extract_implicit_signals()`
- `compute_implicit_value()`
- `aggregate_episode_feedback()`
- `get_feedback_breakdown()`
- `is_positive_feedback()`
- `is_negative_feedback()`

### `core/learning/feedback_aggregator.py`

#### class `FeedbackAggregator`

_Episode loglarından construction stats hesaplar._

Methods:
- `aggregate()`
- `aggregate_incremental()`
- `get_summary()`

### `core/learning/feedback_scorer.py`

#### `compute_wins_losses(stats) -> Tuple[...]`

_Ağırlıklı win/loss hesapla._

#### `compute_feedback_mean(wins, losses) -> float`

_Bayesian Beta ortalaması hesapla._

#### `compute_influence(total_uses) -> float`

_Az veri varken feedback etkisini azalt._

#### `compute_adjustment(stats) -> float`

_Base score için çarpan hesapla._

#### `compute_final_score(base_score, stats) -> Tuple[...]`

_Final skor hesapla ve açıklama metadata'sı döndür._

#### `explain_score(base_score, stats) -> str`

_Skor hesaplamasını açıkla (debugging/logging için)._

#### `is_score_significant(stats, threshold) -> bool`

_Feedback skoru anlamlı mı? (Nötrden yeterince farklı mı?)_

#### `get_feedback_summary(stats) -> Dict`

_Kısa feedback özeti (UI için)._

### `core/learning/feedback_stats.py`

#### class `ConstructionStats` `@dataclass`

_Bir construction için feedback istatistikleri._

Methods:
- `to_dict()`
- `from_dict()`
- `total_explicit()`
- `total_implicit()`
- `total_feedback()`
- `explicit_ratio()`
- `implicit_ratio()`

### `core/learning/feedback_store.py`

#### class `FeedbackStore`

_Construction feedback istatistiklerini JSON'da saklar._

Methods:
- `__init__()`
- `get_stats()`
- `update_stats()`
- `bulk_update()`
- `get_all()`
- `clear()`
- `count()`
- `get_top_constructions()`
- `get_most_used()`

### `core/learning/generalization.py`

#### class `RuleExtractor`

_Pattern'lerden kural cikarma sinifi._

Methods:
- `__init__()`
- `extract_rules()`
- `get_rule()`
- `get_all_rules()`
- `get_rules_by_type()`
- `apply_rule()`
- `find_matching_rule()`
- `clear()`
- `stats()`

### `core/learning/mdl.py`

#### class `MDLConfig` `@dataclass`

_ApproximateMDL konfigurasyonu._

#### class `MDLScore` `@dataclass`

_MDL degerlendirme sonucu._

Methods:
- `__post_init__()`
- `is_good_pattern()`
- `is_risky()`

#### class `ApproximateMDL`

_Minimum Description Length yaklasik hesaplayici._

Methods:
- `__init__()`
- `compute_compression_score()`
- `compute_pattern_length()`
- `compute_episode_length()`
- `evaluate_candidate()`
- `compare_patterns()`
- `rank_patterns()`
- `filter_good_patterns()`
- `get_score_breakdown()`

### `core/learning/pattern_analyzer.py`

#### class `PatternAnalyzer`

_Episode verilerinden pattern analizi yapar._

Methods:
- `__init__()`
- `analyze_intent_frequency()`
- `analyze_act_frequency()`
- `analyze_construction_usage()`
- `analyze_feedback_correlation()`
- `analyze_act_feedback_correlation()`
- `analyze_fallback_rate()`
- `analyze_session_stats()`
- `analyze_feedback_summary()`
- `generate_recommendations()`
- `generate_report()`

#### `create_analyzer(filepath) -> PatternAnalyzer`

_Helper function to create a PatternAnalyzer._

### `core/learning/patterns.py`

#### class `PatternStorage`

_Davranis patternleri depolama ve yonetim sinifi._

Methods:
- `__init__()`
- `store()`
- `get()`
- `find_similar()`
- `update_stats()`
- `get_best_patterns()`
- `get_worst_patterns()`
- `prune_weak_patterns()`
- `count()`
- `stats()`
- `clear()`
- `get_all()`

### `core/learning/persistence/feedback_repo.py`

#### class `FeedbackRepository`

_Repository for feedback persistence operations._

Methods:
- `__init__()`
- `save()`
- `get()`
- `get_by_interaction()`
- `get_by_user()`
- `get_recent()`
- `get_all()`
- `delete()`
- `count()`
- `get_stats()`
- `get_average_score()`
- `clear()`

### `core/learning/persistence/pattern_repo.py`

#### class `PatternRepository`

_Repository for pattern persistence operations._

Methods:
- `__init__()`
- `save()`
- `get()`
- `get_all()`
- `update()`
- `delete()`
- `find_by_type()`
- `get_top_patterns()`
- `count()`
- `get_stats()`
- `clear()`

### `core/learning/processor.py`

#### class `LearningProcessor`

_Ana ogrenme koordinatoru._

Methods:
- `__init__()`
- `learn_from_interaction()`
- `suggest_response()`
- `get_learning_rate()`
- `get_improvement()`
- `get_pattern_for_context()`
- `reinforce_from_feedback()`
- `extract_rules()`
- `generate_from_rule()`
- `get_rules()`
- `stats()`
- `clear()`

### `core/learning/reinforcement.py`

#### class `RewardConfig` `@dataclass`

_Reward hesaplama konfigurasyonu._

#### class `RewardCalculator`

_Feedback'ten reward hesaplayan sinif._

Methods:
- `__init__()`
- `calculate()`
- `calculate_cumulative()`
- `apply_decay()`

#### class `Reinforcer`

_Pattern reinforcement sinifi._

Methods:
- `__init__()`
- `reinforce()`
- `reinforce_similar()`
- `get_history()`
- `get_total_reward()`
- `stats()`
- `clear_history()`

### `core/learning/similarity.py`

#### class `SimilarityConfig` `@dataclass`

_EpisodeSimilarity konfigurasyonu._

Methods:
- `__post_init__()`

#### class `SimilarityResult` `@dataclass`

_Benzerlik hesaplama sonucu._

#### class `EpisodeSimilarity`

_Episode benzerlik hesaplayici._

Methods:
- `__init__()`
- `compute()`
- `compute_detailed()`
- `compute_batch()`
- `find_similar()`
- `find_cluster_candidates()`
- `get_similarity_breakdown()`

#### `jaccard_similarity(set1, set2) -> float`

_Jaccard similarity hesapla._

#### `levenshtein_distance(s1, s2) -> int`

_Levenshtein (edit) mesafesi hesapla._

#### `levenshtein_similarity(s1, s2) -> float`

_Normalize Levenshtein benzerligi hesapla._

### `core/learning/types.py`

#### class `FeedbackType` `(Enum)`

_Geri bildirim turleri._

#### class `PatternType` `(Enum)`

_Davranis pattern turleri._

#### class `Feedback` `@dataclass`

_Geri bildirim kaydi._

Methods:
- `__post_init__()`

#### class `Pattern` `@dataclass`

_Ogrenilen davranis patterni._

Methods:
- `success_rate()`
- `average_reward()`
- `total_uses()`

#### class `LearningOutcome` `@dataclass`

_Ogrenme sonucu._

#### class `Rule` `@dataclass`

_Genellestirilmis kural - pattern'lerden cikarilmis template._

Methods:
- `__post_init__()`

#### `generate_feedback_id() -> str`

_Generate unique feedback ID._

#### `generate_pattern_id() -> str`

_Generate unique pattern ID._

#### `generate_rule_id() -> str`

_Generate unique rule ID._

### `core/memory/conversation.py`

#### class `ConversationConfig` `@dataclass`

_Conversation memory yapilandirmasi._

#### class `ConversationMemory`

_Conversation Memory - Sohbet gecmisi yonetimi._

Methods:
- `__init__()`
- `start_conversation()`
- `end_conversation()`
- `get_active_session()`
- `get_conversation()`
- `add_turn()`
- `get_context()`
- `get_full_history()`
- `get_last_n_turns()`
- `format_context_for_llm()`
- `search_history()`
- `search_by_topic()`
- `search_by_emotion()`
- `conversation_to_episode()`
- `cleanup_inactive_sessions()`
- `get_user_conversations()`
- `stats()`
- `debug_dump()`

#### `get_conversation_memory(config) -> ConversationMemory`

_Conversation memory singleton._

#### `reset_conversation_memory() -> None`

_Reset conversation memory singleton (test icin)._

#### `create_conversation_memory(config) -> ConversationMemory`

_Yeni conversation memory olustur (test icin)._

### `core/memory/embeddings.py`

#### class `LRUCache`

_Simple LRU cache for embeddings._

Methods:
- `__init__()`
- `get()`
- `put()`
- `clear()`
- `stats()`

#### class `EmbeddingEncoder`

_Embedding Encoder - Metin vektorlestirme._

Methods:
- `__init__()`
- `model()`
- `encode()`
- `encode_batch()`
- `get_dimension()`
- `clear_cache()`
- `cache_stats()`
- `stats()`
- `is_model_loaded()`

#### `cosine_similarity(a, b) -> float`

_Compute cosine similarity between two vectors._

#### `batch_cosine_similarity(query, vectors) -> np.ndarray`

_Compute cosine similarity between query and multiple vectors._

#### `top_k_indices(similarities, k, min_threshold) -> List[...]`

_Get top-k indices with highest similarity scores._

#### `euclidean_distance(a, b) -> float`

_Compute Euclidean distance between two vectors._

#### `normalize_vector(v) -> np.ndarray`

_L2 normalize a vector._

#### `get_embedding_encoder(config) -> EmbeddingEncoder`

_Get embedding encoder singleton._

#### `reset_embedding_encoder() -> None`

_Reset embedding encoder singleton (test icin)._

#### `create_embedding_encoder(config) -> EmbeddingEncoder`

_Create new embedding encoder (test icin)._

### `core/memory/persistence/conversation_repo.py`

#### class `ConversationRepository`

_Repository for conversation persistence operations._

Methods:
- `__init__()`
- `create_conversation()`
- `get_conversation()`
- `get_conversation_by_session()`
- `get_active_session()`
- `end_conversation()`
- `touch_conversation()`
- `find_user_conversations()`
- `find_recent_conversations()`
- `find_conversations_by_topic()`
- `cleanup_inactive_sessions()`
- `add_turn()`
- `get_turn()`
- `get_context_window()`
- `get_full_history()`
- `search_history()`
- `search_by_emotion()`
- `search_by_intent()`
- `apply_decay()`
- `cleanup_weak_conversations()`
- `get_stats()`

### `core/memory/persistence/models.py`

#### class `MemoryTypeEnum` `(Enum)`

#### class `RelationshipTypeEnum` `(Enum)`

#### class `InteractionTypeEnum` `(Enum)`

#### class `EpisodeTypeEnum` `(Enum)`

#### class `EpisodeModel`

_Episodic memory - olay kaydı._

Methods:
- `to_dict()`

#### class `RelationshipModel`

_Relationship memory - agent ile ilişki kaydı._

Methods:
- `to_dict()`

#### class `InteractionModel`

_Single interaction record._

Methods:
- `to_dict()`

#### class `SemanticFactModel`

_Semantic memory - subject-predicate-object facts._

Methods:
- `to_dict()`

#### class `EmotionalMemoryModel`

_Emotional memory - affect-tagged memories._

Methods:
- `to_dict()`

#### class `TrustHistoryModel`

_Trust history - trust score changes over time._

Methods:
- `to_dict()`

#### class `CycleMetricModel`

_Cycle metrics - monitoring dashboard için._

Methods:
- `to_dict()`

#### class `ActivityLogModel`

_Activity log - dashboard için event logları._

Methods:
- `to_dict()`

#### class `ConversationModel`

_Conversation memory - sohbet oturumu._

Methods:
- `to_dict()`

#### class `PatternTypeEnum` `(Enum)`

_Pattern type enum for database._

#### class `PatternModel`

_Learning pattern - ogrenilen davranis patterni._

Methods:
- `to_dict()`

#### class `FeedbackTypeEnum` `(Enum)`

_Feedback type enum for database._

#### class `FeedbackModel`

_Learning feedback - geri bildirim kaydi._

Methods:
- `to_dict()`

#### class `DialogueTurnModel`

_Dialogue turn - tek bir mesaj._

Methods:
- `to_dict()`

### `core/memory/persistence/repository.py`

#### class `MemoryRepository`

_Repository for Memory module persistence operations._

Methods:
- `__init__()`
- `save_episode()`
- `get_episode()`
- `find_episodes_by_participant()`
- `find_recent_episodes()`
- `find_episodes_by_type()`
- `find_important_episodes()`
- `touch_episode()`
- `delete_episode()`
- `save_relationship()`
- `get_relationship()`
- `get_relationship_by_agent()`
- `get_or_create_relationship()`
- `find_relationships_by_type()`
- `find_high_trust_relationships()`
- `find_low_trust_relationships()`
- `update_relationship_stats()`
- `save_interaction()`
- `find_interactions_for_relationship()`
- `find_recent_interactions()`
- `save_fact()`
- `find_facts_by_subject()`
- `find_facts_by_predicate()`
- `query_facts()`
- `save_emotional_memory()`
- `find_emotional_memories_by_emotion()`
- `find_flashbulb_memories()`
- `find_intense_emotional_memories()`
- `save_trust_history()`
- `record_trust_change()`
- `get_trust_history()`
- `apply_decay()`
- `cleanup_weak_memories()`
- `get_stats()`

#### `get_database_url() -> str`

_Get database URL from environment or use default._

#### `get_engine(database_url) -> Engine`

_Get or create SQLAlchemy engine._

#### `get_session(engine) -> Session`

_Get a new database session._

#### `init_db(engine) -> None`

_Initialize database tables._

### `core/memory/semantic.py`

#### class `IndexEntry` `@dataclass`

_Internal index entry._

#### class `SemanticMemory`

_Semantic Memory - Embedding bazli arama._

Methods:
- `__init__()`
- `encoder()`
- `add()`
- `add_batch()`
- `remove()`
- `clear()`
- `count()`
- `contains()`
- `search()`
- `search_by_source()`
- `search_similar_to_id()`
- `index_episode()`
- `index_dialogue_turn()`
- `index_conversation()`
- `save()`
- `load()`
- `stats()`

#### `get_semantic_memory(encoder) -> SemanticMemory`

_Get semantic memory singleton._

#### `reset_semantic_memory() -> None`

_Reset semantic memory singleton (test icin)._

#### `create_semantic_memory(encoder) -> SemanticMemory`

_Create new semantic memory (test icin)._

### `core/memory/store.py`

#### class `MemoryConfig` `@dataclass`

_Memory sistem yapilandirmasi._

#### class `MemoryStore`

_Ana memory store - facade pattern._

Methods:
- `__init__()`
- `close()`
- `buffer_sensory()`
- `get_sensory_buffer()`
- `hold_in_working()`
- `get_working_memory()`
- `clear_working_memory()`
- `store_episode()`
- `get_episode()`
- `recall_episodes()`
- `recall_similar_episodes()`
- `get_relationship()`
- `update_relationship()`
- `record_interaction()`
- `get_interaction_history()`
- `is_known_agent()`
- `get_all_relationships()`
- `store_fact()`
- `query_facts()`
- `get_concept()`
- `add_concept()`
- `store_emotional_memory()`
- `recall_by_emotion()`
- `recall_by_trigger()`
- `run_consolidation()`
- `apply_decay()`
- `retrieve()`
- `stats()`
- `debug_dump()`

#### `get_memory_store(config) -> MemoryStore`

_Memory store singleton._

#### `reset_memory_store() -> None`

_Reset memory store singleton (test icin)._

#### `create_memory_store(config) -> MemoryStore`

_Yeni memory store olustur (test icin)._

### `core/memory/types.py`

#### class `MemoryType` `(Enum)`

_Bellek turu._

#### class `EmotionalValence` `(Enum)`

_Duygusal degerlik._

#### class `RelationshipType` `(Enum)`

_Iliski turu._

#### class `InteractionType` `(Enum)`

_Etkilesim turu._

#### class `EpisodeType` `(Enum)`

_Olay turu._

#### class `MemoryItem` `@dataclass`

_Tum memory ogelerinin base class'i._

Methods:
- `touch()`
- `decay()`
- `is_forgotten()`

#### class `SensoryTrace` `@dataclass`

_Duyusal iz - cok kisa sureli (ms-saniye)._

#### class `WorkingMemoryItem` `@dataclass`

_Calisma bellegi ogesi - aktif islem icin (7+-2 limit)._

#### class `Episode` `@dataclass`

_Olay kaydi - ne, nerede, ne zaman, kim._

#### class `EpisodeSummary` `@dataclass`

_Episode ozeti - hizli erisim icin._

#### class `SemanticFact` `@dataclass`

_Anlamsal bilgi - genel bilgi, kavramlar._

#### class `ConceptNode` `@dataclass`

_Kavram dugumu - semantic network icin._

#### class `EmotionalMemory` `@dataclass`

_Duygusal ani - affect-tagged memory._

#### class `Interaction` `@dataclass`

_Tek bir etkilesim kaydi._

#### class `RelationshipRecord` `@dataclass`

_Iliski kaydi - bir agent ile tum gecmis._

Methods:
- `add_interaction()`
- `get_trust_recommendation()`

#### class `ConsolidationTask` `@dataclass`

_Bellek pekistirme gorevi._

#### class `MemoryQuery` `@dataclass`

_Bellek sorgusu._

#### class `RetrievalResult` `@dataclass`

_Bellek getirme sonucu._

#### class `DialogueTurn` `@dataclass`

_Tek bir diyalog turu - kullanici veya ajan mesaji._

#### class `Conversation` `@dataclass`

_Sohbet oturumu - DialogueTurn'lerin koleksiyonu._

Methods:
- `add_turn()`
- `get_last_n_turns()`
- `get_context_window()`
- `end_conversation()`
- `get_duration_seconds()`
- `to_text()`

#### class `EmbeddingModel` `(Enum)`

_Desteklenen embedding modelleri._

#### class `SourceType` `(Enum)`

_Semantic memory kaynak turu._

#### class `EmbeddingConfig` `@dataclass`

_Embedding encoder yapilandirmasi._

#### class `EmbeddingResult` `@dataclass`

_Semantic search sonucu._

### `core/perception/extractor.py`

#### class `ExtractorConfig` `@dataclass`

_Feature extractor yapilandirmasi._

#### class `VisualFeatureExtractor`

_Gorsel ozellik cikarici._

Methods:
- `__init__()`
- `extract()`

#### class `AuditoryFeatureExtractor`

_Isitsel ozellik cikarici._

Methods:
- `__init__()`
- `extract()`

#### class `MotionFeatureExtractor`

_Hareket ozellik cikarici._

Methods:
- `__init__()`
- `extract()`

#### class `AgentExtractor`

_Ajan algilama ve ozellik cikarma._

Methods:
- `__init__()`
- `extract_from_input()`

#### class `ThreatExtractor`

_Tehdit degerlendirmesi cikarici._

Methods:
- `__init__()`
- `extract()`

#### class `FeatureExtractor`

_Ana ozellik cikarici - tum alt cikaricilari koordine eder._

Methods:
- `__init__()`
- `extract_all()`
- `extract_visual()`
- `extract_auditory()`
- `extract_threat()`

### `core/perception/filters.py`

#### class `FilterConfig` `@dataclass`

_Filtre yapilandirmasi._

#### class `AttentionFilter`

_Dikkat yonlendirme ve filtreleme._

Methods:
- `__init__()`
- `calculate_attention()`
- `filter_by_attention()`

#### class `NoiseFilter`

_Gurultu azaltma filtresi._

Methods:
- `__init__()`
- `filter()`
- `filter_batch()`
- `calculate_signal_quality()`

#### class `SalienceFilter`

_Belirginlik filtresi._

Methods:
- `__init__()`
- `filter_by_salience()`
- `calculate_agent_salience()`

#### class `PerceptionFilterPipeline`

_Tum filtreleri birlestiren pipeline._

Methods:
- `__init__()`
- `apply()`

### `core/perception/processor.py`

#### class `ProcessorConfig` `@dataclass`

_PerceptionProcessor yapilandirmasi._

#### class `PerceptionProcessor`

_Ana perception islemcisi._

Methods:
- `__init__()`
- `process()`
- `process_stimulus()`
- `sense()`
- `attend()`
- `perceive()`
- `stats()`
- `reset_stats()`

#### `get_perception_processor(config) -> PerceptionProcessor`

_Default perception processor'i getir veya olustur._

#### `reset_perception_processor() -> None`

_Default processor'i sifirla._

### `core/perception/types.py`

#### class `SensoryModality` `(Enum)`

_Duyusal modalite turleri._

#### class `PerceptualCategory` `(Enum)`

_Algilanan nesne kategorileri._

#### class `ThreatLevel` `(Enum)`

_Tehdit seviyesi._

#### class `AgentDisposition` `(Enum)`

_Ajan tavir/tutumu._

#### class `EmotionalExpression` `(Enum)`

_Yuz ifadesi / duygusal gosterge._

#### class `BodyLanguage` `(Enum)`

_Vucut dili._

#### class `VisualFeatures` `@dataclass`

_Gorsel ozellikler._

#### class `AuditoryFeatures` `@dataclass`

_Isitsel ozellikler._

#### class `MotionFeatures` `@dataclass`

_Hareket ozellikleri (proprioceptive + visual motion)._

#### class `SensoryData` `@dataclass`

_Birlesik duyusal veri._

#### class `PerceptualInput` `@dataclass`

_Ham algi girdisi - SENSE fazina giren veri._

Methods:
- `get_modality()`
- `has_modality()`

#### class `PerceivedAgent` `@dataclass`

_Algilanan ajan - baska bir UEM veya canli varlik._

#### class `ThreatAssessment` `@dataclass`

_Tehdit degerlendirmesi - perception'in kritik ciktisi._

Methods:
- `is_threatening()`
- `requires_immediate_action()`

#### class `AttentionFocus` `@dataclass`

_Dikkat odagi - neye odaklaniliyor._

#### class `PerceptualFeatures` `@dataclass`

_Cikarilmis ozellikler - PERCEIVE fazinin ana ciktisi._

Methods:
- `get_primary_agent()`
- `get_threatening_agents()`

#### class `PerceptualOutput` `@dataclass`

_Perception modulunun tam ciktisi._

Methods:
- `to_dict()`

### `core/self/goals.py`

#### class `PersonalGoalConfig` `@dataclass`

_Kisisel hedef modulu yapilandirmasi._

#### class `PersonalGoalManager`

_Kisisel hedef yoneticisi._

Methods:
- `__init__()`
- `create_goal()`
- `create_goal_from_value()`
- `create_goal_from_need()`
- `get_goal()`
- `get_active_goals()`
- `get_goals_by_domain()`
- `get_highest_motivation_goal()`
- `get_goals_by_value()`
- `get_goals_by_need()`
- `get_stale_goals()`
- `update_progress()`
- `achieve_milestone()`
- `increment_progress()`
- `complete_goal()`
- `abandon_goal()`
- `reactivate_goal()`
- `update_commitment()`
- `boost_intrinsic_motivation()`
- `get_motivation_report()`
- `prioritize_goals()`
- `suggest_focus_goal()`
- `apply_progress_decay()`
- `get_stats()`
- `get_completion_rate()`
- `summary()`

#### `create_personal_goal_manager(config) -> PersonalGoalManager`

_PersonalGoalManager factory._

### `core/self/identity/__init__.py`

#### class `IdentityConfig` `@dataclass`

_Kimlik modulu yapilandirmasi._

#### class `IdentityManager`

_Kimlik yoneticisi._

Methods:
- `__init__()`
- `initialize_identity()`
- `add_trait()`
- `remove_trait()`
- `reinforce_trait()`
- `challenge_trait()`
- `find_trait_by_name()`
- `add_role()`
- `remove_role()`
- `set_primary_role()`
- `add_capability()`
- `remove_capability()`
- `add_limitation()`
- `has_capability()`
- `check_identity_stability()`
- `get_identity_conflicts()`
- `generate_self_description()`
- `apply_trait_decay()`
- `get_stats()`
- `get_trait_history()`
- `get_identity()`
- `to_dict()`

#### `create_identity_manager(config) -> IdentityManager`

_IdentityManager factory._

#### `create_default_identity(name, description) -> Identity`

_Varsayilan kimlik olustur._

### `core/self/needs.py`

#### class `NeedConfig` `@dataclass`

_Ihtiyac modulu yapilandirmasi._

#### class `NeedManager`

_Ihtiyac yoneticisi._

Methods:
- `__init__()`
- `initialize_default_needs()`
- `add_need()`
- `remove_need()`
- `get_need()`
- `get_need_by_name()`
- `get_needs_by_level()`
- `get_unsatisfied_needs()`
- `get_critical_needs()`
- `get_satisfied_needs()`
- `get_most_pressing_need()`
- `prioritize_needs()`
- `satisfy_need()`
- `deprive_need()`
- `satisfy_need_by_name()`
- `check_hierarchy_satisfaction()`
- `get_active_level()`
- `is_level_blocked()`
- `apply_time_decay()`
- `calculate_drive()`
- `get_dominant_drive()`
- `get_stats()`
- `get_overall_wellbeing()`
- `summary()`

#### `get_default_needs() -> List[...]`

_Varsayilan ihtiyaclar (Maslow hiyerarsisi)._

#### `create_need_manager(config, initialize_defaults) -> NeedManager`

_NeedManager factory._

### `core/self/processor.py`

#### class `SelfProcessorConfig` `@dataclass`

_Self processor yapilandirmasi._

#### class `SelfOutput` `@dataclass`

_Self processing ciktisi._

#### class `SelfProcessor`

_Benlik islemcisi._

Methods:
- `__init__()`
- `process()`
- `add_narrative_element()`
- `express_value()`
- `satisfy_need()`
- `reinforce_trait()`
- `progress_goal()`
- `get_self_description()`
- `get_stats()`
- `get_self_state()`
- `summary()`

#### `create_self_processor(config) -> SelfProcessor`

_SelfProcessor factory._

#### `get_self_processor() -> SelfProcessor`

_Singleton benzeri global processor._

### `core/self/types.py`

#### class `IdentityAspect` `(Enum)`

_Kimlik boyutlari._

#### class `ValueCategory` `(Enum)`

_Deger kategorileri._

#### class `ValuePriority` `(Enum)`

_Deger onceligi._

#### class `NeedLevel` `(Enum)`

_Maslow ihtiyac seviyeleri._

#### class `NeedStatus` `(Enum)`

_Ihtiyac durumu._

#### class `GoalDomain` `(Enum)`

_Kisisel hedef alanlari._

#### class `IntegrityStatus` `(Enum)`

_Tutarlilik durumu._

#### class `NarrativeType` `(Enum)`

_Hikaye turleri._

#### class `Value` `@dataclass`

_Bir deger temsili._

Methods:
- `priority_weight()`
- `integrity_score()`
- `express()`
- `violate()`

#### class `Need` `@dataclass`

_Bir ihtiyac temsili (Maslow hiyerarsisi)._

Methods:
- `priority_score()`
- `update_satisfaction()`
- `deprive()`
- `satisfy()`

#### class `PersonalGoal` `@dataclass`

_Kisisel bir hedef temsili._

Methods:
- `total_motivation()`
- `milestone_progress()`
- `achieve_milestone()`
- `update_progress()`

#### class `IdentityTrait` `@dataclass`

_Bir kimlik ozelligi._

Methods:
- `resilience()`
- `reinforce()`
- `challenge()`

#### class `Identity` `@dataclass`

_Kimlik temsili._

Methods:
- `add_trait()`
- `get_trait()`
- `get_traits_by_aspect()`
- `get_core_identity()`
- `add_role()`
- `identity_strength()`
- `identity_stability()`

#### class `NarrativeElement` `@dataclass`

_Kisisel hikayedeki bir oge._

Methods:
- `significance()`

#### class `SelfState` `@dataclass`

_Agent'in benlik durumu - tum benlik bilgilerinin butunu._

Methods:
- `add_value()`
- `get_value()`
- `get_core_values()`
- `get_values_by_category()`
- `add_need()`
- `get_need()`
- `get_needs_by_level()`
- `get_unsatisfied_needs()`
- `get_critical_needs()`
- `get_most_pressing_need()`
- `add_personal_goal()`
- `get_personal_goal()`
- `get_active_personal_goals()`
- `add_narrative_element()`
- `get_significant_narratives()`
- `check_integrity()`
- `summary()`

### `core/self/values/__init__.py`

#### class `ValueSystemConfig` `@dataclass`

_Deger sistemi yapilandirmasi._

#### class `ValueSystem`

_Deger sistemi yoneticisi._

Methods:
- `__init__()`
- `initialize_default_values()`
- `add_value()`
- `remove_value()`
- `get_value()`
- `get_value_by_name()`
- `get_core_values()`
- `get_sacred_values()`
- `get_values_by_category()`
- `get_values_by_priority()`
- `express_value()`
- `violate_value()`
- `express_value_by_name()`
- `detect_conflicts()`
- `resolve_conflict()`
- `prioritize_values()`
- `get_dominant_value()`
- `check_action_alignment()`
- `calculate_value_integrity()`
- `get_integrity_report()`
- `get_stats()`
- `get_value_history()`
- `summary()`

#### `get_default_values() -> List[...]`

_Varsayilan degerler._

#### `create_value_system(config, initialize_defaults) -> ValueSystem`

_ValueSystem factory._

### `core/utils/text.py`

#### `normalize_turkish(text) -> str`

_Normalize Turkish text by converting Turkish characters to ASCII and lowercasing._

#### `normalize_for_matching(text) -> str`

_Normalize text for pattern matching._

## Engine Modules

### `engine/cycle.py`

#### class `CycleConfig` `@dataclass`

_Cycle yapılandırması._

#### class `CycleState` `@dataclass`

_Cycle'ın anlık durumu._

Methods:
- `duration_ms()`
- `is_complete()`

#### class `CognitiveCycle`

_10-Phase Cognitive Cycle._

Methods:
- `__init__()`
- `register_handler()`
- `run()`
- `cycle_count()`
- `current_state()`
- `get_stats()`
- `metrics_history()`
- `current_metrics()`
- `print_summary()`

### `engine/events/bus.py`

#### class `EventType` `(Enum)`

_Sistem event tipleri._

#### class `Event` `@dataclass`

_Sistem event'i._

#### class `EventBus`

_Merkezi event bus - Pub/Sub pattern._

Methods:
- `__init__()`
- `subscribe()`
- `subscribe_all()`
- `unsubscribe()`
- `publish()`
- `emit()`
- `pause()`
- `resume()`
- `clear_history()`
- `get_history()`
- `stats()`

#### `get_event_bus() -> EventBus`

_Default event bus instance'ını getir._

#### `reset_event_bus() -> None`

_Event bus'ı sıfırla (test için)._

### `engine/handlers/__init__.py`

#### `register_all_handlers(cycle, configs)`

_Tüm handler'ları cycle'a kaydet._

### `engine/handlers/affect.py`

#### class `AffectPhaseConfig` `@dataclass`

_FEEL fazı yapılandırması._

#### class `AffectPhaseState` `@dataclass`

_FEEL fazı için tutulan state._

#### class `AffectPhaseHandler`

_FEEL fazı handler'ı._

Methods:
- `__init__()`
- `stats()`
- `get_last_result()`

#### `create_feel_handler(config) -> AffectPhaseHandler`

_FEEL fazı handler'ı oluştur._

#### `simple_feel_handler(phase, state, context) -> PhaseResult`

_Basit FEEL handler - threat'ten valence hesaplar._

### `engine/handlers/cognition.py`

#### class `CognitionHandlerConfig` `@dataclass`

_Cognition handler'ları yapılandırması._

#### class `ReasonPhaseHandler`

_REASON fazı handler'ı._

Methods:
- `__init__()`

#### class `EvaluatePhaseHandler`

_EVALUATE fazı handler'ı._

Methods:
- `__init__()`

#### `create_reason_handler(config, processor) -> ReasonPhaseHandler`

_REASON fazı handler'ı oluştur._

#### `create_evaluate_handler(config, processor) -> EvaluatePhaseHandler`

_EVALUATE fazı handler'ı oluştur._

#### `create_cognition_handlers(config) -> Dict[...]`

_Tüm cognition handler'larını oluştur._

### `engine/handlers/executive.py`

#### class `ExecutiveConfig` `@dataclass`

_Executive fazları yapılandırması._

#### class `DecidePhaseHandler`

_DECIDE fazı handler'ı._

Methods:
- `__init__()`

#### class `ActPhaseHandler`

_ACT fazı handler'ı._

#### `create_decide_handler(config) -> DecidePhaseHandler`

_DECIDE fazı handler'ı oluştur._

#### `create_act_handler() -> ActPhaseHandler`

_ACT fazı handler'ı oluştur._

### `engine/handlers/memory.py`

#### class `RetrievePhaseConfig` `@dataclass`

_RETRIEVE fazı yapılandırması._

#### class `RetrieveHandlerState` `@dataclass`

_Handler durumu._

#### class `RetrievePhaseHandler`

_RETRIEVE fazı - bellek getirme._

Methods:
- `__init__()`
- `stats()`

#### `create_retrieve_handler(config) -> RetrievePhaseHandler`

_RETRIEVE handler oluştur._

### `engine/handlers/perception.py`

#### class `PerceptionHandlerConfig` `@dataclass`

_Perception handler'lari yapilandirmasi._

#### class `SensePhaseHandler`

_SENSE fazi handler'i._

Methods:
- `__init__()`

#### class `AttendPhaseHandler`

_ATTEND fazi handler'i._

Methods:
- `__init__()`

#### class `PerceivePhaseHandler`

_PERCEIVE fazi handler'i._

Methods:
- `__init__()`

#### class `LegacyPerceivePhaseHandler`

_Eski PERCEIVE handler (geri uyumluluk icin)._

Methods:
- `__init__()`

#### `create_sense_handler(config, processor) -> SensePhaseHandler`

_SENSE fazi handler'i olustur._

#### `create_attend_handler(config, processor) -> AttendPhaseHandler`

_ATTEND fazi handler'i olustur._

#### `create_perceive_handler(config, processor) -> PerceivePhaseHandler`

_PERCEIVE fazi handler'i olustur._

#### `create_legacy_perceive_handler(config) -> LegacyPerceivePhaseHandler`

_Legacy PERCEIVE handler olustur (geri uyumluluk)._

### `engine/phases/definitions.py`

#### class `Phase` `(Enum)`

_10-Phase Cognitive Cycle._

Methods:
- `ordered()`
- `get_module()`

#### class `PhaseConfig` `@dataclass`

_Faz yapılandırması._

#### class `PhaseResult` `@dataclass`

_Tek bir fazın sonucu._

Methods:
- `status_str()`

## Meta Modules

### `meta/consciousness/attention.py`

#### class `AttentionConfig` `@dataclass`

_Dikkat modulu yapilandirmasi._

#### class `AttentionFilter` `@dataclass`

_Dikkat filtresi._

Methods:
- `is_blocked()`
- `is_inhibited()`
- `add_inhibition()`
- `clear_expired_inhibitions()`

#### class `AttentionController`

_Dikkat kontrolcusu._

Methods:
- `__init__()`
- `focus_on()`
- `capture_attention()`
- `divide_attention()`
- `consolidate_attention()`
- `get_current_focus()`
- `get_divided_focuses()`
- `get_mode()`
- `is_focused()`
- `is_divided()`
- `sustain_focus()`
- `release_focus()`
- `apply_decay()`
- `check_timeout()`
- `block_type()`
- `unblock_type()`
- `set_min_priority()`
- `get_history()`
- `get_recent_targets()`
- `get_stats()`
- `summary()`

#### `create_attention_controller(config) -> AttentionController`

_AttentionController factory._

### `meta/consciousness/awareness.py`

#### class `AwarenessConfig` `@dataclass`

_Farkindalik modulu yapilandirmasi._

#### class `AwarenessManager`

_Farkindalik yoneticisi._

Methods:
- `__init__()`
- `get_awareness()`
- `get_all_awareness()`
- `get_awareness_level()`
- `update_awareness()`
- `boost_awareness()`
- `diminish_awareness()`
- `refresh_awareness()`
- `get_consciousness_level()`
- `get_overall_awareness()`
- `check_meta_awareness()`
- `apply_decay()`
- `get_dominant_awareness()`
- `get_weak_awareness_types()`
- `is_conscious()`
- `is_aware_of()`
- `get_history()`
- `get_stats()`
- `summary()`

#### `create_awareness_manager(config) -> AwarenessManager`

_AwarenessManager factory._

### `meta/consciousness/integration.py`

#### class `GlobalWorkspaceConfig` `@dataclass`

_Global Workspace yapilandirmasi._

#### class `BroadcastListener` `@dataclass`

_Yayin dinleyicisi._

Methods:
- `accepts()`

#### class `GlobalWorkspace`

_Global Workspace - Bilinc entegrasyon merkezi._

Methods:
- `__init__()`
- `submit_content()`
- `run_competition()`
- `get_top_competitors()`
- `integrate_content()`
- `broadcast()`
- `broadcast_all_pending()`
- `register_listener()`
- `unregister_listener()`
- `cleanup()`
- `process_cycle()`
- `get_state()`
- `get_active_contents()`
- `get_contents_by_type()`
- `get_broadcast_history()`
- `get_stats()`
- `summary()`

#### `create_global_workspace(config) -> GlobalWorkspace`

_GlobalWorkspace factory._

### `meta/consciousness/processor.py`

#### class `ConsciousnessConfig` `@dataclass`

_Bilinc islemcisi yapilandirmasi._

#### class `ConsciousnessOutput` `@dataclass`

_Bilinc islemcisi ciktisi._

#### class `ConsciousnessProcessor`

_Bilinc islemcisi._

Methods:
- `__init__()`
- `process()`
- `focus_on()`
- `release_attention()`
- `update_awareness()`
- `broadcast_content()`
- `register_broadcast_listener()`
- `is_conscious()`
- `get_consciousness_level()`
- `get_overall_awareness()`
- `get_current_focus()`
- `get_experiences()`
- `get_stats()`
- `summary()`

#### `create_consciousness_processor(config) -> ConsciousnessProcessor`

_ConsciousnessProcessor factory._

#### `get_consciousness_processor() -> ConsciousnessProcessor`

_Singleton benzeri global processor._

### `meta/consciousness/types.py`

#### class `ConsciousnessLevel` `(Enum)`

_Bilinc seviyeleri._

#### class `AwarenessType` `(Enum)`

_Farkindalik turleri._

#### class `AttentionMode` `(Enum)`

_Dikkat modlari._

#### class `AttentionPriority` `(Enum)`

_Dikkat onceligi._

#### class `BroadcastType` `(Enum)`

_Yayin turu (Global Workspace)._

#### class `IntegrationStatus` `(Enum)`

_Entegrasyon durumu._

#### class `AttentionFocus` `@dataclass`

_Dikkat odagi._

Methods:
- `is_expired()`
- `priority_score()`

#### class `Qualia` `@dataclass`

_Oznel deneyim temsili._

Methods:
- `phenomenal_strength()`

#### class `WorkspaceContent` `@dataclass`

_Global Workspace icerigi._

Methods:
- `competition_score()`
- `is_expired()`
- `mark_integrated()`
- `mark_broadcast()`

#### class `AwarenessState` `@dataclass`

_Farkindalik durumu._

Methods:
- `quality()`

#### class `GlobalWorkspaceState` `@dataclass`

_Global Workspace durumu._

Methods:
- `add_content()`
- `remove_content()`
- `get_content()`
- `get_contents_by_type()`
- `get_top_contents()`
- `cleanup_expired()`
- `get_awareness()`
- `set_awareness()`
- `get_overall_awareness()`
- `summary()`

#### class `ConsciousExperience` `@dataclass`

_Butunlesik bilinc deneyimi._

Methods:
- `richness()`
- `add_qualia()`
- `summary()`

### `meta/metamind/analyzers.py`

#### class `AnalyzerConfig` `@dataclass`

_Analyzer yapilandirmasi._

#### class `CycleAnalyzer`

_Cycle performans analizcisi._

Methods:
- `__init__()`
- `analyze_cycle()`
- `analyze_from_metrics()`
- `get_aggregate_stats()`
- `get_phase_stats()`
- `get_slowest_phases()`
- `get_recent_anomalies()`
- `get_trend()`
- `get_stats()`
- `summary()`
- `reset()`

#### `create_cycle_analyzer(config) -> CycleAnalyzer`

_CycleAnalyzer factory._

#### `get_cycle_analyzer() -> CycleAnalyzer`

_Default CycleAnalyzer getir._

### `meta/metamind/insights.py`

#### class `InsightGeneratorConfig` `@dataclass`

_InsightGenerator yapilandirmasi._

#### class `InsightGenerator`

_Insight uretici._

Methods:
- `__init__()`
- `generate_from_analysis()`
- `create_insight()`
- `get_insight()`
- `get_active_insights()`
- `get_actionable_insights()`
- `dismiss_insight()`
- `register_generator()`
- `get_stats()`
- `summary()`

#### `create_insight_generator(config) -> InsightGenerator`

_InsightGenerator factory._

#### `get_insight_generator() -> InsightGenerator`

_Default InsightGenerator getir._

### `meta/metamind/learning.py`

#### class `LearningManagerConfig` `@dataclass`

_LearningManager yapilandirmasi._

#### class `AdaptationStrategy` `@dataclass`

_Adaptasyon stratejisi._

Methods:
- `__post_init__()`
- `to_dict()`

#### class `LearningManager`

_Ogrenme yoneticisi._

Methods:
- `__init__()`
- `create_goal()`
- `update_goal_progress()`
- `get_goal()`
- `get_active_goals()`
- `cancel_goal()`
- `generate_goals_from_insights()`
- `generate_goals_from_patterns()`
- `track_metric()`
- `track_analysis()`
- `suggest_adaptation()`
- `get_active_strategies()`
- `get_learning_summary()`
- `get_stats()`
- `summary()`

#### `create_learning_manager(config) -> LearningManager`

_LearningManager factory._

#### `get_learning_manager() -> LearningManager`

_Default LearningManager getir._

### `meta/metamind/patterns.py`

#### class `PatternDetectorConfig` `@dataclass`

_PatternDetector yapilandirmasi._

#### class `PatternDetector`

_Kalip dedektoru._

Methods:
- `__init__()`
- `process_analysis()`
- `get_pattern()`
- `get_patterns_by_type()`
- `get_all_patterns()`
- `get_significant_patterns()`
- `get_stats()`
- `summary()`

#### `create_pattern_detector(config) -> PatternDetector`

_PatternDetector factory._

#### `get_pattern_detector() -> PatternDetector`

_Default PatternDetector getir._

### `meta/metamind/processor.py`

#### class `MetaMindConfig` `@dataclass`

_MetaMindProcessor yapilandirmasi._

#### class `MetaMindOutput` `@dataclass`

_MetaMindProcessor ciktisi._

Methods:
- `to_dict()`

#### class `MetaMindProcessor`

_MetaMind ana islemcisi._

Methods:
- `__init__()`
- `process()`
- `process_from_metrics()`
- `register_listener()`
- `unregister_listener()`
- `get_active_insights()`
- `get_active_patterns()`
- `get_active_goals()`
- `get_adaptation_strategies()`
- `get_performance_trend()`
- `get_system_health()`
- `get_meta_state()`
- `create_insight()`
- `create_goal()`
- `get_stats()`
- `summary()`
- `reset()`

#### `create_metamind_processor(config) -> MetaMindProcessor`

_MetaMindProcessor factory._

#### `get_metamind_processor() -> MetaMindProcessor`

_Default MetaMindProcessor getir._

### `meta/metamind/types.py`

#### class `InsightType` `(Enum)`

_Ogrenilen ders turleri._

#### class `PatternType` `(Enum)`

_Tespit edilen kalip turleri._

#### class `LearningGoalType` `(Enum)`

_Ogrenme hedef turleri._

#### class `MetaStateType` `(Enum)`

_Meta-bilissel durum turleri._

#### class `AnalysisScope` `(Enum)`

_Analiz kapsami._

#### class `SeverityLevel` `(Enum)`

_Ciddiyet seviyesi._

#### class `CycleAnalysisResult` `@dataclass`

_Tek cycle analiz sonucu._

Methods:
- `get_performance_score()`
- `to_dict()`

#### class `Insight` `@dataclass`

_Ogrenilen bir ders/icigor._

Methods:
- `__post_init__()`
- `get_priority()`
- `to_dict()`

#### class `Pattern` `@dataclass`

_Tespit edilen bir kalip._

Methods:
- `__post_init__()`
- `update_occurrence()`
- `to_dict()`

#### class `LearningGoal` `@dataclass`

_Ogrenme hedefi._

Methods:
- `__post_init__()`
- `update_progress()`
- `to_dict()`

#### class `MetaState` `@dataclass`

_MetaMind durumu._

Methods:
- `to_dict()`

### `meta/monitoring/metrics/collector.py`

#### class `Metric` `@dataclass`

_Tek bir metrik ölçümü._

#### class `MetricSummary` `@dataclass`

_Metrik özeti (aggregation)._

#### class `MetricsCollector`

_Sistem metriklerini toplayan collector._

Methods:
- `__init__()`
- `record()`
- `increment()`
- `gauge()`
- `timer()`
- `get_last()`
- `get_history()`
- `get_summary()`
- `get_all_names()`
- `clear()`
- `stats()`

#### `get_metrics_collector() -> MetricsCollector`

_Default metrics collector'ı getir._

### `meta/monitoring/metrics/cycle.py`

#### class `MetricType` `(Enum)`

_Metrik türleri._

#### class `PhaseMetrics` `@dataclass`

_Tek bir phase'in metrikleri._

#### class `CycleMetrics` `@dataclass`

_Tek bir cycle'ın tüm metrikleri._

Methods:
- `record_phase_start()`
- `record_phase_end()`
- `record_memory_retrieval()`
- `record_memory_store()`
- `record_trust_change()`
- `finalize()`
- `to_dict()`
- `get_phase_summary()`
- `get_slowest_phase()`

#### class `CycleMetricsHistory`

_Cycle metrik geçmişi._

Methods:
- `__init__()`
- `add()`
- `get_last()`
- `get_average_duration()`
- `get_phase_averages()`
- `get_success_rate()`
- `get_memory_stats()`
- `get_trust_stats()`
- `count()`

### `meta/monitoring/monitor.py`

#### class `MonitorConfig` `@dataclass`

_Monitor yapılandırması._

#### class `SystemMonitor`

_Sistem monitörü - event bus'ı dinler, metrikleri toplar._

Methods:
- `__init__()`
- `start()`
- `stop()`
- `add_alert_handler()`
- `get_report()`

#### `get_system_monitor() -> SystemMonitor`

_Default system monitor'ı getir._

### `meta/monitoring/persistence.py`

#### class `MonitoringPersistence`

_Monitoring verilerini PostgreSQL'e kaydeden sınıf._

Methods:
- `__init__()`
- `start()`
- `stop()`

#### class `DashboardDataProvider`

_Dashboard için PostgreSQL'den veri sağlayan sınıf._

Methods:
- `__init__()`
- `get_cycle_metrics()`
- `get_phase_durations()`
- `get_memory_stats()`
- `get_trust_levels()`
- `get_recent_activity()`
- `get_all_dashboard_data()`

#### `get_monitoring_persistence() -> MonitoringPersistence`

_Get singleton MonitoringPersistence instance._

#### `get_dashboard_data_provider() -> DashboardDataProvider`

_Get singleton DashboardDataProvider instance._

### `meta/monitoring/reporter.py`

#### class `ReporterConfig` `@dataclass`

_Reporter yapılandırması._

#### class `MonitoringReporter`

_Monitoring verilerini console/log'a yazdıran reporter._

Methods:
- `__init__()`
- `report_cycle()`
- `report_cycle_compact()`
- `report_summary()`
- `report_collector_stats()`
- `report_live_header()`
- `report_live_row()`

#### `get_reporter() -> MonitoringReporter`

_Default reporter'ı getir._

## Interface Modules

### `interface/chat/cli.py`

#### class `CLIChat`

_CLI Chat Interface._

Methods:
- `__init__()`
- `start()`
- `stop()`

#### `main()`

_CLI entry point._

### `interface/dashboard/app.py`

#### `get_data_provider() -> DashboardDataProvider`

_Get cached data provider instance._

#### `get_dashboard_data() -> Dict[...]`

_Gather all dashboard data from PostgreSQL._

#### `render_cycle_metrics(data) -> None`

_Render cycle metrics section._

#### `render_phase_chart(data) -> None`

_Render phase duration bar chart._

#### `render_memory_stats(data) -> None`

_Render memory statistics._

#### `render_trust_chart(data) -> None`

_Render trust levels bar chart._

#### `render_activity_log(data) -> None`

_Render recent activity log._

#### `render_system_stats(data) -> None`

_Render system statistics in sidebar._

#### `main()`

_Main dashboard entry point._
