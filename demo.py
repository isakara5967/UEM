#!/usr/bin/env python3
"""
UEM v2 - Cognitive Cycle Demo

3 senaryo ile StateVector akışını ve karar sürecini görselleştirir.

Senaryolar:
    1. Sad Friend    → help
    2. Happy Friend  → celebrate  
    3. Hostile Enemy → flee/defend

Kullanım:
    python demo.py
    python demo.py --scenario sad
    python demo.py --scenario happy
    python demo.py --scenario threat
    python demo.py --all
"""

import sys
sys.path.insert(0, '.')

import argparse
import time
from dataclasses import dataclass
from typing import Optional

from foundation.state import StateVector, SVField
from foundation.types import Entity, Stimulus
from engine import CognitiveCycle
from engine.phases import Phase
from engine.handlers import register_all_handlers


# ═══════════════════════════════════════════════════════════════════════════
# ANSI COLORS
# ═══════════════════════════════════════════════════════════════════════════

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def colored(text: str, color: str) -> str:
    """Renkli text döndür."""
    return f"{color}{text}{Colors.ENDC}"


def bold(text: str) -> str:
    return colored(text, Colors.BOLD)


def dim(text: str) -> str:
    return colored(text, Colors.DIM)


# ═══════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def print_banner():
    """ASCII banner yazdır."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     ██╗   ██╗███████╗███╗   ███╗    ██╗   ██╗██████╗                      ║
║     ██║   ██║██╔════╝████╗ ████║    ██║   ██║╚════██╗                     ║
║     ██║   ██║█████╗  ██╔████╔██║    ██║   ██║ █████╔╝                     ║
║     ██║   ██║██╔══╝  ██║╚██╔╝██║    ╚██╗ ██╔╝██╔═══╝                      ║
║     ╚██████╔╝███████╗██║ ╚═╝ ██║     ╚████╔╝ ███████╗                     ║
║      ╚═════╝ ╚══════╝╚═╝     ╚═╝      ╚═══╝  ╚══════╝                     ║
║                                                                           ║
║              Unknown Evola Mind - Cognitive Cycle Demo                    ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(colored(banner, Colors.CYAN))


def print_section(title: str):
    """Bölüm başlığı yazdır."""
    print()
    print(colored("─" * 70, Colors.DIM))
    print(colored(f"  {title}", Colors.BOLD + Colors.YELLOW))
    print(colored("─" * 70, Colors.DIM))


def print_scenario_header(name: str, emoji: str, description: str):
    """Senaryo başlığı yazdır."""
    print()
    print(colored("╔" + "═" * 68 + "╗", Colors.CYAN))
    print(colored(f"║  {emoji}  {name:60} ║", Colors.CYAN))
    print(colored("╠" + "═" * 68 + "╣", Colors.CYAN))
    print(colored(f"║  {description:64} ║", Colors.CYAN))
    print(colored("╚" + "═" * 68 + "╝", Colors.CYAN))


def format_value(value: float, width: int = 6) -> str:
    """Değeri formatla ve renklendir."""
    formatted = f"{value:.2f}"
    if value > 0.7:
        return colored(formatted.rjust(width), Colors.GREEN)
    elif value > 0.4:
        return colored(formatted.rjust(width), Colors.YELLOW)
    else:
        return colored(formatted.rjust(width), Colors.RED)


def format_action(action: str) -> str:
    """Action'ı renklendir."""
    action_colors = {
        "help": Colors.GREEN,
        "comfort": Colors.GREEN,
        "celebrate": Colors.GREEN + Colors.BOLD,
        "congratulate": Colors.GREEN,
        "approach": Colors.CYAN,
        "greet": Colors.CYAN,
        "observe": Colors.YELLOW,
        "flee": Colors.RED + Colors.BOLD,
        "avoid": Colors.RED,
        "defend": Colors.RED + Colors.BOLD,
        "wait": Colors.DIM,
    }
    color = action_colors.get(action, Colors.ENDC)
    return colored(action.upper(), color)


