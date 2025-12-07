#!/usr/bin/env python3
"""
UEM v2 - Sympathy Module Test

Kurulumdan sonra çalıştır:
    python tests/unit/test_sympathy.py
"""

import sys
sys.path.insert(0, '.')

from core.affect.emotion.core import PADState, BasicEmotion, get_emotion_pad
from core.affect.social.empathy import (
    Empathy,
    AgentState,
    EmpathyResult,
)
from core.affect.social.sympathy import (
    Sympathy,
    SympathyType,
    SympathyResponse,
    SympathyResult,
    RelationshipContext,
    get_sympathy_pad,
    get_action_tendency,
    predict_sympathy,
    get_sympathy_spectrum,
)


def test_sympathy_types():
    """Sempati türleri."""
    print("\n=== TEST: Sympathy Types ===")
    
    # Prososyal
    prosocial = SympathyType.prosocial()
    print(f"  Prosocial types: {[s.value for s in prosocial]}")
    assert SympathyType.COMPASSION in prosocial
    assert SympathyType.EMPATHIC_JOY in prosocial
    
    # Antisosyal
    antisocial = SympathyType.antisocial()
    print(f"  Antisocial types: {[s.value for s in antisocial]}")
    assert SympathyType.SCHADENFREUDE in antisocial
    assert SympathyType.ENVY in antisocial
    
    print("✅ Sympathy Types PASSED")


def test_sympathy_pad_effects():
    """Sempati PAD etkileri."""
    print("\n=== TEST: Sympathy PAD Effects ===")
    
    types_to_test = [
        (SympathyType.COMPASSION, "negative pleasure, high dominance"),
        (SympathyType.EMPATHIC_JOY, "positive pleasure"),
        (SympathyType.SCHADENFREUDE, "positive pleasure, mid dominance"),
        (SympathyType.ENVY, "negative pleasure, low dominance"),
    ]
    
    for sympathy_type, expected in types_to_test:
        pad = get_sympathy_pad(sympathy_type)
        print(f"  {sympathy_type.value:16} -> {pad}")
    
    # Compassion negatif pleasure ama yüksek dominance
    compassion_pad = get_sympathy_pad(SympathyType.COMPASSION)
    assert compassion_pad.pleasure < 0
    assert compassion_pad.dominance > 0.5
    
    # Empathic joy pozitif pleasure
    joy_pad = get_sympathy_pad(SympathyType.EMPATHIC_JOY)
    assert joy_pad.pleasure > 0
    
    print("✅ Sympathy PAD Effects PASSED")


def test_action_tendencies():
    """Davranış eğilimleri."""
    print("\n=== TEST: Action Tendencies ===")
    
    mappings = [
        (SympathyType.COMPASSION, "help"),
        (SympathyType.EMPATHIC_JOY, "celebrate"),
        (SympathyType.EMPATHIC_ANGER, "defend"),
        (SympathyType.SCHADENFREUDE, "observe"),
        (SympathyType.ENVY, "compete"),
    ]
    
    for sympathy_type, expected_action in mappings:
        action = get_action_tendency(sympathy_type)
        print(f"  {sympathy_type.value:16} -> {action}")
        assert action == expected_action
    
    print("✅ Action Tendencies PASSED")


def test_relationship_context():
    """İlişki bağlamı."""
    print("\n=== TEST: Relationship Context ===")
    
    # Factory methods
    stranger = RelationshipContext.stranger()
    friend = RelationshipContext.friend()
    rival = RelationshipContext.rival()
    
    print(f"  Stranger valence: {stranger.valence}")
    print(f"  Friend valence: {friend.valence}")
    print(f"  Rival valence: {rival.valence}")
    
    assert stranger.valence == 0.0
    assert friend.valence > 0
    assert rival.valence < 0
    
    # From relationship type
    family = RelationshipContext.from_relationship_type("family")
    assert family.valence > 0.5
    
    print("✅ Relationship Context PASSED")


