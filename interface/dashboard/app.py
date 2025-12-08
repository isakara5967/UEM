"""
UEM v2 - Streamlit Dashboard

Real-time monitoring dashboard for UEM system.

Run with: streamlit run interface/dashboard/app.py
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from meta.monitoring.metrics.collector import get_metrics_collector, MetricsCollector
from meta.monitoring.monitor import get_system_monitor, SystemMonitor
from engine.events.bus import get_event_bus, EventBus, Event
from core.affect.social.trust import Trust


# Page config
st.set_page_config(
    page_title="UEM Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)


def get_dashboard_data() -> Dict[str, Any]:
    """Gather all dashboard data from UEM components."""
    metrics = get_metrics_collector()
    monitor = get_system_monitor()
    event_bus = get_event_bus()

    # Cycle metrics
    cycles_completed = metrics.get_summary("cycles_completed")
    cycles_success = metrics.get_summary("cycles_success")
    cycles_failed = metrics.get_summary("cycles_failed")
    cycle_duration = metrics.get_summary("cycle_duration_ms")

    total_cycles = int(cycles_completed.last_value) if cycles_completed else 0
    success_count = int(cycles_success.last_value) if cycles_success else 0
    failed_count = int(cycles_failed.last_value) if cycles_failed else 0

    success_rate = (success_count / total_cycles * 100) if total_cycles > 0 else 0
    avg_duration = cycle_duration.avg_value if cycle_duration else 0

    # Phase durations
    phase_durations = {}
    phase_names = ["1_sense", "2_attend", "3_perceive", "4_retrieve",
                   "5_reason", "6_evaluate", "7_feel", "8_decide", "9_plan", "10_act"]

    for phase in phase_names:
        phase_metrics = [m for m in metrics.get_history("phase_duration_ms", limit=100)
                        if m.tags.get("phase") == phase]
        if phase_metrics:
            phase_durations[phase] = sum(m.value for m in phase_metrics) / len(phase_metrics)
        else:
            phase_durations[phase] = 0

    # Memory stats
    memory_stored = metrics.get_summary("memory_stored") or metrics.get_summary("episodes_stored")
    memory_retrieved = metrics.get_summary("memory_retrieved") or metrics.get_summary("episodes_retrieved")

    memory_stats = {
        "episodes": int(memory_stored.last_value) if memory_stored else 0,
        "retrievals": int(memory_retrieved.last_value) if memory_retrieved else 0,
        "relationships": 0,  # Would come from graph memory
    }

    # Trust data
    trust = Trust()
    trust_data = {}
    try:
        most_trusted = trust.most_trusted(limit=10)
        least_trusted = trust.least_trusted(limit=10)
        all_agents = set([a[0] for a in most_trusted] + [a[0] for a in least_trusted])
        for agent_id in all_agents:
            trust_data[agent_id] = trust.get(agent_id)
    except Exception:
        pass

    # Recent events
    recent_events = event_bus.get_history(limit=50)

    return {
        "cycle_metrics": {
            "total": total_cycles,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration,
            "success_count": success_count,
            "failed_count": failed_count,
        },
        "phase_durations": phase_durations,
        "memory_stats": memory_stats,
        "trust_data": trust_data,
        "recent_events": recent_events,
        "monitor_running": monitor._running,
        "collector_stats": metrics.stats,
        "event_bus_stats": event_bus.stats,
    }


def render_cycle_metrics(data: Dict[str, Any]) -> None:
    """Render cycle metrics section."""
    st.subheader("Cycle Metrics")

    metrics = data["cycle_metrics"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Cycles",
            value=f"{metrics['total']:,}",
            delta=None,
        )

    with col2:
        st.metric(
            label="Success Rate",
            value=f"{metrics['success_rate']:.1f}%",
            delta=f"{metrics['success_count']} OK / {metrics['failed_count']} Failed",
        )

    with col3:
        st.metric(
            label="Avg Duration",
            value=f"{metrics['avg_duration_ms']:.1f} ms",
        )

    with col4:
        status = "Running" if data["monitor_running"] else "Stopped"
        st.metric(
            label="Monitor Status",
            value=status,
        )


def render_phase_chart(data: Dict[str, Any]) -> None:
    """Render phase duration bar chart."""
    st.subheader("Phase Durations (ms)")

    phase_durations = data["phase_durations"]

    if any(v > 0 for v in phase_durations.values()):
        # Create chart data
        chart_data = {
            "Phase": list(phase_durations.keys()),
            "Duration (ms)": list(phase_durations.values()),
        }
        st.bar_chart(chart_data, x="Phase", y="Duration (ms)", use_container_width=True)
    else:
        st.info("No phase duration data yet. Run some cycles to see metrics.")


def render_memory_stats(data: Dict[str, Any]) -> None:
    """Render memory statistics."""
    st.subheader("Memory Stats")

    memory = data["memory_stats"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Episodes",
            value=f"{memory['episodes']:,}",
            help="Total episodic memories stored",
        )

    with col2:
        st.metric(
            label="Relationships",
            value=f"{memory['relationships']:,}",
            help="Entity relationships in graph memory",
        )

    with col3:
        st.metric(
            label="Retrievals",
            value=f"{memory['retrievals']:,}",
            help="Total memory retrieval operations",
        )


def render_trust_chart(data: Dict[str, Any]) -> None:
    """Render trust levels bar chart."""
    st.subheader("Trust Levels by Agent")

    trust_data = data["trust_data"]

    if trust_data:
        # Sort by trust level
        sorted_trust = sorted(trust_data.items(), key=lambda x: x[1], reverse=True)

        chart_data = {
            "Agent": [a[0] for a in sorted_trust],
            "Trust Level": [a[1] for a in sorted_trust],
        }
        st.bar_chart(chart_data, x="Agent", y="Trust Level", use_container_width=True)

        # Trust legend
        st.caption("Trust scale: 0.0 (distrust) - 1.0 (full trust)")
    else:
        st.info("No trust data recorded yet.")


def render_activity_log(data: Dict[str, Any]) -> None:
    """Render recent activity log."""
    st.subheader("Recent Activity")

    events = data["recent_events"]

    if events:
        # Show last 20 events
        for event in reversed(events[-20:]):
            time_str = event.timestamp.strftime("%H:%M:%S")
            event_type = event.event_type.value
            source = event.source or "system"

            # Color code by event type
            if "error" in event_type.lower() or "failed" in event_type.lower():
                icon = "🔴"
            elif "success" in event_type.lower() or "complete" in event_type.lower():
                icon = "🟢"
            elif "start" in event_type.lower():
                icon = "🔵"
            else:
                icon = "⚪"

            st.text(f"{icon} [{time_str}] {event_type} (from: {source})")
    else:
        st.info("No events recorded yet.")


def render_system_stats(data: Dict[str, Any]) -> None:
    """Render system statistics in sidebar."""
    st.sidebar.subheader("System Stats")

    collector_stats = data["collector_stats"]
    bus_stats = data["event_bus_stats"]

    st.sidebar.metric("Metric Names", collector_stats.get("metric_names", 0))
    st.sidebar.metric("Total Records", collector_stats.get("total_records", 0))
    st.sidebar.metric("Total Events", bus_stats.get("total_events", 0))
    st.sidebar.metric("Subscribers", bus_stats.get("subscriber_count", 0))

    uptime = collector_stats.get("uptime_seconds", 0)
    if uptime > 3600:
        uptime_str = f"{uptime/3600:.1f} hours"
    elif uptime > 60:
        uptime_str = f"{uptime/60:.1f} mins"
    else:
        uptime_str = f"{uptime:.0f} secs"

    st.sidebar.metric("Collector Uptime", uptime_str)


def main():
    """Main dashboard entry point."""
    # Header
    st.title("UEM Dashboard")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Sidebar controls
    st.sidebar.title("Controls")

    auto_refresh = st.sidebar.checkbox("Auto-refresh (1s)", value=True)

    if st.sidebar.button("Manual Refresh"):
        st.rerun()

    # Get data
    try:
        data = get_dashboard_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        data = {
            "cycle_metrics": {"total": 0, "success_rate": 0, "avg_duration_ms": 0,
                             "success_count": 0, "failed_count": 0},
            "phase_durations": {},
            "memory_stats": {"episodes": 0, "relationships": 0, "retrievals": 0},
            "trust_data": {},
            "recent_events": [],
            "monitor_running": False,
            "collector_stats": {},
            "event_bus_stats": {},
        }

    # Render system stats in sidebar
    render_system_stats(data)

    # Main content
    render_cycle_metrics(data)

    st.divider()

    # Two column layout for charts
    col1, col2 = st.columns(2)

    with col1:
        render_phase_chart(data)

    with col2:
        render_trust_chart(data)

    st.divider()

    # Memory and Activity
    col1, col2 = st.columns([1, 2])

    with col1:
        render_memory_stats(data)

    with col2:
        render_activity_log(data)

    # Auto-refresh
    if auto_refresh:
        time.sleep(1)
        st.rerun()


if __name__ == "__main__":
    main()
