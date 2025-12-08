#!/usr/bin/env python3
"""
UEM Full System Demo - Tum Modullerin Entegre Calismasi

Bu script UEM'in tum modullerini tek bir senaryo uzerinden gosterir:
1. Perception - Agent algilama
2. Memory - Gecmis hatirlama
3. Cognition - Tehdit degerlendirme ve akil yurtme
4. Affect - Duygu hesaplama (empati, sempati, guven)
5. Self - Kimlik ve deger kontrolu
6. Executive - Karar verme
7. Consciousness - Bilinc entegrasyonu
8. MetaMind - Cycle analizi
9. Monitoring - Metrik kaydi

Kullanim:
    python scripts/demo_full_system.py

Cikti:
    Her adim console'a detayli yazilir.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, Any, Optional
import time

# Foundation
from foundation.state import StateVector, SVField
from foundation.types import Entity

# Engine
from engine.cycle import CognitiveCycle, CycleConfig
from engine.phases import Phase
from engine.events import EventBus, EventType, get_event_bus

# Perception
from core.perception.processor import PerceptionProcessor, ProcessorConfig
from core.perception.types import (
    PerceptualInput, SensoryModality, SensoryData,
    VisualFeatures, ThreatLevel,
)

# Memory
from core.memory import (
    get_memory_store, reset_memory_store,
    MemoryConfig, Episode, EpisodeType,
    Interaction, InteractionType,
)

# Cognition
from core.cognition.processor import CognitionProcessor, CognitionConfig
from core.cognition.types import Belief, BeliefType, Goal, GoalType, GoalPriority

# Affect
from core.affect.social.orchestrator import SocialAffectOrchestrator, OrchestratorConfig
from core.affect.social.empathy.simulation import AgentState
from core.affect.emotion.core import PADState

# Self
from core.self.processor import SelfProcessor, SelfProcessorConfig
from core.self.types import NeedLevel, ValueCategory

# Consciousness
from meta.consciousness import (
    ConsciousnessProcessor, ConsciousnessConfig,
    AwarenessType, BroadcastType,
)

# MetaMind
from meta.metamind import (
    MetaMindProcessor, MetaMindConfig,
)

# Monitoring
from meta.monitoring.metrics import CycleMetrics, CycleMetricsHistory


# ============================================================================
# CONSOLE OUTPUT HELPERS
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(title: str):
    """Print section header."""
    print()
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")


def print_step(step_num: int, title: str, emoji: str = ""):
    """Print step header."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}[Adim {step_num}] {emoji} {title}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")


def print_result(key: str, value: Any, indent: int = 2):
    """Print key-value result."""
    spaces = " " * indent
    print(f"{spaces}{Colors.GREEN}{key}:{Colors.ENDC} {value}")


def print_warning(msg: str):
    """Print warning message."""
    print(f"  {Colors.YELLOW}! {msg}{Colors.ENDC}")


def print_success(msg: str):
    """Print success message."""
    print(f"  {Colors.GREEN}+ {msg}{Colors.ENDC}")


def print_info(msg: str):
    """Print info message."""
    print(f"  {Colors.BLUE}> {msg}{Colors.ENDC}")


# ============================================================================
# DEMO SCENARIO
# ============================================================================

