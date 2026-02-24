"""
Self-Healing IoT Network — Live Dashboard
==========================================
Standalone Streamlit dashboard with built-in simulation.
No backend server or MQTT required.

Run with:
    streamlit run dashboard_live.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random
import math
import time
from collections import deque
from datetime import datetime
from typing import Dict, List

# ──────────────────────────────────────────────
# Page Config (must be first Streamlit call)
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Self-Healing IoT Network — Live",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Premium Dark Theme CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1527 50%, #0a1020 100%);
    color: #e2e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1729 0%, #0a1020 100%);
    border-right: 1px solid rgba(99,179,237,0.15);
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Header banner */
.hero-header {
    background: linear-gradient(135deg, #1a365d 0%, #153e75 40%, #1a4e8a 100%);
    border: 1px solid rgba(99,179,237,0.3);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
}
.hero-title {
    font-size: 2.1rem;
    font-weight: 900;
    background: linear-gradient(90deg, #63b3ed, #90cdf4, #bee3f8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: 0.9rem;
    color: #7fb3d3;
    margin-top: 4px;
    font-weight: 400;
}

/* Metric cards */
.kpi-card {
    background: linear-gradient(135deg, #1a2744 0%, #1e3058 100%);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 12px;
    padding: 18px 20px;
    margin: 4px 0;
    transition: border-color 0.3s;
}
.kpi-card:hover { border-color: rgba(99,179,237,0.5); }
.kpi-label { font-size: 0.72rem; color: #7fb3d3; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.kpi-value { font-size: 2rem; font-weight: 800; color: #bee3f8; line-height: 1.1; font-family: 'JetBrains Mono', monospace; }
.kpi-delta { font-size: 0.78rem; margin-top: 2px; }

/* Node cards */
.node-card {
    border-radius: 12px;
    padding: 14px 16px;
    margin: 6px 0;
    border: 1px solid;
    transition: all 0.3s;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
}
.node-healthy  { background: rgba(72,187,120,0.08); border-color: rgba(72,187,120,0.35); }
.node-anomaly  { background: rgba(237,137,54,0.10); border-color: rgba(237,137,54,0.45); }
.node-fault    { background: rgba(245,101,101,0.10); border-color: rgba(245,101,101,0.45); animation: pulse 1.2s infinite; }
.node-healed   { background: rgba(99,179,237,0.08); border-color: rgba(99,179,237,0.35); }
.node-offline  { background: rgba(100,100,120,0.08); border-color: rgba(100,100,120,0.25); }

@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(245,101,101,0.4); }
    70%  { box-shadow: 0 0 0 8px rgba(245,101,101,0); }
    100% { box-shadow: 0 0 0 0 rgba(245,101,101,0); }
}

/* Event log */
.event-item {
    padding: 8px 12px;
    border-radius: 8px;
    margin: 4px 0;
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    border-left: 3px solid;
}
.ev-normal  { background: rgba(72,187,120,0.07); border-color: #48bb78; color: #9ae6b4; }
.ev-anomaly { background: rgba(237,137,54,0.08); border-color: #ed8936; color: #fbd38d; }
.ev-fault   { background: rgba(245,101,101,0.08); border-color: #f56565; color: #feb2b2; }
.ev-heal    { background: rgba(99,179,237,0.08); border-color: #63b3ed; color: #bee3f8; }

/* Section headings */
.section-head {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #63b3ed;
    margin: 16px 0 8px 0;
    border-bottom: 1px solid rgba(99,179,237,0.15);
    padding-bottom: 4px;
}

/* Override streamlit metric */
[data-testid="metric-container"] {
    background: #1a2744;
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="stMetricValue"] { color: #bee3f8 !important; font-family: 'JetBrains Mono', monospace; }
[data-testid="stMetricLabel"] { color: #7fb3d3 !important; }
[data-testid="stMetricDelta"] { color: #68d391 !important; }

/* Plotly charts background */
.js-plotly-plot { border-radius: 12px; overflow: hidden; }

/* Scrollable event log */
.event-log-container { max-height: 340px; overflow-y: auto; }

/* Trust bar */
.trust-bar-wrap { width: 100%; background: #1a2744; border-radius: 4px; height: 6px; margin-top: 4px; }
.trust-bar-fill { height: 6px; border-radius: 4px; transition: width 0.5s; }

/* Divider */
hr { border-color: rgba(99,179,237,0.1) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# SIMULATION ENGINE
# ══════════════════════════════════════════════
WINDOW_N        = 20
Z_THRESHOLD     = 3.0
CONSENSUS_DELTA = 5.0
ALPHA_TRUST     = 0.7
MAX_HISTORY     = 60  # data points kept per node


class SimNode:
    """Single distributed AI node state — paper equations (1-6)."""

    COLORS = {
        "healthy": "#48bb78",
        "anomaly": "#ed8936",
        "fault":   "#f56565",
        "healed":  "#63b3ed",
        "offline": "#718096",
    }

    def __init__(self, node_id: str, base: float, fault_start: int, fault_end: int,
                 fault_type: str, fault_mag: float = 20.0, offline_steps: list = None):
        self.node_id     = node_id
        self.base        = base
        self.fault_start = fault_start
        self.fault_end   = fault_end
        self.fault_type  = fault_type   # "drift" | "stuck" | "offline" | "noise"
        self.fault_mag   = fault_mag
        self.offline_steps = offline_steps or []

        # AI state
        self.history: deque = deque(maxlen=WINDOW_N)
        self.trust: float   = 1.0
        self.step: int      = 0

        # Timeseries for plotting
        self.ts_steps:    List[int]   = []
        self.ts_values:   List[float] = []
        self.ts_z:        List[float] = []
        self.ts_trust:    List[float] = []
        self.ts_status:   List[str]   = []

        # Counters
        self.anomaly_count = 0
        self.heal_count    = 0
        self.status        = "healthy"
        self.last_value    = base
        self.last_z        = 0.0

    # ── Paper equations ──────────────────────────
    def mu(self) -> float:
        if not self.history: return self.base
        return sum(self.history) / len(self.history)

    def sigma(self) -> float:
        if len(self.history) < 2: return 0.0
        m = self.mu()
        return math.sqrt(sum((x - m) ** 2 for x in self.history) / len(self.history))

    def z_score(self, v: float) -> float:
        s = self.sigma()
        return (v - self.mu()) / s if s > 1e-9 else 0.0

    def update_trust(self, consensus_score: float):
        self.trust = ALPHA_TRUST * self.trust + (1 - ALPHA_TRUST) * consensus_score
        self.trust = max(0.0, min(1.0, self.trust))

    # ── Sense ──────────────────────────────────
    def sense(self, step: int) -> float:
        self.step = step
        if step in self.offline_steps:
            self.status = "offline"
            return None

        v = self.base + random.gauss(0, 0.4)
        if self.fault_start <= step <= self.fault_end:
            if self.fault_type == "drift":
                v += self.fault_mag * random.uniform(0.9, 1.1)
            elif self.fault_type == "stuck":
                v = self.fault_mag
            elif self.fault_type == "noise":
                v += random.gauss(0, self.fault_mag)
        return round(v, 2)


def build_network():
    """Create 6 IoT nodes with scheduled faults."""
    return {
        "Node-A": SimNode("Node-A", base=24.0, fault_start=999, fault_end=999,
                          fault_type="none"),
        "Node-B": SimNode("Node-B", base=25.5, fault_start=12, fault_end=22,
                          fault_type="drift", fault_mag=18.0),
        "Node-C": SimNode("Node-C", base=23.5, fault_start=999, fault_end=999,
                          fault_type="none"),
        "Node-D": SimNode("Node-D", base=26.0, fault_start=28, fault_end=38,
                          fault_type="stuck", fault_mag=99.9),
        "Node-E": SimNode("Node-E", base=25.0, fault_start=999, fault_end=999,
                          fault_type="noise", offline_steps=list(range(18, 24))),
        "Node-F": SimNode("Node-F", base=24.5, fault_start=999, fault_end=999,
                          fault_type="none"),
    }


def simulate_step(nodes: dict, step: int, events: list):
    """One tick of the distributed AI algorithm."""
    readings = {}

    # Phase 1: Sense
    for nid, node in nodes.items():
        readings[nid] = node.sense(step)

    # Phase 2: Local Z-score anomaly detection + consensus
    for nid, node in nodes.items():
        val = readings[nid]
        if val is None:
            node.status = "offline"
            node.ts_steps.append(step)
            node.ts_values.append(None)
            node.ts_z.append(0.0)
            node.ts_trust.append(node.trust)
            node.ts_status.append("offline")
            continue

        node.history.append(val)
        z = node.z_score(val)
        node.last_value = val
        node.last_z = z

        # Local anomaly?
        local_anomaly = abs(z) > Z_THRESHOLD

        if not local_anomaly:
            node.update_trust(1.0)
            node.status = "healthy"
            node.ts_steps.append(step)
            node.ts_values.append(val)
            node.ts_z.append(z)
            node.ts_trust.append(node.trust)
            node.ts_status.append("healthy")
            continue

        # Anomaly detected — request neighbor consensus
        neighbor_vals = [readings[n] for n in readings
                         if n != nid and readings[n] is not None]

        if not neighbor_vals:
            node.status = "anomaly"
        else:
            neighbor_mean = sum(neighbor_vals) / len(neighbor_vals)
            deviation = abs(val - neighbor_mean)          # Eq. (5)
            consensus_score = max(0.0, 1.0 - deviation / (CONSENSUS_DELTA * 2))

            fault_confirmed = deviation > CONSENSUS_DELTA

            # Update trust (Eq. 6)
            node.update_trust(consensus_score)

            if fault_confirmed:
                node.status = "fault"
                node.anomaly_count += 1

                # Self-heal: replace with neighbor interpolation
                corrected = neighbor_mean
                if len(node.history) >= 3:
                    for _ in range(3):
                        node.history.pop()
                node.history.append(corrected)
                node.heal_count += 1
                node.status = "healed"

                events.append({
                    "step": step, "node": nid, "type": "fault",
                    "detail": f"Z={z:.2f} D={deviation:.2f} → Healed to {corrected:.2f}°C",
                    "ts": datetime.now().strftime("%H:%M:%S"),
                })
            else:
                node.status = "anomaly"
                events.append({
                    "step": step, "node": nid, "type": "anomaly",
                    "detail": f"Z={z:.2f} — not confirmed by neighbors",
                    "ts": datetime.now().strftime("%H:%M:%S"),
                })

        node.ts_steps.append(step)
        node.ts_values.append(val)
        node.ts_z.append(z)
        node.ts_trust.append(node.trust)
        node.ts_status.append(node.status)


# ══════════════════════════════════════════════
# CHART BUILDERS
# ══════════════════════════════════════════════
PLOT_BG   = "rgba(10,14,26,0)"
GRID_CLR  = "rgba(99,179,237,0.08)"
FONT_CLR  = "#7fb3d3"
STATUS_CLR = {
    "healthy": "#48bb78",
    "anomaly": "#ed8936",
    "fault":   "#f56565",
    "healed":  "#63b3ed",
    "offline": "#718096",
}
NODE_LINE_COLORS = ["#63b3ed", "#ed8936", "#68d391", "#fc8181",
                    "#b794f4", "#f6ad55"]

# Base layout — NO legend/xaxis/yaxis keys so charts can extend without duplicate-kwarg errors
LAYOUT_BASE = dict(
    paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
    font=dict(family="Inter, JetBrains Mono", color=FONT_CLR, size=11),
    margin=dict(l=40, r=20, t=36, b=36),
)

# Default legend style — merge manually per chart
LEGEND_DEFAULT = dict(
    bgcolor="rgba(0,0,0,0)",
    bordercolor="rgba(99,179,237,0.2)",
    borderwidth=1,
    font=dict(size=10),
)

# Default axis style — apply via update_xaxes / update_yaxes per chart
AXIS_STYLE = dict(gridcolor=GRID_CLR, linecolor="rgba(99,179,237,0.15)",
                  tickfont=dict(size=10))


def _apply_axes(fig):
    """Apply default axis + legend styles. Avoids LAYOUT_BASE duplicate-kwarg clash."""
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    fig.update_layout(legend=LEGEND_DEFAULT)
    return fig


def chart_sensor_readings(nodes: dict) -> go.Figure:
    fig = go.Figure()
    for i, (nid, node) in enumerate(nodes.items()):
        steps = node.ts_steps[-MAX_HISTORY:]
        vals  = node.ts_values[-MAX_HISTORY:]
        clr   = NODE_LINE_COLORS[i % len(NODE_LINE_COLORS)]

        clean_vals = [v if v is not None else None for v in vals]
        fig.add_trace(go.Scatter(
            x=steps, y=clean_vals,
            name=nid, mode="lines+markers",
            line=dict(color=clr, width=2),
            marker=dict(size=4, color=clr),
            connectgaps=False,
            hovertemplate=f"<b>{nid}</b><br>Step: %{{x}}<br>Temp: %{{y:.2f}}°C<extra></extra>",
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="📡 Live Sensor Readings", font=dict(color="#bee3f8", size=13)),
        yaxis_title="Temperature (°C)",
        xaxis_title="Simulation Step",
        height=280,
    )
    _apply_axes(fig)
    return fig


def chart_z_scores(nodes: dict) -> go.Figure:
    fig = go.Figure()

    # Threshold bands
    fig.add_hrect(y0=Z_THRESHOLD, y1=12, fillcolor="rgba(245,101,101,0.06)",
                  line_width=0, annotation_text="Anomaly Zone", annotation_position="top right",
                  annotation_font=dict(color="#f56565", size=9))
    fig.add_hrect(y0=-12, y1=-Z_THRESHOLD, fillcolor="rgba(245,101,101,0.06)", line_width=0)
    fig.add_hline(y=Z_THRESHOLD,  line=dict(color="#f56565", dash="dash", width=1))
    fig.add_hline(y=-Z_THRESHOLD, line=dict(color="#f56565", dash="dash", width=1))
    fig.add_hline(y=0, line=dict(color="rgba(99,179,237,0.3)", width=1))

    for i, (nid, node) in enumerate(nodes.items()):
        clr  = NODE_LINE_COLORS[i % len(NODE_LINE_COLORS)]
        steps = node.ts_steps[-MAX_HISTORY:]
        zs    = node.ts_z[-MAX_HISTORY:]
        fig.add_trace(go.Scatter(
            x=steps, y=zs, name=nid, mode="lines",
            line=dict(color=clr, width=1.5),
            hovertemplate=f"<b>{nid}</b><br>Z = %{{y:.3f}}<extra></extra>",
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="📐 Z-Score Monitor  (|Z| > 3.0 = Anomaly)", font=dict(color="#bee3f8", size=13)),
        yaxis_title="Z-Score",
        xaxis_title="Step",
        height=250,
    )
    _apply_axes(fig)
    fig.update_yaxes(range=[-8, 14])
    return fig


def chart_trust_scores(nodes: dict) -> go.Figure:
    nids   = list(nodes.keys())
    trusts = [nodes[n].trust for n in nids]
    colors = []
    for t in trusts:
        if t >= 0.7:   colors.append("#48bb78")
        elif t >= 0.4: colors.append("#ed8936")
        else:          colors.append("#f56565")

    fig = go.Figure(go.Bar(
        x=nids, y=trusts,
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
        text=[f"{t:.3f}" for t in trusts],
        textposition="outside",
        textfont=dict(color="#bee3f8", size=11, family="JetBrains Mono"),
        hovertemplate="<b>%{x}</b><br>Trust: %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=0.4, line=dict(color="#f56565", dash="dash", width=1),
                  annotation_text="Untrusted threshold",
                  annotation_font=dict(color="#f56565", size=9))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="🔐 Trust Scores  T_i(t+1) = αT_i(t) + (1-α)C_i", font=dict(color="#bee3f8", size=13)),
        height=250,
    )
    _apply_axes(fig)
    fig.update_yaxes(range=[0, 1.15])
    return fig


def chart_consensus_deviation(nodes: dict, readings: dict) -> go.Figure:
    nids = [n for n in nodes if readings.get(n) is not None]
    online_vals = [readings[n] for n in nids]
    deviations  = []

    if len(online_vals) >= 2:
        global_mean = sum(online_vals) / len(online_vals)
        deviations = [abs(v - global_mean) for v in online_vals]
    else:
        deviations = [0.0] * len(nids)

    colors = ["#f56565" if d > CONSENSUS_DELTA else "#63b3ed" for d in deviations]

    fig = go.Figure(go.Bar(
        x=nids, y=deviations,
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
        text=[f"{d:.2f}" for d in deviations],
        textposition="outside",
        textfont=dict(color="#bee3f8", size=10, family="JetBrains Mono"),
        hovertemplate="<b>%{x}</b><br>D_i = %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=CONSENSUS_DELTA, line=dict(color="#f56565", dash="dash", width=1.5),
                  annotation_text=f"Fault threshold δ={CONSENSUS_DELTA}",
                  annotation_font=dict(color="#f56565", size=9))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="🗳️  Consensus Deviation  D_i = |S_i - (1/M)ΣS_j|", font=dict(color="#bee3f8", size=13)),
        yaxis_title="Deviation (°C)",
        height=250,
    )
    _apply_axes(fig)
    return fig


def chart_network_topology(nodes: dict, readings: dict) -> go.Figure:
    """Animated network topology as interactive node graph."""
    # Circular layout
    n = len(nodes)
    labels = list(nodes.keys())
    angles = [2 * math.pi * i / n for i in range(n)]
    xs = [math.cos(a) for a in angles]
    ys = [math.sin(a) for a in angles]

    # Draw edges (mesh connections)
    edge_x, edge_y = [], []
    for i in range(n):
        for j in range(i + 1, n):
            edge_x += [xs[i], xs[j], None]
            edge_y += [ys[i], ys[j], None]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(99,179,237,0.12)", width=1.5),
        hoverinfo="none", showlegend=False,
    ))

    # Nodes
    node_colors   = []
    node_sizes    = []
    node_texts    = []
    node_hovers   = []

    for label, node in nodes.items():
        s = node.status
        clr = STATUS_CLR.get(s, "#718096")
        node_colors.append(clr)
        node_sizes.append(45 if s in ("fault", "anomaly") else 35)

        val = node.last_value if node.last_value is not None else "–"
        node_texts.append(f"<b>{label}</b><br>{val}°C" if val != "–" else f"<b>{label}</b><br>OFFLINE")
        node_hovers.append(
            f"<b>{label}</b><br>"
            f"Status: {s.upper()}<br>"
            f"Value: {node.last_value:.2f}°C<br>"
            f"Z-Score: {node.last_z:.3f}<br>"
            f"Trust: {node.trust:.3f}<br>"
            f"Anomalies: {node.anomaly_count}<br>"
            f"Heals: {node.heal_count}"
        )

    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(
            color=node_colors, size=node_sizes,
            line=dict(color="rgba(255,255,255,0.2)", width=2),
            symbol="circle",
        ),
        text=node_texts,
        textposition="middle center",
        textfont=dict(size=9, color="white", family="JetBrains Mono"),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=node_hovers,
        showlegend=False,
    ))

    # Legend
    for status, clr in STATUS_CLR.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=clr, size=10),
            name=status.capitalize(), showlegend=True,
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="🌐 Distributed Mesh Network Topology", font=dict(color="#bee3f8", size=13)),
        height=340,
        showlegend=True,
    )
    fig.update_layout(legend=dict(
        **LEGEND_DEFAULT,
        orientation="h", yanchor="bottom", y=-0.02, x=0.3,
    ))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# ══════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════
if "nodes" not in st.session_state:
    st.session_state.nodes   = build_network()
    st.session_state.step    = 0
    st.session_state.events  = []
    st.session_state.running = False
    st.session_state.speed   = 0.8
    st.session_state.readings = {}

nodes  = st.session_state.nodes
events = st.session_state.events


# ══════════════════════════════════════════════
# SIDEBAR — CONTROLS
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:12px 0;'>
        <div style='font-size:2.5rem;'>🛰️</div>
        <div style='font-size:1rem;font-weight:700;color:#bee3f8;'>Self-Healing IoT</div>
        <div style='font-size:0.72rem;color:#7fb3d3;'>Distributed AI Network</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-head">⚙️ Simulation Controls</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        start_btn = st.button("▶ Start", use_container_width=True, type="primary")
    with col_b:
        stop_btn = st.button("⏹ Stop", use_container_width=True)

    reset_btn = st.button("🔄 Reset Simulation", use_container_width=True)

    speed = st.slider("⚡ Step Speed (s)", min_value=0.1, max_value=2.0,
                      value=st.session_state.speed, step=0.1)
    st.session_state.speed = speed

    st.markdown("---")
    st.markdown('<div class="section-head">🔧 Network Config</div>', unsafe_allow_html=True)
    z_thresh = st.slider("Z-Score Threshold", 1.0, 5.0, Z_THRESHOLD, 0.1)
    c_delta  = st.slider("Consensus Delta δ", 1.0, 20.0, CONSENSUS_DELTA, 0.5)

    st.markdown("---")
    st.markdown('<div class="section-head">📋 Fault Schedule</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.78rem;color:#7fb3d3;line-height:1.8;font-family:JetBrains Mono;'>
    🟡 Node-B: Drift fault (steps 12-22)<br>
    🔴 Node-D: Stuck fault (steps 28-38)<br>
    ⚫ Node-E: Offline (steps 18-23)<br>
    ✅ Others: Normal operation
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-head">📐 Paper Equations</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.75rem;color:#7fb3d3;font-family:JetBrains Mono;line-height:2;'>
    <b style='color:#bee3f8;'>(1)</b> μ_i = (1/N)Σx_i(k)<br>
    <b style='color:#bee3f8;'>(2)</b> σ_i = √(1/N Σ(x-μ)²)<br>
    <b style='color:#bee3f8;'>(3)</b> Z_i = (x_i-μ_i)/σ_i<br>
    <b style='color:#bee3f8;'>(5)</b> D_i = |S_i-(1/M)ΣS_j|<br>
    <b style='color:#bee3f8;'>(6)</b> T_i = αT_i + (1-α)C_i<br>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# HANDLE CONTROLS
# ══════════════════════════════════════════════
if start_btn:
    st.session_state.running = True
if stop_btn:
    st.session_state.running = False
if reset_btn:
    st.session_state.nodes   = build_network()
    st.session_state.step    = 0
    st.session_state.events  = []
    st.session_state.running = False
    st.session_state.readings = {}
    st.rerun()

# Update local refs after possible reset
nodes  = st.session_state.nodes
events = st.session_state.events

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown(f"""
<div class="hero-header">
    <p class="hero-title">🛰️ Self-Healing IoT Network — Live Dashboard</p>
    <p class="hero-subtitle">
        Distributed AI · Z-Score Detection · Consensus Voting · Adaptive Trust Scoring
        &nbsp;|&nbsp; Step: <b style='color:#bee3f8;'>{st.session_state.step}</b>
        &nbsp;|&nbsp; Status: <b style='color:{"#48bb78" if st.session_state.running else "#ed8936"};'>
        {"▶ RUNNING" if st.session_state.running else "⏸ PAUSED"}</b>
    </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# KPI METRICS ROW
