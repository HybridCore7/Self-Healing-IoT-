"""
API Data Fetcher
Handles all API requests to the backend
"""
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import streamlit as st

from src.dashboard.config import API_BASE_URL, API_TIMEOUT


class APIClient:
    """Client for interacting with the backend API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.timeout = API_TIMEOUT
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make GET request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None
    
    def _post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make POST request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None
    
    def _delete(self, endpoint: str) -> bool:
        """Make DELETE request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.delete(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return False
    
    # Health API
    def get_system_health(self) -> Optional[Dict]:
        """Get overall system health"""
        return self._get("/api/health/")
    
    def get_system_metrics(self) -> Optional[Dict]:
        """Get system performance metrics"""
        return self._get("/api/health/metrics")
    
    def get_device_health_summary(self) -> Optional[Dict]:
        """Get device health summary"""
        return self._get("/api/health/devices")
    
    def get_anomaly_statistics(self) -> Optional[Dict]:
        """Get anomaly statistics"""
        return self._get("/api/health/anomalies")
    
    # Device API
    def get_devices(self) -> Optional[List[Dict]]:
        """Get all devices"""
        result = self._get("/api/devices")
        # API returns a list directly, not a dict
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "devices" in result:
            return result["devices"]
        return result if result else []
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """Get specific device"""
        return self._get(f"/api/devices/{device_id}")
    
    def register_device(self, device_data: Dict) -> Optional[Dict]:
        """Register new device"""
        return self._post("/api/devices/", device_data)
    
    def delete_device(self, device_id: str) -> bool:
        """Delete device"""
        return self._delete(f"/api/devices/{device_id}")
    
    # Telemetry API
    def get_device_telemetry(self, device_id: str, limit: int = 100) -> Optional[Dict]:
        """Get telemetry for device"""
        return self._get(f"/api/telemetry/{device_id}", params={"limit": limit})
    
    def get_telemetry_stats(self, device_id: str, sensor_type: Optional[str] = None) -> Optional[Dict]:
        """Get telemetry statistics"""
        params = {}
        if sensor_type:
            params["sensor_type"] = sensor_type
        return self._get(f"/api/telemetry/{device_id}/stats", params=params)
    
    # Anomaly API
    def get_anomalies(self, device_id: Optional[str] = None, active_only: bool = False, limit: int = 100) -> Optional[Dict]:
        """Get anomalies"""
        params = {"limit": limit, "active_only": active_only}
        if device_id:
            params["device_id"] = device_id
        return self._get("/api/anomalies", params=params)
    
    def get_anomaly(self, anomaly_id: int) -> Optional[Dict]:
        """Get specific anomaly"""
        return self._get(f"/api/anomalies/{anomaly_id}")
    
    def resolve_anomaly(self, anomaly_id: int) -> Optional[Dict]:
        """Resolve an anomaly"""
        return self._post(f"/api/anomalies/{anomaly_id}/resolve", {})
    
    def get_anomaly_summary(self) -> Optional[Dict]:
        """Get anomaly summary statistics"""
        return self._get("/api/anomalies/stats/summary")
    
    def get_anomaly_timeline(self, hours: int = 24) -> Optional[Dict]:
        """Get anomaly timeline"""
        return self._get("/api/anomalies/stats/timeline", params={"hours": hours})
    
    # Healing API
    def get_healing_logs(self, device_id: Optional[str] = None, limit: int = 100) -> Optional[Dict]:
        """Get healing logs"""
        params = {"limit": limit}
        if device_id:
            params["device_id"] = device_id
        return self._get("/api/healing/logs", params=params)
    
    def get_healing_stats(self, device_id: Optional[str] = None) -> Optional[Dict]:
        """Get healing statistics"""
        params = {}
        if device_id:
            params["device_id"] = device_id
        return self._get("/api/healing/stats", params=params)
    
    def get_active_healings(self) -> Optional[Dict]:
        """Get active healing workflows"""
        return self._get("/api/healing/active")
    
    def trigger_healing(self, device_id: str, action: str, parameters: Optional[Dict] = None) -> Optional[Dict]:
        """Trigger manual healing action"""
        data = {"action": action}
        if parameters:
            data["parameters"] = parameters
        return self._post(f"/api/healing/trigger/{device_id}", data)
    
    def get_available_actions(self) -> Optional[Dict]:
        """Get available healing actions"""
        return self._get("/api/healing/actions")
    
    def check_connection(self) -> bool:
        """Check if backend is reachable"""
        try:
            response = requests.get(f"{self.base_url}/api/health/", timeout=2)
            return response.status_code == 200
        except:
            return False


# Singleton instance
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance"""
    return APIClient()
