"""
Dashboard Configuration
"""

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 10  # seconds

# Refresh Settings
AUTO_REFRESH_INTERVAL = 5  # seconds
DEFAULT_LIMIT = 100  # default number of records to fetch

# Chart Colors
COLORS = {
    "primary": "#1f77b4",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "info": "#3498db",
    "secondary": "#95a5a6",
}

STATUS_COLORS = {
    "online": "#2ecc71",
    "offline": "#95a5a6",
    "error": "#e74c3c",
    "warning": "#f39c12",
    "healthy": "#2ecc71",
    "critical": "#e74c3c",
}

SEVERITY_COLORS = {
    "low": "#3498db",
    "medium": "#f39c12",
    "high": "#e67e22",
    "critical": "#e74c3c",
}

# Page Configuration
PAGE_TITLE = "Self-Healing IoT System"
PAGE_ICON = "🔧"
LAYOUT = "wide"

# Chart Settings
CHART_HEIGHT = 400
CHART_TEMPLATE = "plotly_white"