def print_state_vector(state: StateVector, label: str = "StateVector"):
    """StateVector'ı görsel formatla yazdır."""
    print(f"\n  {colored(label, Colors.BOLD)}:")
    
    # Core
    print(f"    ┌─ Core ──────────────────────────────────────┐")
    print(f"    │  Resource:  {format_value(state.resource)}  │  Threat:   {format_value(state.threat)}  │  Wellbeing: {format_value(state.wellbeing)}  │")
    print(f"    └────────────────────────────────────────────┘")
    
    # PAD
    valence = state.get(SVField.VALENCE)
    arousal = state.get(SVField.AROUSAL)
    dominance = state.get(SVField.DOMINANCE)
    print(f"    ┌─ PAD (Emotion) ─────────────────────────────┐")
    print(f"    │  Valence:   {format_value(valence)}  │  Arousal:  {format_value(arousal)}  │  Dominance: {format_value(dominance)}  │")
    print(f"    └────────────────────────────────────────────┘")
    
    # Social
    empathy = state.get(SVField.EMPATHY_TOTAL)
    sympathy = state.get(SVField.SYMPATHY_LEVEL)
    trust = state.get(SVField.TRUST_VALUE)
    print(f"    ┌─ Social ────────────────────────────────────┐")
    print(f"    │  Empathy:   {format_value(empathy)}  │  Sympathy: {format_value(sympathy)}  │  Trust:     {format_value(trust)}  │")
    print(f"    └────────────────────────────────────────────┘")


def print_state_comparison(before: StateVector, after: StateVector):
    """Önceki ve sonraki state'i karşılaştır."""
    print(f"\n  {colored('State Comparison:', Colors.BOLD)}")
    
    def delta_str(before_val: float, after_val: float) -> str:
        delta = after_val - before_val
        if abs(delta) < 0.01:
            return dim("  ─  ")
        elif delta > 0:
            return colored(f"+{delta:.2f}", Colors.GREEN)
        else:
            return colored(f"{delta:.2f}", Colors.RED)
    
    fields = [
        ("Resource", SVField.RESOURCE, lambda s: s.resource),
        ("Threat", SVField.THREAT, lambda s: s.threat),
        ("Wellbeing", SVField.WELLBEING, lambda s: s.wellbeing),
        ("Valence", SVField.VALENCE, lambda s: s.get(SVField.VALENCE)),
        ("Arousal", SVField.AROUSAL, lambda s: s.get(SVField.AROUSAL)),
        ("Empathy", SVField.EMPATHY_TOTAL, lambda s: s.get(SVField.EMPATHY_TOTAL)),
        ("Sympathy", SVField.SYMPATHY_LEVEL, lambda s: s.get(SVField.SYMPATHY_LEVEL)),
        ("Trust", SVField.TRUST_VALUE, lambda s: s.get(SVField.TRUST_VALUE)),
    ]
    
    print(f"    {'Field':<12} {'Before':>8} {'After':>8} {'Delta':>8}")
    print(f"    {'-'*12} {'-'*8} {'-'*8} {'-'*8}")
    
    for name, field, getter in fields:
        before_val = getter(before)
        after_val = getter(after)
        delta = delta_str(before_val, after_val)
        print(f"    {name:<12} {before_val:>8.2f} {after_val:>8.2f} {delta:>8}")


def print_phase_flow(result):
    """Phase akışını görselleştir."""
    print(f"\n  {colored('Cognitive Cycle Flow:', Colors.BOLD)}")
    
    phase_icons = {
        Phase.SENSE: "👁️",
        Phase.ATTEND: "🎯",
        Phase.PERCEIVE: "🔍",
        Phase.RETRIEVE: "💾",
        Phase.REASON: "🧠",
        Phase.EVALUATE: "⚖️",
        Phase.FEEL: "💚",
        Phase.DECIDE: "🎲",
        Phase.PLAN: "📋",
        Phase.ACT: "⚡",
    }
    
    print()
    for phase in Phase.ordered():
        phase_result = result.phase_results.get(phase)
        icon = phase_icons.get(phase, "•")
        
        if phase_result:
            if phase_result.skipped:
                status = dim("SKIP")
            elif phase_result.success:
                status = colored("OK", Colors.GREEN)
            else:
                status = colored("FAIL", Colors.RED)
            
            duration = f"{phase_result.duration_ms:.1f}ms"
            
            # Önemli çıktıları göster
            output_str = ""
            if phase_result.output:
                if "action" in phase_result.output:
                    output_str = f"→ {format_action(phase_result.output['action'])}"
                elif "empathy" in phase_result.output:
                    emp = phase_result.output['empathy']
                    output_str = f"→ empathy={format_value(emp)}"
                elif "agents_detected" in phase_result.output:
                    count = len(phase_result.output["agents_detected"])
                    output_str = f"→ {count} agent(s)"
                elif "suggested_action" in phase_result.output:
                    suggested = phase_result.output.get("suggested_action")
                    if suggested:
                        output_str = f"→ suggests {format_action(suggested)}"
            
            print(f"    {icon} {phase.value:<12} [{status}] {duration:>8}  {output_str}")
        else:
            print(f"    {icon} {phase.value:<12} [---]")
    
    print()


