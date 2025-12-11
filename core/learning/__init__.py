"""
core/learning/__init__.py

Learning Module - Geri bildirim ve pattern ogrenme.
UEM v2 - Kullanici etkilesimlerinden ogrenme.

Components:
- FeedbackType: Geri bildirim turleri
- PatternType: Davranis pattern turleri
- Feedback: Geri bildirim kaydi
- Pattern: Ogrenilen davranis patterni
- LearningOutcome: Ogrenme sonucu
- Episode: Etkilesim kaydi
- EpisodeOutcome: Etkilesim sonucu
- EpisodeSimilarity: Benzerlik hesaplayici
- FeedbackCollector: Geri bildirim toplama
- FeedbackWeighter: Episode agirliklama (Alice uzlasisi)
- ImplicitSignals: Implicit sinyal yapisi
- PatternStorage: Pattern depolama ve arama
- RewardConfig: Reward hesaplama konfigurasyonu
- RewardCalculator: Feedback'ten reward hesaplama
- Reinforcer: Pattern guclendrme
- AdaptationConfig: Adaptasyon konfigurasyonu
- BehaviorAdapter: Davranis adaptasyonu
- LearningProcessor: Ana ogrenme koordinatoru
- MDLConfig: MDL konfigurasyonu
- MDLScore: MDL degerlendirme sonucu
- ApproximateMDL: Pattern degerlendirme (MDL prensibi)
"""

from .types import (
    FeedbackType,
    PatternType,
    Feedback,
    Pattern,
    LearningOutcome,
    Rule,
    generate_feedback_id,
    generate_pattern_id,
    generate_rule_id,
)

from .episode import (
    Episode,
    EpisodeOutcome,
    EpisodeCollection,
    generate_episode_id,
)

from .similarity import (
    SimilarityConfig,
    SimilarityResult,
    EpisodeSimilarity,
    jaccard_similarity,
    levenshtein_distance,
    levenshtein_similarity,
)

from .feedback import (
    FeedbackCollector,
    FeedbackWeighter,
    FeedbackWeighterConfig,
    ImplicitSignals,
)

from .patterns import PatternStorage

from .reinforcement import (
    RewardConfig,
    RewardCalculator,
    Reinforcer,
)

from .adaptation import (
    AdaptationConfig,
    AdaptationRecord,
    BehaviorAdapter,
)

from .generalization import RuleExtractor

from .processor import LearningProcessor

from .mdl import (
    MDLConfig,
    MDLScore,
    ApproximateMDL,
)

# Faz 5 - Episode Logging System
from .episode_types import (
    EpisodeLog,
    ImplicitFeedback as Faz5ImplicitFeedback,
    ConstructionSource,
    ConstructionLevel,
    ApprovalStatus,
    generate_episode_log_id,
)
from .episode_store import EpisodeStore, JSONLEpisodeStore
from .episode_logger import EpisodeLogger
from .pattern_analyzer import PatternAnalyzer, create_analyzer


__all__ = [
    # Enums
    "FeedbackType",
    "PatternType",
    # Dataclasses
    "Feedback",
    "Pattern",
    "LearningOutcome",
    "Rule",
    "Episode",
    "EpisodeOutcome",
    "EpisodeCollection",
    "SimilarityConfig",
    "SimilarityResult",
    "FeedbackWeighterConfig",
    "ImplicitSignals",
    "RewardConfig",
    "AdaptationConfig",
    "AdaptationRecord",
    # Utility functions
    "generate_feedback_id",
    "generate_pattern_id",
    "generate_rule_id",
    "generate_episode_id",
    "jaccard_similarity",
    "levenshtein_distance",
    "levenshtein_similarity",
    # Classes
    "EpisodeSimilarity",
    "FeedbackCollector",
    "FeedbackWeighter",
    "PatternStorage",
    "RewardCalculator",
    "Reinforcer",
    "BehaviorAdapter",
    "RuleExtractor",
    "LearningProcessor",
    "MDLConfig",
    "MDLScore",
    "ApproximateMDL",
    # Faz 5 - Episode Logging
    "EpisodeLog",
    "Faz5ImplicitFeedback",
    "ConstructionSource",
    "ConstructionLevel",
    "ApprovalStatus",
    "generate_episode_log_id",
    "EpisodeStore",
    "JSONLEpisodeStore",
    "EpisodeLogger",
    # Pattern Analyzer
    "PatternAnalyzer",
    "create_analyzer",
]
