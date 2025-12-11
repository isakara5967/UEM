#!/usr/bin/env python3
"""
scripts/generate_test_episodes.py

Automatic Episode Generator for Re-ranking Validation.

Generates test episodes with diverse scenarios to test the feedback-driven
construction re-ranking mechanism. Uses the ThoughtToSpeechPipeline directly
to create episodes with known feedback patterns.

Usage:
    python scripts/generate_test_episodes.py --count 100
    python scripts/generate_test_episodes.py --count 50 --verbose
    python scripts/generate_test_episodes.py --scenarios greetings,empathy

Features:
- Multiple test scenarios with expected dialogue acts
- Automatic feedback assignment (explicit)
- Variation in user inputs (each scenario repeated multiple times)
- Episode logging via pipeline integration
- Summary statistics and re-ranking validation

UEM v2 - Faz 5 Re-ranking Testing Tool.
"""

import argparse
import sys
import random
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Test scenarios: (input, expected_act, feedback, variations)
TEST_SCENARIOS = {
    "greetings": [
        ("Merhaba", "greet", 1.0, ["Merhaba", "Selam", "Selamlar", "Selamün aleyküm"]),
        ("Günaydın", "greet", 1.0, ["Günaydın", "İyi günler", "İyi sabahlar"]),
    ],
    "wellbeing": [
        ("Nasılsın?", "respond_wellbeing", 1.0,
         ["Nasılsın?", "Nasılsın", "İyi misin?", "Naber?", "Ne var ne yok?"]),
        ("Sen nasılsın?", "respond_wellbeing", 1.0,
         ["Sen nasılsın?", "Sende nasıl?", "Sen iyi misin?"]),
    ],
    "empathy": [
        ("Bugün çok yorgunum", "empathize", 1.0,
         ["Bugün çok yorgunum", "Çok yorgunum", "Yorgunum", "Çok yoruldum"]),
        ("Kendimi kötü hissediyorum", "empathize", 1.0,
         ["Kendimi kötü hissediyorum", "Kötü hissediyorum", "İyi değilim"]),
    ],
    "sympathy": [
        ("Moralim bozuk", "sympathize", -1.0,
         ["Moralim bozuk", "Moralim çok bozuk", "Keyfim yok"]),
        ("Hiçbir şey yolunda gitmiyor", "sympathize", -1.0,
         ["Hiçbir şey yolunda gitmiyor", "Her şey ters gidiyor", "Kötü bir gün"]),
    ],
    "thanks": [
        ("Teşekkürler", "accept_thanks", 1.0,
         ["Teşekkürler", "Teşekkür ederim", "Sağ ol", "Çok sağ ol", "Çok teşekkürler"]),
    ],
    "help": [
        ("Bana yardım eder misin?", "offer_help", 1.0,
         ["Bana yardım eder misin?", "Yardım edebilir misin?", "Yardıma ihtiyacım var"]),
    ],
    "inform": [
        ("Sen kimsin?", "inform", 1.0,
         ["Sen kimsin?", "Kimsin sen?", "Adın ne?", "Sen ne yapıyorsun?"]),
    ],
    "farewell": [
        ("Görüşürüz", "farewell", 1.0,
         ["Görüşürüz", "Hoşça kal", "Güle güle", "Bay bay", "Sonra görüşürüz"]),
    ],
}