# ══════════════════════════════════════════════
total_nodes    = len(nodes)
healthy_count  = sum(1 for n in nodes.values() if n.status == "healthy")
fault_count    = sum(1 for n in nodes.values() if n.status in ("fault", "anomaly"))
offline_count  = sum(1 for n in nodes.values() if n.status == "offline")
total_anomalies = sum(n.anomaly_count for n in nodes.values())
total_heals    = sum(n.heal_count for n in nodes.values())
heal_rate      = (total_heals / total_anomalies * 100) if total_anomalies > 0 else 100.0
avg_trust      = sum(n.trust for n in nodes.values()) / total_nodes

m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    st.metric("🔌 Total Nodes",     total_nodes)
with m2:
    st.metric("✅ Healthy",         healthy_count, delta=f"{healthy_count/total_nodes*100:.0f}%")
with m3:
    st.metric("⚠️ Faults / Anom.", fault_count,   delta_color="inverse" if fault_count else "normal")
with m4:
    st.metric("⚫ Offline",         offline_count)
with m5:
    st.metric("🔧 Heals Total",     total_heals,   delta=f"{heal_rate:.0f}% success")
with m6:
    trust_delta = f"{'🔴 Low' if avg_trust < 0.5 else '🟢 Good'}"
    st.metric("🔐 Avg Trust",       f"{avg_trust:.3f}", delta=trust_delta)

