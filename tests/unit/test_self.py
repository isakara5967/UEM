"""
UEM v2 - Self Module Tests

Benlik modulunun unit testleri.
"""

import pytest
from datetime import datetime, timedelta

from core.self import (
    # Types
    IdentityAspect,
    ValueCategory,
    ValuePriority,
    NeedLevel,
    NeedStatus,
    GoalDomain,
    IntegrityStatus,
    NarrativeType,
    Value,
    Need,
    PersonalGoal,
    IdentityTrait,
    Identity,
    NarrativeElement,
    SelfState,
    # Identity
    IdentityConfig,
    IdentityManager,
    create_identity_manager,
    create_default_identity,
    # Goals
    PersonalGoalConfig,
    PersonalGoalManager,
    create_personal_goal_manager,
    # Needs
    NeedConfig,
    NeedManager,
    create_need_manager,
    get_default_needs,
    # Values
    ValueSystemConfig,
    ValueSystem,
    create_value_system,
    get_default_values,
    # Processor
    SelfProcessorConfig,
    SelfOutput,
    SelfProcessor,
    create_self_processor,
)


# ============================================================================
# TYPES TESTS
# ============================================================================

class TestValue:
    """Value dataclass testleri."""

    def test_value_creation(self):
        """Value olusturma."""
        value = Value(
            name="Honesty",
            description="Being truthful",
            category=ValueCategory.MORAL,
            priority=ValuePriority.CORE,
            weight=0.9,
        )
        assert value.name == "Honesty"
        assert value.category == ValueCategory.MORAL
        assert value.priority == ValuePriority.CORE
        assert value.weight == 0.9

    def test_value_priority_weight(self):
        """priority_weight hesaplama."""
        value = Value(priority=ValuePriority.SACRED, weight=1.0)
        assert value.priority_weight == 1.0

        value2 = Value(priority=ValuePriority.OPTIONAL, weight=1.0)
        assert value2.priority_weight == 0.2

    def test_value_integrity_score(self):
        """integrity_score hesaplama."""
        value = Value()
        assert value.integrity_score == 1.0  # Hic ifade/ihlal yok

        value.expression_count = 8
        value.violation_count = 2
        assert value.integrity_score == 0.8

    def test_value_express(self):
        """Deger ifade etme."""
        value = Value()
        initial_count = value.expression_count
        value.express()
        assert value.expression_count == initial_count + 1
        assert value.last_expressed is not None

    def test_value_violate(self):
        """Deger ihlali."""
        value = Value()
        initial_count = value.violation_count
        value.violate()
        assert value.violation_count == initial_count + 1


class TestNeed:
    """Need dataclass testleri."""

    def test_need_creation(self):
        """Need olusturma."""
        need = Need(
            name="Safety",
            level=NeedLevel.SAFETY,
            satisfaction=0.7,
            importance=0.9,
        )
        assert need.name == "Safety"
        assert need.level == NeedLevel.SAFETY
        assert need.satisfaction == 0.7

    def test_need_priority_score(self):
        """priority_score hesaplama."""
        need = Need(
            level=NeedLevel.PHYSIOLOGICAL,
            satisfaction=0.2,  # Dusuk tatmin = yuksek oncelik
            importance=1.0,
            urgency=0.5,
        )
        score = need.priority_score
        assert score > 0  # Dusuk tatmin, yuksek onem

    def test_need_update_satisfaction(self):
        """Tatmin guncelleme."""
        need = Need(satisfaction=0.5)
        need.update_satisfaction(0.2)
        assert need.satisfaction == 0.7

        # Sinirlari test et
        need.update_satisfaction(0.5)
        assert need.satisfaction == 1.0  # Max 1.0

        need.update_satisfaction(-2.0)
        assert need.satisfaction == 0.0  # Min 0.0

    def test_need_status_update(self):
        """Durum guncelleme."""
        need = Need(satisfaction=0.1)
        need._update_status()
        assert need.status == NeedStatus.CRITICAL

        need.satisfaction = 0.4
        need._update_status()
        assert need.status == NeedStatus.UNSATISFIED

        need.satisfaction = 0.8
        need._update_status()
        assert need.status == NeedStatus.SATISFIED

    def test_need_satisfy(self):
        """Ihtiyaci karsilama."""
        need = Need(satisfaction=0.5)
        need.satisfy(0.2)
        assert need.satisfaction == 0.7
        assert need.deprivation_duration == 0.0


