"""
Healing Logs Page
"""
import streamlit as st
import pandas as pd

from src.dashboard.utils.data_fetcher import get_api_client
from src.dashboard.utils.formatters import format_datetime, format_duration
from src.dashboard.components.metrics import error_box, success_box
from src.dashboard.components.charts import create_pie_chart, create_bar_chart

st.set_page_config(page_title="Healing Logs", page_icon="🔧", layout="wide")

st.title("🔧 Self-Healing Actions")

api_client = get_api_client()

# Check connection
if not api_client.check_connection():
    error_box("Backend server is offline")
    st.stop()

# Fetch healing data
healing_stats = api_client.get_healing_stats()
active_healings = api_client.get_active_healings()

if not healing_stats:
    error_box("Failed to fetch healing data")
    st.stop()

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Actions", healing_stats.get('total_actions', 0))
with col2:
    st.metric("Successful", healing_stats.get('successful_actions', 0))
with col3:
    st.metric("Failed", healing_stats.get('failed_actions', 0))
with col4:
    st.metric("Success Rate", f"{healing_stats.get('success_rate', 0)}%")

st.markdown("---")

# Active healings
if active_healings:
    st.markdown("### ⚡ Active Healing Workflows")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Healings", active_healings.get('active_healing_count', 0))
    with col2:
        st.metric("Devices in Cooldown", active_healings.get('devices_in_cooldown', 0))
    with col3:
        orchestrator_running = active_healings.get('orchestrator_running', False)
        status = "✅ Running" if orchestrator_running else "❌ Stopped"
        st.metric("Orchestrator", status)
    
    # Active devices
    active_devices = active_healings.get('active_devices', [])
    if active_devices:
        st.write("**Active Healing Devices:**", ", ".join(active_devices))
    
    st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Actions by Type")
    actions_by_type = healing_stats.get('actions_by_type', {})
    if actions_by_type:
        fig = create_bar_chart(
            actions_by_type,
            title="Healing Actions Distribution",
            color="#2ecc71"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No healing action data available")

with col2:
    st.markdown("### Success vs Failed")
    success_data = {
        "Successful": healing_stats.get('successful_actions', 0),
        "Failed": healing_stats.get('failed_actions', 0),
        "Pending": healing_stats.get('pending_actions', 0)
    }
    fig = create_pie_chart(
        labels=list(success_data.keys()),
        values=list(success_data.values()),
        title="Healing Outcomes",
        colors=["#2ecc71", "#e74c3c", "#f39c12"]
    )
    st.plotly_chart(fig, use_container_width=True)

# Healing logs
st.markdown("---")
st.markdown("### Healing Action Logs")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    device_filter = st.text_input("Filter by Device ID", placeholder="Leave empty for all")
with col2:
    status_filter = st.selectbox("Status", ["All", "success", "failed", "pending", "in_progress"])
with col3:
    limit = st.slider("Max Results", 10, 200, 100)

# Fetch logs
params = {"limit": limit}
if device_filter:
    params["device_id"] = device_filter

logs_data = api_client.get_healing_logs(**params)

if logs_data and logs_data.get('logs'):
    logs = logs_data['logs']
    
    # Filter by status if needed
    if status_filter != "All":
        logs = [log for log in logs if log.get('status') == status_filter]
    
    # Create table
    log_table = []
    for log in logs:
        success_emoji = "✅" if log.get('success') else "❌" if log.get('success') is False else "⏳"
        log_table.append({
            "ID": log.get('id'),
            "Device": log.get('device_id', 'N/A'),
            "Action": log.get('healing_action', 'N/A'),
            "Status": f"{success_emoji} {log.get('status', 'unknown')}",
            "Duration": format_duration(log.get('duration_seconds')),
            "Initiated": format_datetime(log.get('initiated_at')),
            "Completed": format_datetime(log.get('completed_at')) if log.get('completed_at') else "In progress"
        })
    
    df = pd.DataFrame(log_table)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown(f"**Total:** {len(logs)} healing actions")
    
    # Log details
    if logs:
        st.markdown("---")
        st.markdown("### Log Details")
        
        log_ids = [log.get('id') for log in logs]
        selected_id = st.selectbox("Select Log ID", log_ids)
        
        if selected_id:
            selected_log = next((log for log in logs if log.get('id') == selected_id), None)
            
            if selected_log:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {selected_log.get('id')}")
                    st.write(f"**Device:** {selected_log.get('device_id')}")
                    st.write(f"**Action:** {selected_log.get('healing_action')}")
                    st.write(f"**Status:** {selected_log.get('status')}")
                    st.write(f"**Success:** {'Yes' if selected_log.get('success') else 'No' if selected_log.get('success') is False else 'Pending'}")
                
                with col2:
                    st.write(f"**Initiated:** {format_datetime(selected_log.get('initiated_at'))}")
                    st.write(f"**Completed:** {format_datetime(selected_log.get('completed_at')) if selected_log.get('completed_at') else 'In progress'}")
                    st.write(f"**Duration:** {format_duration(selected_log.get('duration_seconds'))}")
                    st.write(f"**Error:** {selected_log.get('error_message', 'None')}")
else:
    st.info("No healing logs found")

# Manual healing trigger
st.markdown("---")
st.markdown("### 🎯 Manual Healing Trigger")

with st.form("manual_healing_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Get devices for dropdown
        devices = api_client.get_devices()
        device_ids = [d.get('device_id') for d in devices] if devices else []
        
        if device_ids:
            target_device = st.selectbox("Target Device", device_ids)
        else:
            target_device = st.text_input("Target Device ID")
            st.warning("No devices registered. Enter device ID manually.")
    
    with col2:
        # Get available actions
        actions_data = api_client.get_available_actions()
        if actions_data and actions_data.get('actions'):
            action_options = [a.get('action') for a in actions_data['actions']]
            selected_action = st.selectbox("Healing Action", action_options)
        else:
            selected_action = st.text_input("Healing Action", value="reset")
    
    st.info("💡 This will manually trigger a healing action on the selected device.")
    
    submitted = st.form_submit_button("🚀 Trigger Healing", type="primary")
    
    if submitted:
        if not target_device or not selected_action:
            error_box("Please select both device and action")
        else:
            result = api_client.trigger_healing(target_device, selected_action)
            
            if result and result.get('success'):
                success_box(f"Healing action '{selected_action}' triggered for device {target_device}")
                st.balloons()
            else:
                error_box("Failed to trigger healing action")

# Available actions reference
with st.expander("📋 Available Healing Actions"):
    actions_data = api_client.get_available_actions()
    if actions_data and actions_data.get('actions'):
        for action in actions_data['actions']:
            st.write(f"**{action.get('action')}**: {action.get('description')}")
    else:
        st.info("No actions available")

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh", key="healing_refresh"):
    import time
    time.sleep(5)
    st.rerun()