st.markdown("---")

# ══════════════════════════════════════════════
# MAIN LAYOUT: Network + Node Cards | Charts
# ══════════════════════════════════════════════
left_col, right_col = st.columns([1, 2], gap="medium")

# ── LEFT: Topology + Node Cards ──────────────
with left_col:
    # Compute current readings for topology
    current_readings = {nid: n.last_value for nid, n in nodes.items()}
    st.plotly_chart(chart_network_topology(nodes, current_readings),
                    use_container_width=True)

    st.markdown('<div class="section-head">📟 Node Status</div>', unsafe_allow_html=True)
    for nid, node in nodes.items():
        status = node.status
        css    = f"node-{status}"
        icon   = {"healthy": "✅", "anomaly": "⚠️", "fault": "🔴",
                   "healed": "🔧", "offline": "⚫"}.get(status, "❓")

        val_str = f"{node.last_value:.2f}°C" if node.last_value is not None else "OFFLINE"
        trust_pct = int(node.trust * 100)
        trust_color = "#48bb78" if node.trust >= 0.7 else "#ed8936" if node.trust >= 0.4 else "#f56565"

        st.markdown(f"""
        <div class="node-card {css}">
            <span style='font-weight:700;color:#bee3f8;'>{icon} {nid}</span>
            <span style='float:right;color:{trust_color};'>T={node.trust:.3f}</span><br>
            <span style='color:#a0aec0;'>Temp:</span> <b>{val_str}</b>
            &nbsp;|&nbsp;
            <span style='color:#a0aec0;'>Z:</span> <b>{node.last_z:.2f}</b><br>
            <span style='color:#a0aec0;'>Anomalies:</span> {node.anomaly_count}
            &nbsp;|&nbsp;
            <span style='color:#a0aec0;'>Heals:</span> {node.heal_count}<br>
            <div class="trust-bar-wrap">
                <div class="trust-bar-fill" style="width:{trust_pct}%;background:{trust_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── RIGHT: Charts ─────────────────────────────
with right_col:
    # Row 1: Sensor readings + Z-scores
    st.plotly_chart(chart_sensor_readings(nodes), use_container_width=True)
    st.plotly_chart(chart_z_scores(nodes),        use_container_width=True)

    # Row 2: Trust + Consensus
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_trust_scores(nodes), use_container_width=True)
    with c2:
        st.plotly_chart(chart_consensus_deviation(nodes, current_readings),
                        use_container_width=True)

# ══════════════════════════════════════════════
# EVENT LOG
# ══════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-head">📋 Self-Healing Event Log</div>', unsafe_allow_html=True)

log_col, stats_col = st.columns([2, 1])

with log_col:
    if events:
        event_html = '<div class="event-log-container">'
        for ev in reversed(events[-40:]):
            ev_type = ev["type"]
            css  = {"fault": "ev-fault", "anomaly": "ev-anomaly",
                    "heal": "ev-heal"}.get(ev_type, "ev-normal")
            icon = {"fault": "🔴", "anomaly": "⚠️", "heal": "🔧"}.get(ev_type, "✅")
            event_html += f"""
            <div class="event-item {css}">
                {icon} [{ev['ts']}] <b>Step {ev['step']}</b> — <b>{ev['node']}</b>: {ev['detail']}
            </div>"""
        event_html += '</div>'
        st.markdown(event_html, unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#7fb3d3;font-size:0.85rem;">No events yet. Start the simulation.</div>',
                    unsafe_allow_html=True)

with stats_col:
    st.markdown('<div class="section-head">📊 Algorithm Stats</div>', unsafe_allow_html=True)

    fault_evs  = sum(1 for e in events if e["type"] == "fault")
    anom_evs   = sum(1 for e in events if e["type"] == "anomaly")

    st.markdown(f"""
    <div style='font-family:JetBrains Mono;font-size:0.82rem;line-height:2.2;color:#a0aec0;
                background:rgba(26,39,68,0.5);border-radius:10px;padding:14px 16px;
                border:1px solid rgba(99,179,237,0.15);'>
    <b style='color:#bee3f8;'>Simulation Step:</b> {st.session_state.step}<br>
    <b style='color:#bee3f8;'>Total Events:</b>    {len(events)}<br>
    <b style='color:#f56565;'>Confirmed Faults:</b> {fault_evs}<br>
    <b style='color:#ed8936;'>Unconfirmed Anomalies:</b> {anom_evs}<br>
    <b style='color:#63b3ed;'>Healing Actions:</b> {total_heals}<br>
    <b style='color:#68d391;'>Heal Success Rate:</b> {heal_rate:.1f}%<br>
    <b style='color:#bee3f8;'>Avg Trust Score:</b> {avg_trust:.4f}<br>
    <b style='color:#7fb3d3;'>Z Threshold:</b>     ±{z_thresh:.1f}<br>
    <b style='color:#7fb3d3;'>Consensus δ:</b>     {c_delta:.1f}°C<br>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style='text-align:center;color:#4a5568;font-size:0.78rem;padding:8px;font-family:JetBrains Mono;'>
    Self-Healing IoT Network — Distributed AI Dashboard
    &nbsp;·&nbsp; Step {st.session_state.step}
    &nbsp;·&nbsp; {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    &nbsp;·&nbsp; Implements paper equations (1)(2)(3)(5)(6)
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SIMULATION TICK (auto-advance when running)
# ══════════════════════════════════════════════
if st.session_state.running:
    st.session_state.step += 1
    simulate_step(st.session_state.nodes, st.session_state.step, st.session_state.events)
    st.session_state.readings = {
        nid: n.last_value for nid, n in st.session_state.nodes.items()
    }
    time.sleep(st.session_state.speed)
    st.rerun()
