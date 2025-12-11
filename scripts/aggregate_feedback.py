#!/usr/bin/env python
"""
scripts/aggregate_feedback.py

Episode loglarından construction feedback stats hesapla.

Episode JSONL dosyasını okur, her construction için
feedback istatistiklerini aggregate eder ve JSON'a kaydeder.

Kullanım:
    python scripts/aggregate_feedback.py
    python scripts/aggregate_feedback.py --episodes data/episodes.jsonl
    python scripts/aggregate_feedback.py --output data/construction_stats.json
    python scripts/aggregate_feedback.py -v  # verbose

UEM v2 - Faz 5 Feedback-Driven Learning.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate episode feedback into construction stats"
    )
    parser.add_argument(
        "--episodes",
        default="data/episodes.jsonl",
        help="Episode JSONL dosya yolu (default: data/episodes.jsonl)"
    )
    parser.add_argument(
        "--output",
        default="data/construction_stats.json",
        help="Çıktı JSON dosya yolu (default: data/construction_stats.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Detaylı çıktı göster"
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=10,
        help="En çok kullanılan N construction'ı göster (default: 10)"
    )
    args = parser.parse_args()

    # Imports
    try:
        from core.learning.episode_store import JSONLEpisodeStore
        from core.learning.feedback_aggregator import FeedbackAggregator
        from core.learning.feedback_store import FeedbackStore
    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("Make sure you're running from the project root directory.")
        sys.exit(1)

    # Check if episodes file exists
    episodes_path = Path(args.episodes)
    if not episodes_path.exists():
        print(f"Error: Episodes file not found: {episodes_path}")
        print("Run some chat sessions first to generate episode data.")
        sys.exit(1)

    # Load episodes
    print(f"Loading episodes from {episodes_path}...")
    episode_store = JSONLEpisodeStore(str(episodes_path))
    episodes = episode_store.get_all()

    if not episodes:
        print("No episodes found. Run some chat sessions first.")
        sys.exit(0)

    print(f"Loaded {len(episodes)} episodes")

    # Aggregate
    print("\nAggregating feedback...")
    aggregator = FeedbackAggregator()
    stats = aggregator.aggregate(episodes)

    print(f"Computed stats for {len(stats)} constructions")

    # Get summary
    summary = aggregator.get_summary(stats)
    print(f"\n--- Summary ---")
    print(f"Total uses: {summary['total_uses']}")
    print(f"Explicit feedback: {summary['total_explicit_feedback']} (+{summary['explicit_positive']} / -{summary['explicit_negative']})")
    print(f"Implicit feedback: {summary['total_implicit_feedback']} (+{summary['implicit_positive']} / -{summary['implicit_negative']})")
    print(f"Average score: {summary['average_score']:.3f}")

    # Save
    output_path = Path(args.output)
    print(f"\nSaving to {output_path}...")
    feedback_store = FeedbackStore(output_path)
    feedback_store.bulk_update(stats)
    print(f"Saved {len(stats)} construction stats")

    # Verbose output
    if args.verbose:
        print(f"\n--- Top {args.top} by usage ---")
        sorted_stats = sorted(
            stats.items(),
            key=lambda x: x[1].total_uses,
            reverse=True
        )
        for cid, s in sorted_stats[:args.top]:
            print(
                f"  {cid}: uses={s.total_uses}, "
                f"+exp={s.explicit_pos}, -exp={s.explicit_neg}, "
                f"+imp={s.implicit_pos}, -imp={s.implicit_neg}, "
                f"score={s.cached_score:.3f}"
            )

        print(f"\n--- Top {args.top} by score ---")
        sorted_by_score = sorted(
            stats.items(),
            key=lambda x: x[1].cached_score,
            reverse=True
        )
        for cid, s in sorted_by_score[:args.top]:
            print(
                f"  {cid}: score={s.cached_score:.3f}, "
                f"uses={s.total_uses}, "
                f"feedback=+{s.explicit_pos + s.implicit_pos}/-{s.explicit_neg + s.implicit_neg}"
            )

    print("\nDone!")


if __name__ == "__main__":
    main()
