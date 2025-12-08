#!/usr/bin/env python3
"""
UEM Dashboard Demo - 20 Farklı Senaryo

Bu script farklı trust senaryolarını simüle eder.
Her senaryo için:
1. Episode kaydedilir
2. Interaction kaydedilir
3. Cognitive cycle çalıştırılır

Dashboard'dan sonuçları kontrol edebilirsiniz.

Kullanım:
    python scripts/demo_dashboard.py

Dashboard:
    streamlit run interface/dashboard/app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from core.memory import (
    get_memory_store, reset_memory_store,
    Interaction, InteractionType,
    MemoryConfig, Episode, EpisodeType,
)
from engine.cycle import CognitiveCycle, CycleConfig
from meta.monitoring.persistence import MonitoringPersistence

# Database connection
DB_URL = "postgresql://uem:uem_secret@localhost:5432/uem_v2"


def create_memory():
    """Create memory store with PostgreSQL persistence."""
    reset_memory_store()
    config = MemoryConfig(
        use_persistence=True,
        db_connection_string=DB_URL,
    )
    return get_memory_store(config)


def create_cycle():
    """Create cognitive cycle with monitoring enabled."""
    config = CycleConfig(
        enable_monitoring=True,
        emit_events=True,
        report_each_cycle=False,
    )
    return CognitiveCycle(config=config)


def run_scenarios(memory, cycle):
    """20 farklı senaryo çalıştır."""

    print("\n" + "="*60)
    print("UEM Dashboard Demo - 20 Senaryo")
    print("Her senaryo: Episode + Interaction + Cycle")
    print("="*60 + "\n")

    scenarios = [
        # ═══════════════════════════════════════════════════════════
        # POZİTİF SENARYOLAR (Trust artışı)
        # ═══════════════════════════════════════════════════════════

        # Senaryo 1: Alice yardım etti
        {
            "agent": "alice",
            "type": InteractionType.HELPED,
            "episode_type": EpisodeType.COOPERATION,
            "trust_impact": 0.15,
            "description": "Alice zor durumda yardım etti",
        },

        # Senaryo 2: Bob ile işbirliği
        {
            "agent": "bob",
            "type": InteractionType.COOPERATED,
            "episode_type": EpisodeType.COOPERATION,
            "trust_impact": 0.10,
            "description": "Bob ile başarılı proje işbirliği",
        },

        # Senaryo 3: Diana kaynak paylaştı
        {
            "agent": "diana",
            "type": InteractionType.SHARED,
            "episode_type": EpisodeType.INTERACTION,
            "trust_impact": 0.12,
            "description": "Diana değerli bilgi paylaştı",
        },

        # Senaryo 4: Jack tehlikeden korudu
        {
            "agent": "jack",
            "type": InteractionType.PROTECTED,
            "episode_type": EpisodeType.SIGNIFICANT,
            "trust_impact": 0.20,
            "description": "Jack tehlikeli durumda koruma sağladı",
        },

        # Senaryo 5: Henry başarıyı kutladı
        {
            "agent": "henry",
            "type": InteractionType.CELEBRATED,
            "episode_type": EpisodeType.EMOTIONAL_EVENT,
            "trust_impact": 0.08,
            "description": "Henry başarıları birlikte kutladı",
        },

        # Senaryo 6: Grace teselli etti
        {
            "agent": "grace",
            "type": InteractionType.COMFORTED,
            "episode_type": EpisodeType.EMOTIONAL_EVENT,
            "trust_impact": 0.10,
            "description": "Grace zor zamanda teselli etti",
        },

        # ═══════════════════════════════════════════════════════════
        # NÖTR SENARYOLAR (Trust değişmez veya minimal)
        # ═══════════════════════════════════════════════════════════

        # Senaryo 7: Frank'i gözlemleme
        {
            "agent": "frank",
            "type": InteractionType.OBSERVED,
            "episode_type": EpisodeType.OBSERVATION,
            "trust_impact": 0.0,
            "description": "Frank'in davranışlarını gözlemleme",
        },

        # Senaryo 8: Bob ile sohbet
        {
            "agent": "bob",
            "type": InteractionType.CONVERSED,
            "episode_type": EpisodeType.INTERACTION,
            "trust_impact": 0.02,
            "description": "Bob ile günlük sohbet",
        },

        # Senaryo 9: Frank ile ticaret
        {
            "agent": "frank",
            "type": InteractionType.TRADED,
            "episode_type": EpisodeType.INTERACTION,
            "trust_impact": 0.03,
            "description": "Frank ile adil ticaret",
        },

        # ═══════════════════════════════════════════════════════════
        # NEGATİF SENARYOLAR (Trust düşüşü)
        # ═══════════════════════════════════════════════════════════

        # Senaryo 10: Ivy ile rekabet
        {
            "agent": "ivy",
            "type": InteractionType.COMPETED,
            "episode_type": EpisodeType.CONFLICT,
            "trust_impact": -0.05,
            "description": "Ivy ile kaynak için rekabet",
        },

        # Senaryo 11: Eve ile çatışma
        {
            "agent": "eve",
            "type": InteractionType.CONFLICTED,
            "episode_type": EpisodeType.CONFLICT,
            "trust_impact": -0.10,
            "description": "Eve ile fikir çatışması",
        },

        # Senaryo 12: Stranger zarar verdi
        {
            "agent": "stranger_1",
            "type": InteractionType.HARMED,
            "episode_type": EpisodeType.CONFLICT,
            "trust_impact": -0.20,
            "description": "Yabancı kasıtlı zarar verdi",
        },

        # Senaryo 13: Charlie ihanet etti (ÇOK NEGATİF)
        {
            "agent": "charlie",
            "type": InteractionType.BETRAYED,
            "episode_type": EpisodeType.SIGNIFICANT,
            "trust_impact": -0.40,
            "description": "Charlie güveni kötüye kullandı - İHANET!",
        },

        # Senaryo 14: Eve tehdit etti
        {
            "agent": "eve",
            "type": InteractionType.THREATENED,
            "episode_type": EpisodeType.CONFLICT,
            "trust_impact": -0.25,
            "description": "Eve açıkça tehdit etti",
        },

        # Senaryo 15: Enemy saldırdı
        {
            "agent": "enemy_1",
            "type": InteractionType.ATTACKED,
            "episode_type": EpisodeType.CONFLICT,
            "trust_impact": -0.35,
            "description": "Düşman fiziksel saldırı gerçekleştirdi",
        },

        # ═══════════════════════════════════════════════════════════
        # KARMA SENARYOLAR (Aynı agent ile farklı etkileşimler)
        # ═══════════════════════════════════════════════════════════

        # Senaryo 16: Alice tekrar yardım etti
        {
            "agent": "alice",
            "type": InteractionType.HELPED,
            "episode_type": EpisodeType.COOPERATION,
            "trust_impact": 0.10,
            "description": "Alice bir kez daha yardım etti",
        },

        # Senaryo 17: Bob koruma sağladı
        {
            "agent": "bob",
            "type": InteractionType.PROTECTED,
            "episode_type": EpisodeType.SIGNIFICANT,
            "trust_impact": 0.15,
            "description": "Bob beklenmedik bir şekilde koruma sağladı",
        },

        # Senaryo 18: Charlie özür diledi ama güven düşük
        {
            "agent": "charlie",
            "type": InteractionType.CONVERSED,
            "episode_type": EpisodeType.INTERACTION,
            "trust_impact": 0.05,
            "description": "Charlie özür diledi - küçük güven artışı",
        },

        # Senaryo 19: Diana işbirliği yaptı
        {
            "agent": "diana",
            "type": InteractionType.COOPERATED,
            "episode_type": EpisodeType.COOPERATION,
            "trust_impact": 0.12,
            "description": "Diana ile başarılı işbirliği",
        },

        # Senaryo 20: Jack hayat kurtardı (YÜKSEK GÜVEN)
        {
            "agent": "jack",
            "type": InteractionType.PROTECTED,
            "episode_type": EpisodeType.SIGNIFICANT,
            "trust_impact": 0.25,
            "description": "Jack hayat kurtardı - KAHRAMANLIK!",
        },
    ]

    # Her senaryoyu çalıştır
    for i, scenario in enumerate(scenarios, 1):
        agent = scenario["agent"]

        # Önceki trust değerini al
        record = memory.get_relationship(agent)
        old_trust = record.trust_score

        # 1. Episode oluştur ve kaydet
        episode = Episode(
            what=scenario["description"],
            who=[agent],
            when=datetime.now(),
            episode_type=scenario["episode_type"],
            outcome=scenario["description"],
            outcome_valence=scenario["trust_impact"],
        )
        episode_id = memory.store_episode(episode)

        # 2. Interaction oluştur ve kaydet
        interaction = Interaction(
            interaction_type=scenario["type"],
            trust_impact=scenario["trust_impact"],
            context=scenario["description"],
            outcome_valence=scenario["trust_impact"],
            timestamp=datetime.now(),
        )
        memory.record_interaction(agent, interaction)

        # 3. Cognitive Cycle çalıştır
        cycle.run()

        # Yeni trust değerini al
        record = memory.get_relationship(agent)
        new_trust = record.trust_score

        # Sonucu yazdır
        delta_str = f"+{scenario['trust_impact']}" if scenario['trust_impact'] >= 0 else f"{scenario['trust_impact']}"
        print(f"[{i:2d}] {agent:12s} | {scenario['type'].value:12s} | "
              f"trust: {old_trust:.2f} → {new_trust:.2f} ({delta_str})")
        print(f"     ├─ Episode: {episode_id[:8]}... ({scenario['episode_type'].value})")
        print(f"     └─ Cycle #{cycle.cycle_count} completed")
        print()

    # Özet
    print("\n" + "="*60)
    print("ÖZET")
    print("="*60)

    # Cycle özeti
    print(f"\nTotal Cycles: {cycle.cycle_count}")
    print(f"Total Episodes: {len(memory.get_recent_episodes(100))}")

    # Trust seviyeleri
    print("\nTrust Seviyeleri:")
    print("-" * 50)

    all_relationships = memory.get_all_relationships()
    all_relationships.sort(key=lambda r: r.trust_score, reverse=True)

    for record in all_relationships:
        bar_len = int(record.trust_score * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        status = ""
        if record.trust_score >= 0.7:
            status = "✓ GÜVENİLİR"
        elif record.trust_score <= 0.3:
            status = "✗ TEHLİKELİ"

        print(f"{record.agent_id:12s} [{bar}] {record.trust_score:.2f} {status}")

    print("\n" + "="*60)
    print("Demo tamamlandı!")
    print("Dashboard'u kontrol edin: streamlit run interface/dashboard/app.py")
    print("="*60 + "\n")

    return all_relationships


def verify_db(memory):
    """DB'deki değerleri doğrula."""
    print("\n" + "="*60)
    print("DB DOĞRULAMA")
    print("="*60)

    if not memory._db_available:
        print("⚠ PostgreSQL bağlantısı yok!")
        return

    try:
        from core.memory.persistence.models import RelationshipModel
        relationships = memory._repository.session.query(RelationshipModel).all()

        print(f"\nDB'de {len(relationships)} relationship kaydı bulundu:\n")

        for rel in sorted(relationships, key=lambda r: r.trust_score, reverse=True):
            print(f"  {rel.agent_id:12s} -> trust_score: {rel.trust_score:.2f}, "
                  f"interactions: {rel.total_interactions}")

        print("\n✓ DB değerleri yukarıdaki gibi.")

    except Exception as e:
        print(f"✗ DB doğrulama hatası: {e}")


def main():
    """Ana fonksiyon."""
    print("\nPostgreSQL'e bağlanılıyor...")

    # MonitoringPersistence başlat
    monitoring = MonitoringPersistence(database_url=DB_URL)
    monitoring.start()
    print("✓ MonitoringPersistence başlatıldı")

    try:
        memory = create_memory()

        if memory._db_available:
            print("✓ PostgreSQL bağlantısı başarılı!")
        else:
            print("⚠ PostgreSQL bağlantısı yok, in-memory mod kullanılacak.")

        # CognitiveCycle oluştur
        cycle = create_cycle()
        print("✓ CognitiveCycle oluşturuldu (enable_monitoring=True)")

        # Senaryoları çalıştır
        run_scenarios(memory, cycle)

        # DB doğrulama
        verify_db(memory)

    except Exception as e:
        print(f"\n✗ Hata: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # MonitoringPersistence durdur
        monitoring.stop()
        print("✓ MonitoringPersistence durduruldu")

    return 0


if __name__ == "__main__":
    sys.exit(main())
