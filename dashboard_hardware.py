"""
Hardware Devices Page — dashboard_hardware.py
=============================================
Standalone Streamlit page showing real hardware devices discovered via MQTT.
Also allows sending healing commands directly from the browser.

Run:  streamlit run dashboard_hardware.py --server.port 8503
OR:   Access as a tab from dashboard_live.py (linked via multipage)
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

st.set_page_config(
    page_title="Hardware Devices — Self-Healing IoT",
    page_icon="🔌",
    layout="wide",
)

# ── Config ─────────────────────────────────────────
API_BASE = "http://localhost:8000/api"

# ── CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0d1527 100%); color: #e2e8f0; }
section[data-testid="stSidebar"] { background: #0f1729; border-right: 1px solid rgba(99,179,237,0.15); }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

.page-title {
    font-size: 1.9rem; font-weight: 900;
    background: linear-gradient(90deg, #63b3ed, #90cdf4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.page-sub { font-size: 0.85rem; color: #7fb3d3; margin-top: 4px; }

/* Device card */
.device-card {
    background: linear-gradient(135deg, #1a2744, #1e3058);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 14px;
    padding: 18px 20px;
    margin: 8px 0;
    transition: border-color 0.3s;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.83rem;
}
.device-card:hover { border-color: rgba(99,179,237,0.5); }
.device-online  { border-left: 4px solid #48bb78; }
.device-offline { border-left: 4px solid #718096; opacity: 0.65; }
.device-healing { border-left: 4px solid #63b3ed; animation: glow 1.5s infinite; }

@keyframes glow {
    0%,100% { box-shadow: 0 0 0 0 rgba(99,179,237,0.3); }
    50%      { box-shadow: 0 0 12px 3px rgba(99,179,237,0.3); }
}

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-online  { background: rgba(72,187,120,0.15); color: #68d391; border: 1px solid #48bb78; }
.badge-offline { background: rgba(113,128,150,0.15); color: #a0aec0; border: 1px solid #718096; }
.badge-esp32   { background: rgba(99,179,237,0.12); color: #90cdf4; border: 1px solid #63b3ed; }
.badge-arduino { background: rgba(72,187,120,0.12); color: #9ae6b4; border: 1px solid #48bb78; }
.badge-raspberry_pi { background: rgba(246,173,85,0.12); color: #f6e05e; border: 1px solid #f6ad55; }
.badge-unknown { background: rgba(113,128,150,0.12); color: #a0aec0; border: 1px solid #718096; }

.section-head {
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 2px;
    color: #63b3ed; margin: 20px 0 8px 0;
    border-bottom: 1px solid rgba(99,179,237,0.12);
    padding-bottom: 4px;
}
.cmd-log {
    background: rgba(10,14,26,0.8);
    border: 1px solid rgba(99,179,237,0.1);
    border-radius: 8px;
    padding: 12px 16px;
    font-family: JetBrains Mono, monospace;
    font-size: 0.78rem;
    max-height: 260px;
    overflow-y: auto;
    color: #7fb3d3;
}
.log-entry { padding: 3px 0; border-bottom: 1px solid rgba(99,179,237,0.05); }
.log-ok    { color: #68d391; }
.log-fail  { color: #fc8181; }
</style>
""", unsafe_allow_html=True)

# ── Helper: call backend API ────────────────────────
def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        if r.status_code == 200:
            return r.json(), None
        return None, f"HTTP {r.status_code}: {r.text}"
    except requests.exceptions.ConnectionError:
        return None, "Backend not reachable. Start with: python -m src.backend.main"
    except Exception as e:
        return None, str(e)

def api_post(path: str, body: dict = None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=body or {}, timeout=5)
        return r.json(), r.status_code == 200
    except requests.exceptions.ConnectionError:
        return {"error": "Backend not reachable"}, False
    except Exception as e:
        return {"error": str(e)}, False

# ── Device type icons ───────────────────────────────
DEVICE_ICONS = {
    "esp32":        "⚡",
    "arduino":      "🟢",
    "raspberry_pi": "🍓",
    "unknown":      "📟",
}