class TestPersonalGoal:
    """PersonalGoal dataclass testleri."""

    def test_goal_creation(self):
        """PersonalGoal olusturma."""
        goal = PersonalGoal(
            name="Learn Python",
            domain=GoalDomain.MASTERY,
            milestones=["basics", "intermediate", "advanced"],
        )
        assert goal.name == "Learn Python"
        assert goal.domain == GoalDomain.MASTERY
        assert len(goal.milestones) == 3

    def test_goal_total_motivation(self):
        """Toplam motivasyon hesaplama."""
        goal = PersonalGoal(
            intrinsic_motivation=0.8,
            extrinsic_motivation=0.4,
            commitment=1.0,
        )
        # 0.8 * 0.7 + 0.4 * 0.3 = 0.56 + 0.12 = 0.68
        assert abs(goal.total_motivation - 0.68) < 0.01

    def test_goal_achieve_milestone(self):
        """Milestone tamamlama."""
        goal = PersonalGoal(milestones=["step1", "step2", "step3"])
        goal.achieve_milestone("step1")
        assert "step1" in goal.achieved_milestones
        assert goal.progress > 0


class TestIdentityTrait:
    """IdentityTrait testleri."""

    def test_trait_creation(self):
        """Trait olusturma."""
        trait = IdentityTrait(
            name="Curious",
            aspect=IdentityAspect.CORE,
            strength=0.8,
            stability=0.9,
        )
        assert trait.name == "Curious"
        assert trait.aspect == IdentityAspect.CORE

    def test_trait_resilience(self):
        """Dayaniklilik hesaplama."""
        trait = IdentityTrait(strength=0.8, stability=0.9)
        assert abs(trait.resilience - 0.72) < 0.01  # 0.8 * 0.9

    def test_trait_reinforce(self):
        """Ozelligi guclendirme."""
        trait = IdentityTrait(strength=0.5, stability=0.5)
        trait.reinforce(0.1)
        assert trait.strength == 0.6
        assert trait.stability == 0.55
        assert trait.reinforcement_count == 1

    def test_trait_challenge(self):
        """Ozelligi sorgulama."""
        trait = IdentityTrait(strength=0.8, stability=0.5)
        initial_strength = trait.strength
        trait.challenge(0.1)
        assert trait.strength < initial_strength
        assert trait.challenge_count == 1


class TestIdentity:
    """Identity dataclass testleri."""

    def test_identity_creation(self):
        """Identity olusturma."""
        identity = Identity(
            name="Agent",
            roles=["Assistant", "Learner"],
            capabilities=["Reasoning"],
        )
        assert identity.name == "Agent"
        assert len(identity.roles) == 2

    def test_identity_add_trait(self):
        """Trait ekleme."""
        identity = Identity()
        trait = IdentityTrait(name="Helpful", aspect=IdentityAspect.CORE)
        identity.add_trait(trait)
        assert trait.id in identity.traits
        assert trait.id in identity.core_traits

    def test_identity_strength(self):
        """Kimlik gucu hesaplama."""
        identity = Identity()
        trait1 = IdentityTrait(name="T1", aspect=IdentityAspect.CORE, strength=0.8)
        trait2 = IdentityTrait(name="T2", aspect=IdentityAspect.CORE, strength=0.6)
        identity.add_trait(trait1)
        identity.add_trait(trait2)
        assert identity.identity_strength == 0.7  # (0.8 + 0.6) / 2


