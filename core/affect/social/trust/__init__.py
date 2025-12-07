"""
UEM v2 - Trust Module

Güven yönetimi - geçmiş etkileşimlere dayalı.

Trust = Geçmişe göre GÜVENMEK

7 Güven Türü: blind, earned, cautious, neutral, conditional, distrust, betrayed
4 Güven Boyutu: competence, benevolence, integrity, predictability

Kullanım:
    from core.affect.social.trust import Trust, TrustLevel, TrustType
    
    trust = Trust()
    
    # Olayları kaydet
    trust.record("alice", "promise_kept")
    trust.record("alice", "helped_me")
    trust.record("bob", "lied_to_me")
    
    # Güven sorgula
    print(f"Alice: {trust.get('alice'):.2f}")  # ~0.65
    print(f"Bob: {trust.get('bob'):.2f}")      # ~0.35
    
    # Karar desteği
    if trust.should_trust("alice", threshold=0.6):
        print("Alice güvenilir")
    
    # Analiz
    analysis = trust.analyze("alice")
    print(trust.explain_trust("bob"))
"""

from .types import (
    TrustLevel,
    TrustType,
    TrustDimension,
    TrustComponents,
    TrustEvent,
    create_trust_event,
    determine_trust_type,
    TRUST_EVENT_IMPACTS,
)

from .manager import (
    TrustProfile,
    TrustConfig,
    TrustManager,
)

from .trust import (
    Trust,
    quick_trust_check,
    calculate_risk_threshold,
)

__all__ = [
    # Types
    "TrustLevel",
    "TrustType",
    "TrustDimension",
    "TrustComponents",
    "TrustEvent",
    "create_trust_event",
    "determine_trust_type",
    "TRUST_EVENT_IMPACTS",
    
    # Manager
    "TrustProfile",
    "TrustConfig",
    "TrustManager",
    
    # Main
    "Trust",
    "quick_trust_check",
    "calculate_risk_threshold",
]
