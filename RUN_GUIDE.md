# Quick Start Guide - Running the System

## 🚀 Running Backend and Frontend

### Option 1: Using Startup Scripts (Easiest)

**Step 1: Open TWO terminal windows**

**Terminal 1 - Start Backend:**
```bash
cd d:\self-healing-iot
scripts\start_backend.bat
```

**Terminal 2 - Start Dashboard:**
```bash
cd d:\self-healing-iot
scripts\start_dashboard.bat
```

---

### Option 2: Manual Commands

**Terminal 1 - Backend:**
```bash
cd d:\self-healing-iot
python -m src.backend.main
```

**Terminal 2 - Dashboard:**
```bash
cd d:\self-healing-iot
streamlit run src\dashboard\app.py
```

---

## 📍 Access URLs

Once both are running:

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8501

---

## ✅ Verification

### Check Backend is Running
```bash
curl http://localhost:8000/api/health/
```

You should see:
```json
{
  "status": "healthy",
  "services": {
    "backend": "running",
    "mqtt": "connected",
    "database": "connected"
  }
}
```

### Check Dashboard
- Open browser to http://localhost:8501
- You should see the dashboard home page
- Sidebar should show "🟢 Backend Connected"

---

## 🛑 Stopping the System

Press **CTRL+C** in each terminal window to stop the services.

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check if dependencies are installed
pip install fastapi uvicorn pydantic paho-mqtt aiosqlite

# Check if port 8000 is already in use
netstat -ano | findstr :8000
```

### Dashboard won't start
```bash
# Install streamlit
pip install streamlit plotly pandas

# Check if port 8501 is already in use
netstat -ano | findstr :8501
```

### Dashboard shows "Backend Offline"
1. Make sure backend is running first
2. Check http://localhost:8000/api/health/ in browser
3. Verify no firewall blocking localhost connections

---

## 📊 What to Do Next

1. **Register a device** via Dashboard → Devices page
2. **View system health** on home page
3. **Explore API docs** at http://localhost:8000/docs
4. **Run device simulator** (optional):
   ```bash
   python -m src.simulator.device_simulator
   ```

---

## 💡 Pro Tips

- Keep both terminals open while using the system
- Use the auto-refresh feature in dashboard for real-time monitoring
- Check API docs for testing endpoints directly
- Enable debug mode in `config/settings.py` for detailed logs