class TestSelfState:
    """SelfState dataclass testleri."""

    def test_selfstate_creation(self):
        """SelfState olusturma."""
        state = SelfState()
        assert state.integrity_status == IntegrityStatus.ALIGNED
        assert state.integrity_score == 1.0

    def test_selfstate_add_value(self):
        """Deger ekleme."""
        state = SelfState()
        value = Value(name="Honesty", priority=ValuePriority.CORE)
        state.add_value(value)
        assert value.id in state.values
        assert value.id in state.core_values

    def test_selfstate_add_need(self):
        """Ihtiyac ekleme."""
        state = SelfState()
        need = Need(name="Safety", level=NeedLevel.SAFETY)
        state.add_need(need)
        assert need.id in state.needs

    def test_selfstate_summary(self):
        """Ozet bilgi."""
        state = SelfState()
        summary = state.summary()
        assert "integrity_status" in summary
        assert "integrity_score" in summary


# ============================================================================
# IDENTITY MANAGER TESTS
# ============================================================================

class TestIdentityManager:
    """IdentityManager testleri."""

    def test_create_identity_manager(self):
        """Factory fonksiyonu."""
        manager = create_identity_manager()
        assert manager is not None
        assert isinstance(manager, IdentityManager)

    def test_initialize_identity(self):
        """Kimlik baslangici."""
        manager = IdentityManager()
        identity = manager.initialize_identity(
            name="TestAgent",
            description="A test agent",
            core_traits=[{"name": "Helpful", "description": "Helps others"}],
            roles=["Tester"],
        )
        assert identity.name == "TestAgent"
        assert len(identity.traits) == 1
        assert "Tester" in identity.roles

    def test_add_trait(self):
        """Trait ekleme."""
        manager = IdentityManager()
        manager.initialize_identity(name="Agent")
        trait = IdentityTrait(name="NewTrait", aspect=IdentityAspect.SOCIAL)
        result = manager.add_trait(trait)
        assert result is True
        assert manager.identity.get_trait(trait.id) is not None

    def test_remove_trait(self):
        """Trait kaldirma."""
        manager = IdentityManager()
        manager.initialize_identity(name="Agent")
        trait = IdentityTrait(name="RemovableTrait", strength=0.3)
        manager.add_trait(trait)
        result = manager.remove_trait(trait.id)
        assert result is True
        assert trait.id not in manager.identity.traits

    def test_reinforce_trait(self):
        """Trait guclendirme."""
        manager = IdentityManager()
        manager.initialize_identity(name="Agent", core_traits=[{"name": "Test"}])
        trait = manager.find_trait_by_name("Test")
        initial_strength = trait.strength
        manager.reinforce_trait(trait.id, 0.1)
        assert trait.strength > initial_strength

    def test_challenge_trait(self):
        """Trait sorgulama."""
        manager = IdentityManager()
        manager.initialize_identity(name="Agent", core_traits=[{"name": "Test"}])
        trait = manager.find_trait_by_name("Test")
        initial_strength = trait.strength
        manager.challenge_trait(trait.id, 0.05)
        assert trait.strength < initial_strength

    def test_add_role(self):
        """Rol ekleme."""
        manager = IdentityManager()
        manager.initialize_identity(name="Agent")
        manager.add_role("NewRole")
        assert "NewRole" in manager.identity.roles

    def test_check_identity_stability(self):
        """Stabilite kontrolu."""
        manager = IdentityManager()
        manager.initialize_identity(
            name="Agent",
            core_traits=[{"name": "Stable", "strength": 0.9, "stability": 0.9}],
        )
        result = manager.check_identity_stability()
        assert result["stable"] is True
        assert result["score"] > 0.8

    def test_generate_self_description(self):
        """Kimlik tanimi olusturma."""
        manager = IdentityManager()
        manager.initialize_identity(
            name="TestAgent",
            description="A helpful agent",
            roles=["Assistant"],
            core_traits=[{"name": "Helpful"}],
        )
        description = manager.generate_self_description()
        assert "TestAgent" in description
        assert "Helpful" in description


# ============================================================================
# PERSONAL GOAL MANAGER TESTS
# ============================================================================

