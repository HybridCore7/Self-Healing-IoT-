"""
Premium Hardware Dashboard — dashboard_hardware.py
=============================================
Streamlit dashboard matching "Anomaly Insights" aesthetic.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime, timedelta

# Configure page
st.set_page_config(page_title="Anomaly Insights", page_icon="🔍", layout="wide")

# CSS and styling to match the reference image
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0d1117; color: #c9d1d9; }

/* Custom Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 4px 4px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
    color: #8b949e;
    font-size: 1.1rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
}

/* Panel Containers */
.panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.panel-header {
    color: #c9d1d9;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.number-badge {
    background: #eab308;
    color: #000;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: bold;
}

/* Table Styles */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.custom-table th {
    text-align: left;
    padding: 12px;
    border-bottom: 1px solid #30363d;
    color: #8b949e;
    font-weight: 500;
}
.custom-table td {
    padding: 12px;
    border-bottom: 1px solid #21262d;
    color: #c9d1d9;
}
.pill-green {
    background: #238636;
    color: #ffffff;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    display: inline-block;
    text-align: center;
    min-width: 80px;
}
.pill-cyan {
    background: #06b6d4;
    color: #ffffff;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    display: inline-block;
    text-align: center;
    min-width: 80px;
}
</style>
""", unsafe_allow_html=True)

API_BASE = "http://localhost:8000/api"

def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=0.5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def api_put(path, body):
    try:
        r = requests.put(f"{API_BASE}{path}", json=body, timeout=3)
        return r.json(), r.status_code in [200, 201]
    except:
        return None, False

