#!/usr/bin/env python3
"""
scripts/analyze_episodes.py

Standalone Episode Pattern Analysis Script.

Episode JSONL verilerinden pattern analizi yapar ve rapor uretir.
Raporu konsola ve data/analysis_report.md dosyasina yazar.

Kullanim:
    python scripts/analyze_episodes.py
    python scripts/analyze_episodes.py --output custom_report.md
    python scripts/analyze_episodes.py --episodes data/episodes.jsonl

UEM v2 - Faz 5 Pattern Evolution Analytics.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.learning import PatternAnalyzer, JSONLEpisodeStore


def main():
    """Run episode pattern analysis."""
    parser = argparse.ArgumentParser(
        description="Episode Pattern Analysis - JSONL verilerinden istatistik ve rapor uretur"
    )
    parser.add_argument(
        "--episodes", "-e",
        default="data/episodes.jsonl",
        help="Episode JSONL dosya yolu (default: data/episodes.jsonl)"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/analysis_report.md",
        help="Rapor cikti dosyasi (default: data/analysis_report.md)"
    )
    parser.add_argument(
        "--no-file",
        action="store_true",
        help="Dosyaya yazma, sadece konsola yazdir"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Sadece dosyaya yaz, konsola yazdirma"
    )

    args = parser.parse_args()

    # Check if episodes file exists
    episodes_path = Path(args.episodes)
    if not episodes_path.exists():
        print(f"Hata: Episode dosyasi bulunamadi: {args.episodes}")
        print("Once birkac episode olusturun:")
        print("  python -m interface.chat.cli --pipeline")
        print("  (birkac mesaj yazin, /good veya /bad ile feedback verin)")
        print("  /quit")
        sys.exit(1)

    # Check if file is empty
    if episodes_path.stat().st_size == 0:
        print(f"Hata: Episode dosyasi bos: {args.episodes}")
        print("Once birkac episode olusturun.")
        sys.exit(1)

    # Create analyzer and generate report
    try:
        store = JSONLEpisodeStore(args.episodes)
        analyzer = PatternAnalyzer(store)

        # Check episode count
        episodes = store.get_all()
        if not episodes:
            print("Hata: Episode verisi bulunamadi.")
            sys.exit(1)

        if not args.quiet:
            print(f"Analiz ediliyor: {len(episodes)} episode...")
            print()

        report = analyzer.generate_report()

        # Print to console
        if not args.quiet:
            print(report)

        # Write to file
        if not args.no_file:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

            if not args.quiet:
                print()
                print(f"Rapor yazildi: {output_path}")

    except Exception as e:
        print(f"Analiz hatasi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
