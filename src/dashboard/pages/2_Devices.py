"""
Device Monitoring Page
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.dashboard.utils.data_fetcher import get_api_client
from src.dashboard.utils.formatters import format_datetime, format_relative_time, get_status_emoji
from src.dashboard.components.metrics import error_box, success_box, warning_box, metric_card
from src.dashboard.components.charts import create_timeline_chart, create_pie_chart

st.set_page_config(page_title="Devices", page_icon="🔌", layout="wide")

st.title("🔌 Device Monitoring")

api_client = get_api_client()

# Check connection
if not api_client.check_connection():
    error_box("Backend server is offline")
    st.stop()

# Tabs
tab1, tab2 = st.tabs(["📋 Device List", "➕ Register Device"])

with tab1:
    st.markdown("### Registered Devices")
    
    # Fetch devices
    devices = api_client.get_devices()
    
    if not devices:
        st.info("No devices registered yet. Use the 'Register Device' tab to add one.")
    else:
        # Device statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total = len(devices)
        online = sum(1 for d in devices if d.get('status') == 'online')
        offline = total - online
        
        with col1:
            st.metric("Total Devices", total)
        with col2:
            st.metric("Online", online)
        with col3:
            st.metric("Offline", offline)
        with col4:
            uptime_pct = (online / total * 100) if total > 0 else 0
            st.metric("Uptime %", f"{uptime_pct:.1f}%")
        
        st.markdown("---")
        
        # Device table
        device_data = []
        for device in devices:
            device_data.append({
                "Device ID": device.get('device_id', 'N/A'),
                "Name": device.get('device_name', 'N/A'),
                "Type": device.get('device_type', 'N/A'),
                "Status": f"{get_status_emoji(device.get('status', 'unknown'))} {device.get('status', 'unknown')}",
                "Location": device.get('location', 'N/A'),
                "Last Heartbeat": format_relative_time(device.get('last_heartbeat'))
            })
        
        df = pd.DataFrame(device_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Device details
        st.markdown("### Device Details")
        
        device_ids = [d.get('device_id') for d in devices]
        selected_device_id = st.selectbox("Select Device", device_ids)
        
        if selected_device_id:
            device = api_client.get_device(selected_device_id)
            
            if device:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Device Information")
                    st.write(f"**ID:** {device.get('device_id')}")
                    st.write(f"**Name:** {device.get('device_name')}")
                    st.write(f"**Type:** {device.get('device_type')}")
                    st.write(f"**Location:** {device.get('location')}")
                    st.write(f"**Status:** {get_status_emoji(device.get('status'))} {device.get('status')}")
                    st.write(f"**Registered:** {format_datetime(device.get('created_at'))}")
                    st.write(f"**Last Heartbeat:** {format_datetime(device.get('last_heartbeat'))}")
                
                with col2:
                    st.markdown("#### Metadata")
                    metadata = device.get('metadata', {})
                    if metadata:
                        for key, value in metadata.items():
                            st.write(f"**{key}:** {value}")
                    else:
                        st.info("No metadata available")
                
                # Telemetry data
                st.markdown("---")
                st.markdown("#### Recent Telemetry")
                
                telemetry_data = api_client.get_device_telemetry(selected_device_id, limit=50)
                
                if telemetry_data and telemetry_data.get('readings'):
                    readings = telemetry_data['readings']
                    
                    # Create dataframe
                    telemetry_df = pd.DataFrame(readings)
                    
                    # Show chart
                    if not telemetry_df.empty and 'timestamp' in telemetry_df.columns and 'value' in telemetry_df.columns:
                        fig = create_timeline_chart(
                            readings,
                            x_field='timestamp',
                            y_field='value',
                            title=f"Telemetry Data - {selected_device_id}",
                            color_field='sensor_type'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Show table
                    with st.expander("📊 View Raw Data"):
                        st.dataframe(telemetry_df, use_container_width=True)
                else:
                    st.info("No telemetry data available")
                
                # Delete device button
                st.markdown("---")
                if st.button(f"🗑️ Delete Device {selected_device_id}", type="secondary"):
                    if api_client.delete_device(selected_device_id):
                        success_box(f"Device {selected_device_id} deleted successfully")
                        st.rerun()
                    else:
                        error_box(f"Failed to delete device {selected_device_id}")

with tab2:
    st.markdown("### Register New Device")
    
    with st.form("register_device_form"):
        device_id = st.text_input("Device ID*", placeholder="e.g., device_001")
        device_name = st.text_input("Device Name*", placeholder="e.g., Temperature Sensor 1")
        device_type = st.selectbox(
            "Device Type*",
            ["esp32_sensor", "raspberry_pi", "arduino", "custom"]
        )
        location = st.text_input("Location", placeholder="e.g., Lab Room A")
        
        col1, col2 = st.columns(2)
        with col1:
            firmware_version = st.text_input("Firmware Version", placeholder="e.g., 1.0.0")
        with col2:
            ip_address = st.text_input("IP Address", placeholder="e.g., 192.168.1.100")
        
        submitted = st.form_submit_button("Register Device", type="primary")
        
        if submitted:
            if not device_id or not device_name or not device_type:
                error_box("Please fill in all required fields (marked with *)")
            else:
                device_data = {
                    "device_id": device_id,
                    "device_name": device_name,
                    "device_type": device_type,
                    "location": location or "Unknown",
                    "metadata": {}
                }
                
                if firmware_version:
                    device_data["metadata"]["firmware_version"] = firmware_version
                if ip_address:
                    device_data["metadata"]["ip_address"] = ip_address
                
                result = api_client.register_device(device_data)
                
                if result:
                    success_box(f"Device {device_id} registered successfully!")
                    st.balloons()
                else:
                    error_box("Failed to register device. It may already exist.")

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh", key="devices_refresh"):
    import time
    time.sleep(5)
    st.rerun()
