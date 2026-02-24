"""
Anomaly Visualization Page
"""
import streamlit as st
import pandas as pd

from src.dashboard.utils.data_fetcher import get_api_client
from src.dashboard.utils.formatters import format_datetime, get_severity_emoji
from src.dashboard.components.metrics import error_box, success_box
from src.dashboard.components.charts import create_pie_chart, create_anomaly_timeline, create_bar_chart

st.set_page_config(page_title="Anomalies", page_icon="⚠️", layout="wide")

st.title("⚠️ Anomaly Detection")

api_client = get_api_client()

# Check connection
if not api_client.check_connection():
    error_box("Backend server is offline")
    st.stop()

# Fetch anomaly data
anomaly_summary = api_client.get_anomaly_summary()
timeline_data = api_client.get_anomaly_timeline(hours=24)

if not anomaly_summary:
    error_box("Failed to fetch anomaly data")
    st.stop()

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Anomalies", anomaly_summary.get('active_count', 0))
with col2:
    st.metric("Last 24 Hours", anomaly_summary.get('last_24h', 0))
with col3:
    st.metric("Last 7 Days", anomaly_summary.get('last_7d', 0))
with col4:
    total = anomaly_summary.get('last_7d', 0)
    resolved = total - anomaly_summary.get('active_count', 0)
    resolution_rate = (resolved / total * 100) if total > 0 else 0
    st.metric("Resolution Rate", f"{resolution_rate:.1f}%")

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Anomalies by Type")
    by_type = anomaly_summary.get('by_type', {})
    if by_type:
        fig = create_pie_chart(
            labels=list(by_type.keys()),
            values=list(by_type.values()),
            title="Distribution by Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No anomaly data available")

with col2:
    st.markdown("### Anomalies by Severity")
    by_severity = anomaly_summary.get('by_severity', {})
    if by_severity:
        fig = create_pie_chart(
            labels=list(by_severity.keys()),
            values=list(by_severity.values()),
            title="Distribution by Severity"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No anomaly data available")

# Timeline
st.markdown("---")
st.markdown("### Anomaly Timeline (Last 24 Hours)")

if timeline_data and timeline_data.get('timeline'):
    fig = create_anomaly_timeline(timeline_data['timeline'])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No timeline data available")

# Anomaly list
st.markdown("---")
st.markdown("### Active Anomalies")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    show_active_only = st.checkbox("Active Only", value=True)
with col2:
    severity_filter = st.selectbox("Severity", ["All", "low", "medium", "high", "critical"])
with col3:
    limit = st.slider("Max Results", 10, 200, 100)

# Fetch anomalies
params = {"active_only": show_active_only, "limit": limit}
if severity_filter != "All":
    params["severity"] = severity_filter

anomalies_data = api_client.get_anomalies(**params)

if anomalies_data and anomalies_data.get('anomalies'):
    anomalies = anomalies_data['anomalies']
    
    # Create table
    anomaly_table = []
    for anomaly in anomalies:
        anomaly_table.append({
            "ID": anomaly.get('id'),
            "Device": anomaly.get('device_id', 'N/A'),
            "Type": anomaly.get('anomaly_type', 'N/A'),
            "Severity": f"{get_severity_emoji(anomaly.get('severity', 'unknown'))} {anomaly.get('severity', 'unknown')}",
            "Sensor": anomaly.get('sensor_type', 'N/A'),
            "Score": f"{anomaly.get('anomaly_score', 0):.2f}" if anomaly.get('anomaly_score') else 'N/A',
            "Detected": format_datetime(anomaly.get('detected_at')),
            "Status": "Active" if not anomaly.get('resolved_at') else "Resolved"
        })
    
    df = pd.DataFrame(anomaly_table)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown(f"**Total:** {len(anomalies)} anomalies")
    
    # Anomaly details
    st.markdown("---")
    st.markdown("### Anomaly Details")
    
    anomaly_ids = [a.get('id') for a in anomalies]
    selected_id = st.selectbox("Select Anomaly ID", anomaly_ids)
    
    if selected_id:
        anomaly = api_client.get_anomaly(selected_id)
        
        if anomaly:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {anomaly.get('id')}")
                st.write(f"**Device:** {anomaly.get('device_id')}")
                st.write(f"**Type:** {anomaly.get('anomaly_type')}")
                st.write(f"**Severity:** {get_severity_emoji(anomaly.get('severity'))} {anomaly.get('severity')}")
                st.write(f"**Sensor:** {anomaly.get('sensor_type', 'N/A')}")
            
            with col2:
                st.write(f"**Score:** {anomaly.get('anomaly_score', 'N/A')}")
                st.write(f"**Detected:** {format_datetime(anomaly.get('detected_at'))}")
                st.write(f"**Resolved:** {format_datetime(anomaly.get('resolved_at')) if anomaly.get('resolved_at') else 'Not resolved'}")
                st.write(f"**Description:** {anomaly.get('description', 'N/A')}")
            
            # Resolve button
            if anomaly.get('is_active'):
                if st.button(f"✅ Resolve Anomaly {selected_id}", type="primary"):
                    result = api_client.resolve_anomaly(selected_id)
                    if result:
                        success_box(f"Anomaly {selected_id} marked as resolved")
                        st.rerun()
                    else:
                        error_box("Failed to resolve anomaly")
else:
    st.info("No anomalies found")

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh", key="anomalies_refresh"):
    import time
    time.sleep(5)
    st.rerun()
