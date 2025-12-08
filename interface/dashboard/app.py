"""
UEM v2 - Streamlit Dashboard

Real-time monitoring dashboard for UEM system.
Reads data from PostgreSQL for cross-process visibility.

Run with: streamlit run interface/dashboard/app.py
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from meta.monitoring.persistence import DashboardDataProvider

# Database URL
DATABASE_URL = os.environ.get(
    "UEM_DATABASE_URL",
    "postgresql://uem:uem_secret@localhost:5432/uem_v2"
)

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


@st.cache_resource
def get_data_provider() -> DashboardDataProvider:
    """Get cached data provider instance."""
    return DashboardDataProvider(database_url=DATABASE_URL)


def get_dashboard_data() -> Dict[str, Any]:
    """Gather all dashboard data from PostgreSQL."""
    provider = get_data_provider()

    try:
        data = provider.get_all_dashboard_data()

        return {
            "cycle_metrics": data["cycle_metrics"],
            "phase_durations": data["phase_durations"],
            "memory_stats": data["memory_stats"],
            "trust_data": data["trust_levels"],
            "recent_activity": data["recent_activity"],
            "db_connected": True,
        }
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return {
            "cycle_metrics": {
                "total": 0,
                "success_rate": 0,
                "avg_duration_ms": 0,
                "success_count": 0,
                "failed_count": 0,
            },
            "phase_durations": {},
            "memory_stats": {"episodes": 0, "relationships": 0, "retrievals": 0},
            "trust_data": {},
            "recent_activity": [],
            "db_connected": False,
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
        status = "Connected" if data.get("db_connected", False) else "Disconnected"
        st.metric(
            label="Database",
            value=status,
        )


def render_phase_chart(data: Dict[str, Any]) -> None:
    """Render phase duration bar chart."""
    st.subheader("Phase Durations (ms)")

    phase_durations = data["phase_durations"]

    if phase_durations and any(v > 0 for v in phase_durations.values()):
        # Sort phases by name for consistent ordering
        sorted_phases = sorted(phase_durations.items(), key=lambda x: x[0])

        chart_data = {
            "Phase": [p[0] for p in sorted_phases],
            "Duration (ms)": [p[1] for p in sorted_phases],
        }
        st.bar_chart(chart_data, x="Phase", y="Duration (ms)", width="stretch")
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
            help="Entity relationships tracked",
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
        st.bar_chart(chart_data, x="Agent", y="Trust Level", width="stretch")

        # Trust legend
        st.caption("Trust scale: 0.0 (distrust) - 1.0 (full trust)")
    else:
        st.info("No trust data recorded yet.")


def render_activity_log(data: Dict[str, Any]) -> None:
    """Render recent activity log."""
    st.subheader("Recent Activity")

    activities = data["recent_activity"]

    if activities:
        # Show last 20 activities
        for activity in activities[:20]:
            created_at = activity.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except (ValueError, AttributeError):
                    time_str = created_at[:8] if len(created_at) >= 8 else "??:??:??"
            else:
                time_str = "??:??:??"

            event_type = activity.get("event_type", "unknown")
            source = activity.get("source") or "system"

            # Color code by event type
            if "error" in event_type.lower() or "failed" in event_type.lower():
                icon = "🔴"
            elif "success" in event_type.lower() or "complete" in event_type.lower():
                icon = "🟢"
            elif "start" in event_type.lower():
                icon = "🔵"
            elif "trust" in event_type.lower():
                icon = "🤝"
            elif "emotion" in event_type.lower():
                icon = "💭"
            elif "threat" in event_type.lower():
                icon = "⚠️"
            else:
                icon = "⚪"

            st.text(f"{icon} [{time_str}] {event_type} (from: {source})")
    else:
        st.info("No events recorded yet.")


def render_system_stats(data: Dict[str, Any]) -> None:
    """Render system statistics in sidebar."""
    st.sidebar.subheader("Database Info")

    cycle_metrics = data["cycle_metrics"]
    memory_stats = data["memory_stats"]

    st.sidebar.metric("Total Cycles", cycle_metrics.get("total", 0))
    st.sidebar.metric("Total Episodes", memory_stats.get("episodes", 0))
    st.sidebar.metric("Total Relationships", memory_stats.get("relationships", 0))

    # Connection status
    if data.get("db_connected"):
        st.sidebar.success("PostgreSQL Connected")
    else:
        st.sidebar.error("PostgreSQL Disconnected")


def main():
    """Main dashboard entry point."""
    # Header
    st.title("UEM Dashboard")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Sidebar controls
    st.sidebar.title("Controls")

    auto_refresh = st.sidebar.checkbox("Auto-refresh (1s)", value=True)

    if st.sidebar.button("Manual Refresh"):
        st.cache_resource.clear()
        st.rerun()

    # Get data from PostgreSQL
    data = get_dashboard_data()

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
