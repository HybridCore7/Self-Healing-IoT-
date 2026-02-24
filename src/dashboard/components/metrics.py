"""
Reusable Metric Components
"""
import streamlit as st
from typing import Optional

from src.dashboard.config import STATUS_COLORS, SEVERITY_COLORS
from src.dashboard.utils.formatters import get_status_emoji, get_severity_emoji


def metric_card(label: str, value: str, delta: Optional[str] = None, help_text: Optional[str] = None):
    """Display a metric card"""
    st.metric(
        label=label,
        value=value,
        delta=delta,
        help=help_text
    )


def status_badge(status: str) -> str:
    """Return colored status badge HTML"""
    emoji = get_status_emoji(status)
    color = STATUS_COLORS.get(status.lower(), "#95a5a6")
    return f"{emoji} **{status.upper()}**"


def severity_badge(severity: str) -> str:
    """Return colored severity badge HTML"""
    emoji = get_severity_emoji(severity)
    color = SEVERITY_COLORS.get(severity.lower(), "#95a5a6")
    return f"{emoji} **{severity.upper()}**"


def health_indicator(health_status: str, label: str = "Health"):
    """Display health status indicator"""
    emoji = get_status_emoji(health_status)
    color = STATUS_COLORS.get(health_status.lower(), "#95a5a6")
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; background-color: {color}20; border-left: 4px solid {color};">
            <span style="font-size: 20px;">{emoji}</span>
            <strong>{label}:</strong> {health_status.upper()}
        </div>
        """,
        unsafe_allow_html=True
    )


def info_box(title: str, content: str, icon: str = "ℹ️"):
    """Display an info box"""
    st.markdown(
        f"""
        <div style="padding: 15px; border-radius: 5px; background-color: #e3f2fd; border-left: 4px solid #2196f3;">
            <span style="font-size: 24px;">{icon}</span>
            <strong style="font-size: 16px;">{title}</strong>
            <p style="margin-top: 10px;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def warning_box(message: str):
    """Display a warning box"""
    st.warning(f"⚠️ {message}")


def error_box(message: str):
    """Display an error box"""
    st.error(f"❌ {message}")


def success_box(message: str):
    """Display a success box"""
    st.success(f"✅ {message}")


def create_metric_row(metrics: list):
    """Create a row of metrics"""
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            metric_card(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                delta=metric.get('delta'),
                help_text=metric.get('help')
            )