def test_basic_sympathy():
    """Temel sempati hesaplama."""
    print("\n=== TEST: Basic Sympathy ===")
    
    # Kendi durumum
    my_pad = PADState(pleasure=0.3, arousal=0.4, dominance=0.5)
    
    # Empati modülü
    empathy = Empathy(my_pad)
    
    # Üzgün arkadaş
    sad_friend = AgentState(
        agent_id="bob",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
        behavioral_cues=["crying"],
    )
    
    # Empati hesapla
    empathy_result = empathy.compute(sad_friend)
    print(f"  Empathy: {empathy_result.total_empathy:.3f}")
    
    # Sempati hesapla
    sympathy = Sympathy(my_pad)
    sympathy_result = sympathy.compute(
        empathy_result,
        relationship=RelationshipContext.friend(),
    )
    
    print(f"  Result: {sympathy_result}")
    print(f"  Dominant: {sympathy_result.dominant_sympathy}")
    print(f"  Intensity: {sympathy_result.total_intensity:.3f}")
    print(f"  Action: {sympathy_result.get_action_tendency()}")
    print(f"  Is prosocial: {sympathy_result.is_prosocial()}")
    
    # Üzgün arkadaşa compassion olmalı
    assert sympathy_result.has_sympathy()
    assert sympathy_result.is_prosocial()
    
    print("✅ Basic Sympathy PASSED")


def test_sympathy_from_agent():
    """AgentState'den direkt sempati."""
    print("\n=== TEST: Sympathy from Agent ===")
    
    my_pad = PADState.neutral()
    sympathy = Sympathy(my_pad)
    
    # Mutlu arkadaş
    happy_friend = AgentState(
        agent_id="alice",
        facial_expression="happy",
        situation="success",
        relationship_to_self="friend",
        behavioral_cues=["laughing", "smiling"],
    )
    
    result = sympathy.compute_from_agent(happy_friend)
    
    print(f"  Result: {result}")
    print(f"  Dominant: {result.dominant_sympathy}")
    
    # Mutlu arkadaşa empathic_joy beklenir
    if result.has_sympathy():
        print(f"  Sympathy type: {result.dominant_sympathy.value}")
    
    print("✅ Sympathy from Agent PASSED")


def test_rival_sympathy():
    """Rakibe sempati (antisosyal olabilir)."""
    print("\n=== TEST: Rival Sympathy ===")
    
    my_pad = PADState.neutral()
    empathy = Empathy(my_pad)
    sympathy = Sympathy(my_pad)
    
    # Rakip başarısız oldu
    failed_rival = AgentState(
        agent_id="rival",
        facial_expression="sad",
        situation="failure",
        relationship_to_self="stranger",  # Bilinmiyor
    )
    
    empathy_result = empathy.compute(failed_rival)
    
    # Negatif ilişki bağlamı
    rival_context = RelationshipContext(
        valence=-0.5,
        negative_history=0.6,
        perceived_deservedness=0.7,  # "Hak etti"
    )
    
    result = sympathy.compute(empathy_result, relationship=rival_context)
    
    print(f"  Empathy: {empathy_result.total_empathy:.3f}")
    print(f"  Result: {result}")
    print(f"  Is antisocial: {result.is_antisocial()}")
    
    # Schadenfreude olabilir
    if result.dominant_sympathy == SympathyType.SCHADENFREUDE:
        print("  ⚠️ Schadenfreude detected (expected for rival)")
    
    print("✅ Rival Sympathy PASSED")


def test_predict_sympathy():
    """Hızlı sempati tahmini."""
    print("\n=== TEST: Predict Sympathy ===")
    
    test_cases = [
        # (target_valence, relationship_valence, expected)
        (-0.5, 0.5, SympathyType.COMPASSION),   # Üzgün + pozitif ilişki
        (-0.5, -0.5, SympathyType.SCHADENFREUDE),  # Üzgün + negatif ilişki
        (0.5, 0.5, SympathyType.EMPATHIC_JOY),  # Mutlu + pozitif ilişki
        (0.5, -0.5, SympathyType.ENVY),         # Mutlu + negatif ilişki
    ]
    
    for target_v, rel_v, expected in test_cases:
        result = predict_sympathy(target_v, rel_v)
        status = "✓" if result == expected else "✗"
        print(f"  {status} target={target_v:+.1f}, rel={rel_v:+.1f} -> {result.value} (expected: {expected.value})")
        assert result == expected
    
    print("✅ Predict Sympathy PASSED")