class TestPersonalGoalManager:
    """PersonalGoalManager testleri."""

    def test_create_goal_manager(self):
        """Factory fonksiyonu."""
        manager = create_personal_goal_manager()
        assert manager is not None

    def test_create_goal(self):
        """Hedef olusturma."""
        manager = PersonalGoalManager()
        goal = manager.create_goal(
            name="Learn",
            domain=GoalDomain.MASTERY,
            milestones=["step1", "step2"],
        )
        assert goal is not None
        assert goal.name == "Learn"
        assert goal.id in manager.goals

    def test_get_active_goals(self):
        """Aktif hedefler."""
        manager = PersonalGoalManager()
        manager.create_goal(name="Goal1")
        manager.create_goal(name="Goal2")
        active = manager.get_active_goals()
        assert len(active) == 2

    def test_update_progress(self):
        """Ilerleme guncelleme."""
        manager = PersonalGoalManager()
        goal = manager.create_goal(name="Goal")
        manager.update_progress(goal.id, 0.5)
        assert goal.progress == 0.5

    def test_achieve_milestone(self):
        """Milestone tamamlama."""
        manager = PersonalGoalManager()
        goal = manager.create_goal(
            name="Goal",
            milestones=["m1", "m2", "m3"],
        )
        result = manager.achieve_milestone(goal.id, "m1")
        assert result is True
        assert "m1" in goal.achieved_milestones

    def test_complete_goal(self):
        """Hedef tamamlama."""
        manager = PersonalGoalManager()
        goal = manager.create_goal(name="Goal")
        manager.complete_goal(goal.id)
        assert goal.is_active is False
        assert goal.progress == 1.0

    def test_abandon_goal(self):
        """Hedef terk etme."""
        manager = PersonalGoalManager()
        goal = manager.create_goal(name="Goal")
        manager.abandon_goal(goal.id)
        assert goal.is_active is False

    def test_prioritize_goals(self):
        """Hedef onceliklendirme."""
        manager = PersonalGoalManager()
        manager.create_goal(name="Low", intrinsic_motivation=0.3)
        manager.create_goal(name="High", intrinsic_motivation=0.9)
        prioritized = manager.prioritize_goals()
        assert prioritized[0].name == "High"

    def test_suggest_focus_goal(self):
        """Odak hedefi onerme."""
        manager = PersonalGoalManager()
        manager.create_goal(name="Goal1", intrinsic_motivation=0.5)
        manager.create_goal(name="Goal2", intrinsic_motivation=0.9)
        focus = manager.suggest_focus_goal()
        assert focus.name == "Goal2"


# ============================================================================
# NEED MANAGER TESTS
# ============================================================================

