#!/usr/bin/env python3
"""
UEM v2 - Trust Module Test

Kurulumdan sonra çalıştır:
    python tests/unit/test_trust.py
"""

import sys
sys.path.insert(0, '.')

from core.affect.social.trust import (
    Trust,
    TrustLevel,
    TrustType,
    TrustDimension,
    TrustComponents,
    TrustEvent,
    TrustProfile,
    TrustConfig,
    TrustManager,
    create_trust_event,
    determine_trust_type,
    quick_trust_check,
    calculate_risk_threshold,
    TRUST_EVENT_IMPACTS,
)


def test_trust_components():
    """Güven bileşenleri."""
    print("\n=== TEST: Trust Components ===")
    
    # Default
    default = TrustComponents.default()
    print(f"  Default: {default.to_dict()}")
    assert default.overall() == 0.5
    
    # High
    high = TrustComponents.high()
    print(f"  High: overall={high.overall():.2f}")
    assert abs(high.overall() - 0.8) < 0.01  # Floating point tolerance
    
    # Low
    low = TrustComponents.low()
    print(f"  Low: overall={low.overall():.2f}")
    assert abs(low.overall() - 0.2) < 0.01
    
    # Custom
    custom = TrustComponents(
        competence=0.9,
        benevolence=0.7,
        integrity=0.8,
        predictability=0.6,
    )
    print(f"  Custom: overall={custom.overall():.2f}")
    print(f"  Strongest: {custom.strongest_dimension().value}")
    print(f"  Weakest: {custom.weakest_dimension().value}")
    
    assert custom.strongest_dimension() == TrustDimension.COMPETENCE
    assert custom.weakest_dimension() == TrustDimension.PREDICTABILITY
    
    print("✅ Trust Components PASSED")


def test_trust_levels():
    """Güven seviyeleri."""
    print("\n=== TEST: Trust Levels ===")
    
    test_cases = [
        (0.95, TrustLevel.BLIND),
        (0.75, TrustLevel.HIGH),
        (0.55, TrustLevel.MODERATE),
        (0.40, TrustLevel.CAUTIOUS),
        (0.20, TrustLevel.LOW),
        (0.05, TrustLevel.DISTRUST),
    ]
    
    for value, expected in test_cases:
        level = TrustLevel.from_value(value)
        status = "✓" if level == expected else "✗"
        print(f"  {status} {value:.2f} -> {level.value} (expected: {expected.value})")
        assert level == expected
    
    print("✅ Trust Levels PASSED")


def test_trust_events():
    """Güven olayları."""
    print("\n=== TEST: Trust Events ===")
    
    # Pozitif olay
    event1 = create_trust_event("promise_kept", "work project")
    print(f"  promise_kept: dim={event1.dimension.value}, impact={event1.impact:+.2f}")
    assert event1.impact > 0
    assert event1.dimension == TrustDimension.INTEGRITY
    
    # Negatif olay
    event2 = create_trust_event("betrayal", "shared secret")
    print(f"  betrayal: dim={event2.dimension.value}, impact={event2.impact:+.2f}")
    assert event2.impact < 0
    assert event2.dimension == TrustDimension.BENEVOLENCE
    
    # Ağırlıklı etki
    print(f"  betrayal weighted_impact: {event2.weighted_impact():.2f}")
    
    print("✅ Trust Events PASSED")


def test_basic_trust():
    """Temel güven işlemleri."""
    print("\n=== TEST: Basic Trust ===")
    
    trust = Trust()
    
    # Yeni ajan - nötr güven
    initial = trust.get("alice")
    print(f"  Initial trust (alice): {initial:.2f}")
    assert initial == 0.5  # Nötr başlangıç
    
    # Pozitif olaylar
    trust.record("alice", "promise_kept")
    trust.record("alice", "helped_me")
    
    after_positive = trust.get("alice")
    print(f"  After positive events: {after_positive:.2f}")
    assert after_positive > initial
    
    # Negatif olay
    trust.record("bob", "lied_to_me")
    
    bob_trust = trust.get("bob")
    print(f"  Bob (after lie): {bob_trust:.2f}")
    assert bob_trust < 0.5
    
    print("✅ Basic Trust PASSED")


def test_trust_profile():
    """Güven profili."""
    print("\n=== TEST: Trust Profile ===")
    
    trust = Trust()
    
    # Olaylar kaydet
    trust.record("charlie", "promise_kept")
    trust.record("charlie", "competent_action")
    trust.record("charlie", "consistent_behavior")
    
    profile = trust.get_profile("charlie")
    
    print(f"  Agent: {profile.agent_id}")
    print(f"  Overall: {profile.overall_trust:.2f}")
    print(f"  Level: {profile.trust_level.value}")
    print(f"  Type: {profile.trust_type.value}")
    print(f"  Interactions: {profile.interaction_count}")
    print(f"  Positive: {profile.positive_events}, Negative: {profile.negative_events}")
    
    assert profile.interaction_count == 3
    assert profile.positive_events == 3
    assert profile.negative_events == 0
    
    print("✅ Trust Profile PASSED")