def print_decision_analysis(result):
    """Karar analizini yazdır."""
    decide_result = result.phase_results.get(Phase.DECIDE)
    
    if not decide_result or not decide_result.output:
        return
    
    output = decide_result.output
    action = output.get("action", "unknown")
    confidence = output.get("confidence", 0)
    reasoning = output.get("reasoning", "")
    inputs = output.get("inputs", {})
    
    print(f"  {colored('Decision Analysis:', Colors.BOLD)}")
    print(f"    ┌────────────────────────────────────────────────────────────┐")
    print(f"    │  Action:     {format_action(action):<48} │")
    print(f"    │  Confidence: {format_value(confidence)}                                          │")
    print(f"    │  Reasoning:  {reasoning[:50]:<50} │")
    print(f"    └────────────────────────────────────────────────────────────┘")
    
    if inputs:
        print(f"\n    Decision Inputs:")
        print(f"      Threat={inputs.get('threat', 0):.2f}  Empathy={inputs.get('empathy', 0):.2f}  Trust={inputs.get('trust', 0):.2f}  Valence={inputs.get('valence', 0):.2f}")


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ScenarioResult:
    """Senaryo sonucu."""
    name: str
    initial_state: StateVector
    final_state: StateVector
    cycle_result: any
    expected_action: str
    actual_action: str
    passed: bool


def create_sad_friend_scenario():
    """Üzgün arkadaş senaryosu."""
    agent = Entity(
        id="alice",
        entity_type="agent",
        attributes={
            "expression": "sad",
            "body_language": "slumped",
            "relationship": "friend",
            "valence": -0.6,
            "arousal": 0.3,
            "dominance": 0.2,
        }
    )
    
    stimulus = Stimulus(
        stimulus_type="social",
        intensity=0.6,
        source_entity=agent,
        content={
            "situation": "loss",
            "verbal": "I lost my job today...",
        }
    )
    
    initial_state = StateVector(
        resource=0.7,
        threat=0.0,
        wellbeing=0.6,
    )
    initial_state.set(SVField.VALENCE, 0.5)
    initial_state.set(SVField.AROUSAL, 0.3)
    
    return stimulus, initial_state, "help"


def create_happy_friend_scenario():
    """Mutlu arkadaş senaryosu."""
    agent = Entity(
        id="bob",
        entity_type="agent",
        attributes={
            "expression": "happy",
            "body_language": "excited",
            "relationship": "friend",
            "valence": 0.8,
            "arousal": 0.8,
            "dominance": 0.7,
        }
    )
    
    stimulus = Stimulus(
        stimulus_type="social",
        intensity=0.8,
        source_entity=agent,
        content={
            "situation": "celebration",
            "verbal": "I got promoted! Let's celebrate!",
        }
    )
    
    initial_state = StateVector(
        resource=0.7,
        threat=0.0,
        wellbeing=0.6,
    )
    initial_state.set(SVField.VALENCE, 0.6)
    initial_state.set(SVField.AROUSAL, 0.5)
    
    return stimulus, initial_state, "celebrate"


def create_hostile_enemy_scenario():
    """Düşman tehdit senaryosu."""
    agent = Entity(
        id="enemy_1",
        entity_type="agent",
        attributes={
            "expression": "angry",
            "body_language": "aggressive",
            "relationship": "enemy",
            "hostile": True,
            "valence": -0.9,
            "arousal": 0.9,
            "dominance": 0.8,
        }
    )
    
    stimulus = Stimulus(
        stimulus_type="social",
        intensity=0.9,
        source_entity=agent,
        content={
            "situation": "conflict",
            "verbal": "You will pay for this!",
        }
    )
    
    initial_state = StateVector(
        resource=0.5,
        threat=0.0,
        wellbeing=0.5,
    )
    initial_state.set(SVField.VALENCE, 0.5)
    initial_state.set(SVField.AROUSAL, 0.3)
    
    return stimulus, initial_state, "flee"  # veya defend


