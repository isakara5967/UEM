# UEM v2 Data Types Reference

_Auto-generated: 2025-12-11 06:11_

Complete reference of all dataclasses and enums in the UEM v2 codebase.

## Enums

Total: 85 enums

| Enum | File | Values |
|------|------|--------|
| `ActionCategory` | foundation/types/actions.py | MOTOR, VERBAL, COGNITIVE, SOCIAL, INTERNAL, ... (+1) |
| `ActionStatus` | foundation/types/actions.py | PENDING, EXECUTING, COMPLETED, FAILED, CANCELLED |
| `AgentDisposition` | core/perception/types.py | FRIENDLY, NEUTRAL, UNFRIENDLY, HOSTILE, UNKNOWN |
| `AnalysisScope` | meta/metamind/types.py | SINGLE_CYCLE, SHORT_TERM, MEDIUM_TERM, LONG_TERM |
| `ApprovalDecision` | core/language/risk/approver.py | APPROVED, APPROVED_WITH_MODIFICATIONS, NEEDS_REVIEW, REJECTED |
| `ApprovalStatus` | core/learning/episode_types.py | APPROVED, NEEDS_REVISION, REJECTED, NOT_CHECKED |
| `AttentionMode` | meta/consciousness/types.py | FOCUSED, DIFFUSE, DIVIDED, AUTOMATIC, SUSTAINED |
| `AttentionPriority` | meta/consciousness/types.py | CRITICAL, HIGH, NORMAL, LOW, BACKGROUND |
| `AwarenessType` | meta/consciousness/types.py | SENSORY, COGNITIVE, EMOTIONAL, SOCIAL, SELF, ... (+1) |
| `BasicEmotion` | core/affect/emotion/core/emotions.py | JOY, SADNESS, FEAR, ANGER, DISGUST, ... (+3) |
| `BeliefStrength` | core/cognition/types.py | CERTAIN, STRONG, MODERATE, WEAK, UNCERTAIN |
| `BeliefType` | core/cognition/types.py | FACTUAL, INFERRED, ASSUMED, HYPOTHETICAL |
| `BodyLanguage` | core/perception/types.py | OPEN, CLOSED, AGGRESSIVE, SUBMISSIVE, RELAXED, ... (+2) |
| `BroadcastType` | meta/consciousness/types.py | PERCEPTION, COGNITION, AFFECT, MEMORY, DECISION, ... (+2) |
| `ConsciousnessLevel` | meta/consciousness/types.py | UNCONSCIOUS, PRECONSCIOUS, SUBCONSCIOUS, CONSCIOUS, HYPERCONSCIOUS |
| `ConstraintSeverity` | core/language/dialogue/message_planner.py | LOW, MEDIUM, HIGH, CRITICAL |
| `ConstraintType` | core/language/dialogue/message_planner.py | ETHICAL, STYLE, CONTENT, SAFETY, TONE |
| `ConstructionLevel` | core/learning/episode_types.py | DEEP, MIDDLE, SURFACE |
| `ConstructionLevel` | core/language/construction/types.py | DEEP, MIDDLE, SURFACE |
| `ConstructionSource` | core/learning/episode_types.py | HUMAN_DEFAULT, LEARNED, ADAPTED |
| `DecayModel` | core/affect/emotion/core/dynamics.py | LINEAR, EXPONENTIAL, LOGARITHMIC |
| `DialogueAct` | core/language/dialogue/types.py | INFORM, EXPLAIN, CLARIFY, ASK, CONFIRM, ... (+18) |
| `EmbeddingModel` | core/memory/types.py | MULTILINGUAL_MINILM, MINILM_L6, MPNET_BASE |
| `EmotionalExpression` | core/perception/types.py | NEUTRAL, HAPPY, SAD, ANGRY, FEARFUL, ... (+4) |
| `EmotionalValence` | core/memory/types.py | VERY_NEGATIVE, NEGATIVE, NEUTRAL, POSITIVE, VERY_POSITIVE |
| `EmpathyChannel` | core/affect/social/empathy/channels.py | COGNITIVE, AFFECTIVE, SOMATIC, PROJECTIVE |
| `EpisodeType` | core/memory/types.py | ENCOUNTER, INTERACTION, OBSERVATION, CONFLICT, COOPERATION, ... (+2) |
| `EpisodeTypeEnum` | core/memory/persistence/models.py | encounter, interaction, observation, conflict, cooperation, ... (+2) |
| `EventType` | engine/events/bus.py | CYCLE_START, CYCLE_END, MODULE_START, MODULE_END, STIMULUS_RECEIVED, ... (+19) |
| `FeedbackType` | core/learning/types.py | POSITIVE, NEGATIVE, NEUTRAL, EXPLICIT, IMPLICIT |
| `FeedbackTypeEnum` | core/memory/persistence/models.py | positive, negative, neutral, explicit, implicit |
| `GoalDomain` | core/self/types.py | GROWTH, RELATIONSHIP, CONTRIBUTION, MASTERY, AUTONOMY, ... (+1) |
| `GoalPriority` | core/cognition/types.py | CRITICAL, HIGH, NORMAL, LOW, BACKGROUND |
| `GoalStatus` | core/cognition/types.py | ACTIVE, PENDING, ACHIEVED, FAILED, SUSPENDED, ... (+1) |
| `GoalType` | core/cognition/types.py | SURVIVAL, MAINTENANCE, ACHIEVEMENT, AVOIDANCE, SOCIAL, ... (+1) |
| `IdentityAspect` | core/self/types.py | CORE, SOCIAL, PROFESSIONAL, RELATIONAL, ASPIRATIONAL |
| `InsightType` | meta/metamind/types.py | PERFORMANCE, BOTTLENECK, OPTIMIZATION, ANOMALY, CORRELATION, ... (+3) |
| `IntegrationStatus` | meta/consciousness/types.py | PENDING, PROCESSING, INTEGRATED, BROADCAST, EXPIRED |
| `IntegrityStatus` | core/self/types.py | ALIGNED, MINOR_CONFLICT, MAJOR_CONFLICT, CRISIS |
| `IntentCategory` | core/language/intent/types.py | GREETING, FAREWELL, ASK_WELLBEING, ASK_IDENTITY, EXPRESS_POSITIVE, ... (+12) |
| `IntentionStrength` | core/cognition/types.py | COMMITTED, INTENDED, CONSIDERING, POSSIBLE |
| `InteractionType` | core/memory/types.py | HELPED, COOPERATED, SHARED, PROTECTED, CELEBRATED, ... (+10) |
| `InteractionTypeEnum` | core/memory/persistence/models.py | helped, cooperated, shared, protected, celebrated, ... (+10) |
| `LLMProvider` | core/language/llm_adapter.py | ANTHROPIC, OPENAI, OLLAMA, MOCK |
| `LearningGoalType` | meta/metamind/types.py | SPEED, ACCURACY, EFFICIENCY, STABILITY, MEMORY, ... (+1) |
| `MVCSCategory` | core/language/construction/mvcs.py | GREET, SELF_INTRO, ASK_WELLBEING, SIMPLE_INFORM, EMPATHIZE_BASIC, ... (+7) |
| `MemoryType` | core/memory/types.py | SENSORY, WORKING, EPISODIC, SEMANTIC, EMOTIONAL, ... (+2) |
| `MemoryTypeEnum` | core/memory/persistence/models.py | sensory, working, episodic, semantic, emotional, ... (+2) |
| `MetaStateType` | meta/metamind/types.py | ANALYZING, LEARNING, ADAPTING, MONITORING, OPTIMIZING, ... (+1) |
| `MetricType` | meta/monitoring/metrics/cycle.py | DURATION, COUNT, GAUGE, DELTA |
| `ModuleType` | foundation/types/base.py | PERCEPTION, COGNITION, MEMORY, AFFECT, SELF, ... (+4) |
| `NarrativeType` | core/self/types.py | ORIGIN, CHALLENGE, TRANSFORMATION, LESSON, RELATIONSHIP |
| `NeedLevel` | core/self/types.py | PHYSIOLOGICAL, SAFETY, BELONGING, ESTEEM, SELF_ACTUALIZATION |
| `NeedStatus` | core/self/types.py | SATISFIED, PARTIAL, UNSATISFIED, CRITICAL |
| `OpportunityLevel` | core/cognition/types.py | EXCELLENT, GOOD, MODERATE, LIMITED, NONE |
| `PADOctant` | core/affect/emotion/core/pad.py | EXUBERANT, DEPENDENT, RELAXED, DOCILE, HOSTILE, ... (+3) |
| `PatternType` | core/learning/types.py | RESPONSE, BEHAVIOR, EMOTION, LANGUAGE |
| `PatternType` | meta/metamind/types.py | RECURRING, CYCLIC, SPIKE, DEGRADATION, STABILITY, ... (+3) |
| `PatternTypeEnum` | core/memory/persistence/models.py | response, behavior, emotion, language |
| `PerceptualCategory` | core/perception/types.py | AGENT, OBJECT, LOCATION, EVENT, ABSTRACT |
| `Phase` | engine/phases/definitions.py | SENSE, ATTEND, PERCEIVE, RETRIEVE, REASON, ... (+5) |
| `Priority` | foundation/types/base.py | CRITICAL, HIGH, NORMAL, LOW |
| `ReasoningType` | core/cognition/types.py | DEDUCTION, INDUCTION, ABDUCTION, ANALOGY |
| `RegulationStrategy` | core/affect/emotion/core/dynamics.py | REAPPRAISAL, SUPPRESSION, DISTRACTION, ACCEPTANCE, RUMINATION |
| `RelationshipType` | core/memory/types.py | UNKNOWN, STRANGER, ACQUAINTANCE, COLLEAGUE, FRIEND, ... (+5) |
| `RelationshipTypeEnum` | core/memory/persistence/models.py | unknown, stranger, acquaintance, colleague, friend, ... (+5) |
| `ResultStatus` | foundation/types/results.py | SUCCESS, PARTIAL, FAILED, SKIPPED |
| `RiskCategory` | core/language/risk/types.py | ETHICAL, EMOTIONAL, FACTUAL, SAFETY, PRIVACY, ... (+1) |
| `RiskLevel` | core/cognition/types.py | CRITICAL, HIGH, MODERATE, LOW, MINIMAL |
| `RiskLevel` | core/language/risk/types.py | LOW, MEDIUM, HIGH, CRITICAL |
| `SVField` | foundation/state/fields.py | RESOURCE, THREAT, WELLBEING, VALENCE, AROUSAL, ... (+26) |
| `SecondaryEmotion` | core/affect/emotion/core/emotions.py | LOVE, OPTIMISM, ACCEPTANCE, SUBMISSION, AWE, ... (+7) |
| `SelectionStrategy` | core/language/dialogue/act_selector.py | CONSERVATIVE, BALANCED, EXPRESSIVE |
| `SensoryModality` | core/perception/types.py | VISUAL, AUDITORY, TACTILE, PROPRIOCEPTIVE, INTEROCEPTIVE, ... (+1) |
| `SeverityLevel` | meta/metamind/types.py | LOW, MEDIUM, HIGH, CRITICAL |
| `SlotType` | core/language/construction/types.py | ENTITY, VERB, ADJECTIVE, ADVERB, NUMBER, ... (+5) |
| `SourceType` | core/memory/types.py | EPISODE, DIALOGUE, FACT, CONCEPT |
| `SympathyType` | core/affect/social/sympathy/types.py | COMPASSION, EMPATHIC_JOY, GRATITUDE, EMPATHIC_SADNESS, EMPATHIC_ANGER, ... (+3) |
| `ThreatLevel` | core/perception/types.py | NONE, LOW, MODERATE, HIGH, CRITICAL |
| `ToneType` | core/language/dialogue/types.py | FORMAL, CASUAL, EMPATHIC, SUPPORTIVE, NEUTRAL, ... (+3) |
| `TrustDimension` | core/affect/social/trust/types.py | COMPETENCE, BENEVOLENCE, INTEGRITY, PREDICTABILITY |
| `TrustLevel` | core/affect/social/trust/types.py | BLIND, HIGH, MODERATE, CAUTIOUS, LOW, ... (+1) |
| `TrustType` | core/affect/social/trust/types.py | BLIND, EARNED, CAUTIOUS, NEUTRAL, CONDITIONAL, ... (+2) |
| `ValueCategory` | core/self/types.py | TERMINAL, INSTRUMENTAL, MORAL, AESTHETIC, EPISTEMIC |
| `ValuePriority` | core/self/types.py | SACRED, CORE, IMPORTANT, PREFERRED, OPTIONAL |

