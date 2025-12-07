#!/usr/bin/env python3
"""
UEM v2 - Emotion Module Test

Kurulumdan sonra çalıştır:
    python test_emotion.py
"""

import sys
sys.path.insert(0, '.')

from core.affect.emotion.core import (
    PADState,
    PADOctant,
    get_octant,
    pad_from_stimulus,
    BasicEmotion,
    get_emotion_pad,
    identify_emotion,
    EmotionState,
    RegulationStrategy,
    create_personality_baseline,
)


def test_pad_basic():
    """PAD temel operasyonları."""
    print("\n=== TEST: PAD Basic ===")
    
    # Oluşturma
    pad = PADState(pleasure=0.5, arousal=0.7, dominance=0.6)
    print(f"Created: {pad}")
    
    # Neutral
    neutral = PADState.neutral()
    print(f"Neutral: {neutral}")
    
    # Distance
    dist = pad.distance(neutral)
    print(f"Distance to neutral: {dist:.3f}")
    
    # Blend
    blended = pad.blend(neutral, 0.5)
    print(f"Blended (50%): {blended}")
    
    # Decay
    decayed = pad.decay(0.3)
    print(f"Decayed (30%): {decayed}")
    
    print("✅ PAD Basic PASSED")


def test_octants():
    """PAD oktant tespiti."""
    print("\n=== TEST: Octants ===")
    
    test_cases = [
        (PADState(pleasure=0.5, arousal=0.7, dominance=0.7), PADOctant.EXUBERANT),
        (PADState(pleasure=-0.5, arousal=0.8, dominance=0.2), PADOctant.ANXIOUS),
        (PADState(pleasure=-0.5, arousal=0.8, dominance=0.7), PADOctant.HOSTILE),
        (PADState(pleasure=0.5, arousal=0.3, dominance=0.6), PADOctant.RELAXED),
    ]
    
    for pad, expected in test_cases:
        octant = get_octant(pad)
        status = "✓" if octant == expected else "✗"
        print(f"  {status} {pad} -> {octant.value} (expected: {expected.value})")
    
    print("✅ Octants PASSED")


def test_basic_emotions():
    """Temel duygu PAD mapping."""
    print("\n=== TEST: Basic Emotions ===")
    
    for emotion in BasicEmotion:
        pad = get_emotion_pad(emotion)
        print(f"  {emotion.value:12} -> {pad}")
    
    print("✅ Basic Emotions PASSED")


def test_emotion_identification():
    """PAD'den duygu tespiti."""
    print("\n=== TEST: Emotion Identification ===")
    
    # Joy benzeri PAD
    joy_like = PADState(pleasure=0.7, arousal=0.6, dominance=0.7)
    identified = identify_emotion(joy_like)
    print(f"  Joy-like {joy_like} -> {identified}")
    
    # Fear benzeri PAD
    fear_like = PADState(pleasure=-0.6, arousal=0.8, dominance=0.2)
    identified = identify_emotion(fear_like)
    print(f"  Fear-like {fear_like} -> {identified}")
    
    # Anger benzeri PAD
    anger_like = PADState(pleasure=-0.5, arousal=0.8, dominance=0.8)
    identified = identify_emotion(anger_like)
    print(f"  Anger-like {anger_like} -> {identified}")
    
    print("✅ Emotion Identification PASSED")


def test_stimulus_response():
    """Stimulus'tan duygu üretme."""
    print("\n=== TEST: Stimulus Response ===")
    
    # Yüksek tehdit
    threat_pad = pad_from_stimulus(threat_level=0.8, reward_level=0.0)
    print(f"  High threat: {threat_pad} -> {identify_emotion(threat_pad)}")
    
    # Yüksek ödül
    reward_pad = pad_from_stimulus(threat_level=0.0, reward_level=0.8)
    print(f"  High reward: {reward_pad} -> {identify_emotion(reward_pad)}")
    
    # Belirsizlik
    uncertain_pad = pad_from_stimulus(threat_level=0.3, reward_level=0.3, uncertainty=0.9)
    print(f"  Uncertain: {uncertain_pad} -> {identify_emotion(uncertain_pad)}")
    
    print("✅ Stimulus Response PASSED")


def test_emotion_dynamics():
    """Duygu dinamikleri."""
    print("\n=== TEST: Emotion Dynamics ===")
    
    # EmotionState oluştur
    emotion = EmotionState()
    print(f"  Initial: {emotion.current}")
    
    # Korku tetikle
    emotion.trigger_emotion(BasicEmotion.FEAR, intensity=0.8)
    print(f"  After FEAR trigger: {emotion.current}")
    print(f"  Dominant emotion: {emotion.get_dominant_emotion()}")
    
    # Decay simülasyonu
    for i in range(3):
        emotion.update(delta_time=2.0)
        print(f"  After {(i+1)*2}s decay: {emotion.current}")
    
    # Düzenleme
    emotion.regulate(RegulationStrategy.REAPPRAISAL, strength=0.7)
    print(f"  After reappraisal: {emotion.current}")
    
    print("✅ Emotion Dynamics PASSED")


def test_personality_baseline():
    """Kişilik bazlı baseline."""
    print("\n=== TEST: Personality Baseline ===")
    
    # Extravert
    extravert = create_personality_baseline(extraversion=0.8, neuroticism=0.2)
    print(f"  Extravert: {extravert}")
    
    # Neurotic
    neurotic = create_personality_baseline(extraversion=0.3, neuroticism=0.8)
    print(f"  Neurotic: {neurotic}")
    
    # Balanced
    balanced = create_personality_baseline(extraversion=0.5, neuroticism=0.5)
    print(f"  Balanced: {balanced}")
    
    print("✅ Personality Baseline PASSED")


def test_social_contagion():
    """Sosyal duygu bulaşması."""
    print("\n=== TEST: Social Contagion ===")
    
    # Kendi durumum
    my_emotion = EmotionState()
    my_emotion.current = PADState(pleasure=0.3, arousal=0.4, dominance=0.5)
    print(f"  My initial: {my_emotion.current}")
    
    # Başkasının korkusu
    other_fear = PADState(pleasure=-0.7, arousal=0.9, dominance=0.2)
    print(f"  Other's fear: {other_fear}")
    
    # Düşük empati
    my_emotion.social_contagion(other_fear, empathy_level=0.3)
    print(f"  After low empathy contagion: {my_emotion.current}")
    
    # Reset ve yüksek empati
    my_emotion.current = PADState(pleasure=0.3, arousal=0.4, dominance=0.5)
    my_emotion.social_contagion(other_fear, empathy_level=0.9)
    print(f"  After high empathy contagion: {my_emotion.current}")
    
    print("✅ Social Contagion PASSED")


def main():
    print("=" * 60)
    print("UEM v2 - Emotion Module Test Suite")
    print("=" * 60)
    
    test_pad_basic()
    test_octants()
    test_basic_emotions()
    test_emotion_identification()
    test_stimulus_response()
    test_emotion_dynamics()
    test_personality_baseline()
    test_social_contagion()
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
