"""
System Health API Endpoints
Provides system-wide health and status information
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil

from src.database.db_manager import get_db_manager
from src.database.repositories.device_repo import DeviceRepository
from src.database.repositories.anomaly_repo import AnomalyRepository
from src.database.repositories.healing_repo import HealingRepository
from src.mqtt.client import get_mqtt_client
from src.healing.orchestrator import get_healing_orchestrator
from src.utils.constants import DeviceStatus, Severity
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def system_health():
    """
    Get overall system health status
    
    Returns health status of all system components:
    - Backend API
    - MQTT broker connection
    - Database connection
    - Healing orchestrator
    """
    logger.info("Health check requested")
    
    try:
        # Check MQTT connection
        mqtt_client = get_mqtt_client()
        mqtt_status = "connected" if mqtt_client and mqtt_client.is_connected() else "disconnected"
        
        # Check database
        try:
            db_manager = await get_db_manager()
            db_status = "connected"
        except Exception:
            db_status = "error"
        
        # Check healing orchestrator
        try:
            orchestrator = get_healing_orchestrator()
            orchestrator_status = orchestrator.get_status()
            healing_status = "running" if orchestrator_status['running'] else "stopped"
        except Exception:
            healing_status = "error"
        
        # Overall health
        all_healthy = all([
            mqtt_status == "connected",
            db_status == "connected",
            healing_status == "running"
        ])
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "backend": "running",
                "mqtt": mqtt_status,
                "database": db_status,
                "healing_orchestrator": healing_status
            }
        }
    
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def system_metrics():
    """
    Get system performance metrics
    
    Returns:
    - Active devices count
    - Total telemetry messages
    - Active anomalies
    - Healing actions (today)
    - System resource usage
    """
    logger.info("System metrics requested")
    
    try:
        db_manager = await get_db_manager()
        
        # Device metrics
        device_repo = DeviceRepository(db_manager)
        all_devices = await device_repo.list_devices()
        active_devices = sum(1 for d in all_devices if d.status == DeviceStatus.ONLINE)
        
        # Anomaly metrics
        anomaly_repo = AnomalyRepository(db_manager)
        active_anomalies = await anomaly_repo.get_active_anomalies()
        anomaly_counts = await anomaly_repo.get_anomaly_counts_by_severity()
        
        # Healing metrics
        healing_repo = HealingRepository(db_manager)
        healing_logs = await healing_repo.get_healing_history(limit=1000)
        
        # Filter today's healing actions
        today = datetime.utcnow().date()
        healing_today = sum(
            1 for log in healing_logs 
            if datetime.fromisoformat(log['initiated_at']).date() == today
        )
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "devices": {
                "total": len(all_devices),
                "active": active_devices,
                "offline": len(all_devices) - active_devices
            },
            "anomalies": {
                "active": len(active_anomalies),
                "by_severity": anomaly_counts
            },
            "healing": {
                "actions_today": healing_today,
                "total_actions": len(healing_logs)
            },
            "system_resources": {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "memory_used_mb": round(memory.used / 1024 / 1024, 2),
                "disk_percent": round(disk.percent, 2),
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices")
async def device_health_summary():
    """
    Get device health summary
    
    Returns summary of all devices with their health status
    """
    logger.info("Device health summary requested")
    
    try:
        db_manager = await get_db_manager()
        device_repo = DeviceRepository(db_manager)
        anomaly_repo = AnomalyRepository(db_manager)
        
        # Get all devices
        devices = await device_repo.list_devices()
        
        # Build health summary
        device_summaries = []
        for device in devices:
            # Get active anomalies for this device
            device_anomalies = await anomaly_repo.get_active_anomalies(device_id=device.device_id)
            
            # Determine health status
            if device.status == DeviceStatus.OFFLINE:
                health = "offline"
            elif len(device_anomalies) > 0:
                # Check severity
                critical_anomalies = [a for a in device_anomalies if a['severity'] == Severity.CRITICAL.value]
                if critical_anomalies:
                    health = "critical"
                else:
                    health = "warning"
            else:
                health = "healthy"
            
            device_summaries.append({
                "device_id": device.device_id,
                "device_name": device.device_name,
                "status": device.status.value,
                "health": health,
                "active_anomalies": len(device_anomalies),
                "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None
            })
        
        # Count by health status
        health_counts = {
            "healthy": sum(1 for d in device_summaries if d['health'] == 'healthy'),
            "warning": sum(1 for d in device_summaries if d['health'] == 'warning'),
            "critical": sum(1 for d in device_summaries if d['health'] == 'critical'),
            "offline": sum(1 for d in device_summaries if d['health'] == 'offline')
        }
        
        return {
            "total_devices": len(devices),
            "health_summary": health_counts,
            "devices": device_summaries
        }
    
    except Exception as e:
        logger.error(f"Error fetching device health summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies")
async def anomaly_statistics():
    """
    Get anomaly statistics
    
    Returns statistics about detected anomalies
    """
    logger.info("Anomaly statistics requested")
    
    try:
        db_manager = await get_db_manager()
        anomaly_repo = AnomalyRepository(db_manager)
        
        # Get active anomalies
        active_anomalies = await anomaly_repo.get_active_anomalies()
        
        # Get counts by type and severity
        type_counts = await anomaly_repo.get_anomaly_counts_by_type()
        severity_counts = await anomaly_repo.get_anomaly_counts_by_severity()
        
        # Get recent anomalies (last 24 hours)
        recent_anomalies = await anomaly_repo.get_recent_anomalies(hours=24)
        
        return {
            "active_anomalies": len(active_anomalies),
            "recent_anomalies_24h": len(recent_anomalies),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "recent_samples": recent_anomalies[:10]  # Latest 10
        }
    
    except Exception as e:
        logger.error(f"Error fetching anomaly statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
