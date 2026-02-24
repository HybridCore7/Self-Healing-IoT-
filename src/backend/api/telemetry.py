"""
Telemetry API Endpoints - Handle telemetry data operations
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from src.backend.models.telemetry import TelemetryCreate, TelemetryResponse, TelemetryStats
from src.database.db_manager import get_db_manager
from src.database.repositories.telemetry_repo import TelemetryRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=dict, status_code=201)
async def create_telemetry(telemetry: TelemetryCreate):
    """
    Create new telemetry record
    """
    logger.info(f"Creating telemetry record for device {telemetry.device_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = TelemetryRepository(db_manager)
        
        telemetry_id = await repo.insert_telemetry(
            telemetry.device_id,
            telemetry.sensor_type,
            telemetry.sensor_value,
            telemetry.unit,
            telemetry.is_anomaly
        )
        
        return {"id": telemetry_id, "message": "Telemetry created successfully"}
    
    except Exception as e:
        logger.error(f"Error creating telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}", response_model=List[dict])
async def get_device_telemetry(
    device_id: str,
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """
    Get telemetry data for a device
    """
    logger.info(f"Fetching telemetry for device {device_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = TelemetryRepository(db_manager)
        
        telemetry_data = await repo.get_recent_telemetry(device_id, sensor_type, limit)
        return telemetry_data
    
    except Exception as e:
        logger.error(f"Error fetching telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/stats", response_model=TelemetryStats)
async def get_telemetry_stats(
    device_id: str,
    sensor_type: str = Query(..., description="Sensor type"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze")
):
    """
    Get telemetry statistics for device and sensor
    """
    logger.info(f"Fetching telemetry stats for {device_id}/{sensor_type}")
    
    try:
        db_manager = await get_db_manager()
        repo = TelemetryRepository(db_manager)
        
        stats = await repo.get_statistics(device_id, sensor_type, hours)
        
        return TelemetryStats(
            device_id=device_id,
            sensor_type=sensor_type,
            min_value=stats.get('min_value'),
            max_value=stats.get('max_value'),
            avg_value=stats.get('avg_value'),
            count=stats.get('count', 0),
            period_hours=hours
        )
    
    except Exception as e:
        logger.error(f"Error fetching telemetry stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/recent", response_model=List[dict])
async def get_anomalous_telemetry(
    device_id: Optional[str] = Query(None, description="Filter by device"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """
    Get anomalous telemetry data
    """
    logger.info("Fetching anomalous telemetry")
    
    try:
        db_manager = await get_db_manager()
        repo = TelemetryRepository(db_manager)
        
        anomalous_data = await repo.get_anomalous_telemetry(device_id, hours, limit)
        return anomalous_data
    
    except Exception as e:
        logger.error(f"Error fetching anomalous telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
