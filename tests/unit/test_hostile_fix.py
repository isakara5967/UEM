#!/usr/bin/env python3
"""
UEM v2 - Hostile/Enemy Fix Test

Enemy için düşük trust ve sympathy test.
"""

import sys
sys.path.insert(0, '.')

from core.affect.emotion.core import PADState
from core.affect.social.empathy import AgentState
from core.affect.social.orchestrator import SocialAffectOrchestrator
from core.affect.social.sympathy import RelationshipContext


def test_friendly_scenario():
    """Arkadaş senaryosu - trust ve sympathy yüksek olmalı."""
    print("\n" + "=" * 60)
    print("TEST: Friendly Scenario (Sad Friend)")
    print("=" * 60)
    
    my_pad = PADState.neutral()
    orchestrator = SocialAffectOrchestrator(my_pad)
    
    friend = AgentState(
        agent_id="friend_alice",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    
    result = orchestrator.process(friend)
    
    print(f"  Agent: {result.agent_id}")
    print(f"  Empathy: {result.empathy.total_empathy:.2f}")
    print(f"  Sympathy: {result.sympathy.total_intensity:.2f}")
    print(f"  Sympathy Type: {result.sympathy.dominant_sympathy.value if result.sympathy.dominant_sympathy else 'none'}")
    print(f"  Trust: {result.trust_before:.2f} → {result.trust_after:.2f}")
    print(f"  Action: {result.suggested_action}")
    
    # Assertions
    assert result.empathy.total_empathy > 0.5, f"Empathy should be high, got {result.empathy.total_empathy}"
    assert result.sympathy.total_intensity > 0.5, f"Sympathy should be high, got {result.sympathy.total_intensity}"
    assert result.trust_after > 0.4, f"Trust should be moderate+, got {result.trust_after}"
    
    print("\n✅ Friendly Scenario PASSED")
    return result


def test_enemy_scenario():
    """Düşman senaryosu - trust ve sympathy düşük olmalı."""
    print("\n" + "=" * 60)
    print("TEST: Enemy Scenario (Hostile Enemy)")
    print("=" * 60)
    
    my_pad = PADState.neutral()
    orchestrator = SocialAffectOrchestrator(my_pad)
    
    enemy = AgentState(
        agent_id="enemy_1",
        facial_expression="angry",
        situation="conflict",
        relationship_to_self="enemy",
    )
    
    result = orchestrator.process(enemy)
    
    print(f"  Agent: {result.agent_id}")
    print(f"  Empathy: {result.empathy.total_empathy:.2f}")
    print(f"  Sympathy: {result.sympathy.total_intensity:.2f}")
    print(f"  Sympathy Type: {result.sympathy.dominant_sympathy.value if result.sympathy.dominant_sympathy else 'none'}")
    print(f"  Trust: {result.trust_before:.2f} → {result.trust_after:.2f}")
    print(f"  Action: {result.suggested_action}")
    
    # Assertions - Düşman için düşük değerler
    assert result.empathy.total_empathy > 0.3, f"Empathy should exist (we understand them), got {result.empathy.total_empathy}"
    assert result.sympathy.total_intensity < 0.3, f"Sympathy should be LOW for enemy, got {result.sympathy.total_intensity}"
    assert result.trust_before < 0.3, f"Trust should start LOW for enemy, got {result.trust_before}"
    
    print("\n✅ Enemy Scenario PASSED")
    return result


def test_hostile_flag_scenario():
    """Hostile flag ile senaryosu."""
    print("\n" + "=" * 60)
    print("TEST: Hostile Flag Scenario")
    print("=" * 60)
    
    my_pad = PADState.neutral()
    orchestrator = SocialAffectOrchestrator(my_pad)
    
    # Stranger ama hostile flag var
    hostile_stranger = AgentState(
        agent_id="hostile_stranger",
        facial_expression="angry",
        situation="threat",
        relationship_to_self="stranger",
    )
    # Manually set hostile attribute
    hostile_stranger.hostile = True
    
    result = orchestrator.process(hostile_stranger)
    
    print(f"  Agent: {result.agent_id}")
    print(f"  Empathy: {result.empathy.total_empathy:.2f}")
    print(f"  Sympathy: {result.sympathy.total_intensity:.2f}")
    print(f"  Trust: {result.trust_before:.2f} → {result.trust_after:.2f}")
    
    # Hostile flag → düşük trust ve sympathy
    assert result.sympathy.total_intensity < 0.3, f"Sympathy should be LOW for hostile, got {result.sympathy.total_intensity}"
    assert result.trust_before < 0.3, f"Trust should start LOW for hostile, got {result.trust_before}"
    
    print("\n✅ Hostile Flag Scenario PASSED")
    return result


def test_comparison():
    """Karşılaştırma tablosu."""
    print("\n" + "=" * 60)
    print("COMPARISON: Friend vs Enemy")
    print("=" * 60)
    
    my_pad = PADState.neutral()
    
    # Friend
    orch1 = SocialAffectOrchestrator(my_pad)
    friend = AgentState(
        agent_id="friend",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    friend_result = orch1.process(friend)
    
    # Enemy
    orch2 = SocialAffectOrchestrator(my_pad)
    enemy = AgentState(
        agent_id="enemy",
        facial_expression="angry",
        situation="conflict",
        relationship_to_self="enemy",
    )
    enemy_result = orch2.process(enemy)
    
    print("\n  ┌─────────────┬──────────┬──────────┐")
    print("  │ Metric      │  Friend  │  Enemy   │")
    print("  ├─────────────┼──────────┼──────────┤")
    print(f"  │ Empathy     │  {friend_result.empathy.total_empathy:6.2f}  │  {enemy_result.empathy.total_empathy:6.2f}  │")
    print(f"  │ Sympathy    │  {friend_result.sympathy.total_intensity:6.2f}  │  {enemy_result.sympathy.total_intensity:6.2f}  │")
    print(f"  │ Trust       │  {friend_result.trust_after:6.2f}  │  {enemy_result.trust_after:6.2f}  │")
    print("  └─────────────┴──────────┴──────────┘")
    
    # Enemy tüm metriklerde daha düşük olmalı (empathy hariç)
    assert enemy_result.sympathy.total_intensity < friend_result.sympathy.total_intensity, \
        "Enemy sympathy should be lower than friend"
    assert enemy_result.trust_after < friend_result.trust_after, \
        "Enemy trust should be lower than friend"
    
    print("\n✅ Comparison PASSED - Enemy values are correctly lower")


def main():
    print("=" * 60)
    print("UEM v2 - Hostile/Enemy Fix Test Suite")
    print("=" * 60)
    
    try:
        test_friendly_scenario()
        test_enemy_scenario()
        test_hostile_flag_scenario()
        test_comparison()
        
        print("\n" + "=" * 60)
        print("🎉 ALL HOSTILE FIX TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