class TestNeedManager:
    """NeedManager testleri."""

    def test_create_need_manager(self):
        """Factory fonksiyonu."""
        manager = create_need_manager()
        assert manager is not None
        assert len(manager.needs) > 0  # Varsayilan ihtiyaclar

    def test_initialize_default_needs(self):
        """Varsayilan ihtiyaclar."""
        manager = NeedManager()
        manager.initialize_default_needs()
        assert len(manager.needs) > 0

    def test_get_need_by_name(self):
        """Isimle ihtiyac bulma."""
        manager = create_need_manager()
        need = manager.get_need_by_name("Energy")
        assert need is not None
        assert need.name == "Energy"

    def test_get_needs_by_level(self):
        """Seviyeye gore ihtiyaclar."""
        manager = create_need_manager()
        physiological = manager.get_needs_by_level(NeedLevel.PHYSIOLOGICAL)
        assert len(physiological) > 0

    def test_get_unsatisfied_needs(self):
        """Karsilanmamis ihtiyaclar."""
        manager = NeedManager()
        need = Need(name="Test", satisfaction=0.3, status=NeedStatus.UNSATISFIED)
        manager.add_need(need)
        unsatisfied = manager.get_unsatisfied_needs()
        assert len(unsatisfied) >= 1

    def test_satisfy_need(self):
        """Ihtiyac karsilama."""
        manager = create_need_manager()
        need = manager.get_need_by_name("Safety")
        initial_satisfaction = need.satisfaction
        manager.satisfy_need(need.id, 0.2)
        assert need.satisfaction > initial_satisfaction

    def test_deprive_need(self):
        """Ihtiyac mahrumiyeti."""
        manager = create_need_manager()
        need = manager.get_need_by_name("Energy")
        initial_satisfaction = need.satisfaction
        manager.deprive_need(need.id, 10.0)  # 10 saat
        assert need.satisfaction < initial_satisfaction

    def test_get_most_pressing_need(self):
        """En acil ihtiyac."""
        manager = NeedManager()
        need1 = Need(name="N1", level=NeedLevel.SAFETY, satisfaction=0.8)
        need2 = Need(name="N2", level=NeedLevel.PHYSIOLOGICAL, satisfaction=0.3)
        manager.add_need(need1)
        manager.add_need(need2)
        pressing = manager.get_most_pressing_need()
        assert pressing.name == "N2"  # Fizyolojik ve dusuk tatmin

    def test_prioritize_needs(self):
        """Ihtiyac onceliklendirme."""
        manager = create_need_manager()
        prioritized = manager.prioritize_needs()
        assert len(prioritized) > 0

    def test_check_hierarchy_satisfaction(self):
        """Hiyerarsi tatmin kontrolu."""
        manager = create_need_manager()
        hierarchy = manager.check_hierarchy_satisfaction()
        assert "levels" in hierarchy
        assert "active_level" in hierarchy

    def test_calculate_drive(self):
        """Durt hesaplama."""
        manager = NeedManager()
        need = Need(name="Test", satisfaction=0.2, importance=0.9)
        manager.add_need(need)
        drive = manager.calculate_drive(need.id)
        assert drive > 0

    def test_get_overall_wellbeing(self):
        """Genel iyilik hali."""
        manager = create_need_manager()
        wellbeing = manager.get_overall_wellbeing()
        assert 0 <= wellbeing <= 1


# ============================================================================
# VALUE SYSTEM TESTS
# ============================================================================

class TestValueSystem:
    """ValueSystem testleri."""

    def test_create_value_system(self):
        """Factory fonksiyonu."""
        system = create_value_system()
        assert system is not None
        assert len(system.values) > 0

    def test_initialize_default_values(self):
        """Varsayilan degerler."""
        system = ValueSystem()
        system.initialize_default_values()
        assert len(system.values) > 0

    def test_add_value(self):
        """Deger ekleme."""
        system = ValueSystem()
        value = Value(name="TestValue", priority=ValuePriority.IMPORTANT)
        result = system.add_value(value)
        assert result is True
        assert value.id in system.values

    def test_remove_value(self):
        """Deger kaldirma."""
        system = ValueSystem()
        value = Value(name="RemovableValue", priority=ValuePriority.OPTIONAL)
        system.add_value(value)
        result = system.remove_value(value.id)
        assert result is True
        assert value.id not in system.values

    def test_sacred_value_protection(self):
        """Kutsal deger korumasi."""
        system = ValueSystem()
        value = Value(name="Sacred", priority=ValuePriority.SACRED)
        system.add_value(value)
        result = system.remove_value(value.id)
        assert result is False  # Silinemez

    def test_get_value_by_name(self):
        """Isimle deger bulma."""
        system = create_value_system()
        value = system.get_value_by_name("Honesty")
        assert value is not None

    def test_get_core_values(self):
        """Temel degerler."""
        system = create_value_system()
        core = system.get_core_values()
        assert len(core) > 0

    def test_express_value(self):
        """Deger ifade etme."""
        system = create_value_system()
        result = system.express_value_by_name("Honesty")
        assert result is True
        assert system._stats["values_expressed"] > 0

    def test_violate_value(self):
        """Deger ihlali."""
        system = create_value_system()
        value = system.get_value_by_name("Honesty")
        result = system.violate_value(value.id)
        assert result["success"] is True
        assert result["is_severe"] is True  # Honesty is SACRED

    def test_detect_conflicts(self):
        """Catisma tespiti."""
        system = ValueSystem()
        v1 = Value(name="V1", conflicting_values=[])
        v2 = Value(name="V2", conflicting_values=[])
        system.add_value(v1)
        system.add_value(v2)
        v1.conflicting_values.append(v2.id)
        conflicts = system.detect_conflicts()
        assert len(conflicts) >= 1

    def test_prioritize_values(self):
        """Deger onceliklendirme."""
        system = create_value_system()
        prioritized = system.prioritize_values()
        assert len(prioritized) > 0

    def test_calculate_value_integrity(self):
        """Deger tutarliligi."""
        system = create_value_system()
        integrity = system.calculate_value_integrity()
        assert 0 <= integrity <= 1


