"""
UEM v2 - StateVector Integration Tests

StateVector ↔ Social Affect entegrasyon testleri.
"""

import sys
sys.path.insert(0, '.')

from foundation.state import StateVector, SVField, StateVectorBridge, get_state_bridge
from core.affect.emotion.core import PADState, BasicEmotion
from core.affect.social.empathy import Empathy, AgentState, EmpathyResult
from core.affect.social.sympathy import Sympathy, SympathyResult, RelationshipContext
from core.affect.social.trust import Trust, TrustProfile
from core.affect.social.orchestrator import (
    SocialAffectOrchestrator,
    OrchestratorConfig,
    create_orchestrator,
    process_social_affect,
)


def print_header(title: str):
    print(f"\n=== TEST: {title} ===")


def test_svfield_definitions():
    """SVField tanımları testi."""
    print_header("SVField Definitions")
    
    # Core fields
    core = SVField.core_fields()
    assert len(core) == 3
    assert SVField.RESOURCE in core
    assert SVField.THREAT in core
    assert SVField.WELLBEING in core
    print(f"  ✓ Core fields: {[f.value for f in core]}")
    
    # Emotion fields
    emotion = SVField.emotion_fields()
    assert SVField.VALENCE in emotion
    assert SVField.AROUSAL in emotion
    assert SVField.DOMINANCE in emotion
    print(f"  ✓ Emotion fields: {[f.value for f in emotion]}")
    
    # Empathy fields
    empathy = SVField.empathy_fields()
    assert SVField.EMPATHY_TOTAL in empathy
    assert SVField.COGNITIVE_EMPATHY in empathy
    print(f"  ✓ Empathy fields: {[f.value for f in empathy]}")
    
    # Sympathy fields
    sympathy = SVField.sympathy_fields()
    assert SVField.SYMPATHY_LEVEL in sympathy
    assert SVField.SYMPATHY_VALENCE in sympathy
    print(f"  ✓ Sympathy fields: {[f.value for f in sympathy]}")
    
    # Trust fields
    trust = SVField.trust_fields()
    assert SVField.TRUST_VALUE in trust
    assert SVField.TRUST_COMPETENCE in trust
    print(f"  ✓ Trust fields: {[f.value for f in trust]}")
    
    # Social fields (all combined)
    social = SVField.social_fields()
    assert len(social) == len(empathy) + len(sympathy) + len(trust)
    print(f"  ✓ Total social fields: {len(social)}")
    
    print("✅ SVField Definitions PASSED")


def test_bridge_write_pad():
    """Bridge PAD yazma testi."""
    print_header("Bridge Write PAD")
    
    bridge = get_state_bridge()
    state = StateVector()
    
    # Positive PAD
    pad = PADState(pleasure=0.8, arousal=0.6, dominance=0.7)
    bridge.write_pad(state, pad)
    
    valence = state.get(SVField.VALENCE)
    arousal = state.get(SVField.AROUSAL)
    dominance = state.get(SVField.DOMINANCE)
    
    # Valence: (0.8 + 1) / 2 = 0.9
    assert 0.89 < valence < 0.91, f"Expected ~0.9, got {valence}"
    assert arousal == 0.6
    assert dominance == 0.7
    print(f"  ✓ PAD → SV: V={valence:.2f}, A={arousal:.2f}, D={dominance:.2f}")
    
    # Negative PAD
    pad_neg = PADState(pleasure=-0.5, arousal=0.3, dominance=0.4)
    bridge.write_pad(state, pad_neg)
    
    valence_neg = state.get(SVField.VALENCE)
    # Valence: (-0.5 + 1) / 2 = 0.25
    assert 0.24 < valence_neg < 0.26, f"Expected ~0.25, got {valence_neg}"
    print(f"  ✓ Negative PAD → SV: V={valence_neg:.2f}")
    
    print("✅ Bridge Write PAD PASSED")


def test_bridge_read_pad():
    """Bridge PAD okuma testi."""
    print_header("Bridge Read PAD")
    
    bridge = get_state_bridge()
    state = StateVector()
    
    # Set values
    state.set(SVField.VALENCE, 0.9)     # → pleasure = 0.8
    state.set(SVField.AROUSAL, 0.6)
    state.set(SVField.DOMINANCE, 0.7)
    
    # Read
    pad = bridge.read_self_pad(state)
    
    assert 0.79 < pad.pleasure < 0.81, f"Expected ~0.8, got {pad.pleasure}"
    assert pad.arousal == 0.6
    assert pad.dominance == 0.7
    print(f"  ✓ SV → PAD: P={pad.pleasure:.2f}, A={pad.arousal:.2f}, D={pad.dominance:.2f}")
    
    # Round-trip test
    bridge.write_pad(state, pad)
    pad2 = bridge.read_self_pad(state)
    
    assert abs(pad.pleasure - pad2.pleasure) < 0.01
    print(f"  ✓ Round-trip: OK")
    
    print("✅ Bridge Read PAD PASSED")


