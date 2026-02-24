# Self-Healing IoT Dashboard

## 🎨 Dashboard Overview

The Streamlit dashboard provides a comprehensive web interface for monitoring and controlling your Self-Healing IoT System.

## 🚀 Quick Start

### Prerequisites
- Backend server must be running
- All dependencies installed (see `docs/WINDOWS_SETUP.md`)

### Start the Dashboard

**Windows:**
```bash
scripts\start_dashboard.bat
```

**Linux/Mac:**
```bash
streamlit run src/dashboard/app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## 📊 Dashboard Pages

### 1. Home (Overview)
**URL:** `http://localhost:8501`

**Features:**
- System health status
- Key metrics (devices, anomalies, healing actions)
- Device health summary
- System resource usage (CPU, memory, disk)
- Connection status indicator
- Auto-refresh capability

### 2. Devices
**URL:** `http://localhost:8501/Devices`

**Features:**
- Device list with status indicators
- Device registration form
- Individual device details
- Real-time telemetry charts
- Device deletion
- Filter and search

### 3. Anomalies
**URL:** `http://localhost:8501/Anomalies`

**Features:**
- Active anomalies table
- Anomaly timeline chart (24 hours)
- Distribution by type and severity
- Anomaly resolution controls
- Detailed anomaly information
- Filtering by severity and status

### 4. Healing Logs
**URL:** `http://localhost:8501/Healing_Logs`

**Features:**
- Healing action history
- Success rate statistics
- Action type distribution
- Manual healing trigger
- Active healing workflows
- Detailed log information

## 🎯 Key Features

### Real-time Updates
- Auto-refresh toggle (configurable interval)
- Manual refresh button
- Last update timestamp

### Interactive Charts
- Plotly-based visualizations
- Hover tooltips
- Zoom and pan
- Export to PNG

### Responsive Design
- Works on desktop and mobile
- Collapsible sidebar
- Adaptive layouts

### Data Management
- Device registration
- Manual healing triggers
- Anomaly resolution
- Filtering and search

## 🔧 Configuration

Edit `src/dashboard/config.py` to customize:

```python
# API Configuration
API_BASE_URL = "http://localhost:8000"

# Refresh Settings
AUTO_REFRESH_INTERVAL = 5  # seconds

# Chart Colors
COLORS = {
    "primary": "#1f77b4",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "danger": "#e74c3c",
}
```

## 📱 Usage Examples

### Register a New Device
1. Navigate to **Devices** page
2. Click **Register Device** tab
3. Fill in device information
4. Click **Register Device** button

### View Anomaly Timeline
1. Navigate to **Anomalies** page
2. View the timeline chart showing anomalies over last 24 hours
3. Filter by severity or type
4. Click on specific anomaly for details

### Trigger Manual Healing
1. Navigate to **Healing Logs** page
2. Scroll to **Manual Healing Trigger** section
3. Select target device
4. Choose healing action
5. Click **Trigger Healing** button

### Monitor System Health
1. Check sidebar for connection status
2. View quick stats in sidebar
3. Main page shows detailed system health
4. Enable auto-refresh for real-time monitoring

## 🐛 Troubleshooting

### Dashboard won't start
```bash
# Check if streamlit is installed
pip install streamlit

# Check if backend is running
curl http://localhost:8000/api/health/
```

### "Backend Offline" error
- Ensure backend server is running: `python -m src.backend.main`
- Check API_BASE_URL in `src/dashboard/config.py`
- Verify backend is accessible at http://localhost:8000

### Charts not displaying
- Check browser console for errors
- Ensure plotly is installed: `pip install plotly`
- Try refreshing the page

### Auto-refresh not working
- Check browser console for errors
- Disable browser extensions that might block auto-refresh
- Try manual refresh button

## 📚 Technical Details

### Architecture
```
src/dashboard/
├── app.py                    # Main Streamlit app (Home page)
├── config.py                 # Dashboard configuration
├── pages/
│   ├── 2_Devices.py         # Device monitoring page
│   ├── 3_Anomalies.py       # Anomaly visualization page
│   └── 4_Healing_Logs.py    # Healing logs page
├── components/
│   ├── charts.py            # Reusable Plotly charts
│   └── metrics.py           # Metric cards and indicators
└── utils/
    ├── data_fetcher.py      # API client
    └── formatters.py        # Data formatting utilities
```

### API Integration
The dashboard uses the `APIClient` class to communicate with the backend:
- All API calls are cached for performance
- Error handling with user-friendly messages
- Connection status checking
- Retry logic for failed requests

### Performance
- Streamlit caching for API responses
- Efficient data fetching
- Lazy loading of charts
- Optimized re-renders

## 🎨 Customization

### Adding a New Page
1. Create `src/dashboard/pages/5_Your_Page.py`
2. Use existing components and utilities
3. Follow the naming convention: `N_Page_Name.py`

### Custom Charts
Use the chart components in `src/dashboard/components/charts.py`:
```python
from src.dashboard.components.charts import create_timeline_chart

fig = create_timeline_chart(
    data=your_data,
    x_field='timestamp',
    y_field='value',
    title='Your Chart Title'
)
st.plotly_chart(fig)
```

### Custom Metrics
Use the metric components in `src/dashboard/components/metrics.py`:
```python
from src.dashboard.components.metrics import metric_card

metric_card(
    label="Your Metric",
    value="123",
    delta="+10%"
)
```

## 📖 Related Documentation

- [API Reference](API_REFERENCE.md)
- [Hardware Integration](HARDWARE_INTEGRATION.md)
- [Windows Setup](WINDOWS_SETUP.md)
- [Quick Start](QUICK_START.md)