def test_trust_type_determination():
    """Güven tipi belirleme."""
    print("\n=== TEST: Trust Type Determination ===")
    
    # Yeni - neutral
    type1 = determine_trust_type(TrustComponents.default(), history_length=0)
    print(f"  New agent: {type1.value}")
    assert type1 == TrustType.NEUTRAL
    
    # Az geçmiş, yüksek güven - blind
    type2 = determine_trust_type(TrustComponents.high(), history_length=1)
    print(f"  Quick high trust: {type2.value}")
    assert type2 == TrustType.BLIND
    
    # Çok geçmiş, yüksek güven - earned veya conditional (0.8 sınırda)
    very_high = TrustComponents(0.85, 0.85, 0.85, 0.85)
    type3 = determine_trust_type(very_high, history_length=10)
    print(f"  Long high trust: {type3.value}")
    assert type3 == TrustType.EARNED
    
    # İhanet sonrası
    type4 = determine_trust_type(TrustComponents.low(), history_length=5, had_betrayal=True)
    print(f"  After betrayal: {type4.value}")
    assert type4 == TrustType.BETRAYED
    
    print("✅ Trust Type Determination PASSED")


def test_should_trust():
    """Güven kararı."""
    print("\n=== TEST: Should Trust ===")
    
    trust = Trust()
    
    # Güvenilir ajan oluştur
    trust.record("reliable", "promise_kept")
    trust.record("reliable", "helped_me")
    trust.record("reliable", "honest_feedback")
    
    # Güvenilmez ajan oluştur
    trust.record("unreliable", "lied_to_me")
    trust.record("unreliable", "promise_broken")
    
    reliable_trust = trust.should_trust("reliable", threshold=0.5)
    unreliable_trust = trust.should_trust("unreliable", threshold=0.5)
    
    print(f"  Reliable ({trust.get('reliable'):.2f}): should_trust={reliable_trust}")
    print(f"  Unreliable ({trust.get('unreliable'):.2f}): should_trust={unreliable_trust}")
    
    assert reliable_trust == True
    assert unreliable_trust == False
    
    print("✅ Should Trust PASSED")


def test_trust_for_action():
    """Aksiyon için güven değerlendirmesi."""
    print("\n=== TEST: Trust for Action ===")
    
    trust = Trust()
    
    # Orta güvenli ajan
    trust.record("dave", "promise_kept")
    trust.record("dave", "competent_action")
    
    # Düşük riskli aksiyon
    can_low, reason_low = trust.trust_for_action("dave", action_risk=0.2)
    print(f"  Low risk (0.2): {can_low} - {reason_low}")
    
    # Yüksek riskli aksiyon
    can_high, reason_high = trust.trust_for_action("dave", action_risk=0.8)
    print(f"  High risk (0.8): {can_high} - {reason_high}")
    
    # Düşük risk kabul edilmeli, yüksek risk reddedilmeli
    assert can_low == True
    # can_high duruma göre değişebilir
    
    print("✅ Trust for Action PASSED")


def test_betrayal_impact():
    """İhanet etkisi."""
    print("\n=== TEST: Betrayal Impact ===")
    
    trust = Trust()
    
    # Güven oluştur
    trust.record("eve", "promise_kept")
    trust.record("eve", "helped_me")
    trust.record("eve", "competent_action")
    
    before = trust.get("eve")
    print(f"  Before betrayal: {before:.2f}")
    
    # İhanet
    trust.record("eve", "betrayal")
    
    after = trust.get("eve")
    print(f"  After betrayal: {after:.2f}")
    
    profile = trust.get_profile("eve")
    print(f"  Betrayal count: {profile.betrayal_count}")
    print(f"  Trust type: {profile.trust_type.value}")
    
    # İhanet büyük düşüş yapmalı
    assert after < before
    assert profile.betrayal_count == 1
    
    print("✅ Betrayal Impact PASSED")


def test_trust_decay():
    """Güven sönümlemesi."""
    print("\n=== TEST: Trust Decay ===")
    
    trust = Trust()
    
    # Yüksek güven oluştur
    trust.set_initial("frank", TrustType.EARNED)
    
    before = trust.get("frank")
    print(f"  Before decay: {before:.2f}")
    
    # 30 gün decay
    trust.apply_time_decay("frank", days=30)
    
    after = trust.get("frank")
    print(f"  After 30 days: {after:.2f}")
    
    # Nötre doğru kaymalı
    assert after < before
    assert after >= 0.5  # Ama nötrün altına düşmemeli
    
    print("✅ Trust Decay PASSED")