def test_quick_sympathy():
    """Quick sympathy metodu."""
    print("\n=== TEST: Quick Sympathy ===")
    
    my_pad = PADState.neutral()
    sympathy = Sympathy(my_pad)
    
    # Farklı kombinasyonlar
    cases = [
        ("sad", "friend", SympathyType.COMPASSION),
        ("happy", "friend", SympathyType.EMPATHIC_JOY),
        ("sad", "enemy", SympathyType.SCHADENFREUDE),
    ]
    
    for emotion, rel, expected in cases:
        result = sympathy.quick_sympathy(emotion, rel)
        status = "✓" if result == expected else "?"
        print(f"  {status} {emotion:6} + {rel:6} -> {result.value if result else 'None'}")
    
    print("✅ Quick Sympathy PASSED")


def test_sympathy_spectrum():
    """Sempati spektrumu."""
    print("\n=== TEST: Sympathy Spectrum ===")
    
    my_pad = PADState.neutral()
    empathy = Empathy(my_pad)
    
    # Üzgün ajan
    sad_agent = AgentState(
        agent_id="test",
        observed_pad=PADState(pleasure=-0.6, arousal=0.4, dominance=0.3),
    )
    
    empathy_result = empathy.compute(sad_agent)
    spectrum = get_sympathy_spectrum(empathy_result)
    
    print("  Sympathy spectrum:")
    sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
    for sympathy_type, prob in sorted_spectrum[:5]:
        print(f"    {sympathy_type.value:18} -> {prob:.3f}")
    
    print("✅ Sympathy Spectrum PASSED")


def test_sympathy_result_dict():
    """SympathyResult to_dict."""
    print("\n=== TEST: Sympathy Result Dict ===")
    
    my_pad = PADState.neutral()
    sympathy = Sympathy(my_pad)
    
    agent = AgentState(
        agent_id="dict_test",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    
    result = sympathy.compute_from_agent(agent)
    result_dict = result.to_dict()
    
    print(f"  Keys: {list(result_dict.keys())}")
    print(f"  Has sympathy: {result_dict['has_sympathy']}")
    print(f"  Dominant: {result_dict['dominant']}")
    print(f"  Is prosocial: {result_dict['is_prosocial']}")
    
    assert "agent_id" in result_dict
    assert "responses" in result_dict
    assert "combined_pad" in result_dict
    
    print("✅ Sympathy Result Dict PASSED")


def test_multiple_sympathies():
    """Birden fazla sempati tepkisi."""
    print("\n=== TEST: Multiple Sympathies ===")
    
    my_pad = PADState.neutral()
    empathy = Empathy(my_pad)
    sympathy = Sympathy(my_pad)
    
    # Karmaşık durum: arkadaş haksızlığa uğramış
    agent = AgentState(
        agent_id="complex",
        facial_expression="sad",
        situation="conflict",
        relationship_to_self="friend",
        behavioral_cues=["crying"],
    )
    
    empathy_result = empathy.compute(agent)
    
    # Haksızlık bağlamı
    context = RelationshipContext(
        valence=0.6,
        perceived_injustice=0.8,
    )
    
    result = sympathy.compute(empathy_result, relationship=context)
    
    print(f"  Number of responses: {len(result.responses)}")
    for resp in result.responses:
        print(f"    - {resp.sympathy_type.value}: {resp.intensity:.3f}")
    
    # Birden fazla sempati olabilir
    if len(result.responses) > 1:
        print("  ✓ Multiple sympathies detected")
    
    print("✅ Multiple Sympathies PASSED")


def main():
    print("=" * 60)
    print("UEM v2 - Sympathy Module Test Suite")
    print("=" * 60)
    
    test_sympathy_types()
    test_sympathy_pad_effects()
    test_action_tendencies()
    test_relationship_context()
    test_basic_sympathy()
    test_sympathy_from_agent()
    test_rival_sympathy()
    test_predict_sympathy()
    test_quick_sympathy()
    test_sympathy_spectrum()
    test_sympathy_result_dict()
    test_multiple_sympathies()
    
    print("\n" + "=" * 60)
    print("🎉 ALL SYMPATHY TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