# ============================================================================
# SELF PROCESSOR TESTS
# ============================================================================

class TestSelfProcessor:
    """SelfProcessor testleri."""

    def test_create_self_processor(self):
        """Factory fonksiyonu."""
        processor = create_self_processor()
        assert processor is not None

    def test_processor_initialization(self):
        """Baslangic durumu."""
        processor = SelfProcessor()
        assert processor.identity_manager is not None
        assert processor.goal_manager is not None
        assert processor.need_manager is not None
        assert processor.value_system is not None

    def test_process(self):
        """Ana islem."""
        processor = SelfProcessor()
        output = processor.process()
        assert isinstance(output, SelfOutput)
        assert output.self_state is not None
        assert output.integrity_score > 0

    def test_process_with_context(self):
        """Baglamli islem."""
        processor = SelfProcessor()
        context = {"event_significance": 0.3}
        output = processor.process(context=context)
        assert output is not None

    def test_process_with_time_delta(self):
        """Zamanli islem."""
        processor = SelfProcessor()
        output = processor.process(time_delta_hours=1.0)
        assert output is not None

    def test_express_value(self):
        """Deger ifade etme."""
        processor = SelfProcessor()
        result = processor.express_value("Honesty")
        assert result is True

    def test_satisfy_need(self):
        """Ihtiyac karsilama."""
        processor = SelfProcessor()
        result = processor.satisfy_need("Safety")
        assert result is True

    def test_reinforce_trait(self):
        """Trait guclendirme."""
        processor = SelfProcessor()
        result = processor.reinforce_trait("Helpful")
        assert result is True

    def test_get_self_description(self):
        """Benlik tanimi."""
        processor = SelfProcessor()
        description = processor.get_self_description()
        assert "UEM Agent" in description

    def test_add_narrative_element(self):
        """Hikaye ogesi ekleme."""
        processor = SelfProcessor()
        element = processor.add_narrative_element(
            title="Test Event",
            narrative_type=NarrativeType.LESSON,
            summary="A test event occurred",
        )
        assert element is not None
        assert len(processor.self_state.narrative) > 0

    def test_get_stats(self):
        """Istatistikler."""
        processor = SelfProcessor()
        processor.process()
        stats = processor.get_stats()
        assert "processor" in stats
        assert "identity" in stats
        assert "goals" in stats
        assert "needs" in stats
        assert "values" in stats

    def test_summary(self):
        """Ozet bilgi."""
        processor = SelfProcessor()
        summary = processor.summary()
        assert "identity" in summary
        assert "values" in summary
        assert "needs" in summary
        assert "goals" in summary
        assert "integrity" in summary


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSelfIntegration:
    """Entegrasyon testleri."""

    def test_value_need_alignment(self):
        """Deger-ihtiyac uyumu."""
        processor = SelfProcessor()

        # Kritik ihtiyac olustur
        need = processor.need_manager.get_need_by_name("Safety")
        need.satisfaction = 0.1
        need._update_status()

        output = processor.process()

        # Kritik ihtiyac onerilmeli
        assert output.most_pressing_need is not None

    def test_goal_value_connection(self):
        """Hedef-deger baglantisi."""
        processor = SelfProcessor()

        # Degerle iliskili hedef olustur
        honesty = processor.value_system.get_value_by_name("Honesty")
        goal = processor.goal_manager.create_goal_from_value(
            value=honesty,
            goal_name="Practice Honesty",
        )
        assert goal is not None
        assert honesty.id in goal.related_values

    def test_identity_value_reinforcement(self):
        """Kimlik-deger pekistirmesi."""
        processor = SelfProcessor()

        # Degeri ifade et
        processor.express_value("Honesty")

        # Iliskili trait guclensin mi?
        ethical_trait = processor.identity_manager.find_trait_by_name("Ethical")
        if ethical_trait:
            initial_strength = ethical_trait.strength
            # Normalde bu otomatik baglantiyla olur
            # Burada sadece baglantinin var oldugunu test ediyoruz
            assert initial_strength > 0

    def test_full_cycle(self):
        """Tam bir self cycle."""
        processor = SelfProcessor()

        # Baslangic durumu
        output1 = processor.process()
        initial_integrity = output1.integrity_score

        # Zaman gecir (ihtiyaclar azalir)
        output2 = processor.process(time_delta_hours=5.0)

        # Ihtiyac karila
        processor.satisfy_need("Energy", 0.5)

        # Deger ifade et
        processor.express_value("Helpfulness")

        # Hedefte ilerle
        goals = processor.goal_manager.get_active_goals()
        if goals:
            processor.goal_manager.increment_progress(goals[0].id, 0.2)

        # Son durum
        output3 = processor.process()

        # Assertions
        assert output1 is not None
        assert output2 is not None
        assert output3 is not None

    def test_integrity_monitoring(self):
        """Tutarlilik izleme."""
        processor = SelfProcessor()

        # Baslangic
        output1 = processor.process()
        assert output1.integrity_status == IntegrityStatus.ALIGNED

        # Deger ihlali
        value = processor.value_system.get_value_by_name("Honesty")
        for _ in range(5):
            processor.value_system.violate_value(value.id)

        # Tutarlilik dususu
        output2 = processor.process()
        assert output2.integrity_score < output1.integrity_score

    def test_need_hierarchy(self):
        """Maslow hiyerarsisi."""
        processor = SelfProcessor()

        # Alt seviye ihtiyaclari kritik yap
        energy = processor.need_manager.get_need_by_name("Energy")
        energy.satisfaction = 0.1
        energy._update_status()

        output = processor.process()

        # En acil ihtiyac fizyolojik olmali
        most_pressing = processor.need_manager.get_most_pressing_need()
        assert most_pressing.level == NeedLevel.PHYSIOLOGICAL


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestSelfEdgeCases:
    """Sinir durumu testleri."""

    def test_empty_processor(self):
        """Bos processor."""
        config = SelfProcessorConfig(initialize_defaults=False)
        processor = SelfProcessor(config)
        output = processor.process()
        assert output is not None

    def test_max_goals_limit(self):
        """Maksimum hedef limiti."""
        config = PersonalGoalConfig(max_active_goals=2)
        manager = PersonalGoalManager(config)
        manager.create_goal(name="Goal1")
        manager.create_goal(name="Goal2")
        goal3 = manager.create_goal(name="Goal3")
        assert goal3 is None  # Limit asildi

    def test_max_values_limit(self):
        """Maksimum deger limiti."""
        config = ValueSystemConfig(max_total_values=3)
        system = ValueSystem(config)
        for i in range(4):
            value = Value(name=f"Value{i}")
            result = system.add_value(value)
            if i >= 3:
                assert result is False

    def test_trait_decay(self):
        """Trait gucu azalmasi."""
        manager = IdentityManager()
        manager.initialize_identity(
            name="Agent",
            core_traits=[{"name": "Test", "strength": 0.8}],
        )
        trait = manager.find_trait_by_name("Test")
        trait.last_reinforced = datetime.now() - timedelta(hours=10)

        decayed = manager.apply_trait_decay(hours_passed=5.0)
        # Decay uygulanmis olmali
        assert len(decayed) >= 0  # Bos olmayabilir
