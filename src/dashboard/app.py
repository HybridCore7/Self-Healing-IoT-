"""
Self-Healing IoT System Dashboard
Main Streamlit Application
"""
import streamlit as st
from datetime import datetime

from src.dashboard.config import PAGE_TITLE, PAGE_ICON, LAYOUT, AUTO_REFRESH_INTERVAL
from src.dashboard.utils.data_fetcher import get_api_client
from src.dashboard.components.metrics import error_box, success_box, warning_box

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-online {
        color: #2ecc71;
    }
    .status-offline {
        color: #e74c3c;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize API client
api_client = get_api_client()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/internet-of-things.png", width=80)
    st.markdown("# 🔧 IoT Dashboard")
    st.markdown("---")
    
    # Connection status
    st.markdown("### Connection Status")
    if api_client.check_connection():
        st.markdown("🟢 **Backend Connected**")
        backend_status = "online"
    else:
        st.markdown("🔴 **Backend Offline**")
        backend_status = "offline"
    
    st.markdown("---")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        refresh_interval = st.slider(
            "Refresh interval (seconds)",
            min_value=1,
            max_value=30,
            value=AUTO_REFRESH_INTERVAL
        )
        st.info(f"Refreshing every {refresh_interval}s")
    
    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    # System info
    st.markdown("### Quick Stats")
    if backend_status == "online":
        metrics = api_client.get_system_metrics()
        if metrics:
            st.metric("Total Devices", metrics.get('devices', {}).get('total', 0))
            st.metric("Active Anomalies", metrics.get('anomalies', {}).get('active', 0))
            st.metric("Healing Actions Today", metrics.get('healing', {}).get('actions_today', 0))
    else:
        st.warning("Backend offline")
    
    st.markdown("---")
    st.markdown("### About")
    st.info(
        "**Self-Healing IoT System**\n\n"
        "AI-powered autonomous fault detection and recovery for IoT devices.\n\n"
        "📚 [Documentation](#) | 🐛 [Report Issue](#)"
    )

# Main content
st.markdown('<p class="main-header">🏠 System Overview</p>', unsafe_allow_html=True)

if backend_status == "offline":
    error_box("Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000")
    st.code("python -m src.backend.main", language="bash")
    st.stop()

# Get system health
health = api_client.get_system_health()
metrics = api_client.get_system_metrics()

if not health or not metrics:
    error_box("Failed to fetch system data")
    st.stop()

# System health status
col1, col2, col3, col4 = st.columns(4)

with col1:
    status = health.get('status', 'unknown')
    if status == 'healthy':
        st.success(f"✅ System {status.upper()}")
    else:
        st.warning(f"⚠️ System {status.upper()}")

with col2:
    services = health.get('services', {})
    mqtt_status = services.get('mqtt', 'unknown')
    if mqtt_status == 'connected':
        st.success(f"✅ MQTT {mqtt_status.upper()}")
    else:
        st.warning(f"⚠️ MQTT {mqtt_status.upper()}")

with col3:
    db_status = services.get('database', 'unknown')
    if db_status == 'connected':
        st.success(f"✅ Database {db_status.upper()}")
    else:
        st.error(f"❌ Database {db_status.upper()}")

with col4:
    healing_status = services.get('healing_orchestrator', 'unknown')
    if healing_status == 'running':
        st.success(f"✅ Healing {healing_status.upper()}")
    else:
        st.error(f"❌ Healing {healing_status.upper()}")

st.markdown("---")

# Key metrics
st.markdown("### 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

device_metrics = metrics.get('devices', {})
anomaly_metrics = metrics.get('anomalies', {})
healing_metrics = metrics.get('healing', {})
system_resources = metrics.get('system_resources', {})

with col1:
    st.metric(
        "Total Devices",
        device_metrics.get('total', 0),
        delta=f"{device_metrics.get('active', 0)} active"
    )

with col2:
    st.metric(
        "Active Anomalies",
        anomaly_metrics.get('active', 0),
        delta=None
    )

with col3:
    st.metric(
        "Healing Actions Today",
        healing_metrics.get('actions_today', 0),
        delta=f"{healing_metrics.get('total_actions', 0)} total"
    )

with col4:
    cpu_percent = system_resources.get('cpu_percent', 0)
    st.metric(
        "CPU Usage",
        f"{cpu_percent}%",
        delta=None
    )

st.markdown("---")

# Device health summary
st.markdown("### 🔌 Device Health Summary")

device_health = api_client.get_device_health_summary()
if device_health:
    health_summary = device_health.get('health_summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Healthy", health_summary.get('healthy', 0))
    with col2:
        st.metric("⚠️ Warning", health_summary.get('warning', 0))
    with col3:
        st.metric("🔴 Critical", health_summary.get('critical', 0))
    with col4:
        st.metric("⚫ Offline", health_summary.get('offline', 0))
    
    # Device list
    with st.expander("📋 View All Devices"):
        devices = device_health.get('devices', [])
        if devices:
            for device in devices:
                cols = st.columns([3, 2, 2, 3])
                with cols[0]:
                    st.write(f"**{device.get('device_name', 'Unknown')}**")
                with cols[1]:
                    status = device.get('status', 'unknown')
                    st.write(f"Status: {status}")
                with cols[2]:
                    health = device.get('health', 'unknown')
                    emoji = "✅" if health == "healthy" else "⚠️" if health == "warning" else "🔴" if health == "critical" else "⚫"
                    st.write(f"{emoji} {health}")
                with cols[3]:
                    anomalies = device.get('active_anomalies', 0)
                    st.write(f"Anomalies: {anomalies}")
        else:
            st.info("No devices registered")

st.markdown("---")

# System resources
st.markdown("### 💻 System Resources")

col1, col2, col3 = st.columns(3)

with col1:
    cpu = system_resources.get('cpu_percent', 0)
    st.metric("CPU", f"{cpu}%")
    st.progress(cpu / 100)

with col2:
    memory = system_resources.get('memory_percent', 0)
    st.metric("Memory", f"{memory}%")
    st.progress(memory / 100)

with col3:
    disk = system_resources.get('disk_percent', 0)
    st.metric("Disk", f"{disk}%")
    st.progress(disk / 100)

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
    unsafe_allow_html=True
)

# Auto-refresh logic
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()
