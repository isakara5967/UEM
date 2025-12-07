#!/usr/bin/env python3
"""
UEM v2 - Unknown Evola Mind

Ana giriş noktası.

Usage:
    python main.py                    # Tek cycle çalıştır
    python main.py --cycles 10        # 10 cycle çalıştır
    python main.py --demo             # Demo modu
"""

import argparse
import logging
import sys
from datetime import datetime

# Foundation
from foundation.state import StateVector, SVField
from foundation.types import Stimulus

# Engine
from engine import CognitiveCycle, Phase, get_event_bus
from engine.phases import PhaseResult

# Monitoring
from meta.monitoring import SystemMonitor, get_metrics_collector


def setup_logging(level: str = "INFO") -> None:
    """Logging yapılandır."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def create_demo_handlers():
    """Demo için örnek phase handler'lar oluştur."""
    
    def sense_handler(phase: Phase, state: StateVector, context) -> PhaseResult:
        """Algı: Ortamdan bilgi al."""
        stimulus = context.metadata.get("stimulus")
        if stimulus:
            state.set(SVField.AROUSAL, stimulus.intensity)
        return PhaseResult(phase=phase, success=True, output={"sensed": True})
    
    def feel_handler(phase: Phase, state: StateVector, context) -> PhaseResult:
        """Duygu: Duygusal tepki hesapla."""
        arousal = state.get(SVField.AROUSAL, 0.5)
        threat = state.threat
        
        # Basit valence hesabı: threat yüksekse negatif
        valence = 0.5 - (threat * 0.8) + (arousal * 0.2)
        state.set(SVField.VALENCE, max(-1, min(1, valence)))
        
        return PhaseResult(phase=phase, success=True, output={"valence": valence})
    
    def decide_handler(phase: Phase, state: StateVector, context) -> PhaseResult:
        """Karar: Bir aksiyon seç."""
        threat = state.threat
        
        if threat > 0.7:
            action = "flee"
        elif threat > 0.3:
            action = "observe"
        else:
            action = "explore"
        
        return PhaseResult(phase=phase, success=True, output={"action": action})
    
    return {
        Phase.SENSE: sense_handler,
        Phase.FEEL: feel_handler,
        Phase.DECIDE: decide_handler,
    }


def run_demo(num_cycles: int = 3) -> None:
    """Demo modu: Basit bir senaryo çalıştır."""
    print("\n" + "=" * 60)
    print("UEM v2 - Demo Mode")
    print("=" * 60 + "\n")
    
    # Setup
    monitor = SystemMonitor()
    monitor.start()
    
    cycle = CognitiveCycle()
    
    # Demo handler'ları kaydet
    handlers = create_demo_handlers()
    for phase, handler in handlers.items():
        cycle.register_handler(phase, handler)
    
    # Farklı threat seviyeleriyle cycle'lar çalıştır
    scenarios = [
        {"name": "Peaceful", "threat": 0.1, "intensity": 0.3},
        {"name": "Alert", "threat": 0.5, "intensity": 0.6},
        {"name": "Danger", "threat": 0.9, "intensity": 0.9},
    ]
    
    for i, scenario in enumerate(scenarios[:num_cycles]):
        print(f"\n--- Scenario {i+1}: {scenario['name']} ---")
        
        # Initial state
        initial_state = StateVector(
            resource=0.7,
            threat=scenario["threat"],
            wellbeing=0.5,
        )
        
        # Stimulus
        stimulus = Stimulus(
            stimulus_type="environmental",
            intensity=scenario["intensity"],
            content={"scenario": scenario["name"]},
        )
        
        # Run
        result = cycle.run(stimulus=stimulus, initial_state=initial_state)
        
        # Output
        print(f"  Cycle ID: {result.cycle_id}")
        print(f"  Duration: {result.duration_ms:.2f}ms")
        print(f"  Threat: {initial_state.threat:.1f}")
        print(f"  Final Valence: {result.state_vector.get(SVField.VALENCE):.2f}")
        
        decide_result = result.phase_results.get(Phase.DECIDE)
        if decide_result and decide_result.output:
            print(f"  Action: {decide_result.output.get('action', 'none')}")
    
    # Report
    print("\n" + "-" * 60)
    print("Monitoring Report:")
    print("-" * 60)
    
    report = monitor.get_report()
    for name, summary in report["summaries"].items():
        if "duration" in name:
            print(f"  {name}: avg={summary['avg']:.2f}ms, count={summary['count']}")
    
    print(f"\n  Total cycles: {cycle.cycle_count}")
    print(f"  Event bus events: {get_event_bus().stats['total_events']}")
    
    monitor.stop()
    print("\n✅ Demo completed!")


def main():
    """Ana fonksiyon."""
    parser = argparse.ArgumentParser(description="UEM v2 - Unknown Evola Mind")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    if args.demo:
        run_demo(args.cycles or 3)
    else:
        # Basic run
        print("UEM v2 starting...")
        
        monitor = SystemMonitor()
        monitor.start()
        
        cycle = CognitiveCycle()
        
        for i in range(args.cycles):
            state = StateVector()
            result = cycle.run(initial_state=state)
            print(f"Cycle {result.cycle_id}: {result.duration_ms:.2f}ms")
        
        monitor.stop()
        print("Done.")


if __name__ == "__main__":
    main()