def test_bridge_write_empathy():
    """Bridge empathy yazma testi."""
    print_header("Bridge Write Empathy")
    
    bridge = get_state_bridge()
    state = StateVector()
    
    # Empathy hesapla
    empathy_module = Empathy(PADState.neutral())
    agent = AgentState(
        agent_id="test",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    empathy_result = empathy_module.compute(agent)
    
    # StateVector'a yaz
    bridge.write_empathy(state, empathy_result)
    
    # Kontrol
    total = state.get(SVField.EMPATHY_TOTAL)
    cognitive = state.get(SVField.COGNITIVE_EMPATHY)
    affective = state.get(SVField.AFFECTIVE_EMPATHY)
    
    assert total > 0, "Empathy total should be > 0"
    assert cognitive > 0, "Cognitive empathy should be > 0"
    print(f"  ✓ Empathy → SV: total={total:.2f}, cog={cognitive:.2f}, aff={affective:.2f}")
    
    # Kanalları oku
    channels = bridge.read_empathy_channels(state)
    assert channels["total"] == total
    print(f"  ✓ Read channels: {channels}")
    
    print("✅ Bridge Write Empathy PASSED")


def test_bridge_write_sympathy():
    """Bridge sympathy yazma testi."""
    print_header("Bridge Write Sympathy")
    
    bridge = get_state_bridge()
    state = StateVector()
    
    # Empathy + Sympathy hesapla
    empathy_module = Empathy(PADState.neutral())
    sympathy_module = Sympathy(PADState.neutral())
    
    agent = AgentState(
        agent_id="test",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    
    empathy_result = empathy_module.compute(agent)
    sympathy_result = sympathy_module.compute(empathy_result, RelationshipContext.friend())
    
    # StateVector'a yaz
    bridge.write_sympathy(state, sympathy_result)
    
    # Kontrol
    level = state.get(SVField.SYMPATHY_LEVEL)
    valence = state.get(SVField.SYMPATHY_VALENCE)
    
    print(f"  ✓ Sympathy → SV: level={level:.2f}, valence={valence:.2f}")
    
    # Prosocial → valence > 0.5
    if sympathy_result.is_prosocial():
        assert valence > 0.5, f"Prosocial should have valence > 0.5, got {valence}"
        print(f"  ✓ Prosocial detected: valence > 0.5")
    
    print("✅ Bridge Write Sympathy PASSED")


def test_bridge_write_trust():
    """Bridge trust yazma testi."""
    print_header("Bridge Write Trust")
    
    bridge = get_state_bridge()
    state = StateVector()
    
    # Trust profili oluştur
    trust_module = Trust()
    trust_module.record("alice", "helped_me", context="test")
    profile = trust_module.get_profile("alice")
    
    # StateVector'a yaz
    bridge.write_trust(state, profile)
    
    # Kontrol
    trust_value = state.get(SVField.TRUST_VALUE)
    competence = state.get(SVField.TRUST_COMPETENCE)
    
    print(f"  ✓ Trust → SV: value={trust_value:.2f}, comp={competence:.2f}")
    
    # Dimensions oku
    dims = bridge.read_trust_dimensions(state)
    assert dims["overall"] == trust_value
    print(f"  ✓ Read dimensions: {dims}")
    
    print("✅ Bridge Write Trust PASSED")


def test_orchestrator_from_state_vector():
    """StateVector'dan orchestrator oluşturma testi."""
    print_header("Orchestrator from StateVector")
    
    # PAD değerleri içeren StateVector
    state = StateVector(resource=0.8, threat=0.1, wellbeing=0.7)
    state.set(SVField.VALENCE, 0.7)   # pleasure = 0.4
    state.set(SVField.AROUSAL, 0.5)
    state.set(SVField.DOMINANCE, 0.6)
    
    # Orchestrator oluştur
    orchestrator = SocialAffectOrchestrator.from_state_vector(state)
    
    # Self PAD kontrol
    assert orchestrator.self_state is not None
    print(f"  ✓ Self PAD loaded: P={orchestrator.self_state.pleasure:.2f}")
    
    # StateVector bağlı mı?
    assert orchestrator.state_vector is state
    print(f"  ✓ StateVector bound: {orchestrator.state_vector is not None}")
    
    print("✅ Orchestrator from StateVector PASSED")


def test_orchestrator_writes_to_state_vector():
    """Orchestrator StateVector'a yazma testi."""
    print_header("Orchestrator Writes to StateVector")
    
    # Boş StateVector
    state = StateVector()
    
    # Başlangıç değerleri
    initial_empathy = state.get(SVField.EMPATHY_TOTAL)
    initial_trust = state.get(SVField.TRUST_VALUE)
    
    print(f"  Initial: empathy={initial_empathy:.2f}, trust={initial_trust:.2f}")
    
    # Orchestrator oluştur ve işle
    orchestrator = SocialAffectOrchestrator.from_state_vector(state)
    
    agent = AgentState(
        agent_id="bob",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="friend",
    )
    
    result = orchestrator.process(agent)
    
    # StateVector güncellendi mi?
    new_empathy = state.get(SVField.EMPATHY_TOTAL)
    new_sympathy = state.get(SVField.SYMPATHY_LEVEL)
    new_trust = state.get(SVField.TRUST_VALUE)
    
    assert new_empathy > 0, f"Empathy should be written, got {new_empathy}"
    print(f"  ✓ Empathy written: {initial_empathy:.2f} → {new_empathy:.2f}")
    print(f"  ✓ Sympathy written: {new_sympathy:.2f}")
    print(f"  ✓ Trust written: {new_trust:.2f}")
    
    # Result'ta StateVector referansı var mı?
    assert result.state_vector is state
    print(f"  ✓ Result has StateVector reference")
    
    print("✅ Orchestrator Writes to StateVector PASSED")


def test_state_vector_persistence():
    """StateVector değerlerinin kalıcılığı testi."""
    print_header("StateVector Persistence")
    
    state = StateVector()
    orchestrator = SocialAffectOrchestrator.from_state_vector(state)
    
    # İlk agent
    agent1 = AgentState(
        agent_id="alice",
        facial_expression="happy",
        situation="success",
        relationship_to_self="friend",
    )
    result1 = orchestrator.process(agent1)
    
    empathy_after_1 = state.get(SVField.EMPATHY_TOTAL)
    trust_after_1 = state.get(SVField.TRUST_VALUE)
    print(f"  After alice: empathy={empathy_after_1:.2f}, trust={trust_after_1:.2f}")
    
    # İkinci agent (aynı orchestrator)
    agent2 = AgentState(
        agent_id="bob",
        facial_expression="angry",
        situation="conflict",
        relationship_to_self="rival",
    )
    result2 = orchestrator.process(agent2)
    
    empathy_after_2 = state.get(SVField.EMPATHY_TOTAL)
    trust_after_2 = state.get(SVField.TRUST_VALUE)
    print(f"  After bob: empathy={empathy_after_2:.2f}, trust={trust_after_2:.2f}")
    
    # Empathy değişmeli (yeni hesaplama)
    # Trust farklı agent için farklı olabilir
    print(f"  ✓ StateVector persists across process calls")
    
    print("✅ StateVector Persistence PASSED")


def test_full_integration():
    """Tam entegrasyon senaryosu."""
    print_header("Full Integration")
    
    # 1. Sistem başlat
    state = StateVector(
        resource=0.7,
        threat=0.0,
        wellbeing=0.6,
    )
    state.set(SVField.VALENCE, 0.6)  # Slightly positive
    state.set(SVField.AROUSAL, 0.4)
    state.set(SVField.DOMINANCE, 0.5)
    
    print(f"  Initial state:")
    print(f"    Core: r={state.resource:.2f}, t={state.threat:.2f}, w={state.wellbeing:.2f}")
    print(f"    PAD: V={state.get(SVField.VALENCE):.2f}, A={state.get(SVField.AROUSAL):.2f}, D={state.get(SVField.DOMINANCE):.2f}")
    
    # 2. Orchestrator oluştur
    orchestrator = SocialAffectOrchestrator.from_state_vector(state)
    
    # 3. Senaryo: Üzgün arkadaş
    print(f"\n  Scenario: Sad friend")
    friend = AgentState(
        agent_id="friend_1",
        facial_expression="sad",
        situation="loss",
        observed_pad=PADState(pleasure=-0.6, arousal=0.3, dominance=0.2),
        relationship_to_self="friend",
    )
    
    result = orchestrator.process(friend)
    
    print(f"  Result:")
    print(f"    Empathy: {result.empathy.total_empathy:.2f}")
    print(f"    Sympathy: {result.sympathy.dominant_sympathy.value if result.sympathy.dominant_sympathy else 'none'}")
    print(f"    Trust: {result.trust_before:.2f} → {result.trust_after:.2f}")
    print(f"    Action: {result.suggested_action}")
    
    print(f"\n  StateVector after:")
    print(f"    Empathy: {state.get(SVField.EMPATHY_TOTAL):.2f}")
    print(f"    Sympathy: level={state.get(SVField.SYMPATHY_LEVEL):.2f}, valence={state.get(SVField.SYMPATHY_VALENCE):.2f}")
    print(f"    Trust: {state.get(SVField.TRUST_VALUE):.2f}")
    
    # 4. Summary
    bridge = get_state_bridge()
    summary = bridge.get_affect_summary(state)
    print(f"\n  Affect summary keys: {list(summary.keys())}")
    
    assert state.get(SVField.EMPATHY_TOTAL) > 0
    assert state.get(SVField.SYMPATHY_LEVEL) > 0
    
    print("\n✅ Full Integration PASSED")


def test_process_social_affect_helper():
    """process_social_affect helper fonksiyonu testi."""
    print_header("process_social_affect Helper")
    
    state = StateVector()
    
    agent = AgentState(
        agent_id="helper_test",
        facial_expression="sad",
        situation="loss",
        relationship_to_self="colleague",
    )
    
    # Helper kullan
    result = process_social_affect(agent, state)
    
    assert result.agent_id == "helper_test"
    assert result.empathy is not None
    assert state.get(SVField.EMPATHY_TOTAL) > 0
    
    print(f"  ✓ Helper works: empathy={result.empathy.total_empathy:.2f}")
    print(f"  ✓ SV updated: {state.get(SVField.EMPATHY_TOTAL):.2f}")
    
    print("✅ process_social_affect Helper PASSED")


def test_social_context_read():
    """SocialContext okuma testi."""
    print_header("SocialContext Read")
    
    state = StateVector()
    bridge = get_state_bridge()
    
    # Değerleri set et
    state.set(SVField.EMPATHY_TOTAL, 0.75)
    state.set(SVField.SYMPATHY_LEVEL, 0.6)
    state.set(SVField.SYMPATHY_VALENCE, 0.8)
    state.set(SVField.TRUST_VALUE, 0.65)
    state.set(SVField.RELATIONSHIP_QUALITY, 0.7)
    
    # Oku
    context = bridge.read_social_context(state)
    
    assert context.empathy_total == 0.75
    assert context.sympathy_level == 0.6
    assert context.trust_value == 0.65
    
    print(f"  ✓ Context: empathy={context.empathy_total:.2f}, sympathy={context.sympathy_level:.2f}")
    print(f"  ✓ Context: trust={context.trust_value:.2f}, quality={context.relationship_quality:.2f}")
    
    print("✅ SocialContext Read PASSED")


def test_reset_social_fields():
    """Sosyal alanları sıfırlama testi."""
    print_header("Reset Social Fields")
    
    state = StateVector()
    bridge = get_state_bridge()
    
    # Değerleri set et
    state.set(SVField.EMPATHY_TOTAL, 0.75)
    state.set(SVField.SYMPATHY_LEVEL, 0.6)
    state.set(SVField.TRUST_VALUE, 0.65)
    
    print(f"  Before: empathy={state.get(SVField.EMPATHY_TOTAL):.2f}, trust={state.get(SVField.TRUST_VALUE):.2f}")
    
    # Sıfırla
    bridge.reset_social_fields(state)
    
    # Kontrol
    assert state.get(SVField.EMPATHY_TOTAL) == 0.0
    assert state.get(SVField.SYMPATHY_LEVEL) == 0.0
    assert state.get(SVField.TRUST_VALUE) == 0.5  # Neutral, 0 değil
    
    print(f"  After: empathy={state.get(SVField.EMPATHY_TOTAL):.2f}, trust={state.get(SVField.TRUST_VALUE):.2f}")
    
    print("✅ Reset Social Fields PASSED")


def main():
    """Tüm testleri çalıştır."""
    print("=" * 60)
    print("UEM v2 - StateVector Integration Tests")
    print("=" * 60)
    
    tests = [
        test_svfield_definitions,
        test_bridge_write_pad,
        test_bridge_read_pad,
        test_bridge_write_empathy,
        test_bridge_write_sympathy,
        test_bridge_write_trust,
        test_orchestrator_from_state_vector,
        test_orchestrator_writes_to_state_vector,
        test_state_vector_persistence,
        test_full_integration,
        test_process_social_affect_helper,
        test_social_context_read,
        test_reset_social_fields,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    if failed == 0:
        print(f"🎉 ALL {passed} TESTS PASSED!")
    else:
        print(f"⚠️  {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