class EpisodeGenerator:
    """Automatic episode generator for testing."""

    def __init__(self, verbose: bool = False):
        """
        Initialize episode generator.

        Args:
            verbose: Print detailed progress
        """
        self.verbose = verbose
        self.pipeline = None
        self.episode_logger = None
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.episodes_generated = 0
        self.feedback_added = 0

    def setup(self) -> bool:
        """
        Setup pipeline and episode logger.

        Returns:
            bool: Success status
        """
        try:
            from core.language.pipeline import ThoughtToSpeechPipeline
            from core.learning.episode_logger import EpisodeLogger
            from core.learning.episode_store import JSONLEpisodeStore

            # Setup episode store
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            episodes_path = data_dir / "episodes.jsonl"

            store = JSONLEpisodeStore(str(episodes_path))
            self.episode_logger = EpisodeLogger(store, self.session_id)

            # Setup pipeline with episode logger
            self.pipeline = ThoughtToSpeechPipeline(
                episode_logger=self.episode_logger
            )

            if self.verbose:
                print(f"✓ Pipeline initialized")
                print(f"✓ Session ID: {self.session_id}")
                print(f"✓ Episodes will be saved to: {episodes_path}")

            return True

        except ImportError as e:
            print(f"Error: Could not import required modules: {e}")
            print("Make sure all dependencies are installed.")
            return False
        except Exception as e:
            print(f"Error during setup: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_scenario(
        self,
        user_input: str,
        expected_act: str,
        feedback: float
    ) -> bool:
        """
        Generate a single episode for a scenario.

        Args:
            user_input: User message
            expected_act: Expected dialogue act
            feedback: Explicit feedback (-1.0 to 1.0)

        Returns:
            bool: Success status
        """
        try:
            # Process through pipeline
            result = self.pipeline.process(user_input)

            if not result.success:
                if self.verbose:
                    print(f"  ✗ Pipeline failed: {result.error}")
                return False

            # Episode is automatically logged by pipeline
            self.episodes_generated += 1

            # Add explicit feedback to the last episode
            if self.episode_logger:
                success = self.episode_logger.add_feedback_to_last(explicit=feedback)
                if success:
                    self.feedback_added += 1

            if self.verbose:
                # ActSelectionResult has primary_acts (list), not act
                act = "unknown"
                if result.act_selection and result.act_selection.primary_acts:
                    act = result.act_selection.primary_acts[0].value
                constr = result.constructions_used[0].id if result.constructions_used else "none"
                print(f"  ✓ '{user_input[:30]}...' -> {act} (constr: {constr}, fb: {feedback:+.1f})")

            return True

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Error: {e}")
            return False

    def generate_episodes(
        self,
        total_count: int,
        scenario_filter: List[str] = None
    ) -> Dict[str, int]:
        """
        Generate multiple episodes across scenarios.

        Args:
            total_count: Total number of episodes to generate
            scenario_filter: List of scenario names to include (None = all)

        Returns:
            Dict with generation statistics
        """
        # Filter scenarios
        scenarios = TEST_SCENARIOS
        if scenario_filter:
            scenarios = {
                k: v for k, v in TEST_SCENARIOS.items()
                if k in scenario_filter
            }

        if not scenarios:
            print("Error: No scenarios selected")
            return {"generated": 0, "failed": 0}

        # Flatten scenarios into list
        scenario_list = []
        for category, items in scenarios.items():
            for base_input, expected_act, feedback, variations in items:
                scenario_list.append((category, expected_act, feedback, variations))

        if not scenario_list:
            print("Error: No scenario items found")
            return {"generated": 0, "failed": 0}

        print(f"\nGenerating {total_count} episodes from {len(scenario_list)} scenario templates...")
        print(f"Scenarios: {', '.join(scenarios.keys())}")
        print()

        success_count = 0
        fail_count = 0

        # Generate episodes
        for i in range(total_count):
            # Pick random scenario
            category, expected_act, feedback, variations = random.choice(scenario_list)

            # Pick random variation
            user_input = random.choice(variations)

            # Generate episode
            if self.verbose:
                print(f"[{i+1}/{total_count}] {category}:")

            success = self.generate_scenario(user_input, expected_act, feedback)

            if success:
                success_count += 1
            else:
                fail_count += 1

            # Progress indicator (non-verbose)
            if not self.verbose and (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{total_count} episodes generated...")

        return {
            "generated": success_count,
            "failed": fail_count,
            "feedback_added": self.feedback_added,
        }

    def print_summary(self, stats: Dict[str, int]) -> None:
        """
        Print generation summary.

        Args:
            stats: Generation statistics
        """
        print("\n" + "="*60)
        print("EPISODE GENERATION SUMMARY")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print(f"Episodes generated: {stats['generated']}")
        print(f"Episodes failed: {stats['failed']}")
        print(f"Feedback added: {stats['feedback_added']}")
        print(f"Success rate: {stats['generated']/(stats['generated']+stats['failed'])*100:.1f}%")
        print()

    def run_aggregation(self) -> None:
        """Run feedback aggregation to compute construction stats."""
        print("Running feedback aggregation...")
        print()

        try:
            from core.learning.episode_store import JSONLEpisodeStore
            from core.learning.feedback_aggregator import FeedbackAggregator
            from core.learning.feedback_store import FeedbackStore

            # Load episodes
            episodes_path = project_root / "data" / "episodes.jsonl"
            store = JSONLEpisodeStore(str(episodes_path))
            episodes = store.get_all()

            print(f"Loaded {len(episodes)} total episodes from store")

            # Aggregate feedback
            aggregator = FeedbackAggregator()
            stats = aggregator.aggregate(episodes)

            print(f"Computed stats for {len(stats)} constructions")

            # Save to construction_stats.json
            stats_path = project_root / "data" / "construction_stats.json"
            feedback_store = FeedbackStore(stats_path)
            feedback_store.bulk_update(stats)

            print(f"Saved construction stats to: {stats_path}")
            print()

            # Show top constructions
            print("Top 10 constructions by usage:")
            sorted_stats = sorted(
                stats.items(),
                key=lambda x: x[1].total_uses,
                reverse=True
            )
            for i, (cid, s) in enumerate(sorted_stats[:10], 1):
                boost = "↑" if s.cached_score > 1.0 else "↓" if s.cached_score < 1.0 else "="
                print(
                    f"  {i:2}. {cid:30} | uses: {s.total_uses:3} | "
                    f"score: {s.cached_score:.3f} {boost} | "
                    f"feedback: +{s.explicit_pos+s.implicit_pos}/-{s.explicit_neg+s.implicit_neg}"
                )

            print()
            print("Top 10 constructions by score (re-ranking boost):")
            sorted_by_score = sorted(
                stats.items(),
                key=lambda x: x[1].cached_score,
                reverse=True
            )
            for i, (cid, s) in enumerate(sorted_by_score[:10], 1):
                if s.total_uses > 0:  # Only show used constructions
                    boost = "↑↑" if s.cached_score > 1.5 else "↑" if s.cached_score > 1.0 else "="
                    print(
                        f"  {i:2}. {cid:30} | score: {s.cached_score:.3f} {boost} | "
                        f"uses: {s.total_uses:3} | "
                        f"fb: +{s.explicit_pos+s.implicit_pos}/-{s.explicit_neg+s.implicit_neg}"
                    )

        except Exception as e:
            print(f"Error during aggregation: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate test episodes for re-ranking validation"
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=50,
        help="Number of episodes to generate (default: 50)"
    )
    parser.add_argument(
        "--scenarios", "-s",
        type=str,
        default=None,
        help="Comma-separated scenario names (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress"
    )
    parser.add_argument(
        "--no-aggregate",
        action="store_true",
        help="Skip feedback aggregation step"
    )

    args = parser.parse_args()

    # Parse scenario filter
    scenario_filter = None
    if args.scenarios:
        scenario_filter = [s.strip() for s in args.scenarios.split(",")]
        # Validate
        invalid = [s for s in scenario_filter if s not in TEST_SCENARIOS]
        if invalid:
            print(f"Error: Invalid scenario names: {', '.join(invalid)}")
            print(f"Available scenarios: {', '.join(TEST_SCENARIOS.keys())}")
            sys.exit(1)

    # Create generator
    generator = EpisodeGenerator(verbose=args.verbose)

    # Setup
    if not generator.setup():
        print("Setup failed. Exiting.")
        sys.exit(1)

    # Generate episodes
    stats = generator.generate_episodes(args.count, scenario_filter)

    # Print summary
    generator.print_summary(stats)

    # Run aggregation
    if not args.no_aggregate and stats["generated"] > 0:
        generator.run_aggregation()

    print("Done!")


if __name__ == "__main__":
    main()