# ══════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════
st.markdown("""
<div style='background:linear-gradient(135deg,#1a365d,#153e75);
            border:1px solid rgba(99,179,237,0.3);border-radius:14px;
            padding:20px 28px;margin-bottom:20px;'>
    <p class="page-title">🔌 Hardware Device Manager</p>
    <p class="page-sub">
        Auto-Discovery · Real-time Status · Remote Healing Commands
        &nbsp;|&nbsp; Supports: ESP32 · Arduino · Raspberry Pi · Any MQTT Device
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔌 Hardware Monitor")
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
    st.markdown("---")
    st.markdown("### 🌐 Connection")
    api_url = st.text_input("Backend URL", value=API_BASE)
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.78rem;color:#7fb3d3;'>
    <b>How devices appear:</b><br><br>
    1. Flash ESP32 with <code>hardware/esp32/esp32_sensor_node.ino</code><br><br>
    2. Set your PC's IP as <code>MQTT_BROKER</code> in the .ino file<br><br>
    3. Start Mosquitto MQTT broker<br><br>
    4. Device appears here within 10 seconds ✅
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# FETCH DATA
# ══════════════════════════════════════════════════════
devices_data, err = api_get("/hardware/devices")
cmd_log_data, _   = api_get("/hardware/commands/log?limit=20")

# ── Simulated devices when backend is offline ────────
if err or not devices_data:
    st.warning(f"⚠️ Backend offline: {err}\n\nShowing demo data — start the backend to see real devices.")
    devices_data = {
        "devices": [
            {"device_id": "esp32_node_01", "device_name": "ESP32 Living Room",
             "device_type": "esp32", "location": "living_room", "status": "online",
             "ip": "192.168.1.42", "mac": "AA:BB:CC:DD:EE:01", "rssi": -55,
             "uptime_ms": 3600000, "seconds_since_seen": 3},
            {"device_id": "arduino_node_01", "device_name": "Arduino Garage",
             "device_type": "arduino", "location": "garage", "status": "online",
             "seconds_since_seen": 8},
            {"device_id": "rpi_node_01", "device_name": "Raspberry Pi Roof",
             "device_type": "raspberry_pi", "location": "roof", "status": "offline",
             "seconds_since_seen": 120},
        ],
        "stats": {"total": 3, "online": 2, "offline": 1}
    }

devices = devices_data.get("devices", [])
stats   = devices_data.get("stats", {})

# ══════════════════════════════════════════════════════
# KPI ROW
# ══════════════════════════════════════════════════════
k1, k2, k3, k4 = st.columns(4)
with k1: st.metric("📟 Total Devices",   stats.get("total", 0))
with k2: st.metric("🟢 Online",          stats.get("online", 0))
with k3: st.metric("⚫ Offline",         stats.get("offline", 0))
with k4: st.metric("🕐 Last Refresh",    datetime.now().strftime("%H:%M:%S"))

st.markdown("---")

# ══════════════════════════════════════════════════════
# DEVICE CARDS + COMMAND PANEL
# ══════════════════════════════════════════════════════
if not devices:
    st.info("🔍 No hardware devices discovered yet.\n\n"
            "Connect an ESP32 to your WiFi and start Mosquitto — "
            "the device will appear here automatically.")
else:
    left, right = st.columns([3, 2], gap="large")

    # ── Device Cards ─────────────────────────────────
    with left:
        st.markdown('<div class="section-head">📡 Discovered Devices</div>',
                    unsafe_allow_html=True)

        for dev in devices:
            did      = dev["device_id"]
            dtype    = dev.get("device_type", "unknown")
            status   = dev.get("status", "unknown")
            icon     = DEVICE_ICONS.get(dtype, "📟")
            css_cls  = "device-online" if status == "online" else "device-offline"
            badge_s  = f'<span class="badge badge-{status}">{status.upper()}</span>'
            badge_t  = f'<span class="badge badge-{dtype}">{dtype}</span>'

            uptime_ms = dev.get("uptime_ms", 0)
            if uptime_ms:
                h = uptime_ms // 3600000
                m = (uptime_ms % 3600000) // 60000
                uptime_str = f"{h}h {m}m"
            else:
                secs = dev.get("seconds_since_seen", 0)
                uptime_str = f"seen {int(secs)}s ago"

            rssi_str = f"{dev.get('rssi', '–')} dBm" if dev.get("rssi") else "N/A"
            ip_str   = dev.get("ip", "–")

            st.markdown(f"""
            <div class="device-card {css_cls}">
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <span style='font-size:1.1rem;font-weight:700;color:#bee3f8;'>
                        {icon} {dev.get("device_name", did)}
                    </span>
                    <div>{badge_s} &nbsp; {badge_t}</div>
                </div>
                <div style='margin-top:8px;color:#a0aec0;line-height:1.9;'>
                    <b style='color:#7fb3d3;'>ID:</b> {did} &nbsp;|&nbsp;
                    <b style='color:#7fb3d3;'>Location:</b> {dev.get("location","–")}<br>
                    <b style='color:#7fb3d3;'>IP:</b> {ip_str} &nbsp;|&nbsp;
                    <b style='color:#7fb3d3;'>MAC:</b> {dev.get("mac","–")}<br>
                    <b style='color:#7fb3d3;'>Signal:</b> {rssi_str} &nbsp;|&nbsp;
                    <b style='color:#7fb3d3;'>Uptime:</b> {uptime_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Command Panel ─────────────────────────────────
    with right:
        st.markdown('<div class="section-head">🔧 Send Healing Command</div>',
                    unsafe_allow_html=True)

        device_ids = [d["device_id"] for d in devices]
        if device_ids:
            selected_device = st.selectbox("Select Device", device_ids)
            selected_info   = next((d for d in devices if d["device_id"] == selected_device), {})
            dtype_auto      = selected_info.get("device_type", "unknown")

            command = st.selectbox("Command", [
                "ping         — Check if device is alive",
                "recalibrate  — Re-read sensor baseline (drift fix)",
                "validate     — Send 5 rapid readings for AI check",
                "reset        — Full hardware restart",
                "increase_frequency — Monitor more closely",
            ])
            cmd_key   = command.split()[0]
            cmd_notes = st.text_input("Notes (optional)", placeholder="e.g. Sensor drift detected")

            col_send, col_heal = st.columns(2)

            with col_send:
                if st.button("📤 Send Command", use_container_width=True, type="primary"):
                    resp, ok = api_post(
                        f"/hardware/command/{selected_device}",
                        {"command": cmd_key, "reason": cmd_notes or "manual"}
                    )
                    if ok:
                        st.success(f"✅ `{cmd_key}` sent to `{selected_device}`")
                    else:
                        st.error(f"❌ Failed: {resp.get('detail', resp)}")

            with col_heal:
                if st.button("🛠️ AI Heal", use_container_width=True):
                    fault = st.session_state.get("fault_type_sel", "sensor_drift")
                    resp, ok = api_post(
                        f"/hardware/heal/{selected_device}",
                        {"fault_type": fault, "device_type": dtype_auto}
                    )
                    if ok:
                        st.success(f"✅ Healing: `{resp.get('command_sent')}` dispatched")
                    else:
                        st.error(f"❌ {resp.get('detail', resp)}")

            st.markdown('<div class="section-head">🎯 AI Heal by Fault Type</div>',
                        unsafe_allow_html=True)
            fault_type = st.selectbox("Fault Type", [
                "sensor_drift", "stuck_sensor", "data_spike",
                "offline", "noise", "frozen"
            ], key="fault_type_sel")

            st.markdown(f"""
            <div style='background:rgba(26,39,68,0.6);border-radius:8px;
                        padding:10px 14px;font-family:JetBrains Mono;
                        font-size:0.78rem;color:#7fb3d3;'>
            <b style='color:#bee3f8;'>Device:</b> {selected_device}<br>
            <b style='color:#bee3f8;'>Type:</b>   {dtype_auto}<br>
            <b style='color:#bee3f8;'>Fault:</b>  {fault_type}<br>
            <b style='color:#bee3f8;'>Status:</b> {"🟢 Online" if selected_info.get("status") == "online" else "⚫ Offline"}
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# COMMAND LOG
# ══════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-head">📋 Recent Healing Commands</div>',
            unsafe_allow_html=True)

if cmd_log_data and cmd_log_data.get("commands"):
    cmds  = cmd_log_data["commands"]
    cstats = cmd_log_data.get("stats", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Commands",  cstats.get("total_commands", 0))
    with c2: st.metric("✅ Successful",   cstats.get("successful", 0))
    with c3: st.metric("❌ Failed",       cstats.get("failed", 0))
    with c4: st.metric("Success Rate",   f"{cstats.get('success_rate', 100):.1f}%")

    log_html = '<div class="cmd-log">'
    for cmd in reversed(cmds):
        ok  = cmd.get("success", False)
        cls = "log-ok" if ok else "log-fail"
        icon = "✅" if ok else "❌"
        log_html += (
            f'<div class="log-entry {cls}">'
            f'{icon} [{cmd.get("timestamp","")[:19]}] '
            f'<b>{cmd.get("device_id","")}</b> → '
            f'<b>{cmd.get("command","")}</b> '
            f'({cmd.get("reason","")})'
            f'</div>'
        )
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
else:
    st.markdown('<div style="color:#7fb3d3;font-size:0.85rem;">'
                'No commands sent yet. Send a command above to see the log.</div>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SETUP GUIDE
# ══════════════════════════════════════════════════════
st.markdown("---")
with st.expander("📖 Hardware Setup Guide — ESP32, Arduino, Raspberry Pi"):
    st.markdown("""
    ## ESP32 Setup (Recommended — Cheapest WiFi Node)

    **Hardware needed:** ESP32 DevKit (~$3-5), DHT22 sensor (~$2), jumper wires

    1. **Install Arduino IDE** → Add ESP32 board:
       `File → Preferences → Board Manager URL:`
       `https://dl.espressif.com/dl/package_esp32_index.json`

    2. **Install libraries** (Sketch → Manage Libraries):
       - `PubSubClient` by Nick O'Leary
       - `ArduinoJson` by Benoit Blanchon
       - `DHT sensor library` by Adafruit

    3. **Wire DHT22 to ESP32:**
       ```
       DHT22 VCC  → ESP32 3.3V
       DHT22 DATA → ESP32 GPIO4
       DHT22 GND  → ESP32 GND
       ```

    4. **Flash the firmware:**
       Open `hardware/esp32/esp32_sensor_node.ino`
       Change: `WIFI_SSID`, `WIFI_PASSWORD`, `MQTT_BROKER` (your PC's IP)
       Select Board: `ESP32 Dev Module` → Upload

    5. **Start MQTT broker on your PC:**
       ```bash
       # Install: https://mosquitto.org/download/
       mosquitto -v
       ```

    6. **Device appears in this dashboard automatically! ✅**

    ---
    ## Arduino + Raspberry Pi Setup

    1. Flash `hardware/arduino/arduino_sensor.ino` to Arduino
    2. Connect Arduino USB → Raspberry Pi USB
    3. On Raspberry Pi run:
       ```bash
       pip3 install paho-mqtt pyserial
       python3 hardware/raspberry_pi/pi_serial_bridge.py \\
           --port /dev/ttyUSB0 \\
           --broker <your-pc-ip>
       ```

    ---
    ## Network Requirements
    - All devices must be on the **same WiFi network** as your PC
    - MQTT broker (Mosquitto) must be running on your PC
    - Check your **firewall** allows port 1883 (TCP)
    """)

# ── Auto-refresh ────────────────────────────────────
if auto_refresh:
    time.sleep(5)
    st.rerun()