def run_scenario(
    name: str,
    emoji: str,
    description: str,
    stimulus: Stimulus,
    initial_state: StateVector,
    expected_action: str,
) -> ScenarioResult:
    """Senaryoyu çalıştır ve sonuçları göster."""
    
    print_scenario_header(name, emoji, description)
    
    # Initial state'i kopyala (karşılaştırma için)
    state_before = initial_state.copy()
    
    print_state_vector(initial_state, "Initial State")
    
    # Agent bilgisi göster
    if stimulus.source_entity:
        agent = stimulus.source_entity
        print(f"\n  {colored('Agent Detected:', Colors.BOLD)}")
        print(f"    ID: {agent.id}")
        print(f"    Expression: {agent.get('expression', 'unknown')}")
        print(f"    Relationship: {agent.get('relationship', 'unknown')}")
        print(f"    Hostile: {agent.get('hostile', False)}")
    
    # Cycle oluştur ve çalıştır
    print(f"\n  {colored('Running Cognitive Cycle...', Colors.CYAN)}")
    
    cycle = CognitiveCycle()
    register_all_handlers(cycle)
    
    start_time = time.perf_counter()
    result = cycle.run(stimulus=stimulus, initial_state=initial_state)
    total_time = (time.perf_counter() - start_time) * 1000
    
    # Phase akışı
    print_phase_flow(result)
    
    # Final state
    print_state_vector(result.state_vector, "Final State")
    
    # Karşılaştırma
    print_state_comparison(state_before, result.state_vector)
    
    # Karar analizi
    print()
    print_decision_analysis(result)
    
    # Sonuç
    decide_result = result.phase_results.get(Phase.DECIDE)
    actual_action = decide_result.output.get("action") if decide_result and decide_result.output else "unknown"
    
    # Expected action kontrolü (flee veya defend kabul edilebilir)
    passed = actual_action == expected_action
    if expected_action == "flee" and actual_action in ["flee", "defend"]:
        passed = True
    if expected_action == "celebrate" and actual_action in ["celebrate", "congratulate"]:
        passed = True
    
    print(f"\n  {colored('Result:', Colors.BOLD)}")
    print(f"    Expected: {format_action(expected_action)}")
    print(f"    Actual:   {format_action(actual_action)}")
    print(f"    Status:   {colored('✓ PASS', Colors.GREEN) if passed else colored('✗ FAIL', Colors.RED)}")
    print(f"    Time:     {total_time:.2f}ms")
    
    return ScenarioResult(
        name=name,
        initial_state=state_before,
        final_state=result.state_vector,
        cycle_result=result,
        expected_action=expected_action,
        actual_action=actual_action,
        passed=passed,
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def run_all_scenarios():
    """Tüm senaryoları çalıştır."""
    print_banner()
    
    scenarios = [
        ("Sad Friend", "😢", "A close friend has just lost their job and needs support",
         *create_sad_friend_scenario()),
        ("Happy Friend", "🎉", "A friend got promoted and wants to celebrate with you",
         *create_happy_friend_scenario()),
        ("Hostile Enemy", "😠", "An aggressive enemy is threatening you",
         *create_hostile_enemy_scenario()),
    ]
    
    results = []
    
    for name, emoji, desc, stimulus, state, expected in scenarios:
        result = run_scenario(name, emoji, desc, stimulus, state, expected)
        results.append(result)
        print()
    
    # Summary
    print_section("SUMMARY")
    
    print(f"\n  {'Scenario':<20} {'Expected':<12} {'Actual':<12} {'Status':<10}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*10}")
    
    for r in results:
        status = colored("PASS", Colors.GREEN) if r.passed else colored("FAIL", Colors.RED)
        print(f"  {r.name:<20} {r.expected_action:<12} {r.actual_action:<12} {status}")
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print()
    if passed == total:
        print(colored(f"  🎉 All {total} scenarios passed!", Colors.GREEN + Colors.BOLD))
    else:
        print(colored(f"  ⚠️  {passed}/{total} scenarios passed", Colors.YELLOW))
    
    print()


def run_single_scenario(scenario_name: str):
    """Tek bir senaryoyu çalıştır."""
    print_banner()
    
    scenarios = {
        "sad": ("Sad Friend", "😢", "A close friend has just lost their job and needs support",
                *create_sad_friend_scenario()),
        "happy": ("Happy Friend", "🎉", "A friend got promoted and wants to celebrate with you",
                  *create_happy_friend_scenario()),
        "threat": ("Hostile Enemy", "😠", "An aggressive enemy is threatening you",
                   *create_hostile_enemy_scenario()),
    }
    
    if scenario_name not in scenarios:
        print(f"Unknown scenario: {scenario_name}")
        print(f"Available: {', '.join(scenarios.keys())}")
        return
    
    name, emoji, desc, stimulus, state, expected = scenarios[scenario_name]
    run_scenario(name, emoji, desc, stimulus, state, expected)
    print()


def main():
    parser = argparse.ArgumentParser(description="UEM v2 - Cognitive Cycle Demo")
    parser.add_argument("--scenario", "-s", type=str, 
                        choices=["sad", "happy", "threat"],
                        help="Run a specific scenario")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Run all scenarios")
    
    args = parser.parse_args()
    
    if args.scenario:
        run_single_scenario(args.scenario)
    else:
        run_all_scenarios()


if __name__ == "__main__":
    main()