### Enum Details

#### `ActionCategory`

**File:** `foundation/types/actions.py:12`

_Eylem kategorileri._

**Values:**
- `MOTOR`
- `VERBAL`
- `COGNITIVE`
- `SOCIAL`
- `INTERNAL`
- `WAIT`

#### `ActionStatus`

**File:** `foundation/types/actions.py:22`

_Eylem durumu._

**Values:**
- `PENDING`
- `EXECUTING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

#### `AgentDisposition`

**File:** `core/perception/types.py:60`

_Ajan tavir/tutumu._

**Values:**
- `FRIENDLY`
- `NEUTRAL`
- `UNFRIENDLY`
- `HOSTILE`
- `UNKNOWN`

#### `AnalysisScope`

**File:** `meta/metamind/types.py:62`

_Analiz kapsami._

**Values:**
- `SINGLE_CYCLE`
- `SHORT_TERM`
- `MEDIUM_TERM`
- `LONG_TERM`

#### `ApprovalDecision`

**File:** `core/language/risk/approver.py:25`

_Onay kararı türleri._

**Values:**
- `APPROVED`
- `APPROVED_WITH_MODIFICATIONS`
- `NEEDS_REVIEW`
- `REJECTED`

#### `ApprovalStatus`

**File:** `core/learning/episode_types.py:65`

_Approval durumu._

**Values:**
- `APPROVED`
- `NEEDS_REVISION`
- `REJECTED`
- `NOT_CHECKED`

#### `AttentionMode`

**File:** `meta/consciousness/types.py:40`

_Dikkat modlari._

**Values:**
- `FOCUSED`
- `DIFFUSE`
- `DIVIDED`
- `AUTOMATIC`
- `SUSTAINED`

#### `AttentionPriority`

**File:** `meta/consciousness/types.py:49`

_Dikkat onceligi._

**Values:**
- `CRITICAL`
- `HIGH`
- `NORMAL`
- `LOW`
- `BACKGROUND`

#### `AwarenessType`

**File:** `meta/consciousness/types.py:30`

_Farkindalik turleri._

**Values:**
- `SENSORY`
- `COGNITIVE`
- `EMOTIONAL`
- `SOCIAL`
- `SELF`
- `META`

#### `BasicEmotion`

**File:** `core/affect/emotion/core/emotions.py:15`

_Temel duygular (Ekman + Plutchik bazlı)._

**Values:**
- `JOY`
- `SADNESS`
- `FEAR`
- `ANGER`
- `DISGUST`
- `SURPRISE`
- `TRUST`
- `ANTICIPATION`

#### `BeliefStrength`

**File:** `core/cognition/types.py:27`

_İnanç gücü seviyeleri._

**Values:**
- `CERTAIN`
- `STRONG`
- `MODERATE`
- `WEAK`
- `UNCERTAIN`

#### `BeliefType`

**File:** `core/cognition/types.py:19`

_İnanç türleri._

**Values:**
- `FACTUAL`
- `INFERRED`
- `ASSUMED`
- `HYPOTHETICAL`

#### `BodyLanguage`

**File:** `core/perception/types.py:82`

_Vucut dili._

**Values:**
- `OPEN`
- `CLOSED`
- `AGGRESSIVE`
- `SUBMISSIVE`
- `RELAXED`
- `TENSE`
- `NEUTRAL`

#### `BroadcastType`

**File:** `meta/consciousness/types.py:58`

_Yayin turu (Global Workspace)._

**Values:**
- `PERCEPTION`
- `COGNITION`
- `AFFECT`
- `MEMORY`
- `DECISION`
- `ACTION`
- `ALERT`

#### `ConsciousnessLevel`

**File:** `meta/consciousness/types.py:21`

_Bilinc seviyeleri._

**Values:**
- `UNCONSCIOUS`
- `PRECONSCIOUS`
- `SUBCONSCIOUS`
- `CONSCIOUS`
- `HYPERCONSCIOUS`

#### `ConstraintSeverity`

**File:** `core/language/dialogue/message_planner.py:31`

_Kısıt ciddiyeti._

**Values:**
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

#### `ConstraintType`

**File:** `core/language/dialogue/message_planner.py:47`

_Kısıt türleri._

**Values:**
- `ETHICAL`
- `STYLE`
- `CONTENT`
- `SAFETY`
- `TONE`

#### `ConstructionLevel`

**File:** `core/learning/episode_types.py:58`

_Construction seviyesi - Construction Grammar teorisinden._

**Values:**
- `DEEP`
- `MIDDLE`
- `SURFACE`

#### `ConstructionLevel`

**File:** `core/language/construction/types.py:42`

_Construction katman seviyeleri._

**Values:**
- `DEEP`
- `MIDDLE`
- `SURFACE`

#### `ConstructionSource`

**File:** `core/learning/episode_types.py:51`

_Construction kaynağı - nereden geldi?_

**Values:**
- `HUMAN_DEFAULT`
- `LEARNED`
- `ADAPTED`

#### `DecayModel`

**File:** `core/affect/emotion/core/dynamics.py:21`

_Duygu sönümlenme modelleri._

**Values:**
- `LINEAR`
- `EXPONENTIAL`
- `LOGARITHMIC`

#### `DialogueAct`

**File:** `core/language/dialogue/types.py:21`

_Konuşma eylemleri - Speech Act Theory'den esinlenilmiş._

**Values:**
- `INFORM`
- `EXPLAIN`
- `CLARIFY`
- `ASK`
- `CONFIRM`
- `EMPATHIZE`
- `ENCOURAGE`
- `COMFORT`
- `SUGGEST`
- `WARN`
- `ADVISE`
- `REFUSE`
- `LIMIT`
- `DEFLECT`
- `ACKNOWLEDGE`
- `APOLOGIZE`
- `THANK`
- `GREET`
- `RESPOND_WELLBEING`
- `RECEIVE_THANKS`
- `LIGHT_CHITCHAT`
- `ACKNOWLEDGE_POSITIVE`
- `CLOSE_CONVERSATION`

#### `EmbeddingModel`

**File:** `core/memory/types.py:649`

_Desteklenen embedding modelleri._

**Values:**
- `MULTILINGUAL_MINILM`
- `MINILM_L6`
- `MPNET_BASE`

#### `EmotionalExpression`

**File:** `core/perception/types.py:69`

_Yuz ifadesi / duygusal gosterge._

**Values:**
- `NEUTRAL`
- `HAPPY`
- `SAD`
- `ANGRY`
- `FEARFUL`
- `SURPRISED`
- `DISGUSTED`
- `CONTEMPTUOUS`
- `THREATENING`

#### `EmotionalValence`

**File:** `core/memory/types.py:30`

_Duygusal degerlik._

**Values:**
- `VERY_NEGATIVE`
- `NEGATIVE`
- `NEUTRAL`
- `POSITIVE`
- `VERY_POSITIVE`

#### `EmpathyChannel`

**File:** `core/affect/social/empathy/channels.py:18`

_Empati kanalları._

**Values:**
- `COGNITIVE`
- `AFFECTIVE`
- `SOMATIC`
- `PROJECTIVE`

#### `EpisodeType`

**File:** `core/memory/types.py:77`

_Olay turu._

**Values:**
- `ENCOUNTER`
- `INTERACTION`
- `OBSERVATION`
- `CONFLICT`
- `COOPERATION`
- `EMOTIONAL_EVENT`
- `SIGNIFICANT`

#### `EpisodeTypeEnum`

**File:** `core/memory/persistence/models.py:77`

**Values:**
- `encounter`
- `interaction`
- `observation`
- `conflict`
- `cooperation`
- `emotional`
- `significant`

#### `EventType`

**File:** `engine/events/bus.py:17`

_Sistem event tipleri._

**Values:**
- `CYCLE_START`
- `CYCLE_END`
- `MODULE_START`
- `MODULE_END`
- `STIMULUS_RECEIVED`
- `ENTITY_DETECTED`
- `THREAT_DETECTED`
- `ATTENTION_SHIFT`
- `REASONING_COMPLETE`
- `HYPOTHESIS_GENERATED`
- `EVALUATION_COMPLETE`
- `MEMORY_STORED`
- `MEMORY_RETRIEVED`
- `MEMORY_CONSOLIDATED`
- `EMOTION_CHANGED`
- `EMPATHY_COMPUTED`
- `TRUST_UPDATED`
- `VALUE_CONFLICT`
- `INTEGRITY_CHECK`
- `ACTION_SELECTED`
- `ACTION_EXECUTED`
- `GOAL_UPDATED`
- `ANOMALY_DETECTED`
- `INSIGHT_GENERATED`

#### `FeedbackType`

**File:** `core/learning/types.py:22`

_Geri bildirim turleri._

**Values:**
- `POSITIVE`
- `NEGATIVE`
- `NEUTRAL`
- `EXPLICIT`
- `IMPLICIT`

#### `FeedbackTypeEnum`

**File:** `core/memory/persistence/models.py:712`

_Feedback type enum for database._

**Values:**
- `positive`
- `negative`
- `neutral`
- `explicit`
- `implicit`

#### `GoalDomain`

**File:** `core/self/types.py:63`

_Kisisel hedef alanlari._

**Values:**
- `GROWTH`
- `RELATIONSHIP`
- `CONTRIBUTION`
- `MASTERY`
- `AUTONOMY`
- `MEANING`

#### `GoalPriority`

**File:** `core/cognition/types.py:46`

_Hedef önceliği._

**Values:**
- `CRITICAL`
- `HIGH`
- `NORMAL`
- `LOW`
- `BACKGROUND`

#### `GoalStatus`

**File:** `core/cognition/types.py:55`

_Hedef durumu._

**Values:**
- `ACTIVE`
- `PENDING`
- `ACHIEVED`
- `FAILED`
- `SUSPENDED`
- `ABANDONED`

#### `GoalType`

**File:** `core/cognition/types.py:36`

_Hedef türleri._

**Values:**
- `SURVIVAL`
- `MAINTENANCE`
- `ACHIEVEMENT`
- `AVOIDANCE`
- `SOCIAL`
- `EXPLORATION`

#### `IdentityAspect`

**File:** `core/self/types.py:19`

_Kimlik boyutlari._

**Values:**
- `CORE`
- `SOCIAL`
- `PROFESSIONAL`
- `RELATIONAL`
- `ASPIRATIONAL`

#### `InsightType`

**File:** `meta/metamind/types.py:18`

_Ogrenilen ders turleri._

**Values:**
- `PERFORMANCE`
- `BOTTLENECK`
- `OPTIMIZATION`
- `ANOMALY`
- `CORRELATION`
- `TREND`
- `WARNING`
- `SUCCESS`

#### `IntegrationStatus`

**File:** `meta/consciousness/types.py:69`

_Entegrasyon durumu._

**Values:**
- `PENDING`
- `PROCESSING`
- `INTEGRATED`
- `BROADCAST`
- `EXPIRED`

#### `IntegrityStatus`

**File:** `core/self/types.py:73`

_Tutarlilik durumu._

**Values:**
- `ALIGNED`
- `MINOR_CONFLICT`
- `MAJOR_CONFLICT`
- `CRISIS`

#### `IntentCategory`

**File:** `core/language/intent/types.py:14`

_Kullanıcı niyeti kategorileri._

**Values:**
- `GREETING`
- `FAREWELL`
- `ASK_WELLBEING`
- `ASK_IDENTITY`
- `EXPRESS_POSITIVE`
- `EXPRESS_NEGATIVE`
- `REQUEST_HELP`
- `REQUEST_INFO`
- `THANK`
- `APOLOGIZE`
- `AGREE`
- `DISAGREE`
- `CLARIFY`
- `COMPLAIN`
- `META_QUESTION`
- `SMALLTALK`
- `UNKNOWN`

#### `IntentionStrength`

**File:** `core/cognition/types.py:65`

_Niyet gücü._

**Values:**
- `COMMITTED`
- `INTENDED`
- `CONSIDERING`
- `POSSIBLE`

#### `InteractionType`

**File:** `core/memory/types.py:53`

_Etkilesim turu._

**Values:**
- `HELPED`
- `COOPERATED`
- `SHARED`
- `PROTECTED`
- `CELEBRATED`
- `COMFORTED`
- `OBSERVED`
- `CONVERSED`
- `TRADED`
- `COMPETED`
- `CONFLICTED`
- `HARMED`
- `BETRAYED`
- `THREATENED`
- `ATTACKED`

#### `InteractionTypeEnum`

**File:** `core/memory/persistence/models.py:55`

**Values:**
- `helped`
- `cooperated`
- `shared`
- `protected`
- `celebrated`
- `comforted`
- `observed`
- `conversed`
- `traded`
- `competed`
- `conflicted`
- `harmed`
- `betrayed`
- `threatened`
- `attacked`

#### `LLMProvider`

**File:** `core/language/llm_adapter.py:25`

_Desteklenen LLM provider'lar._

**Values:**
- `ANTHROPIC`
- `OPENAI`
- `OLLAMA`
- `MOCK`

#### `LearningGoalType`

**File:** `meta/metamind/types.py:42`

_Ogrenme hedef turleri._

**Values:**
- `SPEED`
- `ACCURACY`
- `EFFICIENCY`
- `STABILITY`
- `MEMORY`
- `ADAPTABILITY`

#### `MVCSCategory`

**File:** `core/language/construction/mvcs.py:42`

_MVCS kategori tipleri._

**Values:**
- `GREET`
- `SELF_INTRO`
- `ASK_WELLBEING`
- `SIMPLE_INFORM`
- `EMPATHIZE_BASIC`
- `CLARIFY_REQUEST`
- `SAFE_REFUSAL`
- `RESPOND_WELLBEING`
- `RECEIVE_THANKS`
- `LIGHT_CHITCHAT`
- `ACKNOWLEDGE_POSITIVE`
- `CLOSE_CONVERSATION`

#### `MemoryType`

**File:** `core/memory/types.py:19`

_Bellek turu._

**Values:**
- `SENSORY`
- `WORKING`
- `EPISODIC`
- `SEMANTIC`
- `EMOTIONAL`
- `RELATIONSHIP`
- `CONVERSATION`

#### `MemoryTypeEnum`

**File:** `core/memory/persistence/models.py:30`

**Values:**
- `sensory`
- `working`
- `episodic`
- `semantic`
- `emotional`
- `relationship`
- `conversation`

#### `MetaStateType`

**File:** `meta/metamind/types.py:52`

_Meta-bilissel durum turleri._

**Values:**
- `ANALYZING`
- `LEARNING`
- `ADAPTING`
- `MONITORING`
- `OPTIMIZING`
- `IDLE`

#### `MetricType`

**File:** `meta/monitoring/metrics/cycle.py:13`

_Metrik türleri._

**Values:**
- `DURATION`
- `COUNT`
- `GAUGE`
- `DELTA`

#### `ModuleType`

**File:** `foundation/types/base.py:21`

_Modül tipleri._

**Values:**
- `PERCEPTION`
- `COGNITION`
- `MEMORY`
- `AFFECT`
- `SELF`
- `EXECUTIVE`
- `CONSCIOUSNESS`
- `METAMIND`
- `MONITORING`

#### `NarrativeType`

**File:** `core/self/types.py:81`

_Hikaye turleri._

**Values:**
- `ORIGIN`
- `CHALLENGE`
- `TRANSFORMATION`
- `LESSON`
- `RELATIONSHIP`

#### `NeedLevel`

**File:** `core/self/types.py:46`

_Maslow ihtiyac seviyeleri._

**Values:**
- `PHYSIOLOGICAL`
- `SAFETY`
- `BELONGING`
- `ESTEEM`
- `SELF_ACTUALIZATION`

#### `NeedStatus`

**File:** `core/self/types.py:55`

_Ihtiyac durumu._

**Values:**
- `SATISFIED`
- `PARTIAL`
- `UNSATISFIED`
- `CRITICAL`

#### `OpportunityLevel`

**File:** `core/cognition/types.py:90`

_Fırsat seviyesi._

**Values:**
- `EXCELLENT`
- `GOOD`
- `MODERATE`
- `LIMITED`
- `NONE`

#### `PADOctant`

**File:** `core/affect/emotion/core/pad.py:156`

_PAD uzayının 8 oktantı - temel duygu bölgeleri._

**Values:**
- `EXUBERANT`
- `DEPENDENT`
- `RELAXED`
- `DOCILE`
- `HOSTILE`
- `ANXIOUS`
- `DISDAINFUL`
- `BORED`

#### `PatternType`

**File:** `core/learning/types.py:31`

_Davranis pattern turleri._

**Values:**
- `RESPONSE`
- `BEHAVIOR`
- `EMOTION`
- `LANGUAGE`

#### `PatternType`

**File:** `meta/metamind/types.py:30`

_Tespit edilen kalip turleri._

**Values:**
- `RECURRING`
- `CYCLIC`
- `SPIKE`
- `DEGRADATION`
- `STABILITY`
- `OSCILLATION`
- `IMPROVEMENT`
- `ANOMALY`

#### `PatternTypeEnum`

**File:** `core/memory/persistence/models.py:652`

_Pattern type enum for database._

**Values:**
- `response`
- `behavior`
- `emotion`
- `language`

#### `PerceptualCategory`

**File:** `core/perception/types.py:42`

_Algilanan nesne kategorileri._

**Values:**
- `AGENT`
- `OBJECT`
- `LOCATION`
- `EVENT`
- `ABSTRACT`

#### `Phase`

**File:** `engine/phases/definitions.py:12`

_10-Phase Cognitive Cycle._

**Values:**
- `SENSE`
- `ATTEND`
- `PERCEIVE`
- `RETRIEVE`
- `REASON`
- `EVALUATE`
- `FEEL`
- `DECIDE`
- `PLAN`
- `ACT`

#### `Priority`

**File:** `foundation/types/base.py:13`

_İşlem önceliği._

**Values:**
- `CRITICAL`
- `HIGH`
- `NORMAL`
- `LOW`

#### `ReasoningType`

**File:** `core/cognition/types.py:73`

_Akıl yürütme türleri._

**Values:**
- `DEDUCTION`
- `INDUCTION`
- `ABDUCTION`
- `ANALOGY`

#### `RegulationStrategy`

**File:** `core/affect/emotion/core/dynamics.py:28`

_Duygu düzenleme stratejileri (Gross, 2015)._

**Values:**
- `REAPPRAISAL`
- `SUPPRESSION`
- `DISTRACTION`
- `ACCEPTANCE`
- `RUMINATION`

#### `RelationshipType`

**File:** `core/memory/types.py:39`

_Iliski turu._

**Values:**
- `UNKNOWN`
- `STRANGER`
- `ACQUAINTANCE`
- `COLLEAGUE`
- `FRIEND`
- `CLOSE_FRIEND`
- `FAMILY`
- `RIVAL`
- `ENEMY`
- `NEUTRAL`

#### `RelationshipTypeEnum`

**File:** `core/memory/persistence/models.py:41`

**Values:**
- `unknown`
- `stranger`
- `acquaintance`
- `colleague`
- `friend`
- `close_friend`
- `family`
- `rival`
- `enemy`
- `neutral`

#### `ResultStatus`

**File:** `foundation/types/results.py:14`

_İşlem sonucu durumu._

**Values:**
- `SUCCESS`
- `PARTIAL`
- `FAILED`
- `SKIPPED`

#### `RiskCategory`

**File:** `core/language/risk/types.py:73`

_Risk kategorileri - Riskin türü/kaynağı._

**Values:**
- `ETHICAL`
- `EMOTIONAL`
- `FACTUAL`
- `SAFETY`
- `PRIVACY`
- `BOUNDARY`

#### `RiskLevel`

**File:** `core/cognition/types.py:81`

_Risk seviyesi._

**Values:**
- `CRITICAL`
- `HIGH`
- `MODERATE`
- `LOW`
- `MINIMAL`

#### `RiskLevel`

**File:** `core/language/risk/types.py:27`

_Risk seviyeleri - Kontrol mekanizması tetikleyicisi._

**Values:**
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

#### `SVField`

**File:** `foundation/state/fields.py:11`

_StateVector alanları._

**Values:**
- `RESOURCE`
- `THREAT`
- `WELLBEING`
- `VALENCE`
- `AROUSAL`
- `DOMINANCE`
- `EMOTIONAL_INTENSITY`
- `MOOD_STABILITY`
- `COGNITIVE_EMPATHY`
- `AFFECTIVE_EMPATHY`
- `SOMATIC_EMPATHY`
- `PROJECTIVE_EMPATHY`
- `EMPATHY_TOTAL`
- `SYMPATHY_LEVEL`
- `SYMPATHY_VALENCE`
- `TRUST_VALUE`
- `TRUST_COMPETENCE`
- `TRUST_BENEVOLENCE`
- `TRUST_INTEGRITY`
- `TRUST_PREDICTABILITY`
- `SOCIAL_ENGAGEMENT`
- `RELATIONSHIP_QUALITY`
- `COGNITIVE_LOAD`
- `ATTENTION_FOCUS`
- `CERTAINTY`
- `MEMORY_LOAD`
- `MEMORY_RELEVANCE`
- `KNOWN_AGENT`
- `INTEGRITY`
- `ETHICAL_ALIGNMENT`
- `CONSCIOUSNESS_LEVEL`

#### `SecondaryEmotion`

**File:** `core/affect/emotion/core/emotions.py:34`

_İkincil duygular - temel duyguların kombinasyonları._

**Values:**
- `LOVE`
- `OPTIMISM`
- `ACCEPTANCE`
- `SUBMISSION`
- `AWE`
- `DESPAIR`
- `DISAPPROVAL`
- `REMORSE`
- `CONTEMPT`
- `SHAME`
- `AGGRESSIVENESS`
- `INTEREST`

#### `SelectionStrategy`

**File:** `core/language/dialogue/act_selector.py:25`

_Act seçim stratejisi._

**Values:**
- `CONSERVATIVE`
- `BALANCED`
- `EXPRESSIVE`

#### `SensoryModality`

**File:** `core/perception/types.py:32`

_Duyusal modalite turleri._

**Values:**
- `VISUAL`
- `AUDITORY`
- `TACTILE`
- `PROPRIOCEPTIVE`
- `INTEROCEPTIVE`
- `SOCIAL`

#### `SeverityLevel`

**File:** `meta/metamind/types.py:70`

_Ciddiyet seviyesi._

**Values:**
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

#### `SlotType`

**File:** `core/language/construction/types.py:56`

_Slot türleri - Template'deki değişken tipleri._

**Values:**
- `ENTITY`
- `VERB`
- `ADJECTIVE`
- `ADVERB`
- `NUMBER`
- `TIME`
- `PLACE`
- `REASON`
- `CONNECTOR`
- `FILLER`

#### `SourceType`

**File:** `core/memory/types.py:656`

_Semantic memory kaynak turu._

**Values:**
- `EPISODE`
- `DIALOGUE`
- `FACT`
- `CONCEPT`

#### `SympathyType`

**File:** `core/affect/social/sympathy/types.py:30`

_Sempati türleri._

**Values:**
- `COMPASSION`
- `EMPATHIC_JOY`
- `GRATITUDE`
- `EMPATHIC_SADNESS`
- `EMPATHIC_ANGER`
- `PITY`
- `SCHADENFREUDE`
- `ENVY`

#### `ThreatLevel`

**File:** `core/perception/types.py:51`

_Tehdit seviyesi._

**Values:**
- `NONE`
- `LOW`
- `MODERATE`
- `HIGH`
- `CRITICAL`

#### `ToneType`

**File:** `core/language/dialogue/types.py:71`

_Ton türleri - Mesajın üslup ve atmosferi._

**Values:**
- `FORMAL`
- `CASUAL`
- `EMPATHIC`
- `SUPPORTIVE`
- `NEUTRAL`
- `CAUTIOUS`
- `ENTHUSIASTIC`
- `SERIOUS`

#### `TrustDimension`

**File:** `core/affect/social/trust/types.py:69`

_Güven boyutları (Mayer et al., 1995)._

**Values:**
- `COMPETENCE`
- `BENEVOLENCE`
- `INTEGRITY`
- `PREDICTABILITY`

#### `TrustLevel`

**File:** `core/affect/social/trust/types.py:32`

_Güven seviyeleri._

**Values:**
- `BLIND`
- `HIGH`
- `MODERATE`
- `CAUTIOUS`
- `LOW`
- `DISTRUST`

#### `TrustType`

**File:** `core/affect/social/trust/types.py:58`

_Güven türleri - nasıl oluştuğuna göre._

**Values:**
- `BLIND`
- `EARNED`
- `CAUTIOUS`
- `NEUTRAL`
- `CONDITIONAL`
- `DISTRUST`
- `BETRAYED`

#### `ValueCategory`

**File:** `core/self/types.py:28`

_Deger kategorileri._

**Values:**
- `TERMINAL`
- `INSTRUMENTAL`
- `MORAL`
- `AESTHETIC`
- `EPISTEMIC`

#### `ValuePriority`

**File:** `core/self/types.py:37`

_Deger onceligi._

**Values:**
- `SACRED`
- `CORE`
- `IMPORTANT`
- `PREFERRED`
- `OPTIONAL`

## Dataclasses

Total: 212 dataclasses

| Dataclass | File | Purpose |
|-----------|------|---------|
| `ActScore` | core/language/dialogue/act_selector.py | Bir DialogueAct'in skoru. |
| `ActSelectionResult` | core/language/dialogue/act_selector.py | Seçim sonucu. |
| `ActSelectorConfig` | core/language/dialogue/act_selector.py | DialogueActSelector konfigürasyonu. |
| `Action` | foundation/types/actions.py | Gerçekleştirilecek eylem. |
| `ActionOutcome` | foundation/types/actions.py | Gerçekleştirilen eylemin sonucu. |
| `ActionTemplate` | core/cognition/planning.py | Eylem şablonu. |
| `Actor` | core/language/dialogue/types.py | Konuşmadaki aktör - Kim konuşuyor/dinliyor? |
| `AdaptationConfig` | core/learning/adaptation.py | Adaptasyon konfigurasyonu. |
| `AdaptationRecord` | core/learning/adaptation.py | Adaptasyon kaydi. |
| `AdaptationStrategy` | meta/metamind/learning.py | Adaptasyon stratejisi. |
| `AffectPhaseConfig` | engine/handlers/affect.py | FEEL fazı yapılandırması. |
| `AffectPhaseState` | engine/handlers/affect.py | FEEL fazı için tutulan state. |
| `AffectResult` | foundation/types/results.py | Affect modülü sonucu. |
| `AgentState` | core/affect/social/empathy/simulation.py | Gözlemlenen ajanın durumu. |
| `AnalyzerConfig` | meta/metamind/analyzers.py | Analyzer yapilandirmasi. |
| `ApprovalResult` | core/language/risk/approver.py | Onay sonucu. |
| `AttentionConfig` | meta/consciousness/attention.py | Dikkat modulu yapilandirmasi. |
| `AttentionFilter` | meta/consciousness/attention.py | Dikkat filtresi. |
| `AttentionFocus` | core/perception/types.py | Dikkat odagi - neye odaklaniliyor. |
| `AttentionFocus` | meta/consciousness/types.py | Dikkat odagi. |
| `AuditoryFeatures` | core/perception/types.py | Isitsel ozellikler. |
| `AwarenessConfig` | meta/consciousness/awareness.py | Farkindalik modulu yapilandirmasi. |
| `AwarenessState` | meta/consciousness/types.py | Farkindalik durumu. |
| `Belief` | core/cognition/types.py | Bir inanç/bilgi temsili. |
| `BroadcastListener` | meta/consciousness/integration.py | Yayin dinleyicisi. |
| `ChannelResult` | core/affect/social/empathy/channels.py | Tek bir kanalın sonucu. |
| `ChatConfig` | core/language/chat_agent.py | Chat agent yapilandirmasi. |
| `ChatResponse` | core/language/chat_agent.py | Chat yanit yapisi. |
| `ClassInfo` | scripts/generate_docs.py | Bir class hakkinda bilgi. |
| `CognitionConfig` | core/cognition/processor.py | Biliş işlemci yapılandırması. |
| `CognitionHandlerConfig` | engine/handlers/cognition.py | Cognition handler'ları yapılandırması. |
| `CognitionOutput` | core/cognition/processor.py | Biliş işleme çıktısı. |
| `CognitionResult` | foundation/types/results.py | Cognition modülü sonucu. |
| `CognitiveState` | core/cognition/types.py | Agent'ın biliş durumu - tüm biliş bilgilerinin büt... |
| `ConceptNode` | core/memory/types.py | Kavram dugumu - semantic network icin. |
| `ConsciousExperience` | meta/consciousness/types.py | Butunlesik bilinc deneyimi. |
| `ConsciousnessConfig` | meta/consciousness/processor.py | Bilinc islemcisi yapilandirmasi. |
| `ConsciousnessOutput` | meta/consciousness/processor.py | Bilinc islemcisi ciktisi. |
| `ConsolidationTask` | core/memory/types.py | Bellek pekistirme gorevi. |
| `Construction` | core/language/construction/types.py | 3 katmanlı Construction Grammar yapısı. |
| `ConstructionForm` | core/language/construction/types.py | Construction'ın yüzey formu. |
| `ConstructionGrammarConfig` | core/language/construction/grammar.py | ConstructionGrammar konfigürasyonu. |
| `ConstructionMeaning` | core/language/construction/types.py | Construction'ın anlamı. |
| `ConstructionRealizerConfig` | core/language/construction/realizer.py | ConstructionRealizer konfigürasyonu. |
| `ConstructionScore` | core/language/construction/selector.py | Construction skorlaması. |
| `ConstructionSelectorConfig` | core/language/construction/selector.py | ConstructionSelector konfigürasyonu. |
| `ConstructionStats` | core/learning/feedback_stats.py | Bir construction için feedback istatistikleri. |
| `ContentPoint` | core/language/dialogue/message_planner.py | İçerik noktası - MessagePlan'da ne söylenecek. |
| `Context` | foundation/types/base.py | İşlem context'i - her modüle iletilen bağlam bilgi... |
| `ContextConfig` | core/language/context.py | Context builder yapilandirmasi. |
| `ContextConfig` | core/language/conversation/types.py | ContextManager konfigürasyonu. |
| `ContextSection` | core/language/context.py | Context bolumu. |
| `Conversation` | core/memory/types.py | Sohbet oturumu - DialogueTurn'lerin koleksiyonu. |
| `ConversationConfig` | core/memory/conversation.py | Conversation memory yapilandirmasi. |
| `ConversationContext` | core/language/conversation/types.py | Multi-turn konuşma bağlamı. |
| `CritiqueResult` | core/language/pipeline/self_critique.py | Self critique sonucu. |
| `CycleAnalysisResult` | meta/metamind/types.py | Tek cycle analiz sonucu. |
| `CycleConfig` | engine/cycle.py | Cycle yapılandırması. |
| `CycleMetrics` | meta/monitoring/metrics/cycle.py | Tek bir cycle'ın tüm metrikleri. |
| `CycleResult` | foundation/types/results.py | Tek bir cognitive cycle'ın sonucu. |
| `CycleState` | engine/cycle.py | Cycle'ın anlık durumu. |
| `DialogueTurn` | core/memory/types.py | Tek bir diyalog turu - kullanici veya ajan mesaji. |
| `EmbeddingConfig` | core/memory/types.py | Embedding encoder yapilandirmasi. |
| `EmbeddingResult` | core/memory/types.py | Semantic search sonucu. |
| `EmotionConfig` | core/affect/emotion/core/dynamics.py | Duygu dinamiği yapılandırması. |
| `EmotionProfile` | core/affect/emotion/core/emotions.py | Bir duygunun tam profili. |
| `EmotionState` | core/affect/emotion/core/dynamics.py | Dinamik duygu durumu. |
| `EmotionalMemory` | core/memory/types.py | Duygusal ani - affect-tagged memory. |
| `EmotionalState` | core/language/dialogue/types.py | Duygusal durum - Affect modülünden gelen PAD değer... |
| `EmpathyChannels` | core/affect/social/empathy/channels.py | 4 kanalın birleşik sonucu. |
| `EmpathyConfig` | core/affect/social/empathy/empathy.py | Empati modülü yapılandırması. |
| `EmpathyResult` | core/affect/social/empathy/simulation.py | Empati hesaplama sonucu. |
| `Entity` | foundation/types/base.py | Algılanan varlık (agent, object, location). |
| `Episode` | core/memory/types.py | Olay kaydi - ne, nerede, ne zaman, kim. |
| `Episode` | core/learning/episode.py | Episode - Tek bir etkilesimin tam kaydi. |
| `EpisodeCollection` | core/learning/episode.py | Episode kolleksiyonu - Birden fazla episode'u grup... |
| `EpisodeLog` | core/learning/episode_types.py | Episode Log - Tek bir conversation turn'ünün kapsa... |
| `EpisodeOutcome` | core/learning/episode.py | Episode sonucu - Etkilesimin nasil sonuclandigini ... |
| `EpisodeSummary` | core/memory/types.py | Episode ozeti - hizli erisim icin. |
| `EvaluationConfig` | core/cognition/evaluation/__init__.py | Değerlendirme yapılandırması. |
| `Event` | engine/events/bus.py | Sistem event'i. |
| `ExecutiveConfig` | engine/handlers/executive.py | Executive fazları yapılandırması. |
| `ExecutiveResult` | foundation/types/results.py | Executive modülü sonucu. |
| `ExtractorConfig` | core/perception/extractor.py | Feature extractor yapilandirmasi. |
| `Feedback` | core/learning/types.py | Geri bildirim kaydi. |
| `FeedbackWeighterConfig` | core/learning/feedback.py | FeedbackWeighter konfigurasyonu. |
| `FilterConfig` | core/perception/filters.py | Filtre yapilandirmasi. |
| `FunctionInfo` | scripts/generate_docs.py | Bir fonksiyon hakkinda bilgi. |
| `GlobalWorkspaceConfig` | meta/consciousness/integration.py | Global Workspace yapilandirmasi. |
| `GlobalWorkspaceState` | meta/consciousness/types.py | Global Workspace durumu. |
| `Goal` | core/cognition/types.py | Bir hedef temsili. |
| `Identity` | core/self/types.py | Kimlik temsili. |
| `IdentityConfig` | core/self/identity/__init__.py | Kimlik modulu yapilandirmasi. |
| `IdentityTrait` | core/self/types.py | Bir kimlik ozelligi. |
| `ImplicitFeedback` | core/learning/episode_types.py | Dolaylı geri bildirim sinyalleri. |
| `ImplicitSignals` | core/learning/feedback.py | Implicit (davranistan cikarilan) sinyaller. |
| `IndexEntry` | core/memory/semantic.py | Internal index entry. |
| `InferenceRule` | core/cognition/reasoning/__init__.py | Çıkarım kuralı. |
| `Insight` | meta/metamind/types.py | Ogrenilen bir ders/icigor. |
| `InsightGeneratorConfig` | meta/metamind/insights.py | InsightGenerator yapilandirmasi. |
| `IntentMatch` | core/language/intent/types.py | Bir intent eşleşmesi. |
| `IntentRecognizerConfig` | core/language/intent/recognizer.py | IntentRecognizer konfigürasyonu. |
| `IntentResult` | core/language/intent/types.py | Intent tanıma sonucu. |
| `Intention` | core/cognition/types.py | Bir niyet temsili. |
| `Intention` | core/language/dialogue/types.py | Niyet temsili - Aktör ne yapmak istiyor? |
| `Interaction` | core/memory/types.py | Tek bir etkilesim kaydi. |
| `InternalApproverConfig` | core/language/risk/approver.py | InternalApprover konfigürasyonu. |
| `LLMConfig` | core/language/llm_adapter.py | LLM yapilandirmasi. |
| `LLMResponse` | core/language/llm_adapter.py | LLM yanit yapisi. |
| `LearningGoal` | meta/metamind/types.py | Ogrenme hedefi. |
| `LearningManagerConfig` | meta/metamind/learning.py | LearningManager yapilandirmasi. |
| `LearningOutcome` | core/learning/types.py | Ogrenme sonucu. |
| `MDLConfig` | core/learning/mdl.py | ApproximateMDL konfigurasyonu. |
| `MDLScore` | core/learning/mdl.py | MDL degerlendirme sonucu. |
| `MVCSConfig` | core/language/construction/mvcs.py | MVCS yapilandirmasi. |
| `MemoryConfig` | core/memory/store.py | Memory sistem yapilandirmasi. |
| `MemoryItem` | core/memory/types.py | Tum memory ogelerinin base class'i. |
| `MemoryQuery` | core/memory/types.py | Bellek sorgusu. |
| `MemoryResult` | foundation/types/results.py | Memory modülü sonucu. |
| `Message` | core/language/conversation/types.py | Tek bir konuşma mesajı. |
| `MessageConstraint` | core/language/dialogue/message_planner.py | Mesaj kısıtı - MessagePlan'da neye dikkat edilmeli... |
| `MessagePlan` | core/language/dialogue/types.py | Mesaj Planı - Executive karar çıktısı. |
| `MessagePlannerConfig` | core/language/dialogue/message_planner.py | MessagePlanner konfigürasyonu. |
| `MetaMindConfig` | meta/metamind/processor.py | MetaMindProcessor yapilandirmasi. |
| `MetaMindOutput` | meta/metamind/processor.py | MetaMindProcessor ciktisi. |
| `MetaState` | meta/metamind/types.py | MetaMind durumu. |
| `Metric` | meta/monitoring/metrics/collector.py | Tek bir metrik ölçümü. |
| `MetricSummary` | meta/monitoring/metrics/collector.py | Metrik özeti (aggregation). |
| `ModuleInfo` | scripts/generate_docs.py | Bir Python modulu hakkinda bilgi. |
| `ModuleResult` | foundation/types/results.py | Herhangi bir modülün işlem sonucu. |
| `MonitorConfig` | meta/monitoring/monitor.py | Monitor yapılandırması. |
| `MorphologyRule` | core/language/construction/types.py | Morfoloji kuralı - Yüzey katmanı ek kuralları. |
| `MotionFeatures` | core/perception/types.py | Hareket ozellikleri (proprioceptive + visual motio... |
| `NarrativeElement` | core/self/types.py | Kisisel hikayedeki bir oge. |
| `Need` | core/self/types.py | Bir ihtiyac temsili (Maslow hiyerarsisi). |
| `NeedConfig` | core/self/needs.py | Ihtiyac modulu yapilandirmasi. |
| `OpportunityItem` | core/cognition/evaluation/__init__.py | Tanımlanan bir fırsat. |
| `OrchestratorConfig` | core/affect/social/orchestrator.py | Orkestratör yapılandırması. |
| `PADState` | core/affect/emotion/core/pad.py | PAD duygu durumu. |
| `Pattern` | core/learning/types.py | Ogrenilen davranis patterni. |
| `Pattern` | meta/metamind/types.py | Tespit edilen bir kalip. |
| `PatternDetectorConfig` | meta/metamind/patterns.py | PatternDetector yapilandirmasi. |
| `PerceivedAgent` | core/perception/types.py | Algilanan ajan - baska bir UEM veya canli varlik. |
| `PerceptionHandlerConfig` | engine/handlers/perception.py | Perception handler'lari yapilandirmasi. |
| `PerceptionResult` | foundation/types/results.py | Perception modülü sonucu. |
| `PerceptualFeatures` | core/perception/types.py | Cikarilmis ozellikler - PERCEIVE fazinin ana cikti... |
| `PerceptualInput` | core/perception/types.py | Ham algi girdisi - SENSE fazina giren veri. |
| `PerceptualOutput` | core/perception/types.py | Perception modulunun tam ciktisi. |
| `PersonalGoal` | core/self/types.py | Kisisel bir hedef temsili. |
| `PersonalGoalConfig` | core/self/goals.py | Kisisel hedef modulu yapilandirmasi. |
| `PhaseConfig` | engine/phases/definitions.py | Faz yapılandırması. |
| `PhaseMetrics` | meta/monitoring/metrics/cycle.py | Tek bir phase'in metrikleri. |
| `PhaseResult` | engine/phases/definitions.py | Tek bir fazın sonucu. |
| `PipelineConfig` | core/language/pipeline/config.py | ThoughtToSpeechPipeline ana konfigurasyonu. |
| `PipelineResult` | core/language/pipeline/thought_to_speech.py | Pipeline sonucu. |
| `Plan` | core/cognition/types.py | Bir plan temsili. |
| `PlanStep` | core/cognition/types.py | Plan adımı. |
| `PlanningConfig` | core/cognition/planning.py | Planlama yapılandırması. |
| `ProcessorConfig` | core/perception/processor.py | PerceptionProcessor yapilandirmasi. |
| `Qualia` | meta/consciousness/types.py | Oznel deneyim temsili. |
| `RealizationResult` | core/language/construction/realizer.py | Gerçekleştirme sonucu. |
| `ReasoningConfig` | core/cognition/reasoning/__init__.py | Reasoning engine yapılandırması. |
| `ReasoningResult` | core/cognition/types.py | Akıl yürütme sonucu. |
| `Relationship` | core/language/dialogue/types.py | İlişki bilgisi - Aktörler arası ilişki. |
| `RelationshipContext` | core/affect/social/sympathy/calculator.py | İlişki bağlamı - sempati hesaplamada kullanılır. |
| `RelationshipRecord` | core/memory/types.py | Iliski kaydi - bir agent ile tum gecmis. |
| `ReporterConfig` | meta/monitoring/reporter.py | Reporter yapılandırması. |
| `RetrievalResult` | core/memory/types.py | Bellek getirme sonucu. |
| `RetrieveHandlerState` | engine/handlers/memory.py | Handler durumu. |
| `RetrievePhaseConfig` | engine/handlers/memory.py | RETRIEVE fazı yapılandırması. |
| `RewardConfig` | core/learning/reinforcement.py | Reward hesaplama konfigurasyonu. |
| `Risk` | core/language/dialogue/types.py | Risk bilgisi - SituationModel'deki risk temsili. |
| `RiskAssessment` | core/language/risk/types.py | Kapsamlı risk değerlendirmesi. |
| `RiskFactor` | core/language/risk/types.py | Bireysel risk faktörü. |
| `RiskItem` | core/cognition/evaluation/__init__.py | Tanımlanan bir risk. |
| `RiskScorerConfig` | core/language/risk/scorer.py | RiskScorer konfigürasyonu. |
| `Rule` | core/learning/types.py | Genellestirilmis kural - pattern'lerden cikarilmis... |
| `SelectionResult` | core/language/construction/selector.py | Seçim sonucu. |
| `SelfCritiqueConfig` | core/language/pipeline/config.py | SelfCritique konfigurasyonu. |
| `SelfOutput` | core/self/processor.py | Self processing ciktisi. |
| `SelfProcessorConfig` | core/self/processor.py | Self processor yapilandirmasi. |
| `SelfState` | core/self/types.py | Agent'in benlik durumu - tum benlik bilgilerinin b... |
| `SemanticFact` | core/memory/types.py | Anlamsal bilgi - genel bilgi, kavramlar. |
| `SensoryData` | core/perception/types.py | Birlesik duyusal veri. |
| `SensoryTrace` | core/memory/types.py | Duyusal iz - cok kisa sureli (ms-saniye). |
| `SimilarityConfig` | core/learning/similarity.py | EpisodeSimilarity konfigurasyonu. |
| `SimilarityResult` | core/learning/similarity.py | Benzerlik hesaplama sonucu. |
| `SimulationConfig` | core/affect/social/empathy/simulation.py | Simülasyon yapılandırması. |
| `SituationAssessment` | core/cognition/types.py | Mevcut durumun değerlendirmesi. |
| `SituationBuilderConfig` | core/language/dialogue/situation_builder.py | SituationBuilder konfigürasyonu. |
| `SituationModel` | core/language/dialogue/types.py | Durum Modeli - Perception + Memory + Cognition çık... |
| `Slot` | core/language/construction/types.py | Template slot tanımı. |
| `SocialAffectResult` | core/affect/social/orchestrator.py | Social affect işleminin entegre sonucu. |
| `SocialContext` | foundation/state/bridge.py | StateVector'dan okunan sosyal bağlam. |
| `StateVector` | foundation/state/vector.py | Genişletilebilir StateVector. |
| `Stimulus` | foundation/types/base.py | Dış dünyadan gelen uyaran. |
| `SympathyConfig` | core/affect/social/sympathy/calculator.py | Sempati hesaplama yapılandırması. |
| `SympathyModuleConfig` | core/affect/social/sympathy/sympathy.py | Sempati modülü yapılandırması. |
| `SympathyResponse` | core/affect/social/sympathy/types.py | Tek bir sempati tepkisi. |
| `SympathyResult` | core/affect/social/sympathy/calculator.py | Sempati hesaplama sonucu. |
| `SympathyTrigger` | core/affect/social/sympathy/types.py | Sempati tetikleme koşulu. |
| `TemporalContext` | core/language/dialogue/types.py | Zaman bağlamı - Konuşmanın zamansal özellikleri. |
| `ThreatAssessment` | core/perception/types.py | Tehdit degerlendirmesi - perception'in kritik cikt... |
| `TrustComponents` | core/affect/social/trust/types.py | Güven bileşenleri - 4 boyutlu model. |
| `TrustConfig` | core/affect/social/trust/manager.py | Güven yönetimi yapılandırması. |
| `TrustEvent` | core/affect/social/trust/types.py | Güveni etkileyen olay. |
| `TrustProfile` | core/affect/social/trust/manager.py | Bir ajan için güven profili. |
| `Value` | core/self/types.py | Bir deger temsili. |
| `ValueSystemConfig` | core/self/values/__init__.py | Deger sistemi yapilandirmasi. |
| `VisualFeatures` | core/perception/types.py | Gorsel ozellikler. |
| `WorkingMemoryItem` | core/memory/types.py | Calisma bellegi ogesi - aktif islem icin (7+-2 lim... |
| `WorkspaceContent` | meta/consciousness/types.py | Global Workspace icerigi. |

### Dataclass Details

#### `ActScore`

**File:** `core/language/dialogue/act_selector.py:40`

_Bir DialogueAct'in skoru._

#### `ActSelectionResult`

**File:** `core/language/dialogue/act_selector.py:55`

_Seçim sonucu._

#### `ActSelectorConfig`

**File:** `core/language/dialogue/act_selector.py:74`

_DialogueActSelector konfigürasyonu._

#### `Action`

**File:** `foundation/types/actions.py:32`

_Gerçekleştirilecek eylem._

**Methods:**
- `to_dict()`

#### `ActionOutcome`

**File:** `foundation/types/actions.py:60`

_Gerçekleştirilen eylemin sonucu._

#### `ActionTemplate`

**File:** `core/cognition/planning.py:71`

_Eylem şablonu._

#### `Actor`

**File:** `core/language/dialogue/types.py:88`

_Konuşmadaki aktör - Kim konuşuyor/dinliyor?_

**Methods:**
- `__post_init__()`

#### `AdaptationConfig`

**File:** `core/learning/adaptation.py:32`

_Adaptasyon konfigurasyonu._

#### `AdaptationRecord`

**File:** `core/learning/adaptation.py:40`

_Adaptasyon kaydi._

#### `AdaptationStrategy`

**File:** `meta/metamind/learning.py:53`

_Adaptasyon stratejisi._

**Methods:**
- `__post_init__()`
- `to_dict()`

#### `AffectPhaseConfig`

**File:** `engine/handlers/affect.py:35`

_FEEL fazı yapılandırması._

#### `AffectPhaseState`

**File:** `engine/handlers/affect.py:58`

_FEEL fazı için tutulan state._

#### `AffectResult`

**File:** `foundation/types/results.py:69`

_Affect modülü sonucu._

#### `AgentState`

**File:** `core/affect/social/empathy/simulation.py:38`

_Gözlemlenen ajanın durumu._

**Methods:**
- `has_emotional_cues()`

#### `AnalyzerConfig`

**File:** `meta/metamind/analyzers.py:31`

_Analyzer yapilandirmasi._

#### `ApprovalResult`

**File:** `core/language/risk/approver.py:42`

_Onay sonucu._

**Methods:**
- `is_approved()`
- `needs_modifications()`
- `is_rejected()`

#### `AttentionConfig`

**File:** `meta/consciousness/attention.py:26`

_Dikkat modulu yapilandirmasi._

#### `AttentionFilter`

**File:** `meta/consciousness/attention.py:56`

_Dikkat filtresi._

**Methods:**
- `is_blocked()`
- `is_inhibited()`
- `add_inhibition()`
- `clear_expired_inhibitions()`

#### `AttentionFocus`

**File:** `core/perception/types.py:338`

_Dikkat odagi - neye odaklaniliyor._

#### `AttentionFocus`

**File:** `meta/consciousness/types.py:83`

_Dikkat odagi._

**Methods:**
- `is_expired()`
- `priority_score()`

#### `AuditoryFeatures`

**File:** `core/perception/types.py:126`

_Isitsel ozellikler._

#### `AwarenessConfig`

**File:** `meta/consciousness/awareness.py:24`

_Farkindalik modulu yapilandirmasi._

#### `AwarenessState`

**File:** `meta/consciousness/types.py:247`

_Farkindalik durumu._

**Methods:**
- `quality()`

#### `Belief`

**File:** `core/cognition/types.py:104`

_Bir inanç/bilgi temsili._

**Methods:**
- `strength()`
- `update_confidence()`
- `add_evidence()`
- `add_contradiction()`
- `is_valid()`

#### `BroadcastListener`

**File:** `meta/consciousness/integration.py:68`

_Yayin dinleyicisi._

**Methods:**
- `accepts()`

#### `ChannelResult`

**File:** `core/affect/social/empathy/channels.py:27`

_Tek bir kanalın sonucu._

#### `ChatConfig`

**File:** `core/language/chat_agent.py:81`

_Chat agent yapilandirmasi._

#### `ChatResponse`

**File:** `core/language/chat_agent.py:98`

_Chat yanit yapisi._

#### `ClassInfo`

**File:** `scripts/generate_docs.py:29`

_Bir class hakkinda bilgi._

#### `CognitionConfig`

**File:** `core/cognition/processor.py:61`

_Biliş işlemci yapılandırması._

#### `CognitionHandlerConfig`

**File:** `engine/handlers/cognition.py:45`

_Cognition handler'ları yapılandırması._

#### `CognitionOutput`

**File:** `core/cognition/processor.py:94`

_Biliş işleme çıktısı._

**Methods:**
- `to_dict()`

#### `CognitionResult`

**File:** `foundation/types/results.py:54`

_Cognition modülü sonucu._

#### `CognitiveState`

**File:** `core/cognition/types.py:490`

_Agent'ın biliş durumu - tüm biliş bilgilerinin bütünü._

**Methods:**
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

#### `ConceptNode`

**File:** `core/memory/types.py:251`

_Kavram dugumu - semantic network icin._

#### `ConsciousExperience`

**File:** `meta/consciousness/types.py:391`

_Butunlesik bilinc deneyimi._

**Methods:**
- `richness()`
- `add_qualia()`
- `summary()`

#### `ConsciousnessConfig`

**File:** `meta/consciousness/processor.py:35`

_Bilinc islemcisi yapilandirmasi._

#### `ConsciousnessOutput`

**File:** `meta/consciousness/processor.py:63`

_Bilinc islemcisi ciktisi._

#### `ConsolidationTask`

**File:** `core/memory/types.py:454`

_Bellek pekistirme gorevi._

#### `Construction`

**File:** `core/language/construction/types.py:276`

_3 katmanlı Construction Grammar yapısı._

**Methods:**
- `__post_init__()`
- `success_rate()`
- `total_uses()`
- `is_reliable()`
- `record_success()`
- `record_failure()`
- `realize()`
- `matches_dialogue_act()`
- `to_dict()`

#### `ConstructionForm`

**File:** `core/language/construction/types.py:181`

_Construction'ın yüzey formu._

**Methods:**
- `get_slot_names()`
- `has_slot()`
- `get_required_slots()`
- `validate_slots()`

#### `ConstructionGrammarConfig`

**File:** `core/language/construction/grammar.py:31`

_ConstructionGrammar konfigürasyonu._

#### `ConstructionMeaning`

**File:** `core/language/construction/types.py:236`

_Construction'ın anlamı._

**Methods:**
- `matches_context()`

#### `ConstructionRealizerConfig`

**File:** `core/language/construction/realizer.py:47`

_ConstructionRealizer konfigürasyonu._

#### `ConstructionScore`

**File:** `core/language/construction/selector.py:32`

_Construction skorlaması._

#### `ConstructionSelectorConfig`

**File:** `core/language/construction/selector.py:72`

_ConstructionSelector konfigürasyonu._

#### `ConstructionStats`

**File:** `core/learning/feedback_stats.py:18`

_Bir construction için feedback istatistikleri._

**Methods:**
- `to_dict()`
- `from_dict()`
- `total_explicit()`
- `total_implicit()`
- `total_feedback()`
- `explicit_ratio()`
- `implicit_ratio()`

#### `ContentPoint`

**File:** `core/language/dialogue/message_planner.py:66`

_İçerik noktası - MessagePlan'da ne söylenecek._

**Methods:**
- `__post_init__()`

#### `Context`

**File:** `foundation/types/base.py:35`

_İşlem context'i - her modüle iletilen bağlam bilgisi._

**Methods:**
- `with_source()`

#### `ContextConfig`

**File:** `core/language/context.py:22`

_Context builder yapilandirmasi._

#### `ContextConfig`

**File:** `core/language/conversation/types.py:116`

_ContextManager konfigürasyonu._

#### `ContextSection`

**File:** `core/language/context.py:34`

_Context bolumu._

#### `Conversation`

**File:** `core/memory/types.py:543`

_Sohbet oturumu - DialogueTurn'lerin koleksiyonu.
Episodik bellek ile entegre calisir._

**Methods:**
- `add_turn()`
- `get_last_n_turns()`
- `get_context_window()`
- `end_conversation()`
- `get_duration_seconds()`
- `to_text()`

#### `ConversationConfig`

**File:** `core/memory/conversation.py:33`

_Conversation memory yapilandirmasi._

#### `ConversationContext`

**File:** `core/language/conversation/types.py:48`

_Multi-turn konuşma bağlamı._

**Methods:**
- `get_recent_messages()`
- `get_user_messages()`
- `get_assistant_messages()`
- `get_last_user_message()`
- `get_last_assistant_message()`
- `message_count()`
- `is_empty()`
- `session_duration_seconds()`

#### `CritiqueResult`

**File:** `core/language/pipeline/self_critique.py:29`

_Self critique sonucu._

**Methods:**
- `__post_init__()`
- `needs_revision()`
- `violation_count()`
- `has_critical_violation()`

#### `CycleAnalysisResult`

**File:** `meta/metamind/types.py:83`

_Tek cycle analiz sonucu._

**Methods:**
- `get_performance_score()`
- `to_dict()`

#### `CycleConfig`

**File:** `engine/cycle.py:33`

_Cycle yapılandırması._

#### `CycleMetrics`

**File:** `meta/monitoring/metrics/cycle.py:39`

_Tek bir cycle'ın tüm metrikleri._

**Methods:**
- `record_phase_start()`
- `record_phase_end()`
- `record_memory_retrieval()`
- `record_memory_store()`
- `record_trust_change()`
- `finalize()`
- `to_dict()`
- `get_phase_summary()`
- `get_slowest_phase()`

#### `CycleResult`

**File:** `foundation/types/results.py:87`

_Tek bir cognitive cycle'ın sonucu._

**Methods:**
- `get_result()`

#### `CycleState`

**File:** `engine/cycle.py:47`

_Cycle'ın anlık durumu._

**Methods:**
- `duration_ms()`
- `is_complete()`

#### `DialogueTurn`

**File:** `core/memory/types.py:512`

_Tek bir diyalog turu - kullanici veya ajan mesaji.
Sohbet gecmisinin temel birimi._

#### `EmbeddingConfig`

**File:** `core/memory/types.py:665`

_Embedding encoder yapilandirmasi._

#### `EmbeddingResult`

**File:** `core/memory/types.py:678`

_Semantic search sonucu._

#### `EmotionConfig`

**File:** `core/affect/emotion/core/dynamics.py:38`

_Duygu dinamiği yapılandırması._

#### `EmotionProfile`

**File:** `core/affect/emotion/core/emotions.py:68`

_Bir duygunun tam profili._

#### `EmotionState`

**File:** `core/affect/emotion/core/dynamics.py:59`

_Dinamik duygu durumu._

**Methods:**
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

#### `EmotionalMemory`

**File:** `core/memory/types.py:275`

_Duygusal ani - affect-tagged memory.
Duygusal olarak yuklu anilar daha guclu hatirlanir._

#### `EmotionalState`

**File:** `core/language/dialogue/types.py:212`

_Duygusal durum - Affect modülünden gelen PAD değerleri._

**Methods:**
- `__post_init__()`

#### `EmpathyChannels`

**File:** `core/affect/social/empathy/channels.py:42`

_4 kanalın birleşik sonucu._

**Methods:**
- `__post_init__()`
- `get()`
- `weighted_average()`
- `to_dict()`
- `dominant_channel()`

#### `EmpathyConfig`

**File:** `core/affect/social/empathy/empathy.py:49`

_Empati modülü yapılandırması._

#### `EmpathyResult`

**File:** `core/affect/social/empathy/simulation.py:462`

_Empati hesaplama sonucu._

**Methods:**
- `get_dominant_channel()`
- `get_inferred_emotion()`
- `to_dict()`

#### `Entity`

**File:** `foundation/types/base.py:57`

_Algılanan varlık (agent, object, location)._

**Methods:**
- `get()`

#### `Episode`

**File:** `core/memory/types.py:177`

_Olay kaydi - ne, nerede, ne zaman, kim.
Autobiographical memory._

#### `Episode`

**File:** `core/learning/episode.py:76`

_Episode - Tek bir etkilesimin tam kaydi._

**Methods:**
- `__post_init__()`
- `success()`
- `word_count()`
- `has_emotion()`
- `dialogue_act_count()`
- `construction_count()`
- `to_dict()`
- `from_dict()`

#### `EpisodeCollection`

**File:** `core/learning/episode.py:210`

_Episode kolleksiyonu - Birden fazla episode'u gruplar._

**Methods:**
- `add()`
- `get_successful()`
- `get_by_intent()`
- `get_by_emotion()`
- `get_recent()`
- `success_rate()`
- `average_trust_delta()`

#### `EpisodeLog`

**File:** `core/learning/episode_types.py:135`

_Episode Log - Tek bir conversation turn'ünün kapsamlı kaydı._

**Methods:**
- `__post_init__()`
- `has_explicit_feedback()`
- `has_implicit_feedback()`
- `overall_feedback_score()`
- `is_successful()`
- `has_compound_intent()`
- `trust_delta()`
- `to_dict()`
- `from_dict()`

#### `EpisodeOutcome`

**File:** `core/learning/episode.py:27`

_Episode sonucu - Etkilesimin nasil sonuclandigini kaydeder._

**Methods:**
- `__post_init__()`
- `overall_score()`
- `has_positive_outcome()`

#### `EpisodeSummary`

**File:** `core/memory/types.py:213`

_Episode ozeti - hizli erisim icin._

#### `EvaluationConfig`

**File:** `core/cognition/evaluation/__init__.py:40`

_Değerlendirme yapılandırması._

#### `Event`

**File:** `engine/events/bus.py:62`

_Sistem event'i._

#### `ExecutiveConfig`

**File:** `engine/handlers/executive.py:30`

_Executive fazları yapılandırması._

#### `ExecutiveResult`

**File:** `foundation/types/results.py:78`

_Executive modülü sonucu._

#### `ExtractorConfig`

**File:** `core/perception/extractor.py:36`

_Feature extractor yapilandirmasi._

#### `Feedback`

**File:** `core/learning/types.py:40`

_Geri bildirim kaydi._

**Methods:**
- `__post_init__()`

#### `FeedbackWeighterConfig`

**File:** `core/learning/feedback.py:386`

_FeedbackWeighter konfigurasyonu._

#### `FilterConfig`

**File:** `core/perception/filters.py:32`

_Filtre yapilandirmasi._

#### `FunctionInfo`

**File:** `scripts/generate_docs.py:42`

_Bir fonksiyon hakkinda bilgi._

#### `GlobalWorkspaceConfig`

**File:** `meta/consciousness/integration.py:33`

_Global Workspace yapilandirmasi._

#### `GlobalWorkspaceState`

**File:** `meta/consciousness/types.py:279`

_Global Workspace durumu._

**Methods:**
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

#### `Goal`

**File:** `core/cognition/types.py:178`

_Bir hedef temsili._

**Methods:**
- `importance()`
- `can_start()`
- `is_achieved()`
- `is_failed()`
- `update_progress()`

#### `Identity`

**File:** `core/self/types.py:366`

_Kimlik temsili._

**Methods:**
- `add_trait()`
- `get_trait()`
- `get_traits_by_aspect()`
- `get_core_identity()`
- `add_role()`
- `identity_strength()`
- `identity_stability()`

#### `IdentityConfig`

**File:** `core/self/identity/__init__.py:25`

_Kimlik modulu yapilandirmasi._

#### `IdentityTrait`

**File:** `core/self/types.py:310`

_Bir kimlik ozelligi._

**Methods:**
- `resilience()`
- `reinforce()`
- `challenge()`

#### `ImplicitFeedback`

**File:** `core/learning/episode_types.py:74`

_Dolaylı geri bildirim sinyalleri._

**Methods:**
- `get_signal_score()`
- `to_dict()`

#### `ImplicitSignals`

**File:** `core/learning/feedback.py:435`

_Implicit (davranistan cikarilan) sinyaller._

**Methods:**
- `to_dict()`
- `from_dict()`

#### `IndexEntry`

**File:** `core/memory/semantic.py:41`

_Internal index entry._

#### `InferenceRule`

**File:** `core/cognition/reasoning/__init__.py:61`

_Çıkarım kuralı._

#### `Insight`

**File:** `meta/metamind/types.py:144`

_Ogrenilen bir ders/icigor._

**Methods:**
- `__post_init__()`
- `get_priority()`
- `to_dict()`

#### `InsightGeneratorConfig`

**File:** `meta/metamind/insights.py:25`

_InsightGenerator yapilandirmasi._

#### `IntentMatch`

**File:** `core/language/intent/types.py:41`

_Bir intent eşleşmesi._

#### `IntentRecognizerConfig`

**File:** `core/language/intent/recognizer.py:25`

_IntentRecognizer konfigürasyonu._

#### `IntentResult`

**File:** `core/language/intent/types.py:58`

_Intent tanıma sonucu._

**Methods:**
- `has_intent()`
- `get_all_categories()`

#### `Intention`

**File:** `core/cognition/types.py:260`

_Bir niyet temsili._

**Methods:**
- `priority_score()`
- `strengthen()`
- `weaken()`

#### `Intention`

**File:** `core/language/dialogue/types.py:113`

_Niyet temsili - Aktör ne yapmak istiyor?_

**Methods:**
- `__post_init__()`

#### `Interaction`

**File:** `core/memory/types.py:309`

_Tek bir etkilesim kaydi._

#### `InternalApproverConfig`

**File:** `core/language/risk/approver.py:79`

_InternalApprover konfigürasyonu._

#### `LLMConfig`

**File:** `core/language/llm_adapter.py:34`

_LLM yapilandirmasi._

**Methods:**
- `__post_init__()`

#### `LLMResponse`

**File:** `core/language/llm_adapter.py:55`

_LLM yanit yapisi._

#### `LearningGoal`

**File:** `meta/metamind/types.py:268`

_Ogrenme hedefi._

**Methods:**
- `__post_init__()`
- `update_progress()`
- `to_dict()`

#### `LearningManagerConfig`

**File:** `meta/metamind/learning.py:29`

_LearningManager yapilandirmasi._

#### `LearningOutcome`

**File:** `core/learning/types.py:90`

_Ogrenme sonucu._

#### `MDLConfig`

**File:** `core/learning/mdl.py:31`

_ApproximateMDL konfigurasyonu._

#### `MDLScore`

**File:** `core/learning/mdl.py:76`

_MDL degerlendirme sonucu._

**Methods:**
- `__post_init__()`
- `is_good_pattern()`
- `is_risky()`

#### `MVCSConfig`

**File:** `core/language/construction/mvcs.py:60`

_MVCS yapilandirmasi._

#### `MemoryConfig`

**File:** `core/memory/store.py:46`

_Memory sistem yapilandirmasi._

#### `MemoryItem`

**File:** `core/memory/types.py:93`

_Tum memory ogelerinin base class'i._

**Methods:**
- `touch()`
- `decay()`
- `is_forgotten()`

#### `MemoryQuery`

**File:** `core/memory/types.py:475`

_Bellek sorgusu._

#### `MemoryResult`

**File:** `foundation/types/results.py:62`

_Memory modülü sonucu._

#### `Message`

**File:** `core/language/conversation/types.py:21`

_Tek bir konuşma mesajı._

**Methods:**
- `is_user()`
- `is_assistant()`

#### `MessageConstraint`

**File:** `core/language/dialogue/message_planner.py:88`

_Mesaj kısıtı - MessagePlan'da neye dikkat edilmeli._

#### `MessagePlan`

**File:** `core/language/dialogue/types.py:304`

_Mesaj Planı - Executive karar çıktısı._

**Methods:**
- `__post_init__()`
- `primary_act()`
- `has_emotional_act()`
- `has_boundary_act()`
- `has_warning_act()`

#### `MessagePlannerConfig`

**File:** `core/language/dialogue/message_planner.py:103`

_MessagePlanner konfigürasyonu._

#### `MetaMindConfig`

**File:** `meta/metamind/processor.py:34`

_MetaMindProcessor yapilandirmasi._

#### `MetaMindOutput`

**File:** `meta/metamind/processor.py:62`

_MetaMindProcessor ciktisi._

**Methods:**
- `to_dict()`

#### `MetaState`

**File:** `meta/metamind/types.py:345`

_MetaMind durumu._

**Methods:**
- `to_dict()`

#### `Metric`

**File:** `meta/monitoring/metrics/collector.py:15`

_Tek bir metrik ölçümü._

#### `MetricSummary`

**File:** `meta/monitoring/metrics/collector.py:27`

_Metrik özeti (aggregation)._

#### `ModuleInfo`

**File:** `scripts/generate_docs.py:53`

_Bir Python modulu hakkinda bilgi._

#### `ModuleResult`

**File:** `foundation/types/results.py:23`

_Herhangi bir modülün işlem sonucu._

**Methods:**
- `is_success()`
- `is_failed()`

#### `MonitorConfig`

**File:** `meta/monitoring/monitor.py:19`

_Monitor yapılandırması._

#### `MorphologyRule`

**File:** `core/language/construction/types.py:153`

_Morfoloji kuralı - Yüzey katmanı ek kuralları._

#### `MotionFeatures`

**File:** `core/perception/types.py:152`

_Hareket ozellikleri (proprioceptive + visual motion)._

#### `NarrativeElement`

**File:** `core/self/types.py:443`

_Kisisel hikayedeki bir oge._

**Methods:**
- `significance()`

#### `Need`

**File:** `core/self/types.py:162`

_Bir ihtiyac temsili (Maslow hiyerarsisi)._

**Methods:**
- `priority_score()`
- `update_satisfaction()`
- `deprive()`
- `satisfy()`

#### `NeedConfig`

**File:** `core/self/needs.py:24`

_Ihtiyac modulu yapilandirmasi._

#### `OpportunityItem`

**File:** `core/cognition/evaluation/__init__.py:90`

_Tanımlanan bir fırsat._

**Methods:**
- `expected_value()`

#### `OrchestratorConfig`

**File:** `core/affect/social/orchestrator.py:192`

_Orkestratör yapılandırması._

#### `PADState`

**File:** `core/affect/emotion/core/pad.py:20`

_PAD duygu durumu._

**Methods:**
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

#### `Pattern`

**File:** `core/learning/types.py:58`

_Ogrenilen davranis patterni._

**Methods:**
- `success_rate()`
- `average_reward()`
- `total_uses()`

#### `Pattern`

**File:** `meta/metamind/types.py:202`

_Tespit edilen bir kalip._

**Methods:**
- `__post_init__()`
- `update_occurrence()`
- `to_dict()`

#### `PatternDetectorConfig`

**File:** `meta/metamind/patterns.py:25`

_PatternDetector yapilandirmasi._

#### `PerceivedAgent`

**File:** `core/perception/types.py:235`

_Algilanan ajan - baska bir UEM veya canli varlik._

#### `PerceptionHandlerConfig`

**File:** `engine/handlers/perception.py:45`

_Perception handler'lari yapilandirmasi._

#### `PerceptionResult`

**File:** `foundation/types/results.py:46`

_Perception modülü sonucu._

#### `PerceptualFeatures`

**File:** `core/perception/types.py:367`

_Cikarilmis ozellikler - PERCEIVE fazinin ana ciktisi._

**Methods:**
- `get_primary_agent()`
- `get_threatening_agents()`

#### `PerceptualInput`

**File:** `core/perception/types.py:194`

_Ham algi girdisi - SENSE fazina giren veri._

**Methods:**
- `get_modality()`
- `has_modality()`

#### `PerceptualOutput`

**File:** `core/perception/types.py:421`

_Perception modulunun tam ciktisi._

**Methods:**
- `to_dict()`

#### `PersonalGoal`

**File:** `core/self/types.py:243`

_Kisisel bir hedef temsili._

**Methods:**
- `total_motivation()`
- `milestone_progress()`
- `achieve_milestone()`
- `update_progress()`

#### `PersonalGoalConfig`

**File:** `core/self/goals.py:25`

_Kisisel hedef modulu yapilandirmasi._

#### `PhaseConfig`

**File:** `engine/phases/definitions.py:74`

_Faz yapılandırması._

#### `PhaseMetrics`

**File:** `meta/monitoring/metrics/cycle.py:22`

_Tek bir phase'in metrikleri._

#### `PhaseResult`

**File:** `engine/phases/definitions.py:84`

_Tek bir fazın sonucu._

**Methods:**
- `status_str()`

#### `PipelineConfig`

**File:** `core/language/pipeline/config.py:42`

_ThoughtToSpeechPipeline ana konfigurasyonu._

**Methods:**
- `__post_init__()`
- `minimal()`
- `strict()`
- `balanced()`
- `with_self_critique()`
- `with_risk_level()`

#### `PipelineResult`

**File:** `core/language/pipeline/thought_to_speech.py:68`

_Pipeline sonucu._

**Methods:**
- `id()`
- `is_approved()`
- `risk_level()`
- `was_revised()`
- `failure()`

#### `Plan`

**File:** `core/cognition/types.py:336`

_Bir plan temsili._

**Methods:**
- `total_steps()`
- `progress()`
- `next_step()`
- `add_step()`
- `advance()`
- `fail_current()`

#### `PlanStep`

**File:** `core/cognition/types.py:324`

_Plan adımı._

#### `PlanningConfig`

**File:** `core/cognition/planning.py:44`

_Planlama yapılandırması._

#### `ProcessorConfig`

**File:** `core/perception/processor.py:40`

_PerceptionProcessor yapilandirmasi._

#### `Qualia`

**File:** `meta/consciousness/types.py:139`

_Oznel deneyim temsili._

**Methods:**
- `phenomenal_strength()`

#### `RealizationResult`

**File:** `core/language/construction/realizer.py:26`

_Gerçekleştirme sonucu._

#### `ReasoningConfig`

**File:** `core/cognition/reasoning/__init__.py:34`

_Reasoning engine yapılandırması._

#### `ReasoningResult`

**File:** `core/cognition/types.py:423`

_Akıl yürütme sonucu._

**Methods:**
- `quality_score()`

#### `Relationship`

**File:** `core/language/dialogue/types.py:164`

_İlişki bilgisi - Aktörler arası ilişki._

**Methods:**
- `__post_init__()`

#### `RelationshipContext`

**File:** `core/affect/social/sympathy/calculator.py:35`

_İlişki bağlamı - sempati hesaplamada kullanılır._

**Methods:**
- `stranger()`
- `friend()`
- `rival()`
- `from_relationship_type()`

#### `RelationshipRecord`

**File:** `core/memory/types.py:331`

_Iliski kaydi - bir agent ile tum gecmis.
Trust modulu icin birincil kaynak!_

**Methods:**
- `add_interaction()`
- `get_trust_recommendation()`

#### `ReporterConfig`

**File:** `meta/monitoring/reporter.py:20`

_Reporter yapılandırması._

#### `RetrievalResult`

**File:** `core/memory/types.py:497`

_Bellek getirme sonucu._

#### `RetrieveHandlerState`

**File:** `engine/handlers/memory.py:62`

_Handler durumu._

#### `RetrievePhaseConfig`

**File:** `engine/handlers/memory.py:41`

_RETRIEVE fazı yapılandırması._

#### `RewardConfig`

**File:** `core/learning/reinforcement.py:30`

_Reward hesaplama konfigurasyonu._

#### `Risk`

**File:** `core/language/dialogue/types.py:139`

_Risk bilgisi - SituationModel'deki risk temsili._

**Methods:**
- `__post_init__()`

#### `RiskAssessment`

**File:** `core/language/risk/types.py:135`

_Kapsamlı risk değerlendirmesi._

**Methods:**
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

#### `RiskFactor`

**File:** `core/language/risk/types.py:94`

_Bireysel risk faktörü._

**Methods:**
- `__post_init__()`
- `is_high()`
- `is_critical()`

#### `RiskItem`

**File:** `core/cognition/evaluation/__init__.py:73`

_Tanımlanan bir risk._

**Methods:**
- `severity()`

#### `RiskScorerConfig`

**File:** `core/language/risk/scorer.py:34`

_RiskScorer konfigürasyonu._

#### `Rule`

**File:** `core/learning/types.py:100`

_Genellestirilmis kural - pattern'lerden cikarilmis template._

**Methods:**
- `__post_init__()`

#### `SelectionResult`

**File:** `core/language/construction/selector.py:57`

_Seçim sonucu._

#### `SelfCritiqueConfig`

**File:** `core/language/pipeline/config.py:19`

_SelfCritique konfigurasyonu._

#### `SelfOutput`

**File:** `core/self/processor.py:62`

_Self processing ciktisi._

#### `SelfProcessorConfig`

**File:** `core/self/processor.py:37`

_Self processor yapilandirmasi._

#### `SelfState`

**File:** `core/self/types.py:489`

_Agent'in benlik durumu - tum benlik bilgilerinin butunu._

**Methods:**
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

#### `SemanticFact`

**File:** `core/memory/types.py:229`

_Anlamsal bilgi - genel bilgi, kavramlar.
Context-free facts._

#### `SensoryData`

**File:** `core/perception/types.py:170`

_Birlesik duyusal veri._

#### `SensoryTrace`

**File:** `core/memory/types.py:138`

_Duyusal iz - cok kisa sureli (ms-saniye).
Raw sensory input'un gecici kaydi._

#### `SimilarityConfig`

**File:** `core/learning/similarity.py:26`

_EpisodeSimilarity konfigurasyonu._

**Methods:**
- `__post_init__()`

#### `SimilarityResult`

**File:** `core/learning/similarity.py:71`

_Benzerlik hesaplama sonucu._

#### `SimulationConfig`

**File:** `core/affect/social/empathy/simulation.py:75`

_Simülasyon yapılandırması._

#### `SituationAssessment`

**File:** `core/cognition/types.py:456`

_Mevcut durumun değerlendirmesi._

#### `SituationBuilderConfig`

**File:** `core/language/dialogue/situation_builder.py:39`

_SituationBuilder konfigürasyonu._

#### `SituationModel`

**File:** `core/language/dialogue/types.py:244`

_Durum Modeli - Perception + Memory + Cognition çıktısı._

**Methods:**
- `__post_init__()`
- `get_primary_actor()`
- `get_highest_risk()`
- `has_high_risk()`

#### `Slot`

**File:** `core/language/construction/types.py:85`

_Template slot tanımı._

**Methods:**
- `validate_value()`
- `get_value()`

#### `SocialAffectResult`

**File:** `core/affect/social/orchestrator.py:118`

_Social affect işleminin entegre sonucu._

**Methods:**
- `to_dict()`
- `summary()`

#### `SocialContext`

**File:** `foundation/state/bridge.py:39`

_StateVector'dan okunan sosyal bağlam._

#### `StateVector`

**File:** `foundation/state/vector.py:16`

_Genişletilebilir StateVector._

**Methods:**
- `__post_init__()`
- `get()`
- `set()`
- `has()`
- `update()`
- `to_dict()`
- `from_dict()`
- `copy()`
- `delta()`
- `magnitude()`

#### `Stimulus`

**File:** `foundation/types/base.py:70`

_Dış dünyadan gelen uyaran._

#### `SympathyConfig`

**File:** `core/affect/social/sympathy/calculator.py:85`

_Sempati hesaplama yapılandırması._

#### `SympathyModuleConfig`

**File:** `core/affect/social/sympathy/sympathy.py:50`

_Sempati modülü yapılandırması._

#### `SympathyResponse`

**File:** `core/affect/social/sympathy/types.py:63`

_Tek bir sempati tepkisi._

**Methods:**
- `is_prosocial()`
- `is_antisocial()`

#### `SympathyResult`

**File:** `core/affect/social/sympathy/calculator.py:338`

_Sempati hesaplama sonucu._

**Methods:**
- `has_sympathy()`
- `get_action_tendency()`
- `is_prosocial()`
- `is_antisocial()`
- `to_dict()`

#### `SympathyTrigger`

**File:** `core/affect/social/sympathy/types.py:184`

_Sempati tetikleme koşulu._

**Methods:**
- `matches()`

#### `TemporalContext`

**File:** `core/language/dialogue/types.py:188`

_Zaman bağlamı - Konuşmanın zamansal özellikleri._

**Methods:**
- `conversation_duration()`

#### `ThreatAssessment`

**File:** `core/perception/types.py:292`

_Tehdit degerlendirmesi - perception'in kritik ciktisi._

**Methods:**
- `is_threatening()`
- `requires_immediate_action()`

#### `TrustComponents`

**File:** `core/affect/social/trust/types.py:78`

_Güven bileşenleri - 4 boyutlu model._

**Methods:**
- `__post_init__()`
- `overall()`
- `weakest_dimension()`
- `strongest_dimension()`
- `to_dict()`
- `copy()`
- `default()`
- `high()`
- `low()`

#### `TrustConfig`

**File:** `core/affect/social/trust/manager.py:122`

_Güven yönetimi yapılandırması._

#### `TrustEvent`

**File:** `core/affect/social/trust/types.py:177`

_Güveni etkileyen olay._

**Methods:**
- `weighted_impact()`

#### `TrustProfile`

**File:** `core/affect/social/trust/manager.py:60`

_Bir ajan için güven profili._

**Methods:**
- `__post_init__()`
- `overall_trust()`
- `trust_level()`
- `interaction_count()`
- `trust_ratio()`
- `to_dict()`

#### `Value`

**File:** `core/self/types.py:95`

_Bir deger temsili._

**Methods:**
- `priority_weight()`
- `integrity_score()`
- `express()`
- `violate()`

#### `ValueSystemConfig`

**File:** `core/self/values/__init__.py:24`

_Deger sistemi yapilandirmasi._

#### `VisualFeatures`

**File:** `core/perception/types.py:98`

_Gorsel ozellikler._

#### `WorkingMemoryItem`

**File:** `core/memory/types.py:158`

_Calisma bellegi ogesi - aktif islem icin (7+-2 limit)._

#### `WorkspaceContent`

**File:** `meta/consciousness/types.py:177`

_Global Workspace icerigi._

**Methods:**
- `competition_score()`
- `is_expired()`
- `mark_integrated()`
- `mark_broadcast()`
