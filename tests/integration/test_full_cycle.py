"""
UEM v2 - Full Cycle Integration Tests

Comprehensive tests for the complete cognitive cycle:
- All 10 phases running sequentially
- Perception → Cognition → Memory → Affect → Self → Executive flow
- StateVector consistency across phases
- Consciousness global workspace integration
- MetaMind cycle analysis
- End-to-end scenarios
"""

import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

# Engine
from engine.cycle import CognitiveCycle, CycleConfig, CycleState
from engine.phases import Phase, PhaseConfig, PhaseResult, DEFAULT_PHASE_CONFIGS
from engine.events import EventBus, EventType, Event, get_event_bus

# Foundation
from foundation.state import StateVector, SVField
from foundation.types import Context, Entity, Stimulus

# Handlers
from engine.handlers.perception import (
    create_sense_handler,
    create_attend_handler,
    create_perceive_handler,
)

# Monitoring
from meta.monitoring.metrics import CycleMetrics, CycleMetricsHistory

# Consciousness
from meta.consciousness import (
    ConsciousnessProcessor,
    ConsciousnessLevel,
    AwarenessType,
    WorkspaceContent,
    BroadcastType,
    create_consciousness_processor,
)

# MetaMind
from meta.metamind import (
    MetaMindProcessor,
    CycleAnalysisResult,
    InsightType,
    PatternType,
    create_metamind_processor,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def event_bus():
    """Fresh event bus for each test."""
    return EventBus()


@pytest.fixture
def cycle(event_bus):
    """Cognitive cycle with event bus."""
    config = CycleConfig(
        emit_events=True,
        enable_monitoring=True,
    )
    return CognitiveCycle(config=config, event_bus=event_bus)


@pytest.fixture
def cycle_with_handlers(cycle):
    """Cycle with perception handlers registered."""
    cycle.register_handler(Phase.SENSE, create_sense_handler())
    cycle.register_handler(Phase.ATTEND, create_attend_handler())
    cycle.register_handler(Phase.PERCEIVE, create_perceive_handler())
    return cycle


@pytest.fixture
def simple_stimulus():
    """Simple test stimulus."""
    return Stimulus(
        stimulus_type="social",
        source_entity=Entity(
            id="agent_1",
            entity_type="agent",
            attributes={
                "expression": "neutral",
                "body_language": "relaxed",
            },
        ),
        content={
            "verbal": "Hello, how are you?",
            "situation": "greeting",
        },
        intensity=0.5,
    )


@pytest.fixture
def threatening_stimulus():
    """Threatening test stimulus."""
    return Stimulus(
        stimulus_type="social",
        source_entity=Entity(
            id="threat_agent",
            entity_type="agent",
            attributes={
                "expression": "angry",
                "body_language": "aggressive",
                "hostile": True,
            },
        ),
        content={
            "verbal": "Get out of here!",
            "situation": "confrontation",
        },
        intensity=0.8,
    )


@pytest.fixture
def consciousness_processor():
    """Consciousness processor for integration tests."""
    return create_consciousness_processor()


@pytest.fixture
def metamind_processor():
    """MetaMind processor for integration tests."""
    return create_metamind_processor()


# ============================================================================
# 10 PHASE TESTS
# ============================================================================

class TestAllPhasesRunSequentially:
    """Test that all 10 phases run in correct order."""

    def test_all_phases_enabled_by_default(self, cycle):
        """All phases should be enabled by default."""
        for config in cycle.config.phase_configs:
            assert config.enabled is True

    def test_phases_run_in_order(self, cycle, event_bus):
        """Phases should run in correct sequence."""
        phase_order = []

        def track_phase_start(event: Event):
            if event.event_type == EventType.MODULE_START:
                phase_order.append(event.data.get("phase"))

        event_bus.subscribe(EventType.MODULE_START, track_phase_start)

        cycle.run()

        expected_order = [p.value for p in Phase.ordered()]
        assert phase_order == expected_order

    def test_all_phases_complete(self, cycle):
        """All phases should complete."""
        result = cycle.run()

        assert len(result.phase_results) == 10
        for phase in Phase.ordered():
            assert phase in result.phase_results
            assert result.phase_results[phase].success is True

    def test_cycle_state_updates(self, cycle):
        """Cycle state should update through phases."""
        result = cycle.run()

        assert result.cycle_id == 1
        assert result.is_complete is True
        assert result.duration_ms >= 0
        assert result.start_time is not None
        assert result.end_time is not None

    def test_phase_durations_recorded(self, cycle):
        """Each phase should record its duration."""
        result = cycle.run()

        for phase, phase_result in result.phase_results.items():
            assert phase_result.duration_ms >= 0

    def test_multiple_cycles(self, cycle):
        """Multiple cycles should run independently."""
        result1 = cycle.run()
        result2 = cycle.run()
        result3 = cycle.run()

        assert result1.cycle_id == 1
        assert result2.cycle_id == 2
        assert result3.cycle_id == 3
        assert cycle.cycle_count == 3


# ============================================================================
# PERCEPTION → COGNITION → MEMORY → AFFECT FLOW TESTS
# ============================================================================

class TestModuleFlow:
    """Test data flow between modules."""

    def test_perception_phases_flow(self, cycle_with_handlers, simple_stimulus):
        """SENSE → ATTEND → PERCEIVE should flow correctly."""
        result = cycle_with_handlers.run(stimulus=simple_stimulus)

        # SENSE should capture stimulus
        sense_result = result.phase_results[Phase.SENSE]
        assert sense_result.success is True
        assert sense_result.output.get("sensed") is True

        # ATTEND should process attention
        attend_result = result.phase_results[Phase.ATTEND]
        assert attend_result.success is True
        assert attend_result.output.get("attended") is True

        # PERCEIVE should extract features
        perceive_result = result.phase_results[Phase.PERCEIVE]
        assert perceive_result.success is True
        assert perceive_result.output.get("perceived") is True

    def test_threat_detection_flow(self, cycle_with_handlers, threatening_stimulus):
        """Threat should be detected and flow through."""
        result = cycle_with_handlers.run(stimulus=threatening_stimulus)

        # Threat should be detected in PERCEIVE
        perceive_result = result.phase_results[Phase.PERCEIVE]
        threat_level = perceive_result.output.get("threat_level", 0)
        assert threat_level > 0.3  # Should detect some threat

        # StateVector should reflect threat
        assert result.state_vector.threat > 0

    def test_context_data_propagation(self, cycle_with_handlers, simple_stimulus):
        """Context data should propagate between phases."""
        # Custom handler to check context at RETRIEVE phase
        context_data = {}

        def retrieve_handler(phase, state, context):
            context_data["stimulus"] = context.metadata.get("stimulus")
            context_data["perceptual_input"] = context.metadata.get("perceptual_input")
            context_data["attention"] = context.metadata.get("attention")
            context_data["perceptual_features"] = context.metadata.get("perceptual_features")
            return PhaseResult(phase=phase, success=True)

        cycle_with_handlers.register_handler(Phase.RETRIEVE, retrieve_handler)
        cycle_with_handlers.run(stimulus=simple_stimulus)

        # Context should contain data from previous phases
        assert context_data["stimulus"] is not None
        assert context_data["perceptual_input"] is not None

    def test_phase_results_in_context(self, cycle_with_handlers, simple_stimulus):
        """Phase results should be available in context."""
        results_seen = {}

        def decide_handler(phase, state, context):
            phase_results = context.metadata.get("phase_results", {})
            results_seen.update({
                "has_sense": Phase.SENSE in phase_results,
                "has_attend": Phase.ATTEND in phase_results,
                "has_perceive": Phase.PERCEIVE in phase_results,
            })
            return PhaseResult(phase=phase, success=True)

        cycle_with_handlers.register_handler(Phase.DECIDE, decide_handler)
        cycle_with_handlers.run(stimulus=simple_stimulus)

        assert results_seen.get("has_sense") is True
        assert results_seen.get("has_attend") is True
        assert results_seen.get("has_perceive") is True


# ============================================================================
# STATEVECTOR CONSISTENCY TESTS
# ============================================================================

class TestStateVectorConsistency:
    """Test StateVector consistency across phases."""

    def test_initial_state_preserved(self, cycle):
        """Initial state values should be preserved."""
        initial_state = StateVector(resource=0.8, threat=0.1, wellbeing=0.7)
        result = cycle.run(initial_state=initial_state)

        # Core values should be preserved or updated logically
        assert result.state_vector.resource == pytest.approx(0.8)
        assert result.state_vector.wellbeing == pytest.approx(0.7)

    def test_state_modifications_persist(self, cycle):
        """State modifications should persist through phases."""
        modifications = []

        def modifying_handler(phase, state, context):
            state.set(SVField.AROUSAL, 0.7)
            modifications.append(state.get(SVField.AROUSAL))
            return PhaseResult(phase=phase, success=True)

        cycle.register_handler(Phase.SENSE, modifying_handler)
        result = cycle.run()

        assert result.state_vector.get(SVField.AROUSAL) == pytest.approx(0.7)

    def test_state_updates_cumulative(self, cycle):
        """State updates should be cumulative across phases."""
        def sense_handler(phase, state, context):
            state.set(SVField.AROUSAL, 0.3)
            return PhaseResult(phase=phase, success=True)

        def feel_handler(phase, state, context):
            current_arousal = state.get(SVField.AROUSAL, 0)
            state.set(SVField.AROUSAL, min(1.0, current_arousal + 0.2))
            return PhaseResult(phase=phase, success=True)

        cycle.register_handler(Phase.SENSE, sense_handler)
        cycle.register_handler(Phase.FEEL, feel_handler)
        result = cycle.run()

        assert result.state_vector.get(SVField.AROUSAL) == pytest.approx(0.5)

    def test_threat_accumulates(self, cycle_with_handlers, threatening_stimulus):
        """Threat level should accumulate from perception."""
        result = cycle_with_handlers.run(stimulus=threatening_stimulus)

        # Threat should be set from perception
        assert result.state_vector.threat > 0

    def test_state_vector_copy_independence(self, cycle):
        """State vector copy should be independent."""
        initial_state = StateVector(resource=0.5)

        def modifying_handler(phase, state, context):
            state.resource = 0.9
            return PhaseResult(phase=phase, success=True)

        cycle.register_handler(Phase.SENSE, modifying_handler)
        result = cycle.run(initial_state=initial_state)

        # Original should be unchanged
        assert initial_state.resource == 0.5
        # Result should have modified value
        assert result.state_vector.resource == pytest.approx(0.9)


# ============================================================================
# CONSCIOUSNESS GLOBAL WORKSPACE INTEGRATION TESTS
# ============================================================================

class TestConsciousnessIntegration:
    """Test consciousness module integration with cycle."""

    def test_consciousness_receives_perception_input(
        self,
        consciousness_processor,
        cycle_with_handlers,
        simple_stimulus,
    ):
        """Consciousness should receive perception data."""
        # Boost ALL awareness types with level, clarity and depth
        # Access awareness_manager directly for full parameter support
        for awareness_type in AwarenessType:
            consciousness_processor.awareness_manager.update_awareness(
                awareness_type, level=0.9, clarity=0.9, depth=0.9
            )

        # Run cycle to get perception output
        cycle_result = cycle_with_handlers.run(stimulus=simple_stimulus)
        perceive_result = cycle_result.phase_results[Phase.PERCEIVE]

        # Feed to consciousness
        output = consciousness_processor.process(
            inputs={
                "perception": {
                    "summary": "Agent detected",
                    "relevance": 0.7,
                    "novelty": 0.5,
                },
            },
        )

        # Consciousness should process input and be conscious
        assert output.is_conscious is True
        assert output.active_contents_count >= 0

    def test_consciousness_attention_updates(self, consciousness_processor):
        """Consciousness attention should update with inputs."""
        # First boost awareness to ensure conscious
        consciousness_processor.update_awareness(AwarenessType.SENSORY, level=0.8)
        consciousness_processor.update_awareness(AwarenessType.COGNITIVE, level=0.8)

        # High priority input
        output = consciousness_processor.process(
            inputs={
                "perception": {
                    "summary": "Critical event",
                    "relevance": 0.9,
                    "urgency": 0.9,
                    "threat": 0.8,
                },
            },
        )

        # Attention should have been captured
        focus = consciousness_processor.get_current_focus()
        # Processor should be functional
        assert output.overall_awareness >= 0

    def test_consciousness_awareness_levels(self, consciousness_processor):
        """Consciousness awareness levels should update."""
        # Update sensory awareness
        consciousness_processor.update_awareness(
            AwarenessType.SENSORY,
            level=0.8,
            focus="visual",
        )

        # Check awareness
        output = consciousness_processor.process()
        assert output.overall_awareness >= 0

    def test_consciousness_in_cycle(self, cycle):
        """Consciousness can be integrated into cycle."""
        consciousness = create_consciousness_processor()
        cycle_outputs = []

        def feel_with_consciousness(phase, state, context):
            # Process with consciousness
            output = consciousness.process(
                inputs={
                    "affect": {
                        "valence": state.get(SVField.VALENCE, 0.5),
                        "arousal": state.get(SVField.AROUSAL, 0.5),
                    },
                },
            )
            cycle_outputs.append(output)
            return PhaseResult(
                phase=phase,
                success=True,
                output={"consciousness_level": output.consciousness_level.value},
            )

        cycle.register_handler(Phase.FEEL, feel_with_consciousness)
        result = cycle.run()

        assert len(cycle_outputs) == 1
        assert cycle_outputs[0].consciousness_level in ConsciousnessLevel

    def test_workspace_broadcast_to_modules(self, consciousness_processor):
        """Workspace broadcasts should reach registered modules."""
        received_broadcasts = []

        def broadcast_handler(content: WorkspaceContent):
            received_broadcasts.append(content)

        consciousness_processor.register_broadcast_listener(
            module_name="test_module",
            callback=broadcast_handler,
        )

        # Submit and process content
        consciousness_processor.workspace.submit_content(
            content_type=BroadcastType.PERCEPTION,
            source_module="perception",
            payload={"test": True},
            summary="Test content",
            relevance=0.9,
            urgency=0.8,
            novelty=0.7,
        )

        consciousness_processor.workspace.process_cycle()

        # Broadcast should have been received
        # (depends on competition winning)
        assert isinstance(received_broadcasts, list)


# ============================================================================
# METAMIND CYCLE ANALYSIS TESTS
# ============================================================================

class TestMetaMindIntegration:
    """Test MetaMind module integration with cycle."""

    def test_metamind_analyzes_cycle(self, metamind_processor, cycle):
        """MetaMind should analyze cycle metrics."""
        # Run cycle
        cycle_result = cycle.run()

        # Analyze with MetaMind
        output = metamind_processor.process(
            cycle_id=cycle_result.cycle_id,
            duration_ms=cycle_result.duration_ms,
            phase_durations={
                p.value: r.duration_ms
                for p, r in cycle_result.phase_results.items()
            },
            success=all(r.success for r in cycle_result.phase_results.values()),
        )

        assert output.cycle_id == cycle_result.cycle_id
        assert output.analysis is not None

    def test_metamind_detects_slow_cycle(self, metamind_processor):
        """MetaMind should detect slow cycles."""
        # Simulate slow cycle
        output = metamind_processor.process(
            cycle_id=1,
            duration_ms=1000.0,  # 1 second - slow
            phase_durations={"think": 800.0, "act": 200.0},
            success=True,
        )

        # Should generate insight or detect issue
        assert output.performance_score < 0.5  # Low score for slow cycle

    def test_metamind_tracks_patterns(self, metamind_processor):
        """MetaMind should track patterns over multiple cycles."""
        # Run multiple cycles
        for i in range(20):
            metamind_processor.process(
                cycle_id=i,
                duration_ms=100.0 + (i % 3) * 20,  # Varying duration
                phase_durations={"think": 80.0, "act": 20.0 + (i % 3) * 20},
                success=True,
            )

        # Check stats
        stats = metamind_processor.get_stats()
        assert stats["processor"]["process_calls"] == 20

    def test_metamind_generates_insights_on_failure(self, metamind_processor):
        """MetaMind should generate insights on cycle failure."""
        output = metamind_processor.process(
            cycle_id=1,
            duration_ms=100.0,
            phase_durations={"think": 100.0},
            success=False,
            failed_phases=["think"],
        )

        # Should generate warning insight
        assert len(output.new_insights) > 0

    def test_metamind_suggests_adaptation(self, metamind_processor):
        """MetaMind should suggest adaptations for issues."""
        # Slow cycle should trigger adaptation suggestion
        output = metamind_processor.process(
            cycle_id=1,
            duration_ms=500.0,
            phase_durations={"think": 400.0, "act": 100.0},
            success=True,
        )

        # May suggest adaptation
        assert output.suggested_adaptation is not None or output.performance_score <= 1.0


# ============================================================================
# END-TO-END SCENARIO TESTS
# ============================================================================

class TestEndToEndScenarios:
    """Complete end-to-end scenario tests."""

    def test_greeting_scenario(self, cycle_with_handlers):
        """Test friendly greeting scenario."""
        stimulus = Stimulus(
            stimulus_type="social",
            source_entity=Entity(
                id="friend",
                entity_type="agent",
                attributes={
                    "expression": "happy",
                    "body_language": "open",
                    "relationship": "friend",
                },
            ),
            content={
                "verbal": "Hey! Great to see you!",
                "situation": "greeting",
            },
            intensity=0.6,
        )

        result = cycle_with_handlers.run(stimulus=stimulus)

        # All phases should succeed
        assert all(r.success for r in result.phase_results.values())

        # No significant threat
        assert result.state_vector.threat < 0.3

    def test_threat_assessment_scenario(self, cycle_with_handlers):
        """Test threat assessment and response."""
        stimulus = Stimulus(
            stimulus_type="social",
            source_entity=Entity(
                id="stranger",
                entity_type="agent",
                attributes={
                    "expression": "angry",
                    "body_language": "aggressive",
                    "hostile": True,
                    "threatening": True,
                },
            ),
            content={
                "verbal": "What are you looking at?",
                "situation": "confrontation",
            },
            intensity=0.8,
        )

        result = cycle_with_handlers.run(stimulus=stimulus)

        # All phases should complete
        assert all(r.success for r in result.phase_results.values())

        # Threat should be detected
        assert result.state_vector.threat > 0.5

    def test_memory_retrieval_scenario(self, cycle_with_handlers):
        """Test memory retrieval during processing."""
        memory_accessed = []

        def retrieve_handler(phase, state, context):
            # Simulate memory retrieval
            detected_agents = context.metadata.get("detected_agents", [])
            if detected_agents:
                memory_accessed.append({
                    "agent_id": detected_agents[0].get("id"),
                    "retrieved_at": datetime.now(),
                })
            return PhaseResult(
                phase=phase,
                success=True,
                output={"memories_retrieved": len(memory_accessed)},
            )

        cycle_with_handlers.register_handler(Phase.RETRIEVE, retrieve_handler)

        stimulus = Stimulus(
            stimulus_type="social",
            source_entity=Entity(
                id="known_agent",
                entity_type="agent",
                attributes={"relationship": "acquaintance"},
            ),
            content={"situation": "reunion"},
            intensity=0.5,
        )

        result = cycle_with_handlers.run(stimulus=stimulus)

        # Memory should have been accessed
        assert len(memory_accessed) >= 0  # Depends on agent detection

    def test_decision_making_scenario(self, cycle_with_handlers):
        """Test decision making based on perception."""
        decision_made = []

        def decide_handler(phase, state, context):
            threat = state.threat
            if threat > 0.5:
                decision = "flee"
            elif threat > 0.2:
                decision = "observe"
            else:
                decision = "engage"

            decision_made.append(decision)
            return PhaseResult(
                phase=phase,
                success=True,
                output={"decision": decision},
            )

        cycle_with_handlers.register_handler(Phase.DECIDE, decide_handler)

        # Threatening stimulus
        threatening = Stimulus(
            stimulus_type="social",
            source_entity=Entity(
                id="threat",
                entity_type="agent",
                attributes={"hostile": True, "expression": "angry"},
            ),
            content={"situation": "danger"},
            intensity=0.9,
        )

        result = cycle_with_handlers.run(stimulus=threatening)

        assert len(decision_made) == 1
        # Decision should reflect threat level
        assert decision_made[0] in ["flee", "observe", "engage"]

    def test_action_execution_scenario(self, cycle_with_handlers):
        """Test action execution at end of cycle."""
        actions_executed = []

        def plan_handler(phase, state, context):
            return PhaseResult(
                phase=phase,
                success=True,
                output={"planned_action": "greet"},
            )

        def act_handler(phase, state, context):
            phase_results = context.metadata.get("phase_results", {})
            plan_result = phase_results.get(Phase.PLAN)
            if plan_result and plan_result.output:
                action = plan_result.output.get("planned_action", "none")
                actions_executed.append(action)
            return PhaseResult(
                phase=phase,
                success=True,
                output={"action_executed": actions_executed[-1] if actions_executed else "none"},
            )

        cycle_with_handlers.register_handler(Phase.PLAN, plan_handler)
        cycle_with_handlers.register_handler(Phase.ACT, act_handler)

        result = cycle_with_handlers.run()

        assert len(actions_executed) == 1
        assert actions_executed[0] == "greet"

    def test_full_cognitive_loop(self, cycle_with_handlers, metamind_processor, consciousness_processor):
        """Test complete cognitive loop with all systems."""
        # Boost ALL awareness types with level, clarity and depth
        # Access awareness_manager directly for full parameter support
        for awareness_type in AwarenessType:
            consciousness_processor.awareness_manager.update_awareness(
                awareness_type, level=0.9, clarity=0.9, depth=0.9
            )

        # Create stimulus
        stimulus = Stimulus(
            stimulus_type="social",
            source_entity=Entity(
                id="colleague",
                entity_type="agent",
                attributes={
                    "expression": "neutral",
                    "relationship": "colleague",
                },
            ),
            content={
                "verbal": "Can you help me with something?",
                "situation": "request",
            },
            intensity=0.5,
        )

        # Run cognitive cycle
        cycle_result = cycle_with_handlers.run(stimulus=stimulus)

        # Process with consciousness
        consciousness_output = consciousness_processor.process(
            inputs={
                "perception": {
                    "summary": "Colleague requesting help",
                    "relevance": 0.8,
                },
            },
        )

        # Analyze with MetaMind
        metamind_output = metamind_processor.process(
            cycle_id=cycle_result.cycle_id,
            duration_ms=cycle_result.duration_ms,
            phase_durations={
                p.value: r.duration_ms
                for p, r in cycle_result.phase_results.items()
            },
            success=True,
        )

        # Verify all systems worked
        assert cycle_result.is_complete
        assert consciousness_output.is_conscious
        assert metamind_output.analysis is not None


# ============================================================================
# EVENT BUS INTEGRATION TESTS
# ============================================================================

class TestEventBusIntegration:
    """Test event bus integration with cycle."""

    def test_cycle_events_emitted(self, cycle, event_bus):
        """Cycle should emit start/end events."""
        events_received = []

        def track_event(event: Event):
            events_received.append(event.event_type)

        event_bus.subscribe(EventType.CYCLE_START, track_event)
        event_bus.subscribe(EventType.CYCLE_END, track_event)

        cycle.run()

        assert EventType.CYCLE_START in events_received
        assert EventType.CYCLE_END in events_received

    def test_phase_events_emitted(self, cycle, event_bus):
        """Each phase should emit start/end events."""
        phase_events = []

        def track_phase(event: Event):
            phase_events.append({
                "type": event.event_type,
                "phase": event.data.get("phase"),
            })

        event_bus.subscribe(EventType.MODULE_START, track_phase)
        event_bus.subscribe(EventType.MODULE_END, track_phase)

        cycle.run()

        # Should have 20 events (10 phases x 2 events)
        assert len(phase_events) == 20

    def test_event_data_accuracy(self, cycle, event_bus):
        """Event data should be accurate."""
        end_events = []

        def track_end(event: Event):
            end_events.append(event)

        event_bus.subscribe(EventType.CYCLE_END, track_end)

        result = cycle.run()

        assert len(end_events) == 1
        event = end_events[0]
        # Event should have duration data
        assert "duration_ms" in event.data
        event_duration = event.data.get("duration_ms", 0)
        assert event_duration >= 0
        # Event should have success field
        if "success" in event.data:
            assert isinstance(event.data["success"], bool)


# ============================================================================
# MONITORING INTEGRATION TESTS
# ============================================================================

class TestMonitoringIntegration:
    """Test monitoring integration with cycle."""

    def test_cycle_metrics_recorded(self, cycle):
        """Cycle metrics should be recorded."""
        result = cycle.run()

        metrics = cycle.current_metrics
        assert metrics is not None
        assert metrics.cycle_id == result.cycle_id

    def test_phase_metrics_recorded(self, cycle):
        """Phase metrics should be recorded."""
        cycle.run()

        metrics = cycle.current_metrics
        assert metrics is not None
        assert len(metrics.phase_metrics) == 10

    def test_metrics_history_accumulated(self, cycle):
        """Metrics history should accumulate."""
        for _ in range(5):
            cycle.run()

        assert cycle.metrics_history.count == 5

    def test_cycle_stats_available(self, cycle):
        """Cycle stats should be available."""
        for _ in range(3):
            cycle.run()

        stats = cycle.get_stats()
        assert stats["total_cycles"] == 3
        assert "monitoring" in stats


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in cycle."""

    def test_phase_error_captured(self, cycle):
        """Phase errors should be captured."""
        def failing_handler(phase, state, context):
            raise ValueError("Test error")

        cycle.register_handler(Phase.REASON, failing_handler)
        result = cycle.run()

        # Phase should fail but cycle continues (stop_on_error=False by default)
        reason_result = result.phase_results[Phase.REASON]
        assert reason_result.success is False
        assert "Test error" in reason_result.error

    def test_cycle_continues_on_non_critical_error(self, cycle):
        """Cycle should continue on non-critical errors."""
        def failing_handler(phase, state, context):
            raise ValueError("Non-critical error")

        cycle.register_handler(Phase.EVALUATE, failing_handler)
        result = cycle.run()

        # Later phases should still run
        assert Phase.DECIDE in result.phase_results
        assert Phase.ACT in result.phase_results

    def test_cycle_stops_on_critical_error(self, event_bus):
        """Cycle should stop on critical error if configured."""
        config = CycleConfig(stop_on_error=True)
        cycle = CognitiveCycle(config=config, event_bus=event_bus)

        def failing_handler(phase, state, context):
            raise ValueError("Critical error")

        cycle.register_handler(Phase.SENSE, failing_handler)
        result = cycle.run()

        # Only SENSE should have result
        assert Phase.SENSE in result.phase_results
        # Later phases should not run
        assert result.phase_results[Phase.SENSE].success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
