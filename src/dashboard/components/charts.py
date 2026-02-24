"""
Reusable Chart Components using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
import pandas as pd

from src.dashboard.config import CHART_HEIGHT, CHART_TEMPLATE, COLORS, SEVERITY_COLORS, STATUS_COLORS


def create_timeline_chart(data: List[Dict], x_field: str, y_field: str, title: str, color_field: Optional[str] = None) -> go.Figure:
    """Create timeline/line chart"""
    df = pd.DataFrame(data)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
    else:
        if color_field and color_field in df.columns:
            fig = px.line(df, x=x_field, y=y_field, color=color_field, title=title)
        else:
            fig = px.line(df, x=x_field, y=y_field, title=title)
        
        fig.update_traces(mode='lines+markers')
    
    fig.update_layout(
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE,
        hovermode='x unified'
    )
    
    return fig


def create_pie_chart(labels: List[str], values: List[float], title: str, colors: Optional[List[str]] = None) -> go.Figure:
    """Create pie chart"""
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors) if colors else None,
        hole=0.3  # Donut chart
    )])
    
    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE,
        showlegend=True
    )
    
    return fig


def create_bar_chart(data: Dict[str, float], title: str, orientation: str = 'v', color: Optional[str] = None) -> go.Figure:
    """Create bar chart"""
    if orientation == 'h':
        fig = go.Figure(data=[go.Bar(
            y=list(data.keys()),
            x=list(data.values()),
            orientation='h',
            marker_color=color or COLORS['primary']
        )])
    else:
        fig = go.Figure(data=[go.Bar(
            x=list(data.keys()),
            y=list(data.values()),
            marker_color=color or COLORS['primary']
        )])
    
    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE
    )
    
    return fig


def create_gauge_chart(value: float, title: str, max_value: float = 100, thresholds: Optional[Dict] = None) -> go.Figure:
    """Create gauge chart"""
    if thresholds is None:
        thresholds = {
            'low': 33,
            'medium': 66,
            'high': 100
        }
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        delta={'reference': max_value * 0.8},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': COLORS['primary']},
            'steps': [
                {'range': [0, thresholds['low']], 'color': "lightgray"},
                {'range': [thresholds['low'], thresholds['medium']], 'color': "gray"},
                {'range': [thresholds['medium'], max_value], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        template=CHART_TEMPLATE
    )
    
    return fig


def create_stacked_bar_chart(data: pd.DataFrame, x_field: str, y_fields: List[str], title: str) -> go.Figure:
    """Create stacked bar chart"""
    fig = go.Figure()
    
    for y_field in y_fields:
        fig.add_trace(go.Bar(
            name=y_field,
            x=data[x_field],
            y=data[y_field]
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE
    )
    
    return fig


def create_scatter_plot(data: List[Dict], x_field: str, y_field: str, title: str, color_field: Optional[str] = None) -> go.Figure:
    """Create scatter plot"""
    df = pd.DataFrame(data)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
    else:
        if color_field and color_field in df.columns:
            fig = px.scatter(df, x=x_field, y=y_field, color=color_field, title=title)
        else:
            fig = px.scatter(df, x=x_field, y=y_field, title=title)
    
    fig.update_layout(
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE
    )
    
    return fig


def create_heatmap(data: pd.DataFrame, title: str) -> go.Figure:
    """Create correlation heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale='RdYlGn',
        text=data.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE
    )
    
    return fig


def create_anomaly_timeline(timeline_data: List[Dict]) -> go.Figure:
    """Create anomaly timeline chart with severity breakdown"""
    df = pd.DataFrame(timeline_data)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No anomalies detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
    else:
        # Create stacked area chart for severity levels
        fig = go.Figure()
        
        # Extract severity data
        severities = ['low', 'medium', 'high', 'critical']
        for severity in severities:
            y_values = [item['by_severity'].get(severity, 0) for item in timeline_data]
            fig.add_trace(go.Scatter(
                x=[item['timestamp'] for item in timeline_data],
                y=y_values,
                name=severity.capitalize(),
                mode='lines',
                stackgroup='one',
                fillcolor=SEVERITY_COLORS.get(severity, 'gray')
            ))
    
    fig.update_layout(
        title="Anomaly Timeline (by Severity)",
        xaxis_title="Time",
        yaxis_title="Number of Anomalies",
        height=CHART_HEIGHT,
        template=CHART_TEMPLATE,
        hovermode='x unified'
    )
    
    return fig
