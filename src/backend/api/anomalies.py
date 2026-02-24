"""
Anomaly API Endpoints
Handles anomaly detection data and statistics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from src.database.db_manager import get_db_manager
from src.database.repositories.anomaly_repo import AnomalyRepository
from src.utils.constants import AnomalyType, Severity
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def get_anomalies(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    active_only: bool = Query(False, description="Show only active anomalies"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of anomalies")
):
    """
    Get anomalies with optional filtering
    
    - **device_id**: Filter for specific device
    - **severity**: Filter by severity (low, medium, high, critical)
    - **active_only**: Show only unresolved anomalies
    - **limit**: Maximum results to return
    """
    logger.info(f"Fetching anomalies: device={device_id}, severity={severity}, active_only={active_only}")
    
    try:
        db_manager = await get_db_manager()
        repo = AnomalyRepository(db_manager)
        
        if active_only:
            # Get active anomalies
            severity_enum = Severity(severity) if severity else None
            anomalies = await repo.get_active_anomalies(device_id, severity_enum)
        else:
            # Get recent anomalies
            anomalies = await repo.get_recent_anomalies(hours=24, limit=limit)
            
            # Filter by device if specified
            if device_id:
                anomalies = [a for a in anomalies if a.get('device_id') == device_id]
            
            # Filter by severity if specified
            if severity:
                anomalies = [a for a in anomalies if a.get('severity') == severity]
        
        return {
            "count": len(anomalies),
            "anomalies": anomalies
        }
    
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{anomaly_id}")
async def get_anomaly(anomaly_id: int):
    """
    Get details of a specific anomaly
    """
    logger.info(f"Fetching anomaly: {anomaly_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = AnomalyRepository(db_manager)
        
        # Get anomaly by ID
        async with db_manager.get_connection() as db:
            cursor = await db.execute(
                """
                SELECT id, device_id, anomaly_type, severity, sensor_type,
                       anomaly_score, description, detected_at, resolved_at
                FROM anomalies
                WHERE id = ?
                """,
                (anomaly_id,)
            )
            row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
        
        return {
            "id": row[0],
            "device_id": row[1],
            "anomaly_type": row[2],
            "severity": row[3],
            "sensor_type": row[4],
            "anomaly_score": row[5],
            "description": row[6],
            "detected_at": row[7],
            "resolved_at": row[8],
            "is_active": row[8] is None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{anomaly_id}/resolve")
async def resolve_anomaly(anomaly_id: int):
    """
    Mark an anomaly as resolved
    """
    logger.info(f"Resolving anomaly: {anomaly_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = AnomalyRepository(db_manager)
        
        success = await repo.resolve_anomaly(anomaly_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
        
        return {
            "success": True,
            "message": f"Anomaly {anomaly_id} resolved",
            "resolved_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/device/{device_id}")
async def get_device_anomalies(
    device_id: str,
    active_only: bool = Query(False, description="Show only active anomalies"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get all anomalies for a specific device
    """
    logger.info(f"Fetching anomalies for device: {device_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = AnomalyRepository(db_manager)
        
        if active_only:
            anomalies = await repo.get_active_anomalies(device_id=device_id)
        else:
            # Get recent anomalies and filter by device
            all_anomalies = await repo.get_recent_anomalies(hours=168, limit=limit)  # 7 days
            anomalies = [a for a in all_anomalies if a.get('device_id') == device_id]
        
        return {
            "device_id": device_id,
            "count": len(anomalies),
            "anomalies": anomalies
        }
    
    except Exception as e:
        logger.error(f"Error fetching device anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_anomaly_summary():
    """
    Get summary statistics for anomalies
    """
    logger.info("Fetching anomaly summary")
    
    try:
        db_manager = await get_db_manager()
        repo = AnomalyRepository(db_manager)
        
        # Get active anomalies
        active_anomalies = await repo.get_active_anomalies()
        
        # Get counts by type and severity
        type_counts = await repo.get_anomaly_counts_by_type()
        severity_counts = await repo.get_anomaly_counts_by_severity()
        
        # Get recent anomalies for trend
        recent_24h = await repo.get_recent_anomalies(hours=24)
        recent_7d = await repo.get_recent_anomalies(hours=168)
        
        return {
            "active_count": len(active_anomalies),
            "last_24h": len(recent_24h),
            "last_7d": len(recent_7d),
            "by_type": type_counts,
            "by_severity": severity_counts
        }
    
    except Exception as e:
        logger.error(f"Error fetching anomaly summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/timeline")
async def get_anomaly_timeline(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours")
):
    """
    Get anomaly detection timeline
    
    Returns anomalies grouped by time intervals for visualization
    """
    logger.info(f"Fetching anomaly timeline for last {hours} hours")
    
    try:
        db_manager = await get_db_manager()
        repo = AnomalyRepository(db_manager)
        
        # Get anomalies in time range
        anomalies = await repo.get_recent_anomalies(hours=hours)
        
        # Group by hour
        timeline = {}
        for anomaly in anomalies:
            detected_at = datetime.fromisoformat(anomaly['detected_at'])
            hour_key = detected_at.strftime('%Y-%m-%d %H:00')
            
            if hour_key not in timeline:
                timeline[hour_key] = {
                    "timestamp": hour_key,
                    "count": 0,
                    "by_severity": {}
                }
            
            timeline[hour_key]["count"] += 1
            severity = anomaly.get('severity', 'unknown')
            timeline[hour_key]["by_severity"][severity] = timeline[hour_key]["by_severity"].get(severity, 0) + 1
        
        # Convert to sorted list
        timeline_list = sorted(timeline.values(), key=lambda x: x['timestamp'])
        
        return {
            "hours": hours,
            "total_anomalies": len(anomalies),
            "timeline": timeline_list
        }
    
    except Exception as e:
        logger.error(f"Error fetching anomaly timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