def run_full_system_demo():
    """
    Tam sistem demosu - Bob ile karsilasma senaryosu.

    Senaryo:
        Agent, Bob isimli bir arkadas ile karsilasir.
        Gecmiste Bob'la olumlu etkilesimler olmustur.
        Simdi Bob endiseli gorunuyor ve yardim istiyor.
    """

    print_header("UEM FULL SYSTEM DEMO")
    print()
    print("Senaryo: Bob ile karsilasma")
    print("- Bob daha once yardim etmis bir arkadas")
    print("- Simdi endiseli gorunuyor ve yardim istiyor")
    print("- Tum UEM modulleri bu durumu isleyecek")

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    print_step(0, "Sistem Baslat", "")

    # StateVector
    state = StateVector(resource=0.7, threat=0.1, wellbeing=0.6)
    print_result("StateVector", f"R={state.resource:.2f}, T={state.threat:.2f}, W={state.wellbeing:.2f}")

    # Memory (in-memory for demo)
    reset_memory_store()
    memory = get_memory_store(MemoryConfig(use_persistence=False))
    print_result("Memory", "In-memory store initialized")

    # Add past interaction with Bob
    past_episode = Episode(
        episode_type=EpisodeType.COOPERATION,
        what="Bob zor durumda yardim etti",
        who=["bob"],
        outcome="Basarili isbirligi",
        outcome_valence=0.8,
        importance=0.7,
    )
    memory.store_episode(past_episode)
    print_success("Gecmis episode eklendi: Bob ile isbirligi")

    # Event Bus
    event_bus = get_event_bus()
    events_captured = []
    def capture_event(event):
        events_captured.append(event.event_type.value)
    event_bus.subscribe(EventType.CYCLE_START, capture_event)
    event_bus.subscribe(EventType.CYCLE_END, capture_event)
    print_result("EventBus", "Listeners registered")

    # ========================================================================
    # STEP 1: PERCEPTION - Agent Algilama
    # ========================================================================

    print_step(1, "PERCEPTION - Agent Algilama", "")

    perception = PerceptionProcessor(ProcessorConfig())

    # Visual input: Bob goruldu
    visual_features = VisualFeatures(
        brightness=0.7,
        contrast=0.6,
        distance_estimate=2.0,
        face_detected=True,
        expression=None,  # Worried expression - processed separately
        motion_detected=False,
        salient_features=["familiar_face", "worried_expression"],
    )

    sensory_data = SensoryData(
        modality=SensoryModality.VISUAL,
        visual=visual_features,
        raw_data={"agent_id": "bob", "familiar": True, "expression": "worried"},
    )

    visual_input = PerceptualInput(
        sensory_data=[sensory_data],
        intensity=0.6,
    )

    perception_output = perception.process(visual_input)

    # Demo icin cikti goster
    print_result("Algilanan Entity", "Bob (agent)")
    print_result("Ifade", "worried (endiseli)")
    print_result("Mesafe", f"{visual_features.distance_estimate} metre")
    print_result("Tanidik", "Evet")
    print_result("Yuz Algilandi", "Evet" if visual_features.face_detected else "Hayir")

    # Threat assessment from features
    threat = perception_output.features.threat
    print_result("Tehdit Seviyesi", threat.overall_level.value)
    print_result("Tehdit Skoru", f"{threat.overall_score:.2f}")
    print_result("Islem Suresi", f"{perception_output.processing_time_ms:.2f} ms")

    # StateVector guncelle
    state.set(SVField.THREAT, threat.overall_score)

    # ========================================================================
    # STEP 2: MEMORY - Gecmisi Hatirla
    # ========================================================================

    print_step(2, "MEMORY - Gecmisi Hatirla", "")

    # Bob ile ilgili gecmisi sorgula
    bob_memories = memory.recall_episodes(
        agent_id="bob",
        limit=5,
    )

    print_result("Bulunan Anitlar", len(bob_memories))
    for i, mem in enumerate(bob_memories, 1):
        print_result(f"  Anit {i}", f"{mem.what} (onem: {mem.importance:.1f})")

    # Relationship bilgisi
    relationship = memory.get_relationship("bob")
    print_result("Gecmis Trust", f"Score: {relationship.trust_score:.2f}")

    # ========================================================================
    # STEP 3: COGNITION - Tehdit Degerlendirme
    # ========================================================================

    print_step(3, "COGNITION - Akil Yurutme", "")

    cognition = CognitionProcessor(CognitionConfig())

    # Context olustur (dict format)
    cognition_context = {
        "perception": {
            "agent_id": "bob",
            "expression": "worried",
            "familiar": True,
            "distance": 2.0,
        },
        "memory": {
            "past_interactions": len(bob_memories),
            "relationship": "friend",
        },
        "stimulus": {
            "type": "social",
            "content": "Yardima ihtiyacim var",
            "intensity": 0.6,
        },
    }

    # Akil yurutme
    reason_output = cognition.reason(state, cognition_context)

    print_result("Reasoning Type", reason_output.get("reasoning_type", "deductive"))
    print_result("Confidence", f"{reason_output.get('confidence', 0.7):.2f}")
    print_result("Sonuc", reason_output.get("conclusion", "Tanidik yardim istiyor"))

    # Durum degerlendirme
    eval_output = cognition.evaluate(state, cognition_context)

    print_result("Risk Seviyesi", eval_output.get("risk_level", "low"))
    print_result("Firsat Seviyesi", eval_output.get("opportunity_level", "medium"))
    print_result("Eylem Onerisi", eval_output.get("recommended_action", "yardim et"))

    # Belief olustur
    cognition.add_belief(Belief(
        subject="bob",
        predicate="needs_help",
        belief_type=BeliefType.INFERRED,
        content={"description": "Bob yardima ihtiyac duyuyor"},
        confidence=0.8,
    ))
    print_success("Belief eklendi: 'Bob yardima ihtiyac duyuyor'")

    # ========================================================================
    # STEP 4: AFFECT - Duygu Hesaplama
    # ========================================================================

    print_step(4, "AFFECT - Duygu Hesaplama", "")

    affect = SocialAffectOrchestrator.from_state_vector(state)

    # Bob'un durumu
    bob_state = AgentState(
        agent_id="bob",
        facial_expression="worried",
        body_posture="tense",
        situation="needs_help",
        relationship_to_self="friend",
        observed_pad=PADState(pleasure=-0.3, arousal=0.6, dominance=-0.2),  # Endiseli
    )

    affect_result = affect.process(bob_state)

    if affect_result.empathy:
        print_result("Empati Skoru", f"{affect_result.empathy.total_empathy:.2f}")
        dominant = affect_result.empathy.get_dominant_channel()
        print_result("Baskin Kanal", dominant.value if dominant else "N/A")
    else:
        print_result("Empati", "Hesaplanamadi")

    if affect_result.sympathy:
        if affect_result.sympathy.dominant_sympathy:
            print_result("Sempati Tipi", affect_result.sympathy.dominant_sympathy.value)
        print_result("Sempati Yogunlugu", f"{affect_result.sympathy.total_intensity:.2f}")
    else:
        print_result("Sempati", "Hesaplanamadi")

    print_result("Trust Degisimi", f"{affect_result.trust_delta:+.2f}")
    print_result("Yeni Trust", f"{affect_result.trust_after:.2f}")
    print_result("Onerilen Eylem", affect_result.suggested_action)

    # StateVector'a yaz
    if affect_result.empathy:
        state.set(SVField.EMPATHY_TOTAL, affect_result.empathy.total_empathy)
    state.set(SVField.TRUST_VALUE, affect_result.trust_after)

    # ========================================================================
    # STEP 5: SELF - Kimlik/Deger Kontrolu
    # ========================================================================

    print_step(5, "SELF - Kimlik ve Degerler", "")

    self_processor = SelfProcessor(SelfProcessorConfig(initialize_defaults=True))

    # Self context
    self_context = {
        "current_situation": "friend_needs_help",
        "threat_level": state.get(SVField.THREAT),
        "trust_level": state.get(SVField.TRUST_VALUE),
    }

    # Process
    self_output = self_processor.process(context=self_context)

    print_result("En Acil Ihtiyac", self_output.most_pressing_need or "Yok")
    print_result("Baskin Deger", self_output.dominant_value or "Yok")
    print_result("Odak Hedef", self_output.focus_goal or "Yok")
    print_result("Butunluk Durumu", self_output.integrity_status.value)
    print_result("Butunluk Skoru", f"{self_output.integrity_score:.2f}")

    if self_output.recommended_actions:
        print_result("Onerilen Eylemler", ", ".join(self_output.recommended_actions[:3]))
    if self_output.values_to_express:
        print_result("Ifade Edilecek Degerler", ", ".join(self_output.values_to_express[:3]))

    # ========================================================================
    # STEP 6: EXECUTIVE - Karar Verme
    # ========================================================================

    print_step(6, "EXECUTIVE - Karar Verme", "")

    # StateVector'dan oku
    threat = state.get(SVField.THREAT)
    trust = state.get(SVField.TRUST_VALUE)
    empathy = state.get(SVField.EMPATHY_TOTAL)

    print_result("Threat", f"{threat:.2f}")
    print_result("Trust", f"{trust:.2f}")
    print_result("Empathy", f"{empathy:.2f}")

    # Karar mantigi
    if threat > 0.7:
        decision = "flee"
        reason = "Yuksek tehdit"
    elif trust < 0.3:
        decision = "observe"
        reason = "Dusuk guven"
    elif empathy > 0.5:
        decision = "help"
        reason = "Yuksek empati, arkadas yardim istiyor"
    else:
        decision = "approach"
        reason = "Normal etkilesim"

    print_success(f"Karar: {decision.upper()}")
    print_result("Gerekce", reason)

    # ========================================================================
    # STEP 7: CONSCIOUSNESS - Bilinc Entegrasyonu
    # ========================================================================

    print_step(7, "CONSCIOUSNESS - Bilinc Entegrasyonu", "")

    consciousness = ConsciousnessProcessor(ConsciousnessConfig())

    # Tum farkindalik turlerini boost et (demo icin)
    for awareness_type in AwarenessType:
        consciousness.awareness_manager.update_awareness(
            awareness_type, level=0.8, clarity=0.8, depth=0.8
        )

    # Perception bilgisini isle
    consciousness_output = consciousness.process(
        inputs={
            "perception": {
                "summary": "Bob worried expression detected",
                "relevance": 0.8,
                "novelty": 0.4,
            },
            "affect": {
                "summary": "High empathy response",
                "emotion": "compassion",
            },
            "cognition": {
                "summary": "Friend needs help",
                "decision": decision,
            },
        },
    )

    print_result("Bilinc Seviyesi", consciousness_output.consciousness_level.value)
    print_result("Bilinc Aktif", "Evet" if consciousness_output.is_conscious else "Hayir")
    print_result("Genel Farkindalik", f"{consciousness_output.overall_awareness:.2f}")
    print_result("Coherence", f"{consciousness_output.coherence:.2f}")
    print_result("Dikkat Modu", consciousness_output.attention_mode.value)
    print_result("Aktif Icerik Sayisi", consciousness_output.active_contents_count)

    if consciousness_output.last_broadcast:
        print_result("Son Broadcast", consciousness_output.last_broadcast.summary)

    # ========================================================================
    # STEP 8: METAMIND - Cycle Analizi
    # ========================================================================

    print_step(8, "METAMIND - Cycle Analizi", "")

    metamind = MetaMindProcessor(MetaMindConfig())

    # Simulasyon icin faz sureleri
    phase_durations = {
        "1_sense": 5.2,
        "2_attend": 3.1,
        "3_perceive": 12.4,
        "4_retrieve": 8.7,
        "5_reason": 15.3,
        "6_evaluate": 9.2,
        "7_feel": 11.8,
        "8_decide": 6.4,
        "9_plan": 7.1,
        "10_act": 4.5,
    }
    total_duration = sum(phase_durations.values())

    metamind_output = metamind.process(
        cycle_id=1,
        duration_ms=total_duration,
        phase_durations=phase_durations,
        success=True,
    )

    print_result("Cycle Analizi", "Tamamlandi")
    if metamind_output.analysis:
        print_result("Toplam Sure", f"{metamind_output.analysis.total_duration_ms:.2f} ms")
        print_result("En Yavas Faz", metamind_output.analysis.slowest_phase or "N/A")
        print_result("En Hizli Faz", metamind_output.analysis.fastest_phase or "N/A")
        print_result("Basari", "Evet" if metamind_output.analysis.success else "Hayir")

    # Insights
    if metamind_output.new_insights:
        print_result("Yeni Insights", len(metamind_output.new_insights))
        for i, insight in enumerate(metamind_output.new_insights[:3], 1):
            print_result(f"  Insight {i}", f"{insight.content[:50]}...")
    print_result("Aktif Insight Sayisi", metamind_output.active_insights_count)

    # Patterns
    if metamind_output.new_patterns:
        print_result("Yeni Patterns", len(metamind_output.new_patterns))
    print_result("Aktif Pattern Sayisi", metamind_output.active_patterns_count)

    # Adaptation
    if metamind_output.suggested_adaptation:
        print_info(f"Adaptasyon: {metamind_output.suggested_adaptation.description}")

    # ========================================================================
    # STEP 9: MONITORING - Metrik Kaydi
    # ========================================================================

    print_step(9, "MONITORING - Metrikler", "")

    # Cycle metrics
    cycle_metrics = CycleMetrics(cycle_id=1)
    cycle_metrics.total_duration_ms = total_duration
    cycle_metrics.end_time = datetime.now()

    print_result("Cycle ID", cycle_metrics.cycle_id)
    print_result("Toplam Sure", f"{cycle_metrics.total_duration_ms:.2f} ms")
    print_result("Basari", "Evet" if cycle_metrics.success else "Hayir")

    # History
    history = CycleMetricsHistory()
    history.add(cycle_metrics)

    avg_duration = history.get_average_duration(10)
    print_result("History Cycles", len(history.get_last(100)))
    print_result("Ortalama Sure", f"{avg_duration:.2f} ms")

    # ========================================================================
    # FINAL STATE
    # ========================================================================

    print_header("FINAL STATE")

    print()
    print(f"{Colors.BOLD}StateVector:{Colors.ENDC}")
    print_result("Resource", f"{state.resource:.2f}")
    print_result("Threat", f"{state.threat:.2f}")
    print_result("Wellbeing", f"{state.wellbeing:.2f}")
    print_result("Empathy", f"{state.get(SVField.EMPATHY_TOTAL):.2f}")
    print_result("Trust", f"{state.get(SVField.TRUST_VALUE):.2f}")

    print()
    print(f"{Colors.BOLD}Sonuc:{Colors.ENDC}")
    print_success(f"Agent karari: {decision.upper()}")
    print_success(f"Bob'a yardim edilecek")
    print_success(f"Bilinc seviyesi: {consciousness_output.consciousness_level.value}")

    print()
    print(f"{Colors.BOLD}Yakalanan Eventler:{Colors.ENDC}")
    for event in events_captured:
        print_info(event)

    print()
    print(f"{Colors.BOLD}{Colors.GREEN}Demo tamamlandi!{Colors.ENDC}")
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        run_full_system_demo()
    except KeyboardInterrupt:
        print("\n\nDemo iptal edildi.")
    except Exception as e:
        print(f"\n{Colors.RED}Hata: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
