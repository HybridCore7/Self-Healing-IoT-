"""
Overview Page - Self-Healing IoT Dashboard
Real-time system overview with key metrics, charts, and status
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.dashboard.utils.data_fetcher import get_api_client
from src.dashboard.utils.formatters import format_datetime, format_relative_time, get_status_emoji, get_severity_emoji
from src.dashboard.components.metrics import error_box, success_box, warning_box, metric_card
from src.dashboard.components.charts import (
    create_timeline_chart, create_pie_chart, create_bar_chart,
    create_anomaly_timeline, create_gauge_chart
)

st.set_page_config(page_title="Overview - IoT Dashboard", page_icon="📊", layout="wide")

# Custom CSS for premium look
st.markdown("""
    <style>
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1f77b4;
        padding-left: 10px;
    }
    .status-card {
        padding: 12px;
        border-radius: 8px;
        margin: 4px 0;
        font-weight: bold;
    }
    .heal-event {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 4px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="section-header">📊 System Overview</p>', unsafe_allow_html=True)
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

api_client = get_api_client()

# Backend check
if not api_client.check_connection():
    error_box("Backend server is offline. Start it with: `python -m src.backend.main`")
    st.code("python -m src.backend.main", language="bash")
    st.stop()

# ───────────────────────────────────────────────
# Fetch all data
# ───────────────────────────────────────────────
health = api_client.get_system_health()
metrics = api_client.get_system_metrics()
device_health = api_client.get_device_health_summary()
anomaly_summary = api_client.get_anomaly_summary()
healing_stats = api_client.get_healing_stats()
active_healings = api_client.get_active_healings()
timeline_data = api_client.get_anomaly_timeline(hours=24)

# ───────────────────────────────────────────────
# Section 1: System Status Banner
# ───────────────────────────────────────────────
st.markdown("### 🖥️ System Status")

col1, col2, col3, col4 = st.columns(4)
services = health.get('services', {}) if health else {}

with col1:
    status = health.get('status', 'unknown') if health else 'offline'
    if status == 'healthy':
        st.success(f"✅ System: **HEALTHY**")
    elif status == 'degraded':
        st.warning(f"⚠️ System: **DEGRADED**")
    else:
        st.error(f"❌ System: **{status.upper()}**")

with col2:
    mqtt = services.get('mqtt', 'unknown')
    if mqtt == 'connected':
        st.success("✅ MQTT: **CONNECTED**")
    else:
        st.warning(f"⚠️ MQTT: **{mqtt.upper()}**")

with col3:
    db = services.get('database', 'unknown')
    if db == 'connected':
        st.success("✅ Database: **CONNECTED**")
    else:
        st.error(f"❌ Database: **{db.upper()}**")

with col4:
    healing_svc = services.get('healing_orchestrator', 'unknown')
    if healing_svc == 'running':
        st.success("✅ Healing Engine: **RUNNING**")
    else:
        st.error(f"❌ Healing Engine: **{healing_svc.upper()}**")

st.markdown("---")

# ───────────────────────────────────────────────
# Section 2: Key KPI Metrics
# ───────────────────────────────────────────────
st.markdown("### 📈 Key Performance Indicators")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

device_m = metrics.get('devices', {}) if metrics else {}
anomaly_m = metrics.get('anomalies', {}) if metrics else {}
healing_m = metrics.get('healing', {}) if metrics else {}
sys_res = metrics.get('system_resources', {}) if metrics else {}
health_sum = device_health.get('health_summary', {}) if device_health else {}

with kpi1:
    st.metric("🔌 Total Devices", device_m.get('total', 0),
              delta=f"{device_m.get('active', 0)} online")

with kpi2:
    active_anom = anomaly_m.get('active', 0)
    st.metric("⚠️ Active Anomalies", active_anom,
              delta=f"{anomaly_m.get('today', 0)} today",
              delta_color="inverse")

with kpi3:
    st.metric("🔧 Healed Today", healing_m.get('actions_today', 0),
              delta=f"{healing_m.get('total_actions', 0)} total")

with kpi4:
    success_rate = healing_stats.get('success_rate', 0) if healing_stats else 0
    st.metric("✅ Healing Success Rate", f"{success_rate:.1f}%")

with kpi5:
    healthy_devices = health_sum.get('healthy', 0)
    total_devices = device_m.get('total', 1) or 1
    reliability = (healthy_devices / total_devices) * 100
    st.metric("💚 Network Reliability", f"{reliability:.1f}%")

st.markdown("---")

# ───────────────────────────────────────────────
# Section 3: Device Health + Anomaly Distribution
# ───────────────────────────────────────────────
st.markdown("### 🔌 Device Health & Anomaly Distribution")

col_left, col_right = st.columns(2)

with col_left:
    # Device health donut
    labels = ['Healthy', 'Warning', 'Critical', 'Offline']
    values = [
        health_sum.get('healthy', 0),
        health_sum.get('warning', 0),
        health_sum.get('critical', 0),
        health_sum.get('offline', 0),
    ]
    if sum(values) > 0:
        fig = create_pie_chart(
            labels=labels,
            values=values,
            title="Device Health Distribution",
            colors=['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No device health data available")

with col_right:
    # Anomaly type distribution
    if anomaly_summary:
        by_type = anomaly_summary.get('by_type', {})
        if by_type:
            fig = create_pie_chart(
                labels=list(by_type.keys()),
                values=list(by_type.values()),
                title="Anomaly Distribution by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No anomaly type data available")
    else:
        st.info("No anomaly data available")

# ───────────────────────────────────────────────
# Section 4: Anomaly Timeline
# ───────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📉 Anomaly Timeline (Last 24 Hours)")

if timeline_data and timeline_data.get('timeline'):
    fig = create_anomaly_timeline(timeline_data['timeline'])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No anomaly timeline data available for the last 24 hours. This is good — it may mean no anomalies were detected!")

# ───────────────────────────────────────────────
# Section 5: System Resources
# ───────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💻 System Resources")

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    cpu = sys_res.get('cpu_percent', 0)
    fig = create_gauge_chart(cpu, "CPU Usage (%)", max_value=100)
    st.plotly_chart(fig, use_container_width=True)

with res_col2:
    mem = sys_res.get('memory_percent', 0)
    fig = create_gauge_chart(mem, "Memory Usage (%)", max_value=100)
    st.plotly_chart(fig, use_container_width=True)

with res_col3:
    disk = sys_res.get('disk_percent', 0)
    fig = create_gauge_chart(disk, "Disk Usage (%)", max_value=100)
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────────────────────────
# Section 6: Active Healing Events
# ───────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔧 Active Healing Events")

if active_healings:
    active_count = active_healings.get('active_healing_count', 0)
    cooldown_count = active_healings.get('devices_in_cooldown', 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔄 Active Healings", active_count)
    with col2:
        st.metric("⏳ Devices in Cooldown", cooldown_count)

    pending = active_healings.get('pending_actions', [])
    if pending:
        st.markdown("**Pending Actions:**")
        for action in pending:
            st.markdown(
                f'<div class="heal-event">🔧 Device <code>{action.get("device_id", "N/A")}</code> → '
                f'Action: <strong>{action.get("healing_action", "N/A")}</strong> | '
                f'Status: {action.get("status", "N/A")}</div>',
                unsafe_allow_html=True
            )
    else:
        st.success("✅ No pending healing actions — system is stable!")
else:
    st.info("No active healing data available")

# ───────────────────────────────────────────────
# Section 7: Quick Device Status Table
# ───────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Device Status Summary")

if device_health and device_health.get('devices'):
    devices = device_health['devices']
    rows = []
    for d in devices:
        health_val = d.get('health', 'unknown')
        emoji = "✅" if health_val == "healthy" else "⚠️" if health_val == "warning" else "🔴" if health_val == "critical" else "⚫"
        rows.append({
            "Device": d.get('device_name', 'Unknown'),
            "ID": d.get('device_id', 'N/A'),
            "Status": f"{get_status_emoji(d.get('status', 'unknown'))} {d.get('status', 'unknown')}",
            "Health": f"{emoji} {health_val}",
            "Active Anomalies": d.get('active_anomalies', 0),
            "Last Seen": format_relative_time(d.get('last_heartbeat')),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No devices registered yet. Register devices via the Devices page or start the simulator.")

# ───────────────────────────────────────────────
# Footer
# ───────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:gray;font-size:0.85rem;'>"
    f"Self-Healing IoT System | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    f"</div>",
    unsafe_allow_html=True
)

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh", key="overview_refresh"):
    import time
    interval = st.sidebar.slider("Interval (s)", 5, 60, 10, key="overview_interval")
    time.sleep(interval)
    st.rerun()