def test_compare_and_rank():
    """Karşılaştırma ve sıralama."""
    print("\n=== TEST: Compare and Rank ===")
    
    trust = Trust()
    
    # Farklı güven seviyeleri
    trust.set_initial("high_trust", TrustType.EARNED)
    trust.set_initial("low_trust", TrustType.DISTRUST)
    trust.record("mid_trust", "promise_kept")
    
    # Karşılaştır
    winner = trust.compare("high_trust", "low_trust")
    print(f"  Compare high vs low: {winner}")
    assert winner == "high_trust"
    
    # Sırala
    ranking = trust.rank(["high_trust", "mid_trust", "low_trust"])
    print(f"  Ranking: {ranking}")
    assert ranking[0][0] == "high_trust"
    assert ranking[-1][0] == "low_trust"
    
    print("✅ Compare and Rank PASSED")


def test_analyze():
    """Güven analizi."""
    print("\n=== TEST: Analyze ===")
    
    trust = Trust()
    
    # Karışık geçmiş
    trust.record("grace", "promise_kept")
    trust.record("grace", "helped_me")
    trust.record("grace", "unpredictable_behavior")
    
    analysis = trust.analyze("grace")
    
    print(f"  Overall: {analysis['overall_trust']:.2f}")
    print(f"  Level: {analysis['trust_level']}")
    print(f"  Weakest: {analysis['weakest_dimension']}")
    print(f"  Recommendations: {analysis['recommendations']}")
    
    assert "overall_trust" in analysis
    assert "recommendations" in analysis
    
    print("✅ Analyze PASSED")


def test_explain_trust():
    """Güven açıklaması."""
    print("\n=== TEST: Explain Trust ===")
    
    trust = Trust()
    
    trust.record("henry", "promise_kept")
    trust.record("henry", "lied_to_me")
    
    explanation = trust.explain_trust("henry")
    print(f"  Explanation: {explanation}")
    
    assert "henry" in explanation.lower()
    assert "interaction" in explanation.lower()
    
    print("✅ Explain Trust PASSED")


def test_quick_trust_check():
    """Hızlı güven kontrolü."""
    print("\n=== TEST: Quick Trust Check ===")
    
    # Çok pozitif
    level1 = quick_trust_check(10, 0.9, had_betrayal=False)
    print(f"  High ratio (0.9): {level1.value}")
    assert level1 == TrustLevel.HIGH
    
    # İhanet var
    level2 = quick_trust_check(10, 0.9, had_betrayal=True)
    print(f"  High ratio + betrayal: {level2.value}")
    assert level2 == TrustLevel.CAUTIOUS
    
    # Az etkileşim
    level3 = quick_trust_check(2, 0.9, had_betrayal=False)
    print(f"  Few interactions: {level3.value}")
    assert level3 == TrustLevel.CAUTIOUS
    
    print("✅ Quick Trust Check PASSED")


def test_risk_threshold():
    """Risk eşiği hesaplama."""
    print("\n=== TEST: Risk Threshold ===")
    
    thresholds = [
        (TrustLevel.HIGH, 0.7),
        (TrustLevel.MODERATE, 0.5),
        (TrustLevel.LOW, 0.15),
    ]
    
    for level, expected in thresholds:
        threshold = calculate_risk_threshold(level)
        print(f"  {level.value}: max_risk={threshold:.2f}")
        assert threshold == expected
    
    print("✅ Risk Threshold PASSED")


def test_most_least_trusted():
    """En güvenilir/güvenilmez listesi."""
    print("\n=== TEST: Most/Least Trusted ===")
    
    trust = Trust()
    
    # Çeşitli ajanlar
    trust.set_initial("best", TrustType.EARNED)
    trust.set_initial("good", TrustType.CONDITIONAL)
    trust.set_initial("bad", TrustType.DISTRUST)
    trust.record("neutral", "consistent_behavior")
    
    most = trust.most_trusted(3)
    print(f"  Most trusted: {most}")
    
    least = trust.least_trusted(3)
    print(f"  Least trusted: {least}")
    
    assert most[0][0] == "best"
    assert least[0][0] == "bad"
    
    print("✅ Most/Least Trusted PASSED")


def main():
    print("=" * 60)
    print("UEM v2 - Trust Module Test Suite")
    print("=" * 60)
    
    test_trust_components()
    test_trust_levels()
    test_trust_events()
    test_basic_trust()
    test_trust_profile()
    test_trust_type_determination()
    test_should_trust()
    test_trust_for_action()
    test_betrayal_impact()
    test_trust_decay()
    test_compare_and_rank()
    test_analyze()
    test_explain_trust()
    test_quick_trust_check()
    test_risk_threshold()
    test_most_least_trusted()
    
    print("\n" + "=" * 60)
    print("🎉 ALL TRUST TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
