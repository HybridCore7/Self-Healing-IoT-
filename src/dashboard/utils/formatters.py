"""
Data Formatting Utilities
"""
from datetime import datetime
from typing import Any, Optional


def format_datetime(dt_str: Optional[str]) -> str:
    """Format ISO datetime string to readable format"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str


def format_relative_time(dt_str: Optional[str]) -> str:
    """Format datetime as relative time (e.g., '5 minutes ago')"""
    if not dt_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"
    except:
        return dt_str


def format_number(value: Any, decimals: int = 2) -> str:
    """Format number with specified decimal places"""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except:
        return str(value)


def format_percentage(value: Any, decimals: int = 1) -> str:
    """Format value as percentage"""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except:
        return str(value)


def format_bytes(bytes_value: Any) -> str:
    """Format bytes to human-readable format"""
    if bytes_value is None:
        return "N/A"
    try:
        bytes_value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    except:
        return str(bytes_value)


def format_duration(seconds: Optional[float]) -> str:
    """Format duration in seconds to readable format"""
    if seconds is None:
        return "N/A"
    try:
        seconds = float(seconds)
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"
    except:
        return str(seconds)


def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    status_emojis = {
        "online": "🟢",
        "offline": "⚫",
        "error": "🔴",
        "warning": "🟡",
        "healthy": "✅",
        "critical": "🔴",
        "success": "✅",
        "failed": "❌",
        "pending": "⏳",
        "in_progress": "🔄",
    }
    return status_emojis.get(status.lower(), "⚪")


def get_severity_emoji(severity: str) -> str:
    """Get emoji for severity level"""
    severity_emojis = {
        "low": "🔵",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }
    return severity_emojis.get(severity.lower(), "⚪")