# ── Top Bar ──
colA, colB = st.columns([1, 3])
colA.markdown("<h2 style='margin:0; padding:0; color:white;'>Logs Console</h2>", unsafe_allow_html=True)
colB.markdown("""
<div style='display:flex; align-items:center; gap:12px; height:100%;'>
    <span style='background:#3b82f6; color:white; padding:4px 20px; border-radius:20px; font-weight:bold; letter-spacing:0.5px;'>Self Healing IoT System</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Active Filters
st.markdown("""
<div style='background:#161b22; padding:8px 16px; border-radius:8px; border:1px solid #30363d; display:flex; align-items:center; gap:12px; margin-bottom: 24px;'>
    <span style='color:#8b949e;'>Active Filters</span>
    <span style='background:#3b82f6; color:white; padding:2px 12px; border-radius:12px; font-size:0.8rem;'>app_name:IoT_Nodes ✕</span>
</div>
""", unsafe_allow_html=True)

# Fetch Data
devices_data = api_get("/hardware/devices")
devices = devices_data.get("devices", []) if isinstance(devices_data, dict) else []
if not devices:
    devices = api_get("/devices/")
    
if not devices:
    # Inject temporary offline placeholders if no devices exist
    devices = [
        {"device_id": "node_1", "device_name": "Gateway Node", "metadata": {"role": "Parent Node"}, "status": "offline"},
        {"device_id": "node_2", "device_name": "Sensor Alpha", "metadata": {"role": "Child Node"}, "status": "offline"},
        {"device_id": "node_3", "device_name": "Sensor Beta", "metadata": {"role": "Child Node"}, "status": "offline"}
    ]

# Gather telemetry for all devices to build the views
all_telemetry = []
for d in devices:
    t_data = api_get(f"/telemetry/{d['device_id']}?limit=200")
    if t_data:
        for row in t_data:
            row['device_name'] = d.get('device_name', d['device_id'])
        all_telemetry.extend(t_data)

df = pd.DataFrame(all_telemetry)
if not df.empty and 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs(["Anomaly", "Explore Logs", "Insights", "Network Topology"])

with tab1: # "Anomaly" Tab (Matching the Screenshot)
    col1, col2, col3 = st.columns(3)
    
    # 1. Anomaly Count (Bar Chart)
    with col1:
        st.markdown("<div class='panel'><div class='panel-header'><span class='number-badge'>1</span> Anomaly Count</div>", unsafe_allow_html=True)
        fig1 = go.Figure()
        if not df.empty and 'is_anomaly' in df.columns:
            anom_df = df[df['is_anomaly'] == 1].copy()
            if not anom_df.empty:
                # Group by hour/day
                anom_df['time_bin'] = anom_df['timestamp'].dt.floor('H')
                counts = anom_df.groupby('time_bin').size().reset_index(name='count')
                fig1.add_trace(go.Bar(
                    x=counts['time_bin'], y=counts['count'],
                    marker_color='#f59e0b' # Orange
                ))
        
        fig1.update_layout(
            template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0), height=250,
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='#30363d', zeroline=False)
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 2. Confidence Distribution (Donut Chart)
    with col2:
        st.markdown("<div class='panel'><div class='panel-header'><span class='number-badge'>2</span> Reliability Distribution</div>", unsafe_allow_html=True)
        fig2 = go.Figure()
        if not df.empty and 'is_anomaly' in df.columns:
            total = len(df)
            anoms = df['is_anomaly'].sum()
            normal = total - anoms
            fig2.add_trace(go.Pie(
                labels=['Normal', 'Anomaly'],
                values=[normal, anoms],
                hole=0.75,
                marker_colors=['#22c55e', '#ef4444'], # Green and Red
                textinfo='none'
            ))
            fig2.add_annotation(
                text=f"{(normal/total*100):.0f}%" if total > 0 else "0%",
                x=0.5, y=0.5, font_size=24, font_color="white", showarrow=False
            )
        else:
            # Empty state
            fig2.add_trace(go.Pie(labels=['No Data'], values=[1], hole=0.75, marker_colors=['#30363d'], textinfo='none'))
            
        fig2.update_layout(
            template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0), height=250, showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 3. Anomalies in Services (Heatmap/Scatter)
    with col3:
        st.markdown("<div class='panel'><div class='panel-header'><span class='number-badge'>3</span> Anomalies in Nodes</div>", unsafe_allow_html=True)
        fig3 = go.Figure()
        if not df.empty and 'is_anomaly' in df.columns:
            anom_df = df[df['is_anomaly'] == 1]
            if not anom_df.empty:
                fig3.add_trace(go.Scatter(
                    x=anom_df['timestamp'],
                    y=anom_df['device_name'],
                    mode='markers',
                    marker=dict(symbol='square', size=14, color='#06b6d4'), # Cyan blocks
                    hoverinfo='x+y'
                ))
        
        # Add background grid lines for aesthetic
        fig3.update_layout(
            template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0), height=250,
            xaxis=dict(showgrid=True, gridcolor='#30363d'),
            yaxis=dict(showgrid=True, gridcolor='#30363d')
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. Detailed Data Table
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    table_html = """
    <table class='custom-table'>
        <thead>
            <tr>
                <th>Time</th>
                <th><span class='number-badge' style='display:inline-flex;margin-right:8px;'>4</span>Anomaly Id (Node)</th>
                <th>Service Name</th>
                <th>App Name</th>
                <th>Source</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
    """
    
    if not df.empty and 'is_anomaly' in df.columns:
        recent_anoms = df[df['is_anomaly'] == 1].sort_values('timestamp', ascending=False).head(10)
        if recent_anoms.empty:
            table_html += "<tr><td colspan='6' style='text-align:center;'>No recent anomalies found.</td></tr>"
        else:
            for idx, row in recent_anoms.iterrows():
                time_str = row['timestamp'].strftime('%m/%d/%Y, %I:%M:%S %p')
                node_id = row['device_id'].upper()
                service = "AI_Correction" if pd.notnull(row.get('original_value')) else "Sensor_Fault"
                pill_class = "pill-cyan" if service == "AI_Correction" else "pill-green"
                
                table_html += f"""
                <tr>
                    <td>{time_str}</td>
                    <td style='text-decoration:underline; cursor:pointer;'>{node_id}-{row.get('id', '000')}</td>
                    <td><span class='{pill_class}'>{service}</span></td>
                    <td>IOT_NETWORK</td>
                    <td>MQTT</td>
                    <td>1</td>
                </tr>
                """
    else:
        table_html += "<tr><td colspan='6' style='text-align:center;'>Awaiting hardware data...</td></tr>"
        
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)


with tab2: # "Explore Logs" Tab (Our existing Telemetry & AI Corrections graphs)
    st.markdown("### 📈 Live Telemetry & AI Corrections")
    if not devices:
        st.info("Awaiting hardware connections...")
    else:
        chart_tabs = st.tabs([d.get('device_name', d['device_id']) for d in devices])
        for idx, d in enumerate(devices):
            with chart_tabs[idx]:
                if df.empty:
                    st.info("Awaiting hardware data...")
                    continue
                    
                node_df = df[df['device_id'] == d['device_id']]
                if node_df.empty:
                    st.info("No valid telemetry data yet.")
                    continue
                
                fig = go.Figure()
                # Plot Corrected / Normal Line
                fig.add_trace(go.Scatter(
                    x=node_df['timestamp'], y=node_df['sensor_value'],
                    mode='lines+markers', name='AI Processed Signal',
                    line=dict(color='#00f2fe', width=3, shape='spline'),
                    marker=dict(size=6, color='#00f2fe')
                ))
                
                # Plot Original Anomalies
                if 'is_anomaly' in node_df.columns:
                    anom_df = node_df[node_df['is_anomaly'] == 1]
                    if not anom_df.empty and 'original_value' in anom_df.columns:
                        fig.add_trace(go.Scatter(
                            x=anom_df['timestamp'], y=anom_df['original_value'],
                            mode='markers', name='Raw Hardware Fault',
                            marker=dict(color='#ef4444', size=14, symbol='x', line=dict(color='white', width=1))
                        ))
                        for _, row in anom_df.iterrows():
                            if pd.notnull(row.get('original_value')):
                                fig.add_trace(go.Scatter(
                                    x=[row['timestamp'], row['timestamp']],
                                    y=[row['original_value'], row['sensor_value']],
                                    mode='lines', showlegend=False,
                                    line=dict(color='#ef4444', width=2, dash='dash')
                                ))
                
                fig.update_layout(
                    template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=40, b=20), hovermode='x unified',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)

with tab4: # "Network Topology"
    st.markdown("### 🕸️ Assign Topology")
    if devices:
        d_id = st.selectbox("Select Device", [d['device_id'] for d in devices])
        role = st.selectbox("Assign Role", ["Child Node", "Parent Node"])
        if st.button("Update Role"):
            dev_info = next((d for d in devices if d['device_id'] == d_id), {})
            meta = dev_info.get("metadata") or {}
            meta["role"] = role
            api_put(f"/devices/{d_id}", {"metadata": meta})
            st.success("Updated!")
            time.sleep(1)
            st.rerun()

    st.markdown("### Current Layout")
    for d in devices:
        role = d.get('metadata', {}).get('role', 'Child Node') if isinstance(d.get('metadata'), dict) else 'Child Node'
        color = '#00f2fe' if role == 'Parent Node' else '#a855f7'
        st.markdown(f"""
        <div class='panel' style='border-left: 4px solid {color};'>
            <strong>{role}</strong>: {d.get('device_name', d['device_id'])} ({d['device_id']})<br>
            <span style='color:#8b949e'>Status: {d.get('status', 'offline')}</span>
        </div>
        """, unsafe_allow_html=True)
